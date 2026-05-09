"""
HKC可视化模块测试 (test_visualization.py)
==========================================
测试每个可视化模块能正确生成HTML文件。
测试HTML文件包含有效的DOCTYPE、CSS、JS。
测试图表渲染函数能处理空数据/单点数据/大数据集。
测试报告生成器能整合所有面板。
"""

import os
import sys
import unittest
import tempfile
import re

# 确保项目路径在sys.path中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHTMLTemplate(unittest.TestCase):
    """测试HTML模板引擎"""

    def test_generate_head(self):
        """测试HTML头部生成"""
        from visualization.html_template import generate_head
        head = generate_head("测试页面")
        self.assertIn("<!DOCTYPE html>", head)
        self.assertIn("<title>", head)
        self.assertIn("测试页面", head)
        self.assertIn("<style>", head)
        self.assertIn("#FFD700", head)  # 品牌金色
        self.assertIn("#0A1628", head)  # 品牌深蓝

    def test_generate_nav(self):
        """测试导航栏生成"""
        from visualization.html_template import generate_nav
        nav = generate_nav("consensus")
        self.assertIn("HKC", nav)
        self.assertIn("共识仪表盘", nav)
        self.assertIn("active", nav)

    def test_generate_footer(self):
        """测试页脚生成"""
        from visualization.html_template import generate_footer
        footer = generate_footer()
        self.assertIn("Hongkun AI Chain", footer)
        self.assertIn("v4.0.0", footer)

    def test_wrap_html(self):
        """测试完整HTML包装"""
        from visualization.html_template import wrap_html
        html = wrap_html("测试", "consensus", "<div>内容</div>")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("</html>", html)
        self.assertIn("<body>", html)
        self.assertIn("内容", html)
        self.assertIn("<script>", html)

    def test_save_html(self):
        """测试HTML保存"""
        from visualization.html_template import save_html
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            path = f.name
        try:
            result = save_html("<html>test</html>", path)
            self.assertEqual(result, path)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, "<html>test</html>")
        finally:
            os.unlink(path)

    def test_escape_js(self):
        """测试JS转义"""
        from visualization.html_template import escape_js
        self.assertEqual(escape_js([1, 2, 3]), "[1, 2, 3]")
        self.assertIn("hello", escape_js("hello"))


