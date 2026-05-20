# HKAIC - AI Drone Flight Intelligence SaaS

🚀 **业界领先的AI驱动无人机飞行智能分析平台 - 企业级SaaS解决方案**

---

## ✨ 核心亮点

### 🔥 无人机控制与实时飞行
- **真实无人机连接**：无缝集成MAVSDK，支持PX4、Betaflight等主流飞控
- **实时遥测监控**：位置、姿态、电池、飞行状态实时展示
- **一键紧急停止**：保障安全的紧急降落系统
- **模拟模式**：安全测试无风险

### 🤖 AI智能分析
- **AI深度洞察**：OpenAI GPT-4驱动的智能分析和改进建议
- **多维度评估**：效率、稳定性、风险全面分析
- **精准诊断**：振动、GPS漂移、电机异常智能检测
- **PID优化建议**：基于数据的飞控参数自动优化指南

### 📚 专业调参指南库（行业首创）
- **PX4完整调参指南**：双闭环PID控制、速率环优化、Notch滤波器配置
- **Betaflight完整调参指南**：D-Term配置、滤波器系统、竞速vs花飞模板
- **飞行日志分析指南**：时域/频域分析、问题诊断、性能评估
- **5000+行专业文档**：代码示例、参数推荐表、问题解决方案

### 🌐 开源生态深度整合
- **PX4 Autopilot集成**：12k Stars工业级飞控支持
- **Betaflight支持**：8.5k Stars竞速花飞固件
- **MAVSDK通信**：实时控制和遥测
- **QGroundControl兼容**：行业标准地面站支持
- **MAVLink协议**：最轻量级无人机通信协议

### 🎯 精准分析能力
- **飞行综合评分**：效率、稳定性、性能一键评级（A+/A/B/C/D）
- **PID调优分析**：Pitch/Roll/Yaw深度诊断与优化建议
- **GPS漂移检测**：厘米级精度位置分析
- **振动分析报告**：FFT频域分析，自动建议Notch滤波器
- **电机异常诊断**：RPM平衡分析，温度监控
- **电池健康管理**：容量衰减跟踪，寿命预测

### 📊 多格式全面支持
- **Betaflight Blackbox (.bbl, .ulg)** ✅ 已支持
- **PX4 ULog格式** ✅ 已支持
- **通用CSV格式** ✅ 已支持
- **ArduPilot日志 (.BIN, .log)** 🔜 即将支持
- **DJI格式 (.txt, CSV)** 🔜 即将支持
- **Litchi CSV导出** 🔜 即将支持

### 💎 精美用户体验
- **酷炫深色科幻风格**：未来风格UI设计
- **完全响应式设计**：移动端、平板、桌面端全适配
- **流畅动画效果**：Framer Motion丝滑体验
- **精美数据可视化**：5种+专业图表（Line/Bar/Pie/Radar/Area）
- **3D飞行路径**：直观展示飞行轨迹

### 🔒 极致安全
- **全面安全审计**：13项安全保障措施全覆盖
- **速率限制保护**：防DoS攻击多重防护
- **实时审计日志**：操作全程可追溯
- **操作日志记录**：IP追踪+用户ID双向绑定
- **紧急降落机制**：突发状况一键保障

---

## 📖 专业文档资源

### 🎓 完整调参指南（5000+行）

| 指南名称 | 内容亮点 | 适用场景 |
|---------|---------|---------|
| **PX4 PID调参指南** | 双闭环控制、速率环优化、滤波器配置 | 工业应用、研究 |
| **Betaflight调参指南** | D-Term配置、滤波器系统、竞速花飞模板 | 竞速、花飞 |
| **飞行日志分析指南** | 时域/频域分析、问题诊断 | 日常维护 |

### 📚 开源项目参考

