/**
 * components.js
 * shadcn-ui 风格的组件库
 * 量化交易仪表盘专用
 */

// ===== Button 组件 =====
const Button = {
  /**
   * 创建 Button 组件
   * @param {Object} options - 配置选项
   * @param {string} options.variant - 变体: default, primary, secondary, ghost, danger
   * @param {string} options.size - 尺寸: sm, default, lg, icon
   * @param {string} options.text - 按钮文本
   * @param {string} options.icon - 图标类名 (Bootstrap Icons)
   * @param {Function} options.onClick - 点击事件处理
   * @param {boolean} options.disabled - 是否禁用
   * @param {string} options.className - 额外类名
   * @param {string} options.type - 按钮类型: button, submit, reset
   * @returns {HTMLButtonElement}
   */
  create(options = {}) {
    const {
      variant = 'default',
      size = 'default',
      text = '',
      icon = null,
      onClick = null,
      disabled = false,
      className = '',
      type = 'button'
    } = options;

    const btn = document.createElement('button');
    btn.type = type;
    btn.className = `btn-shadcn btn-shadcn-${variant}`;
    
    if (size !== 'default') {
      btn.classList.add(`btn-shadcn-${size}`);
    }
    
    if (className) {
      btn.classList.add(...className.split(' '));
    }
    
    if (disabled) {
      btn.disabled = true;
    }
    
    // 添加图标
    if (icon) {
      const iconEl = document.createElement('i');
      iconEl.className = icon;
      btn.appendChild(iconEl);
    }
    
    // 添加文本
    if (text) {
      const span = document.createElement('span');
      span.textContent = text;
      btn.appendChild(span);
    }
    
    // 绑定点击事件
    if (onClick && typeof onClick === 'function') {
      btn.addEventListener('click', onClick);
    }
    
    return btn;
  },

  /**
   * 快捷创建方法
   */
  primary(text, onClick, options = {}) {
    return this.create({ variant: 'primary', text, onClick, ...options });
  },

  secondary(text, onClick, options = {}) {
    return this.create({ variant: 'secondary', text, onClick, ...options });
  },

  ghost(text, onClick, options = {}) {
    return this.create({ variant: 'ghost', text, onClick, ...options });
  },

  danger(text, onClick, options = {}) {
    return this.create({ variant: 'danger', text, onClick, ...options });
  }
};

// ===== Card 组件 =====
const Card = {
  /**
   * 创建 Card 组件
   * @param {Object} options - 配置选项
   * @param {string} options.title - 卡片标题
   * @param {string} options.description - 卡片描述
   * @param {HTMLElement|string} options.content - 卡片内容
   * @param {HTMLElement|Array} options.footer - 卡片底部元素
   * @param {string} options.variant - 变体: default, elevated, outline
   * @param {string} options.className - 额外类名
   * @returns {HTMLElement}
   */
  create(options = {}) {
    const {
      title = null,
      description = null,
      content = null,
      footer = null,
      variant = 'default',
      className = ''
    } = options;

    const card = document.createElement('div');
    card.className = `card-shadcn card-shadcn-${variant}`;
    
    if (className) {
      card.classList.add(...className.split(' '));
    }

    // Header
    if (title || description) {
      const header = document.createElement('div');
      header.className = 'card-shadcn-header';
      
      if (title) {
        const titleEl = document.createElement('h3');
        titleEl.className = 'card-shadcn-title';
        titleEl.textContent = title;
        header.appendChild(titleEl);
      }
      
      if (description) {
        const descEl = document.createElement('p');
        descEl.className = 'card-shadcn-description';
        descEl.textContent = description;
        header.appendChild(descEl);
      }
      
      card.appendChild(header);
    }

    // Content
    if (content) {
      const contentEl = document.createElement('div');
      contentEl.className = 'card-shadcn-content';
      
      if (typeof content === 'string') {
        contentEl.innerHTML = content;
      } else {
        contentEl.appendChild(content);
      }
      
      card.appendChild(contentEl);
    }

    // Footer
    if (footer) {
      const footerEl = document.createElement('div');
      footerEl.className = 'card-shadcn-footer';
      
      if (Array.isArray(footer)) {
        footer.forEach(el => footerEl.appendChild(el));
      } else {
        footerEl.appendChild(footer);
      }
      
      card.appendChild(footerEl);
    }

    return card;
  },

  /**
   * 创建统计卡片 (用于仪表盘)
   * @param {Object} options - 配置选项
   * @param {string} options.label - 标签
   * @param {string} options.value - 数值
   * @param {string} options.change - 变化值
   * @param {boolean} options.isPositive - 是否为正变化
   * @param {string} options.icon - 图标类名
   * @returns {HTMLElement}
   */
  stat(options = {}) {
    const { label, value, change, isPositive = true, icon = null } = options;

    const content = document.createElement('div');
    content.innerHTML = `
      <div class="d-flex align-items-center justify-content-between">
        <div>
          <p class="text-muted mb-1" style="font-size: 0.875rem;">${label}</p>
          <h2 class="mb-0" style="font-size: 1.875rem; font-weight: 700;">${value}</h2>
        </div>
        ${icon ? `<div class="p-2 rounded" style="background: hsl(var(--primary) / 0.1);"><i class="${icon}" style="color: hsl(var(--primary)); font-size: 1.5rem;"></i></div>` : ''}
      </div>
      ${change ? `<div class="mt-2"><span class="badge-shadcn badge-shadcn-${isPositive ? 'success' : 'danger'}">${isPositive ? '↑' : '↓'} ${change}</span></div>` : ''}
    `;

    return this.create({ content, variant: 'elevated' });
  }
};

