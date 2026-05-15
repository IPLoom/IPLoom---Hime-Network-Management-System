# Reload trigger stable
from fastapi import FastAPI
import asyncio
import logging
import signal
from app.core.db import init_db, commit, close_shared_connection
from app.routers.config import router as config_router, public_router as config_public_router
from app.routers.scans import router as scans_router
from app.routers.devices import router as devices_router
from app.routers.schedules import router as schedules_router
from app.services.worker import scheduler_loop, scan_runner_loop
from app.routers.ssh import router as ssh_router
from app.routers.events import router as events_router
from app.routers.mqtt import router as mqtt_router
from app.routers.classification import router as classification_router
from app.routers.openwrt import router as openwrt_router
from app.routers.analytics import router as analytics_router
from app.routers.system import router as system_router
from app.routers.assets import router as assets_router


from app.core.logging import setup_logging

# Initialize logging before app creation
setup_logging()
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Network Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def cleanup_stale_scans():
    from app.core.db import get_connection
    from app.core.date_utils import now as utc_now
    logger.info("Cleaning up stale scans from previous run...")
    conn = get_connection()
    try:
        # Mark running or queued scans as interrupted on startup
        conn.execute(
            "UPDATE scans SET status = 'interrupted', finished_at = ?, error_message = 'Interrupted by server restart' WHERE status IN ('running', 'queued')",
            [utc_now()]
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error during startup cleanup: {e}")
    finally:
        conn.close()

async def periodic_checkpoint(interval_seconds: int = 600):
    """Runs a CHECKPOINT on the shared DuckDB connection every `interval_seconds` (default: 10 min)."""
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            from app.core.db import get_connection, get_db_lock
            with get_db_lock():
                conn = get_connection()
                conn.execute("CHECKPOINT")
                conn.close()
            logger.info("DB checkpoint completed (periodic).")
        except Exception as e:
            logger.warning(f"Periodic DB checkpoint failed: {e}")

def run_shutdown_checkpoint():
    """Performs a final CHECKPOINT and closes the shared connection cleanly."""
    try:
        from app.core.db import get_connection, get_db_lock
        with get_db_lock():
            conn = get_connection()
            conn.execute("CHECKPOINT")
            conn.close()
        logger.info("DB checkpoint completed (shutdown).")
    except Exception as e:
        logger.warning(f"Shutdown DB checkpoint failed: {e}")
    finally:
        close_shared_connection()

def _handle_signal(sig, frame):
    """Signal handler for SIGTERM/SIGINT — checkpoints DB before process exits."""
    logger.info(f"Received signal {sig}, running shutdown checkpoint...")
    run_shutdown_checkpoint()
    raise SystemExit(0)

@app.on_event("startup")
async def on_startup():
    from app.core.notifications import manager
    manager.set_loop(asyncio.get_running_loop())

    # Register OS-level signal handlers for Docker stop (SIGTERM) and Ctrl+C (SIGINT)
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    await asyncio.to_thread(init_db)
    await asyncio.to_thread(cleanup_stale_scans)

    # OUI downloader was permanently removed due to high CPU usage on Raspberry Pi.
    # Vendor identification now relies on hardcoded COMMON_OUIS and on-demand API enrichment.

    asyncio.create_task(scheduler_loop())
    asyncio.create_task(scan_runner_loop())
    asyncio.create_task(periodic_checkpoint(interval_seconds=600))  # every 10 min

    # Run network discovery and cache results for onboarding ONLY if not configured
    from app.core.db import get_connection
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM config WHERE key = 'scan_subnets'").fetchone()
        is_configured = bool(row and row[0] and row[0].strip())
    finally:
        conn.close()

    if not is_configured:
        from app.services.discovery import DiscoveryService
        asyncio.create_task(DiscoveryService.run_and_cache())
    else:
        logger.info("Skipping background network discovery: Subnets already configured.")

@app.on_event("shutdown")
async def on_shutdown():
    """FastAPI graceful shutdown — final checkpoint before the event loop stops."""
    logger.info("FastAPI shutdown event: running final DB checkpoint...")
    await asyncio.to_thread(run_shutdown_checkpoint)
    
from app.routers.auth import router as auth_router
from app.core.auth import get_current_user
from fastapi import Depends

from app.routers.topology import router as topology_router
from app.routers.discovery import router as discovery_router

# Mount static files for assets from persistent data directory
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from pathlib import Path
settings = get_settings()

# Ensure directory exists before mounting to avoid startup crash
assets_path = Path(settings.assets_dir)
assets_path.mkdir(parents=True, exist_ok=True)
(assets_path / "brand_icons").mkdir(parents=True, exist_ok=True)
(assets_path / "device_icons").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=settings.assets_dir), name="static")

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(config_public_router, prefix="/api/v1/config", tags=["config"])
app.include_router(config_router, prefix="/api/v1/config", tags=["config"], dependencies=[Depends(get_current_user)])
app.include_router(scans_router, prefix="/api/v1/scans", tags=["scans"], dependencies=[Depends(get_current_user)])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["devices"], dependencies=[Depends(get_current_user)])
app.include_router(discovery_router, prefix="/api/v1/discovery", tags=["discovery"], dependencies=[Depends(get_current_user)])
app.include_router(schedules_router, prefix="/api/v1/schedules", tags=["schedules"], dependencies=[Depends(get_current_user)])
app.include_router(ssh_router, prefix="/api/v1/ssh", tags=["ssh"], dependencies=[Depends(get_current_user)])
app.include_router(events_router, prefix="/api/v1/events", tags=["events"], dependencies=[Depends(get_current_user)])
app.include_router(mqtt_router, prefix="/api/v1/mqtt", tags=["mqtt"], dependencies=[Depends(get_current_user)])
app.include_router(classification_router, prefix="/api/v1/classification", tags=["classification"], dependencies=[Depends(get_current_user)])

app.include_router(openwrt_router, prefix="/api/v1/integrations/openwrt", tags=["openwrt"], dependencies=[Depends(get_current_user)])

from app.routers.adguard import router as adguard_router
app.include_router(adguard_router, prefix="/api/v1/integrations/adguard", tags=["adguard"], dependencies=[Depends(get_current_user)])

app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)])

from app.routers.logs import router as logs_router
app.include_router(logs_router, prefix="/api/v1/logs", tags=["logs"], dependencies=[Depends(get_current_user)])

from app.routers.task_events import router as task_events_router
app.include_router(task_events_router, prefix="/api/v1/task-events", tags=["task-events"], dependencies=[Depends(get_current_user)])
app.include_router(system_router, prefix="/api/v1/system", tags=["system"], dependencies=[Depends(get_current_user)])
app.include_router(assets_router, prefix="/api/v1/assets", tags=["assets"], dependencies=[Depends(get_current_user)])


app.include_router(topology_router, prefix="/api/v1/topology", tags=["topology"], dependencies=[Depends(get_current_user)])
from app.routers.notifications import router as notifications_router
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])



