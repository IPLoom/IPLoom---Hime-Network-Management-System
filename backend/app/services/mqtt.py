import paho.mqtt.client as mqtt
import json
import logging
import time
import threading
from typing import Any, Optional
from app.core.config import get_settings
from app.core.db import get_connection

logger = logging.getLogger(__name__)
# Add a dedicated file handler for MQTT debugging if not already present
if not any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith('mqtt_debug.log') for h in logger.handlers):
    fh = logging.FileHandler('mqtt_debug.log')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)

# Paho MQTT 2.0 compatibility helper
def get_mqtt_client(client_id: str):
    try:
        # Paho 2.0+
        from paho.mqtt.enums import CallbackAPIVersion
        return mqtt.Client(CallbackAPIVersion.VERSION1, client_id=client_id)
    except (ImportError, TypeError):
        # Paho 1.x
        return mqtt.Client(client_id=client_id)

class MQTTManager:
    _instance: Optional['MQTTManager'] = None
    
    def __init__(self):
        self.last_status = "unknown"
        self.last_error = None
        self.last_test_time = 0
        self.is_reachable = False
        self._client = None
        self._lock = threading.Lock()
        self._load_status()
        self._connect_persistent()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_status(self):
        """Loads the last known status from the database."""
        conn = get_connection()
        try:
            row = conn.execute("SELECT value FROM config WHERE key = 'mqtt_status'").fetchone()
            if row:
                self.last_status = row[0]
                self.is_reachable = (self.last_status == "online")
            
            error_row = conn.execute("SELECT value FROM config WHERE key = 'mqtt_error'").fetchone()
            if error_row:
                self.last_error = error_row[0]
        except Exception as e:
            logger.error(f"Failed to load MQTT status: {e}")
        finally:
            conn.close()

    def _save_status(self, status: str, error: str = None):
        """Saves status to the database and updates internal state."""
        self.last_status = status
        self.last_error = error
        self.is_reachable = (status == "online")
        
        conn = get_connection()
        try:
            conn.execute("INSERT OR REPLACE INTO config (key, value, updated_at) VALUES ('mqtt_status', ?, now())", [status])
            conn.execute("INSERT OR REPLACE INTO config (key, value, updated_at) VALUES ('mqtt_error', ?, now())", [error or ""])
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to save MQTT status: {e}")
        finally:
            conn.close()

    def _connect_persistent(self):
        """Connects the persistent client."""
        with self._lock:
            # If we already have a client, don't create a new one.
            # Paho handles auto-reconnect automatically in its own background thread.
            if self._client:
                return
                
            config = self.get_config()
            # Use a highly unique client ID to avoid conflicts during restarts/reloads/multiple processes
            import os
            import random
            # Add random suffix to PID to be extra sure across rapid reloads
            client_id = f"iploom_main_{os.getpid()}_{random.randint(1000, 9999)}"
            logger.info(f"Initializing persistent MQTT client with unique ID: {client_id}")
            
            self._client = get_mqtt_client(client_id)
            
            if config['username']:
                self._client.username_pw_set(config['username'], config['password'])
                
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    self.is_reachable = True
                    self._save_status("online")
                    logger.info("MQTT Persistent Client connected successfully.")
                else:
                    self.is_reachable = False
                    self._save_status("offline", f"Connection failed with code {rc}")
                    logger.warning(f"MQTT Persistent Client failed to connect: rc={rc}")

            def on_disconnect(client, userdata, rc):
                # rc=0 means intentional disconnect. 
                # rc=7 means connection lost (broker kicked us, etc.)
                self.is_reachable = False
                if rc != 0:
                    logger.warning(f"MQTT Persistent Client connection lost (rc={rc}). Paho will attempt auto-reconnect.")
                else:
                    logger.info("MQTT Persistent Client disconnected intentionally.")

            self._client.on_connect = on_connect
            self._client.on_disconnect = on_disconnect
            
            try:
                # Set keepalive to 60s. loop_start() runs the background thread for auto-reconnect.
                self._client.connect(config['broker'], config['port'], keepalive=60)
                self._client.loop_start()
            except Exception as e:
                logger.error(f"Failed to start MQTT persistent client: {e}")
                self.is_reachable = False
                self._save_status("offline", str(e))

    def get_config(self):
        settings = get_settings()
        conn = get_connection()
        try:
            keys = ['mqtt_broker', 'mqtt_port', 'mqtt_base_topic', 'mqtt_username', 'mqtt_password']
            rows = conn.execute("SELECT key, value FROM config WHERE key IN ({})".format(','.join(['?']*len(keys))), keys).fetchall()
            config = {r[0]: r[1] for r in rows}
            
            return {
                'broker': config.get('mqtt_broker') or getattr(settings, 'mqtt_broker', 'localhost'),
                'port': int(config.get('mqtt_port') or getattr(settings, 'mqtt_port', 1883)),
                'base_topic': config.get('mqtt_base_topic') or getattr(settings, 'mqtt_base_topic', 'network_scanner'),
                'username': config.get('mqtt_username') or getattr(settings, 'mqtt_username', None),
                'password': config.get('mqtt_password') or getattr(settings, 'mqtt_password', None)
            }
        finally:
            conn.close()

    def test_connection(self, custom_config: Optional[dict] = None) -> tuple[bool, str]:
        """Tests connection to the broker and updates status."""
        import threading
        config = custom_config or self.get_config()
        client_id = f"iploom_test_{int(time.time())}"
        client = get_mqtt_client(client_id)
        
        logger.info(f"Testing MQTT connection to {config['broker']}:{config['port']}")
        
        if config.get('username'):
            client.username_pw_set(config['username'], config.get('password'))
            
        connect_event = threading.Event()
        result = {"success": False, "error": "Connection timeout"}

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                result["success"] = True
                result["error"] = None
            else:
                result["success"] = False
                result["error"] = f"Connection failed with code {rc}"
            connect_event.set()

        client.on_connect = on_connect
            
        try:
            self.last_test_time = time.time()
            logger.info(f"Connecting to MQTT broker at {config['broker']}:{config['port']}...")
            client.connect(config['broker'], config['port'], keepalive=5)
            client.loop_start()
            
            # Wait for connection or timeout (2 seconds)
            if connect_event.wait(timeout=2.0):
                if result["success"]:
                    logger.info("MQTT connection test successful.")
                    client.disconnect()
                    client.loop_stop()
                    if not custom_config:
                        self._save_status("online")
                    return True, "Connected successfully"
                else:
                    logger.warning(f"MQTT connection test failed: {result['error']}")
                    client.loop_stop()
                    if not custom_config:
                        self._save_status("offline", result["error"])
                    return False, result["error"]
            else:
                logger.warning("MQTT connection test timed out.")
                client.loop_stop()
                if not custom_config:
                    self._save_status("offline", "Connection timeout")
                return False, "Connection timeout"
        except Exception as e:
            logger.error(f"MQTT connection test exception: {e}")
            if not custom_config:
                self._save_status("offline", str(e))
            return False, str(e)

    def check_health(self):
        """Periodic health check for MQTT broker."""
        now = time.time()
        # Only check every 60 seconds
        if now - self.last_test_time < 60:
            return

        self.last_test_time = now
        
        if self._client and self._client.is_connected():
            logger.debug("MQTT health check: Persistent client is connected.")
            self.is_reachable = True
            self._save_status("online")
        elif self._client:
            # Client exists, but disconnected. Paho's background loop is handling it.
            # We don't want to call _connect_persistent or test_connection here,
            # as that would create a competing second connection (Client ID war).
            logger.debug("MQTT health check: Client is currently disconnected. Relying on auto-reconnect loop.")
            self.is_reachable = False
            # Check if we should update DB status to offline if it's been down a while
            if self.last_status == "online":
                self._save_status("offline", "Connection lost; auto-reconnecting...")
        else:
            # No client at all, try to initialize it
            logger.info("MQTT health check: No persistent client found. Initializing...")
            self._connect_persistent()

    def publish(self, topic: str, payload: Any, retain: bool = False):
        if not self._client or not self._client.is_connected():
            self._connect_persistent()
            
        if not self.is_reachable:
            logger.debug(f"Skipping MQTT publish to {topic} because broker is offline/unreachable")
            return
            
        try:
            msg = payload if isinstance(payload, str) else json.dumps(payload)
            logger.info(f"Publishing to {topic} (retain={retain})...")
            # Quality of Service 1 ensures delivery, but we don't wait_for_publish
            # to avoid blocking the caller's thread indefinitely
            self._client.publish(topic, msg, retain=retain, qos=1)
            logger.debug(f"Queued publish to {topic}")
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            # Don't mark offline immediately if it's just one publish failure,
            # but if it's a connection issue, _client.is_connected() will catch it next time.

