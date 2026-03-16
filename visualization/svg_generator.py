"""SVG图表生成器"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from xml.sax.saxutils import escape


class SVGChartGenerator:
    """
    SVG图表生成器 - 生成矢量图表用于量化交易可视化
    
    支持:
    - K线图 (Candlestick)
    - 折线图 (Line)
    - 面积图 (Area)
    - 柱状图 (Bar)
    - 组合图表
    """
    
    # 暗色主题配色
    THEMES = {
        'dark': {
            'background': '#1e1e2e',
            'grid': '#2d2d44',
            'text': '#f1f2f6',
            'text_secondary': '#a4b0be',
            'up': '#00ff88',
            'down': '#ff4757',
            'line': '#3742fa',
            'volume': '#70a1ff',
            'crosshair': '#57606f',
            'profit': '#2ed573',
            'loss': '#ff4757'
        },
        'light': {
            'background': '#ffffff',
            'grid': '#e0e0e0',
            'text': '#333333',
            'text_secondary': '#666666',
            'up': '#26de81',
            'down': '#ff6b6b',
            'line': '#4834d4',
            'volume': '#3498db',
            'crosshair': '#95a5a6',
            'profit': '#2ecc71',
            'loss': '#e74c3c'
        }
    }
    
    def __init__(
        self,
        width: int = 1200,
        height: int = 600,
        theme: str = 'dark'
    ):
        self.width = width
        self.height = height
        self.theme = self.THEMES.get(theme, self.THEMES['dark'])
        self.margin = {'top': 40, 'right': 80, 'bottom': 60, 'left': 80}
        self.chart_height = height - self.margin['top'] - self.margin['bottom']
        self.chart_width = width - self.margin['left'] - self.margin['right']
    
    def _create_svg_header(self) -> str:
        """创建SVG头部"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}"
     xmlns="http://www.w3.org/2000/svg" style="background-color: {self.theme['background']};">
<defs>
    <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" style="stop-color:{self.theme['line']};stop-opacity:0.4" />
        <stop offset="100%" style="stop-color:{self.theme['line']};stop-opacity:0" />
    </linearGradient>
    <filter id="glow">
        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
        <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
        </feMerge>
    </filter>
