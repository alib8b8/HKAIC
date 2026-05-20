"""
HKAIC SaaS - Drone Connection and Control Manager
Module for managing connections to real drones using MAVSDK
"""

import asyncio
import logging
import re
from typing import Dict, Optional, List, Any
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# 安全配置
ALLOWED_URI_PREFIXES = ["udp://", "tcp://", "serial://"]
BLOCKED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0", "::1"]
MAX_TAKEOFF_ALTITUDE = 120  # 最大起飞高度（米）
MIN_TAKEOFF_ALTITUDE = 0.5  # 最小起飞高度（米）
MAX_GOTO_ALTITUDE = 120  # 最大航点高度（米）


class DroneConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class DroneFlightMode(Enum):
    UNKNOWN = "unknown"
    HOLD = "hold"
    TAKEOFF = "takeoff"
    LAND = "land"
    RETURN_TO_HOME = "return_to_home"
    MISSION = "mission"
    OFFBOARD = "offboard"
    MANUAL = "manual"
    ALTCTL = "altitude_control"
    POSCTL = "position_control"


class DroneTelemetry:
    """Drone telemetry data structure"""
    def __init__(self):
        self.position: Dict[str, float] = {
            'latitude': 0.0,
            'longitude': 0.0,
            'absolute_altitude': 0.0,
            'relative_altitude': 0.0
        }
        self.velocity: Dict[str, float] = {
            'north': 0.0,
            'east': 0.0,
            'down': 0.0
        }
        self.attitude: Dict[str, float] = {
            'roll': 0.0,
            'pitch': 0.0,
            'yaw': 0.0
        }
        self.battery: Dict[str, Any] = {
            'voltage': 0.0,
            'remaining': 0.0,
            'current': 0.0
        }
        self.armed: bool = False
        self.in_air: bool = False
        self.flight_mode: str = DroneFlightMode.UNKNOWN.value
        self.landed_state: str = "unknown"
        self.last_update: Optional[datetime] = None


class DroneConnection:
    """Represents a single drone connection"""
    def __init__(self, drone_id: str, connection_uri: str):
        self.drone_id = drone_id
        self.connection_uri = connection_uri
        self.status = DroneConnectionStatus.DISCONNECTED
        self.telemetry = DroneTelemetry()
        self.created_at = datetime.now()
        self.last_connection_time: Optional[datetime] = None
        self._drone_system = None
        self._telemetry_tasks: List[asyncio.Task] = []