def publish_mqtt(topic: str, payload: Any, retain: bool = False):
    MQTTManager.get_instance().publish(topic, payload, retain=retain)

def publish_ha_discovery(device_info: dict):
    config = MQTTManager.get_instance().get_config()
    mac = device_info.get("mac")
    if not mac: return
    
    unique_id = f"iploom_{mac.replace(':', '').lower()}"
    discovery_topic = f"homeassistant/device_tracker/{unique_id}/config"
    
    discovery_payload = {
        "name": device_info.get("hostname") or f"Device {mac}",
        "unique_id": unique_id,
        "state_topic": f"{config['base_topic']}/devices/{unique_id}/status",
        "json_attributes_topic": f"{config['base_topic']}/devices/{unique_id}/attributes",
        "payload_home": "online",
        "payload_not_home": "offline",
        "icon": f"mdi:{device_info.get('icon', 'help-circle')}" if device_info.get('icon') else "mdi:lan-connect",
        "device": {
            "identifiers": [unique_id],
            "name": device_info.get("hostname") or f"Device {mac}",
            "manufacturer": device_info.get("vendor"),
            "model": "Network Device",
            "connections": [["mac", mac]]
        }
    }
    
    publish_mqtt(discovery_topic, discovery_payload, retain=True)

def publish_device_status(device_info: dict, status: str):
    config = MQTTManager.get_instance().get_config()
    mac = device_info.get("mac")
    if not mac:
        return

    key = mac.replace(":", "").lower()
    base_topic = config['base_topic']
    
    state_topic = f"{base_topic}/devices/iploom_{key}/status"
    # Also publish to generic topic for HA compatibility if needed, 
    # but let's stick to the discovery config structure:
    # state_topic: f"{config['base_topic']}/devices/{unique_id}/status"
    
    state_val = "online" if status == "online" else "offline"
    publish_mqtt(state_topic, state_val, retain=True)
    
    # Publish attributes
    attr_topic = f"{base_topic}/devices/iploom_{key}/attributes"
    # Filter out internal DB fields and format for HA
    last_seen = device_info.get("last_seen")
    if hasattr(last_seen, 'isoformat'):
        last_seen_str = last_seen.isoformat()
    else:
        last_seen_str = str(last_seen or "")

    ha_attributes = {
        "ip_address": device_info.get("ip"),
        "mac_address": device_info.get("mac"),
        "name": device_info.get("hostname"),
        "vendor": device_info.get("vendor"),
        "type": device_info.get("device_type"),
        "ip_type": device_info.get("ip_type"),
        "last_seen": last_seen_str,
        "scanner": "IPLoom"
    }
    publish_mqtt(attr_topic, ha_attributes, retain=True)
    
    if status == "online":
        publish_ha_discovery(device_info)

def publish_device_online(device_info: dict):
    publish_device_status(device_info, "online")

def publish_device_offline(device_info: dict):
    publish_device_status(device_info, "offline")