</defs>'''
    
    def _create_grid(self, y_ticks: List[float]) -> str:
        """创建网格线"""
        lines = []
        
        # 水平网格线
        for tick in y_ticks:
            y = self._scale_y(tick, y_ticks[0], y_ticks[-1])
            lines.append(f'<line x1="{self.margin["left"]}" y1="{y}" '
                        f'x2="{self.width - self.margin["right"]}" y2="{y}" '
                        f'stroke="{self.theme["grid"]}" stroke-width="1" stroke-dasharray="4,4"/>')
        
        return '\n'.join(lines)
    
    def _scale_y(self, value: float, min_val: float, max_val: float) -> float:
        """Y轴缩放"""
        if max_val == min_val:
            return self.margin['top'] + self.chart_height / 2
        ratio = (value - min_val) / (max_val - min_val)
        return self.margin['top'] + self.chart_height * (1 - ratio)
    
    def _scale_x(self, index: int, total: int) -> float:
        """X轴缩放"""
        return self.margin['left'] + (index / max(total - 1, 1)) * self.chart_width
    
    def create_candlestick_chart(
        self,
        data: pd.DataFrame,
        title: str = "Candlestick Chart",
        show_volume: bool = True
    ) -> str:
        """
        创建K线图
        
        Args:
            data: DataFrame with ['date', 'open', 'high', 'low', 'close', 'volume']
            title: 图表标题
            show_volume: 是否显示成交量
        """
        if show_volume and 'volume' in data.columns:
            price_height = self.chart_height * 0.7
            volume_height = self.chart_height * 0.25
            volume_gap = self.chart_height * 0.05
        else:
            price_height = self.chart_height
            volume_height = 0
            volume_gap = 0
        
        svg_parts = [self._create_svg_header()]
        
        # 标题
        svg_parts.append(f'''
    <text x="{self.width/2}" y="25" text-anchor="middle" 
          font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="{self.theme['text']}">
        {escape(title)}
    </text>''')
        
        # 计算价格范围
        price_min = data['low'].min()
        price_max = data['high'].max()
        price_range = price_max - price_min
        price_min -= price_range * 0.05
        price_max += price_range * 0.05
        
        # 网格线
        y_ticks = np.linspace(price_min, price_max, 6)
        svg_parts.append(self._create_grid(y_ticks))
        
        # 绘制K线
        candle_width = max(2, self.chart_width / len(data) * 0.7)
        
        for i, (_, row) in enumerate(data.iterrows()):
            x = self._scale_x(i, len(data))
            
            open_y = self.margin['top'] + price_height * (1 - (row['open'] - price_min) / (price_max - price_min))
            close_y = self.margin['top'] + price_height * (1 - (row['close'] - price_min) / (price_max - price_min))
            high_y = self.margin['top'] + price_height * (1 - (row['high'] - price_min) / (price_max - price_min))
            low_y = self.margin['top'] + price_height * (1 - (row['low'] - price_min) / (price_max - price_min))
            
            is_up = row['close'] >= row['open']
            color = self.theme['up'] if is_up else self.theme['down']
            
            # 影线
            svg_parts.append(f'<line x1="{x}" y1="{high_y}" x2="{x}" y2="{low_y}" '
                           f'stroke="{color}" stroke-width="1"/>')
            
            # 实体
            body_top = min(open_y, close_y)
            body_height = abs(close_y - open_y)
            body_height = max(body_height, 1)
            
            svg_parts.append(f'<rect x="{x - candle_width/2}" y="{body_top}" '
                           f'width="{candle_width}" height="{body_height}" '
                           f'fill="{color}" rx="1"/>')
        
        # 绘制成交量
        if show_volume and 'volume' in data.columns:
            vol_max = data['volume'].max()
            vol_top = self.margin['top'] + price_height + volume_gap
            
            for i, (_, row) in enumerate(data.iterrows()):
                x = self._scale_x(i, len(data))
                vol_height = (row['volume'] / vol_max) * volume_height
                is_up = row['close'] >= row['open']
                color = self.theme['up'] if is_up else self.theme['down']
                
                svg_parts.append(f'<rect x="{x - candle_width/2}" y="{vol_top + volume_height - vol_height}" '
                               f'width="{candle_width}" height="{vol_height}" '
                               f'fill="{color}" opacity="0.5"/>')
        
        # Y轴标签
        for tick in y_ticks:
            y = self._scale_y(tick, price_min, price_max)
            svg_parts.append(f'<text x="{self.margin["left"] - 10}" y="{y + 4}" '
                           f'text-anchor="end" font-size="11" fill="{self.theme["text_secondary"]}">'
                           f'{tick:.2f}</text>')
        
        # X轴标签
        n_labels = min(6, len(data))
        for i in range(0, len(data), max(1, len(data) // n_labels)):
            x = self._scale_x(i, len(data))
            date_str = str(data.iloc[i]['date'])[:10] if 'date' in data.columns else str(i)
            svg_parts.append(f'<text x="{x}" y="{self.height - 20}" '
                           f'text-anchor="middle" font-size="11" fill="{self.theme["text_secondary"]}">'
                           f'{date_str}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def create_line_chart(
        self,
        data: pd.DataFrame,
        columns: List[str],
        title: str = "Line Chart",
        fill_area: bool = False
    ) -> str:
        """
        创建折线图
        
        Args:
            data: DataFrame
            columns: 要绘制的列
            title: 标题
            fill_area: 是否填充面积
        """
        svg_parts = [self._create_svg_header()]
        
        # 标题
        svg_parts.append(f'''
    <text x="{self.width/2}" y="25" text-anchor="middle" 
          font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="{self.theme['text']}">
        {escape(title)}
    </text>''')
        
        # 计算范围
        all_values = data[columns].values.flatten()
        y_min = np.nanmin(all_values)
        y_max = np.nanmax(all_values)
        y_range = y_max - y_min
        y_min -= y_range * 0.05
        y_max += y_range * 0.05
        
        colors = ['#3742fa', '#ff6b6b', '#26de81', '#f9ca24', '#6c5ce7']
        
        for col_idx, column in enumerate(columns):
            color = colors[col_idx % len(colors)]
            values = data[column].values
            
            # 创建路径点
            points = []
            for i, val in enumerate(values):
                if not np.isnan(val):
                    x = self._scale_x(i, len(values))
                    y = self._scale_y(val, y_min, y_max)
                    points.append(f"{x},{y}")
            
            if len(points) < 2:
                continue
            
            # 绘制线
            path_d = 'M' + ' L'.join(points)
            svg_parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" '
                           f'stroke-width="2" filter="url(#glow)"/>')
            
            # 填充面积
            if fill_area:
                area_d = path_d + f' L{self._scale_x(len(values)-1, len(values))},{self.height - self.margin["bottom"]} ' \
                                 f'L{self.margin["left"]},{self.height - self.margin["bottom"]} Z'
                svg_parts.append(f'<path d="{area_d}" fill="url(#areaGradient)" opacity="0.3"/>')
        
        # 网格线和标签
        y_ticks = np.linspace(y_min, y_max, 6)
        svg_parts.append(self._create_grid(y_ticks))
        
        for tick in y_ticks:
            y = self._scale_y(tick, y_min, y_max)
            svg_parts.append(f'<text x="{self.margin["left"] - 10}" y="{y + 4}" '
                           f'text-anchor="end" font-size="11" fill="{self.theme["text_secondary"]}">'
                           f'{tick:.2f}</text>')
        
        # 图例
        legend_x = self.width - self.margin['right'] + 10
        for i, col in enumerate(columns):
            color = colors[i % len(colors)]
            y = self.margin['top'] + 20 + i * 20
            svg_parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 20}" y2="{y}" '
                           f'stroke="{color}" stroke-width="2"/>')
            svg_parts.append(f'<text x="{legend_x + 25}" y="{y + 4}" '
                           f'font-size="11" fill="{self.theme["text"]}">{escape(col)}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def create_equity_curve(
        self,
        equity_data: pd.DataFrame,
        trades: List = None,
        title: str = "Equity Curve"
    ) -> str:
        """
        创建权益曲线图
        
        Args:
            equity_data: DataFrame with ['timestamp', 'equity']
            trades: 交易记录列表
            title: 标题
        """
        svg_parts = [self._create_svg_header()]
        
        # 标题
        svg_parts.append(f'''
    <text x="{self.width/2}" y="25" text-anchor="middle" 
          font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="{self.theme['text']}">
        {escape(title)}
    </text>''')
        
        equity = equity_data['equity'].values
        y_min = equity.min()
        y_max = equity.max()
        y_range = y_max - y_min
        y_min -= y_range * 0.05
        y_max += y_range * 0.05
        
        # 基准线
        base_y = self._scale_y(equity[0], y_min, y_max)
        svg_parts.append(f'<line x1="{self.margin["left"]}" y1="{base_y}" '
                       f'x2="{self.width - self.margin["right"]}" y2="{base_y}" '
                       f'stroke="{self.theme["grid"]}" stroke-width="1" stroke-dasharray="5,5"/>')
        
        # 权益曲线
        points = []
        for i, val in enumerate(equity):
            x = self._scale_x(i, len(equity))
            y = self._scale_y(val, y_min, y_max)
            points.append(f"{x},{y}")
        
        # 渐变填充
        path_d = 'M' + ' L'.join(points)
        fill_d = path_d + f' L{self._scale_x(len(equity)-1, len(equity))},{self.height - self.margin["bottom"]} ' \
                         f'L{self.margin["left"]},{self.height - self.margin["bottom"]} Z'
        
        svg_parts.append(f'<path d="{fill_d}" fill="url(#areaGradient)" opacity="0.3"/>')
        svg_parts.append(f'<path d="{path_d}" fill="none" stroke="{self.theme["line"]}" '
                       f'stroke-width="2.5" filter="url(#glow)"/>')
        
        # 标记交易点
        if trades:
            for trade in trades:
                # 简化的交易标记
                pass
        
        # 网格和标签
        y_ticks = np.linspace(y_min, y_max, 6)
        svg_parts.append(self._create_grid(y_ticks))
        
        for tick in y_ticks:
            y = self._scale_y(tick, y_min, y_max)
            svg_parts.append(f'<text x="{self.margin["left"] - 10}" y="{y + 4}" '
                           f'text-anchor="end" font-size="11" fill="{self.theme["text_secondary"]}">'
                           f'${tick:,.0f}</text>')
        
        # 统计信息
        total_return = (equity[-1] - equity[0]) / equity[0]
        stats_text = f"Return: {total_return:.2%} | Final: ${equity[-1]:,.2f}"
        svg_parts.append(f'<text x="{self.margin["left"]}" y="{self.height - 10}" '
                       f'font-size="12" fill="{self.theme["text"]}">{stats_text}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def create_performance_chart(
        self,
        metrics: Dict[str, float],
        title: str = "Performance Metrics"
    ) -> str:
        """
        创建绩效指标图表
        
        Args:
            metrics: 绩效指标字典
            title: 标题
        """
        width, height = 600, 400
        svg_parts = [f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" style="background-color: {self.theme['background']};">''']
        
        # 标题
        svg_parts.append(f'''
    <text x="{width/2}" y="30" text-anchor="middle" 
          font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="{self.theme['text']}">
        {escape(title)}
    </text>''')
        
        # 指标显示
        key_metrics = [
            ('Total Return', 'total_return', '{:.2%}'),
            ('Annual Return', 'annual_return', '{:.2%}'),
            ('Max Drawdown', 'max_drawdown', '{:.2%}'),
            ('Sharpe Ratio', 'sharpe_ratio', '{:.2f}'),
            ('Win Rate', 'win_rate', '{:.2%}'),
            ('Total Trades', 'total_trades', '{:d}'),
        ]
        
        start_y = 70
        row_height = 45
        col_width = 250
        
        for i, (label, key, fmt) in enumerate(key_metrics):
            row = i // 2
            col = i % 2
            x = 50 + col * col_width
            y = start_y + row * row_height
            
            value = metrics.get(key, 0)
            if key in ['total_return', 'annual_return']:
                color = self.theme['profit'] if value > 0 else self.theme['loss']
            elif key == 'max_drawdown':
                color = self.theme['loss']
            else:
                color = self.theme['text']
            
            svg_parts.append(f'<text x="{x}" y="{y}" font-size="13" fill="{self.theme["text_secondary"]}">{label}</text>')
            svg_parts.append(f'<text x="{x}" y="{y + 20}" font-size="16" font-weight="bold" fill="{color}">{fmt.format(value)}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def save_svg(self, svg_content: str, filepath: str):
        """保存SVG文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)
    
    @staticmethod
    def svg_to_base64(svg_content: str) -> str:
        """SVG转Base64"""
        import base64
        return base64.b64encode(svg_content.encode()).decode()
