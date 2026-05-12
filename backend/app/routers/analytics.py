from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.core.db import get_connection
from app.core.dns_db import get_dns_connection
from datetime import datetime, timedelta, timezone
from app.core.date_utils import now as utc_now
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/traffic")
def get_traffic_analytics(range: str = "24h"):
    """
    Returns time-series traffic data aggregated by time buckets.
    range: 24h, yesterday, 7d, 30d, 3m, mtd, last_month, ytd, 1y, all
    """
    conn = get_connection()
    try:
        now = utc_now()
        start_time, end_time, bucket_size, trunc_arg = get_date_range(range, now)

        sql = f"""
            SELECT 
                date_trunc('{trunc_arg}', timestamp) as bucket,
                SUM(down_rate) as download,
                SUM(up_rate) as upload
            FROM device_traffic_history
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY bucket
            ORDER BY bucket ASC
        """
        
        rows = conn.execute(sql, [start_time, end_time]).fetchall()
        
        # Format response
        series = []
        for r in rows:
            series.append({
                "timestamp": r[0],
                "download": r[1],
                "upload": r[2]
            })
            
        # Calculate totals for the period
        totals_row = conn.execute("""
            SELECT 
                SUM(down_rate), 
                SUM(up_rate),
                COUNT(DISTINCT device_id)
            FROM device_traffic_history
            WHERE timestamp >= ? AND timestamp <= ?
        """, [start_time, end_time]).fetchone()
        
        return {
            "series": series,
            "totals": {
                "download": totals_row[0] or 0,
                "upload": totals_row[1] or 0,
                "active_devices": totals_row[2] or 0
            }
        }
    finally:
        conn.close()

@router.get("/top-devices")
def get_top_devices(range: str = "24h", limit: int = 5):
    """
    Returns top consumers by total usage in the time window.
    """
    conn = get_connection()
    try:
        start_time, end_time, _, _ = get_date_range(range)
        
        sql = """
            SELECT 
                d.id, d.name, d.display_name, d.ip, d.icon, d.vendor,
                SUM(h.down_rate) as total_down,
                SUM(h.up_rate) as total_up,
                (SUM(h.down_rate) + SUM(h.up_rate)) as total_usage
            FROM device_traffic_history h
            JOIN devices d ON h.device_id = d.id
            WHERE h.timestamp >= ? AND h.timestamp <= ?
            GROUP BY d.id, d.name, d.display_name, d.ip, d.icon, d.vendor
            ORDER BY total_usage DESC
            LIMIT ?
        """
        
        rows = conn.execute(sql, [start_time, end_time, limit]).fetchall()
        
        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "name": r[2] or r[1],
                "ip": r[3],
                "icon": r[4],
                "vendor": r[5],
                "download": r[6],
                "upload": r[7],
                "total": r[8]
            })
            
        return items
    finally:
        conn.close()

@router.get("/usage-details")
def get_usage_details(range: str = "24h", page: int = 1, limit: int = 10):
    """
    Returns paginated device usage details.
    """
    conn = get_connection()
    try:
        start_time, end_time, _, _ = get_date_range(range)

        offset = (page - 1) * limit

        # Base Query
        base_query = """
            FROM device_traffic_history h
            JOIN devices d ON h.device_id = d.id
            WHERE h.timestamp >= ? AND h.timestamp <= ?
        """

        # Total Count
        count_sql = f"SELECT COUNT(DISTINCT d.id) {base_query}"
        total_items = conn.execute(count_sql, [start_time, end_time]).fetchone()[0]
        total_pages = (total_items + limit - 1) // limit

        # Paginated Data
        data_sql = f"""
            SELECT 
                d.id, d.name, d.display_name, d.ip, d.icon, d.vendor, d.mac,
                SUM(h.down_rate) as total_down,
                SUM(h.up_rate) as total_up,
                (SUM(h.down_rate) + SUM(h.up_rate)) as total_usage,
                MAX(h.timestamp) as last_seen
            {base_query}
            GROUP BY d.id, d.name, d.display_name, d.ip, d.icon, d.vendor, d.mac
            ORDER BY total_usage DESC
            LIMIT ? OFFSET ?
        """
        
        rows = conn.execute(data_sql, [start_time, end_time, limit, offset]).fetchall()
        
        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "name": r[2] or r[1],
                "ip": r[3],
                "icon": r[4],
                "vendor": r[5],
                "mac": r[6],
                "download": r[7],
                "upload": r[8],
                "total": r[9],
                "last_seen": r[10]
            })
            
        return {
            "items": items,
            "total": total_items,
            "page": page,
            "pages": total_pages
        }
    finally:
        conn.close()

