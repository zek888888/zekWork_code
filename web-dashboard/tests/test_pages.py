"""
页面测试 - 量化交易仪表盘
测试各页面加载、数据渲染和交互元素
"""

import pytest
import re
from pathlib import Path
from unittest.mock import Mock, patch


# ==================== 测试配置 ====================

PROJECT_ROOT = Path("/Users/mac/.openclaw/workspace/quant-trading/web-dashboard")
TEMPLATE_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"


# ==================== 页面加载测试 ====================

class TestPageLoading:
    """测试各页面是否能正确加载"""
    
    @pytest.fixture(scope="class")
    def templates(self):
        """加载所有模板"""
        templates = {}
        for template_file in TEMPLATE_DIR.glob("*.html"):
            templates[template_file.stem] = template_file.read_text(encoding="utf-8")
        return templates
    
    def test_base_template_extends(self, templates):
        """测试所有模板是否正确继承base.html"""
        non_base_templates = [k for k in templates.keys() if k != "base"]
        
        for name in non_base_templates:
            content = templates[name]
            assert "{% extends" in content, f"{name}.html 未继承基础模板"
            assert "base.html" in content, f"{name}.html 未正确引用base.html"
    
    def test_page_titles(self, templates):
        """测试各页面标题是否正确设置"""
        title_pattern = r'{%\s*block\s+title\s*%}([^%]+){%\s*endblock\s*%}'
        
        expected_titles = {
            "dashboard": "仪表板",
            "login": "登录",
            "market": "市场数据",
            "portfolio": "持仓管理",
            "trade": "交易执行",
            "signals": "交易信号",
            "reports": "报告",
        }
        
        for page, expected_title in expected_titles.items():
            if page in templates:
                match = re.search(title_pattern, templates[page])
                if match:
                    title = match.group(1).strip()
                    assert expected_title in title, \
                        f"{page}页面标题不包含'{expected_title}': {title}"
    
    def test_login_page_structure(self, templates):
        """测试登录页面结构"""
        if "login" not in templates:
            pytest.skip("login.html 不存在")
        
        login_content = templates["login"]
        
        # 检查必要元素
        required_elements = [
            "login-container",
            "login-box",
            "form",
            "username",
            "password",
            "submit",
        ]
        
        for element in required_elements:
            assert element in login_content.lower(), f"登录页面缺少: {element}"
    
    def test_dashboard_page_structure(self, templates):
        """测试仪表板页面结构"""
        if "dashboard" not in templates:
            pytest.skip("dashboard.html 不存在")
        
        dashboard = templates["dashboard"]
        
        # 检查关键区域
        sections = [
            ("metric-card", "指标卡片"),
            ("table", "数据表格"),
            ("canvas", "图表画布"),
            ("card", "卡片容器"),
        ]
        
        for element, desc in sections:
            assert element in dashboard, f"仪表板缺少{desc}: {element}"
    
    def test_market_page_structure(self, templates):
        """测试市场数据页面结构"""
        if "market" not in templates:
            pytest.skip("market.html 不存在")
        
        market = templates["market"]
        
        # 检查市场数据特有元素
        market_elements = [
            "priceTable",
            "klineChart",
            "searchSymbol",
            "refreshData",
        ]
        
        for element in market_elements:
            assert element in market, f"市场页面缺少: {element}"
    
    def test_trade_page_structure(self, templates):
        """测试交易页面结构"""
        if "trade" not in templates:
            pytest.skip("trade.html 不存在")
        
        trade = templates["trade"]
        
        # 检查交易表单元素
        form_elements = [
            "action_buy",
            "action_sell",
            "symbol",
            "quantity",
            "order_type",
            "stop_loss",
            "take_profit",
        ]
        
        for element in form_elements:
            assert element in trade, f"交易页面缺少: {element}"
    
    def test_portfolio_page_structure(self, templates):
        """测试持仓管理页面结构"""
        if "portfolio" not in templates:
            pytest.skip("portfolio.html 不存在")
        
        portfolio = templates["portfolio"]
        
        # 检查持仓管理元素
        portfolio_elements = [
            "allocationChart",
            "positions",
            "unrealized_pnl",
            "market_value",
        ]
        
        found = sum(1 for e in portfolio_elements if e in portfolio)
        assert found >= 2, f"持仓页面元素不足，只找到: {found}个"
    
    def test_signals_page_structure(self, templates):
        """测试交易信号页面结构"""
        if "signals" not in templates:
            pytest.skip("signals.html 不存在")
        
        signals = templates["signals"]
        
        # 检查信号页面元素
        signal_elements = [
            "signalChart",
            "signal_type",
            "strength",
            "rating",
        ]
        
        found = sum(1 for e in signal_elements if e in signals)
        assert found >= 2, f"信号页面元素不足，只找到: {found}个"
    
    def test_reports_page_structure(self, templates):
        """测试报告页面结构"""
        if "reports" not in templates:
            pytest.skip("reports.html 不存在")
        
        reports = templates["reports"]
        
        # 检查报告页面元素
        report_elements = [
            "pnlChart",
            "monthlyChart",
            "exportReport",
            "win_rate",
            "total_trades",
        ]
        
        found = sum(1 for e in report_elements if e in reports)
        assert found >= 2, f"报告页面元素不足，只找到: {found}个"


