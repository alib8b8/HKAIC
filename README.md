# HKAIC - AI Drone Flight Intelligence SaaS

🚀 **业界领先的AI驱动无人机飞行智能分析平台 - 企业级SaaS解决方案

---

## ✨ 核心亮点

### 🔥 无人机控制与实时飞行
- **真实无人机连接**：无缝集成MAVSDK，支持PX4、Betaflight等主流飞控
- **实时遥测监控**：位置、姿态、电池、飞行状态实时展示
- **一键紧急停止**：保障安全的紧急降落系统
- **模拟模式**：安全测试无风险

### 🤖 AI智能分析
- **AI深度洞察**：OpenAI驱动的智能分析和改进建议
- **多维度评估**：效率、稳定性、风险全面分析
- **精准诊断**：振动、GPS漂移、电机异常智能检测
- **PID优化建议**：基于数据的飞控参数优化指南

### 💰 完整SaaS架构
- **多租户隔离**：企业级数据安全保障
- **订阅管理**：4级灵活定价方案（Free/Basic/Pro/Enterprise）
- **配额控制系统**：智能月度分析配额动态管理
- **团队协作**：支持多成员协作

### 🔒 极致安全
- **全面安全审计**：13项安全保障措施全覆盖
- **速率限制保护**：防DoS攻击多重防护
- **实时审计日志**：操作全程可追溯
- **操作日志记录**：IP追踪+用户ID双向绑定
- **频率限制**：恶意行为智能拦截
- **紧急降落**：突发状况安全保障

### 🎯 精准分析能力
- **飞行综合评分**：效率、稳定性、性能一键评级
- **PID调优分析**：Pitch/Roll/Yaw深度诊断
- **GPS漂移检测**：位置精度精确定位
- **振动分析报告**：振动监测专业级报告
- **电机异常诊断**：提前预警维护

### 📊 多格式支持
- **Betaflight Blackbox格式**
- **PX4 ULog格式**
- **通用CSV格式**

### 💎 精美用户体验
- **酷炫深色科幻风格**：未来风格UI
- **完全响应式设计**：移动端、平板、桌面端全适配
- **流畅动画效果**：Framer Motion丝滑体验
- **精美仪表盘**：数据可视化图表清晰美观
- **直观报告展示**：美观报告一目了然

---

## 📊 灵活订阅方案

| 方案 | 月度价格 | 年度价格 | 月度配额 | 最大文件大小 | AI分析 | 优先支持 | API访问 | 团队成员 |
|------|---------|---------|---------|-------------|---------|----------|----------|-----------|
| Free | $0 | $0 | 5 | 10 MB | ✅ | ✅ | ✅ | 1 |
| Basic | $9.99 | $99 | 25 | 50 MB | ✅ | ✅ | ✅ | 1 |
| Pro | $29.99 | $299 | 100 | 100 MB | ✅ | ✅ | ✅ | 3 |
| Enterprise | $99.99 | $999 | 500 | 500 MB | ✅ | ✅ | ✅ | 10 |

---

## 🏗️ 现代技术架构

```
hkaic/
├── frontend/                 # Next.js前沿架构
│   ├── app/              # App Router最新架构
│   ├── components/       # React高级组件
│   └── package.json
│
└── backend/                # FastAPI高性能架构
    ├── app/
    │   ├── api/          # 完整RESTful API
    │   ├── drone_manager.py  # 无人机管理核心
    │   ├── audit_logger.py   # 安全审计记录
    │   └── health_checker.py # 健康监控系统
    ├── Dockerfile
    └── docker-compose.yml
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
- **前端**：http://localhost:3000
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

---

## 📚 API完整API文档

### 核心端点概览

| 端点 | 方法 | 功能 |
|------|------|------|
| `POST /api/auth/register` | POST | 注册新用户 |
| `POST /api/auth/login` | POST | 登录获取令牌 |
| `GET /api/subscription/plans` | GET | 获取订阅方案 |
| `POST /api/upload/` | POST | 上传飞行日志 |
| `POST /api/analysis/` | POST | 分析飞行日志 |
| `POST /api/drone/connect` | POST | 连接真实无人机 |
| `POST /api/drone/takeoff` | POST | 无人机起飞 |
| `POST /api/drone/land` | POST | 无人机降落 |
| `POST /api/drone/emergency-stop` | POST | 🚨 紧急停止 |
| `GET /api/drone/statistics` | GET | 实时统计数据 |

---

## 🛠️ 现代技术栈

### 前端技术
- **框架**：Next.js 14 (最新版)
- **语言**：TypeScript
- **样式**：Tailwind CSS 3
- **动画**：Framer Motion
- **图表**：Recharts
- **图标**：Lucide React

### 后端技术
- **框架**：FastAPI (极速高性能API
- **语言**：Python 3.11
- **数据库**：PostgreSQL 企业级数据库
- **ORM**：SQLAlchemy 2.0
- **认证**：JWT安全认证
- **AI**：OpenAI API
- **无人机**：MAVSDK
- **速率限制**：slowapi
- **文档**：Swagger UI + ReDoc

### DevOps
- **容器化**：Docker + Docker Compose
- **云存储**：Supabase / S3
- **监控**：健康监控系统

---

## 🔧 轻松配置

### 环境变量配置
```env
DATABASE_URL=sqlite:///./hkaic.db
OPENAI_API_KEY=your-openai-key
SECRET_KEY=your-secret-key
```

---

## 📊 强大分析功能

### 1. 综合飞行评分系统
- 效率评分
- 稳定性评分
- 综合性能评级
- 风险等级评估

### 2. PID调优分析
- Pitch PID 性能分析
- Roll PID 性能分析
- Yaw PID 性能分析
- 优化建议生成

### 3. GPS漂移检测
- 位置精度分析
- 漂移模式检测
- 问题区域识别

### 4. 振动分析
- 最大振动检测
- 平均振动监控
- 峰值精确定位

### 5. 电机异常检测
- 电机性能分析
- 异常模式检测
- 维护建议

---

## 🤝 优秀社区支持

欢迎贡献！提交Pull Request共同进步！

---

## 📞 专属支持

专业级支持渠道

- 文档完备的完整详尽的文档全面的文档
- 开源社区活跃
- 快速响应支持
- 持续功能更新

---

**HKAIC - 让无人机飞行分析简单而智能！ 🚁✨

**GitHub仓库**: https://github.com/alib8b8/HKAIC

**版本**: 2.2.0

**安全等级**: 生产就绪 ⭐⭐⭐⭐⭐

---

让每一次飞行，都安全智能！
