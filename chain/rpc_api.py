"""
Hongkun AI Chain — 语义接口 (rpc_api.py)
==========================================
自然语言查询、AI异常探测限流、WebSocket智能过滤推送。
"""
import hashlib
import os,os,time,re,logging
from typing import Dict,List,Optional,Callable,Any,Tuple
from dataclasses import dataclass,field
from enum import Enum

# ============================================================
# L-04修复: 日志脱敏函数 — 私钥/助记词自动替换，地址显示前6后4位
# ============================================================
# 配置日志记录器
_logger = logging.getLogger("hkc.rpc")

def 日志脱敏(文本: str) -> str:
    """L-04修复: 日志脱敏处理
    - 私钥（64位hex字符串）替换为 ***
    - 助记词（12/24个英文词序列）替换为 ***
    - 地址显示前6后4位，中间用...替代"""
    if not 文本:
        return 文本
    结果 = 文本
    # 替换私钥：匹配64位连续hex字符串（0x开头或不带前缀）
    结果 = re.sub(r'0x[0-9a-fA-F]{64}', '***', 结果)
    结果 = re.sub(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])', '***', 结果)
    # 替换助记词：匹配12或24个英文单词序列
    助记词模式 = r'(?:\b[a-z]+\b\s+){11,23}\b[a-z]+\b'
    结果 = re.sub(助记词模式, '***', 结果)
    # 脱敏地址：0x前缀地址显示前6后4位
    def _脱敏地址(match):
        addr = match.group(0)
        if len(addr) > 12:
            return addr[:6] + '...' + addr[-4:]
        return addr
    结果 = re.sub(r'0x[0-9a-fA-F]{8,40}', _脱敏地址, 结果)
    return 结果

# L-04: 安全日志函数，自动脱敏
def 安全日志(级别: str, 消息: str):
    """L-04: 安全日志记录，自动脱敏敏感信息"""
    脱敏消息 = 日志脱敏(消息)
    getattr(_logger, 级别, _logger.info)(脱敏消息)

class HTTP方法(Enum):
    GET="GET";POST="POST";PUT="PUT";DELETE="DELETE"

@dataclass
class API请求:
    方法:HTTP方法;路径:str;参数:Dict[str,Any]=field(default_factory=dict)
    体:str="";来源IP:str="127.0.0.1";时间戳:float=0.0
    def __post_init__(self):
        if self.时间戳==0: self.时间戳=time.time()

@dataclass
class API响应:
    状态码:int=200;数据:Any=None;消息:str=""
    @staticmethod
    def 成功(数据=None,消息="ok"): return API响应(200,数据,消息)
    @staticmethod
    def 错误(消息:str,码:int=400): return API响应(码,None,消息)
    @staticmethod
    def 限流(消息="AI检测到异常模式"): return API响应(429,None,消息)

class 自然语言解析器:
    """解析自然语言查询为结构化API调用"""
    _意图={"余额|balance|多少币":"balance","交易|转账|tx":"tx_list",
            "区块|block|高度":"block_info","质押|stake":"stake_info",
            "跨链|bridge":"bridge_info","合约|contract":"contract_info",
            "信息|info|状态":"chain_info"}
    def 解析(self,文本:str) -> dict:
        结果={"操作":"unknown","地址":"","时间范围":0,"方向":"both","数量":10,"原文":文本}
        for 模式,op in self._意图.items():
            if re.search(模式,文本): 结果["操作"]=op;break
        addr=re.search(r'(0x[a-fA-F0-9]{8,}|HKAIC_[a-zA-Z0-9]{8,})',文本)
        if addr: 结果["地址"]=addr.group(1)
        方向={"流入|收入|收到":"in","流出|支出|发送":"out","流入流出|双向":"both"}
        for p,d in 方向.items():
            if re.search(p,文本): 结果["方向"]=d;break
        num=re.search(r'最近(\d+)',文本)
        if num: 结果["数量"]=int(num.group(1))
        天=re.search(r'(\d+)天',文本)
        if 天: 结果["时间范围"]=int(天.group(1))
        return 结果
    def 生成描述(self,r:dict) -> str:
        ops={"balance":"余额","tx_list":"交易","block_info":"区块","stake_info":"质押",
             "bridge_info":"跨链","chain_info":"链信息"}
        return f"查询{r['地址'] or '全部'}的{ops.get(r['操作'],'信息')}"

