# HKAIC 项目安全自检报告

## 📅 检查日期
2026-05-19

## 🔍 检查范围
- 后端代码安全
- 前端代码安全
- 依赖安全问题
- 数据验证问题

---

## 🚨 发现的问题汇总

### 🔴 严重问题

#### 1. **导入模块缺失**
**位置**：多个文件
- [backend/app/api/auth.py](file:///workspace/hkaic/backend/app/api/auth.py#L11)
- [backend/app/api/upload.py](file:///workspace/hkaic/backend/app/api/upload.py#L9)
- [backend/app/auth.py](file:///workspace/hkaic/backend/app/auth.py#L14)

**问题描述**：
```python
from app.models import User  # 但 app/models.py 文件不存在！
```

模型类实际上是在 `app/database.py` 中定义的，但代码尝试从不存在的 `app/models.py` 导入。

**影响**：应用无法启动，会报 ImportError 错误。

**修复建议**：
将导入语句改为从 `app.database` 导入：
```python
from app.database import User, SubscriptionPlan
```

---

### 🟡 高优先级问题

#### 2. **缺少密码强度验证**
**位置**：[backend/app/api/auth.py](file:///workspace/hkaic/backend/app/api/auth.py#L25-L55)

**问题描述**：
用户注册时没有对密码进行强度验证（如长度、复杂度等），允许弱密码。

**影响**：
- 账户更容易被暴力破解
- 不符合安全最佳实践

**修复建议**：
添加密码强度验证：
```python
import re

def validate_password_strength(password: str):
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )
    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one lowercase letter"
        )
    if not re.search(r'[0-9]', password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one number"
        )
```

#### 3. **文件名处理安全问题**
**位置**：[backend/app/api/upload.py](file:///workspace/hkaic/backend/app/api/upload.py#L64-L65)

**问题描述**：
虽然使用了 uuid 前缀，但文件名仍保留原始文件名，可能包含特殊字符或路径遍历尝试。

**修复建议**：
清理文件名，只保留安全字符：
```python
import re
safe_filename = re.sub(r'[^\w\-_.]', '_', filename)
unique_filename = f"{uuid.uuid4()}_{safe_filename}"
```

#### 4. **未限制文件上传速率**
**问题描述**：
没有速率限制，可能被用来进行拒绝服务攻击或消耗配额。

**修复建议**：
添加速率限制：
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
async def upload_flight_log(...):
```

---

### 🟢 中优先级问题

#### 5. **缺少请求日志记录**
**问题描述**：
没有安全相关的日志记录（如登录失败、敏感操作等），难以审计和检测攻击。

**修复建议**：
添加结构化日志：
```python
import logging

logger = logging.getLogger(__name__)

# 在登录失败时记录
logger.warning(f"Failed login attempt for email: {login_data.email}")
```

#### 6. **异常处理过于宽泛**
**位置**：[backend/app/api/upload.py](file:///workspace/hkaic/backend/app/api/upload.py#L138-L142)

**问题描述**：
```python
except:  # 捕获所有异常
    pass
```
这会隐藏潜在的错误，且不记录任何信息。

**修复建议**：
```python
except Exception as e:
    logger.error(f"Error deleting file: {e}")
```

#### 7. **JWT 令牌没有黑名单机制**
**问题描述**：
用户注销后，已签发的令牌仍然有效，无法主动撤销。

**修复建议**：
添加 Redis 或数据库存储的令牌黑名单：
```python
invalid_tokens = set()  # 实际应用请用 Redis

def invalidate_token(token: str):
    invalid_tokens.add(token)
```

#### 8. **订阅配额检查逻辑缺失**
**位置**：[backend/app/api/analysis.py](file:///workspace/hkaic/backend/app/api/analysis.py)

**问题描述**：
虽然检查了配额，但没有检查订阅是否过期，也没有重置月度配额的机制。

**修复建议**：
添加订阅过期检查和配额重置逻辑。

---

### 📦 依赖安全检查

#### 9. **部分依赖版本较旧**

检查到的潜在问题：
- `fastapi==0.109.0` - 建议关注更新
- `openai==1.10.0` - 建议保持最新
- `passlib[bcrypt]==1.7.4` - 考虑更新

**建议**：
定期运行安全审计：
```bash
cd backend
pip install safety
safety check  # 检查依赖漏洞
```

---

### 🎨 前端安全检查

#### 10. **缺少基础安全头**
**问题描述**：
没有看到 CSP、X-Frame-Options 等安全头的设置。

**修复建议**：
在 Next.js 中添加安全头：
```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },
};
```

---

### 🗄️ 数据库安全

#### 11. **SQL 注入防护**
**检查结果**：✅ 使用 SQLAlchemy ORM，应该是安全的
- 没有发现直接拼接 SQL 的情况
- 使用参数化查询

**建议**：继续保持使用 ORM。

---

### 🔧 配置安全

#### 12. **环境变量示例包含默认密钥**
**位置**：[backend/.env.example](file:///workspace/hkaic/backend/.env.example#L17)

**问题描述**：
```
SECRET_KEY=your-secret-key-here-change-in-production
```
虽然不是真实密钥，但建议移除或更清楚地标注。

#### 13. **缺少生产环境检查**
**问题描述**：
没有强制检查生产环境是否使用了安全的密钥配置。

---

## 📋 修复优先级建议

### 立即修复 (P0)
1. **导入模块缺失** - 阻止应用正常运行
2. **添加密码强度验证** - 基本安全保障

### 高优先级 (P1)
3. **改进文件名处理**
4. **添加速率限制**
5. **改进异常处理**

### 中优先级 (P2)
6. **添加安全日志**
7. **JWT 黑名单机制**
8. **完善订阅检查**
9. **前端安全头**

### 低优先级 (P3)
10. **依赖更新**
11. **配置改进**

---

## ✅ 做得好的地方

1. **使用 bcrypt 哈希密码** - 安全的哈希算法
2. **多租户数据隔离** - 用户只能访问自己的数据
3. **JWT 认证机制** - 标准的无状态认证
4. **文件大小限制** - 防止过大文件上传
5. **文件类型验证** - 防止恶意文件上传
6. **使用 SQLAlchemy ORM** - 防止 SQL 注入
7. **CORS 配置** - 基础的跨域控制

---

## 📝 安全最佳实践建议

### 1. **实施定期安全审计**
- 每月运行依赖漏洞扫描
- 定期进行代码审查
- 渗透测试（生产环境前）

### 2. **添加监控和告警**
- 登录失败监控
- 异常访问模式检测
- 配额超额告警

### 3. **备份和恢复计划**
- 定期数据库备份
- 加密备份数据
- 测试恢复流程

### 4. **文档和培训**
- 安全编码规范文档
- 团队安全培训
- 事件响应预案

---

## 🔗 相关资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Docs](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Security](https://nextjs.org/docs/app/building-your-application/deploying/production-checklist)

---

**报告完成时间**：2026-05-19
**检查人**：AI Assistant
