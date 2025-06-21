#!/usr/bin/env python3
"""
Celery Worker Startup Script
Starts Celery workers for Charlie task processing
"""

import os
import sys
import subprocess
import signal
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start_celery_worker():
    """Start Celery worker"""
    
    # Celery worker command
    cmd = [
        "celery",
        "-A", "app.services.tasks.task_queue:celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=2",
        "--queues=scripts,email,files,system",
        "--pool=threads"  # Use threads for Windows compatibility
    ]
    
    logger.info("Starting Celery worker...")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        # Start the worker process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        # Handle graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Shutting down Celery worker...")
            process.terminate()
            process.wait()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Monitor the process
        if process.stdout:
            for line in iter(process.stdout.readline, b''):
                print(line.decode().strip())
        
        process.wait()
        
    except Exception as e:
        logger.error(f"Failed to start Celery worker: {e}")
        sys.exit(1)


def start_celery_flower():
    """Start Celery Flower monitoring (optional)"""
    
    cmd = [
        "celery",
        "-A", "app.services.tasks.task_queue:celery_app", 
        "flower",
        "--port=5555"
    ]
    
    logger.info("Starting Celery Flower...")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(cmd)
        return process
    except Exception as e:
        logger.error(f"Failed to start Celery Flower: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Celery components")
    parser.add_argument("--flower", action="store_true", help="Also start Flower monitoring")
    args = parser.parse_args()
    
    if args.flower:
        flower_process = start_celery_flower()
    
    start_celery_worker() 