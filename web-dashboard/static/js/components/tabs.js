/**
 * Tabs 标签页组件
 * 参考 shadcn-ui Tabs 组件设计
 */

class Tabs {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            variant: options.variant || 'default', // default, pills, buttons
            placement: options.placement || 'top', // top, left, right, bottom
            activeIndex: options.activeIndex || 0,
            lazy: options.lazy !== false,
            className: options.className || '',
            onChange: options.onChange || null,
            ...options
        };
        
        this.tabs = [];
        this.panels = [];
        this.activeTab = null;
        
        if (this.container) {
            this.init();
        }
    }
    
    init() {
        this.parseDOM();
        this.createStructure();
        this.bindEvents();
        this.activate(this.options.activeIndex);
    }
    
    parseDOM() {
        // 解析现有的 tab 和 panel
        const tabElements = this.container.querySelectorAll('[data-tab]');
        const panelElements = this.container.querySelectorAll('[data-tab-panel]');
        
        tabElements.forEach((tab, index) => {
            const panelId = tab.dataset.tab;
            const panel = this.container.querySelector(`[data-tab-panel="${panelId}"]`);
            
            this.tabs.push({
                id: panelId,
                element: tab,
                label: tab.textContent.trim(),
                disabled: tab.disabled || tab.dataset.disabled === 'true',
                closable: tab.dataset.closable === 'true'
            });
            
            if (panel) {
                this.panels.push({
                    id: panelId,
                    element: panel
                });
            }
        });
    }
    
    createStructure() {
        this.container.className = `tabs tabs-${this.options.variant} tabs-${this.options.placement} ${this.options.className}`;
        
        // 创建标签列表容器
        this.tabList = document.createElement('div');
        this.tabList.className = 'tabs-list';
        this.tabList.setAttribute('role', 'tablist');
        
        // 创建内容面板容器
        this.panelContainer = document.createElement('div');
        this.panelContainer.className = 'tabs-panels';
        
        // 清空容器
        this.container.innerHTML = '';
        
        // 根据位置决定插入顺序
        if (this.options.placement === 'bottom') {
            this.container.appendChild(this.panelContainer);
            this.container.appendChild(this.tabList);
        } else {
            this.container.appendChild(this.tabList);
            this.container.appendChild(this.panelContainer);
        }
        
        // 渲染标签
        this.renderTabs();
        this.renderPanels();
    }
    
    renderTabs() {
        this.tabList.innerHTML = '';
        
        this.tabs.forEach((tab, index) => {
            const button = document.createElement('button');
            button.className = `tabs-trigger ${tab.disabled ? 'disabled' : ''}`;
            button.setAttribute('role', 'tab');
            button.setAttribute('data-index', index);
            button.setAttribute('aria-selected', 'false');
            button.setAttribute('aria-controls', `panel-${tab.id}`);
            button.setAttribute('id', `tab-${tab.id}`);
            button.disabled = tab.disabled;
            
            // 标签内容
            let content = tab.label;
            if (tab.closable) {
                content += `<span class="tabs-close" data-close="${index}">&times;</span>`;
            }
            button.innerHTML = content;
            
            this.tabList.appendChild(button);
            tab.trigger = button;
        });
    }
    
    renderPanels() {
        this.panels.forEach(panel => {
            panel.element.className = 'tabs-panel';
            panel.element.setAttribute('role', 'tabpanel');
            panel.element.setAttribute('id', `panel-${panel.id}`);
            panel.element.setAttribute('aria-labelledby', `tab-${panel.id}`);
            panel.element.hidden = true;
            
            this.panelContainer.appendChild(panel.element);
        });
    }
    
    bindEvents() {
        // 标签点击事件
        this.tabList.addEventListener('click', (e) => {
            const trigger = e.target.closest('.tabs-trigger');
            if (!trigger || trigger.disabled) return;
            
            // 处理关闭按钮点击
            if (e.target.classList.contains('tabs-close')) {
                e.stopPropagation();
                const index = parseInt(e.target.dataset.close);
                this.closeTab(index);
                return;
            }
            
            const index = parseInt(trigger.dataset.index);
            this.activate(index);
        });
        
        // 键盘导航
        this.tabList.addEventListener('keydown', (e) => {
            const triggers = this.tabList.querySelectorAll('.tabs-trigger:not(.disabled)');
            const currentIndex = Array.from(triggers).findIndex(t => t === document.activeElement);
            
            switch (e.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                    e.preventDefault();
                    const nextIndex = currentIndex < triggers.length - 1 ? currentIndex + 1 : 0;
                    triggers[nextIndex]?.focus();
                    this.activate(parseInt(triggers[nextIndex].dataset.index));
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    const prevIndex = currentIndex > 0 ? currentIndex - 1 : triggers.length - 1;
                    triggers[prevIndex]?.focus();
                    this.activate(parseInt(triggers[prevIndex].dataset.index));
                    break;
                case 'Home':
                    e.preventDefault();
                    triggers[0]?.focus();
                    this.activate(parseInt(triggers[0].dataset.index));
                    break;
                case 'End':
                    e.preventDefault();
                    triggers[triggers.length - 1]?.focus();
                    this.activate(parseInt(triggers[triggers.length - 1].dataset.index));
                    break;
            }
        });
    }
    
    activate(index) {
        if (index < 0 || index >= this.tabs.length) return;
        if (this.tabs[index].disabled) return;
        
        const tab = this.tabs[index];
        const panel = this.panels.find(p => p.id === tab.id);
        
        // 更新标签状态
        this.tabs.forEach((t, i) => {
            const isActive = i === index;
            t.trigger.classList.toggle('active', isActive);
            t.trigger.setAttribute('aria-selected', isActive.toString());
        });
        
        // 更新面板状态
        this.panels.forEach(p => {
            p.element.hidden = p.id !== tab.id;
            if (p.id === tab.id && this.options.lazy) {
                p.element.classList.add('loaded');
            }
        });
        
        this.activeTab = tab;
        
        if (this.options.onChange) {
            this.options.onChange(index, tab, panel);
        }
        
        return this;
    }
    
    // 添加新标签
    addTab(label, content, options = {}) {
        const id = options.id || `tab-${Date.now()}`;
        const index = this.tabs.length;
        
        // 创建标签
        const tab = {
            id: id,
            label: label,
            disabled: options.disabled || false,
            closable: options.closable || false
        };
        this.tabs.push(tab);
        
        // 创建面板
        const panelElement = document.createElement('div');
        panelElement.innerHTML = content;
        const panel = {
            id: id,
            element: panelElement
        };
        this.panels.push(panel);
        
        // 重新渲染
        this.renderTabs();
        this.renderPanels();
        this.bindEvents();
        
        if (options.activate) {
            this.activate(index);
        }
        
        return index;
    }
    
    // 关闭标签
    closeTab(index) {
        if (index < 0 || index >= this.tabs.length) return;
        
        const wasActive = this.tabs[index].trigger.classList.contains('active');
        
        // 移除标签和面板
        this.tabs.splice(index, 1);
        this.panels.splice(index, 1);
        
        // 重新渲染
        this.renderTabs();
        this.renderPanels();
        this.bindEvents();
        
        // 如果关闭的是当前激活的标签，激活相邻标签
        if (wasActive && this.tabs.length > 0) {
            const newIndex = Math.min(index, this.tabs.length - 1);
            this.activate(newIndex);
        }
        
        return this;
    }
    
    // 禁用标签
    disableTab(index) {
        if (this.tabs[index]) {
            this.tabs[index].disabled = true;
            this.tabs[index].trigger.disabled = true;
            this.tabs[index].trigger.classList.add('disabled');
        }
        return this;
    }
    
    // 启用标签
    enableTab(index) {
        if (this.tabs[index]) {
            this.tabs[index].disabled = false;
            this.tabs[index].trigger.disabled = false;
            this.tabs[index].trigger.classList.remove('disabled');
        }
        return this;
    }
    
    // 获取当前激活的索引
    getActiveIndex() {
        return this.tabs.findIndex(t => t.trigger.classList.contains('active'));
    }
    
    // 销毁
    destroy() {
        this.container.innerHTML = '';
        this.container.className = '';
    }
}

// 全局暴露
window.Tabs = Tabs;