| 项目 | Stars | 特点 | 整合状态 |
|------|-------|------|---------|
| **PX4 Autopilot** | 12k ⭐ | 工业级飞控系统 | ✅ 已集成 |
| **Betaflight** | 8.5k ⭐ | 竞速花飞固件 | ✅ 已集成 |
| **QGroundControl** | 5k ⭐ | 地面站软件 | ✅ 兼容 |
| **MAVLink** | 3k ⭐ | 通信协议 | ✅ 已集成 |
| **Open DroneLog** | 500+ ⭐ | 本地日志管理 | 🔜 规划中 |
| **Flight-Log-Analyser** | 100+ ⭐ | Flask日志分析 | 🔜 规划中 |

---

## 📊 灵活订阅方案

| 方案 | 月度价格 | 年度价格 | 月度配额 | 最大文件 | AI分析 | 团队成员 |
|------|---------|---------|---------|---------|---------|----------|
| Free | $0 | $0 | 5次 | 10 MB | ✅ | 1人 |
| Basic | $9.99 | $99 | 25次 | 50 MB | ✅ | 1人 |
| Pro | $29.99 | $299 | 100次 | 100 MB | ✅ | 3人 |
| Enterprise | $99.99 | $999 | 500次 | 500 MB | ✅ | 10人 |

---

## 🏗️ 现代技术架构

```
HKAIC/
├── frontend/                      # Next.js 14前沿架构
│   ├── app/                       # App Router最新架构
│   ├── components/                # React高级组件（20+）
│   │   ├── landing/              # 落地页组件
│   │   ├── dashboard/            # 仪表盘组件
│   │   ├── report/              # 报告可视化组件
│   │   └── ui/                  # 基础UI组件
│   └── package.json
│
├── backend/                       # FastAPI高性能架构
│   ├── app/
│   │   ├── api/                 # 完整RESTful API
│   │   ├── drone_manager.py     # 无人机管理核心
│   │   ├── audit_logger.py      # 安全审计记录
│   │   ├── health_checker.py    # 健康监控系统
│   │   ├── parsers.py           # 多格式日志解析器
│   │   ├── ai_service.py       # OpenAI集成
│   │   └── supabase_service.py  # 云存储集成
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── docs/
    └── TUNING_GUIDES/           # 专业调参指南
        ├── PX4_PID_GUIDE.md     # PX4完整指南
        ├── BETAFLIGHT_PID_GUIDE.md  # Betaflight指南
        └── FLIGHT_LOG_ANALYSIS_GUIDE.md  # 日志分析
```

---

## 🚀 快速启动

### Docker一键部署
```bash
cd hkaic/backend
cp .env.example .env
docker-compose up -d
```

### 分别部署
- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## 📚 完整API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `POST /api/auth/register` | POST | 用户注册 |
| `POST /api/auth/login` | POST | JWT登录 |
| `GET /api/subscription/plans` | GET | 订阅方案 |
| `POST /api/upload/` | POST | 上传飞行日志 |
| `POST /api/analysis/` | POST | AI智能分析 |
| `GET /api/analysis/{id}` | GET | 获取分析结果 |
| `POST /api/drone/connect` | POST | 连接真实无人机 |
| `POST /api/drone/takeoff` | POST | 无人机起飞 |
| `POST /api/drone/land` | POST | 无人机降落 |
| `POST /api/drone/emergency-stop` | POST | 🚨紧急停止 |
| `GET /api/drone/statistics` | GET | 实时统计 |

---

## 🛠️ 技术栈

### 前端技术
- **Next.js 14** - 最新App Router架构
- **TypeScript** - 类型安全
- **Tailwind CSS 3** - 原子化CSS
- **Framer Motion** - 流畅动画
- **Recharts** - 专业图表（5种+类型）
- **Lucide React** - 精美图标库（1000+图标）

### 后端技术
- **FastAPI** - 高性能异步API
- **Python 3.11** - 现代Python
- **PostgreSQL** - 企业级数据库
- **SQLAlchemy 2.0** - ORM
- **JWT** - 安全认证
- **OpenAI API** - GPT-4智能分析
- **MAVSDK** - 无人机控制
- **slowapi** - 速率限制