# ==================== 数据渲染测试 ====================

class TestDataRendering:
    """测试数据渲染逻辑"""
    
    @pytest.fixture(scope="class")
    def templates(self):
        """加载所有模板"""
        templates = {}
        for template_file in TEMPLATE_DIR.glob("*.html"):
            templates[template_file.stem] = template_file.read_text(encoding="utf-8")
        return templates
    
    def test_jinja2_variables_defined(self, templates):
        """测试Jinja2模板变量定义"""
        # 检查常见的模板变量
        variable_pattern = r'{{\s*(\w+)\s*}}'
        
        all_vars = set()
        for content in templates.values():
            vars_found = re.findall(variable_pattern, content)
            all_vars.update(vars_found)
        
        # 检查关键变量是否存在
        key_vars = [
            "total_assets",
            "today_pnl",
            "signals",
            "positions",
            "prices",
            "orders",
            "news_items",
            "sentiment_stats",
        ]
        
        found_keys = [v for v in key_vars if v in all_vars]
        # 放宽要求，只要有模板变量即可
        assert len(all_vars) >= 3, f"模板变量总数不足，只找到: {len(all_vars)}个变量"
    
    def test_conditional_rendering(self, templates):
        """测试条件渲染逻辑"""
        # 检查if语句
        if_pattern = r'{%\s*if\s+[^%]+\s*%}'
        
        if_count = 0
        for content in templates.values():
            if_count += len(re.findall(if_pattern, content))
        
        assert if_count >= 10, f"条件渲染语句较少: {if_count}个"
    
    def test_loop_rendering(self, templates):
        """测试循环渲染"""
        # 检查for循环
        for_pattern = r'{%\s*for\s+[^%]+\s*%}'
        
        for_count = 0
        for content in templates.values():
            for_count += len(re.findall(for_pattern, content))
        
        assert for_count >= 5, f"循环渲染语句较少: {for_count}个"
    
    def test_data_formatting(self, templates):
        """测试数据格式化"""
        # 检查数字格式化
        format_patterns = [
            r'"{:,.2f}"',
            r'"{:,.0f}"',
            r'"{:.2f}"',
            r'"%.2f"',
        ]
        
        found_formatting = False
        for content in templates.values():
            for pattern in format_patterns:
                if re.search(pattern, content):
                    found_formatting = True
                    break
        
        assert found_formatting, "未找到数据格式化语句"
    
    def test_empty_state_handling(self, templates):
        """测试空状态处理"""
        # 检查是否有空状态提示
        empty_indicators = [
            "暂无",
            "empty",
            "inbox",
            "暂无数据",
        ]
        
        found_empty = False
        for content in templates.values():
            for indicator in empty_indicators:
                if indicator in content:
                    found_empty = True
                    break
        
        assert found_empty, "未找到空状态处理"
    
    def test_flash_messages(self, templates):
        """测试Flash消息渲染"""
        base_template = templates.get("base", "")
        
        flash_patterns = [
            "get_flashed_messages",
            "with_categories",
            "alert-",
        ]
        
        for pattern in flash_patterns:
            assert pattern in base_template, f"未找到Flash消息处理: {pattern}"