@router.get("/distribution")
def get_device_distribution():
    """
    Returns breakdown of devices by Vendor and Type.
    """
    conn = get_connection()
    try:
        # Vendor Distribution (Top 5 + Others)
        vendor_rows = conn.execute("""
            SELECT vendor, COUNT(*) as count
            FROM devices
            WHERE vendor IS NOT NULL AND vendor != '' AND vendor != 'Unknown'
            GROUP BY vendor
            ORDER BY count DESC
        """).fetchall()
        
        vendors = []
        other_count = 0
        for i, r in enumerate(vendor_rows):
            if i < 5:
                vendors.append({"label": r[0], "value": r[1]})
            else:
                other_count += r[1]
                
        if other_count > 0:
            vendors.append({"label": "Others", "value": other_count})
            
        # Device Type Distribution
        type_rows = conn.execute("""
            SELECT device_type, COUNT(*) as count
            FROM devices
            WHERE device_type IS NOT NULL AND device_type != ''
            GROUP BY device_type
            ORDER BY count DESC
        """).fetchall()
        
        types = [{"label": r[0].capitalize(), "value": r[1]} for r in type_rows]
        
        return {
            "vendors": vendors,
            "types": types
        }
    finally:
        conn.close()

@router.get("/category-usage")
def get_category_usage(range: str = "24h"):
    """
    Returns total traffic volume aggregated by device type.
    """
    conn = get_connection()
    try:
        start_time, end_time, _, _ = get_date_range(range)
        
        sql = """
            SELECT 
                d.device_type,
                SUM(h.down_rate) as total_down,
                SUM(h.up_rate) as total_up,
                (SUM(h.down_rate) + SUM(h.up_rate)) as total_usage
            FROM device_traffic_history h
            JOIN devices d ON h.device_id = d.id
            WHERE h.timestamp >= ? AND h.timestamp <= ? AND d.device_type IS NOT NULL AND d.device_type != ''
            GROUP BY d.device_type
            ORDER BY total_usage DESC
        """
        
        rows = conn.execute(sql, [start_time, end_time]).fetchall()
        
        items = []
        for r in rows:
            items.append({
                "label": r[0].capitalize(),
                "download": r[1],
                "upload": r[2],
                "total": r[3]
            })
            
        return items
    finally:
        conn.close()

@router.get("/heatmap")
def get_traffic_heatmap(time_range: str = Query("24h", alias="range")):
    """
    Returns aggregated traffic volume by Day of Week and Hour of Day,
    including top 3 devices contributing to each bucket.
    """
    conn = get_connection()
    try:
        start_time, end_time, _, _ = get_date_range(time_range)
        
        # Optimized Fetch: Group by Dow, Hour, AND Device
        # This lets us calculate totals AND find top contributors in one pass
        sql = """
            SELECT 
                extract('isodow' from h.timestamp) as dow,
                extract('hour' from h.timestamp) as h,
                h.device_id,
                d.name,
                d.display_name,
                SUM(h.down_rate + h.up_rate) as total
            FROM device_traffic_history h
            LEFT JOIN devices d ON h.device_id = d.id
            WHERE h.timestamp >= ? AND h.timestamp <= ?
            GROUP BY extract('isodow' from h.timestamp), extract('hour' from h.timestamp), h.device_id, d.name, d.display_name
        """
        
        rows = conn.execute(sql, [start_time, end_time]).fetchall()
        
        # Python Aggregation
        # matrix[d][h] = { total: 0, devices: [] }
        matrix = [[{"total": 0, "devices": []} for _ in range(24)] for _ in range(7)]
        
        # Temp storage to aggregate per bucket before sorting
        # bucket_map[(d, h)] = [ {name, val}, ... ]
        bucket_devices = {}

        for r in rows:
            if r[0] is not None and r[1] is not None:
                d_idx = int(r[0]) - 1 # 0-6
                h_idx = int(r[1])     # 0-23
                if 0 <= d_idx <= 6 and 0 <= h_idx <= 23:
                    val = r[5] or 0
                    device_name = r[4] or r[3] or "Unknown"
                    
                    # Add to total
                    matrix[d_idx][h_idx]["total"] += val
                    
                    # Add to device list
                    key = (d_idx, h_idx)
                    if key not in bucket_devices: bucket_devices[key] = []
                    bucket_devices[key].append({"name": device_name, "value": val})

        # Sort and pick top 3 for each bucket
        for (d, h), devices in bucket_devices.items():
            # Sort by value desc
            devices.sort(key=lambda x: x["value"], reverse=True)
            matrix[d][h]["devices"] = devices[:3]

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        series = []
        
        for i, day in enumerate(days):
            data_points = []
            for h in range(24):
                cell = matrix[i][h]
                data_points.append({
                    "x": f"{h:02d}:00", 
                    "y": cell["total"],
                    "top": cell["devices"] # Pass top devices to frontend
                })
            series.append({"name": day, "data": data_points})
            
        return series
    finally:
        conn.close()

