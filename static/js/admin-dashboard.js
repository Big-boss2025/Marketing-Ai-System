// ===== Admin Dashboard Main JavaScript =====

class AdminDashboard {
    constructor() {
        this.currentPage = 'dashboard';
        this.charts = {};
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.initializeCharts();
        this.startAutoRefresh();
        this.hideLoadingScreen();
    }

    setupEventListeners() {
        // Sidebar navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigateToPage(page);
            });
        });

        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }

        // Refresh data button
        const refreshBtn = document.getElementById('refreshData');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshAllData();
            });
        }

        // Chart period selector
        const chartPeriod = document.getElementById('chartPeriod');
        if (chartPeriod) {
            chartPeriod.addEventListener('change', (e) => {
                this.updateCharts(e.target.value);
            });
        }

        // Mobile responsive
        this.setupMobileHandlers();
    }

    navigateToPage(page) {
        // Update active navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-page="${page}"]`).parentElement.classList.add('active');

        // Hide all pages
        document.querySelectorAll('.page-content').forEach(pageContent => {
            pageContent.classList.remove('active');
        });

        // Show selected page
        const targetPage = document.getElementById(`${page}Page`);
        if (targetPage) {
            targetPage.classList.add('active');
        }

        // Update page title and breadcrumb
        this.updatePageHeader(page);

        // Load page-specific data
        this.loadPageData(page);

        this.currentPage = page;
    }

    updatePageHeader(page) {
        const pageTitle = document.getElementById('pageTitle');
        const currentPageBreadcrumb = document.getElementById('currentPage');
        
        const pageTitles = {
            dashboard: 'لوحة المعلومات',
            users: 'إدارة المستخدمين',
            subscriptions: 'الاشتراكات والباقات',
            credits: 'إدارة الكريديت',
            apis: 'إعدادات APIs',
            features: 'إدارة الميزات',
            content: 'إدارة المحتوى',
            campaigns: 'الحملات التسويقية',
            analytics: 'التحليلات والتقارير',
            system: 'إعدادات النظام'
        };

        if (pageTitle) pageTitle.textContent = pageTitles[page] || page;
        if (currentPageBreadcrumb) currentPageBreadcrumb.textContent = pageTitles[page] || page;
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('collapsed');
        
        // Save state to localStorage
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    }

    hideLoadingScreen() {
        setTimeout(() => {
            const loadingScreen = document.getElementById('loadingScreen');
            const mainContainer = document.getElementById('mainContainer');
            
            if (loadingScreen) {
                loadingScreen.style.opacity = '0';
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                    mainContainer.style.display = 'flex';
                    
                    // Animate main container
                    setTimeout(() => {
                        mainContainer.style.opacity = '1';
                    }, 50);
                }, 300);
            }
        }, 1500);
    }

    async loadInitialData() {
        try {
            // Load dashboard statistics
            await this.loadDashboardStats();
            
            // Load recent activity
            await this.loadRecentActivity();
            
            // Check system status
            await this.checkSystemStatus();
            
            // Restore sidebar state
            this.restoreSidebarState();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('خطأ في تحميل البيانات الأولية', 'error');
        }
    }

    async loadDashboardStats() {
        try {
            const response = await apiClient.get('/admin/dashboard');
            if (response.success) {
                this.updateStatsCards(response.data);
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
            // Use mock data for development
            this.updateStatsCards({
                users: { total: 1250, active: 980, new_today: 15 },
                subscriptions: { active: 450, total_revenue: 25680 },
                tasks: { total: 8750, completed: 7320, pending: 890, failed: 540 },
                credits: { total_used: 156780 }
            });
        }
    }

    updateStatsCards(data) {
        // Update user stats
        const totalUsersEl = document.getElementById('totalUsers');
        if (totalUsersEl) totalUsersEl.textContent = this.formatNumber(data.users?.total || 0);

        // Update revenue stats
        const totalRevenueEl = document.getElementById('totalRevenue');
        if (totalRevenueEl) totalRevenueEl.textContent = '$' + this.formatNumber(data.subscriptions?.total_revenue || 0);

        // Update task stats
        const totalTasksEl = document.getElementById('totalTasks');
        if (totalTasksEl) totalTasksEl.textContent = this.formatNumber(data.tasks?.completed || 0);

        // Update credit stats
        const totalCreditsEl = document.getElementById('totalCredits');
        if (totalCreditsEl) totalCreditsEl.textContent = this.formatNumber(data.credits?.total_used || 0);
    }

    async loadRecentActivity() {
        try {
            const response = await apiClient.get('/admin/activity?limit=10');
            if (response.success) {
                this.renderRecentActivity(response.data);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
            // Use mock data for development
            this.renderRecentActivity([
                {
                    type: 'user',
                    title: 'مستخدم جديد',
                    description: 'انضم أحمد محمد إلى النظام',
                    time: '5 دقائق',
                    icon: 'user'
                },
                {
                    type: 'payment',
                    title: 'دفعة جديدة',
                    description: 'تم استلام دفعة بقيمة $29.99',
                    time: '15 دقيقة',
                    icon: 'payment'
                },
                {
                    type: 'task',
                    title: 'مهمة مكتملة',
                    description: 'تم إنشاء محتوى لحملة تسويقية',
                    time: '30 دقيقة',
                    icon: 'task'
                }
            ]);
        }
    }

    renderRecentActivity(activities) {
        const activityList = document.getElementById('recentActivity');
        if (!activityList) return;

        const activityHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.icon}">
                    <i class="fas fa-${this.getActivityIcon(activity.icon)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                </div>
                <div class="activity-time">${activity.time}</div>
            </div>
        `).join('');

        activityList.innerHTML = activityHTML;
    }

    getActivityIcon(type) {
        const icons = {
            user: 'user-plus',
            payment: 'credit-card',
            task: 'check-circle',
            error: 'exclamation-triangle'
        };
        return icons[type] || 'info-circle';
    }

    async checkSystemStatus() {
        try {
            const response = await apiClient.get('/admin/system/health');
            if (response.success) {
                this.updateSystemStatus(response.data.overall_healthy);
            }
        } catch (error) {
            console.error('Error checking system status:', error);
            this.updateSystemStatus(false);
        }
    }

    updateSystemStatus(isHealthy) {
        const statusIndicator = document.getElementById('systemStatus');
        const statusText = statusIndicator?.nextElementSibling;
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${isHealthy ? 'online' : 'offline'}`;
        }
        
        if (statusText) {
            statusText.textContent = isHealthy ? 'النظام متصل' : 'النظام غير متصل';
        }
    }

    initializeCharts() {
        this.initUsageChart();
        this.initSubscriptionChart();
    }

    initUsageChart() {
        const ctx = document.getElementById('usageChart');
        if (!ctx) return;

        this.charts.usage = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['1', '2', '3', '4', '5', '6', '7'],
                datasets: [{
                    label: 'المستخدمين النشطين',
                    data: [120, 150, 180, 200, 170, 220, 250],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'المهام المكتملة',
                    data: [80, 110, 130, 160, 140, 180, 200],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    initSubscriptionChart() {
        const ctx = document.getElementById('subscriptionChart');
        if (!ctx) return;

        this.charts.subscription = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['مجاني', 'أساسي', 'متقدم', 'مؤسسي'],
                datasets: [{
                    data: [45, 30, 20, 5],
                    backgroundColor: [
                        '#64748b',
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }

    async updateCharts(period) {
        try {
            const response = await apiClient.get(`/admin/analytics/usage?days=${period}`);
            if (response.success && this.charts.usage) {
                // Update chart data
                this.charts.usage.data.datasets[0].data = response.data.active_users;
                this.charts.usage.data.datasets[1].data = response.data.completed_tasks;
                this.charts.usage.update();
            }
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    async loadPageData(page) {
        switch (page) {
            case 'users':
                await this.loadUsersPage();
                break;
            case 'subscriptions':
                await this.loadSubscriptionsPage();
                break;
            case 'credits':
                await this.loadCreditsPage();
                break;
            case 'apis':
                await this.loadApisPage();
                break;
            case 'features':
                await this.loadFeaturesPage();
                break;
            case 'content':
                await this.loadContentPage();
                break;
            case 'campaigns':
                await this.loadCampaignsPage();
                break;
            case 'analytics':
                await this.loadAnalyticsPage();
                break;
            case 'system':
                await this.loadSystemPage();
                break;
        }
    }

    async loadUsersPage() {
        const usersPage = document.getElementById('usersPage');
        if (!usersPage) return;

        usersPage.innerHTML = `
            <div class="page-header">
                <h2>إدارة المستخدمين</h2>
                <div class="page-actions">
                    <button class="btn btn-primary">
                        <i class="fas fa-plus"></i>
                        إضافة مستخدم
                    </button>
                </div>
            </div>
            <div class="content-card">
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>الاسم</th>
                                <th>البريد الإلكتروني</th>
                                <th>الاشتراك</th>
                                <th>الكريديت</th>
                                <th>تاريخ التسجيل</th>
                                <th>الحالة</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody id="usersTableBody">
                            <tr><td colspan="7" class="text-center">جاري تحميل البيانات...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // Load users data
        try {
            const response = await apiClient.get('/admin/users');
            if (response.success) {
                this.renderUsersTable(response.data.users);
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    renderUsersTable(users) {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;

        const usersHTML = users.map(user => `
            <tr>
                <td>${user.full_name || 'غير محدد'}</td>
                <td>${user.email}</td>
                <td>
                    <span class="badge badge-${this.getSubscriptionBadgeClass(user.subscription_status)}">
                        ${this.getSubscriptionLabel(user.subscription_status)}
                    </span>
                </td>
                <td>${this.formatNumber(user.credits_balance)}</td>
                <td>${this.formatDate(user.created_at)}</td>
                <td>
                    <span class="badge badge-${user.is_active ? 'success' : 'secondary'}">
                        ${user.is_active ? 'نشط' : 'غير نشط'}
                    </span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon" onclick="dashboard.viewUser('${user.id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-icon" onclick="dashboard.editUser('${user.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon btn-danger" onclick="dashboard.deleteUser('${user.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        tbody.innerHTML = usersHTML;
    }

    getSubscriptionBadgeClass(status) {
        const classes = {
            free: 'secondary',
            basic: 'info',
            premium: 'success',
            enterprise: 'warning'
        };
        return classes[status] || 'secondary';
    }

    getSubscriptionLabel(status) {
        const labels = {
            free: 'مجاني',
            basic: 'أساسي',
            premium: 'متقدم',
            enterprise: 'مؤسسي'
        };
        return labels[status] || 'غير محدد';
    }

    async refreshAllData() {
        const refreshBtn = document.getElementById('refreshData');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> جاري التحديث...';
            refreshBtn.disabled = true;
        }

        try {
            await this.loadDashboardStats();
            await this.loadRecentActivity();
            await this.checkSystemStatus();
            
            if (this.currentPage !== 'dashboard') {
                await this.loadPageData(this.currentPage);
            }

            this.showToast('تم تحديث البيانات بنجاح', 'success');
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showToast('خطأ في تحديث البيانات', 'error');
        } finally {
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> تحديث البيانات';
                refreshBtn.disabled = false;
            }
        }
    }

    startAutoRefresh() {
        // Refresh data every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardStats();
            this.checkSystemStatus();
        }, 5 * 60 * 1000);
    }

    restoreSidebarState() {
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isCollapsed) {
            document.querySelector('.sidebar').classList.add('collapsed');
        }
    }

    setupMobileHandlers() {
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                const sidebar = document.querySelector('.sidebar');
                const sidebarToggle = document.getElementById('sidebarToggle');
                
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                document.querySelector('.sidebar').classList.remove('open');
            }
        });
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        toastContainer.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'times-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    formatNumber(num) {
        return new Intl.NumberFormat('ar-EG').format(num);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ar-EG');
    }

    // Placeholder methods for user actions
    viewUser(userId) {
        console.log('View user:', userId);
        this.showToast('عرض تفاصيل المستخدم', 'info');
    }

    editUser(userId) {
        console.log('Edit user:', userId);
        this.showToast('تحرير المستخدم', 'info');
    }

    deleteUser(userId) {
        if (confirm('هل أنت متأكد من حذف هذا المستخدم؟')) {
            console.log('Delete user:', userId);
            this.showToast('تم حذف المستخدم', 'success');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AdminDashboard();
});

