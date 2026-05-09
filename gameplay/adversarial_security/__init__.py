"""
HKC 对抗即安全模块 (adversarial_security/)
============================================
传统链：白帽审计一次就完了
HKC玩法：进化沙盒变成链上游戏——红队AI攻击、蓝队AI防御，
攻击成功赚HKAIC、防御成功也赚HKAIC。

子模块：
  - attack_scenarios: 攻击场景库
  - defense_strategies: 防御策略库
  - game_arena: 对战竞技场
  - reward_distributor: 奖励分配器
  - security_leaderboard: 安全排行榜
"""

from .attack_scenarios import 攻击场景库, 攻击类型, 攻击场景
from .defense_strategies import 防御策略库, 防御类型, 防御策略
from .game_arena import 对战竞技场, 对战模式, 对战结果
from .reward_distributor import 奖励分配器, 奖励类型
from .security_leaderboard import 安全排行榜, 称号等级
