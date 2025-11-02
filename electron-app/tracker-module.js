// Tracker Module JavaScript

class TrackerModule {
    constructor() {
        this.API_BASE = 'http://localhost:8000/api';
        this.selectedModules = new Set();
        this.userBalance = 0;
        this.currentSearch = null;
        this.pollInterval = null;
        
        // Module configurations with credits and info
        this.moduleConfigs = [
            {
                key: 'eyeofgod',
                name: 'Eye of God',
                description: 'Deep OSINT search across multiple databases',
                credits: 30,
                sensitive: true,
                requiresDisclaimer: true
            },
            {
                key: 'trucaller',
                name: 'Trucaller',
                description: 'Phone number identification and spam detection',
                credits: 20,
                sensitive: false,
                requiresDisclaimer: false
            },
            {
                key: 'getcontact',
                name: 'GetContact',
                description: 'Contact information and caller ID lookup',
                credits: 20,
                sensitive: false,
                requiresDisclaimer: false
            },
            {
                key: 'you_leak_osint',
                name: 'YouLeak OSINT',
                description: 'Email and data breach information',
                credits: 25,
                sensitive: true,
                requiresDisclaimer: true
            },
            {
                key: 'email2phonenumber',
                name: 'Email to Phone',
                description: 'Link email addresses to phone numbers',
                credits: 20,
                sensitive: false,
                requiresDisclaimer: false
            },
            {
                key: 'phone2email',
                name: 'Phone to Email',
                description: 'Link phone numbers to email addresses',
                credits: 20,
                sensitive: false,
                requiresDisclaimer: false
            },
            {
                key: 'social_search',
                name: 'Social Media Search',
                description: 'Find social media profiles and activity',
                credits: 15,
                sensitive: false,
                requiresDisclaimer: false
            },
            {
                key: 'whois',
                name: 'WHOIS Lookup',
                description: 'Domain registration and ownership information',
                credits: 10,
                sensitive: false,
                requiresDisclaimer: false
            },
            {
                key: 'breachcheck',
                name: 'Breach Check',
                description: 'Check if data appears in known breaches',
                credits: 25,
                sensitive: true,
                requiresDisclaimer: true
            }
        ];
        
        this.init();
    }
    
    async init() {
        await this.loadUserBalance();
        this.renderModules();
        this.attachEventListeners();
    }
    