class AI限流器:
    """AI自动识别异常查询模式，动态限流
    L-05修复: 默认限制调整为每IP每分钟60次请求"""
    def __init__(self,限制:int=60,窗口:int=60):
        self._限制=限制;self._窗口=窗口
        self._记录:Dict[str,List[float]]={};self._模式:Dict[str,Dict[str,int]]={}
        self._黑名单:Dict[str,float]={}
    def 检查(self,请求:API请求) -> Tuple[bool,str]:
        ip=请求.来源IP
        if ip in self._黑名单:
            if time.time()<self._黑名单[ip]: return False,"IP被临时封禁"
            del self._黑名单[ip]
        now=time.time();rec=self._记录.setdefault(ip,[])
        rec[:]=[t for t in rec if now-t<self._窗口];rec.append(now)
        if len(rec)>self._限制: self._黑名单[ip]=now+300;return False,"请求频率超限"
        模式=self._模式.setdefault(ip,{});模式[请求.路径]=模式.get(请求.路径,0)+1
        for 路径,cnt in 模式.items():
            if cnt>self._限制*0.5: self._黑名单[ip]=now+600;return False,"异常查询模式"
        return True,""
    def 状态(self) -> dict: return{"活跃IP":len(self._记录),"黑名单":len(self._黑名单)}

class RESTful处理器:
    """RESTful API+自然语言查询"""
    def __init__(self):
        self._路由:Dict[str,Callable]={};self._nl=自然语言解析器();self._注册默认()
    def _注册默认(self):
        self._路由.update({
            "GET /balance":lambda r:API响应.成功({"余额":"1000 HKAIC"}),
            "GET /tx":lambda r:API响应.成功({"交易":[]}),
            "POST /tx/send":lambda r:API响应.成功({"哈希":hashlib.sha256(os.urandom(32)).hexdigest()[:16]}),  # H-17: os.urandom替代time.time_ns()
            "GET /block":lambda r:API响应.成功({"高度":0}),
            "GET /info":lambda r:API响应.成功({"链名":"Hongkun AI Chain","代号":"HKC","版本":"4.0.0","共识":"PoEI"}),
            "POST /stake":lambda r:API响应.成功({"状态":"质押中"}),
            "POST /bridge/send":lambda r:API响应.成功({"意图ID":hashlib.sha256(os.urandom(32)).hexdigest()[:16]}),  # H-17: os.urandom替代time.time_ns()
            "POST /query":self._自然语言查询})
    def 注册路由(self,方法:str,路径:str,fn:Callable): self._路由[f"{方法} {路径}"]=fn
    def 处理请求(self,请求:API请求) -> API响应:
        键=f"{请求.方法.value} {请求.路径}";fn=self._路由.get(键)
        if not fn: return API响应.错误("未找到路由",404)
        try:
            return fn(请求)
        except Exception as e:
            # L-06修复: 只返回通用错误信息，详细错误记录服务端日志
            import traceback
            安全日志('error', f"REST API内部错误 {键}: {traceback.format_exc()}")
            return API响应.错误("Internal server error",500)
    def _自然语言查询(self,r:API请求) -> API响应:
        文本=r.体 or r.参数.get("q","")
        if not 文本: return API响应.错误("缺少查询内容")
        解析=self._nl.解析(文本);解析["描述"]=self._nl.生成描述(解析);return API响应.成功(解析)

