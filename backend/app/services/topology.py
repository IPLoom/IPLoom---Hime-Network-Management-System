import logging
from typing import Dict, Any, List
from app.core.db import get_connection
from app.core.dns_db import get_dns_connection

logger = logging.getLogger(__name__)

class TopologyService:
    def get_graph(self) -> Dict[str, Any]:
        """
        Generates a graph representation of the network.
        Currently implements a simple Star Topology (Gateway -> Devices).
        """
        conn = get_connection()
        try:
            # Fetch all active devices with latest traffic rates (last 10 mins)
            # We use QUALIFY row_number() to get the most recent rate per device
            sql = """
                SELECT 
                    d.id, d.ip, d.mac, d.display_name, d.device_type, d.vendor, d.status, d.icon, d.parent_id,
                    COALESCE(t.down_rate, 0) as down_rate,
                    COALESCE(t.up_rate, 0) as up_rate,
                    d.last_seen
                FROM devices d
                LEFT JOIN (
                    SELECT device_id, down_rate, up_rate, timestamp
                    FROM device_traffic_history
                    WHERE timestamp >= current_timestamp - interval '10 minutes'
                    QUALIFY row_number() OVER (PARTITION BY device_id ORDER BY timestamp DESC) = 1
                ) t ON d.id = t.device_id
                ORDER BY d.ip
            """
            rows = conn.execute(sql).fetchall()
            
            # Fetch DNS block counts in the last hour
            block_counts = {}
            try:
                dns_conn = get_dns_connection()
                dns_rows = dns_conn.execute("""
                    SELECT device_id, COUNT(*) 
                    FROM dns_logs 
                    WHERE is_blocked = TRUE AND timestamp >= current_timestamp - interval '1 hour'
                    GROUP BY device_id
                """).fetchall()
                block_counts = {r[0]: r[1] for r in dns_rows}
            except Exception as e:
                logger.warning(f"Failed to fetch DNS block counts for topology: {e}")
            
            nodes = {}
            edges = {}
            
            # 1. Identify or Create Gateway
            gateway_id = "gateway_node"
            gateway_ip = None
            
            # Try to find a real gateway (usually .1)
            for row in rows:
                ip = row[1]
                if ip and ip.endswith('.1'):
                    gateway_id = row[0]
                    gateway_ip = ip
                    break
            
            # If no real gateway found, add a virtual one
            if gateway_id == "gateway_node":
                nodes[gateway_id] = {
                    "name": "Router / Gateway",
                    "type": "Router",
                    "status": "online",
                    "ip": "Unknown",
                    "icon": "Router",
                    "down_rate": 0,
                    "up_rate": 0,
                    "last_seen": None,
                    "block_count": 0,
                    "open_ports": []
                }

            # Fetch all open ports
            ports_rows = conn.execute("SELECT device_id, port, protocol, service FROM device_ports").fetchall()
            ports_by_device = {}
            for pr in ports_rows:
                d_id, port, proto, svc = pr
                if d_id not in ports_by_device:
                    ports_by_device[d_id] = []
                ports_by_device[d_id].append({"port": port, "protocol": proto, "service": svc})

            # 2. Build Nodes
            for row in rows:
                dev_id, ip, mac, name, dev_type, vendor, status, icon, parent_id, down_rate, up_rate, last_seen = row
                
                # Infer icon from type if not set
                if not icon:
                    icon = self._get_icon_for_type(dev_type)

                # Add Node
                nodes[dev_id] = {
                    "name": name or ip,
                    "type": dev_type or "Unknown",
                    "vendor": vendor,
                    "status": status,
                    "ip": ip,
                    "mac": mac,
                    "icon": icon or "HelpCircle",
                    "parent_id": parent_id,
                    "down_rate": down_rate,
                    "up_rate": up_rate,
                    "last_seen": last_seen.isoformat() if last_seen else None,
                    "block_count": block_counts.get(dev_id, 0),
                    "open_ports": ports_by_device.get(dev_id, [])
                }

            # 3. Build Edges
            for dev_id, node in nodes.items():
                if dev_id == gateway_id:
                    continue
                
                # Use explicit parent_id if it exists and exists in nodes
                parent = node.get("parent_id")
                if parent and parent in nodes:
                    source_id = parent
                else:
                    source_id = gateway_id
                
                edge_id = f"edge_{source_id}_{dev_id}"
                edges[edge_id] = {
                    "source": source_id,
                    "target": dev_id,
                    "label": "" 
                }

            return {"nodes": nodes, "edges": edges}

        except Exception as e:
            logger.error(f"Failed to generate topology: {e}")
            return {"nodes": {}, "edges": {}}
        finally:
            conn.close()

    def _get_icon_for_type(self, dev_type: str) -> str:
        if not dev_type:
            return None
        
        dt = dev_type.lower()
        if "param" in dt: return None # Ignore internal types
        
        mapping = {
            "mobile": "Smartphone",
            "phone": "Smartphone",
            "android": "Smartphone",
            "iphone": "Smartphone",
            "tablet": "Tablet",
            "ipad": "Tablet",
            "desktop": "Desktop",
            "computer": "Desktop",
            "pc": "Desktop",
            "server": "Server",
            "laptop": "Laptop",
            "macbook": "Laptop",
            "printer": "Printer",
            "tv": "Tv",
            "television": "Tv",
            "camera": "Camera",
            "webcam": "Camera",
            "game": "Gamepad",
            "console": "Gamepad",
            "xbox": "Gamepad",
            "playstation": "Gamepad",
            "nintendo": "Gamepad",
            "watch": "Watch",
            "wearable": "Watch",
            "speaker": "Speaker",
            "audio": "Speaker",
            "alexa": "Speaker",
            "google home": "Speaker",
            "router": "Router",
            "gateway": "Router",
            "access point": "Wifi",
            "ap": "Wifi",
            "switch": "Server"
        }
        
        for key, icon in mapping.items():
            if key in dt:
                return icon
        
        return None