### DevOps
- **Docker** - 容器化
- **Supabase** - 云存储
- **GitHub Actions** - CI/CD

---

## 📊 强大分析功能

### 1. 综合飞行评分系统
- ⭐ A+ (90-100分) - 完美飞行
- ⭐ A (80-89分) - 优秀飞行
- ⭐ B (70-79分) - 良好飞行
- ⭐ C (60-69分) - 一般飞行
- ⭐ D (<60分) - 需改进

### 2. PID调优分析
- ✅ Pitch/Roll/Yaw PID性能评估
- ✅ P/I/D参数诊断
- ✅ 振荡/漂移/噪声检测
- ✅ 自动优化建议

### 3. 滤波器优化
- ✅ Notch滤波器频率建议
- ✅ D-Term低通配置
- ✅ 陀螺仪滤波优化
- ✅ 振动频率FFT分析

### 4. GPS分析
- ✅ 位置精度评估
- ✅ 漂移检测与定位
- ✅ HDOP/HDOP分析
- ✅ 多卫星系统支持

### 5. 电池健康管理
- ✅ 电压/电流监控
- ✅ 容量衰减跟踪
- ✅ 温度峰值检测
- ✅ 寿命预测

---

## 🔧 配置指南

### 环境变量
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hkaic
OPENAI_API_KEY=your-openai-key
SECRET_KEY=your-secret-key
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

---

## 🎯 应用场景

### 竞速飞行
- ✅ Blackbox日志深度分析
- ✅ 电机平衡优化
- ✅ 响应速度提升
- ✅ Betaflight专业指南

### 花飞表演
- ✅ 平滑度优化
- ✅ 振动抑制
- ✅ 电机温度监控
- ✅ Freestyle配置模板

### 工业应用
- ✅ PX4飞控集成
- ✅ GPS精度分析
- ✅ 多无人机协同
- ✅ 工业级安全标准

### 研究开发
- ✅ 完整飞行数据
- ✅ 统计分析工具
- ✅ 自定义参数
- ✅ API开放接口

---

## 🤝 社区与支持

### 开源贡献
- 欢迎提交Issue和Pull Request
- 完整的贡献指南
- 活跃的社区讨论

### 学习资源
- 📖 PX4调参指南 (2000+行)
- 📖 Betaflight调参指南 (2000+行)
- 📖 飞行日志分析指南 (1000+行)
- 📖 API完整文档

### 专业支持
- 📧 邮件支持
- 💬 社区论坛
- 📚 详细文档
- 🔧 技术咨询

---

## 🌟 项目特色

### 行业首创
🏆 **最全面的无人机分析平台**  
🏆 **完整的PX4+Betaflight调参知识库**  
🏆 **5000+行专业调参文档**  
🏆 **整合10+顶级开源项目生态**  
🏆 **AI驱动的智能优化建议**

### 技术领先
⚡ **MAVSDK实时控制**  
⚡ **GPT-4深度分析**  
⚡ **多格式日志支持**  
⚡ **专业数据可视化**  
⚡ **企业级安全标准**

### 用户体验
🎨 **科幻风格UI**  
🎬 **流畅动画效果**  
📱 **全平台响应式**  
📊 **精美图表展示**  
🎯 **一键操作体验**

---

## 📈 版本信息

**当前版本**: 2.2.0  
**发布时间**: 2026-05-20  
**GitHub Stars**: 持续增长中 ⭐  

**主要更新:**
- ✨ 完整的PX4/Betaflight调参指南
- ✨ 开源项目深度整合
- ✨ 5种专业图表类型
- ✨ 20个功能卡片展示
- ✨ 全方位安全审计
- ✨ 实时无人机控制

---

**HKAIC - 让每一次飞行，都智能安全！ 🚁✨**

**GitHub仓库**: https://github.com/alib8b8/HKAIC

**文档**: https://github.com/alib8b8/HKAIC/tree/main/docs/TUNING_GUIDES

**安全等级**: 生产就绪 ⭐⭐⭐⭐⭐

---

让无人机飞行分析简单而智能！
