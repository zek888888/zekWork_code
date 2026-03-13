// 量化交易系统 - 前端交互脚本

// 全局配置
const CONFIG = {
    refreshInterval: 30000, // 30秒自动刷新
    apiBaseUrl: ''
};

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    initTooltips();
    
    // 初始化自动刷新
    initAutoRefresh();
    
    // 初始化实时价格更新
    initRealtimePrices();
});

// 初始化 Bootstrap 工具提示
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => {
        new bootstrap.Tooltip(el);
    });
}

// 自动刷新功能
function initAutoRefresh() {
    // 每30秒刷新一次实时数据
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            updateRealtimeData();
        }
    }, CONFIG.refreshInterval);
}

// 初始化实时价格
function initRealtimePrices() {
    // 如果页面有实时价格表格，开始更新
    const priceTable = document.getElementById('priceTable');
    if (priceTable) {
        updateRealtimePrices();
    }
}

// 更新实时价格
async function updateRealtimePrices() {
    try {
        const response = await fetch('/api/realtime-prices');
        const prices = await response.json();
        
        prices.forEach(price => {
            const row = document.querySelector(`tr[data-symbol="${price.symbol}"]`);
            if (row) {
                const priceCell = row.querySelector('.price');
                const changeCell = row.querySelector('.change-percent');
                
                if (priceCell) priceCell.textContent = `¥${price.price.toFixed(2)}`;
                if (changeCell) {
                    changeCell.textContent = `${price.change_percent >= 0 ? '+' : ''}${price.change_percent.toFixed(2)}%`;
                    changeCell.className = `change-percent text-end ${price.change_percent >= 0 ? 'text-success' : 'text-danger'}`;
                }
            }
        });
    } catch (error) {
        console.error('更新实时价格失败:', error);
    }
}

// 更新实时数据
function updateRealtimeData() {
    // 更新实时价格
    updateRealtimePrices();
    
    // 可以在这里添加其他实时数据更新
}

// 格式化数字
function formatNumber(num, decimals = 2) {
    return num.toLocaleString('zh-CN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// 格式化货币
function formatCurrency(num) {
    return '¥' + formatNumber(num);
}

// 格式化百分比
function formatPercent(num) {
    return (num >= 0 ? '+' : '') + num.toFixed(2) + '%';
}

// 显示加载状态
function showLoading(element) {
    element.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>';
}

// 显示错误信息
function showError(element, message) {
    element.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle"></i> ${message}</div>`;
}

// 确认对话框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 表格排序功能
function sortTable(tableId, columnIndex, numeric = true) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        if (numeric) {
            return parseFloat(aVal.replace(/[^\d.-]/g, '')) - parseFloat(bVal.replace(/[^\d.-]/g, ''));
        }
        return aVal.localeCompare(bVal);
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// 导出表格为 CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        
        cols.forEach(col => {
            rowData.push('"' + col.textContent.trim().replace(/"/g, '""') + '"');
        });
        
        csv.push(rowData.join(','));
    });
    
    const csvContent = '\uFEFF' + csv.join('\n'); // BOM for Excel
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
}

// 打印页面
function printPage() {
    window.print();
}

// 响应式图表调整
function resizeCharts() {
    // 触发所有 Chart.js 图表的调整大小
    if (typeof Chart !== 'undefined') {
        Chart.instances.forEach(chart => {
            chart.resize();
        });
    }
    
    // 触发所有 ECharts 图表的调整大小
    if (typeof echarts !== 'undefined') {
        echarts.getInstanceByDom(document.getElementById('klineChart'))?.resize();
    }
}

// 监听窗口大小变化
window.addEventListener('resize', debounce(resizeCharts, 250));

// 监听页面可见性变化
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        // 页面重新可见时立即更新数据
        updateRealtimeData();
    }
});