# --- DNS Analytics ---

@router.get("/dns/stats")
def get_dns_global_stats(range: str = "24h"):
    """
    Returns KPIs: Total Queries, Blocked, Block %, Avg Response Time
    """
    conn = get_dns_connection()
    # Note: get_dns_connection returns a cursor on a shared connection.
    # We do NOT close it.
    
    start_time, end_time, _, _ = get_date_range(range)
    
    try:
        # Total & Blocked
        row = conn.execute("""
            SELECT 
                COUNT(*), 
                COUNT(CASE WHEN is_blocked = TRUE THEN 1 END),
                AVG(response_time)
            FROM dns_logs
            WHERE timestamp >= ? AND timestamp <= ?
        """, [start_time, end_time]).fetchone()
        
        total = row[0] or 0
        blocked = row[1] or 0
        avg_time = row[2] or 0
        
        block_pct = (blocked / total * 100) if total > 0 else 0
        
        return {
            "total_queries": total,
            "blocked_queries": blocked,
            "block_percentage": round(block_pct, 2),
            "avg_response_time": round(avg_time, 2)
        }
    except Exception as e:
        logger.error(f"DNS Stats Error: {e}")
        return {"total_queries": 0, "blocked_queries": 0, "block_percentage": 0, "avg_response_time": 0}

@router.get("/dns/traffic")
def get_dns_traffic_chart(range: str = "24h"):
    """
    Time series of Queries vs Blocked
    """
    conn = get_dns_connection()
    start_time, end_time, _, trunc = get_date_range(range)
    
    try:
        rows = conn.execute(f"""
            SELECT 
                date_trunc('{trunc}', timestamp) as bucket,
                COUNT(*) as total,
                COUNT(CASE WHEN is_blocked = TRUE THEN 1 END) as blocked
            FROM dns_logs
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY bucket
            ORDER BY bucket ASC
        """, [start_time, end_time]).fetchall()
        
        series = []
        for r in rows:
            series.append({
                "timestamp": r[0],
                "total": r[1],
                "blocked": r[2]
            })
            
        return series
    except Exception as e:
        logger.error(f"DNS Chart Error: {e}")
        return []

