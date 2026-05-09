"""
Hongkun AI Chain — 进化沙盒 (testnet.py)
==========================================
AI自动生成攻击场景,每轮攻击后评估防御,进化出更强攻击再测。
本地多节点模拟、网络拓扑自动构建、共识可视化。
"""
import hashlib,time,random,math
from typing import Dict,List,Optional,Tuple
from dataclasses import dataclass,field
from enum import Enum

class 攻击类型(Enum):
    女巫攻击="sybil";三明治攻击="sandwich";跨链套利="arb";DDoS="ddos"
    长程攻击="long_range";双花="double_spend"

class 拓扑类型(Enum):
    星形="star";环形="ring";全连接="mesh";小世界="small_world"

@dataclass
class 模拟节点:
    节点ID:str;地址:str;端口:int;质押:float=0;K_i:float=0;σ_i:float=0.0
    活跃:bool=True;恶意:bool=False;延迟毫秒:float=0.0

@dataclass
class 攻击场景:
    类型:攻击类型;攻击者:List[str];强度:float=1.0;轮次:int=0
    成功:bool=False;防御得分:float=0.0;细节:str=""

@dataclass
class 安全评估:
    轮次:int;攻击:攻击类型;防御得分:float;系统存活:bool;薄弱点:List[str]=field(default_factory=list)

