# HKAIC 支持调参的机型和飞控

---

## 📋 目录

- [飞控系统](#飞控系统)
- [支持的机型](#支持的机型)
- [详细规格](#详细规格)
- [连接方式](#连接方式)

---

## 🎮 飞控系统

### PX4 飞控

**版本支持:** PX4 v1.11.0+

**支持型号:**
- Pixhawk 1/2/3/4/5/6
- Pixhawk Cube Black/Yellow/Orange/Purple
- Pixracer
- Durandal
- Holybro Kakute H7
- Matek H743
- Omnibus F4/F7
- 及其他兼容PX4的飞控

**核心特性:**
- ✅ 完整的uORB中间件
- ✅ MAVLink通信协议
- ✅ 双闭环PID控制
- ✅ SITL/HITL仿真
- ✅ ROS/ROS2集成

---

### Betaflight 飞控

**版本支持:** Betaflight 4.0+

**支持型号:**
- Betaflight F4/F7/H7系列
- Matek F405/F722/H743
- SpeedyBee F4/F7
- iFlight F4/F7/H7
- T-Motor F4/F7
- 及其他兼容Betaflight的飞控

**核心特性:**
- ✅ 高性能速率控制
- ✅ DShot协议支持
- ✅ Blackbox日志
- ✅ OSD配置
- ✅ 电机协议支持 (PWM/Oneshot/Multishot/DShot)

---

### 其他飞控系统

- **Cleanflight** - 有限支持
- **iNav** - 有限支持
- **Ardupilot** - 计划中

---

## 🚁 支持的机型

### 多旋翼

| 机型类型 | 说明 | 推荐飞控 |
|---------|------|---------|
| **四轴 (X/+)** | 最常见的无人机配置 | PX4/Betaflight |
| **六轴** | 更稳定，适合航拍 | PX4 |
| **八轴** | 大载荷，专业应用 | PX4 |
| **穿越机** | 竞速花飞，灵活快速 | Betaflight |
| **航拍机** | 稳定拍摄，GPS导航 | PX4 |
| **涵道机** | 室内/安全飞行 | Betaflight/PX4 |

---

### 固定翼

| 机型类型 | 说明 | 推荐飞控 |
|---------|------|---------|
| **常规固定翼** | 标准布局飞机 | PX4 |
| **飞翼** | 无尾翼布局 | PX4 |
| **V尾** | 双V尾设计 | PX4 |

---

### VTOL (垂直起降)

| 机型类型 | 说明 | 推荐飞控 |
|---------|------|---------|
| **Tiltrotor** | 倾转旋翼 | PX4 |
| **Tailsitter** | 尾坐式 | PX4 |
| **QuadPlane** | 四轴+固定翼 | PX4 |

---

## 📐 详细规格

### PX4 参数调参范围

| 参数 | 说明 | 默认值 | 范围 |
|------|------|--------|------|
| `MC_ROLL_P` | Roll角度P | 6.5 | 3.0 - 12.0 |
| `MC_PITCH_P` | Pitch角度P | 6.5 | 3.0 - 12.0 |
| `MC_YAW_P` | Yaw角度P | 2.8 | 1.0 - 5.0 |
| `MC_ROLLRATE_P` | Roll速率P | 0.15 | 0.05 - 0.30 |
| `MC_PITCHRATE_P` | Pitch速率P | 0.15 | 0.05 - 0.30 |
| `MC_YAWRATE_P` | Yaw速率P | 0.2 | 0.1 - 0.4 |
| `MC_ROLLRATE_I` | Roll速率I | 0.2 | 0.05 - 0.5 |
| `MC_ROLLRATE_D` | Roll速率D | 0.003 | 0.001 - 0.01 |

---

### Betaflight 参数调参范围

| 参数 | 说明 | 默认值 | 范围 |
|------|------|--------|------|
| `roll_p` | Roll P | 4.5 | 2.0 - 8.0 |
| `pitch_p` | Pitch P | 4.5 | 2.0 - 8.0 |
| `yaw_p` | Yaw P | 8.0 | 4.0 - 15.0 |
| `roll_i` | Roll I | 80 | 40 - 150 |
| `pitch_i` | Pitch I | 80 | 40 - 150 |
| `yaw_i` | Yaw I | 45 | 20 - 100 |
| `roll_d` | Roll D | 30 | 10 - 60 |
| `pitch_d` | Pitch D | 30 | 10 - 60 |

---

## 🔌 连接方式

### USB 串口连接

**适用系统:** Windows / macOS / Linux

**波特率选项:**
- 9600 (调试)
- 57600 (默认)
- 115200 (高速)
- 230400 (极速)

**连接步骤:**
1. 用USB线连接飞控
2. 在HKAIC中点击"连接USB"
3. 选择串口号和波特率
4. 点击"连接"

---

### MAVSDK 连接

**适用系统:** PX4

**连接方式:**
- UDP (仿真/SITL)
- 串口 (USB/TTL)
- TCP

---

## 📝 备注

### 机型特点与调参建议

#### 竞速穿越机 (Betaflight)
- 高响应速度
- 建议P值较高，D值适中
- 竞速模式预设已优化

#### 航拍机 (PX4)
- 稳定性优先
- 建议P值适中，D值较高
- GPS/气压计辅助

#### 大载荷无人机
- 需要更强的D值阻尼
- 建议降低P值
- 载重模式预设

---

### 常见配置预设

| 预设名称 | 适用场景 | 特点 |
|---------|---------|------|
| **竞速** | FPV比赛 | 高响应，激进 |
| **花飞** | 花式飞行 | 灵活，易操控 |
| **航拍** | 稳定拍摄 | 平滑，高阻尼 |
| **载重** | 负载飞行 | 稳定，保守 |

---

## 🔧 技术支持

如遇到特定机型或飞控的调参问题，请:
1. 检查 [PROJECT_INTRODUCTION.md](./PROJECT_INTRODUCTION.md)
2. 参考 [PX4_PID_GUIDE.md](./TUNING_GUIDES/PX4_PID_GUIDE.md) 或 [BETAFLIGHT_PID_GUIDE.md](./TUNING_GUIDES/BETAFLIGHT_PID_GUIDE.md)
3. 联系技术支持

---

*最后更新: 2026-05-21*