class WS订阅:
    def __init__(self,cid:str,地址:str="",事件:List[str]=None,相关:List[str]=None):
        self.cid=cid;self.地址=地址;self.事件=事件 or[];self.相关=相关 or[]
    def 匹配(self,e:dict) -> bool:
        类型ok=not self.事件 or e.get("type") in self.事件
        地址ok=not self.相关 or any(a in str(e) for a in self.相关)
        return 类型ok and 地址ok

class WebSocket推送器:
    """智能过滤:只推送与用户相关的事件"""
    def __init__(self): self._subs:Dict[str,WS订阅]={};self._q:List[dict]=[];self._stat={"推送":0,"过滤":0}
    def 订阅(self,cid:str,**kw): self._subs[cid]=WS订阅(cid,**kw)
    def 取消订阅(self,cid:str): self._subs.pop(cid,None)
    def 推送事件(self,事件:dict) -> int:
        n=0
        for s in self._subs.values():
            if s.匹配(事件): self._q.append({"目标":s.cid,"事件":事件});n+=1;self._stat["推送"]+=1
            else: self._stat["过滤"]+=1
        return n
    def 状态(self) -> dict: return{"订阅":len(self._subs),"统计":self._stat}

class RPC服务器:
    """统筹RESTful+WebSocket+AI限流"""
    def __init__(self,rest端口:int=8843,ws端口:int=8844,api_key:str=""):
        self._rp=rest端口;self._wp=ws端口;self._rest=RESTful处理器()
        self._ws=WebSocket推送器();self._limiter=AI限流器();self._running=False
        # API Key认证：写操作需要提供有效API Key
        self._api_key=api_key or hashlib.sha256(os.urandom(32)).hexdigest()
        self._写操作={"POST /tx/send","POST /stake","POST /bridge/send"}
    @property
    def API密钥(self)->str:return self._api_key
    def 设置API密钥(self,key:str):self._api_key=key
    @property
    def rest处理器(self): return self._rest
    @property
    def ws推送器(self): return self._ws
    @property
    def 限流器(self): return self._limiter
    def 启动(self): self._running=True;return True
    def 停止(self): self._running=False
    def 处理请求(self,请求:API请求) -> API响应:
        ok,原因=self._limiter.检查(请求)
        if not ok: return API响应.限流(原因)
        # 写操作需要API Key认证
        操作键=f"{请求.方法.value} {请求.路径}"
        if 操作键 in self._写操作:
            提供key=请求.参数.get("api_key","")
            if 提供key!=self._api_key:
                return API响应.错误("未授权: 写操作需要有效的API Key",401)
        return self._rest.处理请求(请求)
    def 状态(self) -> dict: return{"运行":"✅" if self._running else "⏹","REST":self._rp,"WS":self._wp}

if __name__=="__main__":
    srv=RPC服务器();srv.启动();nl=自然语言解析器()
    for q in["查一下地址0xabc最近7天的流入量","最近5笔跨链交易"]: print(f"  {q}→{nl.生成描述(nl.解析(q))}")
    r=srv.处理请求(API请求(HTTP方法.POST,"/query",体="查余额"));print(f"  NL:{r.数据}")