class DroneManager:
    """
    Manager for handling drone connections
    Supports connecting to and controlling multiple drones simultaneously
    """
    
    def __init__(self):
        self._connections: Dict[str, DroneConnection] = {}
        self._lock = asyncio.Lock()
        logger.info("DroneManager initialized")
    
    async def connect_drone(
        self, 
        drone_id: str, 
        connection_uri: str = "udp://:14540"
    ) -> Dict[str, Any]:
        """
        Connect to a drone
        
        Args:
            drone_id: Unique identifier for the drone
            connection_uri: MAVLink connection URI (e.g., "udp://:14540", "serial:///dev/ttyUSB0")
        
        Returns:
            Connection status information
        """
        drone_id_validation = validate_drone_id(drone_id)
        if not drone_id_validation["valid"]:
            return {
                "success": False,
                "message": drone_id_validation["error"],
                "status": "validation_failed"
            }
        
        uri_validation = validate_connection_uri(connection_uri)
        if not uri_validation["valid"]:
            return {
                "success": False,
                "message": uri_validation["error"],
                "status": "validation_failed"
            }
        
        async with self._lock:
            if drone_id in self._connections:
                existing = self._connections[drone_id]
                if existing.status == DroneConnectionStatus.CONNECTED:
                    return {
                        "success": True,
                        "message": f"Drone {drone_id} already connected",
                        "status": existing.status.value
                    }
            
            # Create new connection
            connection = DroneConnection(drone_id, connection_uri)
            self._connections[drone_id] = connection
            connection.status = DroneConnectionStatus.CONNECTING
            
            logger.info(f"Connecting to drone {drone_id} at {connection_uri}")
            
            try:
                # Try to import MAVSDK
                from mavsdk import System
                
                # Initialize drone system
                drone = System()
                connection._drone_system = drone
                
                # Connect to drone
                await drone.connect(system_address=connection_uri)
                
                # Wait for discovery
                logger.info(f"Waiting for drone {drone_id} to be discovered...")
                async for state in drone.core.connection_state():
                    if state.is_connected:
                        logger.info(f"Drone {drone_id} connected successfully!")
                        connection.status = DroneConnectionStatus.CONNECTED
                        connection.last_connection_time = datetime.now()
                        
                        # Start telemetry monitoring
                        self._start_telemetry_monitoring(connection)
                        
                        return {
                            "success": True,
                            "message": f"Connected to drone {drone_id}",
                            "status": connection.status.value,
                            "connection_uri": connection_uri
                        }
                        
            except ImportError:
                logger.warning("⚠️ MAVSDK not installed, using simulated connection")
                logger.warning(f"⚠️ SIMULATION MODE: Drone {drone_id} is NOT a real drone!")
                await asyncio.sleep(1.0)
                connection.status = DroneConnectionStatus.CONNECTED
                connection.last_connection_time = datetime.now()
                connection.telemetry.armed = False
                connection.telemetry.in_air = False
                
                return {
                    "success": True,
                    "message": f"[SIMULATION MODE] Connected to drone {drone_id}",
                    "status": connection.status.value,
                    "simulated": True,
                    "warning": "⚠️ This is a simulated drone. No real flight will occur."
                }
                
            except Exception as e:
                logger.error(f"Failed to connect to drone {drone_id}: {str(e)}")
                connection.status = DroneConnectionStatus.ERROR
                return {
                    "success": False,
                    "message": f"Connection failed: {str(e)}",
                    "status": connection.status.value
                }
    
    def _start_telemetry_monitoring(self, connection: DroneConnection):
        """Start telemetry monitoring tasks for a connected drone"""
        if not connection._drone_system:
            return
        
        async def monitor_position():
            try:
                async for position in connection._drone_system.telemetry.position():
                    connection.telemetry.position = {
                        'latitude': position.latitude_deg,
                        'longitude': position.longitude_deg,
                        'absolute_altitude': position.absolute_altitude_m,
                        'relative_altitude': position.relative_altitude_m
                    }
                    connection.telemetry.last_update = datetime.now()
            except Exception as e:
                logger.error(f"Position monitoring error: {str(e)}")
        
        async def monitor_attitude():
            try:
                async for attitude in connection._drone_system.telemetry.attitude_euler():
                    connection.telemetry.attitude = {
                        'roll': attitude.roll_deg,
                        'pitch': attitude.pitch_deg,
                        'yaw': attitude.yaw_deg
                    }
                    connection.telemetry.last_update = datetime.now()
            except Exception as e:
                logger.error(f"Attitude monitoring error: {str(e)}")
        
        async def monitor_battery():
            try:
                async for battery in connection._drone_system.telemetry.battery():
                    connection.telemetry.battery = {
                        'voltage': battery.voltage_v,
                        'remaining': battery.remaining_percent,
                        'current': 0.0
                    }
                    connection.telemetry.last_update = datetime.now()
            except Exception as e:
                logger.error(f"Battery monitoring error: {str(e)}")
        
        async def monitor_status():
            try:
                async for armed in connection._drone_system.telemetry.armed():
                    connection.telemetry.armed = armed
                    connection.telemetry.last_update = datetime.now()
                
                async for in_air in connection._drone_system.telemetry.in_air():
                    connection.telemetry.in_air = in_air
                    connection.telemetry.last_update = datetime.now()
            except Exception as e:
                logger.error(f"Status monitoring error: {str(e)}")
        
        # Start tasks
        connection._telemetry_tasks = [
            asyncio.create_task(monitor_position()),
            asyncio.create_task(monitor_attitude()),
            asyncio.create_task(monitor_battery()),
            asyncio.create_task(monitor_status())
        ]
    
    async def disconnect_drone(self, drone_id: str) -> Dict[str, Any]:
        """Disconnect from a drone"""
        async with self._lock:
            if drone_id not in self._connections:
                return {
                    "success": False,
                    "message": f"Drone {drone_id} not found"
                }
            
            connection = self._connections[drone_id]
            
            # Cancel telemetry tasks
            for task in connection._telemetry_tasks:
                if not task.done():
                    task.cancel()
            
            # Clear drone system
            connection._drone_system = None
            connection.status = DroneConnectionStatus.DISCONNECTED
            
            logger.info(f"Disconnected from drone {drone_id}")
            
            return {
                "success": True,
                "message": f"Disconnected from drone {drone_id}"
            }
    
    async def get_drone_status(self, drone_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a drone"""
        async with self._lock:
            if drone_id not in self._connections:
                return None
            
            connection = self._connections[drone_id]
            
            return {
                "drone_id": drone_id,
                "status": connection.status.value,
                "connection_uri": connection.connection_uri,
                "connected_at": connection.last_connection_time.isoformat() if connection.last_connection_time else None,
                "telemetry": {
                    "position": connection.telemetry.position,
                    "velocity": connection.telemetry.velocity,
                    "attitude": connection.telemetry.attitude,
                    "battery": connection.telemetry.battery,
                    "armed": connection.telemetry.armed,
                    "in_air": connection.telemetry.in_air,
                    "flight_mode": connection.telemetry.flight_mode,
                    "last_update": connection.telemetry.last_update.isoformat() if connection.telemetry.last_update else None
                }
            }
    
    def list_drones(self) -> List[Dict[str, Any]]:
        """List all registered drones"""
        return [
            {
                "drone_id": drone_id,
                "status": conn.status.value,
                "connection_uri": conn.connection_uri,
                "connected_at": conn.last_connection_time.isoformat() if conn.last_connection_time else None
            }
            for drone_id, conn in self._connections.items()
        ]
    
    async def arm_drone(self, drone_id: str) -> Dict[str, Any]:
        """Arm the drone"""
        async with self._lock:
            if drone_id not in self._connections:
                return {"success": False, "message": "Drone not found"}
            
            connection = self._connections[drone_id]
            if connection.status != DroneConnectionStatus.CONNECTED:
                return {"success": False, "message": "Drone not connected"}
            
            try:
                if connection._drone_system:
                    await connection._drone_system.action.arm()
                    connection.telemetry.armed = True
                    logger.info(f"Drone {drone_id} armed")
                else:
                    # Simulate arming
                    connection.telemetry.armed = True
                    await asyncio.sleep(0.5)
                
                return {
                    "success": True,
                    "message": f"Drone {drone_id} armed",
                    "armed": True
                }
            except Exception as e:
                logger.error(f"Failed to arm drone {drone_id}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Arming failed: {str(e)}"
                }
    
    async def disarm_drone(self, drone_id: str) -> Dict[str, Any]:
        """Disarm the drone"""
        async with self._lock:
            if drone_id not in self._connections:
                return {"success": False, "message": "Drone not found"}
            
            connection = self._connections[drone_id]
            
            try:
                if connection._drone_system:
                    await connection._drone_system.action.disarm()
                    connection.telemetry.armed = False
                else:
                    connection.telemetry.armed = False
                    await asyncio.sleep(0.5)
                
                logger.info(f"Drone {drone_id} disarmed")
                return {
                    "success": True,
                    "message": f"Drone {drone_id} disarmed",
                    "armed": False
                }
            except Exception as e:
                logger.error(f"Failed to disarm drone {drone_id}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Disarming failed: {str(e)}"
                }
    
    async def takeoff_drone(self, drone_id: str, altitude: float = 2.0) -> Dict[str, Any]:
        """Command drone to takeoff"""
        altitude_validation = validate_takeoff_altitude(altitude)
        if not altitude_validation.get("valid", False):
            return {
                "success": False,
                "message": altitude_validation["error"],
                "status": "validation_failed"
            }
        
        adjusted_altitude = altitude_validation.get("adjusted", False)
        actual_altitude = altitude_validation.get("altitude", altitude)
        
        async with self._lock:
            if drone_id not in self._connections:
                return {"success": False, "message": "Drone not found"}
            
            connection = self._connections[drone_id]
            if connection.status != DroneConnectionStatus.CONNECTED:
                return {"success": False, "message": "Drone not connected"}
            
            if adjusted_altitude:
                logger.warning(f"Takeoff altitude adjusted to {actual_altitude}m for drone {drone_id}")
            
            try:
                if connection._drone_system:
                    await connection._drone_system.action.set_takeoff_altitude(actual_altitude)
                    await connection._drone_system.action.takeoff()
                    connection.telemetry.in_air = True
                else:
                    connection.telemetry.in_air = True
                    await asyncio.sleep(1.0)
                
                logger.info(f"Drone {drone_id} taking off to {actual_altitude}m")
                
                result = {
                    "success": True,
                    "message": f"Drone {drone_id} taking off",
                    "altitude": actual_altitude
                }
                
                if adjusted_altitude:
                    result["warning"] = altitude_validation.get("message", "")
                
                return result
            except Exception as e:
                logger.error(f"Takeoff failed for drone {drone_id}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Takeoff failed: {str(e)}"
                }
    
    async def land_drone(self, drone_id: str) -> Dict[str, Any]:
        """Command drone to land"""
        async with self._lock:
            if drone_id not in self._connections:
                return {"success": False, "message": "Drone not found"}
            
            connection = self._connections[drone_id]
            
            try:
                if connection._drone_system:
                    await connection._drone_system.action.land()
                    connection.telemetry.in_air = False
                else:
                    connection.telemetry.in_air = False
                    await asyncio.sleep(1.0)
                
                logger.info(f"Drone {drone_id} landing")
                return {
                    "success": True,
                    "message": f"Drone {drone_id} landing"
                }
            except Exception as e:
                logger.error(f"Landing failed for drone {drone_id}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Landing failed: {str(e)}"
                }
    
    async def return_to_home(self, drone_id: str) -> Dict[str, Any]:
        """Command drone to return to home"""
        async with self._lock:
            if drone_id not in self._connections:
                return {"success": False, "message": "Drone not found"}
            
            connection = self._connections[drone_id]
            
            try:
                if connection._drone_system:
                    await connection._drone_system.action.return_to_launch()
                else:
                    await asyncio.sleep(0.5)
                
                logger.info(f"Drone {drone_id} returning to home")
                return {
                    "success": True,
                    "message": f"Drone {drone_id} returning to home"
                }
            except Exception as e:
                logger.error(f"Return to home failed for drone {drone_id}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Return to home failed: {str(e)}"
                }
    
    async def set_position(
        self,
        drone_id: str,
        latitude: float,
        longitude: float,
        altitude: float
    ) -> Dict[str, Any]:
        """Send position control command"""
        coord_validation = validate_coordinates(latitude, longitude, altitude)
        if not coord_validation["valid"]:
            return {
                "success": False,
                "message": "; ".join(coord_validation.get("errors", ["Invalid coordinates"])),
                "status": "validation_failed"
            }
        
        async with self._lock:
            if drone_id not in self._connections:
                return {"success": False, "message": "Drone not found"}
            
            connection = self._connections[drone_id]
            
            try:
                if connection._drone_system:
                    await connection._drone_system.action.goto_location(
                        latitude,
                        longitude,
                        altitude,
                        0.0
                    )
                else:
                    connection.telemetry.position = {
                        'latitude': latitude,
                        'longitude': longitude,
                        'absolute_altitude': altitude,
                        'relative_altitude': altitude
                    }
                    await asyncio.sleep(0.5)
                
                logger.info(f"Drone {drone_id} moving to position ({latitude}, {longitude}, {altitude}m)")
                return {
                    "success": True,
                    "message": "Position command sent",
                    "target": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "altitude": altitude
                    }
                }
            except Exception as e:
                logger.error(f"Position command failed for drone {drone_id}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Position command failed: {str(e)}"
                }


# Singleton instance
drone_manager = DroneManager()


def validate_drone_id(drone_id: str) -> Dict[str, Any]:
    """
    验证无人机 ID 格式
    只允许字母、数字、连字符和下划线，长度 1-64
    """
    if not drone_id or len(drone_id) > 64:
        return {
            "valid": False,
            "error": "Drone ID must be 1-64 characters"
        }
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, drone_id):
        return {
            "valid": False,
            "error": "Drone ID can only contain letters, numbers, hyphens and underscores"
        }
    
    return {"valid": True}


def validate_connection_uri(uri: str) -> Dict[str, Any]:
    """
    验证连接 URI 是否安全
    只允许特定协议和白名单主机
    """
    if not uri:
        return {
            "valid": False,
            "error": "Connection URI is required"
        }
    
    if not any(uri.startswith(prefix) for prefix in ALLOWED_URI_PREFIXES):
        return {
            "valid": False,
            "error": f"Invalid URI protocol. Allowed: {', '.join(ALLOWED_URI_PREFIXES)}"
        }
    
    try:
        parsed = urlparse(uri)
        hostname = parsed.hostname if parsed.hostname else ""
        
        if hostname in BLOCKED_HOSTS:
            return {
                "valid": False,
                "error": "Connection to localhost/internal hosts is not allowed"
            }
        
    except Exception:
        return {
            "valid": False,
            "error": "Invalid URI format"
        }
    
    return {"valid": True}


def validate_coordinates(latitude: float, longitude: float, altitude: float) -> Dict[str, Any]:
    """
    验证坐标是否在安全范围内
    """
    errors = []
    
    if not isinstance(latitude, (int, float)) or not -90 <= latitude <= 90:
        errors.append(f"Latitude must be between -90 and 90 degrees")
    
    if not isinstance(longitude, (int, float)) or not -180 <= longitude <= 180:
        errors.append(f"Longitude must be between -180 and 180 degrees")
    
    if not isinstance(altitude, (int, float)) or not 0 <= altitude <= MAX_GOTO_ALTITUDE:
        errors.append(f"Altitude must be between 0 and {MAX_GOTO_ALTITUDE} meters")
    
    if errors:
        return {"valid": False, "errors": errors}
    
    return {"valid": True}


def validate_takeoff_altitude(altitude: float) -> Dict[str, Any]:
    """
    验证起飞高度是否安全
    """
    if not isinstance(altitude, (int, float)):
        return {
            "valid": False,
            "error": "Altitude must be a number"
        }
    
    if altitude < MIN_TAKEOFF_ALTITUDE:
        return {
            "valid": True,
            "adjusted": True,
            "altitude": MIN_TAKEOFF_ALTITUDE,
            "message": f"Altitude adjusted to minimum safe height ({MIN_TAKEOFF_ALTITUDE}m)"
        }
    
    if altitude > MAX_TAKEOFF_ALTITUDE:
        return {
            "valid": False,
            "error": f"Takeoff altitude exceeds maximum allowed ({MAX_TAKEOFF_ALTITUDE}m)"
        }
    
    return {"valid": True}
