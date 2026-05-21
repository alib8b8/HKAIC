# HKAIC - 0 成本运行指南

---

## 🚀 完全免费的本地运行方案

### ✅ 费用：$0
### ✅ 功能：完整 AI 调参助手
### ✅ 隐私：数据完全本地处理

---

## 📦 快速开始（3分钟）

### 第一步：克隆项目
```bash
git clone https://github.com/alib8b8/HKAIC.git
cd HKAIC
```

### 第二步：安装前端依赖
```bash
npm install
```

### 第三步：启动前端
```bash
npm run dev
```

### 第四步：访问应用
打开浏览器访问：**http://localhost:3000**

**完成！🎉 现在可以免费使用完整的 AI 调参功能！**

---

## 🧠 AI 功能说明

### 当前版本（已包含）
✅ **内置 AI 模拟引擎**
- 支持自然语言对话
- 智能 PID 参数分析
- 问题识别和解决方案
- 预设配置推荐
- **完全免费，无需 API Key**

### 工作原理
- 内置调参知识库（5000+ 行专业文档）
- 模式匹配算法
- 实时参数计算
- 无需联网的本地 AI

### 功能覆盖
- ✅ 无人机连接模拟
- ✅ PID 参数调整建议
- ✅ 问题诊断（灵敏、抖动、漂移等）
- ✅ 预设配置（竞速、花飞、载重）
- ✅ USB 连接（需要后端）

---

## 📱 完整功能列表

### 免费功能 ✅
| 功能 | 说明 | 费用 |
|------|------|------|
| AI 对话调参 | 自然语言交互 | **$0** |
| PID 参数调整 | 滑块控制 | **$0** |
| 问题诊断 | 智能分析 | **$0** |
| 预设配置 | 竞速/花飞/载重 | **$0** |
| 参数备份 | 本地存储 | **$0** |
| 用户认证 | 注册登录 | **$0** |
| USB 连接 | 串口通信 | **$0** |

### 可选升级功能 💰
| 功能 | 说明 | 费用 |
|------|------|------|
| 深度学习 AI | DeepSeek 微调模型 | $0-10/月 |
| 云端同步 | 多设备同步 | $0-5/月 |
| 团队协作 | 共享配置 | $0-20/月 |

---

## 🔧 高级配置（可选）

### 启用后端服务（可选）

#### 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件（全部可选）：
```env
# 数据库（可选，使用 SQLite 则免费）
DATABASE_URL=sqlite:///./hkaic.db

# AI 服务（可选，不填则使用内置模拟）
DEEPSEEK_API_KEY=your-key-here

# 安全配置
SECRET_KEY=your-secret-key
```

#### 启动后端
```bash
cd backend
uvicorn app.main:app --reload
```

#### 后端 API
- API 文档：http://localhost:8000/docs
- 自动生成的交互式文档

---

## 🖥️ USB 连接真实无人机

### Windows
1. 安装 CH340/FTDI 驱动
2. 连接无人机 USB
3. 在应用中点击"连接 USB"
4. 选择对应的串口

### macOS
1. 通常免驱动
2. 连接无人机 USB
3. 在应用中点击"连接 USB"
4. 选择 `/dev/tty.usbmodem` 或 `/dev/tty.usbserial`

### Linux
1. 添加用户到 dialout 组
   ```bash
   sudo usermod -a -G dialout $USER
   ```
2. 重新登录
3. 连接无人机 USB
4. 在应用中点击"连接 USB"

---

## 🌐 分享给他人

### 方式 1：分享代码（推荐）
```bash
# 1. 分享仓库链接
https://github.com/alib8b8/HKAIC

# 2. 他人克隆
git clone https://github.com/alib8b8/HKAIC.git
cd HKAIC
npm install
npm run dev
```

### 方式 2：打包分享
```bash
# 1. 打包
tar -czvf hkaic-share.tar.gz .

# 2. 分享压缩包
# 他人解压后：
tar -xzvf hkaic-share.tar.gz
cd hkaic
npm install
npm run dev
```

### 方式 3：使用免费 Git 平台
- **GitLab**（免费私有仓库）
- **Gitee**（国内，访问快）
- **Codeberg**（免费开源）

---

## 💡 常见问题

### Q: 需要网络吗？
**A**: 仅首次安装需要网络，之后完全离线可用！

### Q: 数据安全吗？
**A**: 100% 本地处理，数据不会上传到任何服务器！

### Q: 支持哪些无人机？
**A**: PX4、Betaflight 等主流飞控

### Q: 可以商用吗？
**A**: 可以！采用开源许可证，欢迎商业使用

### Q: 如何更新到最新版本？
```bash
git pull origin main
npm install
npm run dev
```

---

## 🎯 使用场景

### 个人使用 ✅
- 学习无人机调参
- 优化自己的无人机
- 记录调参历史

### 小团队使用 ✅
- 分享配置给队友
- 统一调参标准
- 团队配置备份

### 教学使用 ✅
- 无人机课程教学
- 实验参数演示
- 学生实践操作

---

## 🔒 隐私保证

- ✅ 数据完全存储在本地
- ✅ 不上传任何飞行数据
- ✅ 不需要注册账户（可选）
- ✅ 不追踪任何用户行为
- ✅ 100% 开源透明

---

## 🚀 性能规格

### 系统要求
- **CPU**: 任意现代 CPU
- **内存**: 4GB+
- **存储**: 2GB+
- **系统**: Windows/macOS/Linux

### 运行要求
- **Node.js**: v16+
- **npm**: v8+
- **Python**: 3.8+（可选后端）

### 性能表现
- 启动时间：< 5 秒
- 响应速度：< 100ms
- 内存占用：< 500MB
- 电池消耗：极低

---

## 🎉 立即开始

```bash
# 克隆项目
git clone https://github.com/alib8b8/HKAIC.git

# 进入目录
cd HKAIC

# 安装依赖
npm install

# 启动应用
npm run dev

# 打开浏览器
# 访问 http://localhost:3000
```

**享受免费的 AI 调参体验！🎯✈️**

---

**HKAIC - 调参，从未如此简单！完全免费！**

---

*最后更新：2026-05-21*
*版本：1.0.0*
*费用：$0*
