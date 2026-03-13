/**
 * Dialog 模态对话框组件
 * 参考 shadcn-ui Dialog 组件设计
 */

class Dialog {
    constructor(options = {}) {
        this.options = {
            title: options.title || '',
            content: options.content || '',
            showClose: options.showClose !== false,
            closeOnOverlay: options.closeOnOverlay !== false,
            closeOnEsc: options.closeOnEsc !== false,
            width: options.width || '520px',
            className: options.className || '',
            onOpen: options.onOpen || null,
            onClose: options.onClose || null,
            onConfirm: options.onConfirm || null,
            onCancel: options.onCancel || null,
            ...options
        };
        
        this.element = null;
        this.overlay = null;
        this.isOpen = false;
        
        this.init();
    }
    
    init() {
        this.createElement();
        this.bindEvents();
    }
    
    createElement() {
        // 创建遮罩层
        this.overlay = document.createElement('div');
        this.overlay.className = 'dialog-overlay';
        
        // 创建对话框容器
        this.element = document.createElement('div');
        this.element.className = `dialog ${this.options.className}`;
        this.element.style.width = this.options.width;
        this.element.setAttribute('role', 'dialog');
        this.element.setAttribute('aria-modal', 'true');
        
        // 构建对话框内容
        let html = '';
        
        // 头部
        if (this.options.title || this.options.showClose) {
            html += '<div class="dialog-header">';
            if (this.options.title) {
                html += `<h3 class="dialog-title">${this.options.title}</h3>`;
            }
            if (this.options.showClose) {
                html += '<button class="dialog-close" aria-label="关闭">&times;</button>';
            }
            html += '</div>';
        }
        
        // 内容区
        html += '<div class="dialog-content">';
        html += this.options.content;
        html += '</div>';
        
        // 底部按钮区
        if (this.options.showFooter !== false) {
            html += '<div class="dialog-footer">';
            if (this.options.showCancel !== false) {
                html += '<button class="btn btn-secondary dialog-cancel">取消</button>';
            }
            html += '<button class="btn btn-primary dialog-confirm">确定</button>';
            html += '</div>';
        }
        
        this.element.innerHTML = html;
        this.overlay.appendChild(this.element);
        document.body.appendChild(this.overlay);
    }
    
    bindEvents() {
        // 关闭按钮
        const closeBtn = this.element.querySelector('.dialog-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
        
        // 取消按钮
        const cancelBtn = this.element.querySelector('.dialog-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                if (this.options.onCancel) {
                    this.options.onCancel();
                }
                this.close();
            });
        }
        
        // 确认按钮
        const confirmBtn = this.element.querySelector('.dialog-confirm');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                if (this.options.onConfirm) {
                    this.options.onConfirm();
                }
                this.close();
            });
        }
        
        // 点击遮罩关闭
        if (this.options.closeOnOverlay) {
            this.overlay.addEventListener('click', (e) => {
                if (e.target === this.overlay) {
                    this.close();
                }
            });
        }
        
        // ESC键关闭
        if (this.options.closeOnEsc) {
            this.escHandler = (e) => {
                if (e.key === 'Escape' && this.isOpen) {
                    this.close();
                }
            };
        }
    }
    
    open() {
        if (this.isOpen) return;
        
        // 防止背景滚动
        document.body.style.overflow = 'hidden';
        
        // 显示对话框
        this.overlay.classList.add('active');
        this.element.classList.add('active');
        
        // 聚焦到对话框
        this.element.focus();
        
        // 添加ESC事件监听
        if (this.options.closeOnEsc) {
            document.addEventListener('keydown', this.escHandler);
        }
        
        this.isOpen = true;
        
        if (this.options.onOpen) {
            this.options.onOpen();
        }
        
        return this;
    }
    
    close() {
        if (!this.isOpen) return;
        
        // 移除active类触发关闭动画
        this.element.classList.remove('active');
        this.overlay.classList.remove('active');
        
        // 恢复背景滚动
        document.body.style.overflow = '';
        
        // 移除ESC事件监听
        if (this.options.closeOnEsc) {
            document.removeEventListener('keydown', this.escHandler);
        }
        
        this.isOpen = false;
        
        if (this.options.onClose) {
            this.options.onClose();
        }
        
        return this;
    }
    
    destroy() {
        this.close();
        if (this.overlay && this.overlay.parentNode) {
            this.overlay.parentNode.removeChild(this.overlay);
        }
    }
    
    // 静态方法：alert
    static alert(message, options = {}) {
        const dialog = new Dialog({
            title: options.title || '提示',
            content: `<p>${message}</p>`,
            showCancel: false,
            ...options
        });
        dialog.open();
        return dialog;
    }
    
    // 静态方法：confirm
    static confirm(message, options = {}) {
        return new Promise((resolve) => {
            const dialog = new Dialog({
                title: options.title || '确认',
                content: `<p>${message}</p>`,
                onConfirm: () => resolve(true),
                onCancel: () => resolve(false),
                ...options
            });
            dialog.open();
        });
    }
    
    // 静态方法：prompt
    static prompt(message, defaultValue = '', options = {}) {
        return new Promise((resolve) => {
            const dialog = new Dialog({
                title: options.title || '输入',
                content: `
                    <p>${message}</p>
                    <input type="text" class="form-control" value="${defaultValue}" id="prompt-input" style="margin-top: 12px;">
                `,
                onConfirm: () => {
                    const input = document.getElementById('prompt-input');
                    resolve(input ? input.value : null);
                },
                onCancel: () => resolve(null),
                ...options
            });
            dialog.open();
            // 聚焦输入框
            setTimeout(() => {
                const input = document.getElementById('prompt-input');
                if (input) input.focus();
            }, 100);
        });
    }
}

// 全局暴露
window.Dialog = Dialog;
