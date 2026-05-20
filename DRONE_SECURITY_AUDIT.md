# HKAIC SaaS - 无人机控制功能安全审计报告

**审计日期:** 2026-05-19  
**审计范围:** 无人机连接和控制功能  
**版本:** 2.1.0

---

## 📋 执行摘要

本次安全审计针对 HKAIC SaaS 新增的无人机控制功能进行了全面检查。发现了 **15 个安全问题**，其中：

- 🚨 **严重（Critical）:** 5 个
- ⚠️ **高（High）:** 6 个  
- ⚡ **中（Medium）:** 4 个

---

## 🚨 严重安全问题（Critical）

### 1. 连接 URI 无验证 - 任意网络连接 (CRITICAL)

**位置:** [drone_manager.py:90-174](file:///workspace/hkaic/backend/app/drone_manager.py#L90-L174)

**问题描述:**
用户可以指定任意连接 URI，可能导致：
- 连接到内网服务 (`tcp://192.168.1.1:22`)
- 端口扫描攻击
- 连接到恶意设备

**风险:**
```
攻击者可以指定 connection_uri: "tcp://127.0.0.1:22" 
尝试连接到 SSH 端口进行扫描或攻击
```

**修复建议:**
```python
ALLOWED_URI_PREFIXES = ["udp://", "tcp://", "serial://"]
BLOCKED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

def validate_connection_uri(uri: str) -> bool:
    """验证连接 URI 是否安全"""
    if not any(uri.startswith(prefix) for prefix in ALLOWED_URI_PREFIXES):
        return False
    
    # 阻止连接到本地服务
    parsed = urlparse(uri)
    if parsed.hostname in BLOCKED_HOSTS:
        return False
    
    return True
```

---

### 2. 坐标无范围验证 - 危险飞行指令 (CRITICAL)

**位置:** [drone_manager.py:449-495](file:///workspace/hkaic/backend/app/drone_manager.py#L449-L495)

**问题描述:**
经纬度坐标没有范围验证：
- 纬度应为 -90 到 90
- 经度应为 -180 到 180
- 高度应有上下限

**风险:**
```
用户可以发送无效坐标：
latitude: 999999  (无效)
longitude: -999999 (无效)
altitude: 99999   (危险高度)

这可能导致无人机行为异常或坠毁
```

**修复建议:**
```python
def validate_coordinates(latitude: float, longitude: float, altitude: float) -> Dict[str, Any]:
    """验证坐标是否在安全范围内"""
    errors = []
    
    if not -90 <= latitude <= 90:
        errors.append(f"Invalid latitude: {latitude} (must be -90 to 90)")
    
    if not -180 <= longitude <= 180:
        errors.append(f"Invalid longitude: {longitude} (must be -180 to 180)")
    
    if not 0 <= altitude <= 120:  # 最大 120 米
        errors.append(f"Invalid altitude: {altitude} (must be 0 to 120 meters)")
    
    if errors:
        return {"valid": False, "errors": errors}
    
    return {"valid": True}
```

---

### 3. 高度无限制 - 危险飞行 (CRITICAL)

**位置:** [drone_manager.py:363-393](file:///workspace/hkaic/backend/app/drone_manager.py#L363-L393)

**问题描述:**
起飞高度没有上限验证，可能导致：
- 超出法规限制高度
- GPS 信号丢失
- 无人机失控

**风险:**
```
altitude: 5000  # 5公里高度 - 极度危险
altitude: -100  # 负高度 - 不可能
```

**修复建议:**
```python
MAX_TAKEOFF_ALTITUDE = 120  # 米，符合大多数法规
MIN_TAKEOFF_ALTITUDE = 0.5  # 最小 0.5 米

async def takeoff_drone(self, drone_id: str, altitude: float = 2.0) -> Dict[str, Any]:
    if altitude > MAX_TAKEOFF_ALTITUDE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Takeoff altitude exceeds maximum allowed ({MAX_TAKEOFF_ALTITUDE}m)"
        )
    
    if altitude < MIN_TAKEOFF_ALTITUDE:
        altitude = MIN_TAKEOFF_ALTITUDE
```

---

### 4. 缺少用户-无人机绑定 - 权限控制缺失 (CRITICAL)

**位置:** [drone_manager.py](file:///workspace/hkaic/backend/app/drone_manager.py) 和 [drone.py](file:///workspace/hkaic/backend/app/api/drone.py)

**问题描述:**
任何认证用户可以控制任何无人机，没有访问控制：
- 用户 A 可以控制用户 B 的无人机
- 没有租户隔离
- 没有所有权验证

**风险:**
```
用户 1 创建了无人机 "drone-001"
用户 2 可以发送 arm/takeoff/land 命令给 "drone-001"
这可能导致：
- 劫持他人无人机
- 恶意操控他人设备
- 造成财产损失或人身伤害
```

**修复建议:**
```python
class DroneConnection:
    def __init__(self, drone_id: str, connection_uri: str, owner_id: int):
        self.drone_id = drone_id
        self.connection_uri = connection_uri
        self.owner_id = owner_id  # 添加所有者 ID
        # ...

async def verify_drone_ownership(drone_id: str, user_id: int, db: Session) -> bool:
    """验证用户是否有权控制该无人机"""
    connection = drone_manager._connections.get(drone_id)
    if not connection:
        return False
    
    return connection.owner_id == user_id
```

---

### 5. 无人机 ID 无格式验证 - 注入风险 (CRITICAL)

**位置:** [drone_manager.py:68](file:///workspace/hkaic/backend/app/drone_manager.py#L68) 和 [drone.py](file:///workspace/hkaic/backend/app/api/drone.py)

**问题描述:**
无人机 ID 没有格式验证或清理：
- 可以包含特殊字符
- 可能用于路径遍历（如果用于文件路径）
- 可能包含恶意代码

**风险:**
```
drone_id: "../../../etc/passwd"
drone_id: "'; DROP TABLE drones; --"
drone_id: "<script>alert('xss')</script>"
```

**修复建议:**
```python
import re

def validate_drone_id(drone_id: str) -> bool:
    """验证无人机 ID 格式"""
    # 只允许字母、数字、连字符和下划线
    pattern = r'^[a-zA-Z0-9_-]{1,64}$'
    return bool(re.match(pattern, drone_id))

def sanitize_drone_id(drone_id: str) -> str:
    """清理无人机 ID"""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', drone_id)[:64]
```

---

## ⚠️ 高安全问题（High）

### 6. 无连接数量限制 - 拒绝服务 (HIGH)

**问题:** 没有限制单个用户或全局的无人机连接数

**风险:** 攻击者可以创建大量连接耗尽资源

**修复建议:**
```python
MAX_CONNECTIONS_PER_USER = 5
MAX_TOTAL_CONNECTIONS = 100

async def connect_drone(self, drone_id: str, connection_uri: str, user_id: int) -> Dict:
    user_connections = sum(1 for c in self._connections.values() if c.owner_id == user_id)
    if user_connections >= MAX_CONNECTIONS_PER_USER:
        raise HTTPException(status_code=403, detail="Connection limit reached")
```

---

### 7. 无操作频率限制 - 滥用风险 (HIGH)

**问题:** 没有限制用户发送命令的频率

**风险:** 快速发送大量命令可能导致无人机行为异常或崩溃

**修复建议:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/arm")
@limiter.limit("10/minute")  # 每分钟最多 10 次
async def arm_drone(...):
    pass
```

---

### 8. 缺少操作审计日志 (HIGH)

**问题:** 飞行控制操作没有记录到审计日志

**风险:** 无法追踪谁在何时执行了什么操作

**修复建议:**
```python
async def arm_drone(self, drone_id: str, user_id: int) -> Dict:
    audit_log = {
        "action": "arm",
        "drone_id": drone_id,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": "success"
    }
    await save_audit_log(audit_log)
    logger.info(f"AUDIT: User {user_id} armed drone {drone_id}")
```

---

### 9. 缺少订阅等级控制 (HIGH)

**问题:** 所有认证用户都有完整的无人机控制权限

**风险:** 免费用户也可以控制真实无人机，可能导致滥用

**修复建议:**
```python
# 在数据库中添加无人机控制权限
TIER_PERMISSIONS = {
    "free": {"can_connect": False, "can_control": False},
    "basic": {"can_connect": True, "can_control": True, "max_drones": 1},
    "pro": {"can_connect": True, "can_control": True, "max_drones": 5},
    "enterprise": {"can_connect": True, "can_control": True, "max_drones": -1}
}

def check_drone_permission(tier: str, action: str) -> bool:
    return TIERS_PERMISSIONS.get(tier, {}).get(f"can_{action}", False)
```

---

### 10. 模拟模式无警告标记 (HIGH)

**位置:** [drone_manager.py:151-165](file:///workspace/hkaic/backend/app/drone_manager.py#L151-L165)

**问题:** 模拟连接成功时没有明确的安全警告

**风险:** 用户可能误以为在控制真实无人机

**修复建议:**
```python
if simulated:
    logger.warning(f"SIMULATED connection to drone {drone_id} - NOT A REAL DRONE!")
    return {
        "success": True,
        "message": f"[SIMULATION MODE] Connected to drone {drone_id}",
        "status": "connected",
        "simulated": True,
        "warning": "This is a simulated drone. No real flight will occur."
    }
```

---

### 11. 缺少紧急停止机制 (HIGH)

**问题:** 没有紧急停止所有操作的端点

**风险:** 出现异常时无法快速停止所有无人机

**修复建议:**
```python
@router.post("/emergency-stop", response_model=MessageResponse)
async def emergency_stop(current_user: User = Depends(get_current_user)):
    """
    Emergency stop - Land all drones immediately
    """
    logger.critical(f"EMERGENCY STOP triggered by user {current_user.id}")
    
    results = []
    for drone_id in drone_manager.list_drones():
        result = await drone_manager.emergency_land(drone_id)
        results.append({"drone_id": drone_id, "result": result})
    
    return {
        "message": "Emergency stop executed",
        "details": results
    }
```

---

## ⚡ 中等问题（Medium）

### 12. 异常消息泄露系统信息 (MEDIUM)

**位置:** 多个端点的 except 块

**问题:** 错误消息可能泄露内部系统信息

**示例:**
```python
# 不好 - 泄露内部错误
raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

# 好 - 通用错误消息
raise HTTPException(status_code=500, detail="Connection failed. Please try again.")
```

---

### 13. 缺少连接超时设置 (MEDIUM)

**问题:** 连接操作没有超时设置，可能导致请求挂起

**修复建议:**
```python
import asyncio

async def connect_drone_with_timeout(uri: str, timeout: float = 30.0) -> Dict:
    try:
        return await asyncio.wait_for(
            connect_drone_impl(uri),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return {"success": False, "message": "Connection timeout"}
```

---

### 14. 缺少定期健康检查 (MEDIUM)

**问题:** 没有定期检查无人机连接状态

**修复建议:**
```python
async def health_check_task():
    """定期检查所有无人机连接状态"""
    while True:
        await asyncio.sleep(60)  # 每分钟检查一次
        for drone_id, connection in drone_manager._connections.items():
            if connection.status == DroneConnectionStatus.CONNECTED:
                # 检查最后更新时间
                if connection.telemetry.last_update:
                    age = datetime.now() - connection.telemetry.last_update
                    if age > timedelta(minutes=5):
                        logger.warning(f"Drone {drone_id} telemetry stale")
```

---

### 15. API 文档缺乏安全警告 (MEDIUM)

**问题:** OpenAPI 文档没有安全使用警告

**修复建议:**
```python
@router.post("/takeoff", response_model=DroneActionResponse)
async def takeoff_drone(
    request: DroneTakeoffRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Command drone to takeoff
    
    ⚠️ SAFETY WARNING: This sends actual flight commands to a real drone.
    Ensure proper safety measures are in place before use.
    
    Requires authentication
    """
    pass
```

---

## 📊 问题统计

| 严重程度 | 数量 | 状态 |
|---------|------|------|
| Critical | 5 | 需要立即修复 |
| High | 6 | 尽快修复 |
| Medium | 4 | 应该修复 |

---

## 🎯 修复优先级

### P0 - 立即修复（上线前）
1. ✅ URI 验证
2. ✅ 坐标范围验证
3. ✅ 高度限制
4. ✅ 用户-无人机绑定
5. ✅ 无人机 ID 格式验证

### P1 - 上线后第一周
6. 连接数量限制
7. 操作频率限制
8. 审计日志
9. 订阅等级控制
10. 模拟模式警告

### P2 - 后续迭代
11. 紧急停止机制
12. 异常消息清理
13. 超时设置
14. 健康检查
15. API 文档安全警告

---

## 🔒 安全建议总结

### 必须修复项（生产环境部署前）
- ✅ 实现 URI 白名单验证
- ✅ 添加坐标和高度范围检查
- ✅ 实现用户-无人机所有权验证
- ✅ 添加无人机 ID 格式验证
- ✅ 实施订阅等级权限控制

### 推荐实施项
- 添加速率限制
- 实现审计日志
- 添加紧急停止功能
- 改进错误消息
- 添加安全警告

---

**审计完成时间:** 2026-05-19  
**审计人:** AI Security Auditor  
**下次审计计划:** 2026-06-19
