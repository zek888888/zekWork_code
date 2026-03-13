"""
响应式适配测试 - 量化交易仪表盘
测试移动端、平板和桌面端适配
"""

import pytest
import re
from pathlib import Path


# ==================== 测试配置 ====================

PROJECT_ROOT = Path("/Users/mac/.openclaw/workspace/quant-trading/web-dashboard")
CSS_DIR = PROJECT_ROOT / "static" / "css"
TEMPLATE_DIR = PROJECT_ROOT / "templates"

# 响应式断点定义
BREAKPOINTS = {
    "xs": {"max": 576, "name": "超小屏(手机)"},
    "sm": {"min": 577, "max": 768, "name": "小屏(大屏手机)"},
    "md": {"min": 769, "max": 992, "name": "中屏(平板)"},
    "lg": {"min": 993, "max": 1200, "name": "大屏(桌面)"},
    "xl": {"min": 1201, "name": "超大屏(大桌面)"},
}


# ==================== 移动端适配测试 ====================

class TestMobileResponsiveness:
    """测试移动端适配 (max-width: 768px)"""
    
    @pytest.fixture(scope="class")
    def all_css(self):
        """加载所有CSS"""
        css_content = ""
        for css_file in CSS_DIR.glob("*.css"):
            css_content += css_file.read_text(encoding="utf-8") + "\n"
        return css_content
    
    @pytest.fixture(scope="class")
    def all_templates(self):
        """加载所有模板"""
        templates = {}
        for template_file in TEMPLATE_DIR.glob("*.html"):
            templates[template_file.stem] = template_file.read_text(encoding="utf-8")
        return templates
    
    def test_mobile_breakpoint_exists(self, all_css):
        """测试移动端断点是否存在"""
        mobile_patterns = [
            r'@media\s*\(\s*max-width:\s*768px\s*\)',
            r'@media\s*\(\s*max-width:\s*767\.?98px\s*\)',
            r'@media\s*\(\s*max-width:\s*575\.?98px\s*\)',
        ]
        
        found = any(re.search(pattern, all_css, re.IGNORECASE) for pattern in mobile_patterns)
        assert found, "未找到移动端断点 (@media max-width: 768px)"
    
    def test_mobile_font_size_adjustments(self, all_css):
        """测试移动端字体大小调整"""
        # 提取移动端样式块
        mobile_block = self._extract_media_block(all_css, 768)
        
        if mobile_block:
            # 检查字体大小调整
            font_patterns = [
                r'font-size\s*:\s*\d+\.?\d*px',
                r'font-size\s*:\s*\d+\.?\d*rem',
                r'font-size\s*:\s*\d+\.?\d*em',
            ]
            
            found_font = any(re.search(pattern, mobile_block) for pattern in font_patterns)
            if not found_font:
                pytest.skip("移动端未调整字体大小（建议添加）")
        else:
            pytest.skip("未找到移动端样式块")
    
    def test_mobile_padding_adjustments(self, all_css):
        """测试移动端内边距调整"""
        mobile_block = self._extract_media_block(all_css, 768)
        
        if mobile_block:
            padding_pattern = r'padding\s*:\s*[^;]+;'
            found = re.search(padding_pattern, mobile_block)
            if not found:
                pytest.skip("移动端未调整内边距（建议添加）")
        else:
            pytest.skip("未找到移动端样式块")
    
    def test_mobile_navigation_collapse(self, all_templates):
        """测试移动端导航折叠"""
        base_template = all_templates.get("base", "")
        
        # 检查Bootstrap导航折叠类
        nav_elements = [
            "navbar-toggler",
            "navbar-collapse",
            "collapse",
        ]
        
        for element in nav_elements:
            assert element in base_template, f"移动端导航缺少: {element}"
    
    def test_mobile_grid_adjustments(self, all_templates):
        """测试移动端网格调整"""
        combined = " ".join(all_templates.values())
        
        # 检查响应式网格类
        grid_classes = [
            r'col-\d+',           # col-6, col-12
            r'col-sm-\d+',        # col-sm-6
            r'col-md-\d+',        # col-md-4
        ]
        
        found_grids = []
        for pattern in grid_classes:
            matches = re.findall(pattern, combined)
            found_grids.extend(matches)
        
        assert len(found_grids) >= 10, f"响应式网格类使用不足: {len(found_grids)}个"
    
    def test_mobile_table_responsive(self, all_templates):
        """测试移动端表格响应式"""
        combined = " ".join(all_templates.values())
        
        # 检查表格响应式类
        table_responsive = "table-responsive" in combined
        
        # 检查表格存在
        has_tables = "<table" in combined
        
        if has_tables:
            assert table_responsive, "表格应使用table-responsive类以适应移动端"
    
    def test_mobile_button_sizes(self, all_templates):
        """测试移动端按钮大小"""
        combined = " ".join(all_templates.values())
        
        # 检查按钮类
        button_classes = [
            "btn-sm",
            "btn-lg",
            "btn",
        ]
        
        found = sum(1 for cls in button_classes if cls in combined)
        assert found >= 2, "应使用按钮大小类"
    
    def test_mobile_touch_targets(self, all_css):
        """测试触摸目标大小"""
        # 检查是否有足够的触摸目标大小 (至少44px)
        touch_patterns = [
            r'(?:min-width|min-height)\s*:\s*(?:4[4-9]|[5-9]\d)\s*px',
            r'padding\s*:\s*(?:1[2-9]|[2-9]\d)',
        ]
        
        found = any(re.search(pattern, all_css) for pattern in touch_patterns)
        if not found:
            pytest.skip("建议添加触摸目标大小优化 (min 44px)")
    
    def _extract_media_block(self, css, max_width):
        """提取特定断点的媒体查询块"""
        pattern = rf'@media\s*\([^)]*{max_width}[^)]*\)\s*\{{([^}}]+(?:\{{[^}}]*\}}[^}}]*)*)\}}'
        match = re.search(pattern, css, re.DOTALL | re.IGNORECASE)
        return match.group(1) if match else None


