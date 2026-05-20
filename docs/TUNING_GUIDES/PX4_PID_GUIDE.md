# PX4 PID调参完全指南

**版本:** 1.11.0+  
**适用平台:** HKAIC  
**难度:** 中高级

---

## 📚 目录

1. [PX4简介](#px4简介)
2. [PID控制器基础](#pid控制器基础)
3. [多旋翼控制器架构](#多旋翼控制器架构)
4. [基础调参步骤](#基础调参步骤)
5. [高级调参技术](#高级调参技术)
6. [常见问题与解决方案](#常见问题与解决方案)
7. [HKAIC分析集成](#hkaic分析集成)

---

## 🚀 PX4简介

PX4是行业标准的开源无人机飞控系统，支持：
- 多旋翼（Quadrotor, Hexarotor, Octocopter等）
- 固定翼飞机
- VTOL（垂直起降）
- Rover（无人车）
- 水下航行器

**关键特性:**
- uORB发布/订阅中间件
- DDS/ROS 2集成
- MAVLink通信协议
- SITL（软件在环）仿真
- NuttX实时操作系统

**官方资源:**
- 文档: https://docs.px4.io/
- GitHub: https://github.com/PX4/PX4-Autopilot
- 社区论坛: https://discuss.px4.io/

---

## ⚙️ PID控制器基础

### 什么是PID?

PID代表**比例（Proportional）**、**积分（Integral）**、**微分（Derivative）**，是无人机控制的核心算法。

### PID各参数作用

| 参数 | 作用 | 调大时效果 | 调大时风险 |
|------|------|-----------|-----------|
| **P (比例)** | 根据误差大小产生控制力 | 响应更快 | 可能振荡 |
| **I (积分)** | 消除稳态误差 | 消除漂移 | 响应迟缓 |
| **D (微分)** | 预测误差变化趋势 | 减少过冲 | 噪声敏感 |

### PX4中的PID实现

```
控制输出 = P×误差 + I×误差积分 + D×误差微分
```

---

## 🎛️ 多旋翼控制器架构

### 双闭环控制

PX4使用**双闭环控制**：

```
外环（位置控制）          内环（速率控制）
┌─────────────┐          ┌─────────────┐
│ 期望位置    │          │ 期望速率    │
└──────┬──────┘          └──────┬──────┘
       │                        │
       ▼                        ▼
┌─────────────┐          ┌─────────────┐
│ 位置误差    │          │ 速率误差    │
│ ─────────── │          │ ─────────── │
│ P控制器     │          │ PID控制器   │
└──────┬──────┘          └──────┬──────┘
       │                        │
       └────────┬───────────────┘
                │
                ▼
         ┌─────────────┐
         │ 电机控制    │
         │ PWM输出     │
         └─────────────┘
```

### 关键参数层级

#### 1. 外环（姿态控制）
- `MC_ROLL_P` - Roll角度P
- `MC_PITCH_P` - Pitch角度P
- `MC_YAW_P` - Yaw角度P

#### 2. 内环（速率控制）
- `MC_ROLLRATE_P` - Roll速率P
- `MC_ROLLRATE_I` - Roll速率I
- `MC_ROLLRATE_D` - Roll速率D
- `MC_PITCHRATE_P` - Pitch速率P
- `MC_PITCHRATE_I` - Pitch速率I
- `MC_PITCHRATE_D` - Pitch速率D
- `MC_YAWRATE_P` - Yaw速率P
- `MC_YAWRATE_I` - Yaw速率I
- `MC_YAWRATE_D` - Yaw速率D

---

## 🔧 基础调参步骤

### 阶段1: 初始设置

#### 1.1 基础参数配置

```python
# 推荐初始参数（Quadrotor X构型）
initial_params = {
    # 速率环
    "MC_ROLLRATE_P": 0.15,
    "MC_ROLLRATE_I": 0.05,
    "MC_ROLLRATE_D": 0.003,
    "MC_PITCHRATE_P": 0.15,
    "MC_PITCHRATE_I": 0.05,
    "MC_PITCHRATE_D": 0.003,
    "MC_YAWRATE_P": 0.15,
    "MC_YAWRATE_I": 0.05,
    "MC_YAWRATE_D": 0.000,
    
    # 姿态环
    "MC_ROLL_P": 6.5,
    "MC_PITCH_P": 6.5,
    "MC_YAW_P": 6.0,
    
    # 推力参数
    "MC_ROLL_TC": 0.15,
    "MC_PITCH_TC": 0.15,
}
```

#### 1.2 滤波器设置

```python
# D项低通滤波器（重要！）
filter_params = {
    # 陀螺仪低通滤波
    "IMU_GYRO_CUTOFF": 100,  # Hz
    
    # D项低通滤波
    "MC_DTERM_CUTOFF": 100,  # Hz
    
    # Notch滤波器（振动大时启用）
    "IMU_INTEG_RATE": 400,  # Hz
}
```

---

### 阶段2: 速率环调参

#### 2.1 Roll/Pitch速率P调参

**目标:** 快速响应，无持续振荡

**测试方法:**
1. 切换到Manual/Stabilized模式
2. 快速向左向右打杆
3. 观察无人机响应

**调节规则:**

| 观察现象 | 问题原因 | 调整方法 |
|---------|---------|---------|
| 响应迟缓 | P太小 | 增加P值 |
| 快速振荡 | P太大 | 减小P值 |
| 颤抖/抖动 | P太大或噪声 | 减小P，检查滤波器 |

**调节步骤:**
```python
# 从0.10开始，每次增加0.01
test_sequence = [0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20]

# 找到最佳值后，测试D项
# D的作用：减少过冲和振荡
# D从0.001开始，逐渐增加
d_tests = [0.001, 0.002, 0.003, 0.004, 0.005]
```

#### 2.2 速率I调参

**目标:** 消除稳态误差（漂移）

**测试方法:**
1. 悬停时观察是否漂移
2. 做动作后是否回到原位

**调节规则:**

| 观察现象 | 问题原因 | 调整方法 |
|---------|---------|---------|
| 持续漂移 | I太小 | 增加I值 |
| 响应迟缓 | I太大 | 减小I值 |
| 振荡后漂移 | I太大 | 减小I值 |

**调节步骤:**
```python
# I值通常在P的1/3到1/5之间
# 从0.02开始测试
i_tests = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07]
```

---

### 阶段3: D项优化（关键）

D项是最敏感的参数，需要细心调整。

#### 3.1 D的作用

- **抑制过冲**: 预测误差变化，提前减速
- **增加阻尼**: 减少振荡
- **噪声放大**: 高频振动会被放大

#### 3.2 调节步骤

```python
# 步骤1: 找到合适的D值
# 目标: 无过冲，无颤抖
d_test_values = [
    0.001,  # 初始值
    0.002,
    0.003,  # 通常最佳值
    0.004,
    0.005,
]

# 步骤2: 调整滤波器
# D值越大，需要越低的截止频率
d_filter_mapping = {
    0.001: 100,  # D小可以用高截止频率
    0.002: 90,
    0.003: 80,
    0.004: 70,
    0.005: 60,
}
```

#### 3.3 D项故障排除

| 现象 | 原因 | 解决方案 |
|-----|------|---------|
| 颤抖 | D太大或噪声 | 减小D或降低MC_DTERM_CUTOFF |
| 无效果 | D太小 | 增加D |
| 响应迟缓 | D太大 | 减小D |

---

### 阶段4: 姿态环调参

#### 4.1 Roll/Pitch角度P

```python
# 角度P控制角度跟踪
angle_p_tests = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]

# 调节规则
adjustment_rules = {
    "undershoot": "增加P",  # 角度跟不上
    "overshoot": "减小P",   # 超过期望角度
    "oscillation": "减小P",  # 振荡
}
```

#### 4.2 时间常数

```python
# MC_ROLL_TC 和 MC_PITCH_TC
# 控制角度到速率的转换速度
tc_values = [0.10, 0.12, 0.15, 0.18, 0.20, 0.25]

# 调节规则
# TC越小: 响应越快，但可能振荡
# TC越大: 响应越平滑，但可能迟缓
```

---

## 🎯 高级调参技术

### 1. Notch滤波器配置

**作用:** 消除特定频率的振动（如电机安装共振）

```python
# 动态Notch滤波器
notch_params = {
    # 自动检测并滤除振动
    "IMU_GYRO_NF1_BW": 20,    # 带宽Hz
    "IMU_GYRO_NF1_FREQ": 80,  # 中心频率Hz
    
    # 多重Notch（更宽频率范围）
    "IMU_GYRO_NF2_BW": 30,
    "IMU_GYRO_NF2_FREQ": 120,
}
```

**HKAIC分析建议:**
```python
# 基于振动分析自动建议Notch频率
def suggest_notch_filter(vibration_data):
    # 找到振动峰值频率
    peak_freq = find_peak_frequency(vibration_data)
    
    return {
        "IMU_GYRO_NF1_FREQ": peak_freq,
        "IMU_GYRO_NF1_BW": 20,
        "suggestion": f"检测到{peak_freq}Hz振动，建议启用Notch滤波"
    }
```

---

### 2. 推力参数优化

```python
# 推力曲线（非线性）
thrust_params = {
    # 默认值（线性）
    "MPC_THR_HOVER": 0.5,  # 悬停推力50%
    
    # 曲线参数
    "MPC_THR_CURVE": 0,   # 0=线性，1=曲线
    
    # 最小推力
    "MPC_Z_VEL_MAX_UP": 3.0,    # 最大上升速度 m/s
    "MPC_Z_VEL_MAX_DN": 1.5,    # 最大下降速度 m/s
}
```

---

### 3. 自适应控制

PX4支持**MAVLink参数协议**，可远程调参：

```python
# 使用MAVSDK进行远程调参
from mavsdk import System
from mavsdk.param import ParamType

async def tune_pid_remotely():
    drone = System()
    await drone.connect()
    
    # 读取当前P值
    p_value = await drone.param.get_param_float("MC_ROLLRATE_P")
    print(f"当前P值: {p_value}")
    
    # 动态调整
    await drone.param.set_param_float("MC_ROLLRATE_P", 0.16)
    
    # 保存参数
    await drone.param.save_params()
```

---

## ❓ 常见问题与解决方案

### 问题1: 快速振荡

**症状:** Roll/Pitch快速来回摆动

**原因:** P值太大或D值太小

**解决:**
```python
# 立即执行
adjustments = {
    "MC_ROLLRATE_P": "减小0.02",
    "MC_PITCHRATE_P": "减小0.02",
    "MC_ROLLRATE_D": "增加0.001",
    "MC_PITCHRATE_D": "增加0.001",
}
```

---

### 问题2: 颤抖/抖动

**症状:** 电机发出高频颤抖声，机身微震

**原因:** 
- D项太大（放大噪声）
- 滤波器截止频率太高
- 机械松动

**解决:**
```python
adjustments = {
    # 方案1: 减小D
    "MC_ROLLRATE_D": "减小0.001",
    "MC_PITCHRATE_D": "减小0.001",
    
    # 方案2: 降低D项滤波器
    "MC_DTERM_CUTOFF": "从100降到80或60",
    
    # 方案3: 降低陀螺仪滤波器
    "IMU_GYRO_CUTOFF": "从100降到80",
}
```

---

### 问题3: 持续漂移

**症状:** 不打杆时缓慢漂移

**原因:** I值太小

**解决:**
```python
adjustments = {
    "MC_ROLLRATE_I": "增加0.02",
    "MC_PITCHRATE_I": "增加0.02",
    "MC_YAWRATE_I": "增加0.02",
}
```

---

### 问题4: 过冲后振荡

**症状:** 响应超调，然后小幅振荡

**原因:** D值太小

**解决:**
```python
adjustments = {
    "MC_ROLLRATE_D": "增加0.001",
    "MC_PITCHRATE_D": "增加0.001",
}
```

---

### 问题5: 低速时不稳定

**症状:** 飞行速度低时摇晃

**原因:** P值太小或I值太小

**解决:**
```python
# 通常增加I值有效
adjustments = {
    "MC_ROLLRATE_I": "增加0.01",
    "MC_PITCHRATE_I": "增加0.01",
}
```

---

### 问题6: 振动导致失控

**症状:** 高推力时剧烈振动

**原因:** 
- 桨叶不平衡
- 电机座松动
- 滤波器设置不当

**解决:**
```python
# 立即降低滤波器截止频率
emergency_adjustments = {
    "IMU_GYRO_CUTOFF": 60,      # 降到60Hz
    "MC_DTERM_CUTOFF": 60,      # 降到60Hz
}

# 同时检查机械问题
mechanical_check = [
    "检查桨叶平衡",
    "检查电机安装",
    "检查减震球状态",
]
```

---

## 🔍 HKAIC分析集成

### 1. 自动PID分析

HKAIC可以分析你的飞行日志并提供PID建议：

```python
class PIDAnalyzer:
    """基于飞行日志的PID分析"""
    
    def analyze(self, flight_log):
        """
        分析飞行日志并给出建议
        """
        results = {
            'roll_analysis': self.analyze_axis(flight_log, 'roll'),
            'pitch_analysis': self.analyze_axis(flight_log, 'pitch'),
            'yaw_analysis': self.analyze_axis(flight_log, 'yaw'),
        }
        
        return results
    
    def analyze_axis(self, log, axis):
        """分析单个轴"""
        data = self.extract_axis_data(log, axis)
        
        # 检测问题
        issues = []
        
        if self.detect_oscillation(data):
            issues.append({
                'type': 'oscillation',
                'severity': 'high',
                'suggestion': '减小P值或增加D值',
                'params': [f'MC_{axis.upper()}RATE_P', f'MC_{axis.upper()}RATE_D']
            })
        
        if self.detect_drift(data):
            issues.append({
                'type': 'drift',
                'severity': 'medium',
                'suggestion': '增加I值',
                'params': [f'MC_{axis.upper()}RATE_I']
            })
        
        if self.detect_noise(data):
            issues.append({
                'type': 'noise',
                'severity': 'high',
                'suggestion': '减小D值或降低滤波器频率',
                'params': ['MC_DTERM_CUTOFF', f'MC_{axis.upper()}RATE_D']
            })
        
        return {
            'issues': issues,
            'metrics': self.calculate_metrics(data),
            'recommendations': self.generate_recommendations(issues)
        }
```

### 2. 振动分析

```python
class VibrationAnalyzer:
    """振动分析与Notch滤波建议"""
    
    def analyze_vibration(self, flight_log):
        """分析振动数据"""
        vib_data = flight_log.vibration
        
        # 找到主要振动频率
        dominant_freq = self.find_dominant_frequency(vib_data)
        
        # 检测谐波
        harmonics = self.find_harmonics(dominant_freq)
        
        return {
            'dominant_frequency': dominant_freq,
            'harmonics': harmonics,
            'severity': self.assess_severity(vib_data),
            'suggestions': [
                {
                    'param': 'IMU_GYRO_NF1_FREQ',
                    'value': dominant_freq,
                    'reason': f'检测到{dominant_freq}Hz主振动'
                },
                {
                    'param': 'IMU_GYRO_NF1_BW',
                    'value': 20,
                    'reason': '标准带宽设置'
                }
            ]
        }
```

### 3. 性能评估

```python
class PerformanceEvaluator:
    """飞行性能评估"""
    
    def evaluate(self, flight_log):
        """综合性能评估"""
        
        metrics = {
            'stability': self.calculate_stability(flight_log),
            'responsiveness': self.calculate_responsiveness(flight_log),
            'efficiency': self.calculate_efficiency(flight_log),
            'control_quality': self.calculate_control_quality(flight_log),
        }
        
        # 综合评分
        overall_score = sum(metrics.values()) / len(metrics)
        
        return {
            'metrics': metrics,
            'overall_score': overall_score,
            'grade': self.get_grade(overall_score),
            'recommendations': self.generate_recommendations(metrics)
        }
    
    def calculate_stability(self, log):
        """稳定性评分（0-100）"""
        # 基于姿态误差标准差
        roll_error_std = log.roll - log.roll_setpoint
        pitch_error_std = log.pitch - log.pitch_setpoint
        
        stability = 100 - (roll_error_std + pitch_error_std) * 10
        return max(0, min(100, stability))
    
    def get_grade(self, score):
        """评分转等级"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'
```

---

## 📊 HKAIC自动调参流程

### 完整分析流程

```python
# HKAIC PID优化流程
async def optimize_pid_with_hkaic(flight_log_path):
    """
    使用HKAIC进行PID优化的完整流程
    """
    # 1. 解析飞行日志
    log = await parse_flight_log(flight_log_path)
    
    # 2. 执行多维度分析
    analysis_results = {
        'pid_analysis': pid_analyzer.analyze(log),
        'vibration_analysis': vibration_analyzer.analyze_vibration(log),
        'performance_evaluation': performance_evaluator.evaluate(log),
        'battery_analysis': battery_analyzer.analyze(log),
    }
    
    # 3. 生成优化建议
    suggestions = generate_optimization_suggestions(analysis_results)
    
    # 4. 预览效果
    preview = simulate_improvement(analysis_results, suggestions)
    
    # 5. 用户确认后应用
    # await apply_parameters(suggestions)
    
    return {
        'analysis': analysis_results,
        'suggestions': suggestions,
        'preview': preview,
    }
```

---

## 🎓 调参口诀

### PID调节口诀

```
PID调参有诀窍，
先P后I最后D。

P太大，会振荡，
P太小，反应慢。

I太大，响应慢，
I太小，漂移现。

D太大，噪声扰，
D太小，过冲高。

滤波截止要配合，
频率太高噪声进。

振动分析找频率，
Notch滤波要设置。

调参完成要测试，
悬停悬停再悬停。
```

---

## 📚 参考资源

### 官方文档
- PX4调参指南: https://docs.px4.io/main/en/config/
- PID控制器: https://docs.px4.io/main/en/config_mc/pid_tuning_multicopter_basic.html
- 高级PID: https://docs.px4.io/main/en/config_mc/pid_tuning_multicopter.html

### 社区资源
- PX4论坛: https://discuss.px4.io/
- GitHub Issues: https://github.com/PX4/PX4-Autopilot/issues

### 工具
- QGroundControl: 实时调参
- Flight Review: 在线日志分析 https://logs.px4.io/

---

## ✅ 总结

### 调参检查清单

- [ ] 初始参数设置正确
- [ ] 速率环P调优（无振荡）
- [ ] 速率环D调优（无颤抖）
- [ ] 速率环I调优（无漂移）
- [ ] 姿态环P调优（跟踪良好）
- [ ] 滤波器配置（振动抑制）
- [ ] 安全检查（悬停测试）
- [ ] 飞行测试（多种机动）
- [ ] 日志分析（HKAIC）
- [ ] 参数保存

### 推荐参数范围

| 参数 | 推荐范围 | 典型值 |
|------|---------|--------|
| MC_ROLLRATE_P | 0.12-0.20 | 0.15 |
| MC_ROLLRATE_I | 0.03-0.10 | 0.05 |
| MC_ROLLRATE_D | 0.002-0.005 | 0.003 |
| MC_PITCHRATE_P | 0.12-0.20 | 0.15 |
| MC_PITCHRATE_I | 0.03-0.10 | 0.05 |
| MC_PITCHRATE_D | 0.002-0.005 | 0.003 |
| MC_YAWRATE_P | 0.12-0.20 | 0.15 |
| MC_YAWRATE_I | 0.03-0.10 | 0.05 |
| MC_DTERM_CUTOFF | 60-120 Hz | 100 |

---

**作者:** HKAIC  
**最后更新:** 2026-05-20  
**版本:** 1.0.0