    async loadUserBalance() {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${this.API_BASE}/tracker/balance`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.userBalance = data.credits;
                this.updateBalanceDisplay();
            }
        } catch (error) {
            console.error('Failed to load balance:', error);
            this.showNotification('Failed to load credit balance', 'error');
        }
    }
    
    updateBalanceDisplay() {
        const balanceEl = document.getElementById('creditBalance');
        if (balanceEl) {
            balanceEl.textContent = this.userBalance.toLocaleString();
        }
    }
    
    renderModules() {
        const grid = document.getElementById('modulesGrid');
        if (!grid) return;
        
        grid.innerHTML = this.moduleConfigs.map(module => `
            <div class="module-card" data-module="${module.key}">
                <div class="module-header">
                    <input type="checkbox" 
                           class="module-checkbox" 
                           id="module-${module.key}" 
                           data-module="${module.key}">
                    <div class="module-info">
                        <div class="module-name">${module.name}</div>
                        <div class="module-description">${module.description}</div>
                        <div class="module-badges">
                            ${module.sensitive ? '<span class="badge badge-sensitive">Sensitive</span>' : ''}
                            ${module.requiresDisclaimer ? '<span class="badge badge-disclaimer">Legal Notice</span>' : ''}
                        </div>
                    </div>
                    <div class="module-credits">
                        <span>💎</span>
                        <span>${module.credits}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    attachEventListeners() {
        // Module selection
        document.getElementById('modulesGrid')?.addEventListener('click', (e) => {
            const card = e.target.closest('.module-card');
            if (card) {
                const checkbox = card.querySelector('.module-checkbox');
                const moduleKey = card.dataset.module;
                
                if (e.target !== checkbox) {
                    checkbox.checked = !checkbox.checked;
                }
                
                if (checkbox.checked) {
                    this.selectedModules.add(moduleKey);
                    card.classList.add('selected');
                } else {
                    this.selectedModules.delete(moduleKey);
                    card.classList.remove('selected');
                }
                
                this.updateCostSummary();
            }
        });
        
        // Form submission
        document.getElementById('trackerForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
        
        // Reset button
        document.getElementById('btnReset')?.addEventListener('click', () => {
            this.resetForm();
        });
        
        // Export PDF button
        document.getElementById('btnExportPDF')?.addEventListener('click', () => {
            this.exportPDF();
        });
    }
    
    updateCostSummary() {
        const selectedCount = this.selectedModules.size;
        const totalCost = Array.from(this.selectedModules).reduce((sum, key) => {
            const module = this.moduleConfigs.find(m => m.key === key);
            return sum + (module ? module.credits : 0);
        }, 0);
        
        document.getElementById('selectedCount').textContent = selectedCount;
        document.getElementById('totalCost').textContent = totalCost;
        
        const costValueEl = document.getElementById('totalCost');
        const submitBtn = document.getElementById('btnSubmit');
        
        if (totalCost > this.userBalance) {
            costValueEl.className = 'cost-value insufficient';
            submitBtn.disabled = true;
        } else {
            costValueEl.className = 'cost-value sufficient';
            submitBtn.disabled = selectedCount === 0;
        }
    }
    
    async handleSubmit() {
        const formData = {
            search_type: document.getElementById('searchType').value,
            search_value: document.getElementById('searchValue').value,
            case_number: document.getElementById('caseNumber').value || null,
            officer_name: document.getElementById('officerName').value || null,
            badge_number: document.getElementById('badgeNumber').value || null,
            department: document.getElementById('department').value || null,
            modules: Array.from(this.selectedModules)
        };
        
        // Validate
        if (!formData.search_value.trim()) {
            this.showNotification('Please enter a search value', 'error');
            return;
        }
        
        if (this.selectedModules.size === 0) {
            this.showNotification('Please select at least one module', 'error');
            return;
        }
        
        // Check if sensitive modules require disclaimer
        const sensitiveModules = Array.from(this.selectedModules).filter(key => {
            const module = this.moduleConfigs.find(m => m.key === key);
            return module && module.requiresDisclaimer;
        });
        
        if (sensitiveModules.length > 0) {
            await this.showDisclaimer(formData);
        } else {
            await this.submitSearch(formData);
        }
    }
    
    async showDisclaimer(formData) {
        const disclaimerText = await this.fetchDisclaimer();
        
        const modal = document.createElement('div');
        modal.className = 'disclaimer-modal';
        modal.innerHTML = `
            <div class="disclaimer-content">
                <h2 class="disclaimer-title">
                    <span>⚠️</span>
                    Legal Disclaimer & Terms of Use
                </h2>
                <div class="disclaimer-text">${disclaimerText}</div>
                <div class="disclaimer-actions">
                    <button class="btn-decline" id="btnDeclineDisclaimer">Decline</button>
                    <button class="btn-accept" id="btnAcceptDisclaimer">I Accept</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        return new Promise((resolve) => {
            document.getElementById('btnAcceptDisclaimer').onclick = () => {
                document.body.removeChild(modal);
                this.submitSearch(formData);
                resolve(true);
            };
            
            document.getElementById('btnDeclineDisclaimer').onclick = () => {
                document.body.removeChild(modal);
                this.showNotification('Search cancelled', 'info');
                resolve(false);
            };
        });
    }
    
    async fetchDisclaimer() {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${this.API_BASE}/tracker/disclaimer`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.disclaimer;
            }
        } catch (error) {
            console.error('Failed to fetch disclaimer:', error);
        }
        
        return 'You acknowledge that this search involves sensitive data and must be used in accordance with applicable laws and regulations.';
    }
    
