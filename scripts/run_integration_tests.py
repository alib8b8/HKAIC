"""
HKC 第二步 — 一键运行所有集成测试
===================================
运行4大验证项:
  1. 跨链桥端到端验证
  2. ATH 9步握手真实执行
  3. 经济模型压力测试
  4. 异常场景测试
"""

import sys
import os
import time

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.integration.test_crosschain_e2e import run_tests as run_crosschain
from tests.integration.test_ath_handshake_e2e import run_tests as run_ath
from tests.integration.test_economy_stress import run_tests as run_economy
from tests.integration.test_fault_tolerance import run_tests as run_fault


def main():
    print("\n" + "🜏"*40)
    print("  HKC 第二步 — 全流程验证")
    print("  验证内容: 跨链桥 / ATH握手 / 经济压力 / 异常容错")
    print("🜏"*40)

    开始时间 = time.time()
    结果 = {}

    # 测试1: 跨链桥端到端
    print("\n\n" + "━"*60)
    print("  📦 验证1/4: 跨链桥端到端验证")
    print("━"*60)
    try:
        结果["跨链桥"] = run_crosschain()
    except Exception as e:
        print(f"  ❌ 跨链桥测试异常: {e}")
        结果["跨链桥"] = False

    # 测试2: ATH 9步握手
    print("\n\n" + "━"*60)
    print("  📦 验证2/4: ATH 9步握手真实执行")
    print("━"*60)
    try:
        结果["ATH"] = run_ath()
    except Exception as e:
        print(f"  ❌ ATH测试异常: {e}")
        结果["ATH"] = False

    # 测试3: 经济模型压力
    print("\n\n" + "━"*60)
    print("  📦 验证3/4: 经济模型压力测试")
    print("━"*60)
    try:
        结果["经济压力"] = run_economy()
    except Exception as e:
        print(f"  ❌ 经济压力测试异常: {e}")
        结果["经济压力"] = False

    # 测试4: 异常场景
    print("\n\n" + "━"*60)
    print("  📦 验证4/4: 异常场景测试")
    print("━"*60)
    try:
        结果["异常容错"] = run_fault()
    except Exception as e:
        print(f"  ❌ 异常测试异常: {e}")
        结果["异常容错"] = False

    # 汇总
    耗时 = time.time() - 开始时间
    全部通过 = all(结果.values())
    通过数 = sum(1 for v in 结果.values() if v)

    print("\n\n" + "🜏"*40)
    print("  HKC 第二步 — 全流程验证报告")
    print("🜏"*40)
    for 名称, 通过 in 结果.items():
        状态 = "✅ 通过" if 通过 else "❌ 失败"
        print(f"  {名称}: {状态}")
    print(f"\n  总耗时: {耗时:.2f}秒")
    print(f"  通过率: {通过数}/{len(结果)}")
    print(f"\n  最终结论: {'✅ 第二步全流程验证通过' if 全部通过 else '❌ 存在失败项'}")
    print("🜏"*40)

    return 全部通过


if __name__ == "__main__":
    成功 = main()
    sys.exit(0 if 成功 else 1)