// ===== Badge 组件 =====
const Badge = {
  /**
   * 创建 Badge 组件
   * @param {Object} options - 配置选项
   * @param {string} options.text - 徽章文本
   * @param {string} options.variant - 变体: default, secondary, outline, ghost, success, danger, warning, info
   * @param {string} options.className - 额外类名
   * @returns {HTMLElement}
   */
  create(options = {}) {
    const { text = '', variant = 'default', className = '' } = options;

    const badge = document.createElement('span');
    badge.className = `badge-shadcn badge-shadcn-${variant}`;
    badge.textContent = text;
    
    if (className) {
      badge.classList.add(...className.split(' '));
    }

    return badge;
  },

  /**
   * 快捷创建方法
   */
  success(text, options = {}) {
    return this.create({ text, variant: 'success', ...options });
  },

  danger(text, options = {}) {
    return this.create({ text, variant: 'danger', ...options });
  },

  warning(text, options = {}) {
    return this.create({ text, variant: 'warning', ...options });
  },

  info(text, options = {}) {
    return this.create({ text, variant: 'info', ...options });
  }
};

// ===== Table 组件 =====
const Table = {
  /**
   * 创建 Table 组件
   * @param {Object} options - 配置选项
   * @param {Array} options.columns - 列定义 [{key, title, render?, width?, align?}]
   * @param {Array} options.data - 数据数组
   * @param {string} options.variant - 变体: default, striped, compact
   * @param {string} options.className - 额外类名
   * @param {Function} options.onRowClick - 行点击事件
   * @param {Function} options.rowClassName - 行类名生成函数
   * @returns {HTMLElement}
   */
  create(options = {}) {
    const {
      columns = [],
      data = [],
      variant = 'default',
      className = '',
      onRowClick = null,
      rowClassName = null
    } = options;

    const container = document.createElement('div');
    container.className = 'table-shadcn-container';

    const table = document.createElement('table');
    table.className = `table-shadcn table-shadcn-${variant}`;
    
    if (className) {
      table.classList.add(...className.split(' '));
    }

    // 表头
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    columns.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col.title || col.key;
      
      if (col.width) {
        th.style.width = col.width;
      }
      
      if (col.align) {
        th.style.textAlign = col.align;
      }
      
      headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // 表体
    const tbody = document.createElement('tbody');
    
    data.forEach((row, index) => {
      const tr = document.createElement('tr');
      
      if (onRowClick) {
        tr.style.cursor = 'pointer';
        tr.addEventListener('click', () => onRowClick(row, index));
      }
      
      if (rowClassName) {
        const extraClass = rowClassName(row, index);
        if (extraClass) {
          tr.classList.add(...extraClass.split(' '));
        }
      }
      
      columns.forEach(col => {
        const td = document.createElement('td');
        
        if (col.align) {
          td.style.textAlign = col.align;
        }
        
        // 自定义渲染或默认显示
        if (col.render && typeof col.render === 'function') {
          const rendered = col.render(row[col.key], row, index);
          if (typeof rendered === 'string') {
            td.innerHTML = rendered;
          } else if (rendered instanceof HTMLElement) {
            td.appendChild(rendered);
          }
        } else {
          td.textContent = row[col.key] !== undefined ? row[col.key] : '';
        }
        
        tr.appendChild(td);
      });
      
      tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    container.appendChild(table);

    return container;
  },

  /**
   * 创建带分页的表格
   * @param {Object} options - 配置选项
   * @param {number} options.pageSize - 每页条数
   * @param {number} options.currentPage - 当前页
   * @returns {Object} { element, updateData, setPage }
   */
  withPagination(options = {}) {
    const { pageSize = 10, currentPage = 1, ...tableOptions } = options;
    
    let currentData = [];
    let currentPageNum = currentPage;
    
    const wrapper = document.createElement('div');
    
    const tableContainer = document.createElement('div');
    wrapper.appendChild(tableContainer);
    
    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'd-flex justify-content-between align-items-center mt-3';
    paginationContainer.style.padding = '0 0.5rem';
    wrapper.appendChild(paginationContainer);

    function renderTable() {
      const start = (currentPageNum - 1) * pageSize;
      const end = start + pageSize;
      const pageData = currentData.slice(start, end);
      
      const table = Table.create({
        ...tableOptions,
        data: pageData
      });
      
      tableContainer.innerHTML = '';
      tableContainer.appendChild(table);
      
      renderPagination();
    }

    function renderPagination() {
      const totalPages = Math.ceil(currentData.length / pageSize);
      
      paginationContainer.innerHTML = `
        <span class="text-muted" style="font-size: 0.875rem;">
          显示 ${Math.min((currentPageNum - 1) * pageSize + 1, currentData.length)} - ${Math.min(currentPageNum * pageSize, currentData.length)} 
          共 ${currentData.length} 条
        </span>
        <div class="d-flex gap-2">
          <button class="btn-shadcn btn-shadcn-ghost btn-shadcn-sm" ${currentPageNum <= 1 ? 'disabled' : ''} id="btn-prev">
            <i class="bi bi-chevron-left"></i>
          </button>
          <span class="d-flex align-items-center px-2" style="font-size: 0.875rem;">
            ${currentPageNum} / ${totalPages || 1}
          </span>
          <button class="btn-shadcn btn-shadcn-ghost btn-shadcn-sm" ${currentPageNum >= totalPages ? 'disabled' : ''} id="btn-next">
            <i class="bi bi-chevron-right"></i>
          </button>
        </div>
      `;
      
      const prevBtn = paginationContainer.querySelector('#btn-prev');
      const nextBtn = paginationContainer.querySelector('#btn-next');
      
      if (prevBtn && !prevBtn.disabled) {
        prevBtn.addEventListener('click', () => {
          if (currentPageNum > 1) {
            currentPageNum--;
            renderTable();
          }
        });
      }
      
      if (nextBtn && !nextBtn.disabled) {
        nextBtn.addEventListener('click', () => {
          if (currentPageNum < totalPages) {
            currentPageNum++;
            renderTable();
          }
        });
      }
    }

    return {
      element: wrapper,
      updateData(data) {
        currentData = data;
        currentPageNum = 1;
        renderTable();
      },
      setPage(page) {
        currentPageNum = page;
        renderTable();
      }
    };
  }
};

// ===== Input 组件 =====
const Input = {
  /**
   * 创建 Input 组件
   * @param {Object} options - 配置选项
   * @param {string} options.type - 输入类型
   * @param {string} options.placeholder - 占位符
   * @param {string} options.value - 默认值
   * @param {Function} options.onChange - 变化事件
   * @param {Function} options.onEnter - 回车事件
   * @param {boolean} options.disabled - 是否禁用
   * @param {string} options.className - 额外类名
   * @returns {HTMLInputElement}
   */
  create(options = {}) {
    const {
      type = 'text',
      placeholder = '',
      value = '',
      onChange = null,
      onEnter = null,
      disabled = false,
      className = ''
    } = options;

    const input = document.createElement('input');
    input.type = type;
    input.className = 'input-shadcn';
    input.placeholder = placeholder;
    input.value = value;
    
    if (disabled) {
      input.disabled = true;
    }
    
    if (className) {
      input.classList.add(...className.split(' '));
    }
    
    if (onChange) {
      input.addEventListener('input', (e) => onChange(e.target.value, e));
    }
    
    if (onEnter) {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          onEnter(e.target.value, e);
        }
      });
    }
    
    return input;
  }
};

