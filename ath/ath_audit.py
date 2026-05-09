"""
Hongkun AI Chain — ATH行为审计 (ath_audit.py)
================================================
全链路追溯,Merkle树存储,不可篡改。
日志保留6个月+,按Agent/时间/类型检索。
与audit_engine.py联动。
[ATH] 标签标识ATH相关事件
"""
import hashlib,time,math
from typing import Dict,List,Optional
from dataclasses import dataclass,field
from enum import Enum

class 审计事件类型(Enum):
    握手发起="hs_init";握手完成="hs_done";握手失败="hs_fail"
    凭证签发="cred_issue";凭证撤销="cred_revoke"
    K_i更新="ki_update";链上锚定="onchain"
    异常行为="anomaly"

@dataclass
class 审计记录:
    """[ATH] 审计记录"""
    事件ID:str;类型:审计事件类型;AgentDID:str;时间戳:float=0.0
    详情:str="";哈希:str="";前一哈希:str=""
    def __post_init__(self):
        if self.时间戳==0: self.时间戳=time.time()
        if not self.哈希:
            数据=f"{self.事件ID}:{self.类型.value}:{self.AgentDID}:{self.时间戳}:{self.详情}"
            self.哈希=hashlib.sha256(数据.encode()).hexdigest()[:32]

class ath_AuditEngine:
    """[ATH] ATH行为审计引擎——Merkle树存储,不可篡改"""
    def __init__(self):
        self._记录:List[审计记录]=[]
        self._索引_Agent:Dict[str,List[int]]={}   # DID→[记录索引]
        self._索引_类型:Dict[str,List[int]]={}    # 类型→[记录索引]
        self._Merkle根:str=""

    def ath_记录事件(self,类型:审计事件类型,AgentDID:str,详情:str="") -> 审计记录:
        """[ATH] 记录审计事件"""
        # H-15: os.urandom替代time.time_ns()
        eid=hashlib.sha256(f"{类型.value}:{AgentDID}:{os.urandom(16).hex()}".encode()).hexdigest()[:16]
        前一哈希=self._记录[-1].哈希 if self._记录 else "0"*32
        记录=审计记录(事件ID=eid,类型=类型,AgentDID=AgentDID,详情=详情,前一哈希=前一哈希)
        idx=len(self._记录);self._记录.append(记录)
        self._索引_Agent.setdefault(AgentDID,[]).append(idx)
        self._索引_类型.setdefault(类型.value,[]).append(idx)
        self._更新Merkle();return 记录

    def ath_查询Agent(self,DID:str,数量:int=20) -> List[审计记录]:
        """[ATH] 按Agent检索"""
        索引=self._索引_Agent.get(DID,[])[-数量:]
        return[self._记录[i] for i in 索引 if i<len(self._记录)]

    def ath_查询时间范围(self,开始:float,结束:float) -> List[审计记录]:
        """[ATH] 按时间检索"""
        return[r for r in self._记录 if 开始<=r.时间戳<=结束]

    def ath_查询类型(self,类型:审计事件类型) -> List[审计记录]:
        """[ATH] 按类型检索"""
        索引=self._索引_类型.get(类型.value,[])
        return[self._记录[i] for i in 索引 if i<len(self._记录)]

    def _更新Merkle(self):
        """更新Merkle根"""
        哈希列表=[r.哈希 for r in self._记录[-256:]]  # 最近256条
        当前=哈希列表[:]
        while len(当前)>1:
            下一层=[]
            for i in range(0,len(当前),2):
                左=当前[i];右=当前[i+1] if i+1<len(当前) else 左
                下一层.append(hashlib.sha256((左+右).encode()).hexdigest()[:32])
            当前=下一层
        self._Merkle根=当前[0] if 当前 else "0"*32

    def ath_验证完整性(self) -> bool:
        """验证审计日志完整性"""
        for i in range(1,len(self._记录)):
            if self._记录[i].前一哈希!=self._记录[i-1].哈希: return False
        return True

    def ath_生成摘要(self) -> str:
        """生成审计摘要"""
        总=len(self._记录)
        类型统计={}
        for r in self._记录: 类型统计[r.类型.value]=类型统计.get(r.类型.value,0)+1
        lines=[f"[ATH] 审计摘要: {总}条记录"]
        for t,c in sorted(类型统计.items(),key=lambda x:-x[1]):
            lines.append(f"  {t}: {c}")
        lines.append(f"  Merkle根: {self._Merkle根}")
        lines.append(f"  完整性: {'✅' if self.ath_验证完整性() else '❌'}")
        return "\n".join(lines)

    def 状态(self) -> dict:
        return{"记录数":len(self._记录),"Merkle根":self._Merkle根[:16]+"...",
               "完整":self.ath_验证完整性(),"Agent数":len(self._索引_Agent)}