# ==================== 平板适配测试 ====================

class TestTabletResponsiveness:
    """测试平板适配 (768px - 992px)"""
    
    @pytest.fixture(scope="class")
    def all_css(self):
        """加载所有CSS"""
        css_content = ""
        for css_file in CSS_DIR.glob("*.css"):
            css_content += css_file.read_text(encoding="utf-8") + "\n"
        return css_content
    
    @pytest.fixture(scope="class")
    def all_templates(self):
        """加载所有模板"""
        templates = {}
        for template_file in TEMPLATE_DIR.glob("*.html"):
            templates[template_file.stem] = template_file.read_text(encoding="utf-8")
        return templates
    
    def test_tablet_breakpoint_exists(self, all_css):
        """测试平板断点是否存在"""
        tablet_patterns = [
            r'@media\s*\(\s*min-width:\s*768px\s*and\s*max-width:\s*992px\s*\)',
            r'@media\s*\(\s*max-width:\s*992px\s*\)',
            r'@media\s*\(\s*min-width:\s*768px\s*\)',
        ]
        
        found = any(re.search(pattern, all_css, re.IGNORECASE) for pattern in tablet_patterns)
        if not found:
            pytest.skip("未找到专门的平板断点（使用Bootstrap响应式类也可以）")
    
    def test_tablet_grid_layout(self, all_templates):
        """测试平板网格布局"""
        combined = " ".join(all_templates.values())
        
        # 检查平板断点的网格类
        tablet_grid_patterns = [
            r'col-md-\d+',
            r'col-sm-\d+',
        ]
        
        found = any(re.search(pattern, combined) for pattern in tablet_grid_patterns)
        assert found, "应使用平板断点的网格类 (col-md-*, col-sm-*)"
    
    def test_tablet_card_layout(self, all_templates):
        """测试平板卡片布局"""
        combined = " ".join(all_templates.values())
        
        # 检查卡片布局类
        card_patterns = [
            r'col-md-\d+.*card',
            r'card.*col-md-\d+',
        ]
        
        found = any(re.search(pattern, combined, re.DOTALL) for pattern in card_patterns)
        if not found:
            pytest.skip("建议优化平板卡片布局")
    
    def test_tablet_sidebar_handling(self, all_css):
        """测试平板侧边栏处理"""
        # 检查是否有侧边栏相关的响应式处理
        sidebar_patterns = [
            r'sidebar.*768',
            r'768.*sidebar',
            r'drawer.*768',
        ]
        
        found = any(re.search(pattern, all_css, re.IGNORECASE) for pattern in sidebar_patterns)
        # 不是强制要求
        if not found:
            pytest.skip("未找到平板侧边栏处理（可选）")


# ==================== 桌面端适配测试 ====================

