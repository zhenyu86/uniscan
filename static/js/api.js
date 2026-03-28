/**
 * UniScan Detection Platform - API Client
 * 统一的API请求封装
 */

const API = {
    baseURL: '/api/v1',

    /**
     * 发送请求
     */
    async request(method, url, data = null, options = {}) {
        const config = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(`${this.baseURL}${url}`, config);
            const result = await response.json();

            if (result.code === 401) {
                window.location.href = '/login';
                return null;
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * GET请求
     */
    get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.request('GET', fullUrl);
    },

    /**
     * POST请求
     */
    post(url, data) {
        return this.request('POST', url, data);
    },

    /**
     * PUT请求
     */
    put(url, data) {
        return this.request('PUT', url, data);
    },

    /**
     * DELETE请求
     */
    delete(url) {
        return this.request('DELETE', url);
    },

    /**
     * 上传文件
     */
    upload(url, formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    onProgress(percent);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(xhr.statusText));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Network Error'));
            });

            xhr.open('POST', `${this.baseURL}${url}`);
            xhr.send(formData);
        });
    }
};

/**
 * 认证API
 */
const AuthAPI = {
    login: (username, password, remember = false) => {
        return API.post('/auth/login', { username, password, remember });
    },

    logout: () => {
        return API.post('/auth/logout');
    },

    getUserInfo: () => {
        return API.get('/auth/info');
    },

    changePassword: (oldPassword, newPassword) => {
        return API.put('/auth/password', { old_password: oldPassword, new_password: newPassword });
    },

    updateProfile: (data) => {
        return API.put('/auth/profile', data);
    }
};

/**
 * 设备API
 */
const DeviceAPI = {
    getGroups: () => {
        return API.get('/devices/groups');
    },

    createGroup: (data) => {
        return API.post('/devices/groups', data);
    },

    updateGroup: (id, data) => {
        return API.put(`/devices/groups/${id}`, data);
    },

    deleteGroup: (id) => {
        return API.delete(`/devices/groups/${id}`);
    },

    getDevices: (params = {}) => {
        return API.get('/devices', params);
    },

    getDevice: (id) => {
        return API.get(`/devices/${id}`);
    },

    createDevice: (data) => {
        return API.post('/devices', data);
    },

    updateDevice: (id, data) => {
        return API.put(`/devices/${id}`, data);
    },

    deleteDevice: (id) => {
        return API.delete(`/devices/${id}`);
    },

    updateStatus: (id, status) => {
        return API.put(`/devices/${id}/status`, { status });
    }
};

/**
 * 检测API
 */
const DetectAPI = {
    uploadImage: (file, onProgress) => {
        const formData = new FormData();
        formData.append('file', file);
        return API.upload('/detect/upload/image', formData, onProgress);
    },

    uploadVideo: (file, onProgress) => {
        const formData = new FormData();
        formData.append('file', file);
        return API.upload('/detect/upload/video', formData, onProgress);
    },

    quickDetect: (file, params = {}, onProgress) => {
        const formData = new FormData();
        formData.append('file', file);
        Object.keys(params).forEach(key => {
            formData.append(key, params[key]);
        });
        return API.upload('/detect/quick', formData, onProgress);
    },

    createTask: (data) => {
        return API.post('/detect/task', data);
    },

    getTasks: (params = {}) => {
        return API.get('/detect/tasks', params);
    },

    getTask: (id) => {
        return API.get(`/detect/tasks/${id}`);
    },

    cancelTask: (id) => {
        return API.post(`/detect/tasks/${id}/cancel`);
    },

    getTaskResults: (id, params = {}) => {
        return API.get(`/detect/tasks/${id}/results`, params);
    },

    exportTaskResults: (id, format = 'json') => {
        return API.get(`/detect/tasks/${id}/export`, { format });
    },

    getUploads: (params = {}) => {
        return API.get('/detect/uploads', params);
    }
};

/**
 * 告警API
 */
const AlertAPI = {
    getAlerts: (params = {}) => {
        return API.get('/alerts', params);
    },

    getStats: () => {
        return API.get('/alerts/stats');
    },

    getRecent: (limit = 5) => {
        return API.get('/alerts/recent', { limit });
    },

    getAlert: (id) => {
        return API.get(`/alerts/${id}`);
    },

    handleAlert: (id, data) => {
        return API.post(`/alerts/${id}/handle`, data);
    },

    batchHandle: (alertIds, data) => {
        return API.post('/alerts/batch-handle', { alert_ids: alertIds, ...data });
    }
};

/**
 * 统计API
 */