class TestConsensusDashboard(unittest.TestCase):
    """测试PoEI共识仪表盘"""

    def test_generate_with_mock_data(self):
        """测试模拟数据生成仪表盘"""
        from visualization.consensus_dashboard import generate_consensus_dashboard
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_consensus_dashboard(output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("PoEI", content)
            self.assertIn("<canvas", content)
        finally:
            os.unlink(path)

    def test_generate_with_custom_data(self):
        """测试自定义数据生成"""
        from visualization.consensus_dashboard import generate_consensus_dashboard
        nodes = [
            {"name": "Test-01", "K_i": 50, "S_i": 100000,
             "sigma_i": 0.5, "E_i": 600, "tier": "涌银", "color": "#C0C0C0"}
        ]
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_consensus_dashboard(nodes=nodes, output_path=path)
            self.assertTrue(os.path.exists(result))
        finally:
            os.unlink(path)

    def test_empty_data(self):
        """测试空数据"""
        from visualization.consensus_dashboard import generate_consensus_dashboard
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_consensus_dashboard(nodes=[], epochs=[], output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<!DOCTYPE html>", content)
        finally:
            os.unlink(path)


class TestEconomyCharts(unittest.TestCase):
    """测试经济仿真图表"""

    def test_generate_default(self):
        """测试默认生成"""
        from visualization.economy_charts import generate_economy_charts
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_economy_charts(output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("HKAIC", content)
        finally:
            os.unlink(path)

    def test_single_point_data(self):
        """测试单点数据"""
        from visualization.economy_charts import generate_economy_charts
        data = {
            "days": [1], "circulating": [5000000], "staking": [3000000],
            "burned": [0], "price": [0.5], "apy": [10.0],
            "gas": [1.0], "inflation": [0.5], "users": [1000]
        }
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_economy_charts(economy_data=data, output_path=path)
            self.assertTrue(os.path.exists(result))
        finally:
            os.unlink(path)


class TestBridgeMonitor(unittest.TestCase):
    """测试跨链桥监控面板"""

    def test_generate_default(self):
        """测试默认生成"""
        from visualization.bridge_monitor import generate_bridge_monitor
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_bridge_monitor(output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("ETB", content)
            self.assertIn("Solver", content)
        finally:
            os.unlink(path)


class TestNetworkTopology(unittest.TestCase):
    """测试P2P网络拓扑图"""

    def test_generate_default(self):
        """测试默认生成"""
        from visualization.network_topology import generate_network_topology
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_network_topology(output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("P2P", content)
        finally:
            os.unlink(path)


class TestWalletPanel(unittest.TestCase):
    """测试涌信钱包面板"""

    def test_generate_default(self):
        """测试默认生成"""
        from visualization.wallet_panel import generate_wallet_panel
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_wallet_panel(output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("涌信", content)
            self.assertIn("信用分", content)
        finally:
            os.unlink(path)


class TestGuardianDashboard(unittest.TestCase):
    """测试AI守护者大屏"""

    def test_generate_default(self):
        """测试默认生成"""
        from visualization.guardian_dashboard import generate_guardian_dashboard
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_guardian_dashboard(output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("守护者", content)
        finally:
            os.unlink(path)


class TestBlockExplorerUI(unittest.TestCase):
    """测试区块浏览器UI"""

    def test_generate_default(self):
        """测试默认生成"""
        from visualization.block_explorer_ui import generate_block_explorer_ui
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_block_explorer_ui(output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("区块浏览器", content)
            self.assertIn("searchInput", content)
        finally:
            os.unlink(path)


class TestReportGenerator(unittest.TestCase):
    """测试综合报告生成器"""

    def test_generate_full_report(self):
        """测试生成完整报告"""
        from visualization.report_generator import generate_report
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_report(output_path=path)
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # 检查包含所有面板
            self.assertIn("consensus", content)
            self.assertIn("economy", content)
            self.assertIn("bridge", content)
            self.assertIn("network", content)
            self.assertIn("wallet", content)
            self.assertIn("guardian", content)
            self.assertIn("explorer", content)
        finally:
            os.unlink(path)

    def test_generate_partial_report(self):
        """测试生成部分面板报告"""
        from visualization.report_generator import generate_report
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = generate_report(
                include_panels=["consensus", "economy"],
                output_path=path
            )
            self.assertTrue(os.path.exists(result))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("consensus", content)
            self.assertIn("economy", content)
        finally:
            os.unlink(path)

    def test_report_valid_html_structure(self):
        """测试报告HTML结构完整性"""
        from visualization.report_generator import generate_report
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            generate_report(output_path=path)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(content.startswith("<!DOCTYPE html>"))
            self.assertIn("</html>", content)
            self.assertIn("<style>", content)
            self.assertIn("</style>", content)
            self.assertIn("<script>", content)
            self.assertIn("</script>", content)
        finally:
            os.unlink(path)


class TestHTMLValidity(unittest.TestCase):
    """测试所有模块生成的HTML基本有效性"""

    def _check_html(self, module_name, generate_fn, **kwargs):
        """通用HTML有效性检查"""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            generate_fn(output_path=path, **kwargs)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # DOCTYPE
            self.assertTrue(content.startswith("<!DOCTYPE html>"),
                f"{module_name}: 缺少DOCTYPE")
            # 闭合标签
            self.assertIn("</html>", content, f"{module_name}: 缺少</html>")
            # CSS存在
            self.assertIn("<style>", content, f"{module_name}: 缺少<style>")
            # JS存在
            self.assertIn("<script>", content, f"{module_name}: 缺少<script>")
            # Canvas
            self.assertIn("<canvas", content, f"{module_name}: 缺少<canvas>")
            # 中文UI
            self.assertTrue(len(re.findall(r"[一-鿿]", content)) > 10,
                f"{module_name}: 中文UI文案不足")
        finally:
            os.unlink(path)

    def test_consensus_html(self):
        from visualization.consensus_dashboard import generate_consensus_dashboard
        self._check_html("consensus", generate_consensus_dashboard)

    def test_economy_html(self):
        from visualization.economy_charts import generate_economy_charts
        self._check_html("economy", generate_economy_charts)

    def test_bridge_html(self):
        from visualization.bridge_monitor import generate_bridge_monitor
        self._check_html("bridge", generate_bridge_monitor)

    def test_network_html(self):
        from visualization.network_topology import generate_network_topology
        self._check_html("network", generate_network_topology)

    def test_wallet_html(self):
        from visualization.wallet_panel import generate_wallet_panel
        self._check_html("wallet", generate_wallet_panel)

    def test_guardian_html(self):
        from visualization.guardian_dashboard import generate_guardian_dashboard
        self._check_html("guardian", generate_guardian_dashboard)

    def test_explorer_html(self):
        from visualization.block_explorer_ui import generate_block_explorer_ui
        self._check_html("explorer", generate_block_explorer_ui)


if __name__ == "__main__":
    unittest.main(verbosity=2)