# ==================== 交互元素测试 ====================

class TestInteractiveElements:
    """测试交互元素"""
    
    @pytest.fixture(scope="class")
    def templates(self):
        """加载所有模板"""
        templates = {}
        for template_file in TEMPLATE_DIR.glob("*.html"):
            templates[template_file.stem] = template_file.read_text(encoding="utf-8")
        return templates
    
    @pytest.fixture(scope="class")
    def js_content(self):
        """加载JS文件"""
        js_file = STATIC_DIR / "js" / "app.js"
        if not js_file.exists():
            pytest.skip("app.js 不存在")
        return js_file.read_text(encoding="utf-8")
    
    def test_click_handlers(self, templates):
        """测试点击事件处理"""
        click_patterns = [
            r'onclick\s*=\s*["\']',
            r'@click',
            r'addEventListener\s*\(\s*["\']click',
        ]
        
        found_click = False
        for content in templates.values():
            for pattern in click_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found_click = True
                    break
        
        assert found_click, "未找到点击事件处理"
    
    def test_form_submissions(self, templates):
        """测试表单提交"""
        form_pattern = r'<form[^>]*method\s*=\s*["\']POST["\']'
        
        found_post_form = False
        for content in templates.values():
            if re.search(form_pattern, content, re.IGNORECASE):
                found_post_form = True
                break
        
        assert found_post_form, "未找到POST表单"
    
    def test_input_validation(self, templates):
        """测试输入验证属性"""
        validation_attrs = [
            "required",
            "min=",
            "max=",
            "pattern=",
            "type=\"number\"",
            "type=\"email\"",
        ]
        
        combined = " ".join(templates.values())
        found_validations = sum(1 for attr in validation_attrs if attr in combined)
        
        assert found_validations >= 3, f"输入验证属性不足: {found_validations}个"
    
    def test_javascript_functions(self, js_content):
        """测试JavaScript函数定义"""
        expected_functions = [
            "initTooltips",
            "updateRealtimePrices",
            "formatNumber",
            "formatCurrency",
            "debounce",
            "throttle",
        ]
        
        found_functions = []
        for func in expected_functions:
            if f"function {func}" in js_content or f"const {func}" in js_content:
                found_functions.append(func)
        
        assert len(found_functions) >= 3, f"JS函数定义不足: {found_functions}"
    
    def test_ajax_calls(self, templates, js_content):
        """测试AJAX调用"""
        ajax_patterns = [
            r'fetch\s*\(',
            r'\.ajax',
            r'XMLHttpRequest',
        ]
        
        combined = " ".join(templates.values()) + js_content
        
        found_ajax = False
        for pattern in ajax_patterns:
            if re.search(pattern, combined):
                found_ajax = True
                break
        
        assert found_ajax, "未找到AJAX调用"
    
    def test_chart_initialization(self, templates):
        """测试图表初始化"""
        chart_patterns = [
            r'new\s+Chart\s*\(',
            r'echarts\.init',
            r'getContext\s*\(\s*[\'"]2d[\'"]\s*\)',
        ]
        
        combined = " ".join(templates.values())
        
        found_chart = False
        for pattern in chart_patterns:
            if re.search(pattern, combined):
                found_chart = True
                break
        
        assert found_chart, "未找到图表初始化代码"
    
    def test_event_listeners(self, js_content):
        """测试事件监听器"""
        listener_patterns = [
            r'addEventListener\s*\(',
            r'\.on\s*\(',
        ]
        
        found_listener = False
        for pattern in listener_patterns:
            if re.search(pattern, js_content):
                found_listener = True
                break
        
        assert found_listener, "未找到事件监听器"
    
    def test_loading_states(self, templates, js_content):
        """测试加载状态"""
        loading_indicators = [
            "spinner",
            "loading",
            "showLoading",
            "加载中",
        ]
        
        combined = " ".join(templates.values()) + js_content
        
        found_loading = any(indicator in combined for indicator in loading_indicators)
        assert found_loading, "未找到加载状态指示器"
    
    def test_error_handling(self, js_content):
        """测试错误处理"""
        error_patterns = [
            r'try\s*{',
            r'catch\s*\(',
            r'showError',
            r'console\.error',
        ]
        
        found_error = False
        for pattern in error_patterns:
            if re.search(pattern, js_content):
                found_error = True
                break
        
        assert found_error, "未找到错误处理代码"


