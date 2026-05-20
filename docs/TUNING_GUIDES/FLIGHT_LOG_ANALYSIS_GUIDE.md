# 无人机飞行日志分析最佳实践

**版本:** 1.0  
**适用平台:** HKAIC  
**难度:** 中级

---

## 📚 目录

1. [简介](#简介)
2. [日志格式](#日志格式)
3. [数据解读](#数据解读)
4. [分析方法](#分析方法)
5. [常见问题诊断](#常见问题诊断)
6. [HKAIC集成](#hkaic集成)

---

## 🎯 简介

飞行日志是理解和优化无人机性能的关键。通过分析日志，你可以：

- ✅ **诊断问题** - 找出飞行异常的根源
- ✅ **优化性能** - 调整PID参数达到最佳状态
- ✅ **预防故障** - 提前发现潜在问题
- ✅ **记录飞行** - 建立飞行历史档案

---

## 📁 日志格式

### 1. Betaflight Blackbox (.bbl, .ulg)

**特点:**
- 最详细的日志格式
- 包含所有PID、电机、陀螺仪数据
- 适合竞速和花飞调参

**包含数据:**
```python
blackbox_fields = [
    'time',
    'rcCommand',       # 遥控器命令
    'gyroADC',        # 陀螺仪原始数据
    'accelADC',       # 加速度计数据
    'motor',          # 电机输出
    'pid',            # PID输出
    'setpoint',       # 期望值
    'vbat',           # 电池电压
    'amperage',       # 电流
    'baro',           # 气压计
    'mag',            # 磁力计
    'gps',            # GPS数据
]
```

---

### 2. PX4 ULog (.ulg)

**特点:**
- PX4飞控标准格式
- 结构化消息系统
- 支持自定义消息

**包含数据:**
```python
ulog_fields = [
    'sensor_gyro',       # 陀螺仪
    'sensor_accel',      # 加速度计
    'vehicle_attitude',   # 姿态
    'vehicle_local_position',  # 位置
    'actuator_outputs',  # 执行器输出
    'battery_status',    # 电池状态
    'vehicle_gps_position',  # GPS位置
]
```

---

### 3. ArduPilot日志 (.BIN, .log)

**特点:**
- ArduPilot飞控格式
- 二进制和文本两种格式
- 广泛用于DIY无人机

**包含数据:**
```python
ardupilot_fields = [
    'ATT',              # 姿态
    'RCOU',             # 遥控器输出
    'RATE',             # 速率环数据
    'PID',              # PID数据
    'GPS',              # GPS数据
    'BAT',              # 电池数据
    'ESC',              # ESC数据
    'IMU',              # IMU数据
]
```

---

### 4. DJI格式 (.txt, .srt)

**特点:**
- DJI无人机专用
- 压缩格式
- 部分数据开放

**包含数据:**
```python
dji_fields = [
    'latitude',
    'longitude',
    'altitude',
    'velocity',
    'battery',
    'gimbal',
    'flight_time',
]
```

---

## 📊 数据解读

### 1. 姿态数据

#### Roll/Pitch/Yaw

```python
# 解读姿态数据
def interpret_attitude(roll, pitch, yaw):
    """
    分析姿态数据
    """
    results = {}
    
    # Roll分析
    results['roll'] = {
        'max': max(roll),
        'min': min(roll),
        'mean': np.mean(roll),
        'std': np.std(roll),
        'oscillations': count_oscillations(roll)
    }
    
    # 检测问题
    if results['roll']['oscillations'] > 10:
        results['roll']['issue'] = "可能P值太高"
    
    if abs(results['roll']['mean']) > 5:
        results['roll']['issue'] = "存在系统性倾斜"
    
    return results
```

---

### 2. 陀螺仪数据

```python
# 陀螺仪数据解读
def interpret_gyroscope(gyro_data):
    """
    分析陀螺仪数据
    """
    # 计算振动
    vibration = {
        'x': calculate_vibration(gyro_data['x']),
        'y': calculate_vibration(gyro_data['y']),
        'z': calculate_vibration(gyro_data['z']),
    }
    
    # 检测振动频率
    for axis in ['x', 'y', 'z']:
        fft_result = perform_fft(gyro_data[axis])
        dominant_freq = find_dominant_frequency(fft_result)
        vibration[f'{axis}_frequency'] = dominant_freq
    
    return {
        'vibration_amplitude': vibration,
        'status': 'good' if max(vibration.values()) < threshold else 'warning'
    }
```

---

### 3. 电机输出

```python
# 电机输出分析
def analyze_motor_outputs(motor_data):
    """
    分析电机输出
    """
    # 计算电机平衡
    motor_balance = {
        'm1': motor_data['m1'],
        'm2': motor_data['m2'],
        'm3': motor_data['m3'],
        'm4': motor_data['m4'],
    }
    
    # 检测电机不平衡
    motor_std = np.std([motor_balance['m1'], motor_balance['m2'], 
                        motor_balance['m3'], motor_balance['m4']])
    
    issues = []
    if motor_std > 50:
        issues.append("电机输出不平衡")
    
    # 检测电机过热（ESC温度数据）
    if 'esc_temp' in motor_data:
        if max(motor_data['esc_temp']) > 80:
            issues.append("ESC温度过高")
    
    return {
        'balance': motor_balance,
        'std': motor_std,
        'issues': issues
    }
```

---

### 4. 电池数据

```python
# 电池健康分析
def analyze_battery(battery_data):
    """
    分析电池健康状态
    """
    results = {
        'voltage': {
            'initial': battery_data['voltage'][0],
            'final': battery_data['voltage'][-1],
            'drop': battery_data['voltage'][0] - battery_data['voltage'][-1],
        },
        'current': {
            'max': max(battery_data['current']),
            'avg': np.mean(battery_data['current']),
        },
        'capacity': {
            'used': sum(battery_data['current']) / 3600,  # mAh
        }
    }
    
    # 计算健康分数
    health_score = 100
    
    if results['voltage']['drop'] > 3.0:
        health_score -= 20
    
    if results['current']['max'] > 50:
        health_score -= 10
    
    if results['capacity']['used'] > 4000:
        health_score -= 10
    
    results['health_score'] = health_score
    results['health_status'] = 'good' if health_score > 80 else 'warning'
    
    return results
```

---

## 🔍 分析方法

### 1. 时域分析

```python
# 时域分析方法
def time_domain_analysis(data):
    """
    时域分析
    """
    return {
        'mean': np.mean(data),
        'std': np.std(data),
        'max': np.max(data),
        'min': np.min(data),
        'peak_to_peak': np.max(data) - np.min(data),
        'rms': np.sqrt(np.mean(np.array(data)**2)),
    }
```

---

### 2. 频域分析 (FFT)

```python
# 频域分析方法
def frequency_domain_analysis(data, sampling_rate=1000):
    """
    频域分析 - 检测振动频率
    """
    # 执行FFT
    fft_result = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(data), 1/sampling_rate)
    
    # 获取幅度谱
    magnitude = np.abs(fft_result)
    
    # 找到主频率
    peak_idx = np.argmax(magnitude[1:len(magnitude)//2]) + 1
    dominant_freq = freqs[peak_idx]
    
    # 找到所有显著频率
    threshold = np.max(magnitude) * 0.1
    significant_freqs = []
    for i, mag in enumerate(magnitude):
        if mag > threshold and freqs[i] > 0:
            significant_freqs.append({
                'frequency': freqs[i],
                'magnitude': mag
            })
    
    return {
        'dominant_frequency': dominant_freq,
        'significant_frequencies': significant_freqs,
        'spectrum': magnitude
    }
```

---

### 3. 相关性分析

```python
# 相关性分析
def correlation_analysis(data1, data2):
    """
    分析两组数据的相关性
    """
    correlation = np.corrcoef(data1, data2)[0, 1]
    
    return {
        'correlation': correlation,
        'interpretation': '强正相关' if correlation > 0.7 else 
                        '强负相关' if correlation < -0.7 else
                        '弱相关' if abs(correlation) > 0.3 else
                        '几乎无相关'
    }
```

---

## 🐛 常见问题诊断

### 问题1: 振荡

**症状:** 飞行中持续小幅振荡

**诊断方法:**
```python
def diagnose_oscillation(flight_log):
    """
    诊断振荡问题
    """
    # 检查Roll/Pitch响应
    roll_response = flight_log['roll_gyro'] - flight_log['roll_setpoint']
    
    # 计算振荡次数
    zero_crossings = count_zero_crossings(roll_response)
    oscillation_count = zero_crossings / 2
    
    # 检测PID设置
    pid_analysis = analyze_pid_for_oscillation(flight_log)
    
    return {
        'oscillation_count': oscillation_count,
        'likely_cause': 'P值太高' if oscillation_count > 20 else '正常',
        'suggestions': [
            '减小P值5-10%',
            '增加D值10-15%',
            '检查电机平衡'
        ]
    }
```

---

### 问题2: 振动

**症状:** 电机发出异常声音，飞行不稳

**诊断方法:**
```python
def diagnose_vibration(flight_log):
    """
    诊断振动问题
    """
    # 频域分析
    freq_analysis = frequency_domain_analysis(flight_log['gyro'])
    
    # 检测振动频率
    issues = []
    
    for freq_data in freq_analysis['significant_frequencies']:
        freq = freq_data['frequency']
        
        if 80 < freq < 150:
            issues.append({
                'frequency': freq,
                'cause': '电机安装不平衡',
                'solution': '平衡电机或桨叶'
            })
        elif 150 < freq < 300:
            issues.append({
                'frequency': freq,
                'cause': '可能的共振',
                'solution': '检查减震和刚性'
            })
        elif 300 < freq < 600:
            issues.append({
                'frequency': freq,
                'cause': '电机噪声',
                'solution': '检查电机轴承或电调'
            })
    
    return {
        'vibration_severity': 'high' if len(issues) > 3 else 'medium',
        'issues': issues,
        'solutions': [issue['solution'] for issue in issues]
    }
```

---

###问题3: GPS漂移

**诊断方法:**
```python
def diagnose_gps_drift(flight_log):
    """
    诊断GPS漂移问题
    """
    gps_data = flight_log['gps']
    
    # 计算位置标准差
    position_std = {
        'lat': np.std(gps_data['latitude']),
        'lon': np.std(gps_data['longitude']),
    }
    
    # 计算水平精度
    hdop = gps_data.get('hdop', 1.0)
    
    issues = []
    solutions = []
    
    if position_std['lat'] > 5 or position_std['lon'] > 5:
        issues.append("位置数据波动大")
        solutions.append("检查GPS天线位置")
        solutions.append("确保GPS上方无遮挡")
    
    if hdop > 2.0:
        issues.append("GPS精度不足")
        solutions.append("等待更多卫星锁定")
        solutions.append("避免在建筑物附近飞行")
    
    return {
        'issues': issues,
        'solutions': list(set(solutions)),
        'recommendations': generate_gps_recommendations(gps_data)
    }
```

---

### 问题4: 电池异常

**诊断方法:**
```python
def diagnose_battery_issues(battery_data):
    """
    诊断电池问题
    """
    issues = []
    
    # 检测电压异常下降
    if battery_data['voltage_drop'] > 3.5:
        issues.append("电压下降过大")
    
    # 检测压降
    if battery_data['voltage_sag'] > 2.0:
        issues.append("电池压降严重")
    
    # 检测温度过高
    if max(battery_data['temp']) > 60:
        issues.append("电池温度过高")
    
    # 检测容量异常
    if battery_data['capacity_used'] > 4500:
        issues.append("放电容量过大")
    
    return {
        'issues': issues,
        'health_status': 'warning' if issues else 'good',
        'recommendations': generate_battery_recommendations(issues)
    }
```

---

## 🤖 HKAIC集成

### 1. 完整分析流程

```python
class ComprehensiveAnalyzer:
    """
    综合飞行日志分析
    """
    
    def analyze(self, flight_log_path):
        """
        完整分析流程
        """
        # 1. 解析日志
        log = self.parser.parse(flight_log_path)
        
        # 2. 执行多维度分析
        results = {
            'basic_metrics': self.analyze_basic_metrics(log),
            'pid_performance': self.analyze_pid_performance(log),
            'vibration_analysis': self.analyze_vibration(log),
            'motor_analysis': self.analyze_motors(log),
            'battery_health': self.analyze_battery(log),
            'gps_quality': self.analyze_gps(log),
            'control_quality': self.analyze_control(log),
        }
        
        # 3. 问题诊断
        results['diagnostics'] = self.diagnose_problems(results)
        
        # 4. 生成建议
        results['recommendations'] = self.generate_recommendations(results)
        
        # 5. 综合评分
        results['overall_score'] = self.calculate_overall_score(results)
        
        return results
    
    def calculate_overall_score(self, results):
        """
        计算综合评分
        """
        scores = {
            'stability': results['basic_metrics']['stability_score'],
            'efficiency': results['basic_metrics']['efficiency_score'],
            'control': results['control_quality']['score'],
            'battery': results['battery_health']['health_score'],
            'gps': results['gps_quality']['accuracy_score'],
        }
        
        # 加权平均
        weights = {
            'stability': 0.3,
            'efficiency': 0.2,
            'control': 0.25,
            'battery': 0.15,
            'gps': 0.1,
        }
        
        overall = sum(scores[key] * weights[key] for key in weights)
        
        return {
            'overall_score': overall,
            'detailed_scores': scores,
            'grade': self.score_to_grade(overall)
        }
```

---

### 2. 自动化报告生成

```python
def generate_analysis_report(analysis_results):
    """
    生成分析报告
    """
    report = f"""
# 飞行日志分析报告

## 综合评分: {analysis_results['overall_score']['overall_score']:.1f}/100
**等级: {analysis_results['overall_score']['grade']}**

---

## 1. 基础指标

- 飞行时长: {analysis_results['basic_metrics']['flight_duration']:.1f}分钟
- 最大速度: {analysis_results['basic_metrics']['max_speed']:.1f}m/s
- 最大高度: {analysis_results['basic_metrics']['max_altitude']:.1f}m
- 总飞行距离: {analysis_results['basic_metrics']['total_distance']:.1f}m

---

## 2. 性能评分

| 项目 | 评分 |
|------|------|
| 稳定性 | {analysis_results['overall_score']['detailed_scores']['stability']:.1f}/100 |
| 效率 | {analysis_results['overall_score']['detailed_scores']['efficiency']:.1f}/100 |
| 控制质量 | {analysis_results['overall_score']['detailed_scores']['control']:.1f}/100 |
| 电池健康 | {analysis_results['overall_score']['detailed_scores']['battery']:.1f}/100 |
| GPS精度 | {analysis_results['overall_score']['detailed_scores']['gps']:.1f}/100 |

---

## 3. 问题诊断
"""
    
    # 添加诊断问题
    if analysis_results['diagnostics']['issues']:
        report += "\n### 发现的问题:\n\n"
        for issue in analysis_results['diagnostics']['issues']:
            report += f"- ⚠️ **{issue['type']}**: {issue['description']}\n"
            report += f"  - 原因: {issue['cause']}\n"
            report += f"  - 建议: {issue['solution']}\n\n"
    
    # 添加建议
    report += "## 4. 优化建议\n\n"
    for rec in analysis_results['recommendations']:
        report += f"### {rec['category']}\n"
        report += f"{rec['suggestion']}\n\n"
    
    return report
```

---

## 📊 分析指标总结

| 指标类型 | 关键指标 | 正常范围 | 问题阈值 |
|---------|---------|---------|---------|
| **稳定性** | Roll/Pitch标准差 | < 5° | > 10° |
| **振动** | 振动幅度 | < 0.5g | > 1.0g |
| **电机** | 电机不平衡 | < 50 | > 100 |
| **电池** | 电压下降 | < 3.0V | > 4.0V |
| **GPS** | HDOP | < 1.5 | > 2.5 |
| **控制** | 跟踪误差 | < 10° | > 20° |

---

## 🎯 最佳实践

### 1. 飞行前检查
- ✅ 确保GPS卫星数充足
- ✅ 检查电池电量
- ✅ 验证传感器校准
- ✅ 检查桨叶状态

### 2. 飞行中记录
- ✅ 记录飞行条件
- ✅ 注意异常情况
- ✅ 记录电池使用情况

### 3. 飞行后分析
- ✅ 立即上传日志
- ✅ 检查关键指标
- ✅ 诊断发现的问题
- ✅ 记录优化措施

### 4. 持续改进
- ✅ 定期分析日志
- ✅ 对比历史数据
- ✅ 优化参数设置
- ✅ 记录改进效果

---

## 📚 参考资源

### 官方文档
- PX4日志分析: https://docs.px4.io/main/en/log/flight_log_analysis.html
- Betaflight Blackbox: https://betaflight.com/docs/development/blackbox
- ArduPilot日志: https://ardupilot.org/copter/docs/common-downloading-and-analyzing-data-logs-in-mission-planner.html

### 工具
- Flight Review (PX4): https://logs.px4.io/
- Blackbox Explorer: https://github.com/betaflight/blackbox-tools
- Mission Planner: https://ardupilot.org/planner/

---

**作者:** HKAIC  
**最后更新:** 2026-05-20  
**版本:** 1.0.0

