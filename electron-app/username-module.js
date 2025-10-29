// Username Searcher Module

class UsernameSearcherModule {
    constructor() {
        this.API_BASE = 'http://localhost:8000/api';
        this.currentSearch = null;
        this.cacheEnabled = true;
        
        this.init();
    }
    
    async init() {
        await this.loadCacheStats();
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        // Search form submission
        const searchForm = document.getElementById('usernameSearchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSearch();
            });
        }
        
        // Cache toggle
        const cacheToggle = document.getElementById('cacheToggle');
        if (cacheToggle) {
            cacheToggle.addEventListener('change', (e) => {
                this.cacheEnabled = e.target.checked;
            });
        }
        
        // Clear cache button
        const clearCacheBtn = document.getElementById('btnClearCache');
        if (clearCacheBtn) {
            clearCacheBtn.addEventListener('click', () => {
                this.clearCache();
            });
        }
        
        // Export PDF button
        const exportBtn = document.getElementById('btnExportPDF');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportPDF();
            });
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('btnRefresh');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                if (this.currentSearch) {
                    this.loadSearchResults(this.currentSearch.id);
                }
            });
        }
    }
    
    async loadCacheStats() {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${this.API_BASE}/username/cache/stats`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const stats = await response.json();
                this.updateCacheStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Failed to load cache stats:', error);
        }
    }
    
    updateCacheStatsDisplay(stats) {
        const validEl = document.getElementById('validCache');
        const totalEl = document.getElementById('totalSearches');
        
        if (validEl) validEl.textContent = stats.valid_cache || 0;
        if (totalEl) totalEl.textContent = stats.total_searches || 0;
    }
    
    async handleSearch() {
        const username = document.getElementById('usernameInput').value.trim();
        const caseId = document.getElementById('caseId').value;
        const officerName = document.getElementById('officerName').value;
        
        // Validate
        if (!username) {
            this.showNotification('Please enter a username', 'error');
            return;
        }
        
        if (username.length < 3) {
            this.showNotification('Username must be at least 3 characters', 'error');
            return;
        }
        
        const searchBtn = document.getElementById('btnSearch');
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<span class="spinner"></span> Searching...';
        
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${this.API_BASE}/username/search`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    case_id: caseId ? parseInt(caseId) : null,
                    officer_name: officerName || null
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentSearch = data;
                
                this.showNotification(
                    `Search completed! Found on ${data.platforms_found} out of ${data.platforms_checked} platforms`,
                    'success'
                );
                
                // Show results
                this.displayResults(data);
                
                // Reload cache stats
                await this.loadCacheStats();
                
                // Scroll to results
                document.getElementById('resultsSection')?.scrollIntoView({ behavior: 'smooth' });
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Search failed', 'error');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showNotification('Failed to perform search', 'error');
        } finally {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '🔍 Search Username';
        }
    }
    
    async displayResults(search) {
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection) return;
        
        resultsSection.style.display = 'block';
        
        // Update status banner
        this.updateStatusBanner(search);
        
        // Update statistics
        this.updateStatistics(search);
        
        // Load and display platform results
        await this.loadPlatformResults(search.id);
    }
    
    updateStatusBanner(search) {
        const banner = document.getElementById('statusBanner');
        if (!banner) return;
        
        const statusConfig = {
            'completed': {
                class: 'completed',
                icon: '✅',
                title: 'Search Completed',
                subtitle: `Found username on ${search.platforms_found} platforms`
            },
            'in_progress': {
                class: 'in-progress',
                icon: '🔄',
                title: 'Search In Progress',
                subtitle: 'Checking platforms...'
            },
            'failed': {
                class: 'failed',
                icon: '❌',
                title: 'Search Failed',
                subtitle: search.error_message || 'An error occurred'
            },
            'pending': {
                class: 'pending',
                icon: '⏳',
                title: 'Search Pending',
                subtitle: 'Queued for processing'
            }
        };
        
        const config = statusConfig[search.status] || statusConfig.pending;
        
        banner.className = `search-status-banner ${config.class}`;
        banner.innerHTML = `
            <div class="status-icon-large">${config.icon}</div>
            <div class="status-content">
                <div class="status-title">${config.title}</div>
                <div class="status-subtitle">${config.subtitle}</div>
            </div>
        `;
    }
    
    updateStatistics(search) {
        document.getElementById('totalPlatforms').textContent = search.platforms_checked || 0;
        document.getElementById('foundPlatforms').textContent = search.platforms_found || 0;
        
        const successRate = search.platforms_checked > 0
            ? Math.round((search.platforms_found / search.platforms_checked) * 100)
            : 0;
        document.getElementById('successRate').textContent = successRate + '%';
    }
    
    async loadPlatformResults(searchId) {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${this.API_BASE}/username/search/${searchId}/results`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const results = await response.json();
                this.renderPlatformResults(results);
            }
        } catch (error) {
            console.error('Failed to load platform results:', error);
        }
    }
    
    renderPlatformResults(results) {
        const grid = document.getElementById('platformsGrid');
        if (!grid) return;
        
        if (!results || results.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <div class="empty-state-title">No Platforms Found</div>
                    <div class="empty-state-text">
                        This username was not found on any of the checked platforms.
                    </div>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = results.map(result => {
            // Determine confidence level
            let confidenceClass = 'low';
            let confidenceText = 'Low';
            if (result.confidence_score >= 0.8) {
                confidenceClass = 'high';
                confidenceText = 'High';
            } else if (result.confidence_score >= 0.5) {
                confidenceClass = 'medium';
                confidenceText = 'Medium';
            }
            
            const confidencePercent = Math.round(result.confidence_score * 100);
            
            // Format discovery date
            const discoveredDate = result.discovered_at
                ? new Date(result.discovered_at).toLocaleString()
                : 'N/A';
            
            // Get platform icon (emoji)
            const icon = this.getPlatformIcon(result.platform_name);
            
            return `
                <div class="platform-card" onclick="window.open('${result.platform_url}', '_blank')">
                    <div class="platform-card-header">
                        <div class="platform-icon-name">
                            <div class="platform-icon">${icon}</div>
                            <div class="platform-name">${result.platform_name}</div>
                        </div>
                        <div class="confidence-badge ${confidenceClass}">
                            ${confidencePercent}% ${confidenceText}
                        </div>
                    </div>
                    <a href="${result.platform_url}" 
                       target="_blank" 
                       class="platform-url"
                       onclick="event.stopPropagation()">
                        ${this.truncateUrl(result.platform_url, 50)}
                    </a>
                    <div class="platform-discovered">
                        ${discoveredDate}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    getPlatformIcon(platformName) {
        const icons = {
            'Instagram': '📷',
            'Twitter': '🐦',
            'Facebook': '📘',
            'LinkedIn': '💼',
            'GitHub': '🐙',
            'TikTok': '🎵',
            'YouTube': '📺',
            'Reddit': '🤖',
            'Pinterest': '📌',
            'Snapchat': '👻',
            'Telegram': '✈️',
            'Discord': '🎮',
            'Twitch': '🎮',
            'Steam': '🎮',
            'Spotify': '🎵',
            'SoundCloud': '🎵',
            'Medium': '✍️',
            'Dev.to': '💻',
            'Stack Overflow': '📚',
            'Quora': '❓',
            'GitLab': '🦊',
            'Behance': '🎨',
            'Dribbble': '🏀',
            'Patreon': '🎁',
            'Ko-fi': '☕'
        };
        return icons[platformName] || '🔗';
    }
    
    truncateUrl(url, maxLength) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength - 3) + '...';
    }
    
    async loadSearchResults(searchId) {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${this.API_BASE}/username/search/${searchId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentSearch = data;
                this.displayResults(data);
            }
        } catch (error) {
            console.error('Failed to refresh results:', error);
            this.showNotification('Failed to refresh results', 'error');
        }
    }
    
    async clearCache() {
        const username = document.getElementById('usernameInput').value.trim();
        
        if (!username && !confirm('Clear ALL cached searches? This action cannot be undone.')) {
            return;
        }
        
        try {
            const token = localStorage.getItem('authToken');
            const url = username
                ? `${this.API_BASE}/username/cache/clear?username=${encodeURIComponent(username)}`
                : `${this.API_BASE}/username/cache/clear`;
            
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showNotification(data.message, 'success');
                await this.loadCacheStats();
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Failed to clear cache', 'error');
            }
        } catch (error) {
            console.error('Clear cache error:', error);
            this.showNotification('Failed to clear cache', 'error');
        }
    }
    
    async exportPDF() {
        if (!this.currentSearch || !this.currentSearch.id) {
            this.showNotification('No search results to export', 'error');
            return;
        }
        
        const btn = document.getElementById('btnExportPDF');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Generating PDF...';
        
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(
                `${this.API_BASE}/username/search/${this.currentSearch.id}/export/pdf`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `username_report_${this.currentSearch.id}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('PDF exported successfully!', 'success');
            } else {
                this.showNotification('Failed to export PDF', 'error');
            }
        } catch (error) {
            console.error('PDF export error:', error);
            this.showNotification('Failed to export PDF', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '📄 Export PDF';
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
            max-width: 400px;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 4000);
    }
}

// Initialize on page load
let usernameSearcherModule;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('usernameSearcherPage')) {
        usernameSearcherModule = new UsernameSearcherModule();
    }
});
