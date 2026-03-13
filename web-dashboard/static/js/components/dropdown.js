/**
 * Dropdown 下拉菜单组件
 * 参考 shadcn-ui DropdownMenu 组件设计
 */

class Dropdown {
    constructor(trigger, options = {}) {
        this.trigger = typeof trigger === 'string' ? document.querySelector(trigger) : trigger;
        this.options = {
            placement: options.placement || 'bottom-start', // bottom-start, bottom-end, top-start, top-end
            trigger: options.trigger || 'click', // click, hover
            closeOnClick: options.closeOnClick !== false,
            closeOnOutside: options.closeOnOutside !== false,
            menuItems: options.menuItems || [],
            className: options.className || '',
            onOpen: options.onOpen || null,
            onClose: options.onClose || null,
            onSelect: options.onSelect || null,
            ...options
        };
        
        this.menu = null;
        this.isOpen = false;
        this.hoverTimeout = null;
        
        if (this.trigger) {
            this.init();
        }
    }
    
    init() {
        this.createMenu();
        this.bindEvents();
    }
    
    createMenu() {
        this.menu = document.createElement('div');
        this.menu.className = `dropdown-menu ${this.options.className}`;
        this.menu.setAttribute('role', 'menu');
        
        // 构建菜单内容
        this.renderMenuItems();
        
        document.body.appendChild(this.menu);
    }
    
    renderMenuItems() {
        if (!this.options.menuItems.length) return;
        
        let html = '';
        this.options.menuItems.forEach((item, index) => {
            if (item.type === 'divider') {
                html += '<div class="dropdown-divider"></div>';
            } else if (item.type === 'header') {
                html += `<div class="dropdown-header">${item.label}</div>`;
            } else {
                const disabled = item.disabled ? 'disabled' : '';
                const icon = item.icon ? `<i class="ti ti-${item.icon}"></i>` : '';
                const shortcut = item.shortcut ? `<span class="dropdown-shortcut">${item.shortcut}</span>` : '';
                
                html += `
                    <button class="dropdown-item ${disabled}" role="menuitem" data-index="${index}">
                        ${icon}
                        <span class="dropdown-item-label">${item.label}</span>
                        ${shortcut}
                    </button>
                `;
            }
        });
        
        this.menu.innerHTML = html;
        
        // 绑定菜单项点击事件
        this.menu.querySelectorAll('.dropdown-item:not(.disabled)').forEach(item => {
            item.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                const menuItem = this.options.menuItems[index];
                
                if (this.options.onSelect) {
                    this.options.onSelect(menuItem, index);
                }
                
                if (menuItem.onClick) {
                    menuItem.onClick(menuItem, index);
                }
                
                if (this.options.closeOnClick) {
                    this.close();
                }
            });
        });
    }
    
    bindEvents() {
        // 触发器事件
        if (this.options.trigger === 'click') {
            this.trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggle();
            });
        } else if (this.options.trigger === 'hover') {
            this.trigger.addEventListener('mouseenter', () => {
                clearTimeout(this.hoverTimeout);
                this.open();
            });
            
            this.trigger.addEventListener('mouseleave', () => {
                this.hoverTimeout = setTimeout(() => {
                    if (!this.menu.matches(':hover')) {
                        this.close();
                    }
                }, 150);
            });
            
            this.menu.addEventListener('mouseenter', () => {
                clearTimeout(this.hoverTimeout);
            });
            
            this.menu.addEventListener('mouseleave', () => {
                this.hoverTimeout = setTimeout(() => {
                    this.close();
                }, 150);
            });
        }
        
        // 点击外部关闭
        if (this.options.closeOnOutside) {
            document.addEventListener('click', (e) => {
                if (this.isOpen && !this.trigger.contains(e.target) && !this.menu.contains(e.target)) {
                    this.close();
                }
            });
        }
        
        // 键盘导航
        this.menu.addEventListener('keydown', (e) => {
            const items = this.menu.querySelectorAll('.dropdown-item:not(.disabled)');
            const currentIndex = Array.from(items).findIndex(item => item === document.activeElement);
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
                    items[nextIndex]?.focus();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                    items[prevIndex]?.focus();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.close();
                    this.trigger.focus();
                    break;
                case 'Enter':
                    if (currentIndex >= 0) {
                        items[currentIndex].click();
                    }
                    break;
            }
        });
        
        // 窗口大小改变时重新定位
        window.addEventListener('resize', () => {
            if (this.isOpen) {
                this.position();
            }
        });
        
        // 滚动时关闭
        window.addEventListener('scroll', () => {
            if (this.isOpen) {
                this.close();
            }
        }, true);
    }
    
    position() {
        const triggerRect = this.trigger.getBoundingClientRect();
        const menuRect = this.menu.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let top, left;
        
        // 计算位置
        switch (this.options.placement) {
            case 'bottom-start':
                top = triggerRect.bottom + 4;
                left = triggerRect.left;
                break;
            case 'bottom-end':
                top = triggerRect.bottom + 4;
                left = triggerRect.right - menuRect.width;
                break;
            case 'top-start':
                top = triggerRect.top - menuRect.height - 4;
                left = triggerRect.left;
                break;
            case 'top-end':
                top = triggerRect.top - menuRect.height - 4;
                left = triggerRect.right - menuRect.width;
                break;
            default:
                top = triggerRect.bottom + 4;
                left = triggerRect.left;
        }
        
        // 边界检测和调整
        if (left + menuRect.width > viewportWidth) {
            left = viewportWidth - menuRect.width - 8;
        }
        if (left < 8) {
            left = 8;
        }
        if (top + menuRect.height > viewportHeight) {
            top = triggerRect.top - menuRect.height - 4;
        }
        if (top < 8) {
            top = triggerRect.bottom + 4;
        }
        
        this.menu.style.top = `${top + window.scrollY}px`;
        this.menu.style.left = `${left + window.scrollX}px`;
    }
    
    open() {
        if (this.isOpen) return;
        
        this.position();
        this.menu.classList.add('active');
        this.trigger.setAttribute('aria-expanded', 'true');
        this.isOpen = true;
        
        if (this.options.onOpen) {
            this.options.onOpen();
        }
        
        // 聚焦第一个菜单项
        setTimeout(() => {
            const firstItem = this.menu.querySelector('.dropdown-item:not(.disabled)');
            if (firstItem) firstItem.focus();
        }, 50);
        
        return this;
    }
    
    close() {
        if (!this.isOpen) return;
        
        this.menu.classList.remove('active');
        this.trigger.setAttribute('aria-expanded', 'false');
        this.isOpen = false;
        
        if (this.options.onClose) {
            this.options.onClose();
        }
        
        return this;
    }
    
    toggle() {
        return this.isOpen ? this.close() : this.open();
    }
    
    destroy() {
        this.close();
        if (this.menu && this.menu.parentNode) {
            this.menu.parentNode.removeChild(this.menu);
        }
    }
    
    // 更新菜单项
    updateMenuItems(items) {
        this.options.menuItems = items;
        this.renderMenuItems();
    }
}

// 全局暴露
window.Dropdown = Dropdown;
