// ===== API Client for Admin Dashboard =====

class APIClient {
    constructor() {
        this.baseURL = '/api';
        this.token = localStorage.getItem('admin_token');
        this.refreshToken = localStorage.getItem('admin_refresh_token');
    }

    // Set authentication token
    setToken(token, refreshToken = null) {
        this.token = token;
        localStorage.setItem('admin_token', token);
        
        if (refreshToken) {
            this.refreshToken = refreshToken;
            localStorage.setItem('admin_refresh_token', refreshToken);
        }
    }

    // Clear authentication
    clearAuth() {
        this.token = null;
        this.refreshToken = null;
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_refresh_token');
    }

    // Get default headers
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // Handle API response
    async handleResponse(response) {
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            // Handle authentication errors
            if (response.status === 401) {
                if (this.refreshToken) {
                    const refreshed = await this.refreshAuthToken();
                    if (refreshed) {
                        // Retry the original request
                        return { success: false, retry: true };
                    }
                }
                
                this.clearAuth();
                window.location.href = '/admin/login';
                return { success: false, error: 'Authentication required' };
            }

            throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        return { success: true, data };
    }

    // Refresh authentication token
    async refreshAuthToken() {
        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.setToken(data.access_token, data.refresh_token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }

        return false;
    }

    // Generic request method
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: method.toUpperCase(),
            headers: this.getHeaders(),
            ...options
        };

        if (data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);
            const result = await this.handleResponse(response);

            // Retry once if token was refreshed
            if (result.retry) {
                config.headers = this.getHeaders();
                const retryResponse = await fetch(url, config);
                return await this.handleResponse(retryResponse);
            }

            return result;
        } catch (error) {
            console.error(`API ${method} ${endpoint} failed:`, error);
            return {
                success: false,
                error: error.message || 'Network error occurred'
            };
        }
    }

    // HTTP methods
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request('GET', url);
    }

    async post(endpoint, data) {
        return this.request('POST', endpoint, data);
    }

    async put(endpoint, data) {
        return this.request('PUT', endpoint, data);
    }

    async patch(endpoint, data) {
        return this.request('PATCH', endpoint, data);
    }

    async delete(endpoint) {
        return this.request('DELETE', endpoint);
    }

    // File upload method
    async upload(endpoint, formData, onProgress = null) {
        const url = `${this.baseURL}${endpoint}`;
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Set up progress tracking
            if (onProgress) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        onProgress(percentComplete);
                    }
                });
            }

            xhr.onload = async () => {
                try {
                    const response = {
                        ok: xhr.status >= 200 && xhr.status < 300,
                        status: xhr.status,
                        statusText: xhr.statusText,
                        json: () => Promise.resolve(JSON.parse(xhr.responseText))
                    };
                    
                    const result = await this.handleResponse(response);
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            };

            xhr.onerror = () => {
                reject(new Error('Upload failed'));
            };

            xhr.open('POST', url);
            
            // Set authorization header
            if (this.token) {
                xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
            }

            xhr.send(formData);
        });
    }

    // Batch request method
    async batch(requests) {
        const promises = requests.map(req => 
            this.request(req.method, req.endpoint, req.data)
        );

        try {
            const results = await Promise.allSettled(promises);
            return results.map((result, index) => ({
                request: requests[index],
                success: result.status === 'fulfilled' && result.value.success,
                data: result.status === 'fulfilled' ? result.value.data : null,
                error: result.status === 'rejected' ? result.reason.message : 
                       (result.value && !result.value.success ? result.value.error : null)
            }));
        } catch (error) {
            console.error('Batch request failed:', error);
            return requests.map(req => ({
                request: req,
                success: false,
                error: error.message
            }));
        }
    }

    // Specific API methods for admin dashboard
    
    // Authentication
    async login(email, password) {
        return this.post('/auth/admin/login', { email, password });
    }

    async logout() {
        const result = await this.post('/auth/logout');
        this.clearAuth();
        return result;
    }

    // Dashboard
    async getDashboardStats() {
        return this.get('/admin/dashboard');
    }

    async getSystemHealth() {
        return this.get('/admin/system/health');
    }

    async getRecentActivity(limit = 10) {
        return this.get('/admin/activity', { limit });
    }

    // Users
    async getUsers(page = 1, perPage = 20, search = '') {
        return this.get('/admin/users', { page, per_page: perPage, search });
    }

    async getUser(userId) {
        return this.get(`/admin/users/${userId}`);
    }

    async updateUser(userId, data) {
        return this.put(`/admin/users/${userId}`, data);
    }

    async deleteUser(userId) {
        return this.delete(`/admin/users/${userId}`);
    }

    async adjustUserCredits(userId, amount, description, notes = '') {
        return this.post(`/admin/users/${userId}/credits`, {
            amount,
            description,
            notes
        });
    }

    // API Configurations
    async getAPIConfigs() {
        return this.get('/admin/api-configs');
    }

    async createAPIConfig(data) {
        return this.post('/admin/api-configs', data);
    }

    async updateAPIConfig(configId, data) {
        return this.put(`/admin/api-configs/${configId}`, data);
    }

    async deleteAPIConfig(configId) {
        return this.delete(`/admin/api-configs/${configId}`);
    }

    async testAPIConnection(serviceName) {
        return this.post(`/admin/api-configs/${serviceName}/test`);
    }

    // Feature Toggles
    async getFeatureToggles() {
        return this.get('/admin/feature-toggles');
    }

    async updateFeatureToggle(featureId, data) {
        return this.put(`/admin/feature-toggles/${featureId}`, data);
    }

    // Subscriptions
    async getSubscriptionPlans() {
        return this.get('/admin/subscription-plans');
    }

    async updateSubscriptionPlan(planId, data) {
        return this.put(`/admin/subscription-plans/${planId}`, data);
    }

    // Credit Management
    async getCreditPackages() {
        return this.get('/admin/credit-packages');
    }

    async getTaskCreditCosts() {
        return this.get('/admin/task-credit-costs');
    }

    async updateTaskCreditCost(costId, data) {
        return this.put(`/admin/task-credit-costs/${costId}`, data);
    }

    // Analytics
    async getUsageAnalytics(days = 30) {
        return this.get('/admin/analytics/usage', { days });
    }

    async getRevenueAnalytics(period = 'month') {
        return this.get('/admin/analytics/revenue', { period });
    }

    // Content Management
    async getContent(page = 1, perPage = 20, type = '', status = '') {
        return this.get('/admin/content', { 
            page, 
            per_page: perPage, 
            type, 
            status 
        });
    }

    async approveContent(contentId) {
        return this.post(`/admin/content/${contentId}/approve`);
    }

    async rejectContent(contentId, reason) {
        return this.post(`/admin/content/${contentId}/reject`, { reason });
    }

    // Campaigns
    async getCampaigns(page = 1, perPage = 20, status = '') {
        return this.get('/admin/campaigns', { 
            page, 
            per_page: perPage, 
            status 
        });
    }

    async getCampaign(campaignId) {
        return this.get(`/admin/campaigns/${campaignId}`);
    }

    // Tasks
    async getTasks(page = 1, perPage = 20, status = '', type = '') {
        return this.get('/admin/tasks', { 
            page, 
            per_page: perPage, 
            status, 
            type 
        });
    }

    async retryTask(taskId) {
        return this.post(`/admin/tasks/${taskId}/retry`);
    }

    async cancelTask(taskId) {
        return this.post(`/admin/tasks/${taskId}/cancel`);
    }

    // System Settings
    async getSystemSettings() {
        return this.get('/admin/system/settings');
    }

    async updateSystemSettings(settings) {
        return this.put('/admin/system/settings', settings);
    }

    async exportData(type, filters = {}) {
        return this.get(`/admin/export/${type}`, filters);
    }

    async importData(type, file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', type);
        
        return this.upload('/admin/import', formData);
    }
}

// Create global API client instance
window.apiClient = new APIClient();