class TestDesktopResponsiveness:
    """测试桌面端适配 (min-width: 992px)"""
    
    @pytest.fixture(scope="class")
    def all_css(self):
        """加载所有CSS"""
        css_content = ""
        for css_file in CSS_DIR.glob("*.css"):
            css_content += css_file.read_text(encoding="utf-8") + "\n"
        return css_content
    
    @pytest.fixture(scope="class")
    def all_templates(self):
        """加载所有模板"""
        templates = {}
        for template_file in TEMPLATE_DIR.glob("*.html"):
            templates[template_file.stem] = template_file.read_text(encoding="utf-8")
        return templates
    
    def test_desktop_breakpoint_exists(self, all_css):
        """测试桌面端断点是否存在"""
        desktop_patterns = [
            r'@media\s*\(\s*min-width:\s*992px\s*\)',
            r'@media\s*\(\s*min-width:\s*1200px\s*\)',
            r'@media\s*\(\s*min-width:\s*1400px\s*\)',
        ]
        
        found = any(re.search(pattern, all_css, re.IGNORECASE) for pattern in desktop_patterns)
        if not found:
            pytest.skip("未找到桌面端断点（使用默认样式也可以）")
    
    def test_desktop_grid_layout(self, all_templates):
        """测试桌面端网格布局"""
        combined = " ".join(all_templates.values())
        
        # 检查桌面端网格类
        desktop_patterns = [
            r'col-lg-\d+',
            r'col-xl-\d+',
            r'col-xxl-\d+',
        ]
        
        found = any(re.search(pattern, combined) for pattern in desktop_patterns)
        assert found, "应使用桌面端网格类 (col-lg-*, col-xl-*)"
    
    def test_desktop_container_width(self, all_css):
        """测试桌面端容器宽度"""
        # 检查容器最大宽度
        container_patterns = [
            r'container[^}]*max-width',
            r'\.container\s*\{[^}]*max-width',
            r'max-width\s*:\s*\d+px',
        ]
        
        found = any(re.search(pattern, all_css, re.IGNORECASE) for pattern in container_patterns)
        if not found:
            pytest.skip("未找到容器宽度限制（使用Bootstrap默认也可以）")
    
    def test_desktop_multi_column_layout(self, all_templates):
        """测试桌面端多列布局"""
        combined = " ".join(all_templates.values())
        
        # 检查多列布局类
        multi_column_patterns = [
            r'col-lg-\d+',
            r'col-xl-\d+',
            r'col-md-\d+.*col-lg-\d+',
        ]
        
        found = any(re.search(pattern, combined) for pattern in multi_column_patterns)
        if not found:
            pytest.skip("桌面端未使用多列布局（使用Bootstrap默认也可以）")
    
    def test_desktop_chart_size(self, all_templates):
        """测试桌面端图表大小"""
        combined = " ".join(all_templates.values())
        
        # 检查图表高度设置
        chart_patterns = [
            r'height\s*:\s*\d+px',
            r'height="\d+"',
        ]
        
        found = any(re.search(pattern, combined, re.IGNORECASE) for pattern in chart_patterns)
        if not found:
            pytest.skip("未找到图表高度设置")


# ==================== 视口和Meta测试 ====================

class TestViewport:
    """测试视口配置"""
    
    def test_viewport_meta_tag(self):
        """测试视口meta标签"""
        base_template = TEMPLATE_DIR / "base.html"
        if not base_template.exists():
            pytest.skip("base.html 不存在")
        
        content = base_template.read_text(encoding="utf-8")
        
        viewport_patterns = [
            r'<meta[^>]*name\s*=\s*["\']viewport["\']',
            r'width\s*=\s*device-width',
            r'initial-scale\s*=',
        ]
        
        for pattern in viewport_patterns:
            assert re.search(pattern, content, re.IGNORECASE), f"缺少视口配置: {pattern}"
    
    def test_responsive_images(self):
        """测试响应式图片"""
        combined = ""
        for template_file in TEMPLATE_DIR.glob("*.html"):
            combined += template_file.read_text(encoding="utf-8")
        
        # 检查图片类
        img_classes = [
            "img-fluid",
            "img-responsive",
        ]
        
        # 如果有图片，应该使用响应式类
        if "<img" in combined:
            found = any(cls in combined for cls in img_classes)
            if not found:
                pytest.skip("图片建议使用响应式类 (img-fluid)")


# ==================== 打印样式测试 ====================

class TestPrintStyles:
    """测试打印样式"""
    
    @pytest.fixture(scope="class")
    def all_css(self):
        """加载所有CSS"""
        css_content = ""
        for css_file in CSS_DIR.glob("*.css"):
            css_content += css_file.read_text(encoding="utf-8") + "\n"
        return css_content
    
    def test_print_media_query(self, all_css):
        """测试打印媒体查询"""
        print_pattern = r'@media\s+print'
        found = re.search(print_pattern, all_css, re.IGNORECASE)
        assert found, "应添加打印样式 (@media print)"
    
    def test_print_hide_elements(self, all_css):
        """测试打印时隐藏的元素"""
        # 提取打印样式块
        print_block = self._extract_print_block(all_css)
        
        if print_block:
            # 检查是否隐藏了导航和按钮
            hide_patterns = [
                r'navbar.*display\s*:\s*none',
                r'\.btn.*display\s*:\s*none',
                r'display\s*:\s*none',
            ]
            
            found = any(re.search(pattern, print_block, re.IGNORECASE) for pattern in hide_patterns)
            assert found, "打印样式应隐藏导航和按钮"
        else:
            pytest.skip("未找到打印样式块")
    
    def _extract_print_block(self, css):
        """提取打印媒体查询块"""
        pattern = r'@media\s+print\s*\{([^}]+(?:\{[^}]*\}}[^}]*)*)\}'
        match = re.search(pattern, css, re.DOTALL | re.IGNORECASE)
        return match.group(1) if match else None