// ===== Toast 通知组件 =====
const Toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.style.cssText = `
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      `;
      document.body.appendChild(this.container);
    }
  },

  /**
   * 显示 Toast 通知
   * @param {Object} options - 配置选项
   * @param {string} options.message - 消息内容
   * @param {string} options.type - 类型: success, error, warning, info
   * @param {number} options.duration - 显示时长(ms)
   */
  show(options = {}) {
    this.init();
    
    const {
      message = '',
      type = 'info',
      duration = 3000
    } = options;

    const icons = {
      success: 'bi-check-circle-fill',
      error: 'bi-x-circle-fill',
      warning: 'bi-exclamation-triangle-fill',
      info: 'bi-info-circle-fill'
    };

    const colors = {
      success: 'hsl(var(--trade-up))',
      error: 'hsl(var(--trade-down))',
      warning: 'hsl(38 92% 50%)',
      info: 'hsl(217 91% 60%)'
    };

    const toast = document.createElement('div');
    toast.style.cssText = `
      background: hsl(var(--card));
      border: 1px solid hsl(var(--border));
      border-radius: var(--radius);
      padding: 1rem 1.25rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      min-width: 300px;
      animation: slide-in 0.3s ease-out;
    `;
    toast.innerHTML = `
      <i class="bi ${icons[type]}" style="color: ${colors[type]}; font-size: 1.25rem;"></i>
      <span style="color: hsl(var(--foreground)); font-size: 0.875rem;">${message}</span>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'fade-in 0.3s ease-out reverse';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  success(message, duration) {
    this.show({ message, type: 'success', duration });
  },

  error(message, duration) {
    this.show({ message, type: 'error', duration });
  },

  warning(message, duration) {
    this.show({ message, type: 'warning', duration });
  },

  info(message, duration) {
    this.show({ message, type: 'info', duration });
  }
};

// ===== 加载状态组件 =====
const Loading = {
  /**
   * 创建加载指示器
   * @param {Object} options - 配置选项
   * @param {string} options.size - 尺寸: sm, default, lg
   * @param {string} options.text - 加载文本
   * @returns {HTMLElement}
   */
  spinner(options = {}) {
    const { size = 'default', text = null } = options;
    
    const sizes = {
      sm: '1rem',
      default: '1.5rem',
      lg: '2rem'
    };

    const wrapper = document.createElement('div');
    wrapper.style.cssText = `
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
    `;
    
    const spinner = document.createElement('div');
    spinner.style.cssText = `
      width: ${sizes[size]};
      height: ${sizes[size]};
      border: 2px solid hsl(var(--border));
      border-top-color: hsl(var(--primary));
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    `;
    
    wrapper.appendChild(spinner);
    
    if (text) {
      const textEl = document.createElement('span');
      textEl.style.cssText = 'color: hsl(var(--muted-foreground)); font-size: 0.875rem;';
      textEl.textContent = text;
      wrapper.appendChild(textEl);
    }
    
    // 添加旋转动画
    if (!document.getElementById('loading-animation')) {
      const style = document.createElement('style');
      style.id = 'loading-animation';
      style.textContent = `
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `;
      document.head.appendChild(style);
    }
    
    return wrapper;
  },

  /**
   * 创建骨架屏
   * @param {Object} options - 配置选项
   * @param {number} options.lines - 行数
   * @param {boolean} options.avatar - 是否显示头像占位
   * @returns {HTMLElement}
   */
  skeleton(options = {}) {
    const { lines = 3, avatar = false } = options;
    
    const wrapper = document.createElement('div');
    wrapper.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      width: 100%;
    `;
    
    if (avatar) {
      const avatarEl = document.createElement('div');
      avatarEl.style.cssText = `
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        background: linear-gradient(90deg, hsl(var(--muted)) 25%, hsl(var(--muted)) / 0.5 50%, hsl(var(--muted)) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
      `;
      wrapper.appendChild(avatarEl);
    }
    
    for (let i = 0; i < lines; i++) {
      const line = document.createElement('div');
      line.style.cssText = `
        height: 0.875rem;
        border-radius: 0.25rem;
        background: linear-gradient(90deg, hsl(var(--muted)) 25%, hsl(var(--muted) / 0.5) 50%, hsl(var(--muted)) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        width: ${i === lines - 1 ? '60%' : '100%'};
      `;
      wrapper.appendChild(line);
    }
    
    // 添加闪烁动画
    if (!document.getElementById('skeleton-animation')) {
      const style = document.createElement('style');
      style.id = 'skeleton-animation';
      style.textContent = `
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `;
      document.head.appendChild(style);
    }
    
    return wrapper;
  }
};

// ===== 导出组件 =====
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Button, Card, Badge, Table, Input, Toast, Loading };
}

// 浏览器环境下挂载到 window
if (typeof window !== 'undefined') {
  window.ShadcnUI = { Button, Card, Badge, Table, Input, Toast, Loading };
}