@router.get("/dns/top-domains")
def get_dns_top_domains(range: str = "24h", limit: int = 10, offset: int = 0, type: str = "all"):
    """
    Top queried domains. type: 'all', 'blocked', 'allowed'
    """
    conn = get_dns_connection()
    start_time, end_time, _, _ = get_date_range(range)
    
    where_clause = "WHERE l.timestamp >= ? AND l.timestamp <= ?"
    if type == "blocked":
        where_clause += " AND l.is_blocked = TRUE"
    elif type == "allowed":
        where_clause += " AND l.is_blocked = FALSE"
        
    try:
        rows = conn.execute(f"""
            SELECT 
                d.domain,
                d.category,
                COUNT(*) as count,
                MODE(l.device_id) as top_device_id
            FROM dns_logs l
            JOIN dns_domains d ON l.domain_id = d.id
            {where_clause}
            GROUP BY d.domain, d.category
            ORDER BY count DESC
            LIMIT ? OFFSET ?
        """, [start_time, end_time, limit, offset]).fetchall()
        
        # Resolve names for top devices
        conn_main = get_connection()
        device_ids = list(set(r[3] for r in rows if r[3]))
        device_map = {}
        if device_ids:
            # Simple list query
            dev_rows = conn_main.execute(f"SELECT id, name, display_name, icon, device_type FROM devices WHERE id IN ({','.join(['?']*len(device_ids))})", device_ids).fetchall()
            for dr in dev_rows:
                device_map[dr[0]] = {
                    "name": dr[2] or dr[1],
                    "icon": dr[3],
                    "type": dr[4]
                }

        return [{
            "domain": r[0], 
            "category": r[1], 
            "count": r[2],
            "top_client_id": r[3],
            "top_client_name": device_map.get(r[3], {}).get("name", "Unknown Device"),
            "top_client_icon": device_map.get(r[3], {}).get("icon"),
            "top_client_type": device_map.get(r[3], {}).get("type")
        } for r in rows]
    except Exception as e:
        logger.error(f"DNS Top Domains Error: {e}")
        return []

@router.get("/dns/top-clients")
def get_dns_top_clients(range: str = "24h", limit: int = 10, offset: int = 0):
    """
    Top clients by query volume.
    """
    # map device_id to names using Main DB is best, but we are in shared connection mode.
    # Option: Return device_ids and let frontend resolve names from store?
    # Or fetch device mapping from main DB here? 
    # Let's fetch map from main DB.
    
    conn_dns = get_dns_connection()
    conn_main = get_connection()
    start_time, end_time, _, _ = get_date_range(range)
    
    try:
        # Get stats
        rows = conn_dns.execute("""
            SELECT device_id, client_ip, COUNT(*) as count
            FROM dns_logs
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY device_id, client_ip
            ORDER BY count DESC
            LIMIT ? OFFSET ?
        """, [start_time, end_time, limit, offset]).fetchall()
        
        # Resolve names
        results = []
        device_cache = {}
        
        for r in rows:
            dev_id = r[0]
            ip = r[1]
            count = r[2]
            name = ip 
            
            if dev_id:
                if dev_id not in device_cache:
                    d_row = conn_main.execute("SELECT name, display_name FROM devices WHERE id = ?", [dev_id]).fetchone()
                    if d_row:
                        device_cache[dev_id] = d_row[1] or d_row[0]
                
                if dev_id in device_cache:
                    name = device_cache[dev_id]
            
            results.append({"name": name, "count": count, "device_id": dev_id})
            
        return results
    except Exception as e:
        logger.error(f"DNS Top Clients Error: {e}")
        return []
    finally:
        conn_main.close()

def get_date_range(range_str: str, now: Optional[datetime] = None):
    if not now:
        now = utc_now()
    
    # Defaults
    start = now - timedelta(hours=24)
    end = now
    bucket = "1 hour"
    trunc = "hour"

    if range_str == "24h":
        start = now - timedelta(hours=24)
        bucket = "1 hour"
        trunc = "hour"
    elif range_str == "yesterday":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        bucket = "1 hour"
        trunc = "hour"
    elif range_str == "7d":
        start = now - timedelta(days=7)
        bucket = "6 hours"
        trunc = "hour"
    elif range_str == "30d":
        start = now - timedelta(days=30)
        bucket = "1 day"
        trunc = "day"
    elif range_str == "3m":
        start = now - timedelta(days=90)
        bucket = "1 week"
        trunc = "week" # DuckDB supports week? Yes uses isodow or similar, but date_trunc('week',...) works usually
    elif range_str == "mtd":
        start = datetime(now.year, now.month, 1)
        bucket = "1 day"
        trunc = "day"
    elif range_str == "last_month":
        # First day of this month
        this_month_first = datetime(now.year, now.month, 1)
        # Last day of prev month = this_month_first - resolution
        end = this_month_first - timedelta(seconds=1)
        # First day of prev month
        start = datetime(end.year, end.month, 1)
        bucket = "1 day"
        trunc = "day"
    elif range_str == "ytd":
        start = datetime(now.year, 1, 1)
        bucket = "1 month"
        trunc = "month" # date_trunc('month',...)
    elif range_str == "1y":
        start = now - timedelta(days=365)
        bucket = "1 month"
        trunc = "month"
    elif range_str == "all":
        start = datetime(2020, 1, 1) # Arbitrary old date
        bucket = "1 month"
        trunc = "month"

    return start, end, bucket, trunc

