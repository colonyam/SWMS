#!/usr/bin/env python3
"""
IoT Sensor Simulator for Smart Waste Management System

This simulator mimics IoT sensors installed in waste bins by:
- Generating realistic fill level data
- Simulating different waste generation patterns
- Sending data to the backend API
- Simulating battery drain
- Creating occasional sensor anomalies

Usage:
    python simulator.py [--api-url URL] [--interval SECONDS] [--bins COUNT]
"""

import asyncio
import argparse
import logging
import random
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import httpx
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WasteBinSimulator:
    """Simulates a single waste bin sensor"""
    
    # Waste generation patterns (fill % per hour)
    PATTERNS = {
        "residential": {"base_rate": 0.5, "peak_hours": [8, 9, 18, 19, 20], "peak_multiplier": 2.0},
        "commercial": {"base_rate": 1.5, "peak_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17], "peak_multiplier": 1.5},
        "recreational": {"base_rate": 0.8, "peak_hours": [10, 11, 12, 13, 14, 15, 16], "peak_multiplier": 3.0},
        "industrial": {"base_rate": 2.0, "peak_hours": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18], "peak_multiplier": 1.2},
        "event": {"base_rate": 3.0, "peak_hours": list(range(24)), "peak_multiplier": 2.5},
    }
    
    def __init__(self, bin_id: int, location_type: str = "residential", 
                 initial_fill: float = 20.0, initial_battery: float = 100.0):
        self.bin_id = bin_id
        self.location_type = location_type
        self.fill_level = initial_fill
        self.battery_level = initial_battery
        self.temperature = 20.0
        self.is_online = True
        self.last_reading_time = datetime.now()
        self.pattern = self.PATTERNS.get(location_type, self.PATTERNS["residential"])
        
        # Random variation factors
        self.variation_factor = random.uniform(0.8, 1.2)
        self.sensor_drift = random.uniform(-2.0, 2.0)
        
    def calculate_fill_rate(self) -> float:
        """Calculate current fill rate based on time and pattern"""
        current_hour = datetime.now().hour
        
        base_rate = self.pattern["base_rate"] * self.variation_factor
        
        # Apply peak hour multiplier
        if current_hour in self.pattern["peak_hours"]:
            base_rate *= self.pattern["peak_multiplier"]
        
        # Weekend adjustment (higher for recreational)
        if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
            if self.location_type in ["recreational", "event"]:
                base_rate *= 1.5
            elif self.location_type == "commercial":
                base_rate *= 0.3  # Lower on weekends for commercial
        
        return base_rate / 2  # Divide by 2 since we update every 30 seconds
    
    def generate_reading(self) -> Dict:
        """Generate a new sensor reading"""
        if not self.is_online:
            # Randomly come back online
            if random.random() < 0.1:  # 10% chance to come back online
                self.is_online = True
                logger.info(f"Bin {self.bin_id} sensor came back online")
            else:
                return None
        
        # Simulate occasional sensor failures (1% chance)
        if random.random() < 0.01:
            self.is_online = False
            logger.warning(f"Bin {self.bin_id} sensor went offline")
            return None
        
        # Calculate time since last reading
        now = datetime.now()
        time_diff_hours = (now - self.last_reading_time).total_seconds() / 3600
        self.last_reading_time = now
        
        # Update fill level
        fill_rate = self.calculate_fill_rate()
        self.fill_level += fill_rate * time_diff_hours * random.uniform(0.8, 1.2)
        
        # Cap at 100%
        self.fill_level = min(100.0, self.fill_level)
        
        # Simulate collection (reset to low level when very full - simulating manual collection)
        if self.fill_level >= 98:
            if random.random() < 0.3:  # 30% chance of collection when critical
                logger.info(f"Bin {self.bin_id} was collected (simulated)")
                self.fill_level = random.uniform(5, 15)
        
        # Update battery (slow drain)
        self.battery_level -= random.uniform(0.01, 0.05)
        self.battery_level = max(0.0, self.battery_level)
        
        # Update temperature (diurnal variation)
        hour = datetime.now().hour
        base_temp = 20.0 + 5.0 * ((hour - 14) ** 2) / 100  # Peak at 2 PM
        self.temperature = base_temp + random.uniform(-2.0, 2.0)
        
        # Add sensor noise
        reported_fill = max(0.0, min(100.0, self.fill_level + self.sensor_drift + random.uniform(-1.0, 1.0)))
        reported_battery = max(0.0, min(100.0, self.battery_level + random.uniform(-0.5, 0.5)))
        reported_temp = self.temperature + random.uniform(-0.5, 0.5)
        
        return {
            "bin_id": self.bin_id,
            "fill_level_percent": round(reported_fill, 2),
            "temperature_celsius": round(reported_temp, 2),
            "battery_percent": round(reported_battery, 2),
            "timestamp": now.isoformat()
        }


