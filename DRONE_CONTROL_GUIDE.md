# HKAIC - Drone Control Feature Guide

## Overview

This feature adds real drone connection and control capabilities to HKAIC SaaS using MAVSDK. You can now connect to real or simulated drones, view telemetry, and send flight commands.

## Key Features

- Connect to multiple drones simultaneously
- Real-time telemetry monitoring (position, attitude, battery, etc.)
- Basic flight commands: arm/disarm, takeoff, land, return to home
- Position control (goto waypoints)
- Simulated drone support for testing

## API Endpoints

### Authentication Required

All drone control endpoints require a valid JWT token.

### Connection Management

#### `POST /api/drone/connect`
Connect to a drone.

**Request Body:**
```json
{
  "drone_id": "drone-001",
  "connection_uri": "udp://:14540"
}
```

**Connection URIs:**
- `udp://:14540` - UDP connection (for PX4 SITL simulation)
- `serial:///dev/ttyUSB0` - Serial connection (USB telemetry radios)
- `tcp://192.168.1.100:5760` - TCP connection

#### `POST /api/drone/disconnect`
Disconnect from a drone.

**Request Body:**
```json
{
  "drone_id": "drone-001"
}
```

#### `GET /api/drone/list`
List all connected drones.

#### `GET /api/drone/status/{drone_id}`
Get detailed status and telemetry for a specific drone.

### Flight Control

#### `POST /api/drone/arm`
Arm the drone motors.

**Request Body:**
```json
{
  "drone_id": "drone-001"
}
```

#### `POST /api/drone/disarm`
Disarm the drone motors.

**Request Body:**
```json
{
  "drone_id": "drone-001"
}
```

#### `POST /api/drone/takeoff`
Takeoff to specified altitude.

**Request Body:**
```json
{
  "drone_id": "drone-001",
  "altitude": 2.0
}
```

#### `POST /api/drone/land`
Land the drone.

**Request Body:**
```json
{
  "drone_id": "drone-001"
}
```

#### `POST /api/drone/return-home`
Return to home position.

**Request Body:**
```json
{
  "drone_id": "drone-001"
}
```

#### `POST /api/drone/goto`
Fly to specified coordinates.

**Request Body:**
```json
{
  "drone_id": "drone-001",
  "latitude": 47.397742,
  "longitude": 8.545594,
  "altitude": 10.0
}
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Running with PX4 SITL (Simulation)

For testing without a real drone, you can use the PX4 Software-in-the-Loop simulator.

#### Option A: Using Docker (Recommended)

```bash
# Run PX4 SITL in Docker
docker run -d --name px4-sitl \
  -p 14540:14540/udp \
  jonasvautherin/px4-gazebo-headless:latest
```

#### Option B: Building PX4 from Source

```bash
# Clone PX4 repository
git clone https://github.com/PX4/PX4-Autopilot.git
cd PX4-Autopilot
git submodule update --init --recursive

# Run SITL simulation
make px4_sitl gazebo-classic
```

### 3. Connecting via HKAIC

Start the HKAIC backend:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

Then use the API to connect:
```bash
curl -X POST http://localhost:8000/api/drone/connect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"drone_id": "sim-drone", "connection_uri": "udp://:14540"}'
```

### 4. Real Drone Connection

#### PX4 Drone with Telemetry Radio

1. Connect your telemetry radio to your computer via USB
2. Identify the serial port (typically `/dev/ttyUSB0` on Linux, `COM3` on Windows)
3. Use connection URI like `serial:///dev/ttyUSB0`

#### DJI Drone

For DJI drones, you would need additional integration with the DJI Onboard SDK.

## Architecture

### Drone Manager (`app/drone_manager.py`)

- `DroneManager` - Singleton managing all drone connections
- `DroneConnection` - Single drone connection instance
- `DroneTelemetry` - Telemetry data structure

### API (`app/api/drone.py`)

- REST endpoints for all drone operations
- Authentication required for all actions
- Full error handling and logging

## Safety Considerations

⚠️ **IMPORTANT SAFETY NOTES:**

1. Always test new code in simulation first
2. Have a safety pilot ready with manual override capabilities
3. Fly in approved areas only
4. Follow all local aviation regulations
5. Never fly near people, animals, or obstacles
6. Ensure adequate battery levels before flight
7. Set appropriate geofence limits
8. Always have a return-to-home failsafe configured

## Troubleshooting

### Drone won't connect

- Verify connection URI is correct
- Check if drone is powered on
- For SITL, verify simulator is running
- Check network/firewall settings

### Commands not responding

- Ensure drone is armed before takeoff
- Check that you have GPS lock
- Verify battery level is sufficient
- Check if drone is in correct flight mode

### MAVSDK ImportError

If you see "MAVSDK not installed" warnings, install it:

```bash
pip install mavsdk
```

## Future Enhancements

- WebSocket for real-time telemetry streaming
- Mission planning and execution
- Camera control and image capture
- Gimbal control
- Advanced flight modes (follow-me, orbit, etc.)
- Multiple vehicle coordination
- ROS2 integration for advanced autonomy

## Example Usage

```python
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. Connect to drone
response = requests.post(f"{BASE_URL}/api/drone/connect", 
    headers=headers,
    json={"drone_id": "my-drone", "connection_uri": "udp://:14540"}
)
print("Connect:", response.json())

# 2. Check status
response = requests.get(f"{BASE_URL}/api/drone/status/my-drone", headers=headers)
print("Status:", response.json())

# 3. Arm and takeoff
requests.post(f"{BASE_URL}/api/drone/arm", headers=headers, json={"drone_id": "my-drone"})
requests.post(f"{BASE_URL}/api/drone/takeoff", headers=headers, 
    json={"drone_id": "my-drone", "altitude": 5.0})

# 4. Fly somewhere
requests.post(f"{BASE_URL}/api/drone/goto", headers=headers,
    json={
        "drone_id": "my-drone", 
        "latitude": 47.397742,
        "longitude": 8.545594,
        "altitude": 10.0
    })

# 5. Land
requests.post(f"{BASE_URL}/api/drone/land", headers=headers, json={"drone_id": "my-drone"})

# 6. Disconnect
requests.post(f"{BASE_URL}/api/drone/disconnect", headers=headers, json={"drone_id": "my-drone"})
```
