/**
 * API Management Dashboard JavaScript
 * Handles all dashboard functionality and API interactions
 */

class APIDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.charts = {};
        this.currentPage = 1;
        this.logsPerPage = 50;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadDashboard();
        this.checkSystemHealth();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.refreshCurrentSection();
        }, 30000);
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });
        
        // Mobile menu toggle
        document.getElementById('mobileMenuToggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('sidebar-collapsed');
        });
        
        document.getElementById('sidebarToggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.add('sidebar-collapsed');
        });
        
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshCurrentSection();
        });
        
        // API Keys management
        document.getElementById('addApiKeyBtn').addEventListener('click', () => {
            this.showModal('addApiKeyModal');
        });
        
        document.getElementById('addApiKeyForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addApiKey(new FormData(e.target));
        });
        
        // Usage logs filters
        document.getElementById('serviceFilter').addEventListener('change', () => {
            this.loadUsageLogs();
        });
        
        document.getElementById('statusFilter').addEventListener('change', () => {
            this.loadUsageLogs();
        });
        
        document.getElementById('exportLogsBtn').addEventListener('click', () => {
            this.exportLogs();
        });
        
        // Pagination
        document.getElementById('logsPrevBtn').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadUsageLogs();
            }
        });
        
        document.getElementById('logsNextBtn').addEventListener('click', () => {
            this.currentPage++;
            this.loadUsageLogs();
        });
        
        // Cache management
        document.getElementById('clearExpiredCacheBtn').addEventListener('click', () => {
            this.clearCache('expired');
        });
        
        document.getElementById('clearAllCacheBtn').addEventListener('click', () => {
            if (confirm('Are you sure you want to clear all cache? This action cannot be undone.')) {
                this.clearCache('all');
            }
        });
        
        // Rate limits
        document.getElementById('checkRateLimitsBtn').addEventListener('click', () => {
            const userId = document.getElementById('userIdInput').value;
            if (userId) {
                this.checkRateLimits(userId);
            }
        });
        
        document.getElementById('resetRateLimitsBtn').addEventListener('click', () => {
            const userId = document.getElementById('userIdInput').value;
            if (userId && confirm(`Are you sure you want to reset rate limits for user ${userId}?`)) {
                this.resetRateLimits(userId);
            }
        });
        
        // Modal handling
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.hideModal(modal.id);
            });
        });
        
        // Close modal on outside click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal.id);
                }
            });
        });
    }
    
    showSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[href="#${section}"]`).classList.add('active');
        
        // Hide all sections
        document.querySelectorAll('.section').forEach(sec => {
            sec.classList.add('hidden');
        });
        
        // Show selected section
        document.getElementById(`${section}-section`).classList.remove('hidden');
        
        // Update page title
        const titles = {
            'dashboard': 'Dashboard',
            'api-keys': 'API Keys',
            'usage-logs': 'Usage Logs',
            'services': 'Services',
            'cache': 'Cache Management',
            'queue': 'Queue Management',
            'rate-limits': 'Rate Limits'
        };
        document.getElementById('pageTitle').textContent = titles[section] || section;
        
        this.currentSection = section;
        
        // Load section data
        this.loadSectionData(section);
    }
    
    loadSectionData(section) {
        switch (section) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'api-keys':
                this.loadApiKeys();
                break;
            case 'usage-logs':
                this.loadUsageLogs();
                break;
            case 'services':
                this.loadServices();
                break;
            case 'cache':
                this.loadCacheStats();
                break;
            case 'queue':
                this.loadQueueStats();
                break;
            case 'rate-limits':
                // Rate limits are loaded on demand
                break;
        }
    }
    
    refreshCurrentSection() {
        this.loadSectionData(this.currentSection);
        this.checkSystemHealth();
    }
    
    async apiCall(endpoint, options = {}) {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`/api/management${endpoint}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification('API call failed: ' + error.message, 'error');
            throw error;
        }
    }
    
    async loadDashboard() {
        try {
            // Load overview stats
            const [apiKeysData, usageStats, cacheStats, queueStats] = await Promise.all([
                this.apiCall('/api-keys'),
                this.apiCall('/usage-stats?days=1'),
                this.apiCall('/cache-stats'),
                this.apiCall('/queue-stats')
            ]);
            
            // Update dashboard cards
            document.getElementById('apiKeysCount').textContent = apiKeysData.total || 0;
            document.getElementById('apiRequestsCount').textContent = usageStats.stats?.total_requests || 0;
            document.getElementById('queueSize').textContent = this.getTotalQueueSize(queueStats.queue_stats);
            
            // Calculate cache hit rate
            const hitRate = this.calculateCacheHitRate(cacheStats.cache_stats);
            document.getElementById('cacheHitRate').textContent = hitRate;
            
            // Load charts
            await this.loadUsageChart();
            await this.loadRequestTypesChart();
            await this.loadRecentActivity();
            
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }
    
    async loadUsageChart() {
        try {
            const data = await this.apiCall('/usage-stats?days=7');
            
            // Create mock data for the chart (you would process real data here)
            const labels = [];
            const values = [];
            
            for (let i = 6; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                labels.push(date.toLocaleDateString());
                values.push(Math.floor(Math.random() * 100)); // Mock data
            }
            
            const ctx = document.getElementById('usageChart').getContext('2d');
            
            if (this.charts.usage) {
                this.charts.usage.destroy();
            }
            
            this.charts.usage = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'API Requests',
                        data: values,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Failed to load usage chart:', error);
        }
    }
    
    async loadRequestTypesChart() {
        try {
            const data = await this.apiCall('/usage-stats?days=7');
            
            const requestTypes = data.stats?.request_types || {};
            const labels = Object.keys(requestTypes);
            const values = Object.values(requestTypes);
            
            const ctx = document.getElementById('requestTypesChart').getContext('2d');
            
            if (this.charts.requestTypes) {
                this.charts.requestTypes.destroy();
            }
            
            this.charts.requestTypes = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444',
                            '#8b5cf6'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
        } catch (error) {
            console.error('Failed to load request types chart:', error);
        }
    }
    
    async loadRecentActivity() {
        try {
            const data = await this.apiCall('/usage-logs?per_page=10');
            const container = document.getElementById('recentActivity');
            
            if (data.logs && data.logs.length > 0) {
                container.innerHTML = data.logs.map(log => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                        <div class="flex items-center">
                            <div class="status-indicator status-${log.response_status === 'success' ? 'healthy' : 'unhealthy'}"></div>
                            <div>
                                <p class="font-medium">${log.request_type} - ${log.api_key?.service_name || 'Unknown'}</p>
                                <p class="text-sm text-gray-600">${new Date(log.created_at).toLocaleString()}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="text-sm font-medium">${log.response_time_ms}ms</p>
                            <p class="text-sm text-gray-600">${log.cost_credits} credits</p>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p class="text-center text-gray-500 py-8">No recent activity</p>';
            }
            
        } catch (error) {
            console.error('Failed to load recent activity:', error);
            document.getElementById('recentActivity').innerHTML = 
                '<p class="text-center text-red-500 py-8">Failed to load recent activity</p>';
        }
    }
    
    async loadApiKeys() {
        try {
            const data = await this.apiCall('/api-keys');
            const tbody = document.getElementById('apiKeysTable');
            
            if (data.api_keys && data.api_keys.length > 0) {
                tbody.innerHTML = data.api_keys.map(key => `
                    <tr>
                        <td class="font-medium">${key.service_name}</td>
                        <td>
                            <span class="status-indicator status-${key.is_active ? 'healthy' : 'unhealthy'}"></span>
                            ${key.is_active ? 'Active' : 'Inactive'}
                        </td>
                        <td>${key.usage_count}</td>
                        <td>${key.last_used ? new Date(key.last_used).toLocaleString() : 'Never'}</td>
                        <td>${key.rate_limit_per_minute}/min</td>
                        <td>
                            <div class="flex space-x-2">
                                <button onclick="dashboard.toggleApiKey('${key.service_name}', ${!key.is_active})" 
                                        class="btn-${key.is_active ? 'secondary' : 'primary'} text-sm">
                                    ${key.is_active ? 'Disable' : 'Enable'}
                                </button>
                                <button onclick="dashboard.testApiService('${key.service_name}')" 
                                        class="btn-secondary text-sm">
                                    Test
                                </button>
                                <button onclick="dashboard.deleteApiKey('${key.service_name}')" 
                                        class="btn-danger text-sm">
                                    Delete
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-gray-500">No API keys configured</td></tr>';
            }
            
        } catch (error) {
            console.error('Failed to load API keys:', error);
            document.getElementById('apiKeysTable').innerHTML = 
                '<tr><td colspan="6" class="text-center py-8 text-red-500">Failed to load API keys</td></tr>';
        }
    }
    
    async loadUsageLogs() {
        try {
            const serviceFilter = document.getElementById('serviceFilter').value;
            const statusFilter = document.getElementById('statusFilter').value;
            
            let url = `/usage-logs?page=${this.currentPage}&per_page=${this.logsPerPage}`;
            if (serviceFilter) url += `&service_name=${serviceFilter}`;
            if (statusFilter) url += `&status=${statusFilter}`;
            
            const data = await this.apiCall(url);
            const tbody = document.getElementById('usageLogsTable');
            
            if (data.logs && data.logs.length > 0) {
                tbody.innerHTML = data.logs.map(log => `
                    <tr>
                        <td>${new Date(log.created_at).toLocaleString()}</td>
                        <td>${log.api_key?.service_name || 'Unknown'}</td>
                        <td>${log.user_id || 'Anonymous'}</td>
                        <td>${log.request_type}</td>
                        <td>
                            <span class="status-indicator status-${log.response_status === 'success' ? 'healthy' : 'unhealthy'}"></span>
                            ${log.response_status}
                        </td>
                        <td>${log.response_time_ms}ms</td>
                        <td>${log.cost_credits} credits</td>
                    </tr>
                `).join('');
                
                // Update pagination
                this.updateLogsPagination(data.pagination);
            } else {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-gray-500">No usage logs found</td></tr>';
            }
            
        } catch (error) {
            console.error('Failed to load usage logs:', error);
            document.getElementById('usageLogsTable').innerHTML = 
                '<tr><td colspan="7" class="text-center py-8 text-red-500">Failed to load usage logs</td></tr>';
        }
    }
    
    updateLogsPagination(pagination) {
        document.getElementById('logsStart').textContent = ((pagination.page - 1) * pagination.per_page) + 1;
        document.getElementById('logsEnd').textContent = Math.min(pagination.page * pagination.per_page, pagination.total);
        document.getElementById('logsTotal').textContent = pagination.total;
        
        document.getElementById('logsPrevBtn').disabled = !pagination.has_prev;
        document.getElementById('logsNextBtn').disabled = !pagination.has_next;
    }
    
    async loadServices() {
        try {
            const data = await this.apiCall('/service-status');
            const container = document.getElementById('servicesGrid');
            
            const services = Object.entries(data.services);
            
            if (services.length > 0) {
                container.innerHTML = services.map(([name, info]) => `
                    <div class="card p-6">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="text-lg font-semibold capitalize">${name.replace('_', ' ')}</h4>
                            <span class="status-indicator status-${info.configured && info.active ? 'healthy' : 'unhealthy'}"></span>
                        </div>
                        
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span>Configured:</span>
                                <span class="${info.configured ? 'text-green-600' : 'text-red-600'}">
                                    ${info.configured ? 'Yes' : 'No'}
                                </span>
                            </div>
                            <div class="flex justify-between">
                                <span>Active:</span>
                                <span class="${info.active ? 'text-green-600' : 'text-red-600'}">
                                    ${info.active ? 'Yes' : 'No'}
                                </span>
                            </div>
                            <div class="flex justify-between">
                                <span>Free Tier:</span>
                                <span class="${info.free_tier ? 'text-green-600' : 'text-gray-600'}">
                                    ${info.free_tier ? 'Yes' : 'No'}
                                </span>
                            </div>
                        </div>
                        
                        <div class="mt-4">
                            <p class="text-sm font-medium mb-2">Operations:</p>
                            <div class="flex flex-wrap gap-1">
                                ${info.operations.map(op => `
                                    <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">${op}</span>
                                `).join('')}
                            </div>
                        </div>
                        
                        ${info.configured ? `
                            <button onclick="dashboard.testApiService('${name}')" 
                                    class="btn-primary w-full mt-4">
                                Test Service
                            </button>
                        ` : ''}
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p class="text-center text-gray-500 py-8">No services configured</p>';
            }
            
        } catch (error) {
            console.error('Failed to load services:', error);
            document.getElementById('servicesGrid').innerHTML = 
                '<p class="text-center text-red-500 py-8">Failed to load services</p>';
        }
    }
    
    async loadCacheStats() {
        try {
            const data = await this.apiCall('/cache-stats');
            const container = document.getElementById('cacheStats');
            const stats = data.cache_stats;
            
            let statsHtml = `
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span>Cache Type:</span>
                        <span class="font-medium">${stats.cache_type}</span>
                    </div>
            `;
            
            if (stats.cache_type === 'redis') {
                statsHtml += `
                    <div class="flex justify-between">
                        <span>Total Keys:</span>
                        <span class="font-medium">${stats.total_keys || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Memory Usage:</span>
                        <span class="font-medium">${stats.memory_usage || 'Unknown'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Cache Hits:</span>
                        <span class="font-medium">${stats.hits || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Cache Misses:</span>
                        <span class="font-medium">${stats.misses || 0}</span>
                    </div>
                `;
            } else {
                statsHtml += `
                    <div class="flex justify-between">
                        <span>Total Files:</span>
                        <span class="font-medium">${stats.total_files || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Total Size:</span>
                        <span class="font-medium">${stats.total_size_mb || 0} MB</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Expired Files:</span>
                        <span class="font-medium">${stats.expired_files || 0}</span>
                    </div>
                `;
            }
            
            statsHtml += '</div>';
            container.innerHTML = statsHtml;
            
        } catch (error) {
            console.error('Failed to load cache stats:', error);
            document.getElementById('cacheStats').innerHTML = 
                '<p class="text-center text-red-500 py-8">Failed to load cache statistics</p>';
        }
    }
    
    async loadQueueStats() {
        try {
            const data = await this.apiCall('/queue-stats');
            const container = document.getElementById('queueStats');
            const stats = data.queue_stats;
            
            let statsHtml = `
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span>Queue Type:</span>
                        <span class="font-medium">${stats.queue_type}</span>
                    </div>
            `;
            
            if (stats.queue_sizes) {
                Object.entries(stats.queue_sizes).forEach(([priority, size]) => {
                    statsHtml += `
                        <div class="flex justify-between">
                            <span>${priority} Priority:</span>
                            <span class="font-medium">${size}</span>
                        </div>
                    `;
                });
            }
            
            if (stats.stats) {
                Object.entries(stats.stats).forEach(([key, value]) => {
                    statsHtml += `
                        <div class="flex justify-between">
                            <span>${key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span>
                            <span class="font-medium">${value}</span>
                        </div>
                    `;
                });
            }
            
            statsHtml += '</div>';
            container.innerHTML = statsHtml;
            
        } catch (error) {
            console.error('Failed to load queue stats:', error);
            document.getElementById('queueStats').innerHTML = 
                '<p class="text-center text-red-500 py-8">Failed to load queue statistics</p>';
        }
    }
    
    async checkSystemHealth() {
        try {
            const data = await this.apiCall('/system-health');
            const healthIndicator = document.getElementById('systemHealth');
            const health = data.health;
            
            let statusClass = 'status-healthy';
            let statusText = 'System Healthy';
            
            if (health.status === 'degraded') {
                statusClass = 'status-warning';
                statusText = 'System Degraded';
            } else if (health.status === 'unhealthy') {
                statusClass = 'status-unhealthy';
                statusText = 'System Unhealthy';
            }
            
            healthIndicator.innerHTML = `
                <span class="status-indicator ${statusClass}"></span>
                <span class="text-sm text-gray-600">${statusText}</span>
            `;
            
        } catch (error) {
            console.error('Failed to check system health:', error);
            document.getElementById('systemHealth').innerHTML = `
                <span class="status-indicator status-unhealthy"></span>
                <span class="text-sm text-gray-600">Health Check Failed</span>
            `;
        }
    }
    
    async addApiKey(formData) {
        try {
            const data = Object.fromEntries(formData);
            
            // Convert numeric fields
            data.rate_limit_per_minute = parseInt(data.rate_limit_per_minute);
            data.rate_limit_per_day = parseInt(data.rate_limit_per_day);
            if (data.monthly_quota) {
                data.monthly_quota = parseInt(data.monthly_quota);
            }
            
            const result = await this.apiCall('/api-keys', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            if (result.success) {
                this.showNotification('API key added successfully', 'success');
                this.hideModal('addApiKeyModal');
                this.loadApiKeys();
            } else {
                this.showNotification(result.error || 'Failed to add API key', 'error');
            }
            
        } catch (error) {
            console.error('Failed to add API key:', error);
            this.showNotification('Failed to add API key', 'error');
        }
    }
    
    async toggleApiKey(serviceName, isActive) {
        try {
            const result = await this.apiCall(`/api-keys/${serviceName}/toggle`, {
                method: 'POST',
                body: JSON.stringify({ is_active: isActive })
            });
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.loadApiKeys();
            } else {
                this.showNotification(result.error || 'Failed to toggle API key', 'error');
            }
            
        } catch (error) {
            console.error('Failed to toggle API key:', error);
            this.showNotification('Failed to toggle API key', 'error');
        }
    }
    
    async deleteApiKey(serviceName) {
        if (!confirm(`Are you sure you want to delete the API key for ${serviceName}?`)) {
            return;
        }
        
        try {
            const result = await this.apiCall(`/api-keys/${serviceName}`, {
                method: 'DELETE'
            });
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.loadApiKeys();
            } else {
                this.showNotification(result.error || 'Failed to delete API key', 'error');
            }
            
        } catch (error) {
            console.error('Failed to delete API key:', error);
            this.showNotification('Failed to delete API key', 'error');
        }
    }
    
    async testApiService(serviceName) {
        this.showModal('testApiModal');
        
        document.getElementById('testApiForm').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const testType = formData.get('type');
            
            try {
                const result = await this.apiCall(`/test-api/${serviceName}`, {
                    method: 'POST',
                    body: JSON.stringify({ type: testType })
                });
                
                const resultsDiv = document.getElementById('testResults');
                resultsDiv.classList.remove('hidden');
                resultsDiv.querySelector('pre').textContent = JSON.stringify(result, null, 2);
                
            } catch (error) {
                console.error('API test failed:', error);
                const resultsDiv = document.getElementById('testResults');
                resultsDiv.classList.remove('hidden');
                resultsDiv.querySelector('pre').textContent = `Error: ${error.message}`;
            }
        };
    }
    
    async clearCache(type) {
        try {
            const result = await this.apiCall('/cache/clear', {
                method: 'POST',
                body: JSON.stringify({ type })
            });
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.loadCacheStats();
            } else {
                this.showNotification(result.error || 'Failed to clear cache', 'error');
            }
            
        } catch (error) {
            console.error('Failed to clear cache:', error);
            this.showNotification('Failed to clear cache', 'error');
        }
    }
    
    async checkRateLimits(userId) {
        try {
            const data = await this.apiCall(`/rate-limits?user_id=${userId}`);
            const container = document.getElementById('rateLimitsInfo');
            
            if (data.rate_limits) {
                const limits = data.rate_limits;
                
                container.innerHTML = Object.entries(limits).map(([type, info]) => `
                    <div class="card p-4">
                        <h4 class="font-semibold mb-2 capitalize">${type.replace('_', ' ')} Rate Limit</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span class="text-gray-600">Limit:</span>
                                <span class="font-medium ml-2">${info.limit}</span>
                            </div>
                            <div>
                                <span class="text-gray-600">Remaining:</span>
                                <span class="font-medium ml-2">${info.remaining}</span>
                            </div>
                            <div>
                                <span class="text-gray-600">Reset Time:</span>
                                <span class="font-medium ml-2">${new Date(info.reset_time * 1000).toLocaleString()}</span>
                            </div>
                            <div>
                                <span class="text-gray-600">Retry After:</span>
                                <span class="font-medium ml-2">${info.retry_after}s</span>
                            </div>
                        </div>
                        <div class="mt-2">
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div class="bg-blue-600 h-2 rounded-full" 
                                     style="width: ${(info.remaining / info.limit) * 100}%"></div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
            
        } catch (error) {
            console.error('Failed to check rate limits:', error);
            this.showNotification('Failed to check rate limits', 'error');
        }
    }
    
    async resetRateLimits(userId) {
        try {
            const result = await this.apiCall('/rate-limits/reset', {
                method: 'POST',
                body: JSON.stringify({ user_id: parseInt(userId) })
            });
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.checkRateLimits(userId);
            } else {
                this.showNotification(result.error || 'Failed to reset rate limits', 'error');
            }
            
        } catch (error) {
            console.error('Failed to reset rate limits:', error);
            this.showNotification('Failed to reset rate limits', 'error');
        }
    }
    
    async exportLogs() {
        try {
            const serviceFilter = document.getElementById('serviceFilter').value;
            const days = 30; // Default to 30 days
            
            let url = `/export-logs?days=${days}`;
            if (serviceFilter) url += `&service_name=${serviceFilter}`;
            
            const token = localStorage.getItem('access_token');
            const response = await fetch(`/api/management${url}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `api_usage_logs_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.showNotification('Logs exported successfully', 'success');
            } else {
                throw new Error('Export failed');
            }
            
        } catch (error) {
            console.error('Failed to export logs:', error);
            this.showNotification('Failed to export logs', 'error');
        }
    }
    
    // Utility methods
    showModal(modalId) {
        document.getElementById(modalId).style.display = 'block';
    }
    
    hideModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
        
        // Reset forms
        const form = document.querySelector(`#${modalId} form`);
        if (form) {
            form.reset();
        }
        
        // Hide test results
        const testResults = document.getElementById('testResults');
        if (testResults) {
            testResults.classList.add('hidden');
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    getTotalQueueSize(queueStats) {
        if (!queueStats || !queueStats.queue_sizes) return 0;
        return Object.values(queueStats.queue_sizes).reduce((sum, size) => sum + size, 0);
    }
    
    calculateCacheHitRate(cacheStats) {
        if (!cacheStats) return '0%';
        
        if (cacheStats.cache_type === 'redis' && cacheStats.hits !== undefined && cacheStats.misses !== undefined) {
            const total = cacheStats.hits + cacheStats.misses;
            if (total === 0) return '0%';
            return Math.round((cacheStats.hits / total) * 100) + '%';
        }
        
        return 'N/A';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new APIDashboard();
});

