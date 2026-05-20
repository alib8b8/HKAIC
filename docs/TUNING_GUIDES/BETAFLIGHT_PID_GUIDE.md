# Betaflight PID调参完全指南

**版本:** 4.5.0+  
**适用平台:** HKAIC  
**难度:** 中高级  
**适用场景:** 竞速、花飞、自稳飞行

---

## 📚 目录

1. [Betaflight简介](#betaflight简介)
2. [Betaflight vs PX4](#betaflight-vs-px4)
3. [Betaflight控制器架构](#betaflight控制器架构)
4. [PID调参基础](#pid调参基础)
5. [D-Term配置](#d-term配置)
6. [滤波器配置](#滤波器配置)
7. [高级调参](#高级调参)
8. [竞速vs花飞](#竞速vs花飞)
9. [HKAIC集成](#hkaic集成)

---

## 🚀 Betaflight简介

Betaflight是专为**竞速**和**花飞**设计的开源飞控固件，以其**低延迟**和**高响应性**著称。

### 核心特点

- ⚡ **超低延迟** - < 1ms控制环路
- 🎮 **实时调参** - 通过CMS/OSD调整
- 📊 **Blackbox日志** - 详细飞行数据记录
- 🎛️ **丰富滤波器** - 多级动态滤波
- 🔧 **灵活配置** - 几乎所有参数可调

### 支持的飞控

- STM32F4/F7/H7系列
- 各种Pixhawk兼容板
- Matek, Holybro, SpeedyBee等

**官方资源:**
- 官网: https://betaflight.com/
- 文档: https://betaflight.com/docs
- GitHub: https://github.com/betaflight/betaflight

---

## ⚖️ Betaflight vs PX4

| 特性 | Betaflight | PX4 |
|------|------------|-----|
| **设计目标** | 竞速/花飞 | 工业应用 |
| **控制延迟** | < 1ms | 2-5ms |
| **PID算法** | 传统PID + Anti-Gravity | 自适应控制 |
| **滤波器** | 多级动态 | 基础Notch |
| **日志格式** | Blackbox (.bbl) | ULog |
| **适用用户** | 竞赛/发烧友 | 工业/研究 |
| **学习曲线** | 中等 | 陡峭 |

### 选择建议

- **选择Betaflight如果:**
  - 你是竞速或花飞飞行员
  - 需要极致响应
  - 需要详细日志分析
  - 追求极限性能

- **选择PX4如果:**
  - 你需要复杂任务
  - 需要GPS自主飞行
  - 需要ROS集成
  - 应用于研究或工业

---

## 🎛️ Betaflight控制器架构

### 控制环路

```
输入 → PT1滤波器 → PID控制器 → Motor Output
          ↓
      D-Term计算
```

### Betaflight特有的概念

#### 1. PT1滤波器
Betaflight使用PT1（一阶滞后）滤波器代替传统低通：

```c
// PT1滤波器实现
output = input * coefficient + output * (1 - coefficient)
// 响应更快，相位延迟更小
```

#### 2. Feedforward (FF)
前馈控制 - 预测并补偿期望角速度变化：

```python
# Betaflight PID公式
output = error * P + error * I * dt + (error - prev_error) / dt * D
       + (setpoint - prev_setpoint) / dt * FF
```

#### 3. Anti-Gravity (AG)
防止急速油门变化导致的姿态倾斜：

```python
# Anti-Gravity增益
ag_gain = 3.5  # 典型值
anti_gravity_factor = 1 + ag_gain * abs(throttle_change_rate)
```

---

## ⚙️ PID调参基础

### PID参数详解

#### P (Proportional) - 比例

**作用:** 根据当前误差产生控制力

```python
p_params = {
    # Roll/Pitch P
    "roll_p": 45,      # 典型值40-50
    "pitch_p": 47,     # 通常比roll高5-10%
    
    # Yaw P
    "yaw_p": 35,       # 通常低于roll/pitch
}
```

**调节规则:**
- P太高: 🔴 振荡、颤抖、电机发热
- P太低: 🟡 响应迟钝、跟踪不佳

---

#### I (Integral) - 积分

**作用:** 消除长期累积误差（漂移）

```python
i_params = {
    "roll_i": 80,      # 典型值70-90
    "pitch_i": 85,     # 通常接近roll
    "yaw_i": 120,      # 通常比roll/pitch高
}
```

**调节规则:**
- I太高: 🔴 响应迟缓、过冲后振荡
- I太低: 🟡 悬停漂移、手动修正多

---

#### D (Derivative) - 微分

**作用:** 预测误差趋势，提前减速

```python
d_params = {
    "roll_d": 35,       # 典型值30-40
    "pitch_d": 38,      # 通常比roll高
    "yaw_d": 0,         # Yaw通常不使用D
}
```

**Betaflight D特点:**
- Betaflight使用**简化D项**（不使用原始D）
- D越大，阻尼越强

**调节规则:**
- D太高: 🔴 颤抖、噪声放大、电机蜂鸣
- D太低: 🟡 过冲、振荡、落地弹跳

---

### Feedforward (FF) - 前馈

Betaflight特有参数，控制响应速度：

```python
ff_params = {
    "roll_ff": 35,      # 典型值30-40
    "pitch_ff": 40,     # 通常比roll高
    "yaw_ff": 0,        # 通常不使用
}
```

**作用:**
- 提高响应速度
- 减少跟踪误差
- 减少P需求

**调节规则:**
- FF太高: 🔴 过冲、机械振动
- FF太低: 🟡 响应迟钝

---

## 🔧 D-Term配置

D-Term是Betaflight中最敏感的参数！

### D-Term设置

```python
# D-Term设置
d_term_config = {
    # D项类型
    "dterm_filter_type": "PT1",  # 或 "BIQUAD"
    
    # D项低通滤波
    "dterm_lowpass_hz": 100,    # 关键参数！
    
    # D项低通2（可选）
    "dterm_lowpass2_hz": 200,
    
    # D项曲线指数（影响D响应曲线）
    "dterm_curve_expo": 15,     # 0-100，影响非线性
}
```

### D-Term调节流程

#### 步骤1: 设置D-Term类型

```python
# 推荐PT1滤波器
d_term_filter_type = "PT1"
```

#### 步骤2: 调整截止频率

```python
# 从100Hz开始测试
dterm_tests = [
    {"hz": 80, "description": "更平滑，但响应慢"},
    {"hz": 100, "description": "平衡设置"},
    {"hz": 120, "description": "更快响应，可能噪声"},
    {"hz": 150, "description": "激进设置，电机发热"},
    {"hz": 180, "description": "极限设置，不推荐"},
]
```

#### 步骤3: 调整曲线指数

```python
# dterm_curve_expo调节
expo_tests = [
    {"value": 0, "description": "线性D项"},
    {"value": 15, "description": "推荐值，低速阻尼好"},
    {"value": 25, "description": "更激进，低速更平滑"},
    {"value": 50, "description": "非常激进"},
]
```

---

### D-Term问题诊断

| 现象 | 原因 | 解决方案 |
|-----|------|---------|
| 电机蜂鸣声 | D太大或滤波器太低 | 降低D或提高滤波器Hz |
| 颤抖 | D太大，噪声放大 | 降低D，降低D-Term Hz |
| 响应慢 | D太小 | 增加D，提高D-Term Hz |
| 落地弹跳 | D太小 | 增加D |
| 振荡 | D太小或P太大 | 增加D或降低P |

---

## 🎚️ 滤波器配置

Betaflight提供强大的滤波器系统！

### 滤波器层级

```
陀螺仪数据
    ↓
1. RPM Notch滤波器 ← 消除电机谐波
    ↓
2. 陀螺仪低通 ← 基础噪声过滤
    ↓
3. D-Term低通 ← D项噪声过滤
    ↓
4. Yaw Lowpass ← Yaw轴特殊处理
```

### 各滤波器详解

#### 1. 陀螺仪低通

```python
gyro_lowpass_params = {
    "gyro_lowpass_hz": 250,    # 典型值200-500
    "gyro_lowpass_type": "PT1",  # PT1或BIQUAD
}
```

#### 2. D-Term低通（关键！）

```python
dterm_lowpass_params = {
    # 第一级D-Term低通
    "dterm_lowpass_hz": 100,    # 关键！80-150Hz
    "dterm_lowpass_type": "PT1",
    
    # 第二级D-Term低通（可选）
    "dterm_lowpass2_hz": 200,
    "dterm_lowpass2_type": "PT1",
}
```

#### 3. RPM Notch滤波器

```python
rpm_notch_params = {
    # 电机谐波Notch
    "dyn_notch_width_percent": 10,    # Notch宽度
    "dyn_notch_q": 120,              # Q值，越高质量越窄
    "dyn_notch_min_hz": 100,         # 最小检测频率
    
    # 静态Notch（备用）
    "gyro_notch_hz": {
        "1": 260,  # 第一个Notch频率
        "2": 330,  # 第二个Notch频率
    },
    "gyro_notch_q": {
        "1": 500,
        "2": 500,
    },
}
```

#### 4. Yaw滤波器

```python
yaw_lowpass_params = {
    "yaw_lowpass_hz": 100,    # Yaw轴单独低通
}
```

---

### 滤波器配置模板

#### 竞速配置（高响应）

```python
racing_profile = {
    # 陀螺仪
    "gyro_lowpass_hz": 500,
    "gyro_lowpass_type": "PT1",
    
    # D-Term - 激进
    "dterm_lowpass_hz": 150,
    "dterm_lowpass_type": "PT1",
    "dterm_curve_expo": 25,
    
    # Notch
    "dyn_notch_width_percent": 8,
    "dyn_notch_q": 120,
    "dyn_notch_min_hz": 120,
}
```

#### 花飞配置（平滑）

```python
freestyle_profile = {
    # 陀螺仪
    "gyro_lowpass_hz": 250,
    "gyro_lowpass_type": "PT1",
    
    # D-Term - 平滑
    "dterm_lowpass_hz": 100,
    "dterm_lowpass_type": "PT1",
    "dterm_curve_expo": 15,
    
    # Notch - 更宽
    "dyn_notch_width_percent": 12,
    "dyn_notch_q": 100,
    "dyn_notch_min_hz": 100,
}
```

#### 电池7"载重配置

```python
heavy_load_profile = {
    # 陀螺仪 - 更低
    "gyro_lowpass_hz": 180,
    "gyro_lowpass_type": "PT1",
    
    # D-Term - 更低截止
    "dterm_lowpass_hz": 90,
    "dterm_lowpass_type": "PT1",
    "dterm_curve_expo": 10,
    
    # 额外滤波器
    "dterm_lowpass2_hz": 150,
}
```

---

## 🎯 高级调参

### 1. Anti-Gravity

防止急速油门变化导致的姿态倾斜：

```python
antigravity_params = {
    "anti_gravity_gain": 3500,    # 典型值3000-5000
    "anti_gravity_thresh": 20,    # 油门变化阈值
    "anti_gravity_mode": "_smooth",  # 或 "step"
}
```

**调节规则:**
- AG太高: 🔴 油门响应迟缓
- AG太低: 🟡 急速油门时倾斜

---

### 2. TPA (Throttle PID Attenuation)

高速飞行时减少PID影响：

```python
tpa_params = {
    "tpa_rate": 20,         # 衰减斜率
    "tpa_breakpoint": 1350,  # 开始衰减的油门值
}
```

---

### 3. Throttle Boost

增加最小油门输出：

```python
throttle_params = {
    "throttle_boost": 0,        # 0-20
    "throttle_tilt_comp": 50,   # 倾斜补偿
}
```

---

### 4. Feedforward (FF) 高级

```python
ff_params = {
    "roll_ff": 35,              # 前馈增益
    "roll_ff_interpolate": " bilinear",  # 插值方式
    "roll_ff_smooth": 25,       # 平滑度
    "roll_ff_boost": 0,        # 加速增益
}
```

---

### 5. D-Min

Betaflight特有，根据飞行状态动态调整D项：

```python
dmin_params = {
    "roll_d_min": 25,           # 最小D值
    "roll_d_min_gain": 30,      # D最小增益
    "roll_d_min_advance": 0,    # D最小提前
}
```

---

## 🏎️ 竞速vs花飞

### 竞速配置重点

```python
racing_priority = {
    # 响应优先
    "roll_p": 48,
    "pitch_p": 50,
    "roll_i": 80,
    "pitch_i": 85,
    "roll_d": 37,
    "pitch_d": 40,
    
    # 高FF
    "roll_ff": 40,
    "pitch_ff": 45,
    
    # 激进滤波器
    "dterm_lowpass_hz": 150,
    "gyro_lowpass_hz": 500,
}
```

### 花飞配置重点

```python
freestyle_priority = {
    # 平滑优先
    "roll_p": 45,
    "pitch_p": 47,
    "roll_i": 85,
    "pitch_i": 90,
    "roll_d": 35,
    "pitch_d": 38,
    
    # 适中FF
    "roll_ff": 30,
    "pitch_ff": 35,
    
    # 平滑滤波器
    "dterm_lowpass_hz": 100,
    "gyro_lowpass_hz": 250,
}
```

---

## 🔍 HKAIC集成

### 1. Blackbox日志解析

HKAIC已支持Betaflight Blackbox (.bbl) 格式：

```python
class BlackboxParser:
    """Betaflight Blackbox日志解析"""
    
    def parse(self, filepath):
        """解析.bbl文件"""
        with open(filepath, 'rb') as f:
            return self._decode_blackbox(f)
    
    def extract_flight_data(self, log):
        """提取飞行数据"""
        return {
            'roll': log['rcCommand'][0],      # Roll命令
            'pitch': log['rcCommand'][1],     # Pitch命令
            'yaw': log['rcCommand'][2],       # Yaw命令
            'throttle': log['rcCommand'][3],  # 油门
            
            'gyro': {
                'roll': log['gyroADC'][0],
                'pitch': log['gyroADC'][1],
                'yaw': log['gyroADC'][2],
            },
            
            'pid': {
                'roll': log['pid'],
                'pitch': log['pid'],
                'yaw': log['pid'],
            },
            
            'motor': log['motor'],
            'vbat': log['vbat'],
        }
```

### 2. Betaflight特定分析

```python
class BetaflightAnalyzer:
    """Betaflight特定分析"""
    
    def analyze_blackbox(self, log):
        """分析Blackbox日志"""
        results = {
            'motor_outputs': self.analyze_motor_outputs(log),
            'pid_performance': self.analyze_pid_performance(log),
            'filter_effectiveness': self.analyze_filters(log),
            'd_term_analysis': self.analyze_d_term(log),
            'feedforward_analysis': self.analyze_feedforward(log),
        }
        
        return results
    
    def analyze_motor_outputs(self, log):
        """分析电机输出"""
        motors = log['motor']
        
        # 计算电机平衡
        motor_balance = self.calculate_motor_balance(motors)
        
        # 检测电机问题
        motor_issues = []
        for i, motor in enumerate(motors):
            if motor > 1900:
                motor_issues.append(f"Motor {i+1}接近最大值")
            if motor < 1000:
                motor_issues.append(f"Motor {i+1}接近最小值")
        
        return {
            'balance': motor_balance,
            'issues': motor_issues,
            'recommendations': self.generate_motor_recommendations(motor_balance)
        }
    
    def analyze_d_term(self, log):
        """分析D-Term性能"""
        d_term = log['dTerm']
        
        # 计算D-Term均值和峰值
        d_mean = np.mean(d_term)
        d_max = np.max(np.abs(d_term))
        d_noise = self.calculate_noise(d_term)
        
        # 诊断
        issues = []
        suggestions = []
        
        if d_noise > 50:
            issues.append("D-Term噪声过高")
            suggestions.append("降低dterm_lowpass_hz或dterm_curve_expo")
        
        if d_max > 400:
            issues.append("D-Term峰值过高")
            suggestions.append("检查滤波器设置或增加D-Term限制")
        
        return {
            'mean': d_mean,
            'max': d_max,
            'noise': d_noise,
            'issues': issues,
            'suggestions': suggestions
        }
```

### 3. 自动调参建议

```python
class BetaflightAutoTuner:
    """Betaflight自动调参建议"""
    
    def suggest_parameters(self, flight_log):
        """基于飞行日志给出参数建议"""
        
        analysis = self.analyzer.analyze_blackbox(flight_log)
        
        suggestions = []
        
        # P调参建议
        if analysis['pid_performance']['overshoot'] > 10:
            suggestions.append({
                'param': 'roll_p',
                'action': 'decrease',
                'amount': 2,
                'reason': '检测到过冲'
            })
        
        # D调参建议
        if analysis['d_term_analysis']['noise'] > 50:
            suggestions.append({
                'param': 'dterm_lowpass_hz',
                'action': 'decrease',
                'amount': 10,
                'reason': 'D-Term噪声过高'
            })
        
        # 滤波器建议
        if analysis['filter_effectiveness']['vibration'] > threshold:
            suggestions.append({
                'param': 'dyn_notch_width_percent',
                'action': 'increase',
                'amount': 2,
                'reason': '振动抑制不足'
            })
        
        return suggestions
```

---

## 📊 Betaflight参数推荐值

### 竞速5" Quad

```python
racing_5in_quad = {
    # PID
    "roll_p": 48,
    "roll_i": 80,
    "roll_d": 37,
    "pitch_p": 50,
    "pitch_i": 85,
    "pitch_d": 40,
    "yaw_p": 35,
    "yaw_i": 120,
    "yaw_d": 0,
    
    # Feedforward
    "roll_ff": 40,
    "pitch_ff": 45,
    "yaw_ff": 0,
    
    # D-Min
    "roll_d_min": 30,
    "pitch_d_min": 33,
    
    # 滤波器
    "gyro_lowpass_hz": 500,
    "dterm_lowpass_hz": 150,
    "dterm_lowpass2_hz": 250,
    "dyn_notch_q": 120,
    
    # Anti-Gravity
    "anti_gravity_gain": 4000,
    "anti_gravity_mode": "smooth",
    
    # TPA
    "tpa_rate": 15,
    "tpa_breakpoint": 1350,
}
```

### 花飞5" Quad

```python
freestyle_5in_quad = {
    # PID
    "roll_p": 45,
    "roll_i": 85,
    "roll_d": 35,
    "pitch_p": 47,
    "pitch_i": 90,
    "pitch_d": 38,
    "yaw_p": 35,
    "yaw_i": 120,
    "yaw_d": 0,
    
    # Feedforward
    "roll_ff": 30,
    "pitch_ff": 35,
    "yaw_ff": 0,
    
    # D-Min
    "roll_d_min": 25,
    "pitch_d_min": 28,
    
    # 滤波器
    "gyro_lowpass_hz": 250,
    "dterm_lowpass_hz": 100,
    "dterm_lowpass2_hz": 200,
    "dyn_notch_q": 100,
    
    # Anti-Gravity
    "anti_gravity_gain": 3500,
    "anti_gravity_mode": "smooth",
    
    # TPA
    "tpa_rate": 20,
    "tpa_breakpoint": 1350,
}
```

### 长续航/7"载重

```python
heavy_7in_quad = {
    # PID - 降低响应
    "roll_p": 42,
    "roll_i": 90,
    "roll_d": 32,
    "pitch_p": 44,
    "pitch_i": 95,
    "pitch_d": 35,
    "yaw_p": 35,
    "yaw_i": 130,
    "yaw_d": 0,
    
    # 滤波器 - 更低截止
    "gyro_lowpass_hz": 180,
    "dterm_lowpass_hz": 90,
    "dterm_lowpass2_hz": 150,
    "dyn_notch_q": 100,
    
    # Anti-Gravity - 更高
    "anti_gravity_gain": 5000,
}
```

---

## 🎓 Betaflight调参口诀

```
Betaflight调参有技巧，
先滤波器来后PID。

电机Notch要开启，
陀螺仪低通先设定。

D-Term低通是核心，
从高往低调。

D值太高电机响，
颤抖噪声要提防。

FF前馈提响应，
P值可以适当降。

Anti-Gravity防倾斜，
高低适当要平衡。

竞速追求快响应，
花飞追求更平滑。

滤波器配置要灵活，
载重需要更低通。

Blackbox来分析，
HKAIC帮你来优化。
```

---

## ❓ 常见问题

### Q1: 电机发出高频蜂鸣声

**A:** D值太大或D-Term低通Hz太低
```python
solution = {
    "action": "降低D值或增加dterm_lowpass_hz",
    "example": "dterm_lowpass_hz从100增加到120"
}
```

### Q2: 飞行中颤抖

**A:** P值太大或滤波器太低
```python
solution = {
    "action": "降低P值或增加gyro_lowpass_hz",
    "example": "roll_p从48降到45"
}
```

### Q3: 急速油门时倾斜

**A:** Anti-Gravity太低
```python
solution = {
    "action": "增加anti_gravity_gain",
    "example": "anti_gravity_gain从3000增加到4000"
}
```

### Q4: 落地弹跳

**A:** D值太小
```python
solution = {
    "action": "增加D值",
    "example": "roll_d从35增加到37"
}
```

### Q5: GPS模式下漂移

**A:** I值太低
```python
solution = {
    "action": "增加I值",
    "example": "roll_i从80增加到90"
}
```

---

## 📚 参考资源

### 官方文档
- Betaflight官网: https://betaflight.com/
- 配置指南: https://betaflight.com/docs/wiki/configurator/
- Blackbox: https://betaflight.com/docs/development/blackbox-log/

### 工具
- Betaflight Configurator: GUI调参工具
- Blackbox Explorer: 日志查看器
- Betaflight Blackbox Tools: https://github.com/betaflight/blackbox-tools

### 社区
- RCGroups Betaflight论坛
- OscarLiang博客

---

## ✅ 总结

### Betaflight调参检查清单

- [ ] 陀螺仪低通设置（250-500Hz）
- [ ] D-Term低通设置（90-150Hz）
- [ ] 启用Dynamic Notch
- [ ] P调优（无振荡）
- [ ] I调优（无漂移）
- [ ] D调优（无颤抖）
- [ ] FF调优（响应适当）
- [ ] Anti-Gravity设置
- [ ] Blackbox日志分析
- [ ] 滤波器效果验证

### 推荐参数范围

| 参数 | 竞速 | 花飞 | 载重 |
|------|------|------|------|
| roll_p | 45-50 | 43-47 | 40-44 |
| roll_d | 35-40 | 33-38 | 30-34 |
| dterm_lowpass_hz | 130-150 | 90-110 | 80-95 |
| gyro_lowpass_hz | 400-500 | 200-300 | 150-200 |

---

**作者:** HKAIC  
**最后更新:** 2026-05-20  
**版本:** 1.0.0