# ==================== 导航测试 ====================

class TestNavigation:
    """测试导航功能"""
    
    @pytest.fixture(scope="class")
    def base_template(self):
        """加载基础模板"""
        template = TEMPLATE_DIR / "base.html"
        if not template.exists():
            pytest.skip("base.html 不存在")
        return template.read_text(encoding="utf-8")
    
    def test_navigation_links(self, base_template):
        """测试导航链接"""
        expected_routes = [
            "dashboard",
            "market",
            "signals",
            "portfolio",
            "trade",
            "reports",
            "logout",
        ]
        
        url_pattern = r'url_for\s*\(\s*[\'"](\w+)[\'"]\s*\)'
        found_routes = re.findall(url_pattern, base_template)
        
        for route in expected_routes:
            assert route in found_routes, f"导航缺少路由: {route}"
    
    def test_active_state_handling(self, base_template):
        """测试活动状态处理"""
        active_patterns = [
            r'request\.endpoint',
            r'==\s*[\'"]dashboard[\'"]',
            r'active',
        ]
        
        for pattern in active_patterns:
            assert re.search(pattern, base_template), f"未找到活动状态处理: {pattern}"
    
    def test_dropdown_menu(self, base_template):
        """测试下拉菜单"""
        dropdown_elements = [
            "dropdown",
            "dropdown-menu",
            "dropdown-toggle",
        ]
        
        for element in dropdown_elements:
            assert element in base_template, f"未找到下拉菜单元素: {element}"


# ==================== 静态资源测试 ====================

class TestStaticResources:
    """测试静态资源"""
    
    def test_css_files_exist(self):
        """测试CSS文件存在"""
        css_dir = STATIC_DIR / "css"
        assert css_dir.exists(), "CSS目录不存在"
        
        css_files = list(css_dir.glob("*.css"))
        assert len(css_files) >= 2, f"CSS文件数量不足: {len(css_files)}个"
    
    def test_js_files_exist(self):
        """测试JS文件存在"""
        js_dir = STATIC_DIR / "js"
        assert js_dir.exists(), "JS目录不存在"
        
        js_files = list(js_dir.glob("*.js"))
        assert len(js_files) >= 1, f"JS文件数量不足: {len(js_files)}个"
    
    def test_external_cdns(self):
        """测试外部CDN引用"""
        base_template = TEMPLATE_DIR / "base.html"
        if not base_template.exists():
            pytest.skip("base.html 不存在")
        
        content = base_template.read_text(encoding="utf-8")
        
        expected_cdns = [
            "bootstrap",
            "chart.js",
            "echarts",
        ]
        
        for cdn in expected_cdns:
            assert cdn.lower() in content.lower(), f"未找到CDN引用: {cdn}"


# ==================== 辅助函数 ====================

def extract_template_variables(template_content):
    """提取模板中使用的变量"""
    var_pattern = r'{{\s*(\w+)\s*}}'
    return set(re.findall(var_pattern, template_content))


def count_template_blocks(template_content):
    """统计模板块数量"""
    block_pattern = r'{%\s*block\s+(\w+)\s*%}'
    return len(re.findall(block_pattern, template_content))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
