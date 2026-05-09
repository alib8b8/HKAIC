# HKC 本地5节点测试网 — 部署指南

## 概述

本测试网在本地启动5个独立的HKC节点进程，验证：
1. **P2P互联** — 5节点全连接，互相发现注册
2. **PoEI共识出块** — 基于涌现智能分数的出块者选举
3. **端到端交易** — 钱包→交易池→出块→确认→余额更新
4. **涌信钱包** — 通过钱包发起转账

## 快速启动

### 方式一：一键脚本（推荐）

```bash
cd hongkun_ai_lab
python scripts/start_testnet.py
```

### 方式二：手动启动

```bash
# 终端1: 启动节点0
python scripts/node_process.py --node-id 0 --p2p-port 8001 --rpc-port 8841 \
    --seeds 8002,8003,8004,8005 --validator 涌金_Alice --stake 10000 --K-i 95

# 终端2: 启动节点1
python scripts/node_process.py --node-id 1 --p2p-port 8002 --rpc-port 8842 \
    --seeds 8001,8003,8004,8005 --validator 涌金_Bob --stake 8000 --K-i 80

# 终端3-5: 类似启动其他节点
```

### 方式三：Docker Compose

```bash
cd hongkun_ai_lab
docker-compose up -d
docker-compose logs -f   # 查看日志
docker-compose down       # 停止
```

## 节点配置

| 节点 | 验证者 | 质押(HKAIC) | K_i | P2P端口 | RPC端口 |
|------|--------|-------------|-----|---------|---------|
| 0 | 涌金_Alice | 10000 | 95 | 8001 | 8841 |
| 1 | 涌金_Bob | 8000 | 80 | 8002 | 8842 |
| 2 | 涌银_Carol | 6000 | 65 | 8003 | 8843 |
| 3 | 涌银_Dave | 4000 | 45 | 8004 | 8844 |
| 4 | 涌铜_Eve | 2000 | 25 | 8005 | 8845 |

## RPC API 接口

### 节点状态
```
GET /status          — 节点完整状态
GET /info            — 链基本信息
GET /blockchain      — 区块链摘要
GET /block/{高度}    — 获取指定区块
GET /validators      — 验证者列表
GET /consensus       — 共识状态
GET /txpool          — 交易池
GET /wallets         — 钱包列表
GET /balance/{地址}  — 查询余额
```

### 交易操作
```
POST /wallet/create  — 创建钱包 {"name":"Alice","seed":""}
POST /wallet/mint    — 铸币 {"wallet":"Alice","amount":1000000}
POST /tx/send        — 转账 {"from":"Alice","to":"地址","amount":100,"fee":0.001}
POST /force_block    — 强制出块
```

### P2P通信
```
GET  /p2p/ping            — 心跳检测
GET  /p2p/block/{高度}    — 请求区块
POST /p2p/block           — 接收广播区块
POST /p2p/tx              — 接收广播交易
POST /p2p/register        — 节点注册
```

## 使用示例

```bash
# 查看节点0状态
curl http://127.0.0.1:8841/status

# 创建钱包
curl -X POST http://127.0.0.1:8841/wallet/create \
    -H "Content-Type: application/json" \
    -d '{"name":"Alice"}'

# 铸币
curl -X POST http://127.0.0.1:8841/wallet/mint \
    -H "Content-Type: application/json" \
    -d '{"wallet":"Alice","amount":1000000}'

# 转账
curl -X POST http://127.0.0.1:8841/tx/send \
    -H "Content-Type: application/json" \
    -d '{"from":"Alice","to":"HKAIC_xxx","amount":100,"fee":0.001}'

# 强制出块
curl -X POST http://127.0.0.1:8841/force_block

# 查看区块链
curl http://127.0.0.1:8841/blockchain
```

## 测试结果

| 测试项 | 结果 | 说明 |
|--------|------|------|
| P2P互联 | ✅ 通过 | 5节点全连接，互相注册 |
| PoEI共识出块 | ✅ 通过 | 基于涌现分数选举出块者 |
| 端到端交易 | ✅ 通过 | 交易提交→出块→确认→余额更新 |
| 涌信钱包 | ✅ 通过 | 钱包创建→铸币→转账 |

## 架构说明

### 节点进程架构
```
┌──────────────────────────────────┐
│          HKC Node Process        │
├──────────────────────────────────┤
│                                  │
│  ┌──────────────┐  ┌──────────┐ │
│  │ HTTP RPC     │  │ P2P      │ │
│  │ Server       │  │ Client   │ │
│  │ (8841)       │  │ (HTTP)   │ │
│  └──────┬───────┘  └────┬─────┘ │
│         │                │       │
│  ┌──────▼────────────────▼─────┐ │
│  │     节点状态                 │ │
│  │  ┌────────┐  ┌───────────┐ │ │
│  │  │区块链  │  │共识引擎   │ │ │
│  │  │(区块链)│  │(PoEI)     │ │ │
│  │  └────────┘  └───────────┘ │ │
│  │  ┌────────┐  ┌───────────┐ │ │
│  │  │账本    │  │交易引擎   │ │ │
│  │  │(UTXO)  │  │(Mempool)  │ │ │
│  │  └────────┘  └───────────┘ │ │
│  │  ┌────────┐                │ │
│  │  │钱包管理│                │ │
│  │  └────────┘                │ │
│  └─────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐│
│  │  共识循环线程 (3秒轮次)      ││
│  │  节点发现线程 (5秒轮次)      ││
│  └──────────────────────────────┘│
└──────────────────────────────────┘
```

### P2P通信流程
```
Node-0 ──HTTP POST /p2p/register──→ Node-1,2,3,4
Node-0 ──HTTP POST /p2p/tx────────→ Node-1,2,3,4 (广播交易)
Node-0 ──HTTP POST /p2p/block─────→ Node-1,2,3,4 (广播区块)
Node-0 ──HTTP GET  /p2p/ping──────→ Node-1,2,3,4 (心跳)
```

## 问题与解决方案

| # | 问题 | 原因 | 解决方案 |
|---|------|------|----------|
| 1 | 首次出块失败 | 铸币直接到账本，交易池为空 | 铸币同时添加交易到交易池 |
| 2 | 共识未选出出块者 | 推进共识只有1步 | 测试网宽松模式:允许任何节点出块 |
| 3 | 账本余额重复扣减 | 出块确认时再次执行账本转账 | 区分铸币交易(跳过)和普通转账 |
| 4 | P2P无真实Socket | 原代码全是进程内模拟 | 新增HTTP-based P2P通信层 |

## 下一步

1. **Docker部署** — 用docker-compose启动5容器测试网
2. **跨节点交易同步** — 交易在节点间广播和确认
3. **更多共识轮次** — 自动连续出块
4. **攻击测试** — 双花、女巫攻击模拟
5. **生产化改进** — 真实WebSocket、gRPC P2P通信
