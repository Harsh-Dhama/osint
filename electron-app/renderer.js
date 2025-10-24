// OSINT Platform - Renderer Process
const { ipcRenderer } = require('electron');

// State management
let currentUser = null;
let authToken = null;
let backendUrl = '';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    backendUrl = await ipcRenderer.invoke('get-backend-url');
    console.log('Backend URL:', backendUrl);
    
    // Check if user is already logged in
    const token = await ipcRenderer.invoke('get-store-value', 'authToken');
    if (token) {
        authToken = token;
        await verifyToken();
    }
    
    setupEventListeners();
});

// Global error handlers to help capture errors in DevTools and show in UI
window.addEventListener('error', (e) => {
    console.error('Window error captured:', e.error || e.message, e);
    const errEl = document.getElementById('loginError');
    if (errEl) errEl.textContent = 'Console error: ' + (e.error?.message || e.message);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    const errEl = document.getElementById('loginError');
    if (errEl) errEl.textContent = 'Unhandled rejection: ' + (e.reason?.message || JSON.stringify(e.reason));
});

// Event Listeners
function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Disclaimer checkbox
    const disclaimerCheckbox = document.getElementById('disclaimerAccept');
    if (disclaimerCheckbox) {
        disclaimerCheckbox.addEventListener('change', (e) => {
            document.getElementById('acceptDisclaimer').disabled = !e.target.checked;
        });
    }
    
    // Accept disclaimer button
    const acceptBtn = document.getElementById('acceptDisclaimer');
    if (acceptBtn) {
        acceptBtn.addEventListener('click', handleDisclaimerAccept);
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Navigation
    const navLinks = document.querySelectorAll('.nav-menu a');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = e.target.getAttribute('data-view');
            if (view) {
                navigateToView(view);
            }
        });
    });
}

