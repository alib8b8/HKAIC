"""
Hongkun AI Chain — PoEI共识引擎 (consensus_engine.py)
======================================================
基于白皮书PoEI公式的完整共识流程,带自适应参数。

核心:
  E_i = (K_i · √S_i)^α · σ_i^β · Φ(Λ_i)

自适应:
  - α/β根据全网协同质量自动调整
  - 协同质量高→β升高放大涌现激励
  - Slashing惩罚自适应:初犯轻罚+警告,累犯指数加重
  - epoch管理、涌现分数计算、出块者选举、视图切换与超时处理
"""
import hashlib,time,math,random
from typing import Dict,List,Optional,Set,Tuple
from dataclasses import dataclass,field
from enum import Enum

class Epoch阶段(Enum):
    提案="propose";预投票="prevote";预提交="precommit";提交="commit"

@dataclass
class Epoch信息:
    """Epoch信息"""
    编号:int=0;开始时间:float=0.0;结束时间:float=0.0
    阶段:Epoch阶段=Epoch阶段.提案;出块者:str=""
    种子:str="";超时计数:int=0

class Epoch管理器:
    """Epoch生命周期管理"""
    def __init__(self,epoch时长:float=60.0):
        self._时长=epoch时长;self._当前=Epoch信息()
        self._历史:List[Epoch信息]=[]
    @property
    def 当前epoch(self) -> Epoch信息: return self._当前
    def 开始新epoch(self,种子:str="") -> Epoch信息:
        self._历史.append(self._当前)
        # L-06修复: epoch种子使用os.urandom不可预测随机源
        import os as _os
        安全种子=种子 or hashlib.sha256(_os.urandom(32)).hexdigest()[:16]
        self._当前=Epoch信息(编号=self._当前.编号+1,开始时间=time.time(),
            结束时间=time.time()+self._时长,阶段=Epoch阶段.提案,种子=安全种子)
        return self._当前
    def 推进阶段(self) -> Optional[Epoch阶段]:
        阶段序列=[Epoch阶段.提案,Epoch阶段.预投票,Epoch阶段.预提交,Epoch阶段.提交]
        当前索引=阶段序列.index(self._当前.阶段) if self._当前.阶段 in 阶段序列 else -1
        if 当前索引<len(阶段序列)-1:
            self._当前.阶段=阶段序列[当前索引+1];return self._当前.阶段
        return None
    def 是否超时(self) -> bool: return time.time()>self._当前.结束时间
    def 处理超时(self) -> str:
        self._当前.超时计数+=1
        if self._当前.超时计数>=3: return "视图切换"
        self._当前.结束时间=time.time()+self._时长;return "延长epoch"

class 出块者选举器:
    """基于PoEI公式的出块者选举
    H(epoch_seed ∥ addr_i ∥ E_i) < T · E_i / ΣE
    M-04修复: K=0节点不得参与出块选举"""
    def 选举(self,候选:List[str],涌现分数:Dict[str,float],epoch种子:str,
             知识贡献:Dict[str,float]=None) -> Optional[str]:
        if not 候选: return None
        # M-04: K=0节点硬检查，排除零知识贡献的节点
        if 知识贡献:
            候选=[n for n in 候选 if 知识贡献.get(n,0)>0]
        if not 候选: return None
        总E=sum(涌现分数.get(n,0) for n in 候选)
        if 总E<=0: return None
        T=2**256-1;最佳=None;最小哈希=float('inf')
        for n in 候选:
            E_i=涌现分数.get(n,0)
            if E_i<=0: continue
            输入=f"{epoch种子}|{n}|{E_i:.16f}"
            哈希值=int(hashlib.sha256(输入.encode()).hexdigest(),16)
            节点目标=int(T*E_i/总E)
            if 哈希值<节点目标 and 哈希值<最小哈希:
                最小哈希=哈希值;最佳=n
        return 最佳

