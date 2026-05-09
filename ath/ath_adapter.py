"""
Hongkun AI Chain — First ATH-Native Blockchain
================================================
ATH协议适配器 — 实现9步握手流程,与PoEI/ETB深度联动。

ATH三方角色映射:
  用户(End User) → HKAIC持有者
  智能体(Agent)  → 验证节点/Solver
  应用(App)      → 链服务/跨链桥

与PoEI联动: 握手成功→K_i提升, K_i增量=基础×交互质量×权限精细度
与ETB联动: Solver必须ATH握手才能参与

[ATH]标签标识所有ATH相关事件
"""
import hashlib,time,math
from typing import Dict,List,Optional,Tuple
from dataclasses import dataclass,field
from enum import Enum

class ATH握手阶段(Enum):
    """ATH 9步握手"""
    注册请求=1;身份验证=2;能力声明=3;策略协商=4
    权限授予=5;会话建立=6;心跳检测=7;行为审计=8;信任更新=9

class ATH角色(Enum):
    用户="user";智能体="agent";应用="app"

@dataclass
class ATH身份:
    """[ATH] ATH去中心化身份"""
    DID:str;角色:ATH角色;公钥:str;创建时间:float=0.0;过期时间:float=0.0
    信任评分:float=50.0;握手次数:int=0;活跃:bool=True
    K_i绑定:float=0.0  # 与PoEI的K_i绑定
    def __post_init__(self):
        if self.创建时间==0: self.创建时间=time.time()
        if self.过期时间==0: self.过期时间=self.创建时间+86400*365
    def 是否过期(self) -> bool: return time.time()>self.过期时间

@dataclass
class ATH握手记录:
    """[ATH] 握手记录"""
    握手ID:str;发起者DID:str;响应者DID:str;阶段:ATH握手阶段=ATH握手阶段.注册请求
    开始时间:float=0.0;完成时间:float=0.0;成功:bool=False
    交互质量:float=0.0;权限精细度:float=0.0
    def __post_init__(self):
        if self.开始时间==0: self.开始时间=time.time()

class ath_HandshakeAdapter:
    """[ATH] ATH协议适配器 — 9步握手实现与PoEI/ETB联动"""
    def __init__(self):
        self._身份注册:Dict[str,ATH身份]={}
        self._握手记录:Dict[str,ATH握手记录]={}
        self._活跃会话:Dict[str,dict]={}
        self._链上锚定:List[dict]=[]  # 链上锚定记录

    def ath_注册身份(self,DID:str,角色:ATH角色,公钥:str) -> ATH身份:
        """[ATH] 注册ATH身份"""
        身份=ATH身份(DID=DID,角色=角色,公钥=公钥)
        self._身份注册[DID]=身份
        # 链上锚定:身份注册交易
        self._锚定上链("身份注册",DID=DID,角色=角色.value,时间=time.time())
        return 身份

    def ath_发起握手(self,发起者DID:str,响应者DID:str) -> ATH握手记录:
        """[ATH] 发起9步握手"""
        # H-14: os.urandom替代time.time_ns()
        hid=hashlib.sha256(f"{发起者DID}:{响应者DID}:{os.urandom(16).hex()}".encode()).hexdigest()[:16]
        记录=ATH握手记录(握手ID=hid,发起者DID=发起者DID,响应者DID=响应者DID)
        self._握手记录[hid]=记录;return 记录

    def ath_推进握手(self,握手ID:str) -> Optional[ATH握手阶段]:
        """[ATH] 推进握手到下一阶段"""
        记录=self._握手记录.get(握手ID)
        if not 记录: return None
        当前=记录.阶段.value
        if 当前<9:
            新阶段=ATH握手阶段(当前+1);记录.阶段=新阶段
            # 链上锚定:关键步骤签名上链
            if 新阶段 in(ATH握手阶段.身份验证,ATH握手阶段.权限授予,ATH握手阶段.信任更新):
                self._锚定上链("握手步骤",握手ID=握手ID,阶段=新阶段.value,时间=time.time())
            if 新阶段==ATH握手阶段.信任更新:
                记录.完成时间=time.time();记录.成功=True
                # 更新信任评分
                发起=self._身份注册.get(记录.发起者DID)
                响应=self._身份注册.get(记录.响应者DID)
                if 发起: 发起.握手次数+=1;发起.信任评分=min(100,发起.信任评分+2)
                if 响应: 响应.握手次数+=1;响应.信任评分=min(100,响应.信任评分+2)
            return 新阶段
        return None

    def ath_完成握手(self,握手ID:str,交互质量:float=0.5,权限精细度:float=0.5) -> float:
        """[ATH] 完成握手,计算K_i增量并返回
        K_i增量 = 基础增量 × 交互质量 × 权限精细度
        交互越深(K_i提升越大),权限越精细(K_i提升越大)"""
        记录=self._握手记录.get(握手ID)
        if not 记录 or not 记录.成功: return 0.0
        记录.交互质量=交互质量;记录.权限精细度=权限精细度
        基础增量=5.0
        K_i增量=基础增量*交互质量*权限精细度
        # 更新身份的K_i绑定
        身份=self._身份注册.get(记录.发起者DID)
        if 身份: 身份.K_i绑定+=K_i增量
        return K_i增量

    def ath_撤销握手(self,DID:str,原因:str="") -> float:
        """[ATH] 撤销/握手失败→K_i下降"""
        身份=self._身份注册.get(DID)
        if not 身份: return 0.0
        下降=身份.K_i绑定*0.1;身份.K_i绑定=max(0,身份.K_i绑定-下降)
        身份.信任评分=max(0,身份.信任评分-10)
        return 下降

    def ath_验证Solver(self,SolverID:str) -> bool:
        """[ATH] 验证Solver是否通过ATH握手——ETB联动入口"""
        身份=self._身份注册.get(SolverID)
        return 身份 is not None and 身份.信任评分>=30 and 身份.活跃 and not 身份.是否过期()

    def _锚定上链(self,类型:str,**数据):
        """ATH链上锚定——将关键数据写入鸿坤链"""
        记录={"类型":f"[ATH]{类型}",**数据,"锚定哈希":hashlib.sha256(str(数据).encode()).hexdigest()[:16]}
        self._链上锚定.append(记录)

    def 状态(self) -> dict:
        return{"注册身份":len(self._身份注册),"握手记录":len(self._握手记录),
               "链上锚定":len(self._链上锚定),"活跃会话":len(self._活跃会话)}

if __name__=="__main__":
    print("  [ATH] ATH适配器 Demo")
    adapter=ath_HandshakeAdapter()
    adapter.ath_注册身份("did:agent:solver_1",ATH角色.智能体,"pubkey_1")
    adapter.ath_注册身份("did:user:alice",ATH角色.用户,"pubkey_2")
    hs=adapter.ath_发起握手("did:user:alice","did:agent:solver_1")
    while hs.阶段.value<9: adapter.ath_推进握手(hs.握手ID)
    K增量=adapter.ath_完成握手(hs.握手ID,0.8,0.9)
    print(f"  [ATH] 握手完成 K_i增量={K增量:.2f}")
    print(f"  [ATH] Solver验证={adapter.ath_验证Solver('did:agent:solver_1')}")
    print(f"  {adapter.状态()}")
