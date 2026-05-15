import duckdb
import shutil
import json
import uuid
from pathlib import Path
from app.core.config import get_settings
import logging
import threading

logger = logging.getLogger(__name__)

_shared_conn: duckdb.DuckDBPyConnection = None
_db_lock = threading.RLock()

def get_db_lock():
    """Returns the global database lock for maintenance operations."""
    return _db_lock

def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a cursor from a shared DuckDB connection.
    This pattern is much more stable on Windows to prevent 'Database is locked' errors.
    The shared connection handles the file lock, and each call returns a thread-safe cursor.
    """
    global _shared_conn
    with _db_lock:
        if _shared_conn is None:
            settings = get_settings()
            db_path = Path(settings.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Open the master connection for the process
            _shared_conn = duckdb.connect(str(db_path))
            
            # Optimize DuckDB for concurrency and consistency
            _shared_conn.execute("SET threads TO 4")
            _shared_conn.execute("SET memory_limit = '512MB'")
            _shared_conn.execute("SET TimeZone='UTC'")
            # Persistent settings for consistency
            _shared_conn.execute("PRAGMA checkpoint_threshold='10MB'")
        
        # Return a cursor based on the master connection
        return _shared_conn.cursor()

def close_shared_connection():
    """Closes the global shared connection. Useful for operations like restore or backup."""
    global _shared_conn
    with _db_lock:
        if _shared_conn:
            try:
                _shared_conn.close()
                logger.info("Shared database connection closed.")
            except Exception as e:
                logger.error(f"Error closing shared connection: {e}")
            _shared_conn = None

def commit(conn=None) -> None:
    """
    Commits the global shared connection. 
    The 'conn' argument is accepted for backward compatibility but ignored.
    """
    global _shared_conn
    with _db_lock:
        if _shared_conn:
            _shared_conn.commit()

def init_db() -> None:
    settings = get_settings()
    print(f"Initializing database at {settings.db_path}...")
    
    conn = get_connection()
    try:
        if settings.db_init_mode == "recreate":
            print("Recreating database tables...")
            conn.execute("""
                DROP TABLE IF EXISTS scan_schedules;
                DROP TABLE IF EXISTS device_ports;
                DROP TABLE IF EXISTS devices;
                DROP TABLE IF EXISTS scan_results;
                DROP TABLE IF EXISTS scans;
                DROP TABLE IF EXISTS config;
                DROP TABLE IF EXISTS classification_rules;
            """)

        print(f"Loading schema from {settings.db_schema_path}...")
        schema_sql = Path(settings.db_schema_path).read_text(encoding="utf-8")
        conn.execute(schema_sql)
        
        # Migrations
        migrate_db(conn)
        
        # Seeding
        seed_classification_rules(conn)
        
        print("Database initialized successfully.")
        commit()
    except Exception as e:
        print(f"ERROR during database initialization: {e}")
        raise e
    finally:
        conn.close()

def migrate_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Adds missing columns to existing tables."""
    settings = get_settings()
    # Check if vendor/icon exist in devices
    cols = conn.execute("PRAGMA table_info('devices')").fetchall()
    col_names = [c[1] for c in cols]
    
    if 'vendor' not in col_names:
        print("Migration: Adding 'vendor' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN vendor TEXT")
    
    if 'icon' not in col_names:
        print("Migration: Adding 'icon' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN icon TEXT")

    if 'open_ports' not in col_names:
        print("Migration: Adding 'open_ports' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN open_ports TEXT")

    if 'status' not in col_names:
        print("Migration: Adding 'status' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN status TEXT DEFAULT 'unknown'")

    if 'ip_type' not in col_names:
        print("Migration: Adding 'ip_type' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN ip_type TEXT")

    if 'is_trusted' not in col_names:
        print("Migration: Adding 'is_trusted' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN is_trusted BOOLEAN DEFAULT FALSE")

    if 'parent_id' not in col_names:
        print("Migration: Adding 'parent_id' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN parent_id TEXT")

    if 'dns_stats' not in col_names:
        print("Migration: Adding 'dns_stats' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN dns_stats JSON")

    if 'missing_count' not in col_names:
        print("Migration: Adding 'missing_count' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN missing_count INTEGER DEFAULT 0")

    # Ensure device_status_history table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS device_status_history (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            status TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure device_traffic_history table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS device_traffic_history (
            id          TEXT PRIMARY KEY,
            device_id   TEXT NOT NULL,
            timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rx_bytes    BIGINT NOT NULL DEFAULT 0,
            tx_bytes    BIGINT NOT NULL DEFAULT 0,
            down_rate   BIGINT DEFAULT 0, 
            up_rate     BIGINT DEFAULT 0
        )
    """)

    # Migration for device_ports UNIQUE constraint
    # DuckDB doesn't allow adding UNIQUE to existing tables.
    # We check if it exists by looking at indexes or trying a dummy insert (or just check table_info if supported)
    # Safer: check if we've already run this migration using a config key or checking schema
    # PRAGMA table_info doesn't show UNIQUE easily, but we can check the table definition
    master = conn.execute("SELECT sql FROM sqlite_master WHERE name = 'device_ports'").fetchone()
    if master and "UNIQUE" not in master[0]:
        print("Migration: Adding UNIQUE constraint to 'device_ports'")
        # Ensure we start fresh
        conn.execute("DROP TABLE IF EXISTS device_ports_new")
        conn.execute("""
            CREATE TABLE device_ports_new (
                device_id  TEXT NOT NULL,
                port       INTEGER NOT NULL,
                protocol   TEXT NOT NULL,
                service    TEXT,
                banner     TEXT,
                last_seen  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, port, protocol)
            );
        """)
        # De-duplicate: Keep the most recent last_seen and any service/banner
        conn.execute("""
            INSERT INTO device_ports_new (device_id, port, protocol, service, banner, last_seen)
            SELECT device_id, port, protocol, arg_max(service, last_seen), arg_max(banner, last_seen), MAX(last_seen)
            FROM device_ports
            GROUP BY device_id, port, protocol
        """)
        conn.execute("DROP TABLE device_ports")
        conn.execute("ALTER TABLE device_ports_new RENAME TO device_ports")
    
    # 3. Normalize protocol to lowercase and deduplicate
    try:
        current_data = conn.execute("SELECT device_id, port, protocol FROM device_ports").fetchall()
        has_uppercase = any(d[2] != d[2].lower() for d in current_data)
        
        if has_uppercase:
            print("Migration: Normalizing protocols to lowercase and deduplicating...")
            # We'll use a temporary table to deduplicate
            conn.execute("CREATE TABLE device_ports_dedup (device_id TEXT, port INTEGER, protocol TEXT, service TEXT, banner TEXT, last_seen TIMESTAMP, UNIQUE(device_id, port, protocol))")
            
            # Insert with REPLACE to keep the latest service name/time for the lowercase version
            conn.execute("""
                INSERT OR REPLACE INTO device_ports_dedup (device_id, port, protocol, service, banner, last_seen)
                SELECT device_id, port, LOWER(protocol), service, banner, last_seen
                FROM device_ports
                ORDER BY last_seen ASC
            """)
            
            conn.execute("DROP TABLE device_ports")
            conn.execute("ALTER TABLE device_ports_dedup RENAME TO device_ports")
            print("Migration: Protocols normalized successfully.")
    except Exception as e:
        print(f"Migration error (normalization): {e}")

    # 4. Indexes for Performance (Idempotent)
    # DuckDB CREATE INDEX IF NOT EXISTS is supported in newer versions, checking explicitly or using try/except block is safer if unsure of version match
    try:
        print("Migration: Checking/Creating indexes...")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_device_id ON device_status_history(device_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_changed_at ON device_status_history(changed_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_traffic_device_id ON device_traffic_history(device_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON device_traffic_history(timestamp)")
        
        # Scan Results Indexes (for Fidelity / History)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_results_scan_id ON scan_results(scan_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_results_mac ON scan_results(mac)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_results_ip ON scan_results(ip)")

        # Also index devices table for faster lookups if not primary key (id is PK, so indexed)
        # conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac)") # mac is part of logic but often via ID.
    except Exception as e:
        print(f"Migration error (indexes): {e}")

    # 5. Ensure classification_rules table exists (added redundantly to schema.sql)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classification_rules (
            id               TEXT PRIMARY KEY,
            name             TEXT NOT NULL,
            pattern_hostname TEXT,
            pattern_vendor   TEXT,
            ports            TEXT,
            device_type      TEXT NOT NULL,
            icon             TEXT NOT NULL,
            priority         INTEGER NOT NULL DEFAULT 100,
            is_builtin       BOOLEAN NOT NULL DEFAULT FALSE,
            updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Ensure users table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            region TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 7. Unified Notifications Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            task_type TEXT,
            event_type TEXT,
            message TEXT NOT NULL,
            level TEXT NOT NULL,
            target TEXT,
            details JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read_at ON notifications(read_at)")
    
    # Ensure custom_assets table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_assets (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            type        TEXT NOT NULL, -- 'brand' or 'device'
            path        TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add brand columns to devices if they don't exist
    try:
        conn.execute("ALTER TABLE devices ADD COLUMN brand TEXT")
    except: pass
    try:
        conn.execute("ALTER TABLE devices ADD COLUMN brand_icon TEXT")
    except: pass

    # Ensure asset directories exist
    assets_dir = Path(settings.assets_dir)
    (assets_dir / "brand_icons").mkdir(parents=True, exist_ok=True)
    (assets_dir / "device_icons").mkdir(parents=True, exist_ok=True)

    seed_custom_assets(conn)
    commit()

def seed_custom_assets(conn: duckdb.DuckDBPyConnection) -> None:
    """Seeds the custom_assets table with default brand mappings and copies files."""
    try:
        settings = get_settings()
        assets_dir = Path(settings.assets_dir)
        brand_dir = assets_dir / "brand_icons"
        brand_dir.mkdir(parents=True, exist_ok=True)

        # Source directory for seed icons.
        # In Docker: baked into image at /app/seed/brand (primary)
        # In development: relative path from source tree (fallback)
        docker_seed_path = Path("/app/seed/brand")
        dev_seed_path = Path(__file__).parent.parent.parent.parent / "ui" / "public" / "brand"
        seed_dir = docker_seed_path if docker_seed_path.exists() else dev_seed_path
        print(f"Brand icon seed source: {seed_dir}")

        # Format: (id, name, type) - filename is resolved by searching for any supported extension
        initial_brands = [
            ("adguard",      "AdGuard Home",    "brand"),
            ("openwrt",      "OpenWrt",          "brand"),
            ("mqtt",         "MQTT",             "brand"),
            ("apple",        "Apple",            "brand"),
            ("google",       "Google",           "brand"),
            ("amazon",       "Amazon",           "brand"),
            ("microsoft",    "Microsoft",        "brand"),
            ("raspberry",    "Raspberry Pi",     "brand"),
            ("ubiquiti",     "Ubiquiti / UniFi", "brand"),
            ("synology",     "Synology",         "brand"),
            ("tplink",       "TP-Link",          "brand"),
            ("philips",      "Philips Hue",      "brand"),
            ("esphome",      "ESPHome",          "brand"),
            ("tasmota",      "Tasmota",          "brand"),
            ("homeassistant","Home Assistant",   "brand"),
            ("sonos",        "Sonos",            "brand"),
        ]
        
        for asset_id, name, asset_type in initial_brands:
            # Check if already seeded
            exists = conn.execute("SELECT 1 FROM custom_assets WHERE id = ?", [asset_id]).fetchone()
            if exists:
                continue

            # Search for the icon file by asset_id with any supported extension
            src = None
            found_ext = None
            for ext in [".svg", ".png", ".jpg", ".jpeg"]:
                candidate = seed_dir / (asset_id + ext)
                if candidate.exists():
                    src = candidate
                    found_ext = ext
                    break

            if not src:
                print(f"Skipping seed for '{name}': No icon found in {seed_dir}")
                continue

            # Copy to persistent storage (Docker volume)
            dest_filename = f"{asset_id}{found_ext}"
            dest = brand_dir / dest_filename
            shutil.copy2(src, dest)

            path = f"/static/brand_icons/{dest_filename}"
            conn.execute(
                "INSERT INTO custom_assets (id, name, type, path) VALUES (?, ?, ?, ?)",
                [asset_id, name, asset_type, path]
            )
            print(f"Seeded brand icon: {name} ({dest_filename})")

    except Exception as e:
        print(f"Error seeding assets: {e}")

def seed_classification_rules(conn: duckdb.DuckDBPyConnection) -> None:
    """Seeds the classification_rules table from initial_rules.json if empty."""
    try:
        count = conn.execute("SELECT count(*) FROM classification_rules").fetchone()[0]
        if count > 0:
            return

        print("Seeding initial classification rules...")
        
        rules_path = Path(__file__).parent.parent / "core" / "initial_rules.json"
        if not rules_path.exists():
            print(f"Warning: {rules_path} not found. Skipping seeding.")
            return
            
        rules_data = json.loads(rules_path.read_text(encoding="utf-8"))
        for rule in rules_data:
            conn.execute(
                """
                INSERT INTO classification_rules (id, name, pattern_hostname, pattern_vendor, ports, device_type, icon, priority, is_builtin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(uuid.uuid4()),
                    rule["name"],
                    rule.get("pattern_hostname"),
                    rule.get("pattern_vendor"),
                    json.dumps(rule.get("ports", [])),
                    rule["device_type"],
                    rule["icon"],
                    rule.get("priority", 100),
                    True # is_builtin
                ]
            )
        commit()
        print(f"Successfully seeded {len(rules_data)} classification rules.")
    except Exception as e:
        print(f"Error seeding classification rules: {e}")
