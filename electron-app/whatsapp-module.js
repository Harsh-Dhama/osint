/**
 * WhatsApp Profiler Module - Complete Frontend Implementation
 * 
 * Features:
 * - QR Code Display and Login
 * - Single Profile Scraping
 * - Bulk CSV Upload
 * - Progress Tracking
 * - Results Display
 * - Excel Export
 */

class WhatsAppProfiler {
    constructor(apiBaseUrl) {
        this.apiBaseUrl = apiBaseUrl;
        this.authToken = null;
        this.isLoggedIn = false;
        this.currentCaseId = null;
        this.scrapedProfiles = [];
        
        console.log('[WhatsApp] Module initialized');
    }
    
    setAuthToken(token) {
        this.authToken = token;
        console.log('[WhatsApp] Auth token set');
    }
    
    async loadUI(containerId) {
        console.log('[WhatsApp] Loading UI...');
        const container = document.getElementById(containerId);
        
        container.innerHTML = `
            <div class="whatsapp-profiler">
                <!-- Header -->
                <div class="module-header">
                    <h2>💬 WhatsApp Profile Scraper</h2>
                    <div class="session-status">
                        <span id="wa-session-status" class="status-badge status-offline">Not Logged In</span>
                        <button id="wa-logout-btn" class="btn btn-secondary btn-sm" style="display: none;">Close Session</button>
                    </div>
                </div>
                
                <!-- Login Section -->
                <div id="wa-login-section" class="section">
                    <div class="card">
                        <h3>🔐 WhatsApp Web Login</h3>
                        <p>Scan the QR code below with your WhatsApp mobile app to start scraping</p>
                        
                        <div id="wa-qr-container" class="qr-container" style="display: none;">
                            <img id="wa-qr-image" alt="WhatsApp QR Code" class="qr-image">
                            <p class="qr-instruction">Scan this QR code with WhatsApp</p>
                            <div class="qr-loading" id="wa-qr-loading">
                                <div class="spinner"></div>
                                <p>Waiting for scan...</p>
                            </div>
                        </div>
                        
                        <button id="wa-show-qr-btn" class="btn btn-primary btn-lg">
                            Show QR Code & Login
                        </button>
                        
                        <div id="wa-login-error" class="error-message" style="display: none;"></div>
                    </div>
                </div>
                
                <!-- Scraping Section (Hidden until logged in) -->
                <div id="wa-scraping-section" class="section" style="display: none;">
                    <!-- Case Selection -->
                    <div class="card">
                        <h3>📁 Select Case</h3>
                        <div class="form-group">
                            <label>Investigation Case</label>
                            <select id="wa-case-select" class="form-control">
                                <option value="">Loading cases...</option>
                            </select>
                        </div>
                    </div>
                    
                    <!-- Tabs -->
                    <div class="tabs">
                        <button class="tab-btn active" data-tab="single">Single Profile</button>
                        <button class="tab-btn" data-tab="bulk">Bulk Upload</button>
                        <button class="tab-btn" data-tab="results">Results</button>
                    </div>
                    
                    <!-- Single Profile Tab -->
                    <div id="tab-single" class="tab-content active">
                        <div class="card">
                            <h3>📱 Scrape Single Profile</h3>
                            <form id="wa-single-form">
                                <div class="form-group">
                                    <label>Phone Number (with country code)</label>
                                    <input type="text" id="wa-phone-input" class="form-control" 
                                           placeholder="+919876543210" required>
                                    <small>Include country code (e.g., +91 for India)</small>
                                </div>
                                <button type="submit" class="btn btn-primary" id="wa-scrape-btn">
                                    Scrape Profile
                                </button>
                            </form>
                            
                            <div id="wa-scrape-progress" class="progress-section" style="display: none;">
                                <div class="spinner"></div>
                                <p id="wa-scrape-status">Scraping profile...</p>
                            </div>
                            
                            <div id="wa-scrape-result" class="result-card" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <!-- Bulk Upload Tab -->
                    <div id="tab-bulk" class="tab-content">
                        <div class="card">
                            <h3>📊 Bulk Upload (CSV)</h3>
                            <p>Upload a CSV file with phone numbers</p>
                            
                            <div class="csv-format-info">
                                <strong>CSV Format:</strong>
                                <pre>phone_number
+919876543210
+919876543211
+919876543212</pre>
                            </div>
                            
                            <form id="wa-bulk-form">
                                <div class="form-group">
                                    <label>Upload CSV File</label>
                                    <input type="file" id="wa-csv-input" class="form-control" 
                                           accept=".csv" required>
                                </div>
                                <button type="submit" class="btn btn-primary">
                                    Upload & Scrape
                                </button>
                            </form>
                            
                            <div id="wa-bulk-progress" class="progress-section" style="display: none;">
                                <div class="progress-bar-container">
                                    <div id="wa-bulk-progress-bar" class="progress-bar"></div>
                                </div>
                                <p id="wa-bulk-status">Processing...</p>
                            </div>
                            
                            <div id="wa-bulk-results" class="results-list" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <!-- Results Tab -->
                    <div id="tab-results" class="tab-content">
                        <div class="card">
                            <div class="results-header">
                                <h3>📋 Scraped Profiles</h3>
                                <button id="wa-export-btn" class="btn btn-success">
                                    Export to Excel
                                </button>
                            </div>
                            
                            <div id="wa-profiles-list" class="profiles-grid">
                                <p class="empty-message">No profiles scraped yet</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        console.log('[WhatsApp] UI loaded, binding events...');
        this.bindEvents();
    }
    
    bindEvents() {
        // Show QR button
        document.getElementById('wa-show-qr-btn').addEventListener('click', () => {
            console.log('[WhatsApp] Show QR button clicked');
            this.showQRCode();
        });
        
        // Logout button
        document.getElementById('wa-logout-btn').addEventListener('click', () => {
            console.log('[WhatsApp] Logout button clicked');
            this.closeSession();
        });
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                console.log(`[WhatsApp] Switching to tab: ${tab}`);
                this.switchTab(tab);
            });
        });
        
        // Single scrape form
        document.getElementById('wa-single-form').addEventListener('submit', (e) => {
            e.preventDefault();
            console.log('[WhatsApp] Single scrape form submitted');
            this.scrapeSingleProfile();
        });
        
        // Bulk upload form
        document.getElementById('wa-bulk-form').addEventListener('submit', (e) => {
            e.preventDefault();
            console.log('[WhatsApp] Bulk upload form submitted');
            this.handleBulkUpload();
        });
        
        // Export button
        document.getElementById('wa-export-btn').addEventListener('click', () => {
            console.log('[WhatsApp] Export button clicked');
            this.exportProfiles();
        });
        
        // Case selection
        document.getElementById('wa-case-select').addEventListener('change', (e) => {
            this.currentCaseId = e.target.value;
            console.log(`[WhatsApp] Case selected: ${this.currentCaseId}`);
            if (this.currentCaseId) {
                this.loadCaseProfiles();
            }
        });
        
        console.log('[WhatsApp] All events bound');
    }
    
    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`tab-${tabName}`).classList.add('active');
        
        if (tabName === 'results' && this.currentCaseId) {
            this.loadCaseProfiles();
        }
    }
    
    async showQRCode() {
        console.log('[WhatsApp] Fetching QR code...');
        const btn = document.getElementById('wa-show-qr-btn');
        btn.disabled = true;
        btn.textContent = 'Loading...';
        
        try {
            const response = await this.apiCall('/api/whatsapp/qr-code', 'GET');
            console.log('[WhatsApp] QR code response:', response);
            
            if (response.is_logged_in) {
                console.log('[WhatsApp] Already logged in');
                this.handleLoginSuccess();
            } else if (response.browser_visible) {
                // New flow: Browser window opened with actual WhatsApp Web
                console.log('[WhatsApp] Browser window opened with WhatsApp Web');
                document.getElementById('wa-qr-container').style.display = 'block';
                
                // Hide the image and show a message instead
                const qrImage = document.getElementById('wa-qr-image');
                qrImage.style.display = 'none';
                
                const qrContainer = document.getElementById('wa-qr-container');
                qrContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px;">
                        <div style="font-size: 64px; margin-bottom: 20px;">🌐</div>
                        <h3 style="color: #25D366; margin-bottom: 15px;">WhatsApp Web Browser Opened</h3>
                        <p style="font-size: 16px; color: #666; margin-bottom: 20px;">
                            ${response.message || 'A browser window has opened with the real WhatsApp Web interface.'}
                        </p>
                        <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <p style="font-weight: bold; margin-bottom: 10px;">📱 Steps to scan:</p>
                            <ol style="text-align: left; display: inline-block; margin: 0; padding-left: 20px;">
                                <li>Look for the browser window that just opened</li>
                                <li>Open WhatsApp on your phone</li>
                                <li>Tap Menu (⋮) or Settings → Linked Devices</li>
                                <li>Tap "Link a Device"</li>
                                <li>Scan the QR code shown in the browser window</li>
                            </ol>
                        </div>
                        <div class="qr-loading">
                            <div class="spinner"></div>
                            <p>Waiting for you to scan the QR code in the browser window...</p>
                        </div>
                    </div>
                `;
                
                btn.style.display = 'none';
                
                // Wait for login
                this.waitForLogin();
            } else if (response.qr_code) {
                // Old flow: QR code image returned (fallback)
                console.log('[WhatsApp] QR code received, displaying...');
                document.getElementById('wa-qr-container').style.display = 'block';
                
                const qrImage = document.getElementById('wa-qr-image');
                try { qrImage.decoding = 'sync'; } catch (e) {}

                qrImage.onload = () => {
                    try {
                        qrImage.style.width = qrImage.naturalWidth + 'px';
                        qrImage.style.height = qrImage.naturalHeight + 'px';
                        qrImage.style.imageRendering = 'pixelated';
                        qrImage.style.border = 'none';
                        qrImage.style.boxShadow = 'none';
                        qrImage.style.background = 'transparent';
                        const container = document.getElementById('wa-qr-container');
                        if (container) container.style.padding = '24px';
                        console.log('[WhatsApp] ✓ QR image loaded (natural size)', qrImage.naturalWidth, qrImage.naturalHeight);
                    } catch (e) { console.warn('QR image onload handler failed', e); }
                };

                if (response.qr_code.startsWith('data:')) {
                    qrImage.src = response.qr_code;
                    console.log('[WhatsApp] ✓ QR image set (full data URI)');
                } else {
                    qrImage.src = `data:image/png;base64,${response.qr_code}`;
                    console.log('[WhatsApp] ✓ QR image set (base64 prepended)');
                }
                btn.style.display = 'none';
                
                // Wait for login
                this.waitForLogin();
            }
        } catch (error) {
            console.error('[WhatsApp] QR code error:', error);
            this.showError('wa-login-error', error.message);
            btn.disabled = false;
            btn.textContent = 'Show QR Code & Login';
        }
    }
    
    async waitForLogin() {
        console.log('[WhatsApp] Waiting for login...');
        try {
            const response = await this.apiCall('/api/whatsapp/wait-for-login?timeout=300', 'POST');
            console.log('[WhatsApp] Login response:', response);
            
            if (response.success) {
                console.log('[WhatsApp] ✓ Login successful!');
                this.handleLoginSuccess();
            }
        } catch (error) {
            console.error('[WhatsApp] Login wait error:', error);
            this.showError('wa-login-error', error.message);
            document.getElementById('wa-show-qr-btn').style.display = 'block';
            document.getElementById('wa-qr-container').style.display = 'none';
        }
    }
    
    handleLoginSuccess() {
        console.log('[WhatsApp] Handling login success...');
        this.isLoggedIn = true;
        
        // Update UI
        document.getElementById('wa-session-status').textContent = 'Logged In';
        document.getElementById('wa-session-status').className = 'status-badge status-online';
        document.getElementById('wa-logout-btn').style.display = 'inline-block';
        document.getElementById('wa-login-section').style.display = 'none';
        document.getElementById('wa-scraping-section').style.display = 'block';
        
        // Load cases
        this.loadCases();
        
        console.log('[WhatsApp] ✓ UI updated for logged in state');
    }
    
    async loadCases() {
        console.log('[WhatsApp] Loading cases...');
        try {
            const response = await this.apiCall('/api/cases', 'GET');
            console.log(`[WhatsApp] Loaded ${response.length} cases`);
            
            const select = document.getElementById('wa-case-select');
            select.innerHTML = '<option value="">Select a case...</option>';
            
            response.forEach(case_ => {
                const option = document.createElement('option');
                option.value = case_.id;
                option.textContent = `${case_.case_number} - ${case_.title}`;
                select.appendChild(option);
            });
            
            console.log('[WhatsApp] ✓ Cases loaded to dropdown');
        } catch (error) {
            console.error('[WhatsApp] Load cases error:', error);
            document.getElementById('wa-case-select').innerHTML = '<option value="">Error loading cases</option>';
        }
    }
    
    async scrapeSingleProfile() {
        console.log('[WhatsApp] Starting single profile scrape...');
        
        const phone = document.getElementById('wa-phone-input').value.trim();
        if (!this.currentCaseId) {
            alert('Please select a case first');
            return;
        }
        
        console.log(`[WhatsApp] Scraping ${phone} for case ${this.currentCaseId}`);
        
        const progress = document.getElementById('wa-scrape-progress');
        const result = document.getElementById('wa-scrape-result');
        const btn = document.getElementById('wa-scrape-btn');
        
        progress.style.display = 'block';
        result.style.display = 'none';
        btn.disabled = true;
        
        try {
            const response = await this.apiCall('/api/whatsapp/scrape', 'POST', {
                phone_number: phone,
                case_id: parseInt(this.currentCaseId)
            });
            
            console.log('[WhatsApp] ✓ Scrape successful:', response);
            
            progress.style.display = 'none';
            result.style.display = 'block';
            result.innerHTML = this.renderProfile(response);
            
            // Clear input
            document.getElementById('wa-phone-input').value = '';
            
        } catch (error) {
            console.error('[WhatsApp] Scrape error:', error);
            progress.style.display = 'none';
            result.style.display = 'block';
            result.innerHTML = `<div class="error-card"><strong>Error:</strong> ${error.message}</div>`;
        } finally {
            btn.disabled = false;
        }
    }
    
    async handleBulkUpload() {
        console.log('[WhatsApp] Starting bulk upload...');
        
        const fileInput = document.getElementById('wa-csv-input');
        const file = fileInput.files[0];
        
        if (!this.currentCaseId) {
            alert('Please select a case first');
            return;
        }
        
        if (!file) {
            alert('Please select a CSV file');
            return;
        }
        
        console.log(`[WhatsApp] Uploading CSV: ${file.name}`);
        
        try {
            // Parse CSV
            const formData = new FormData();
            formData.append('file', file);
            
            const uploadResponse = await fetch(
                `${this.apiBaseUrl}/api/whatsapp/upload/csv?case_id=${this.currentCaseId}`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`
                    },
                    body: formData
                }
            );
            
            if (!uploadResponse.ok) {
                throw new Error('CSV upload failed');
            }
            
            const uploadData = await uploadResponse.json();
            console.log(`[WhatsApp] ✓ CSV parsed: ${uploadData.phone_numbers.length} numbers`);
            
            // Start bulk scrape
            await this.bulkScrape(uploadData.phone_numbers);
            
        } catch (error) {
            console.error('[WhatsApp] Bulk upload error:', error);
            alert(`Error: ${error.message}`);
        }
    }
    
    async bulkScrape(phoneNumbers) {
        console.log(`[WhatsApp] Starting bulk scrape for ${phoneNumbers.length} numbers`);
        
        const progress = document.getElementById('wa-bulk-progress');
        const results = document.getElementById('wa-bulk-results');
        const status = document.getElementById('wa-bulk-status');
        const progressBar = document.getElementById('wa-bulk-progress-bar');
        
        progress.style.display = 'block';
        results.style.display = 'none';
        
        try {
            status.textContent = `Scraping ${phoneNumbers.length} profiles...`;
            
            const response = await this.apiCall('/api/whatsapp/scrape/bulk', 'POST', {
                case_id: parseInt(this.currentCaseId),
                phone_numbers: phoneNumbers
            });
            
            console.log('[WhatsApp] ✓ Bulk scrape completed:', response);
            
            progress.style.display = 'none';
            results.style.display = 'block';
            results.innerHTML = `
                <div class="success-card">
                    <h4>✓ Bulk Scrape Completed</h4>
                    <p>Successfully scraped ${response.saved} out of ${response.total} profiles</p>
                </div>
                <div class="bulk-results-list">
                    ${response.results.map(r => this.renderProfile(r)).join('')}
                </div>
            `;
            
            // Switch to results tab
            this.switchTab('results');
            
        } catch (error) {
            console.error('[WhatsApp] Bulk scrape error:', error);
            progress.style.display = 'none';
            alert(`Bulk scrape error: ${error.message}`);
        }
    }
    
    async loadCaseProfiles() {
        if (!this.currentCaseId) return;
        
        console.log(`[WhatsApp] Loading profiles for case ${this.currentCaseId}`);
        
        try {
            const profiles = await this.apiCall(`/api/whatsapp/case/${this.currentCaseId}`, 'GET');
            console.log(`[WhatsApp] ✓ Loaded ${profiles.length} profiles`);
            
            const container = document.getElementById('wa-profiles-list');
            
            if (profiles.length === 0) {
                container.innerHTML = '<p class="empty-message">No profiles for this case yet</p>';
            } else {
                container.innerHTML = profiles.map(p => this.renderProfile(p)).join('');
            }
            
            this.scrapedProfiles = profiles;
            
        } catch (error) {
            console.error('[WhatsApp] Load profiles error:', error);
        }
    }
    
    renderProfile(profile) {
        const statusClass = profile.is_available ? 'available' : 'unavailable';
        const statusText = profile.is_available ? 'Available' : 'Not Available';
        
        return `
            <div class="profile-card ${statusClass}">
                <div class="profile-header">
                    <span class="profile-status">${statusText}</span>
                    <span class="profile-phone">${profile.phone_number}</span>
                </div>
                <div class="profile-body">
                    <div class="profile-field">
                        <strong>Name:</strong>
                        <span>${profile.display_name || 'N/A'}</span>
                    </div>
                    <div class="profile-field">
                        <strong>About:</strong>
                        <span>${profile.about || 'N/A'}</span>
                    </div>
                    <div class="profile-field">
                        <strong>Last Seen:</strong>
                        <span>${profile.last_seen || 'N/A'}</span>
                    </div>
                    ${profile.error ? `<div class="profile-error">Error: ${profile.error}</div>` : ''}
                </div>
                <div class="profile-footer">
                    <small>Scraped: ${new Date(profile.scraped_at).toLocaleString()}</small>
                </div>
            </div>
        `;
    }
    
    async exportProfiles() {
        if (!this.currentCaseId) {
            alert('Please select a case first');
            return;
        }
        
        console.log(`[WhatsApp] Exporting profiles for case ${this.currentCaseId}`);
        
        const btn = document.getElementById('wa-export-btn');
        btn.disabled = true;
        btn.textContent = 'Exporting...';
        
        try {
            const response = await this.apiCall('/api/whatsapp/export', 'POST', {
                case_id: parseInt(this.currentCaseId),
                format: 'excel'
            });
            
            console.log('[WhatsApp] ✓ Export successful:', response);
            
            // Download file with authentication token
            await this.downloadFile(response.download_url, response.filename);
            
            alert(`Successfully exported ${response.profile_count} profiles!`);
            
        } catch (error) {
            console.error('[WhatsApp] Export error:', error);
            alert(`Export error: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Export to Excel';
        }
    }
    
    async downloadFile(downloadUrl, filename) {
        /**
         * Download file with authentication token using fetch + blob
         */
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${this.apiBaseUrl}${downloadUrl}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.statusText}`);
            }
            
            // Get the blob
            const blob = await response.blob();
            
            // Create a download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('[WhatsApp] ✓ File downloaded:', filename);
        } catch (error) {
            console.error('[WhatsApp] Download error:', error);
            throw error;
        }
    }
    
    async closeSession() {
        console.log('[WhatsApp] Closing session...');
        
        try {
            await this.apiCall('/api/whatsapp/close-session', 'POST');
            console.log('[WhatsApp] ✓ Session closed');
            
            // Reset UI
            this.isLoggedIn = false;
            document.getElementById('wa-session-status').textContent = 'Not Logged In';
            document.getElementById('wa-session-status').className = 'status-badge status-offline';
            document.getElementById('wa-logout-btn').style.display = 'none';
            document.getElementById('wa-login-section').style.display = 'block';
            document.getElementById('wa-scraping-section').style.display = 'none';
            document.getElementById('wa-qr-container').style.display = 'none';
            document.getElementById('wa-show-qr-btn').style.display = 'block';
            
        } catch (error) {
            console.error('[WhatsApp] Close session error:', error);
        }
    }
    
    async apiCall(endpoint, method = 'GET', body = null) {
        console.log(`[WhatsApp API] ${method} ${endpoint}`);
        
        const options = {
            method,
            headers: {
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            }
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${this.apiBaseUrl}${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            console.error(`[WhatsApp API] Error:`, data);
            throw new Error(data.detail || 'API request failed');
        }
        
        console.log(`[WhatsApp API] ✓ Success`);
        return data;
    }
    
    showError(elementId, message) {
        const errorDiv = document.getElementById(elementId);
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

// Export for use in renderer
window.WhatsAppProfiler = WhatsAppProfiler;
console.log('[WhatsApp] Module loaded successfully');