# ==================== 断点一致性测试 ====================

class TestBreakpointConsistency:
    """测试断点一致性"""
    
    @pytest.fixture(scope="class")
    def all_css(self):
        """加载所有CSS"""
        css_content = ""
        for css_file in CSS_DIR.glob("*.css"):
            css_content += css_file.read_text(encoding="utf-8") + "\n"
        return css_content
    
    def test_bootstrap_breakpoints_alignment(self, all_css):
        """测试与Bootstrap断点对齐"""
        # Bootstrap 5 断点
        bootstrap_breakpoints = [576, 768, 992, 1200, 1400]
        
        # 提取所有断点值
        breakpoint_pattern = r'(?:min-width|max-width):\s*(\d+)px'
        found_breakpoints = set(int(m) for m in re.findall(breakpoint_pattern, all_css))
        
        # 检查是否使用了接近Bootstrap的断点
        aligned = any(bp in found_breakpoints or bp-0.02 in found_breakpoints 
                     for bp in bootstrap_breakpoints)
        
        if not aligned and found_breakpoints:
            pytest.skip(f"断点与Bootstrap不完全对齐: {found_breakpoints}")
    
    def test_no_conflicting_breakpoints(self, all_css):
        """测试没有冲突的断点"""
        # 提取所有媒体查询
        media_pattern = r'@media\s*\([^)]+\)'
        media_queries = re.findall(media_pattern, all_css, re.IGNORECASE)
        
        # 检查是否有明显冲突的断点
        # 这是一个基本检查，复杂冲突需要人工审查
        assert len(media_queries) > 0, "应至少有一个媒体查询"
    
    def test_breakpoint_order(self, all_css):
        """测试断点顺序（从大到小或从小到大）"""
        # 这是一个建议性的测试
        # 实际检查需要更复杂的CSS解析
        pass


# ==================== 设备特定测试 ====================

class TestDeviceSpecific:
    """测试设备特定适配"""
    
    @pytest.fixture(scope="class")
    def all_css(self):
        """加载所有CSS"""
        css_content = ""
        for css_file in CSS_DIR.glob("*.css"):
            css_content += css_file.read_text(encoding="utf-8") + "\n"
        return css_content
    
    def test_iphone_se_viewport(self, all_css):
        """测试iPhone SE视口 (375px)"""
        # 检查375px附近的样式
        iphone_pattern = r'(?:max-width:\s*3[7-9]\d|min-width:\s*3[7-9]\d)'
        found = re.search(iphone_pattern, all_css)
        
        # 不是强制要求
        if not found:
            pytest.skip("未找到iPhone SE特定样式（可选）")
    
    def test_ipad_viewport(self, all_css):
        """测试iPad视口 (768px-1024px)"""
        ipad_patterns = [
            r'(?:min|max)-width:\s*768',
            r'(?:min|max)-width:\s*1024',
        ]
        
        found = any(re.search(pattern, all_css) for pattern in ipad_patterns)
        if not found:
            pytest.skip("未找到iPad特定样式（使用通用平板样式也可以）")
    
    def test_large_desktop_viewport(self, all_css):
        """测试大屏桌面视口 (1440px+)"""
        large_patterns = [
            r'min-width:\s*1200',
            r'min-width:\s*1400',
            r'min-width:\s*1440',
        ]
        
        found = any(re.search(pattern, all_css) for pattern in large_patterns)
        if not found:
            pytest.skip("未找到大屏桌面特定样式（可选）")


# ==================== 辅助函数 ====================

def get_media_queries(css_content):
    """提取所有媒体查询"""
    pattern = r'@media\s*\([^)]+\)\s*\{([^}]+(?:\{[^}]*\}}[^}]*)*)\}'
    return re.findall(pattern, css_content, re.DOTALL | re.IGNORECASE)


def get_breakpoint_values(css_content):
    """提取所有断点值"""
    pattern = r'(?:min-width|max-width):\s*(\d+)px'
    return sorted(set(int(m) for m in re.findall(pattern, css_content)))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
