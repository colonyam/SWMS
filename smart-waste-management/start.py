#!/usr/bin/env python3
"""
Smart Waste Management System - Quick Start Script

This script helps you quickly start the application.
"""

import subprocess
import sys
import os
import argparse
import time
import signal

PROCESSES = []


def signal_handler(sig, frame):
    """Handle shutdown signal"""
    print("\n\nShutting down...")
    for process in PROCESSES:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass
    sys.exit(0)


def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or higher is required")
        return False
    
    # Check if pip is available
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
    except:
        print("Error: pip is not available")
        return False
    
    print("Dependencies check passed!")
    return True


def install_backend_deps():
    """Install backend dependencies"""
    print("Installing backend dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"],
            check=True
        )
        print("Backend dependencies installed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing backend dependencies: {e}")
        return False


def start_backend():
    """Start the backend server"""
    print("Starting backend server...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "backend")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", 
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd="backend",
        env=env
    )
    
    PROCESSES.append(process)
    return process


def seed_database():
    """Seed the database with sample data"""
    print("Seeding database...")
    try:
        import httpx
        time.sleep(3)  # Wait for server to start
        response = httpx.post("http://localhost:8000/api/v1/seed-data", timeout=10)
        if response.status_code == 200:
            print("Database seeded successfully!")
            return True
        else:
            print(f"Warning: Database seed returned {response.status_code}")
            return False
    except Exception as e:
        print(f"Warning: Could not seed database: {e}")
        return False


def start_simulator():
    """Start the IoT simulator"""
    print("Starting IoT simulator...")
    
    # Check if simulator dependencies are installed
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "iot_simulator/requirements.txt"],
            check=True,
            capture_output=True
        )
    except:
        print("Warning: Could not install simulator dependencies")
        return None
    
    process = subprocess.Popen(
        [sys.executable, "simulator.py", "--api-url", "http://localhost:8000"],
        cwd="iot_simulator"
    )
    
    PROCESSES.append(process)
    return process


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           Smart Waste Management System                      ║
║                                                              ║
║  Real-time monitoring | Analytics | Route Optimization       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_access_info():
    """Print access information"""
    info = """
╔══════════════════════════════════════════════════════════════╗
║  Access Information:                                         ║
║                                                              ║
║  Dashboard:     http://localhost:8000                        ║
║  API Docs:      http://localhost:8000/docs                   ║
║  API Base:      http://localhost:8000/api/v1                 ║
║                                                              ║
║  Press Ctrl+C to stop all services                           ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(info)


def main():
    parser = argparse.ArgumentParser(
        description="Smart Waste Management System - Quick Start"
    )
    parser.add_argument(
        "--no-simulator",
        action="store_true",
        help="Don't start the IoT simulator"
    )
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Don't seed the database"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install dependencies before starting"
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_backend_deps():
            sys.exit(1)
    
    # Start backend
    backend_process = start_backend()
    
    # Wait for backend to start
    time.sleep(2)
    
    # Seed database
    if not args.no_seed:
        seed_database()
    
    # Start simulator
    if not args.no_simulator:
        simulator_process = start_simulator()
    
    print_access_info()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
            # Check if processes are still running
            for process in PROCESSES:
                if process.poll() is not None:
                    print(f"\nProcess exited with code {process.returncode}")
                    signal_handler(None, None)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
