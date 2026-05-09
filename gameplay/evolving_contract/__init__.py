"""
HKC 自进化智能合约模块 (evolving_contract/)
===============================================
传统链：合约部署后写死
HKC玩法：合约根据链上AI观测结果自适应演化。
合约有"基因"，会"变异"，好的变异留下，坏的变异淘汰。

子模块：
  - contract_genome: 合约基因组
  - evolution_engine: 进化引擎
  - fitness_evaluator: 适应性评估器
  - mutation_sandbox: 变异沙盒
  - evolution_governance: 进化治理
"""

from .contract_genome import 合约基因组, 基因座, 基因型
from .evolution_engine import 进化引擎, 环境状态, 进化记录
from .fitness_evaluator import 适应性评估器, 评估维度, 评估结果
from .mutation_sandbox import 变异沙盒, 沙盒结果
from .evolution_governance import 进化治理, 提议状态, 进化提议
