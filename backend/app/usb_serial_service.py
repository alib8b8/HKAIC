import serial
import serial.tools.list_ports
import asyncio
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class SerialPortInfo:
    device: str
    description: str
    hardware_id: str
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None


@dataclass
class SerialConnection:
    port: str
    baudrate: int
    serial: serial.Serial
    connected: bool = False
    last_activity: Optional[datetime] = None


class USBSerialService:
    def __init__(self):
        self.connections: Dict[str, SerialConnection] = {}
        self.message_handlers: List[Callable] = []
        self.read_tasks: Dict[str, asyncio.Task] = {}

    def list_ports(self) -> List[SerialPortInfo]:
        ports = serial.tools.list_ports.comports()
        port_list = []
        
        for port in ports:
            port_info = SerialPortInfo(
                device=port.device,
                description=port.description,
                hardware_id=port.hwid,
                vendor_id=port.vid,
                product_id=port.pid
            )
            port_list.append(port_info)
            
        return port_list

    def connect(self, port: str, baudrate: int = 57600) -> bool:
        try:
            if port in self.connections and self.connections[port].connected:
                logger.warning(f"Port {port} already connected")
                return True

            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1,
                write_timeout=1
            )
            
            connection = SerialConnection(
                port=port,
                baudrate=baudrate,
                serial=ser,
                connected=True,
                last_activity=datetime.now()
            )
            
            self.connections[port] = connection
            logger.info(f"Successfully connected to {port} at {baudrate} baud")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {port}: {str(e)}")
            return False

    def disconnect(self, port: str) -> bool:
        try:
            if port in self.connections:
                connection = self.connections[port]
                if connection.connected:
                    connection.serial.close()
                del self.connections[port]
                logger.info(f"Disconnected from {port}")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from {port}: {str(e)}")
            return False

    def is_connected(self, port: str) -> bool:
        return port in self.connections and self.connections[port].connected

    def send_data(self, port: str, data: bytes) -> bool:
        try:
            if port not in self.connections:
                logger.error(f"Port {port} not connected")
                return False
                
            connection = self.connections[port]
            if not connection.connected:
                logger.error(f"Port {port} is not connected")
                return False
                
            bytes_written = connection.serial.write(data)
            connection.last_activity = datetime.now()
            
            logger.debug(f"Sent {bytes_written} bytes to {port}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending data to {port}: {str(e)}")
            return False

    def receive_data(self, port: str, timeout: float = 1.0) -> Optional[bytes]:
        try:
            if port not in self.connections:
                return None
                
            connection = self.connections[port]
            if not connection.connected:
                return None
                
            connection.serial.timeout = timeout
            data = connection.serial.read_all()
            
            if data:
                connection.last_activity = datetime.now()
                logger.debug(f"Received {len(data)} bytes from {port}")
                
            return data
            
        except Exception as e:
            logger.error(f"Error receiving data from {port}: {str(e)}")
            return None

    def send_text(self, port: str, text: str) -> bool:
        return self.send_data(port, text.encode('utf-8'))

    def send_json(self, port: str, data: dict) -> bool:
        try:
            json_str = json.dumps(data) + '\n'
            return self.send_text(port, json_str)
        except Exception as e:
            logger.error(f"Error sending JSON: {str(e)}")
            return False

    def get_connection_status(self, port: str) -> Optional[dict]:
        if port not in self.connections:
            return None
            
        connection = self.connections[port]
        return {
            'port': connection.port,
            'baudrate': connection.baudrate,
            'connected': connection.connected,
            'last_activity': connection.last_activity.isoformat() if connection.last_activity else None
        }

    def get_all_connections(self) -> List[dict]:
        return [
            self.get_connection_status(port)
            for port in self.connections
        ]

    def add_message_handler(self, handler: Callable):
        self.message_handlers.append(handler)

    def close_all(self):
        for port in list(self.connections.keys()):
            self.disconnect(port)


usb_serial_service = USBSerialService()