class IoTSimulator:
    """Main IoT Simulator class"""
    
    def __init__(self, api_url: str = "http://localhost:8000", update_interval: int = 30):
        self.api_url = api_url.rstrip("/")
        self.update_interval = update_interval
        self.bins: Dict[int, WasteBinSimulator] = {}
        self.client = httpx.AsyncClient(timeout=10.0)
        self.running = False
        self.api_key = None
        
    async def initialize_bins(self, count: int = 15):
        """Initialize simulator with existing bins from API or create new ones"""
        logger.info(f"Initializing {count} simulated bins...")
        
        # Try to get existing bins from API
        try:
            response = await self.client.get(f"{self.api_url}/api/v1/bins/")
            if response.status_code == 200:
                existing_bins = response.json()
                logger.info(f"Found {len(existing_bins)} existing bins")
                
                for bin_data in existing_bins[:count]:
                    # Determine location type from name or random
                    location_type = self._infer_location_type(bin_data.get("location_name", ""))
                    
                    self.bins[bin_data["id"]] = WasteBinSimulator(
                        bin_id=bin_data["id"],
                        location_type=location_type,
                        initial_fill=random.uniform(10, 60),
                        initial_battery=random.uniform(60, 100)
                    )
            else:
                logger.warning(f"Failed to get bins: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching bins: {e}")
        
        # If no bins found, seed the database
        if not self.bins:
            logger.info("No bins found. Seeding database...")
            try:
                response = await self.client.post(f"{self.api_url}/api/v1/seed-data")
                if response.status_code == 200:
                    logger.info("Database seeded successfully")
                    # Re-fetch bins
                    await self.initialize_bins(count)
                    return
            except Exception as e:
                logger.error(f"Error seeding database: {e}")
        
        logger.info(f"Initialized {len(self.bins)} simulated bins")
    
    def _infer_location_type(self, location_name: str) -> str:
        """Infer location type from location name"""
        name_lower = location_name.lower()
        
        if any(word in name_lower for word in ["park", "recreational", "stadium", "arena"]):
            return "recreational"
        elif any(word in name_lower for word in ["industrial", "factory", "warehouse"]):
            return "industrial"
        elif any(word in name_lower for word in ["market", "mall", "plaza", "square", "downtown", "street"]):
            return "commercial"
        elif any(word in name_lower for word in ["event", "convention", "expo"]):
            return "event"
        else:
            return "residential"
    
    async def send_reading(self, reading: Dict) -> bool:
        """Send a sensor reading to the API"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/v1/readings/",
                json=reading
            )
            
            if response.status_code == 201:
                logger.debug(f"Sent reading for bin {reading['bin_id']}: {reading['fill_level_percent']:.1f}%")
                return True
            else:
                logger.warning(f"Failed to send reading: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending reading: {e}")
            return False
    
    async def run_simulation_cycle(self):
        """Run one simulation cycle - generate and send readings for all bins"""
        readings = []
        
        for bin_sim in self.bins.values():
            reading = bin_sim.generate_reading()
            if reading:
                readings.append(reading)
        
        # Send readings in batch for efficiency
        if readings:
            try:
                response = await self.client.post(
                    f"{self.api_url}/api/v1/readings/batch",
                    json=readings
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Batch sent: {result.get('created_count', 0)} readings, "
                               f"{result.get('error_count', 0)} errors")
                else:
                    logger.warning(f"Batch send failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error in batch send: {e}")
    
    async def run(self):
        """Main simulation loop"""
        self.running = True
        logger.info(f"Starting IoT Simulator (interval: {self.update_interval}s)")
        
        cycle_count = 0
        
        while self.running:
            try:
                await self.run_simulation_cycle()
                cycle_count += 1
                
                # Periodic status report every 10 cycles
                if cycle_count % 10 == 0:
                    avg_fill = sum(b.fill_level for b in self.bins.values()) / len(self.bins) if self.bins else 0
                    critical_bins = sum(1 for b in self.bins.values() if b.fill_level >= 95)
                    logger.info(f"Status: {len(self.bins)} bins, avg fill: {avg_fill:.1f}%, critical: {critical_bins}")
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in simulation cycle: {e}")
                await asyncio.sleep(5)  # Shorter sleep on error
    
    def stop(self):
        """Stop the simulator"""
        logger.info("Stopping IoT Simulator...")
        self.running = False
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="IoT Sensor Simulator for Smart Waste Management System"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Update interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=15,
        help="Number of bins to simulate (default: 15)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_arguments()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    simulator = IoTSimulator(
        api_url=args.api_url,
        update_interval=args.interval
    )
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        simulator.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize bins
        await simulator.initialize_bins(count=args.bins)
        
        if not simulator.bins:
            logger.error("No bins available for simulation. Exiting.")
            return 1
        
        # Run simulation
        await simulator.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        await simulator.cleanup()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