// Authentication Functions
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        errorDiv.textContent = '';
        
        // Create form data
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        console.log('Attempting login POST to:', `${backendUrl}/api/auth/login`, 'payload:', formData.toString());

        const response = await fetch(`${backendUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });
        
        console.log('Login HTTP response status:', response.status, response.statusText);
        let data = null;
        try {
            data = await response.json();
        } catch (err) {
            // Could be non-JSON error or network problem
            console.error('Failed to parse login response as JSON:', err);
            const text = await response.text().catch(() => null);
            console.error('Login response text:', text);
            throw new Error('Invalid response from server: ' + (text || response.status));
        }

        if (!response.ok) {
            // Show backend-provided detail if present
            console.error('Login failed, server response:', data);
            throw new Error(data.detail || data.message || 'Login failed');
        }
        
        // Store token
        authToken = data.access_token;
        await ipcRenderer.invoke('set-store-value', 'authToken', authToken);
        
        // Get user info
        await getCurrentUser();
        
        // Check disclaimer acceptance
        if (!currentUser.disclaimer_accepted) {
            showDisclaimerModal();
        } else {
            showDashboard();
        }
        
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = error.message || 'Unknown error - check DevTools console';
    }
}

async function verifyToken() {
    try {
        await getCurrentUser();
        showDashboard();
    } catch (error) {
        // Token invalid, show login
        await handleLogout();
    }
}

async function getCurrentUser() {
    const response = await fetch(`${backendUrl}/api/auth/me`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
    
    if (!response.ok) {
        throw new Error('Failed to get user info');
    }
    
    currentUser = await response.json();
    return currentUser;
}

async function handleDisclaimerAccept() {
    try {
        const response = await fetch(`${backendUrl}/api/auth/accept-disclaimer`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ accepted: true })
        });
        
        if (!response.ok) {
            throw new Error('Failed to accept disclaimer');
        }
        
        currentUser.disclaimer_accepted = true;
        hideDisclaimerModal();
        showDashboard();
        
    } catch (error) {
        alert('Error accepting disclaimer: ' + error.message);
    }
}

async function handleLogout() {
    authToken = null;
    currentUser = null;
    await ipcRenderer.invoke('delete-store-value', 'authToken');
    
    // Hide dashboard, show login
    document.getElementById('mainDashboard').style.display = 'none';
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('loginForm').reset();
}

// UI Functions
function showDisclaimerModal() {
    document.getElementById('disclaimerModal').style.display = 'flex';
}

function hideDisclaimerModal() {
    document.getElementById('disclaimerModal').style.display = 'none';
}

function showDashboard() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('mainDashboard').style.display = 'flex';
    
    // Update user info
    document.getElementById('userInfo').textContent = 
        `${currentUser.full_name} (${currentUser.role})`;
    document.getElementById('userCredits').textContent = currentUser.credits;
    
    // Show admin link if admin
    if (currentUser.role === 'admin') {
        document.getElementById('adminLink').style.display = 'block';
    }
    
    // Load dashboard
    navigateToView('dashboard');
}

function navigateToView(view) {
    // Update active nav item
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-view') === view) {
            link.classList.add('active');
        }
    });
    
    // Update content title
    const titles = {
        'dashboard': 'Dashboard',
        'cases': 'Cases',
        'whatsapp': 'WhatsApp Profiler',
        'facial': 'Facial Recognition',
        'social': 'Social Media Scraper',
        'monitoring': 'Social Media Monitoring',
        'username': 'Username Searcher',
        'tracker': 'Number/Email Tracker',
        'reports': 'Reports',
        'admin': 'Admin Panel'
    };
    
    document.getElementById('contentTitle').textContent = titles[view] || view;
    
    // Load view content
    loadViewContent(view);
}

async function loadViewContent(view) {
    const contentBody = document.getElementById('contentBody');
    
    switch (view) {
        case 'dashboard':
            contentBody.innerHTML = `
                <h2>Welcome to OSINT Platform</h2>
                <p>Select a tool from the sidebar to begin your investigation.</p>
                <div style="margin-top: 30px;">
                    <h3>Quick Stats</h3>
                    <p>Total Cases: Loading...</p>
                    <p>Active Investigations: Loading...</p>
                    <p>Reports Generated: Loading...</p>
                </div>
            `;
            break;
            
        case 'cases':
            console.log('[Renderer] Loading Cases module...');
            contentBody.innerHTML = `
                <div class="cases-container">
                    <!-- Cases Header -->
                    <div class="cases-header">
                        <h2>📁 Case Management</h2>
                        <button id="create-case-btn" class="btn btn-primary">
                            ➕ Create New Case
                        </button>
                    </div>
                    
                    <!-- Cases Table -->
                    <div class="card mt-3">
                        <h3>Active Cases</h3>
                        <table class="cases-table" id="cases-table">
                            <thead>
                                <tr>
                                    <th>Case Number</th>
                                    <th>Title</th>
                                    <th>Priority</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="cases-tbody">
                                <tr><td colspan="6" style="text-align:center;">Loading cases...</td></tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Create/Edit Case Modal -->
                    <div id="case-modal" class="modal-overlay" style="display: none;">
                        <div class="modal-dialog">
                            <div class="modal-header">
                                <h3 id="modal-title">Create New Case</h3>
                                <button class="modal-close" onclick="document.getElementById('case-modal').style.display='none'">&times;</button>
                            </div>
                            <div class="modal-body">
                                <form id="case-form">
                                    <input type="hidden" id="case-id" value="">
                                    
                                    <div class="form-group">
                                        <label>Case Title *</label>
                                        <input type="text" id="case-title" class="form-control" required placeholder="e.g., Missing Person Investigation">
                                    </div>
                                    
                                    <div class="form-group">
                                        <label>Description</label>
                                        <textarea id="case-description" class="form-control" rows="4" placeholder="Detailed description of the case..."></textarea>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label>Priority</label>
                                        <select id="case-priority" class="form-control">
                                            <option value="low">🟢 Low</option>
                                            <option value="medium" selected>🟡 Medium</option>
                                            <option value="high">🔴 High</option>
                                        </select>
                                    </div>
                                    
                                    <div class="form-group" id="status-group" style="display: none;">
                                        <label>Status</label>
                                        <select id="case-status" class="form-control">
                                            <option value="open">Open</option>
                                            <option value="in_progress">In Progress</option>
                                            <option value="closed">Closed</option>
                                        </select>
                                    </div>
                                    
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary" onclick="document.getElementById('case-modal').style.display='none'">Cancel</button>
                                        <button type="submit" class="btn btn-primary" id="save-case-btn">Create Case</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Load cases and setup event listeners
            loadCases();
            
            // Create case button
            document.getElementById('create-case-btn').addEventListener('click', () => {
                console.log('[Cases] Opening create case modal');
                document.getElementById('modal-title').textContent = 'Create New Case';
                document.getElementById('case-id').value = '';
                document.getElementById('case-title').value = '';
                document.getElementById('case-description').value = '';
                document.getElementById('case-priority').value = 'medium';
                document.getElementById('status-group').style.display = 'none';
                document.getElementById('save-case-btn').textContent = 'Create Case';
                document.getElementById('case-modal').style.display = 'flex';
            });
            
            // Case form submit
            document.getElementById('case-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                await saveCaseForm();
            });
            break;
            
        case 'whatsapp':
            console.log('[Renderer] Loading WhatsApp module...');
            contentBody.innerHTML = '<div id="whatsapp-container"></div>';
            
            // Initialize WhatsApp module
            if (window.whatsappProfiler) {
                console.log('[Renderer] WhatsApp profiler already initialized');
            } else {
                console.log('[Renderer] Creating new WhatsApp profiler instance');
                window.whatsappProfiler = new window.WhatsAppProfiler(backendUrl);
                window.whatsappProfiler.setAuthToken(authToken);
            }
            
            await window.whatsappProfiler.loadUI('whatsapp-container');
            console.log('[Renderer] ✓ WhatsApp module loaded');
            break;
            
        case 'facial':
            contentBody.innerHTML = `
                <div class="card">
                    <h2>🔍 Facial Recognition System</h2>
                    <p>Upload an image to perform facial recognition search</p>
                    
                    <div class="form-group mt-3">
                        <label>Select Case</label>
                        <select id="facial-case-select" class="form-control">
                            <option value="">Select a case...</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Upload Image</label>
                        <input type="file" id="facial-image-input" class="form-control" accept="image/*">
                    </div>
                    
                    <button id="facial-search-btn" class="btn btn-primary mt-2">Start Facial Search</button>
                    
                    <div id="facial-result" class="mt-3" style="display: none;">
                        <h3>Search Results</h3>
                        <p>Feature coming soon - facial recognition in progress</p>
                    </div>
                </div>
            `;
            // Load cases for facial
            loadCasesForModule('facial-case-select');
            document.getElementById('facial-search-btn').addEventListener('click', async () => {
                const caseId = document.getElementById('facial-case-select').value;
                const fileInput = document.getElementById('facial-image-input');
                const resultDiv = document.getElementById('facial-result');
                
                if (!caseId) {
                    alert('Please select a case');
                    return;
                }
                if (!fileInput.files[0]) {
                    alert('Please select an image');
                    return;
                }
                
                try {
                    // Show loading
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = '<p class="text-info">🔍 Processing image and searching...</p>';
                    
                    // Convert image to base64
                    const file = fileInput.files[0];
                    const base64Image = await fileToBase64(file);
                    
                    // Remove data:image/...;base64, prefix if present
                    const cleanBase64 = base64Image.replace(/^data:image\/[a-z]+;base64,/, '');
                    
                    // Perform search
                    const searchData = {
                        case_id: parseInt(caseId),
                        image_base64: cleanBase64,
                        search_type: 'database_match'
                    };
                    
                    const result = await apiRequest('/api/facial/search', 'POST', searchData);
                    
                    // Display results
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <strong>✅ Search Completed!</strong>
                        </div>
                        <div class="card mt-3">
                            <h4>Search Details</h4>
                            <p><strong>Search ID:</strong> ${result.id}</p>
                            <p><strong>Case ID:</strong> ${result.case_id}</p>
                            <p><strong>Search Type:</strong> ${result.search_type}</p>
                            <p><strong>Timestamp:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
                            <p><strong>Image Path:</strong> ${result.source_image_path}</p>
                        </div>
                        <div class="alert alert-info mt-3">
                            <strong>ℹ️ Note:</strong> Image has been saved and indexed. 
                            Facial recognition matching is now active. Results will be displayed when matches are found.
                        </div>
                    `;
                } catch (error) {
                    console.error('Facial search error:', error);
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>❌ Error:</strong> ${error.message || 'Failed to perform search'}
                        </div>
                    `;
                }
            });
            break;
            
        case 'tracker':
            contentBody.innerHTML = `
                <div class="card">
                    <h2>📞 Number/Email Tracker</h2>
                    <p>Search for information about phone numbers and email addresses</p>
                    <div class="alert alert-info">
                        <strong>Credits:</strong> Each search costs 10 credits. Your balance: <span id="tracker-credits">Loading...</span>
                    </div>
                    
                    <div class="form-group mt-3">
                        <label>Select Case</label>
                        <select id="tracker-case-select" class="form-control">
                            <option value="">Select a case...</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Search Type</label>
                        <select id="tracker-type" class="form-control">
                            <option value="phone">Phone Number</option>
                            <option value="email">Email Address</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Enter Value</label>
                        <input type="text" id="tracker-value" class="form-control" placeholder="e.g., +919876543210 or email@example.com">
                    </div>
                    
                    <button id="tracker-search-btn" class="btn btn-primary">Search (10 Credits)</button>
                    
                    <div id="tracker-result" class="mt-3" style="display: none;">
                        <h3>Search Results</h3>
                        <p>Feature coming soon - bot-based tracking in progress</p>
                    </div>
                </div>
            `;
            // Load cases and credits
            loadCasesForModule('tracker-case-select');
            loadTrackerCredits();
            document.getElementById('tracker-search-btn').addEventListener('click', async () => {
                const caseId = document.getElementById('tracker-case-select').value;
                const searchType = document.getElementById('tracker-type').value;
                const searchValue = document.getElementById('tracker-value').value.trim();
                const resultDiv = document.getElementById('tracker-result');
                
                if (!caseId) {
                    alert('Please select a case');
                    return;
                }
                if (!searchValue) {
                    alert('Please enter a value to search');
                    return;
                }
                
                // Validate input format
                if (searchType === 'phone' && !searchValue.match(/^\+?[0-9]{10,15}$/)) {
                    alert('Please enter a valid phone number (10-15 digits, can start with +)');
                    return;
                }
                
                if (searchType === 'email' && !searchValue.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
                    alert('Please enter a valid email address');
                    return;
                }
                
                try {
                    // Show loading
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = '<p class="text-info">🔍 Searching... (10 credits will be deducted)</p>';
                    
                    // Perform search
                    const searchData = {
                        case_id: parseInt(caseId),
                        search_type: searchType,
                        search_value: searchValue
                    };
                    
                    const result = await apiRequest('/api/tracker/search', 'POST', searchData);
                    
                    // Reload credits
                    await loadTrackerCredits();
                    
                    // Display results
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <strong>✅ Search Completed!</strong> (10 credits deducted)
                        </div>
                        <div class="card mt-3">
                            <h4>Search Details</h4>
                            <p><strong>Search ID:</strong> ${result.id}</p>
                            <p><strong>Case ID:</strong> ${result.case_id}</p>
                            <p><strong>Search Type:</strong> ${result.search_type.toUpperCase()}</p>
                            <p><strong>Search Value:</strong> ${result.search_value}</p>
                            <p><strong>Timestamp:</strong> ${new Date(result.searched_at).toLocaleString()}</p>
                            <p><strong>Credits Used:</strong> ${result.credits_used}</p>
                        </div>
                        <div class="alert alert-info mt-3">
                            <strong>ℹ️ Search Initiated:</strong> Your search has been queued. 
                            Results will be aggregated from multiple sources and available in the case file shortly.
                            Check back in a few minutes.
                        </div>
                        <button class="btn btn-secondary mt-2" onclick="viewCaseSearches(${caseId})">View All Searches for This Case</button>
                    `;
                } catch (error) {
                    console.error('Tracker search error:', error);
                    
                    // Check if insufficient credits error
                    if (error.message && error.message.includes('Insufficient credits')) {
                        resultDiv.innerHTML = `
                            <div class="alert alert-danger">
                                <strong>❌ Insufficient Credits</strong>
                                <p>${error.message}</p>
                                <p>Please contact an administrator to top up your credits.</p>
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <div class="alert alert-danger">
                                <strong>❌ Error:</strong> ${error.message || 'Failed to perform search'}
                            </div>
                        `;
                    }
                }
            });
            break;
            
        default:
            contentBody.innerHTML = `
                <div class="card">
                    <h2>${view}</h2>
                    <div class="alert alert-info">
                        <strong>ℹ️ Coming Soon</strong>
                        <p>This module is currently being developed. Check back soon for updates!</p>
                    </div>
                </div>
            `;
    }
}

// Helper function to load cases for modules
async function loadCasesForModule(selectId) {
    try {
        const cases = await apiRequest('/api/cases');
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">Select a case...</option>';
            cases.forEach(c => {
                const option = document.createElement('option');
                option.value = c.id;
                option.textContent = `${c.case_number} - ${c.title}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading cases:', error);
    }
}

// Helper function to load tracker credits
async function loadTrackerCredits() {
    try {
        const data = await apiRequest('/api/tracker/credits');
        const creditsSpan = document.getElementById('tracker-credits');
        if (creditsSpan) {
            creditsSpan.textContent = data.credits;
        }
    } catch (error) {
        console.error('Error loading credits:', error);
        const creditsSpan = document.getElementById('tracker-credits');
        if (creditsSpan) {
            creditsSpan.textContent = 'Error';
        }
    }
}

// Cases Management Functions
async function loadCases() {
    console.log('[Cases] Loading all cases...');
    try {
        const cases = await apiRequest('/api/cases');
        console.log(`[Cases] Loaded ${cases.length} cases`);
        
        const tbody = document.getElementById('cases-tbody');
        if (!tbody) return;
        
        if (cases.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#999;">No cases found. Create your first case!</td></tr>';
            return;
        }
        
        tbody.innerHTML = cases.map(c => {
            const priority = c.priority === 'high' ? '🔴 High' : c.priority === 'medium' ? '🟡 Medium' : '🟢 Low';
            const status = c.status === 'open' ? '<span class="badge badge-success">Open</span>' : 
                          c.status === 'in_progress' ? '<span class="badge badge-warning">In Progress</span>' :
                          '<span class="badge badge-secondary">Closed</span>';
            const date = new Date(c.created_at).toLocaleDateString();
            
            return `
                <tr>
                    <td><strong>${c.case_number}</strong></td>
                    <td>${c.title}</td>
                    <td>${priority}</td>
                    <td>${status}</td>
                    <td>${date}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="editCase(${c.id})">✏️ Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteCase(${c.id}, '${c.case_number}')">🗑️ Delete</button>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('[Cases] Error loading cases:', error);
        alert('Error loading cases: ' + error.message);
    }
}

async function editCase(caseId) {
    console.log(`[Cases] Editing case ${caseId}`);
    try {
        const caseData = await apiRequest(`/api/cases/${caseId}`);
        
        document.getElementById('modal-title').textContent = 'Edit Case';
        document.getElementById('case-id').value = caseData.id;
        document.getElementById('case-title').value = caseData.title;
        document.getElementById('case-description').value = caseData.description || '';
        document.getElementById('case-priority').value = caseData.priority;
        document.getElementById('case-status').value = caseData.status;
        document.getElementById('status-group').style.display = 'block';
        document.getElementById('save-case-btn').textContent = 'Update Case';
        document.getElementById('case-modal').style.display = 'flex';
        
    } catch (error) {
        console.error('[Cases] Error loading case:', error);
        alert('Error loading case: ' + error.message);
    }
}

async function saveCaseForm() {
    console.log('[Cases] Saving case form...');
    const caseId = document.getElementById('case-id').value;
    const isEdit = caseId !== '';
    
    const caseData = {
        title: document.getElementById('case-title').value.trim(),
        description: document.getElementById('case-description').value.trim(),
        priority: document.getElementById('case-priority').value
    };
    
    if (isEdit) {
        caseData.status = document.getElementById('case-status').value;
    }
    
    if (!caseData.title) {
        alert('Please enter a case title');
        return;
    }
    
    try {
        if (isEdit) {
            console.log(`[Cases] Updating case ${caseId}`);
            await apiRequest(`/api/cases/${caseId}`, {
                method: 'PUT',
                body: JSON.stringify(caseData)
            });
            console.log('[Cases] ✓ Case updated successfully');
        } else {
            console.log('[Cases] Creating new case');
            await apiRequest('/api/cases', {
                method: 'POST',
                body: JSON.stringify(caseData)
            });
            console.log('[Cases] ✓ Case created successfully');
        }
        
        document.getElementById('case-modal').style.display = 'none';
        loadCases();
        alert(isEdit ? 'Case updated successfully!' : 'Case created successfully!');
        
    } catch (error) {
        console.error('[Cases] Error saving case:', error);
        alert('Error saving case: ' + error.message);
    }
}

async function deleteCase(caseId, caseNumber) {
    if (!confirm(`Are you sure you want to delete case ${caseNumber}?\n\nThis will permanently delete all associated data including:\n- WhatsApp profiles\n- Facial searches\n- Tracker results\n- All other investigation data\n\nThis action cannot be undone!`)) {
        return;
    }
    
    console.log(`[Cases] Deleting case ${caseId}`);
    try {
        await apiRequest(`/api/cases/${caseId}`, {
            method: 'DELETE'
        });
        console.log('[Cases] ✓ Case deleted successfully');
        loadCases();
        alert('Case deleted successfully');
    } catch (error) {
        console.error('[Cases] Error deleting case:', error);
        alert('Error deleting case: ' + error.message);
    }
}

// Make functions globally available
window.editCase = editCase;
window.deleteCase = deleteCase;

// Helper function to convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// View all tracker searches for a case
async function viewCaseSearches(caseId) {
    try {
        const searches = await apiRequest(`/api/tracker/case/${caseId}`);
        
        if (searches.length === 0) {
            alert('No searches found for this case yet.');
            return;
        }
        
        let html = `
            <div class="card">
                <h3>All Searches for Case ID: ${caseId}</h3>
                <table class="cases-table mt-3">
                    <thead>
                        <tr>
                            <th>Search ID</th>
                            <th>Type</th>
                            <th>Value</th>
                            <th>Credits Used</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        searches.forEach(search => {
            html += `
                <tr>
                    <td>${search.id}</td>
                    <td><span class="badge badge-info">${search.search_type.toUpperCase()}</span></td>
                    <td>${search.search_value}</td>
                    <td>${search.credits_used}</td>
                    <td>${new Date(search.searched_at).toLocaleString()}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        document.getElementById('tracker-result').innerHTML = html;
        
    } catch (error) {
        console.error('Error loading case searches:', error);
        alert('Error loading case searches: ' + error.message);
    }
}

// Make function globally available
window.viewCaseSearches = viewCaseSearches;

// API Helper Functions
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    const response = await fetch(`${backendUrl}${endpoint}`, {
        ...options,
        ...defaultOptions
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }
    
    return response.json();
}

// Export for use in other modules
window.api = {
    request: apiRequest,
    getCurrentUser: () => currentUser,
    getAuthToken: () => authToken
};