# ============================================================
# 以太坊兼容 JSON-RPC 接口
# ============================================================
class 以太坊RPC处理器:
    """
    以太坊标准JSON-RPC接口适配层
    支持MetaMask/SafePal/imToken/Trust Wallet连接
    """

    def __init__(self, 链ID: int = 9901):
        self._chain_id = 链ID
        self._待广播交易: Dict[str, bytes] = {}
        self._已确认交易: Dict[str, dict] = {}
        self._区块数据: Dict[int, dict] = {0: {"number": "0x0", "hash": "0x" + "0"*64, "transactions": []}}
        self._当前块高 = 0
        self._地址nonce: Dict[str, int] = {}
        self._gas价格 = 10 ** 10  # 10 Gwei

    def 处理JSONRPC(self, 方法: str, 参数: list = None) -> dict:
        """处理以太坊JSON-RPC请求"""
        参数 = 参数 or []
        处理器 = {
            "eth_chainId": self._eth_chainId,
            "eth_getBalance": self._eth_getBalance,
            "eth_sendRawTransaction": self._eth_sendRawTransaction,
            "eth_getTransactionByHash": self._eth_getTransactionByHash,
            "eth_getTransactionReceipt": self._eth_getTransactionReceipt,
            "eth_blockNumber": self._eth_blockNumber,
            "eth_getBlockByNumber": self._eth_getBlockByNumber,
            "eth_call": self._eth_call,
            "eth_estimateGas": self._eth_estimateGas,
            "eth_gasPrice": self._eth_gasPrice,
            "eth_getTransactionCount": self._eth_getTransactionCount,
            "net_version": self._net_version,
            "web3_clientVersion": self._web3_clientVersion,
        }
        fn = 处理器.get(方法)
        if fn is None:
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {方法}"}, "id": None}
        try:
            结果 = fn(参数)
            return {"jsonrpc": "2.0", "result": 结果, "id": 1}
        except Exception as e:
            # L-06修复: 只返回通用错误信息，详细错误只记录服务端日志
            import traceback
            安全日志('error', f"JSON-RPC内部错误: {traceback.format_exc()}")
            return {"jsonrpc": "2.0", "error": {"code": -32000, "message": "Internal error"}, "id": 1}

    def _eth_chainId(self, 参数) -> str:
        """eth_chainId — 返回链ID"""
        return "0x" + hex(self._chain_id)[2:]

    def _eth_getBalance(self, 参数) -> str:
        """eth_getBalance — 查询余额"""
        地址 = 参数[0] if 参数 else "0x" + "0" * 40
        # 通过映射查找余额
        from .wallet_adapter import 地址适配器
        适配 = 地址适配器()
        hkc地址 = 适配.EVM到HKC(地址)
        余额鸿坤 = 0
        if hkc地址 and hasattr(self, '_账本') and self._账本:
            余额鸿坤 = self._账本.查询余额(hkc地址)
        return "0x" + hex(余额鸿坤)[2:] if 余额鸿坤 > 0 else "0x0"

    def _eth_sendRawTransaction(self, 参数) -> str:
        """eth_sendRawTransaction — 广播签名交易"""
        from .eip155 import EIP155交易
        from .evm_compat import keccak256
        rawhex = 参数[0].replace("0x", "") if 参数 else ""
        rawbytes = bytes.fromhex(rawhex)
        交易哈希 = keccak256(rawbytes)
        哈希hex = "0x" + 交易哈希.hex()
        self._待广播交易[哈希hex] = rawbytes
        # 尝试解码交易
        try:
            tx = EIP155交易.从原始交易(rawbytes)
            self._已确认交易[哈希hex] = tx.到字典()
            self._已确认交易[哈希hex]["交易哈希"] = 哈希hex
            self._当前块高 += 1
            self._已确认交易[哈希hex]["块高"] = self._当前块高
        except Exception:
            pass
        return 哈希hex

    def _eth_getTransactionByHash(self, 参数) -> dict:
        """eth_getTransactionByHash — 查询交易"""
        哈希 = 参数[0] if 参数 else ""
        交易 = self._已确认交易.get(哈希)
        if 交易:
            return {
                "hash": 哈希,
                "nonce": 交易.get("nonce", "0x0"),
                "blockHash": "0x" + "0" * 64,
                "blockNumber": hex(交易.get("块高", 0)),
                "transactionIndex": "0x0",
                "from": 交易.get("from", "0x" + "0" * 40),
                "to": 交易.get("to", "0x" + "0" * 40),
                "value": 交易.get("value", "0x0"),
                "gas": 交易.get("gasLimit", "0x5208"),
                "gasPrice": 交易.get("gasPrice", "0x2540be400"),
                "input": 交易.get("data", "0x"),
                "v": 交易.get("v", "0x0"),
                "r": 交易.get("r", "0x0"),
                "s": 交易.get("s", "0x0"),
            }
        return None

    def _eth_getTransactionReceipt(self, 参数) -> dict:
        """eth_getTransactionReceipt — 查询交易回执"""
        哈希 = 参数[0] if 参数 else ""
        交易 = self._已确认交易.get(哈希)
        if 交易:
            return {
                "transactionHash": 哈希,
                "transactionIndex": "0x0",
                "blockHash": "0x" + "0" * 64,
                "blockNumber": hex(交易.get("块高", 0)),
                "from": 交易.get("from", "0x" + "0" * 40),
                "to": 交易.get("to", "0x" + "0" * 40),
                "cumulativeGasUsed": "0x5208",
                "gasUsed": "0x5208",
                "contractAddress": None,
                "logs": [],
                "logsBloom": "0x" + "0" * 512,
                "status": "0x1",
                "effectiveGasPrice": 交易.get("gasPrice", "0x2540be400"),
            }
        return None

    def _eth_blockNumber(self, 参数) -> str:
        """eth_blockNumber — 最新区块号"""
        return "0x" + hex(self._当前块高)[2:]

    def _eth_getBlockByNumber(self, 参数) -> dict:
        """eth_getBlockByNumber — 查询区块"""
        块高hex = 参数[0] if 参数 else "0x0"
        块高 = int(块高hex, 16)
        return {
            "number": 块高hex,
            "hash": "0x" + hashlib.sha256(str(块高).encode()).hexdigest(),
            "parentHash": "0x" + "0" * 64,
            "nonce": "0x0000000000000000",
            "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
            "logsBloom": "0x" + "0" * 512,
            "transactionsRoot": "0x" + "0" * 64,
            "stateRoot": "0x" + "0" * 64,
            "receiptsRoot": "0x" + "0" * 64,
            "miner": "0x" + "0" * 40,
            "difficulty": "0x0",
            "totalDifficulty": "0x0",
            "extraData": "0x",
            "size": "0x0",
            "gasLimit": "0x1c9c380",
            "gasUsed": "0x0",
            "timestamp": hex(int(time.time())),
            "transactions": [],
            "uncles": [],
        }

    def _eth_call(self, 参数) -> str:
        """eth_call — 只读合约调用"""
        return "0x"

    def _eth_estimateGas(self, 参数) -> str:
        """eth_estimateGas — 估算Gas"""
        return "0x5208"

    def _eth_gasPrice(self, 参数) -> str:
        """eth_gasPrice — 当前Gas价格"""
        return "0x" + hex(self._gas价格)[2:]

    def _eth_getTransactionCount(self, 参数) -> str:
        """eth_getTransactionCount — 获取nonce"""
        地址 = 参数[0] if 参数 else "0x" + "0" * 40
        nonce = self._地址nonce.get(地址.lower(), 0)
        return "0x" + hex(nonce)[2:]

    def _net_version(self, 参数) -> str:
        """net_version — 网络版本号"""
        return str(self._chain_id)

    def _web3_clientVersion(self, 参数) -> str:
        """web3_clientVersion — 客户端版本"""
        return "HongkunAIChain/v4.0.0/HKC-EVM-Compatible"

    def 绑定账本(self, 账本实例):
        """绑定鸿坤内部账本实例"""
        self._账本 = 账本实例

    def 增加nonce(self, 地址: str):
        """交易确认后增加nonce"""
        self._地址nonce[地址.lower()] = self._地址nonce.get(地址.lower(), 0) + 1


# 向RPC服务器注入以太坊RPC处理器
def 创建EVM兼容RPC(链ID: int = 9901) -> 以太坊RPC处理器:
    """创建EVM兼容的JSON-RPC处理器"""
    return 以太坊RPC处理器(链ID=链ID)