@router.get("/dns/stats/{device_id}")
def get_device_dns_stats(device_id: str, range: str = "24h"):
    """
    Returns KPIs for a specific device.
    """
    logger.debug(f"Fetching DNS stats for device: {device_id} (range: {range})")
    conn = get_dns_connection()
    start_time, end_time, _, _ = get_date_range(range)
    
    # Get the device IP for fallback matching (incase device_id was NULL during sync)
    conn_main = get_connection()
    dev_row = conn_main.execute("SELECT ip FROM devices WHERE id = ?", [device_id]).fetchone()
    device_ip = dev_row[0] if dev_row else None
    
    where_clause = "(device_id = ?"
    params = [device_id]
    if device_ip:
        where_clause += " OR client_ip = ?"
        params.append(device_ip)
    where_clause += ")"

    try:
        # 1. Total & Blocked
        res = conn.execute(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_blocked = TRUE THEN 1 END) as blocked,
                AVG(response_time) as avg_latency
            FROM dns_logs
            WHERE {where_clause} AND timestamp >= ? AND timestamp <= ?
        """, params + [start_time, end_time]).fetchone()
        
        total = res[0] or 0
        blocked = res[1] or 0
        avg_latency = float(res[2] or 0)
        
        return {
            "total": total,
            "blocked": blocked,
            "block_rate": round((blocked / total * 100), 1) if total > 0 else 0,
            "avg_latency": round(avg_latency, 1)
        }
    except Exception as e:
        logger.error(f"Device DNS Stats Error: {e}")
        return {
            "total": 0,
            "blocked": 0,
            "block_rate": 0,
            "avg_latency": 0
        }
    finally:
        conn.close()
        conn_main.close()

@router.get("/dns/logs/{device_id}/count")
def get_device_dns_logs_count(device_id: str):
    """
    Returns total count of DNS logs for a specific device.
    """
    conn = get_dns_connection()
    conn_main = get_connection()
    dev_row = conn_main.execute("SELECT ip FROM devices WHERE id = ?", [device_id]).fetchone()
    device_ip = dev_row[0] if dev_row else None

    where_clause = "(device_id = ?"
    params = [device_id]
    if device_ip:
        where_clause += " OR client_ip = ?"
        params.append(device_ip)
    where_clause += ")"

    try:
        res = conn.execute(f"SELECT COUNT(*) FROM dns_logs WHERE {where_clause}", params).fetchone()
        return {"total": res[0] or 0}
    except Exception as e:
        logger.error(f"Error fetching DNS logs count: {e}")
        return {"total": 0}
    finally:
        conn.close()
        conn_main.close()

@router.get("/dns/logs/{device_id}")
def get_device_dns_logs(device_id: str, limit: int = 50, offset: int = 0):
    """
    Returns recent DNS queries for a specific device.
    """
    logger.debug(f"Fetching DNS logs for device: {device_id} (limit: {limit})")
    conn = get_dns_connection()
    # Fallback IP matching
    conn_main = get_connection()
    dev_row = conn_main.execute("SELECT ip FROM devices WHERE id = ?", [device_id]).fetchone()
    device_ip = dev_row[0] if dev_row else None

    where_clause = "(device_id = ?"
    params = [device_id]
    if device_ip:
        where_clause += " OR client_ip = ?"
        params.append(device_ip)
    where_clause += ")"

    try:
        # Get logs joined with domains
        rows = conn.execute(f"""
            SELECT 
                l.timestamp,
                d.domain,
                l.status,
                l.response_time,
                l.is_blocked,
                d.category
            FROM dns_logs l
            JOIN dns_domains d ON l.domain_id = d.id
            WHERE {where_clause}
            ORDER BY l.timestamp DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()
        
        return [{
            "timestamp": r[0],
            "domain": r[1],
            "status": r[2],
            "response_time": r[3],
            "is_blocked": bool(r[4]),
            "category": r[5]
        } for r in rows]
    except Exception as e:
        logger.error(f"Device DNS Logs Error: {e}")
        return []
    finally:
        conn.close()
        conn_main.close()