class PoEI共识引擎:
    """
    PoEI共识执行引擎——自适应参数版

    白皮书公式:
      E_i = (K_i · √S_i)^α · σ_i^β · Φ(Λ_i)
      σ_i = Σ_{j∈N(i)} C_ij · √(K_i·K_j) / |N(i)|
      Φ(Λ) = max(Λ, Λ_min)

    自适应:
      协同质量 = 平均σ_i / 最大理论σ_i
      协同质量高→β自动升高(放大涌现)
      协同质量低→β降低(回归基础安全)

    Slashing自适应:
      初犯: 轻罚(5%)+警告
      累犯: 指数加重 5% × 2^(n-1), n为违规次数
    """
    # 基础参数
    ALPHA=0.6;BETA=1.2;MIN_LIVENESS=0.3;SLASH_BASE=0.05
    # 自适应范围
    ALPHA_MIN=0.4;ALPHA_MAX=0.8;BETA_MIN=0.8;BETA_MAX=2.0
    # 协同质量阈值
    协同质量高阈值=0.5;协同质量低阈值=0.2

    def __init__(self):
        self._K:Dict[str,float]={};self._S:Dict[str,float]={}
        self._Λ:Dict[str,float]={};self._最后活跃:Dict[str,float]={}
        self._协同图:Dict[str,Dict[str,float]]={};self._E缓存:Dict[str,float]={}
        self._总E:float=0.0;self._违规记录:Dict[str,int]={}
        self._epoch_mgr=Epoch管理器();self._选举器=出块者选举器()

    # ---- 状态更新 ----
    def 更新知识贡献(self,节点:str,值:float):
        旧=self._K.get(节点,0);衰减=self._时间衰减(节点)
        self._K[节点]=旧*衰减+值;self._更新活跃(节点)
    def 更新质押(self,节点:str,量:float):
        self._S[节点]=量;self._更新活跃(节点)
    def 记录协同(self,A:str,B:str,强度:float):
        self._协同图.setdefault(A,{})[B]=强度
        self._协同图.setdefault(B,{})[A]=强度
    def _更新活跃(self,节点:str):
        self._最后活跃[节点]=time.time();self._Λ[节点]=1.0
    def _时间衰减(self,节点:str) -> float:
        t=self._最后活跃.get(节点,0)
        if t==0: return 1.0
        return math.pow(0.5,(time.time()-t)/2592000)  # 30天半衰期

    # ---- 涌现分数计算(严格对应白皮书公式) ----
    def 计算涌现分数(self,节点:str) -> float:
        """E_i = (K_i · √S_i)^α · σ_i^β · Φ(Λ_i)"""
        K=self._K.get(节点,0);S=self._S.get(节点,0)
        Λ=self._Λ.get(节点,0);σ=self.计算协同因子(节点)
        S_prime=math.sqrt(max(S,0))
        基础=math.pow(K*S_prime+1e-12,self.ALPHA)
        协同=math.pow(σ+1e-12,self.BETA)
        活跃度=max(Λ,self.MIN_LIVENESS)
        E=基础*协同*活跃度;self._E缓存[节点]=E;return E

    def 计算协同因子(self,节点:str) -> float:
        """σ_i = Σ C_ij·√(K_i·K_j) / |N(i)|"""
        协同=self._协同图.get(节点,{})
        if not 协同: return 0.0
        K_i=self._K.get(节点,1.0);加权=0.0
        for 邻居,C_ij in 协同.items():
            K_j=self._K.get(邻居,1.0);几何=math.sqrt(max(K_i*K_j,0));加权+=C_ij*几何
        return 加权/len(协同)

    def 计算总涌现分数(self) -> float:
        总=0.0
        for n in self._S: 总+=self.计算涌现分数(n)
        self._总E=总;return 总

    # ---- 出块者选举 ----
    def 判定出块权(self,候选:List[str],epoch种子:str="") -> Optional[str]:
        if not 候选: return None
        # L-06修复: epoch种子使用os.urandom不可预测随机源
        import os as _os
        if not epoch种子: epoch种子=hashlib.sha256(_os.urandom(32)).hexdigest()
        涌现分数={n:self.计算涌现分数(n) for n in 候选}
        # M-04: 传递知识贡献信息给选举器
        return self._选举器.选举(候选,涌现分数,epoch种子,self._K)

    # ---- 自适应参数调整 ----
    def 自适应调整(self):
        """根据全网协同质量自动调整α/β"""
        所有σ=[self.计算协同因子(n) for n in self._S if n in self._协同图]
        if not 所有σ: return
        平均σ=sum(所有σ)/len(所有σ);最大理论σ=max(所有σ) if 所有σ else 1.0
        协同质量=平均σ/max(最大理论σ,1e-6)
        if 协同质量>self.协同质量高阈值:
            self.BETA=min(self.BETA_MAX,self.BETA*1.05)  # 放大涌现激励
            self.ALPHA=max(self.ALPHA_MIN,self.ALPHA*0.98)
        elif 协同质量<self.协同质量低阈值:
            self.BETA=max(self.BETA_MIN,self.BETA*0.95)  # 回归基础安全
            self.ALPHA=min(self.ALPHA_MAX,self.ALPHA*1.02)

    # ---- Slashing自适应 ----
    def 惩罚作恶(self,节点:str,原因:str="") -> float:
        """初犯轻罚+警告,累犯指数加重: SLASH_BASE × 2^(n-1)"""
        质押=self._S.get(节点,0);次数=self._违规记录.get(节点,0)+1
        self._违规记录[节点]=次数
        惩罚率=self.SLASH_BASE*math.pow(2,min(次数-1,5))  # 最高32倍
        惩罚率=min(惩罚率,1.0)  # 不超过100%
        惩罚额=质押*惩罚率
        self._S[节点]=质押-惩罚额;self._K[节点]=0
        for 邻居 in list(self._协同图.get(节点,{}).keys()):
            if 邻居 in self._协同图: self._协同图[邻居].pop(节点,None)
        self._协同图.pop(节点,None)
        return 惩罚额

    # ---- Epoch管理 ----
    def 开始新epoch(self) -> Epoch信息:
        self.自适应调整();return self._epoch_mgr.开始新epoch()
    def 推进共识(self) -> Optional[str]:
        """推进共识阶段,返回出块者(提交阶段)或None"""
        下一阶段=self._epoch_mgr.推进阶段()
        if 下一阶段==Epoch阶段.提交:
            候选=list(self._S.keys())
            出块者=self.判定出块权(候选,self._epoch_mgr.当前epoch.种子)
            if 出块者: self._epoch_mgr.当前epoch.出块者=出块者
            return 出块者
        if self._epoch_mgr.是否超时():
            处理=self._epoch_mgr.处理超时()
            return f"超时:{处理}"
        return None

    def 节点报告(self,节点:str) -> dict:
        E=self.计算涌现分数(节点);σ=self.计算协同因子(节点)
        K=self._K.get(节点,0);S=self._S.get(节点,0)
        总E=self._总E or self.计算总涌现分数()
        概率=E/max(总E,1e-6)
        return{"地址":节点,"K":f"{K:.4f}","S":f"{S:.2f}","σ":f"{σ:.6f}",
               "E":f"{E:.8f}","出块概率":f"{概率:.4%}","违规":self._违规记录.get(节点,0)}

    def 网络摘要(self) -> dict:
        总E=self._总E or self.计算总涌现分数()
        return{"验证者":len(self._S),"总E":f"{总E:.8f}","α":f"{self.ALPHA:.4f}",
               "β":f"{self.BETA:.4f}","协同边":sum(len(v) for v in self._协同图.values())//2,
               "epoch":self._epoch_mgr.当前epoch.编号}

if __name__=="__main__":
    print("  HKC PoEI共识引擎 Demo")
    engine=PoEI共识引擎()
    for name,stk,k in[("Alice",10000,85),("Bob",5000,60),("Carol",8000,75),("Dave",3000,40)]:
        engine.更新质押(name,stk);engine.更新知识贡献(name,k)
    for a,b,c in[("Alice","Bob",0.8),("Alice","Carol",0.6),("Bob","Carol",0.7)]:
        engine.记录协同(a,b,c)
    engine.计算总涌现分数()
    for n in["Alice","Bob","Carol","Dave"]: print(f"  {engine.节点报告(n)}")
    for i in range(3):
        ep=engine.开始新epoch();winner=engine.判定出块权(["Alice","Bob","Carol","Dave"],ep.种子)
        print(f"  Epoch{ep.编号}: 出块者={winner}")
    engine.惩罚作恶("Dave","双花");print(f"  Dave被Slashing: {engine.节点报告('Dave')}")
    engine.自适应调整();print(f"  自适应后: α={engine.ALPHA:.4f} β={engine.BETA:.4f}")
