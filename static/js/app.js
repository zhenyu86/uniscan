/**
 * UniScan Detection Platform - Main App
 * 主应用程序逻辑
 */

// 全局配置
const AppConfig = {
    autoRefreshInterval: 5000, // 自动刷新间隔（毫秒）
    pageSize: 20, // 默认分页大小
    maxUploadSize: 500 * 1024 * 1024 // 最大上传大小
};

// 当前用户信息
let currentUser = null;

/**
 * 初始化应用
 */
async function initApp() {
    // 检查登录状态
    try {
        const result = await AuthAPI.getUserInfo();
        if (result && result.code === 200) {
            currentUser = result.data;
            updateUserDisplay();
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Failed to get user info:', error);
    }

    // 初始化侧边栏
    initSidebar();

    // 初始化通知
    initNotifications();

    // 检查当前页面并高亮菜单
    highlightCurrentMenu();
}

/**
 * 更新用户显示
 */
function updateUserDisplay() {
    const avatarEl = document.querySelector('.user-avatar');
    const nameEl = document.querySelector('.user-name');
    const roleEl = document.querySelector('.user-role');

    if (currentUser) {
        if (avatarEl) {
            avatarEl.textContent = currentUser.real_name ? currentUser.real_name.charAt(0) : currentUser.username.charAt(0);
        }
        if (nameEl) {
            nameEl.textContent = currentUser.real_name || currentUser.username;
        }
        if (roleEl) {
            const roleMap = {
                'admin': '管理员',
                'manager': '场景管理员',
                'operator': '操作员',
                'viewer': '查看者'
            };
            roleEl.textContent = roleMap[currentUser.role] || currentUser.role;
        }
    }
}

/**
 * 初始化侧边栏
 */
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const collapseBtn = document.querySelector('.collapse-btn');

    // 检查本地存储的状态
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed && sidebar) {
        sidebar.classList.add('collapsed');
        if (mainContent) {
            mainContent.classList.add('expanded');
        }
    }

    // 折叠按钮点击事件
    if (collapseBtn) {
        collapseBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            if (mainContent) {
                mainContent.classList.toggle('expanded');
            }
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }

    // 移动端侧边栏切换
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }
}

/**
 * 高亮当前菜单
 */
function highlightCurrentMenu() {
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.sidebar-menu a');

    menuLinks.forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
}

/**
 * 初始化通知
 */
function initNotifications() {
    // 定期检查新告警
    setInterval(async () => {
        try {
            const result = await AlertAPI.getRecent(1);
            if (result && result.code === 200 && result.data.length > 0) {
                const latestAlert = result.data[0];
                updateNotificationBadge(latestAlert);
            }
        } catch (error) {
            console.error('Failed to check notifications:', error);
        }
    }, AppConfig.autoRefreshInterval);
}

/**
 * 更新通知徽章
 */
function updateNotificationBadge(alert) {
    const badge = document.querySelector('.notification-badge');
    if (badge && alert.status === 'pending') {
        badge.style.display = 'block';
    }
}

/**
 * 登出
 */
async function logout() {
    try {
        await AuthAPI.logout();
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout failed:', error);
        window.location.href = '/login';
    }
}

/**
 * 分页组件
 */
class Pagination {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.currentPage = options.currentPage || 1;
        this.totalPages = options.totalPages || 1;
        this.onPageChange = options.onPageChange || (() => {});
        this.render();
    }

    render() {
        if (!this.container) return;

        let html = '';

        // 上一页按钮
        html += `<button class="pagination-btn" ${this.currentPage <= 1 ? 'disabled' : ''} data-page="${this.currentPage - 1}">
            <i class="bi bi-chevron-left"></i>
        </button>`;

        // 页码按钮
        const maxButtons = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(this.totalPages, startPage + maxButtons - 1);

        if (endPage - startPage < maxButtons - 1) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        if (startPage > 1) {
            html += `<button class="pagination-btn" data-page="1">1</button>`;
            if (startPage > 2) {
                html += `<span class="pagination-ellipsis">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }

        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                html += `<span class="pagination-ellipsis">...</span>`;
            }
            html += `<button class="pagination-btn" data-page="${this.totalPages}">${this.totalPages}</button>`;
        }

        // 下一页按钮
        html += `<button class="pagination-btn" ${this.currentPage >= this.totalPages ? 'disabled' : ''} data-page="${this.currentPage + 1}">
            <i class="bi bi-chevron-right"></i>
        </button>`;

        this.container.innerHTML = html;

        // 绑定点击事件
        this.container.querySelectorAll('.pagination-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt(btn.dataset.page);
                if (!isNaN(page) && page >= 1 && page <= this.totalPages && page !== this.currentPage) {
                    this.currentPage = page;
                    this.onPageChange(page);
                    this.render();
                }
            });
        });
    }

    update(currentPage, totalPages) {
        this.currentPage = currentPage;
        this.totalPages = totalPages;
        this.render();
    }
}

/**
 * 表格排序
 */
class TableSorter {
    constructor(table) {
        this.table = typeof table === 'string' ? document.querySelector(table) : table;
        this.currentSort = { column: null, direction: 'asc' };
        this.init();
    }

    init() {
        if (!this.table) return;

        const headers = this.table.querySelectorAll('th[data-sortable]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => this.sort(header));
        });
    }

    sort(header) {
        const column = header.dataset.sortable;

        if (this.currentSort.column === column) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.column = column;
            this.currentSort.direction = 'asc';
        }

        // 触发排序事件
        const event = new CustomEvent('tablesort', {
            detail: { column: this.currentSort.column, direction: this.currentSort.direction }
        });
        this.table.dispatchEvent(event);
    }
}

/**
 * 模态框管理
 */
class Modal {
    constructor(id) {
        this.overlay = document.getElementById(id);
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.id = id;
            this.overlay.className = 'modal-overlay';
            document.body.appendChild(this.overlay);
        }
        this.bindEvents();
    }

    bindEvents() {
        // 点击背景关闭
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.hide();
            }
        });

        // 关闭按钮
        const closeBtn = this.overlay.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }
    }

    show() {
        this.overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    hide() {
        this.overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    setContent(html) {
        const modal = this.overlay.querySelector('.modal');
        if (modal) {
            modal.innerHTML = html;
        }
    }
}

/**
 * 加载状态管理
 */
function showLoading(container) {
    const el = typeof container === 'string' ? document.querySelector(container) : container;
    if (!el) return;

    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="spinner"></div>';
    el.style.position = 'relative';
    el.appendChild(overlay);
}

function hideLoading(container) {
    const el = typeof container === 'string' ? document.querySelector(container) : container;
    if (!el) return;

    const overlay = el.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * 空状态显示
 */
function showEmpty(container, message = '暂无数据', icon = 'bi-inbox') {
    const el = typeof container === 'string' ? document.querySelector(container) : container;
    if (!el) return;

    el.innerHTML = `
        <div class="empty-state">
            <i class="bi ${icon}"></i>
            <p>${message}</p>
        </div>
    `;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 只在非登录页面初始化
    if (!window.location.pathname.includes('/login')) {
        initApp();
    }
});

// 导出全局函数
window.Pagination = Pagination;
window.TableSorter = TableSorter;
window.Modal = Modal;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showEmpty = showEmpty;
window.logout = logout;
window.currentUser = currentUser;
window.AppConfig = AppConfig;
