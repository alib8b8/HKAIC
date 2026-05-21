from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from ..usb_serial_service import usb_serial_service, SerialPortInfo
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/usb", tags=["usb-serial"])


class ConnectRequest(BaseModel):
    port: str
    baudrate: int = 57600


class SendDataRequest(BaseModel):
    port: str
    data: Optional[str] = None
    json_data: Optional[dict] = None


class PortInfoResponse(BaseModel):
    device: str
    description: str
    hardware_id: str
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None


@router.get("/ports", response_model=List[PortInfoResponse])
async def list_ports():
    try:
        ports = usb_serial_service.list_ports()
        return [
            PortInfoResponse(
                device=p.device,
                description=p.description,
                hardware_id=p.hardware_id,
                vendor_id=p.vendor_id,
                product_id=p.product_id
            )
            for p in ports
        ]
    except Exception as e:
        logger.error(f"Error listing ports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list serial ports: {str(e)}"
        )


@router.post("/connect")
async def connect_to_port(request: ConnectRequest):
    try:
        success = usb_serial_service.connect(request.port, request.baudrate)
        if success:
            return {
                "success": True,
                "message": f"Connected to {request.port}",
                "port": request.port,
                "baudrate": request.baudrate
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to {request.port}"
            )
    except Exception as e:
        logger.error(f"Error connecting to port: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection error: {str(e)}"
        )


@router.post("/disconnect")
async def disconnect_from_port(port: str):
    try:
        success = usb_serial_service.disconnect(port)
        if success:
            return {
                "success": True,
                "message": f"Disconnected from {port}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to disconnect from {port}"
            )
    except Exception as e:
        logger.error(f"Error disconnecting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disconnect error: {str(e)}"
        )


@router.get("/status/{port}")
async def get_port_status(port: str):
    try:
        status_info = usb_serial_service.get_connection_status(port)
        if status_info:
            return status_info
        else:
            return {
                "port": port,
                "connected": False,
                "message": "Port not connected"
            }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status error: {str(e)}"
        )


@router.get("/connections")
async def get_all_connections():
    try:
        connections = usb_serial_service.get_all_connections()
        return {
            "connections": connections,
            "count": len(connections)
        }
    except Exception as e:
        logger.error(f"Error getting connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connections error: {str(e)}"
        )


@router.post("/send")
async def send_data(request: SendDataRequest):
    try:
        if not usb_serial_service.is_connected(request.port):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Port {request.port} is not connected"
            )
        
        if request.json_data:
            success = usb_serial_service.send_json(request.port, request.json_data)
        elif request.data:
            success = usb_serial_service.send_text(request.port, request.data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either data or json_data must be provided"
            )
        
        if success:
            return {
                "success": True,
                "message": "Data sent successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send data"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Send error: {str(e)}"
        )


@router.get("/receive/{port}")
async def receive_data(port: str, timeout: float = 1.0):
    try:
        if not usb_serial_service.is_connected(port):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Port {port} is not connected"
            )
        
        data = usb_serial_service.receive_data(port, timeout)
        
        if data:
            try:
                text_data = data.decode('utf-8')
                return {
                    "success": True,
                    "data": text_data,
                    "raw": data.hex()
                }
            except UnicodeDecodeError:
                return {
                    "success": True,
                    "raw": data.hex(),
                    "message": "Binary data received"
                }
        else:
            return {
                "success": True,
                "data": None,
                "message": "No data available"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error receiving data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Receive error: {str(e)}"
        )


@router.post("/auto-detect")
async def auto_detect_drone():
    try:
        ports = usb_serial_service.list_ports()
        
        for port in ports:
            if any(keyword in port.description.lower() for keyword in 
                   ['pixhawk', 'px4', 'ardupilot', 'betaflight', 'flight controller', 'usb serial']):
                return {
                    "success": True,
                    "detected": True,
                    "port": port.device,
                    "description": port.description,
                    "suggested_baudrates": [57600, 115200, 9600]
                }
        
        if ports:
            return {
                "success": True,
                "detected": False,
                "ports": [p.device for p in ports],
                "message": "No known flight controller found, but serial ports available"
            }
        else:
            return {
                "success": True,
                "detected": False,
                "message": "No serial ports found"
            }
    except Exception as e:
        logger.error(f"Error auto-detecting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-detect error: {str(e)}"
        )