const AnalyticsAPI = {
    getDashboard: () => {
        return API.get('/analytics/dashboard');
    },

    getDetectionTrend: (days = 7) => {
        return API.get('/analytics/detection-trend', { days });
    },

    getClassDistribution: (params = {}) => {
        return API.get('/analytics/class-distribution', params);
    },

    getAlertTrend: (days = 7) => {
        return API.get('/analytics/alert-trend', { days });
    },

    getHourlyStats: (params = {}) => {
        return API.get('/analytics/hourly-stats', params);
    },

    getDeviceStats: () => {
        return API.get('/analytics/device-stats');
    },

    getComparison: (period = 'week') => {
        return API.get('/analytics/comparison', { period });
    },

    triggerAggregate: (date) => {
        return API.post('/analytics/aggregate', { date });
    }
};

/**
 * 场景API
 */
const SceneAPI = {
    getScenes: () => {
        return API.get('/scenes');
    },

    getScene: (id) => {
        return API.get(`/scenes/${id}`);
    },

    createScene: (data) => {
        return API.post('/scenes', data);
    },

    updateScene: (id, data) => {
        return API.put(`/scenes/${id}`, data);
    },

    deleteScene: (id) => {
        return API.delete(`/scenes/${id}`);
    },

    cloneScene: (id, data) => {
        return API.post(`/scenes/${id}/clone`, data);
    },

    setDefault: (id) => {
        return API.post(`/scenes/${id}/set-default`);
    },

    getTemplates: (category = null) => {
        return API.get('/scenes/templates', category ? { category } : {});
    },

    getTemplate: (id) => {
        return API.get(`/scenes/templates/${id}`);
    },

    createFromTemplate: (templateId, data) => {
        return API.post(`/scenes/create-from-template/${templateId}`, data);
    }
};

/**
 * 规则API
 */
const RuleAPI = {
    getRules: (params = {}) => {
        return API.get('/rules', params);
    },

    getAllRules: (params = {}) => {
        return API.get('/rules/all', params);
    },

    getRule: (id) => {
        return API.get(`/rules/${id}`);
    },

    createRule: (data) => {
        return API.post('/rules', data);
    },

    updateRule: (id, data) => {
        return API.put(`/rules/${id}`, data);
    },

    deleteRule: (id) => {
        return API.delete(`/rules/${id}`);
    },

    toggleRule: (id) => {
        return API.post(`/rules/${id}/toggle`);
    },

    testRule: (data) => {
        return API.post('/rules/test', data);
    },

    getTypes: () => {
        return API.get('/rules/types');
    },

    getLevels: () => {
        return API.get('/rules/levels');
    }
};

/**
 * 设置API
 */
const SettingsAPI = {
    getUsers: (params = {}) => {
        return API.get('/settings/users', params);
    },

    getUser: (id) => {
        return API.get(`/settings/users/${id}`);
    },

    createUser: (data) => {
        return API.post('/settings/users', data);
    },

    updateUser: (id, data) => {
        return API.put(`/settings/users/${id}`, data);
    },

    deleteUser: (id) => {
        return API.delete(`/settings/users/${id}`);
    },

    resetPassword: (id, password) => {
        return API.post(`/settings/users/${id}/reset-password`, { password });
    },

    getModels: () => {
        return API.get('/settings/models');
    },

    getActiveModel: () => {
        return API.get('/settings/models/active');
    },

    activateModel: (id) => {
        return API.post(`/settings/models/${id}/activate`);
    },

    getConfigs: () => {
        return API.get('/settings/configs');
    },

    getConfig: (key) => {
        return API.get(`/settings/configs/${key}`);
    },

    updateConfigs: (configs) => {
        return API.put('/settings/configs', { configs });
    },

    getLogs: (params = {}) => {
        return API.get('/settings/logs', params);
    },

    getDashboards: (params = {}) => {
        return API.get('/settings/dashboards', params);
    },

    createDashboard: (data) => {
        return API.post('/settings/dashboards', data);
    },

    updateDashboard: (id, data) => {
        return API.put(`/settings/dashboards/${id}`, data);
    },

    deleteDashboard: (id) => {
        return API.delete(`/settings/dashboards/${id}`);
    }
};

/**
 * 工具函数
 */
const Utils = {
    /**
     * 格式化日期
     */
    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN');
    },

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * 显示Toast通知
     */
    showToast(message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    /**
     * 显示确认对话框
     */
    confirm(message, callback) {
        if (window.confirm(message)) {
            callback();
        }
    },

    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * 节流函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * 复制到剪贴板
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            Utils.showToast('已复制到剪贴板', 'success');
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    },

    /**
     * 下载文件
     */
    downloadFile(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
};

// 导出API对象
window.API = API;
window.AuthAPI = AuthAPI;
window.DeviceAPI = DeviceAPI;
window.DetectAPI = DetectAPI;
window.AlertAPI = AlertAPI;
window.AnalyticsAPI = AnalyticsAPI;
window.SceneAPI = SceneAPI;
window.RuleAPI = RuleAPI;
window.SettingsAPI = SettingsAPI;
window.Utils = Utils;