    async submitSearch(formData) {
        const submitBtn = document.getElementById('btnSubmit');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Submitting...';
        
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${this.API_BASE}/tracker/search`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentSearch = data;
                this.showNotification('Search submitted successfully!', 'success');
                
                // Reload balance
                await this.loadUserBalance();
                
                // Show results section
                this.showResults(data);
                
                // Start polling for updates
                this.startPolling(data.search_id);
                
                // Scroll to results
                document.getElementById('resultsSection')?.scrollIntoView({ behavior: 'smooth' });
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Search failed', 'error');
            }
        } catch (error) {
            console.error('Search submission error:', error);
            this.showNotification('Failed to submit search', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '🔍 Start Search';
        }
    }
    
    showResults(searchData) {
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection) return;
        
        resultsSection.style.display = 'block';
        
        // Update status
        this.updateSearchStatus(searchData);
        
        // If completed, show results
        if (searchData.status === 'completed' && searchData.results) {
            this.renderResults(searchData.results);
        }
    }
    
    updateSearchStatus(searchData) {
        const statusEl = document.getElementById('searchStatus');
        if (!statusEl) return;
        
        const statusMap = {
            'pending': { icon: '⏳', text: 'Pending', detail: 'Search queued for processing' },
            'in_progress': { icon: '🔄', text: 'In Progress', detail: 'Querying databases...' },
            'completed': { icon: '✅', text: 'Completed', detail: 'Search finished successfully' },
            'failed': { icon: '❌', text: 'Failed', detail: searchData.error || 'Search encountered an error' }
        };
        
        const status = statusMap[searchData.status] || statusMap.pending;
        
        statusEl.className = `search-status ${searchData.status}`;
        statusEl.innerHTML = `
            <div class="status-icon">${status.icon}</div>
            <div class="status-info">
                <div class="status-text">${status.text}</div>
                <div class="status-detail">${status.detail}</div>
            </div>
        `;
    }
    
    renderResults(results) {
        const summaryEl = document.getElementById('summaryContent');
        const modulesEl = document.getElementById('modulesContent');
        
        if (!results || results.length === 0) {
            summaryEl.innerHTML = '<p>No results found</p>';
            return;
        }
        
        // Render summary
        const summary = this.generateSummary(results);
        summaryEl.innerHTML = `
            <div class="summary-grid">
                <div class="summary-card">
                    <h4>Search Overview</h4>
                    <div class="summary-item">
                        <span class="summary-label">Total Modules</span>
                        <span class="summary-value">${results.length}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Successful</span>
                        <span class="summary-value">${summary.successful}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Failed</span>
                        <span class="summary-value">${summary.failed}</span>
                    </div>
                </div>
                <div class="summary-card">
                    <h4>Key Findings</h4>
                    ${summary.keyFindings.map(finding => `
                        <div class="summary-item">
                            <span class="summary-label">${finding.label}</span>
                            <span class="summary-value">${finding.value}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Render module results
        modulesEl.innerHTML = results.map(result => this.renderModuleResult(result)).join('');
    }
    
    generateSummary(results) {
        const successful = results.filter(r => r.success).length;
        const failed = results.length - successful;
        
        // Extract key findings
        const keyFindings = [];
        
        results.forEach(result => {
            if (result.success && result.data) {
                const data = typeof result.data === 'string' ? JSON.parse(result.data) : result.data;
                
                // Extract interesting fields
                if (data.name) keyFindings.push({ label: 'Name', value: data.name });
                if (data.email) keyFindings.push({ label: 'Email', value: data.email });
                if (data.location) keyFindings.push({ label: 'Location', value: data.location });
            }
        });
        
        // Remove duplicates
        const uniqueFindings = keyFindings.filter((f, i, arr) => 
            arr.findIndex(x => x.label === f.label && x.value === f.value) === i
        ).slice(0, 5);
        
        return { successful, failed, keyFindings: uniqueFindings };
    }
    
    renderModuleResult(result) {
        const config = this.moduleConfigs.find(m => m.key === result.module_name);
        const moduleName = config ? config.name : result.module_name;
        
        let confidenceClass = 'low';
        if (result.confidence_level >= 0.8) confidenceClass = 'high';
        else if (result.confidence_level >= 0.5) confidenceClass = 'medium';
        
        const confidencePercent = Math.round(result.confidence_level * 100);
        
        if (!result.success) {
            return `
                <div class="module-result-card">
                    <div class="module-result-header">
                        <div class="module-result-title">${moduleName}</div>
                        <span class="confidence-badge low">Failed</span>
                    </div>
                    <p style="color: #ef4444;">${result.error || 'No data available'}</p>
                </div>
            `;
        }
        
        const data = typeof result.data === 'string' ? JSON.parse(result.data) : result.data;
        
        return `
            <div class="module-result-card">
                <div class="module-result-header">
                    <div class="module-result-title">${moduleName}</div>
                    <span class="confidence-badge ${confidenceClass}">${confidencePercent}% Confidence</span>
                </div>
                <div class="module-result-data">
                    ${Object.entries(data).map(([key, value]) => `
                        <div class="data-row">
                            <div class="data-label">${this.formatLabel(key)}</div>
                            <div class="data-value">${this.formatValue(value)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    formatLabel(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    formatValue(value) {
        if (typeof value === 'object') {
            return JSON.stringify(value, null, 2);
        }
        return value;
    }
    
    startPolling(searchId) {
        this.stopPolling();
        
        this.pollInterval = setInterval(async () => {
            await this.checkSearchStatus(searchId);
        }, 5000); // Poll every 5 seconds
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }
    
    async checkSearchStatus(searchId) {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${this.API_BASE}/tracker/search/${searchId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentSearch = data;
                
                this.updateSearchStatus(data);
                
                if (data.status === 'completed' || data.status === 'failed') {
                    this.stopPolling();
                    
                    if (data.status === 'completed' && data.results) {
                        this.renderResults(data.results);
                        this.showNotification('Search completed!', 'success');
                    }
                }
            }
        } catch (error) {
            console.error('Failed to check search status:', error);
        }
    }
    
    async exportPDF() {
        if (!this.currentSearch || !this.currentSearch.search_id) {
            this.showNotification('No search results to export', 'error');
            return;
        }
        
        const btn = document.getElementById('btnExportPDF');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> Generating PDF...';
        
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(
                `${this.API_BASE}/tracker/search/${this.currentSearch.search_id}/export/pdf`,
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
                a.download = `tracker_report_${this.currentSearch.search_id}.pdf`;
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
    
    resetForm() {
        document.getElementById('trackerForm').reset();
        this.selectedModules.clear();
        
        document.querySelectorAll('.module-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        document.querySelectorAll('.module-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.updateCostSummary();
        
        // Hide results
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
        
        this.stopPolling();
        this.currentSearch = null;
    }
    
    showNotification(message, type = 'info') {
        // Simple notification system - can be enhanced
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
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }
}

// Initialize on page load
let trackerModule;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('trackerPage')) {
        trackerModule = new TrackerModule();
    }
});

// Tab switching
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const activeTab = document.querySelector(`.tab[data-tab="${tabName}"]`);
    const activeContent = document.getElementById(`${tabName}Content`);
    
    if (activeTab) activeTab.classList.add('active');
    if (activeContent) activeContent.classList.add('active');
}