@router.get("/dns/query-types")
def get_dns_query_types(range: str = "24h"):
    """
    Returns breakdown of DNS queries by type (A, AAAA, PTR, etc.)
    """
    conn = get_dns_connection()
    start_time, end_time, _, _ = get_date_range(range)
    try:
        rows = conn.execute("""
            SELECT query_type, COUNT(*) as count
            FROM dns_logs
            WHERE timestamp >= ? AND timestamp <= ? AND query_type IS NOT NULL
            GROUP BY query_type
            ORDER BY count DESC
        """, [start_time, end_time]).fetchall()
        
        return [{"label": r[0], "value": r[1]} for r in rows]
    except Exception as e:
        logger.error(f"DNS Query Types Error: {e}")
        return []
    finally:
        conn.close()

@router.get("/dns/risky-devices")
def get_dns_risky_devices(range: str = "24h", limit: int = 5):
    """
    Returns devices with the highest DNS block rates.
    """
    conn_dns = get_dns_connection()
    conn_main = get_connection()
    start_time, end_time, _, _ = get_date_range(range)
    try:
        # Get devices with at least 10 queries to avoid noise
        rows = conn_dns.execute("""
            SELECT 
                device_id,
                COUNT(*) as total,
                COUNT(CASE WHEN is_blocked = TRUE THEN 1 END) as blocked
            FROM dns_logs
            WHERE timestamp >= ? AND timestamp <= ? AND device_id IS NOT NULL
            GROUP BY device_id
            HAVING total >= 10
            ORDER BY (CAST(blocked AS FLOAT) / total) DESC
            LIMIT ?
        """, [start_time, end_time, limit]).fetchall()
        
        results = []
        for r in rows:
            dev_id, total, blocked = r
            # Resolve name
            d_row = conn_main.execute("SELECT name, display_name, icon, ip FROM devices WHERE id = ?", [dev_id]).fetchone()
            if d_row:
                results.append({
                    "id": dev_id,
                    "name": d_row[1] or d_row[0],
                    "icon": d_row[2],
                    "ip": d_row[3],
                    "total": total,
                    "blocked": blocked,
                    "block_rate": round((blocked / total * 100), 1) if total > 0 else 0
                })
        return results
    except Exception as e:
        logger.error(f"DNS Risky Devices Error: {e}")
        return []
    finally:
        conn_dns.close()
        conn_main.close()

@router.get("/summary")
def get_analytics_summary():
    """
    Consolidated summary for the Dashboard (24h default)
    """
    conn_main = get_connection()
    conn_dns = get_dns_connection()
    
    now = utc_now()
    start_24h = now - timedelta(hours=24)
    
    try:
        # 1. Traffic Totals
        traffic_row = conn_main.execute("""
            SELECT SUM(down_rate), SUM(up_rate)
            FROM device_traffic_history
            WHERE timestamp >= ?
        """, [start_24h]).fetchone()
        
        # 2. DNS Totals
        dns_row = conn_dns.execute("""
            SELECT 
                COUNT(*), 
                COUNT(CASE WHEN is_blocked = TRUE THEN 1 END),
                MODE(device_id)
            FROM dns_logs
            WHERE timestamp >= ?
        """, [start_24h]).fetchone()
        
        total_queries = dns_row[0] or 0
        blocked_queries = dns_row[1] or 0
        top_client_id = dns_row[2]
        
        top_client_name = "None"
        if top_client_id:
            c_row = conn_main.execute("SELECT name, display_name FROM devices WHERE id = ?", [top_client_id]).fetchone()
            if c_row:
                top_client_name = c_row[1] or c_row[0]

        return {
            "traffic": {
                "download": traffic_row[0] or 0,
                "upload": traffic_row[1] or 0
            },
            "dns": {
                "total": total_queries,
                "blocked": blocked_queries,
                "block_rate": round((blocked_queries / total_queries * 100), 1) if total_queries > 0 else 0,
                "top_client": top_client_name
            }
        }
    except Exception as e:
        logger.error(f"Summary Error: {e}")
        return {}
    finally:
        conn_dns.close()
        conn_main.close()
