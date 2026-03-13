/**
 * Toast 消息提示组件
 * 参考 shadcn-ui Toast 组件设计
 */

class Toast {
    constructor(options = {}) {
        this.options = {
            type: options.type || 'info', // success, error, warning, info
            title: options.title || '',
            message: options.message || '',
            duration: options.duration !== undefined ? options.duration : 5000,
            showClose: options.showClose !== false,
            showProgress: options.showProgress !== false,
            position: options.position || 'top-right', // top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
            onClose: options.onClose || null,
            onClick: options.onClick || null,
            ...options
        };
        
        this.element = null;
        this.progressBar = null;
        this.closeTimeout = null;
        this.startTime = null;
        this.remainingTime = this.options.duration;
        this.isPaused = false;
        
        this.init();
    }
    
    init() {
        this.createElement();
        this.bindEvents();
        this.startTimer();
    }
    
    createElement() {
        // 获取或创建容器
        this.container = this.getContainer();
        
        // 创建 toast 元素
        this.element = document.createElement('div');
        this.element.className = `toast toast-${this.options.type}`;
        this.element.setAttribute('role', 'alert');
        
        // 图标
        const iconMap = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-triangle',
            info: 'info-circle'
        };
        const icon = iconMap[this.options.type] || 'info-circle';
        
        // 构建内容
        let html = '';
        html += `<div class="toast-icon"><i class="ti ti-${icon}"></i></div>`;
        html += '<div class="toast-content">';
        
        if (this.options.title) {
            html += `<div class="toast-title">${this.options.title}</div>`;
        }
        if (this.options.message) {
            html += `<div class="toast-message">${this.options.message}</div>`;
        }
        
        html += '</div>';
        
        if (this.options.showClose) {
            html += '<button class="toast-close" aria-label="关闭">&times;</button>';
        }
        
        if (this.options.showProgress && this.options.duration > 0) {
            html += '<div class="toast-progress"><div class="toast-progress-bar"></div></div>';
        }
        
        this.element.innerHTML = html;
        this.container.appendChild(this.element);
        
        // 获取进度条元素
        if (this.options.showProgress) {
            this.progressBar = this.element.querySelector('.toast-progress-bar');
        }
        
        // 触发动画
        requestAnimationFrame(() => {
            this.element.classList.add('active');
        });
    }
    
    getContainer() {
        const position = this.options.position;
        let container = document.querySelector(`.toast-container[data-position="${position}"]`);
        
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            container.setAttribute('data-position', position);
            document.body.appendChild(container);
        }
        
        return container;
    }
    
    bindEvents() {
        // 关闭按钮
        const closeBtn = this.element.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.close();
            });
        }
        
        // 点击事件
        if (this.options.onClick) {
            this.element.addEventListener('click', (e) => {
                if (!e.target.closest('.toast-close')) {
                    this.options.onClick(this);
                }
            });
            this.element.style.cursor = 'pointer';
        }
        
        // 鼠标悬停暂停
        this.element.addEventListener('mouseenter', () => {
            this.pause();
        });
        
        this.element.addEventListener('mouseleave', () => {
            this.resume();
        });
    }
    
    startTimer() {
        if (this.options.duration <= 0) return;
        
        this.startTime = Date.now();
        
        this.closeTimeout = setTimeout(() => {
            this.close();
        }, this.remainingTime);
        
        // 进度条动画
        if (this.progressBar) {
            this.progressBar.style.transition = `width ${this.remainingTime}ms linear`;
            requestAnimationFrame(() => {
                this.progressBar.style.width = '0%';
            });
        }
    }
    
    pause() {
        if (this.isPaused || this.options.duration <= 0) return;
        
        this.isPaused = true;
        clearTimeout(this.closeTimeout);
        
        // 计算剩余时间
        const elapsed = Date.now() - this.startTime;
        this.remainingTime -= elapsed;
        
        // 暂停进度条
        if (this.progressBar) {
            const computedStyle = window.getComputedStyle(this.progressBar);
            const width = computedStyle.getPropertyValue('width');
            this.progressBar.style.transition = 'none';
            this.progressBar.style.width = width;
        }
    }
    
    resume() {
        if (!this.isPaused || this.options.duration <= 0) return;
        
        this.isPaused = false;
        this.startTime = Date.now();
        
        this.closeTimeout = setTimeout(() => {
            this.close();
        }, this.remainingTime);
        
        // 恢复进度条
        if (this.progressBar) {
            this.progressBar.style.transition = `width ${this.remainingTime}ms linear`;
            this.progressBar.style.width = '0%';
        }
    }
    
    close() {
        if (this.closeTimeout) {
            clearTimeout(this.closeTimeout);
        }
        
        this.element.classList.remove('active');
        this.element.classList.add('closing');
        
        setTimeout(() => {
            if (this.element && this.element.parentNode) {
                this.element.parentNode.removeChild(this.element);
            }
            
            // 清理空容器
            const container = document.querySelector(`.toast-container[data-position="${this.options.position}"]`);
            if (container && container.children.length === 0) {
                container.parentNode.removeChild(container);
            }
            
            if (this.options.onClose) {
                this.options.onClose(this);
            }
        }, 300);
    }
    
    // 静态方法：显示成功消息
    static success(message, options = {}) {
        return new Toast({
            type: 'success',
            message: message,
            ...options
        });
    }
    
    // 静态方法：显示错误消息
    static error(message, options = {}) {
        return new Toast({
            type: 'error',
            message: message,
            duration: options.duration || 8000, // 错误消息显示更久
            ...options
        });
    }
    
    // 静态方法：显示警告消息
    static warning(message, options = {}) {
        return new Toast({
            type: 'warning',
            message: message,
            ...options
        });
    }
    
    // 静态方法：显示信息消息
    static info(message, options = {}) {
        return new Toast({
            type: 'info',
            message: message,
            ...options
        });
    }
}

// Toast 管理器
class ToastManager {
    constructor() {
        this.toasts = [];
        this.maxToasts = 5;
        this.defaultPosition = 'top-right';
    }
    
    show(options) {
        // 限制最大数量
        if (this.toasts.length >= this.maxToasts) {
            this.toasts[0].close();
            this.toasts.shift();
        }
        
        const toast = new Toast({
            position: this.defaultPosition,
            ...options,
            onClose: (t) => {
                this.remove(t);
                if (options.onClose) options.onClose(t);
            }
        });
        
        this.toasts.push(toast);
        return toast;
    }
    
    success(message, options = {}) {
        return this.show({ type: 'success', message, ...options });
    }
    
    error(message, options = {}) {
        return this.show({ type: 'error', message, ...options });
    }
    
    warning(message, options = {}) {
        return this.show({ type: 'warning', message, ...options });
    }
    
    info(message, options = {}) {
        return this.show({ type: 'info', message, ...options });
    }
    
    remove(toast) {
        const index = this.toasts.indexOf(toast);
        if (index > -1) {
            this.toasts.splice(index, 1);
        }
    }
    
    clearAll() {
        this.toasts.forEach(toast => toast.close());
        this.toasts = [];
    }
}

// 创建全局 toast 管理器
window.toast = new ToastManager();
window.Toast = Toast;