class 网络拓扑构建器:
    """自动构建不同类型的网络拓扑"""
    def 构建(self,类型:拓扑类型,节点数:int) -> Dict[str,List[str]]:
        nodes=[f"node_{i}" for i in range(节点数)]
        邻接:Dict[str,List[str]]={n:[] for n in nodes}
        if 类型==拓扑类型.星形:
            for n in nodes[1:]: 邻接[nodes[0]].append(n);邻接[n].append(nodes[0])
        elif 类型==拓扑类型.环形:
            for i in range(节点数):
                邻接[nodes[i]].append(nodes[(i+1)%节点数])
                邻接[nodes[(i+1)%节点数]].append(nodes[i])
        elif 类型==拓扑类型.全连接:
            for i in range(节点数):
                for j in range(i+1,节点数):
                    邻接[nodes[i]].append(nodes[j]);邻接[nodes[j]].append(nodes[i])
        elif 类型==拓扑类型.小世界:
            for i in range(节点数):
                for d in range(1,3):
                    j=(i+d)%节点数;邻接[nodes[i]].append(nodes[j]);邻接[nodes[j]].append(nodes[i])
            for _ in range(节点数//2):
                a=random.choice(nodes);b=random.choice(nodes)
                if a!=b and b not in 邻接[a]: 邻接[a].append(b);邻接[b].append(a)
        return 邻接

class 压力测试器:
    """交易生成与压力测试"""
    def __init__(self): self._已发送:int=0;self._已确认:int=0;self._延迟列表:List[float]=[]
    def 生成交易(self,数量:int) -> List[dict]:
        txs=[]
        for i in range(数量):
            tx={"from":f"addr_{random.randint(1,100)}","to":f"addr_{random.randint(1,100)}",
                "amount":random.randint(1,1000)*10**16,"fee":random.randint(1,10)*10**13,
                "type":random.choice(["转账","质押","跨链","合约"])}
            txs.append(tx)
        self._已发送+=数量;return txs
    def 记录确认(self,延迟:float):
        self._已确认+=1;self._延迟列表.append(延迟)
    def 吞吐量(self) -> float: return self._已确认/max(sum(self._延迟列表),1)
    def 状态(self) -> dict:
        avg_delay=sum(self._延迟列表)/max(len(self._延迟列表),1)
        return{"已发送":self._已发送,"已确认":self._已确认,"平均延迟":f"{avg_delay:.1f}ms"}

class 测试网:
    """
    进化沙盒——AI自动生成攻击场景,评估防御,进化攻击再测

    流程:
      1. 启动多节点模拟网络
      2. 生成攻击场景
      3. 执行攻击,评估防御效果
      4. 根据防御得分进化出更强攻击
      5. 重复,产出安全评估报告
    """
    def __init__(self,节点数:int=5):
        self._节点数=节点数;self._节点:Dict[str,模拟节点]={}
        self._拓扑构建=网络拓扑构建器();self._压测=压力测试器()
        self._拓扑:Dict[str,List[str]]={};self._攻击历史:List[攻击场景]=[]
        self._评估历史:List[安全评估]=[];self._轮次:int=0
        self._薄弱点:List[str]=[]

    @property
    def 压力测试器(self): return self._压测

    def 初始化网络(self,拓扑:拓扑类型=拓扑类型.小世界):
        """自动构建网络拓扑,分配初始状态"""
        self._拓扑=self._拓扑构建.构建(拓扑,self._节点数)
        for nid in self._拓扑:
            self._节点[nid]=模拟节点(节点ID=nid,地址="127.0.0.1",
                端口=8800+int(nid.split("_")[1]),
                质押=random.uniform(1000,50000),K_i=random.uniform(10,100),
                σ_i=random.uniform(0.1,0.8),延迟毫秒=random.uniform(1,50))

    def 生成攻击场景(self,强度:float=1.0) -> 攻击场景:
        """AI生成攻击场景——每轮进化更强"""
        类型=random.choice(list(攻击类型))
        攻击者数=max(1,int(self._节点数*0.3*强度))
        候选=list(self._节点.keys());random.shuffle(候选)
        攻击者=候选[:攻击者数]
        for a in 攻击者: self._节点[a].恶意=True
        return 攻击场景(类型=类型,攻击者=攻击者,强度=强度,轮次=self._轮次)

    def 执行攻击(self,场景:攻击场景) -> 安全评估:
        """执行攻击并评估防御效果"""
        self._轮次+=1;防御得分=0.0;存活=True;薄弱=[]
        if 场景.类型==攻击类型.女巫攻击:
            伪造节点数=int(self._节点数*场景.强度)
            诚实σ=sum(n.σ_i for n in self._节点.values() if not n.恶意)
            伪造σ=伪造节点数*0.01  # 伪造节点σ极低
            防御得分=诚实σ/max(诚实σ+伪造σ,1e-6)
            if 防御得分<0.5: 薄弱.append("协同净化阈值过高")
        elif 场景.类型==攻击类型.DDoS:
            在线率=sum(1 for n in self._节点.values() if n.活跃)/max(len(self._节点),1)
            防御得分=在线率
            if 在线率<0.6: 薄弱.append("DDoS防御不足");存活=在线率>0.3
        elif 场景.类型==攻击类型.双花:
            双花检测率=0.95*场景.强度/(1+场景.强度)
            防御得分=双花检测率
            if 双花检测率<0.8: 薄弱.append("双花检测需加强")
        else:
            防御得分=random.uniform(0.6,0.95)
        场景.成功=防御得分<0.5;场景.防御得分=防御得分
        self._攻击历史.append(场景)
        评估=安全评估(轮次=self._轮次,攻击=场景.类型,防御得分=防御得分,系统存活=存活,薄弱点=薄弱)
        self._评估历史.append(评估);self._薄弱点.extend(薄弱)
        return 评估

    def 进化攻击(self) -> 攻击场景:
        """根据防御效果进化出更强攻击"""
        if not self._攻击历史: return self.生成攻击场景()
        最低防御=min(s.防御得分 for s in self._攻击历史)
        新强度=1.0+(1.0-最低防御)*0.5  # 防御越弱,攻击进化越快
        return self.生成攻击场景(min(新强度,3.0))

    def 运行进化沙盒(self,轮数:int=10) -> List[安全评估]:
        """运行多轮进化攻击测试"""
        results=[]
        for _ in range(轮数):
            if self._攻击历史 and self._攻击历史[-1].防御得分>0.7:
                场景=self.进化攻击()
            else:
                场景=self.生成攻击场景()
            评估=self.执行攻击(场景);results.append(评估)
        return results

    def 安全评估报告(self) -> str:
        """产出安全评估报告"""
        lines=["="*50,"  HKC 安全评估报告","="*50]
        lines.append(f"  总轮次: {self._轮次}")
        lines.append(f"  系统存活率: {sum(1 for e in self._评估历史 if e.系统存活)/max(len(self._评估历史),1):.1%}")
        avg_def=sum(e.防御得分 for e in self._评估历史)/max(len(self._评估历史),1)
        lines.append(f"  平均防御得分: {avg_def:.2f}")
        if self._薄弱点:
            from collections import Counter
            cnt=Counter(self._薄弱点)
            lines.append("  薄弱点:")
            for bp,c in cnt.most_common(5): lines.append(f"    [{c}次] {bp}")
        lines.append("="*50)
        return "\n".join(lines)

    def 共识可视化(self) -> str:
        """ASCII可视化当前共识状态"""
        lines=["  ┌─ HKC 共识状态 ─────────────┐"]
        for nid,n in self._节点.items():
            bar="█"*int(n.K_i/10)+"░"*(10-int(n.K_i/10))
            标记="⚠️" if n.恶意 else "✅"
            lines.append(f"  │ {标记} {nid}: K={n.K_i:.0f} [{bar}] σ={n.σ_i:.2f}")
        lines.append("  └──────────────────────────┘")
        return "\n".join(lines)

    def 状态(self) -> dict:
        return{"节点":len(self._节点),"轮次":self._轮次,"攻击历史":len(self._攻击历史),
               "薄弱点":len(set(self._薄弱点)),"压测":self._压测.状态()}

if __name__=="__main__":
    print("  HKC 进化沙盒 Demo")
    tn=测试网(5);tn.初始化网络()
    print(tn.共识可视化())
    results=tn.运行进化沙盒(5)
    for r in results: print(f"  轮{r.轮次}: {r.攻击.value} 防御={r.防御得分:.2f} {'✅' if r.系统存活 else '❌'}")
    print(tn.安全评估报告())
