from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import psutil
import datetime
import os
import time
from ..database import get_db

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/stats")
def get_system_stats():
    """
    Get real-time system vitals (CPU, RAM, Disk).
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    
    # Memory
    mem = psutil.virtual_memory()
    memory_stats = {
        "percent": mem.percent,
        "used_gb": round(mem.used / (1024**3), 2),
        "total_gb": round(mem.total / (1024**3), 2)
    }
    
    # Disk
    disk = psutil.disk_usage('/')
    disk_stats = {
        "percent": disk.percent,
        "used_tb": round(disk.used / (1024**4), 2),
        "total_tb": round(disk.total / (1024**4), 2)
    }
    
    # Boot time
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat()
    
    # Network Speed (requires global storage for delta)
    global _prev_net, _prev_time
    curr_net = psutil.net_io_counters()
    curr_time = time.time()
    
    net_speed = {"up": 0.0, "down": 0.0}
    if '_prev_net' in globals():
        dt = curr_time - _prev_time
        if dt > 0:
            net_speed["up"] = round((curr_net.bytes_sent - _prev_net.bytes_sent) / (1024**2) / dt, 2)
            net_speed["down"] = round((curr_net.bytes_recv - _prev_net.bytes_recv) / (1024**2) / dt, 2)
    
    _prev_net = curr_net
    _prev_time = curr_time
    
    return {
        "cpu": cpu_percent,
        "memory": memory_stats,
        "disk": disk_stats,
        "network": net_speed,
        "boot_time": boot_time,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
