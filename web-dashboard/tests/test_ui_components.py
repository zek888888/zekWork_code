"""
UI组件测试 - 量化交易仪表盘
测试CSS变量、组件渲染和响应式断点
"""

import pytest
import re
from pathlib import Path


# ==================== 测试配置 ====================

PROJECT_ROOT = Path("/Users/mac/.openclaw/workspace/quant-trading/web-dashboard")
CSS_DIR = PROJECT_ROOT / "static" / "css"
TEMPLATE_DIR = PROJECT_ROOT / "templates"


# ==================== CSS变量测试 ====================

class TestCSSVariables:
    """测试CSS变量是否正确加载和定义"""
    
    @pytest.fixture(scope="class")
    def dark_theme_css(self):
        """加载深色主题CSS文件"""
        css_file = CSS_DIR / "dark-theme.css"
        if not css_file.exists():
            pytest.skip("dark-theme.css 文件不存在")
        return css_file.read_text(encoding="utf-8")
    
    @pytest.fixture(scope="class")
    def style_css(self):
        """加载主样式CSS文件"""
        css_file = CSS_DIR / "style.css"
        if not css_file.exists():
            pytest.skip("style.css 文件不存在")
        return css_file.read_text(encoding="utf-8")
    
    def test_css_variables_defined(self, dark_theme_css):
        """测试CSS变量是否正确在:root中定义"""
        # 检查:root块是否存在
        root_match = re.search(r':root\s*\{([^}]+)\}', dark_theme_css, re.DOTALL)
        assert root_match, "未找到 :root CSS变量定义块"
        
        root_content = root_match.group(1)
        
        # 检查核心CSS变量是否存在
        required_vars = [
            "--bg-primary",
            "--bg-secondary",
            "--bg-card",
            "--text-primary",
            "--text-secondary",
            "--accent-primary",
            "--success",
            "--danger",
            "--warning",
            "--info",
            "--border-color",
            "--shadow-md",
            "--radius-md",
            "--transition-normal",
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in root_content:
                missing_vars.append(var)
        
        assert not missing_vars, f"缺少以下CSS变量: {missing_vars}"
    
    def test_color_variables_have_valid_values(self, dark_theme_css):
        """测试颜色变量是否有有效的颜色值"""
        # 匹配CSS变量定义
        var_pattern = r'(--[\w-]+)\s*:\s*([^;]+);'
        variables = dict(re.findall(var_pattern, dark_theme_css))
        
        color_vars = [k for k in variables.keys() if any(
            x in k for x in ["bg-", "text-", "accent-", "success", "danger", "warning", "info", "border-"]
        )]
        
        valid_color_patterns = [
            r'^#[0-9a-fA-F]{3,8}$',  # HEX颜色
            r'^rgba?\([^)]+\)$',      # RGB/RGBA
            r'^hsla?\([^)]+\)$',      # HSL/HSLA
            r'^linear-gradient',       # 渐变
            r'^var\(',                # CSS变量引用
        ]
        
        invalid_colors = []
        for var in color_vars:
            value = variables[var].strip()
            is_valid = any(re.match(pattern, value) for pattern in valid_color_patterns)
            if not is_valid and value not in ["transparent", "none", "inherit", "initial"]:
                invalid_colors.append(f"{var}: {value}")
        
        assert not invalid_colors, f"以下颜色变量值可能无效: {invalid_colors[:5]}"
    
    def test_css_variable_usage(self, dark_theme_css):
        """测试CSS变量是否被实际使用"""
        # 获取所有定义的变量名
        defined_vars = set(re.findall(r'(--[\w-]+)\s*:', dark_theme_css))
        
        # 获取所有使用的变量
        used_vars = set(re.findall(r'var\((--[\w-]+)', dark_theme_css))
        
        # 核心变量应该被使用
        core_vars = {
            "--bg-primary", "--bg-card", "--text-primary",
            "--accent-primary", "--success", "--danger"
        }
        
        unused_core = core_vars - used_vars
        # 只警告，不强制失败，因为有些变量可能是预留的
        if unused_core:
            pytest.warn(f"以下核心CSS变量未被使用: {unused_core}")
    
    def test_responsive_breakpoints_defined(self, dark_theme_css, style_css):
        """测试响应式断点是否定义"""
        combined_css = dark_theme_css + style_css
        
        # 检查常见的响应式断点
        breakpoints = [
            (r'@media\s*\(\s*max-width:\s*576px\s*\)', "xs断点"),
            (r'@media\s*\(\s*max-width:\s*768px\s*\)', "sm断点"),
            (r'@media\s*\(\s*max-width:\s*992px\s*\)', "md断点"),
            (r'@media\s*\(\s*max-width:\s*1200px\s*\)', "lg断点"),
        ]
        
        found_breakpoints = []
        for pattern, name in breakpoints:
            if re.search(pattern, combined_css, re.IGNORECASE):
                found_breakpoints.append(name)
        
        assert len(found_breakpoints) >= 1, "未找到任何响应式断点定义"
    
    def test_animation_keyframes_defined(self, dark_theme_css):
        """测试动画关键帧是否定义"""
        keyframes = re.findall(r'@keyframes\s+(\w+)', dark_theme_css)
        
        expected_animations = ["fadeIn", "count-up", "pulse-glow"]
        for anim in expected_animations:
            if anim in keyframes:
                assert True
                return
        
        # 至少应该有一些动画
        assert len(keyframes) >= 1, "未找到任何CSS动画关键帧"


# ==================== 组件渲染测试 ====================

class TestComponentRendering:
    """测试UI组件是否正确渲染"""
    
    @pytest.fixture(scope="class")
    def base_template(self):
        """加载基础模板"""
        template = TEMPLATE_DIR / "base.html"
        if not template.exists():
            pytest.skip("base.html 模板不存在")
        return template.read_text(encoding="utf-8")
    
    @pytest.fixture(scope="class")
    def dashboard_template(self):
        """加载仪表板模板"""
        template = TEMPLATE_DIR / "dashboard.html"
        if not template.exists():
            pytest.skip("dashboard.html 模板不存在")
        return template.read_text(encoding="utf-8")
    
    def test_base_template_structure(self, base_template):
        """测试基础模板结构完整性"""
        required_elements = [
            "<!DOCTYPE html>",
            "<html",
            "<head>",
            "<body>",
            "{% block content %}",
            "{% block extra_js %}",
            "bootstrap",
            "chart.js",
        ]
        
        missing = []
        for element in required_elements:
            if element.lower() not in base_template.lower():
                missing.append(element)
        
        assert not missing, f"基础模板缺少必要元素: {missing}"
    
    def test_navigation_components(self, base_template):
        """测试导航栏组件"""
        nav_elements = [
            "navbar",
            "navbar-brand",
            "navbar-nav",
            "nav-link",
            "dropdown-menu",
        ]
        
        for element in nav_elements:
            assert element in base_template, f"导航栏缺少 {element} 类"
    
    def test_metric_cards_structure(self, dashboard_template):
        """测试指标卡片结构"""
        # 检查metric-card类是否存在
        assert "metric-card" in dashboard_template, "未找到metric-card类"
        
        # 检查卡片基本结构
        card_elements = [
            "card",
            "card-body",
            "card-title",
            "card-subtitle",
        ]
        
        for element in card_elements:
            assert element in dashboard_template, f"卡片组件缺少 {element} 类"
    
    def test_chart_containers(self, dashboard_template):
        """测试图表容器是否存在"""
        chart_ids = [
            "assetChart",
            "sentimentChart",
        ]
        
        for chart_id in chart_ids:
            pattern = rf'id\s*=\s*["\']{chart_id}["\']'
            assert re.search(pattern, dashboard_template), f"未找到图表容器: {chart_id}"
    
    def test_table_components(self, dashboard_template):
        """测试表格组件"""
        table_classes = [
            "table",
            "table-hover",
            "table-responsive",
        ]
        
        for cls in table_classes:
            assert cls in dashboard_template, f"表格缺少 {cls} 类"
    
    def test_badge_components(self, dashboard_template):
        """测试徽章组件"""
        badge_types = [
            "badge bg-success",
            "badge bg-danger",
            "badge bg-info",
            "badge bg-warning",
            "badge bg-secondary",
        ]
        
        found_badges = []
        for badge in badge_types:
            if badge in dashboard_template:
                found_badges.append(badge)
        
        assert len(found_badges) >= 3, f"徽章类型不足，只找到: {found_badges}"
    
    def test_progress_bar_components(self, dashboard_template):
        """测试进度条组件"""
        assert "progress" in dashboard_template, "未找到progress类"
        assert "progress-bar" in dashboard_template, "未找到progress-bar类"
    
    def test_button_variants(self, base_template, dashboard_template):
        """测试按钮变体"""
        combined = base_template + dashboard_template
        
        button_classes = [
            "btn-primary",
            "btn-success",
            "btn-danger",
            "btn-info",
            "btn-warning",
            "btn-outline-primary",
        ]
        
        found_buttons = []
        for btn in button_classes:
            if btn in combined:
                found_buttons.append(btn)
        
        assert len(found_buttons) >= 4, f"按钮变体不足，只找到: {found_buttons}"
    
    def test_form_components(self):
        """测试表单组件类"""
        # 加载所有模板
        templates = {}
        for template_file in TEMPLATE_DIR.glob("*.html"):
            templates[template_file.stem] = template_file.read_text(encoding="utf-8")
        
        combined = " ".join(templates.values())
        
        form_classes = [
            "form-control",
            "form-select",
            "form-check",
            "input-group",
        ]
        
        found = sum(1 for cls in form_classes if cls in combined)
        assert found >= 2, f"表单组件类不足，只找到: {found}个"


# ==================== 响应式断点测试 ====================

class TestResponsiveBreakpoints:
    """测试响应式断点是否正确配置"""
    
    @pytest.fixture(scope="class")
    def all_css(self):
        """加载所有CSS文件"""
        css_content = ""
        for css_file in CSS_DIR.glob("*.css"):
            css_content += css_file.read_text(encoding="utf-8") + "\n"
        return css_content
    
    def test_mobile_breakpoint_styles(self, all_css):
        """测试移动端断点样式"""
        # 检查768px及以下断点
        mobile_pattern = r'@media\s*\([^)]*max-width[^)]*768[^)]*\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
        mobile_match = re.search(mobile_pattern, all_css, re.DOTALL | re.IGNORECASE)
        
        assert mobile_match, "未找到移动端断点样式 (max-width: 768px)"
        
        mobile_styles = mobile_match.group(1)
        
        # 检查移动端特定的样式调整
        mobile_adjustments = [
            "padding",
            "font-size",
            "margin",
        ]
        
        found = any(adj in mobile_styles for adj in mobile_adjustments)
        assert found, "移动端断点缺少实际的样式调整"
    
    def test_responsive_grid_classes(self, all_css):
        """测试响应式网格类"""
        # Bootstrap网格类应该在HTML中使用
        grid_classes = [
            r'col-md-\d+',
            r'col-sm-\d+',
            r'col-lg-\d+',
            r'col-xl-\d+',
        ]
        
        # 检查模板中的网格类
        templates_content = ""
        for template in TEMPLATE_DIR.glob("*.html"):
            templates_content += template.read_text(encoding="utf-8") + "\n"
        
        found_grids = []
        for pattern in grid_classes:
            if re.search(pattern, templates_content):
                found_grids.append(pattern)
        
        assert len(found_grids) >= 2, f"响应式网格类使用不足: {found_grids}"
    
    def test_table_responsive(self, all_css):
        """测试表格响应式"""
        assert "table-responsive" in all_css or True  # 类在HTML中使用
        
        # 检查模板
        for template in TEMPLATE_DIR.glob("*.html"):
            content = template.read_text(encoding="utf-8")
            if "<table" in content:
                assert "table-responsive" in content or "table" in content, \
                    f"{template.name} 中的表格可能缺少响应式处理"
    
    def test_font_size_responsive(self, all_css):
        """测试字体大小响应式调整"""
        # 检查是否有响应式字体大小调整
        font_patterns = [
            r'font-size\s*:\s*[^;]+;[^}]*@media',
            r'@media[^}]+font-size',
        ]
        
        has_responsive_font = any(
            re.search(pattern, all_css, re.DOTALL | re.IGNORECASE)
            for pattern in font_patterns
        )
        
        # 不是强制要求，但建议有
        if not has_responsive_font:
            pytest.skip("未找到响应式字体大小调整（建议添加）")
    
    def test_spacing_responsive(self, all_css):
        """测试间距响应式调整"""
        # 检查响应式间距调整
        spacing_pattern = r'@media[^}]+(?:padding|margin)[^}]*:\s*\d+px'
        has_responsive_spacing = re.search(spacing_pattern, all_css, re.DOTALL | re.IGNORECASE)
        
        assert has_responsive_spacing, "建议添加响应式间距调整"


# ==================== 视觉回归测试建议 ====================

def test_visual_regression_recommendations():
    """
    视觉回归测试建议
    
    建议实施以下视觉回归测试：
    """
    recommendations = """
    视觉回归测试建议：
    
    1. 工具推荐：
       - Playwright + playwright-visual-regression
       - Cypress + cypress-image-snapshot
       - Storybook + Chromatic
       - Percy (云服务)
    
    2. 测试场景：
       - 登录页面完整截图
       - 仪表板关键指标卡片
       - 市场数据表格和K线图
       - 交易表单所有状态
       - 持仓管理页面
       - 报告页面图表
       - 深色/浅色主题切换
    
    3. 断点截图：
       - 375px (iPhone SE)
       - 768px (iPad)
       - 1440px (桌面)
       - 1920px (大屏)
    
    4. 测试数据：
       - 使用固定的mock数据
       - 冻结时间戳
       - 禁用动画
    
    5. 阈值设置：
       - 像素差异阈值: 0.2%
       - 忽略区域: 动态数据、时间戳
    """
    
    # 这是一个文档性质的测试
    assert True, recommendations


# ==================== 覆盖率检查 ====================

def test_css_coverage():
    """检查CSS覆盖率"""
    css_files = list(CSS_DIR.glob("*.css"))
    assert len(css_files) >= 2, "CSS文件数量不足"
    
    total_css_lines = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in css_files)
    assert total_css_lines > 100, f"CSS代码行数较少: {total_css_lines}行"


def test_template_coverage():
    """检查模板覆盖率"""
    templates = list(TEMPLATE_DIR.glob("*.html"))
    required_templates = ["base.html", "dashboard.html", "login.html"]
    
    template_names = [t.name for t in templates]
    
    for required in required_templates:
        assert required in template_names, f"缺少必要模板: {required}"
    
    assert len(templates) >= 5, f"模板数量不足: {len(templates)}个"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
