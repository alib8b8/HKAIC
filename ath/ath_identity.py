"""
Hongkun AI Chain — ATH身份管理 (ath_identity.py)
==================================================
DID去中心化身份,与PoEI的K_i绑定:验证身份后才能积累K_i。
[ATH] 标签标识ATH相关事件
"""
import hashlib,time,math
from typing import Dict,List,Optional
from dataclasses import dataclass,field
from enum import Enum

class 凭证状态(Enum):
    有效="valid";已撤销="revoked";已过期="expired"

@dataclass
class DID凭证:
    """[ATH] DID凭证"""
    凭证ID:str;持有者DID:str;签发者DID:str;类型:str
    声明:Dict[str,str]=field(default_factory=dict)
    签发时间:float=0.0;过期时间:float=0.0;状态:凭证状态=凭证状态.有效
    签名:str=""
    def __post_init__(self):
        if self.签发时间==0: self.签发时间=time.time()
        if self.过期时间==0: self.过期时间=self.签发时间+86400*90
        if not self.签名:
            self.签名=hashlib.sha256(f"{self.持有者DID}:{self.类型}:{self.签发时间}".encode()).hexdigest()[:32]
    def 是否有效(self) -> bool:
        return self.状态==凭证状态.有效 and time.time()<self.过期时间

class ath_IdentityManager:
    """[ATH] ATH身份管理器——DID注册/签发/撤销/过期,与PoEI K_i绑定"""
    def __init__(self):
        self._身份:Dict[str,dict]={}     # DID→{凭证列表, K_i绑定, 信任评分}
        self._凭证:Dict[str,DID凭证]={}
        self._K_i绑定:Dict[str,float]={}  # DID→K_i值

    def ath_注册身份(self,DID:str,类型:str="agent") -> bool:
        """[ATH] 注册DID身份"""
        if DID in self._身份: return False
        self._身份[DID]={"类型":类型,"注册时间":time.time(),"信任评分":50.0,"凭证数":0}
        self._K_i绑定[DID]=0.0;return True

    def ath_签发凭证(self,持有者DID:str,签发者DID:str,类型:str,声明:Dict[str,str]=None) -> Optional[DID凭证]:
        """[ATH] 签发DID凭证"""
        if 持有者DID not in self._身份 or 签发者DID not in self._身份: return None
        # H-16: os.urandom替代time.time_ns()
        cid=hashlib.sha256(f"{持有者DID}:{类型}:{os.urandom(16).hex()}".encode()).hexdigest()[:16]
        凭证=DID凭证(凭证ID=cid,持有者DID=持有者DID,签发者DID=签发者DID,类型=类型,声明=声明 or {})
        self._凭证[cid]=凭证;self._身份[持有者DID]["凭证数"]+=1
        return 凭证

    def ath_验证身份(self,DID:str) -> bool:
        """[ATH] 验证身份是否有效——与PoEI K_i绑定"""
        if DID not in self._身份: return False
        身份=self._身份[DID]
        # 至少有一个有效凭证
        有效凭证=[c for c in self._凭证.values() if c.持有者DID==DID and c.是否有效()]
        return len(有效凭证)>0

    def ath_撤销凭证(self,凭证ID:str) -> bool:
        """[ATH] 撤销凭证"""
        凭证=self._凭证.get(凭证ID)
        if not 凭证: return False
        凭证.状态=凭证状态.已撤销;return True

    def ath_更新K_i(self,DID:str,增量:float) -> float:
        """[ATH] 更新与PoEI绑定的K_i——只有验证身份后才能积累"""
        if not self.ath_验证身份(DID): return 0.0
        self._K_i绑定[DID]=self._K_i绑定.get(DID,0)+增量;return self._K_i绑定[DID]

    def ath_获取K_i(self,DID:str) -> float:
        """[ATH] 获取绑定K_i"""
        return self._K_i绑定.get(DID,0.0)

    def 状态(self) -> dict:
        return{"注册身份":len(self._身份),"有效凭证":sum(1 for c in self._凭证.values() if c.是否有效()),
               "K_i绑定用户":sum(1 for v in self._K_i绑定.values() if v>0)}
