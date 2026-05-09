"""
EVM钱包连接配置 (evm_config.py)
=================================
HKC主网/测试网配置、MetaMask"添加网络"JSON。
"""

import json
from typing import Dict, Any

# ============================================================
# HKC主网配置
# ============================================================
HKC主网配置 = {
    "链名称": "Hongkun AI Chain Mainnet",
    "链代号": "HKC",
    "chainId": 9901,
    "RPC_URL": "https://rpc.hongkunai.com",
    "区块浏览器URL": "https://explorer.hongkunai.com",
    "货币符号": "HKAIC",
    "货币精度": 16,
    "最小单位": "hongkun",
    "1_HKAIC_等于_鸿坤": 10 ** 16,
    "图标URL": "https://hongkunai.com/logo.png",
}

# ============================================================
# HKC测试网配置
# ============================================================
HKC测试网配置 = {
    "链名称": "Hongkun AI Chain Testnet",
    "链代号": "HKC-Test",
    "chainId": 9902,
    "RPC_URL": "https://rpc-testnet.hongkunai.com",
    "区块浏览器URL": "https://explorer-testnet.hongkunai.com",
    "货币符号": "tHKAIC",
    "货币精度": 16,
    "最小单位": "hongkun",
    "1_tHKAIC_等于_鸿坤": 10 ** 16,
    "图标URL": "https://hongkunai.com/logo.png",
}


# ============================================================
# MetaMask "添加网络" 配置JSON
# ============================================================
def MetaMask主网配置() -> Dict[str, Any]:
    """
    生成MetaMask "添加网络" 的配置JSON
    用于wallet_addEthereumChain接口
    """
    return {
        "chainId": "0x" + hex(HKC主网配置["chainId"])[2:],
        "chainName": HKC主网配置["链名称"],
        "nativeCurrency": {
            "name": HKC主网配置["货币符号"],
            "symbol": HKC主网配置["货币符号"],
            "decimals": HKC主网配置["货币精度"],
        },
        "rpcUrls": [HKC主网配置["RPC_URL"]],
        "blockExplorerUrls": [HKC主网配置["区块浏览器URL"]],
        "iconUrls": [HKC主网配置["图标URL"]],
    }


def MetaMask测试网配置() -> Dict[str, Any]:
    """生成MetaMask测试网配置JSON"""
    return {
        "chainId": "0x" + hex(HKC测试网配置["chainId"])[2:],
        "chainName": HKC测试网配置["链名称"],
        "nativeCurrency": {
            "name": HKC测试网配置["货币符号"],
            "symbol": HKC测试网配置["货币符号"],
            "decimals": HKC测试网配置["货币精度"],
        },
        "rpcUrls": [HKC测试网配置["RPC_URL"]],
        "blockExplorerUrls": [HKC测试网配置["区块浏览器URL"]],
        "iconUrls": [HKC测试网配置["图标URL"]],
    }


# ============================================================
# SafePal / imToken / Trust Wallet 通用配置
# ============================================================
def 通用EVM钱包配置(网络: str = "主网") -> Dict[str, Any]:
    """
    生成通用EVM钱包添加网络配置
    适用于SafePal、imToken、Trust Wallet等
    """
    if 网络 == "主网":
        cfg = HKC主网配置
    else:
        cfg = HKC测试网配置

    return {
        "networkName": cfg["链名称"],
        "rpcUrl": cfg["RPC_URL"],
        "chainId": cfg["chainId"],
        "symbol": cfg["货币符号"],
        "blockExplorerUrl": cfg["区块浏览器URL"],
        "decimals": cfg["货币精度"],
    }


def 获取网络配置(chain_id: int) -> Dict[str, Any]:
    """根据chainId获取网络配置"""
    if chain_id == HKC主网配置["chainId"]:
        return HKC主网配置
    elif chain_id == HKC测试网配置["chainId"]:
        return HKC测试网配置
    else:
        raise ValueError(f"未知的chainId: {chain_id}")


def 所有钱包配置JSON(格式化: bool = True) -> str:
    """
    输出所有钱包配置的JSON字符串
    包含MetaMask主网/测试网配置
    """
    配置 = {
        "Hongkun AI Chain": {
            "MetaMask_主网": MetaMask主网配置(),
            "MetaMask_测试网": MetaMask测试网配置(),
            "通用EVM_主网": 通用EVM钱包配置("主网"),
            "通用EVM_测试网": 通用EVM钱包配置("测试网"),
        }
    }
    缩进 = 2 if 格式化 else None
    return json.dumps(配置, indent=缩进, ensure_ascii=False)


if __name__ == "__main__":
    print("=" * 60)
    print("  HKC EVM钱包连接配置")
    print("=" * 60)
    print(f"\n主网 chainId: {HKC主网配置['chainId']} (0x{HKC主网配置['chainId']:x})")
    print(f"测试网 chainId: {HKC测试网配置['chainId']} (0x{HKC测试网配置['chainId']:x})")
    print(f"\nMetaMask主网配置:")
    print(json.dumps(MetaMask主网配置(), indent=2, ensure_ascii=False))
    print(f"\n全部配置JSON:")
    print(所有钱包配置JSON()[:500] + "...")
    print("\n✅ 配置模块Demo完成！")
