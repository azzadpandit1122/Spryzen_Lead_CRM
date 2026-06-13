/* ==========================================================================
   CLINETHUB FRONTEND ENGINE (js/app.js)
   ========================================================================== */

const API_BASE = window.location.origin;

// Application State
const state = {
    token: localStorage.getItem('token') || null,
    user: null,
    activeView: 'dashboard',
    charts: {
        line: null,
        pie: null
    },
    systemUsers: [] // Used for assignments
};

// Bootstrap toast helper
let toastInstance = null;
function showToast(message, isError = false) {
    const toastEl = document.getElementById('liveToast');
    const toastMsgEl = document.getElementById('toastMessage');
    
    if (!toastInstance) {
        toastInstance = new bootstrap.Toast(toastEl, { delay: 4000 });
    }
    
    toastEl.classList.remove('success-toast', 'error-toast');
    toastEl.classList.add(isError ? 'error-toast' : 'success-toast');
    toastMsgEl.textContent = message;
    toastInstance.show();
}

// Clean API Request Helper
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    // Set headers
    const headers = options.headers || {};
    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }
    
    // Default to JSON content type unless it's FormData
    if (!(options.body instanceof FormData) && typeof options.body === 'object') {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }
    
    options.headers = headers;
    
    try {
        const response = await fetch(url, options);
        
        // Handle unauthorized token
        if (response.status === 401) {
            handleLogout();
            showToast("Session expired. Please sign in again.", true);
            throw new Error("Unauthorized");
        }
        
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            const errMsg = errData.detail || `Error: ${response.statusText}`;
            throw new Error(errMsg);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error on ${endpoint}:`, error);
        throw error;
    }
}

/* ==========================================================================
   AUTHENTICATION & PROFILE MANAGEMENT
   ========================================================================== */

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const usernameEl = document.getElementById('login-username');
    const passwordEl = document.getElementById('login-password');
    const loginBtn = document.getElementById('login-btn');
    const spinner = loginBtn.querySelector('.spinner-border');
    
    loginBtn.disabled = true;
    spinner.classList.remove('d-none');
    
    try {
        const formData = new FormData();
        formData.append('username', usernameEl.value.trim());
        formData.append('password', passwordEl.value);
        
        const response = await apiRequest('/api/auth/login', {
            method: 'POST',
            body: formData
        });
        
        state.token = response.access_token;
        localStorage.setItem('token', state.token);
        
        await fetchUserProfile();
        
        usernameEl.value = '';
        passwordEl.value = '';
        
        initApp();
        showToast("Signed in successfully!");
        
    } catch (error) {
        showToast(error.message, true);
    } finally {
        loginBtn.disabled = false;
        spinner.classList.add('d-none');
    }
});

async function fetchUserProfile() {
    try {
        const user = await apiRequest('/api/auth/me');
        state.user = user;
        
        // Update sidebar header & UI elements
        document.getElementById('user-display-name').textContent = user.full_name;
        document.getElementById('user-display-role').textContent = user.role.replace('_', ' ');
        document.getElementById('user-avatar-char').textContent = user.full_name.charAt(0).toUpperCase();
        
        // Show Admin Nav Link if authorized
        const adminNavItem = document.getElementById('nav-admin-item');
        if (user.role === 'admin') {
            adminNavItem.classList.remove('d-none');
        } else {
            adminNavItem.classList.add('d-none');
        }
        
        if (user.role === 'admin' || user.role === 'sales_manager') {
            fetchSystemUsers();
        }
    } catch (error) {
        handleLogout();
    }
}

function handleLogout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('token');
    
    document.getElementById('app-container').classList.add('d-none');
    document.getElementById('login-container').classList.remove('d-none');
}

document.getElementById('logout-btn').addEventListener('click', () => {
    handleLogout();
    document.getElementById('app-container').classList.remove('sidebar-collapsed');
    showToast("Logged out successfully");
});

// Sidebar Toggle & Backdrop Event Listeners
document.getElementById('sidebar-toggle-btn').addEventListener('click', () => {
    document.getElementById('app-container').classList.toggle('sidebar-collapsed');
});

const sidebarBackdrop = document.getElementById('sidebar-backdrop');
if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', () => {
        document.getElementById('app-container').classList.remove('sidebar-collapsed');
    });
}

/* ==========================================================================
   NAVIGATION & VIEWS SYSTEM
   ========================================================================== */

document.querySelectorAll('#sidebar .nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        document.querySelectorAll('#sidebar .nav-link').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        const viewName = link.getAttribute('data-view');
        switchView(viewName);
        
        // Auto-close sidebar on mobile after selecting a view
        if (window.innerWidth <= 768) {
            document.getElementById('app-container').classList.remove('sidebar-collapsed');
        }
    });
});

function switchView(viewName) {
    state.activeView = viewName;
    
    document.querySelectorAll('.app-view').forEach(view => view.classList.add('d-none'));
    
    const activeViewEl = document.getElementById(`view-${viewName}`);
    if (activeViewEl) {
        activeViewEl.classList.remove('d-none');
    }
    
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    
    if (viewName === 'dashboard') {
        pageTitle.textContent = "Dashboard";
        pageSubtitle.textContent = "Overview of leads collection and business pipeline analytics";
        refreshDashboard();
    } else if (viewName === 'leads') {
        pageTitle.textContent = "Client Leads Board";
        pageSubtitle.textContent = "Review details, assign operators, claim prospects, and update engagement status";
        refreshLeadsList();
    } else if (viewName === 'scanner') {
        pageTitle.textContent = "Project Scanner Engine";
        pageSubtitle.textContent = "Configure targeting parameters and launch compliance searches across public platforms";
        loadScannerConfig();
    } else if (viewName === 'reminders') {
        pageTitle.textContent = "Follow-Ups & Reminders";
        pageSubtitle.textContent = "Manage client outreach notifications and schedule alerts";
        refreshReminders();
    } else if (viewName === 'admin') {
        pageTitle.textContent = "Admin User Panel";
        pageSubtitle.textContent = "Create user accounts, manage roles, and audit access control logs";
        refreshAdminPanel();
    }
}

// Clock updates
setInterval(() => {
    const timeDisplay = document.getElementById('current-time-display');
    if (timeDisplay) {
        timeDisplay.textContent = new Date().toLocaleTimeString();
    }
}, 1000);

/* ==========================================================================
   DASHBOARD / ANALYTICS VIEW
   ========================================================================== */

async function refreshDashboard() {
    try {
        const metrics = await apiRequest('/api/reports/dashboard');
        
        // Update stats counters
        document.getElementById('stat-total-leads').textContent = metrics.lead_metrics.total_leads;
        document.getElementById('stat-leads-conversion').textContent = `${metrics.lead_metrics.pipeline_conversion_rate}%`;
        document.getElementById('stat-active-reminders').textContent = metrics.sales_metrics.follow_ups_scheduled;
        document.getElementById('stat-won-deals').textContent = metrics.sales_metrics.opportunities_won;
        document.getElementById('stat-lost-deals').textContent = `${metrics.sales_metrics.opportunities_lost} lost opportunities`;
        document.getElementById('stat-calls-made').textContent = metrics.sales_metrics.calls_made;
        
        const engagementRate = metrics.lead_metrics.total_leads > 0 
            ? Math.round((metrics.sales_metrics.calls_made / metrics.lead_metrics.total_leads) * 100) 
            : 0;
        document.getElementById('stat-contact-rate').textContent = `${engagementRate}%`;
        
        renderDashboardCharts(metrics.lead_metrics);
        renderAuditLogs(metrics.recent_activities);
        
    } catch (err) {
        showToast("Error updating dashboard data.", true);
    }
}

function renderDashboardCharts(metrics) {
    const lineCtx = document.getElementById('leadsLineChart').getContext('2d');
    const pieCtx = document.getElementById('sourcesPieChart').getContext('2d');
    
    if (state.charts.line) state.charts.line.destroy();
    if (state.charts.pie) state.charts.pie.destroy();
    
    const dateLabels = Object.keys(metrics.leads_by_date);
    const dateCounts = Object.values(metrics.leads_by_date);
    
    state.charts.line = new Chart(lineCtx, {
        type: 'line',
        data: {
            labels: dateLabels.map(d => d.slice(5)), // Format to MM-DD
            datasets: [{
                label: 'Opportunities Discovered',
                data: dateCounts,
                borderColor: '#1e293b',
                backgroundColor: 'rgba(30, 41, 59, 0.05)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: '#3b82f6',
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    grid: { color: '#f1f5f9' },
                    ticks: { color: '#64748b', stepSize: 1 }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b' }
                }
            }
        }
    });
    
    const sourceLabels = Object.keys(metrics.leads_by_source);
    const sourceCounts = Object.values(metrics.leads_by_source);
    
    state.charts.pie = new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels: sourceLabels,
            datasets: [{
                data: sourceCounts,
                backgroundColor: [
                    '#0a66c2',  // LinkedIn
                    '#e1306c',  // Instagram
                    '#0f172a',  // X (Twitter)
                    '#166534'   // Google Maps
                ],
                borderWidth: 1.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#0f172a', font: { family: 'Outfit', size: 10 } }
                }
            },
            cutout: '70%'
        }
    });
}

function renderAuditLogs(logs) {
    const tbody = document.getElementById('audit-log-tbody');
    tbody.innerHTML = '';
    
    if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">No recent activity found.</td></tr>`;
        return;
    }
    
    logs.forEach(log => {
        tbody.innerHTML += `
            <tr>
                <td class="text-muted small">${log.timestamp}</td>
                <td><span class="badge bg-light text-dark border">${log.username}</span></td>
                <td><span class="badge bg-light text-dark text-uppercase small" style="border: 1px solid var(--border-darker);">${log.action}</span></td>
                <td class="text-truncate" style="max-width: 400px;" title="${log.details}">${log.details}</td>
            </tr>
        `;
    });
}

/* ==========================================================================
   CLIENT LEADS VIEW & MANAGEMENT
   ========================================================================= */

let loadedLeads = [];

document.getElementById('lead-filter-btn').addEventListener('click', refreshLeadsList);
document.getElementById('lead-filter-reset-btn').addEventListener('click', () => {
    document.getElementById('lead-filter-keyword').value = '';
    document.getElementById('lead-filter-source').value = '';
    document.getElementById('lead-filter-status').value = '';
    document.getElementById('lead-filter-date-from').value = '';
    document.getElementById('lead-filter-date-to').value = '';
    refreshLeadsList();
});

async function refreshLeadsList() {
    const keyword = document.getElementById('lead-filter-keyword').value.trim();
    const source = document.getElementById('lead-filter-source').value;
    const status = document.getElementById('lead-filter-status').value;
    const dateFrom = document.getElementById('lead-filter-date-from').value;
    const dateTo = document.getElementById('lead-filter-date-to').value;
    
    let queryParams = [];
    if (keyword) queryParams.push(`keyword=${encodeURIComponent(keyword)}`);
    if (source) queryParams.push(`source=${encodeURIComponent(source)}`);
    if (status) queryParams.push(`status=${encodeURIComponent(status)}`);
    if (dateFrom) queryParams.push(`date_from=${dateFrom}`);
    if (dateTo) queryParams.push(`date_to=${dateTo}`);
    
    const queryString = queryParams.length > 0 ? `?${queryParams.join('&')}` : '';
    
    try {
        const leads = await apiRequest(`/api/leads${queryString}`);
        loadedLeads = leads;
        
        document.getElementById('leads-count-summary').innerHTML = `<i class="bi bi-funnel text-primary me-2"></i>${leads.length} Opportunities Identified`;
        
        renderLeadsList(leads);
        populateLeadsSelect(leads);
    } catch (err) {
        showToast("Error retrieving leads.", true);
    }
}

function renderLeadsList(leads) {
    const tbody = document.getElementById('leads-list-tbody');
    tbody.innerHTML = '';
    
    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-5">
                    <i class="bi bi-inbox fs-2 d-block mb-3"></i>
                    No leads collected yet. Head to the <strong>Project Scanner</strong> to run a compliance scan!
                </td>
            </tr>
        `;
        return;
    }
    
    leads.forEach(lead => {
        let srcClass = 'source-linkedin';
        if (lead.source === 'Instagram') srcClass = 'source-instagram';
        else if (lead.source === 'X (Twitter)') srcClass = 'source-twitter';
        else if (lead.source === 'Google Maps') srcClass = 'source-google-maps';
        else if (lead.source === 'Upwork') srcClass = 'source-upwork';
        else if (lead.source === 'Reddit') srcClass = 'source-reddit';
        else if (lead.source === 'Wellfound') srcClass = 'source-wellfound';
        else if (lead.source === 'GitHub') srcClass = 'source-github';
        
        let statusClass = 'status-new-lead';
        if (lead.status === 'Contacted') statusClass = 'status-contacted';
        else if (lead.status === 'Interested') statusClass = 'status-interested';
        else if (lead.status === 'Follow Up Required') statusClass = 'status-follow-up-required';
        else if (lead.status === 'Proposal Sent') statusClass = 'status-proposal-sent';
        else if (lead.status === 'Negotiation') statusClass = 'status-negotiation';
        else if (lead.status === 'Won') statusClass = 'status-won';
        else if (lead.status === 'Lost') statusClass = 'status-lost';
        else if (lead.status === 'Closed') statusClass = 'status-closed';
        
        let pClass = 'priority-normal';
        if (lead.priority === 'Best Opportunity') pClass = 'priority-best';
        else if (lead.priority === 'Better Opportunity') pClass = 'priority-better';
        else if (lead.priority === 'Low Priority') pClass = 'priority-low';
        
        let trustBadgeClass = 'bg-warning-subtle text-warning border border-warning-subtle';
        if (lead.trust_score >= 90) trustBadgeClass = 'bg-success-subtle text-success border border-success-subtle';
        else if (lead.trust_score >= 80) trustBadgeClass = 'bg-info-subtle text-info border border-info-subtle';
        
        let assigneeText = '<span class="text-muted small">Unassigned</span>';
        if (lead.assigned_to) {
            assigneeText = `<span class="badge bg-light text-dark border">${lead.assigned_to.full_name}</span>`;
        }
        
        let claimBtnHtml = '';
        if (!lead.claimed_by_id && !lead.assigned_to_id) {
            claimBtnHtml = `<button class="btn btn-sm btn-outline-success px-2 py-1 me-1" onclick="claimLeadOpportunity(${lead.id})" title="Claim Opportunity"><i class="bi bi-person-check-fill"></i> Claim</button>`;
        }
        
        let assignBtnHtml = '';
        if (state.user && (state.user.role === 'admin' || state.user.role === 'sales_manager')) {
            assignBtnHtml = `<button class="btn btn-sm btn-outline-info px-2 py-1 me-1" onclick="openAssignModal(${lead.id}, '${lead.project_name.replace(/'/g, "\\'")}')" title="Assign Lead"><i class="bi bi-people-fill"></i></button>`;
        }
        
        let deleteBtnHtml = '';
        if (state.user && (state.user.role === 'admin' || state.user.role === 'sales_manager')) {
            deleteBtnHtml = `<button class="btn btn-sm btn-outline-danger px-2 py-1" onclick="deleteLeadOpportunity(${lead.id})" title="Delete Lead"><i class="bi bi-trash-fill"></i></button>`;
        }
        
        tbody.innerHTML += `
            <tr>
                <td>
                    <div class="lead-hover-trigger" data-lead-id="${lead.id}" onclick="openViewLeadModal(${lead.id})" style="cursor: pointer;">
                        <div class="d-flex align-items-center mb-1">
                            <div class="fw-bold text-dark hover-underline">${lead.project_name}</div>
                            <span class="badge ${trustBadgeClass} ms-2" style="font-size: 0.65rem;">
                                <i class="bi bi-shield-fill-check me-1"></i>Trust: ${lead.trust_score || 85}%
                            </span>
                        </div>
                        <div class="text-muted small text-truncate" style="max-width: 320px;">
                            ${lead.project_description ? lead.project_description.split('###')[0].replace(/#+/g, '').trim() : 'No description'}
                        </div>
                        <div class="text-muted small mt-1"><i class="bi bi-calendar-check me-1"></i>Collected: ${lead.collection_date} ${lead.collection_time.slice(0,5)}</div>
                        ${lead.trust_factors ? `<div class="text-muted small mt-1" style="font-size: 0.72rem;"><i class="bi bi-patch-check-fill text-primary me-1"></i><span class="text-secondary font-monospace">${lead.trust_factors}</span></div>` : ''}
                    </div>
                </td>
                <td>
                    ${lead.source_link ? `
                        <a href="${lead.source_link}" target="_blank" class="badge badge-source ${srcClass} text-decoration-none" title="Visit Lead Source Link">
                            ${lead.source} <i class="bi bi-box-arrow-up-right ms-1"></i>
                        </a>
                    ` : `
                        <span class="badge badge-source ${srcClass}">${lead.source}</span>
                    `}
                </td>
                <td>
                    <span class="small text-muted"><i class="bi bi-geo-alt-fill text-danger me-1"></i>${lead.location || 'Unknown'}</span>
                </td>
                <td>
                    <div class="fw-semibold small text-dark">${lead.contact_name || 'N/A'}</div>
                    <div class="small text-muted">${lead.email_address || ''}</div>
                    <div class="small text-muted">${lead.phone_number || ''}</div>
                </td>
                <td>
                    <span class="badge ${statusClass}">${lead.status}</span>
                </td>
                <td>
                    <span class="badge ${pClass}">${lead.priority}</span>
                </td>
                <td>${assigneeText}</td>
                <td class="text-end">
                    <div class="d-flex justify-content-end align-items-center">
                        ${claimBtnHtml}
                        ${assignBtnHtml}
                        <button class="btn btn-sm btn-outline-info px-2 py-1 me-1" onclick="openViewLeadModal(${lead.id})" title="View Vetting Details"><i class="bi bi-eye-fill"></i></button>
                        <button class="btn btn-sm btn-outline-primary px-2 py-1 me-1" onclick="openEditLeadModal(${lead.id})" title="Edit Details"><i class="bi bi-pencil-fill"></i></button>
                        ${deleteBtnHtml}
                    </div>
                </td>
            </tr>
        `;
    });
    
    // Initialize hover preview cards for all triggers
    setupLeadHoverCards();
}

async function claimLeadOpportunity(leadId) {
    try {
        await apiRequest(`/api/leads/${leadId}/claim`, { method: 'POST' });
        showToast("Lead claimed successfully!");
        refreshLeadsList();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deleteLeadOpportunity(leadId) {
    if (!confirm("Are you sure you want to delete this opportunity?")) return;
    try {
        await apiRequest(`/api/leads/${leadId}`, { method: 'DELETE' });
        showToast("Lead deleted successfully!");
        refreshLeadsList();
    } catch (err) {
        showToast(err.message, true);
    }
}

function openAssignModal(leadId, title) {
    document.getElementById('assign-lead-id').value = leadId;
    document.getElementById('assign-lead-title-text').textContent = `Assign: "${title}"`;
    
    const modal = new bootstrap.Modal(document.getElementById('assignLeadModal'));
    modal.show();
}

document.getElementById('assign-lead-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const leadId = document.getElementById('assign-lead-id').value;
    const userId = document.getElementById('assign-user-select').value;
    
    try {
        await apiRequest(`/api/leads/${leadId}/assign?assignee_id=${userId}`, { method: 'POST' });
        
        const modalEl = document.getElementById('assignLeadModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        
        showToast("Lead assigned successfully!");
        refreshLeadsList();
    } catch (err) {
        showToast(err.message, true);
    }
});

// Copy text to clipboard helper in View Lead modal
function copyViewLeadText(elementId) {
    const text = document.getElementById(elementId).innerText;
    if (text === 'N/A') {
        showToast("No text to copy", true);
        return;
    }
    navigator.clipboard.writeText(text).then(() => {
        showToast("Copied to clipboard!");
    }).catch(err => {
        console.error("Failed to copy: ", err);
        showToast("Copy failed", true);
    });
}

function openViewLeadModal(leadId) {
    const lead = loadedLeads.find(l => l.id === leadId);
    if (!lead) return;

    document.getElementById('view-lead-project').innerText = lead.project_name;
    document.getElementById('view-lead-location').innerText = lead.location || 'Unknown';
    
    // Set source badge
    const srcEl = document.getElementById('view-lead-source-badge');
    srcEl.innerText = lead.source;
    
    let srcClass = 'bg-secondary';
    if (lead.source === 'LinkedIn') srcClass = 'source-linkedin';
    else if (lead.source === 'Instagram') srcClass = 'source-instagram';
    else if (lead.source === 'X (Twitter)') srcClass = 'source-twitter';
    else if (lead.source === 'Google Maps') srcClass = 'source-google-maps';
    else if (lead.source === 'Upwork') srcClass = 'source-upwork';
    else if (lead.source === 'Reddit') srcClass = 'source-reddit';
    else if (lead.source === 'Wellfound') srcClass = 'source-wellfound';
    else if (lead.source === 'GitHub') srcClass = 'source-github';
    srcEl.className = `badge badge-source ${srcClass}`;

    // Status badge
    const statusEl = document.getElementById('view-lead-status-badge');
    statusEl.innerText = lead.status;
    let statusClass = 'status-new-lead';
    if (lead.status === 'Contacted') statusClass = 'status-contacted';
    else if (lead.status === 'Interested') statusClass = 'status-interested';
    else if (lead.status === 'Follow Up Required') statusClass = 'status-follow-up-required';
    else if (lead.status === 'Proposal Sent') statusClass = 'status-proposal-sent';
    else if (lead.status === 'Negotiation') statusClass = 'status-negotiation';
    else if (lead.status === 'Won') statusClass = 'status-won';
    else if (lead.status === 'Lost') statusClass = 'status-lost';
    else if (lead.status === 'Closed') statusClass = 'status-closed';
    statusEl.className = `badge ${statusClass}`;

    // Priority badge
    const priorityEl = document.getElementById('view-lead-priority-badge');
    priorityEl.innerText = lead.priority;
    let pClass = 'priority-normal';
    if (lead.priority === 'Best Opportunity') pClass = 'priority-best';
    else if (lead.priority === 'Better Opportunity') pClass = 'priority-better';
    else if (lead.priority === 'Low Priority') pClass = 'priority-low';
    priorityEl.className = `badge ${pClass}`;

    // Collection DateTime
    document.getElementById('view-lead-collected').innerText = `${lead.collection_date} ${lead.collection_time.slice(0, 5)}`;

    // Description text
    document.getElementById('view-lead-description').innerText = lead.project_description || 'No description provided';

    // Contact profile
    document.getElementById('view-lead-contact').innerText = lead.contact_name || 'N/A';
    document.getElementById('view-lead-email').innerText = lead.email_address || 'N/A';
    document.getElementById('view-lead-phone').innerText = lead.phone_number || 'N/A';
    
    const webEl = document.getElementById('view-lead-website');
    if (lead.website) {
        webEl.innerText = lead.website.replace('https://', '').replace('http://', '');
        webEl.href = lead.website;
        webEl.classList.remove('d-none');
    } else {
        webEl.innerText = 'N/A';
        webEl.href = '#';
    }

    // Vetting report details
    const score = lead.trust_score || 85;
    document.getElementById('view-lead-trust-score-pct').innerText = `${score}%`;
    const progressEl = document.getElementById('view-lead-trust-progress');
    progressEl.style.width = `${score}%`;
    progressEl.setAttribute('aria-valuenow', score);
    
    if (score >= 90) {
        progressEl.className = 'progress-bar bg-success';
    } else if (score >= 80) {
        progressEl.className = 'progress-bar bg-info';
    } else {
        progressEl.className = 'progress-bar bg-warning';
    }

    // Authenticity Level & Icon
    const tierText = lead.authenticity_level || (score >= 95 ? "Tier 1: Gold Super Lead (Highest Vetting)" : (score >= 85 ? "Tier 2: Silver Vetted Lead (Confirmed Real)" : "Tier 3: Bronze Warm Lead (Potential Match)"));
    document.getElementById('view-lead-tier').innerText = tierText;
    
    const tierIcon = document.getElementById('view-lead-tier-icon');
    if (score >= 95) {
        tierIcon.className = 'bi bi-shield-fill-check text-warning fs-4';
    } else if (score >= 85) {
        tierIcon.className = 'bi bi-patch-check-fill text-success fs-4';
    } else {
        tierIcon.className = 'bi bi-check-circle-fill text-info fs-4';
    }

    // Set other vetting items
    document.getElementById('view-lead-source-detail').innerText = lead.lead_source_detail || `Vetted crawl on ${lead.source} matching active keywords.`;
    document.getElementById('view-lead-trust-source').innerText = lead.trust_source || `Trust factors matching verification criteria for platform.`;
    document.getElementById('view-lead-trust-factors').innerText = lead.trust_factors || 'Manual assessment verification check: OK';

    // Internal Notes
    document.getElementById('view-lead-notes').innerText = lead.notes || 'No internal notes added yet.';

    // Direct link to post
    const linkEl = document.getElementById('view-lead-direct-link');
    if (lead.source_link) {
        linkEl.href = lead.source_link;
        linkEl.style.display = 'inline-block';
    } else {
        linkEl.style.display = 'none';
    }

    // Bind edit button
    const editBtn = document.getElementById('view-lead-edit-btn');
    editBtn.onclick = function() {
        const viewModalEl = document.getElementById('viewLeadModal');
        const viewModal = bootstrap.Modal.getInstance(viewModalEl);
        if (viewModal) viewModal.hide();
        openEditLeadModal(lead.id);
    };

    const modal = new bootstrap.Modal(document.getElementById('viewLeadModal'));
    modal.show();
}

function openEditLeadModal(leadId) {
    const lead = loadedLeads.find(l => l.id === leadId);
    if (!lead) return;
    
    document.getElementById('edit-lead-id').value = lead.id;
    document.getElementById('edit-lead-project').value = lead.project_name;
    document.getElementById('edit-lead-source').value = lead.source;
    document.getElementById('edit-lead-location').value = lead.location || '';
    document.getElementById('edit-lead-description').value = lead.project_description || '';
    document.getElementById('edit-lead-contact').value = lead.contact_name || '';
    document.getElementById('edit-lead-phone').value = lead.phone_number || '';
    document.getElementById('edit-lead-email').value = lead.email_address || '';
    document.getElementById('edit-lead-website').value = lead.website || '';
    document.getElementById('edit-lead-source-link').value = lead.source_link || '';
    document.getElementById('edit-lead-status').value = lead.status;
    document.getElementById('edit-lead-priority').value = lead.priority;
    document.getElementById('edit-lead-notes').value = lead.notes || '';
    document.getElementById('edit-lead-trust-factors').value = lead.trust_factors || '';
    document.getElementById('edit-lead-authenticity-level').value = lead.authenticity_level || 'Tier 2: Silver Vetted Lead (Confirmed Real)';
    document.getElementById('edit-lead-source-detail').value = lead.lead_source_detail || '';
    document.getElementById('edit-lead-trust-source').value = lead.trust_source || '';
    
    const modal = new bootstrap.Modal(document.getElementById('editLeadModal'));
    modal.show();
}

document.getElementById('edit-lead-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const leadId = document.getElementById('edit-lead-id').value;
    
    const leadData = {
        project_name: document.getElementById('edit-lead-project').value.trim(),
        location: document.getElementById('edit-lead-location').value.trim() || null,
        project_description: document.getElementById('edit-lead-description').value.trim() || null,
        contact_name: document.getElementById('edit-lead-contact').value.trim(),
        phone_number: document.getElementById('edit-lead-phone').value.trim(),
        email_address: document.getElementById('edit-lead-email').value.trim(),
        website: document.getElementById('edit-lead-website').value.trim() || null,
        source_link: document.getElementById('edit-lead-source-link').value.trim(),
        status: document.getElementById('edit-lead-status').value,
        priority: document.getElementById('edit-lead-priority').value,
        notes: document.getElementById('edit-lead-notes').value.trim(),
        trust_score: parseInt(document.getElementById('edit-lead-trust-score').value) || 85,
        trust_factors: document.getElementById('edit-lead-trust-factors').value.trim() || null,
        authenticity_level: document.getElementById('edit-lead-authenticity-level').value,
        lead_source_detail: document.getElementById('edit-lead-source-detail').value.trim() || null,
        trust_source: document.getElementById('edit-lead-trust-source').value.trim() || null
    };
    
    try {
        await apiRequest(`/api/leads/${leadId}`, {
            method: 'PUT',
            body: leadData
        });
        
        const modalEl = document.getElementById('editLeadModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        
        showToast("Lead opportunity details updated!");
        refreshLeadsList();
    } catch (err) {
        showToast(err.message, true);
    }
});

document.getElementById('create-lead-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const todayStr = new Date().toISOString().slice(0, 10);
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    
    const leadData = {
        project_name: document.getElementById('create-lead-project').value.trim(),
        source: document.getElementById('create-lead-source').value,
        location: document.getElementById('create-lead-location').value.trim() || null,
        project_description: document.getElementById('create-lead-description').value.trim() || null,
        contact_name: document.getElementById('create-lead-contact').value.trim(),
        phone_number: document.getElementById('create-lead-phone').value.trim(),
        email_address: document.getElementById('create-lead-email').value.trim(),
        website: document.getElementById('create-lead-website').value.trim() || null,
        source_link: document.getElementById('create-lead-source-link').value.trim(),
        status: document.getElementById('create-lead-status').value,
        priority: document.getElementById('create-lead-priority').value,
        trust_score: parseInt(document.getElementById('create-lead-trust-score').value) || 85,
        trust_factors: document.getElementById('create-lead-trust-factors').value.trim() || null,
        authenticity_level: document.getElementById('create-lead-authenticity-level').value,
        lead_source_detail: document.getElementById('create-lead-source-detail').value.trim() || null,
        trust_source: document.getElementById('create-lead-trust-source').value.trim() || null,
        collection_date: todayStr,
        collection_time: timeStr
    };
    
    try {
        await apiRequest('/api/leads', {
            method: 'POST',
            body: leadData
        });
        
        const modalEl = document.getElementById('createLeadModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        
        document.getElementById('create-lead-form').reset();
        
        showToast("Manual lead opportunity created!");
        refreshLeadsList();
    } catch (err) {
        showToast(err.message, true);
    }
});

/* ==========================================================================
   PROJECT SCANNER ENGINE VIEW
   ========================================================================== */

async function loadScannerConfig() {
    try {
        const config = await apiRequest('/api/scanner/config');
        document.getElementById('scanner-keywords').value = config.keywords;
        
        const sourcesList = config.sources.split(',').map(s => s.trim());
        document.getElementById('src-linkedin').checked = sourcesList.includes('LinkedIn');
        document.getElementById('src-instagram').checked = sourcesList.includes('Instagram');
        document.getElementById('src-twitter').checked = sourcesList.includes('X (Twitter)');
        document.getElementById('src-gmaps').checked = sourcesList.includes('Google Maps');
        document.getElementById('src-upwork').checked = sourcesList.includes('Upwork');
        document.getElementById('src-reddit').checked = sourcesList.includes('Reddit');
        document.getElementById('src-wellfound').checked = sourcesList.includes('Wellfound');
        document.getElementById('src-github').checked = sourcesList.includes('GitHub');
        
    } catch (err) {
        showToast("Failed to fetch scanner settings config.", true);
    }
}

document.getElementById('scanner-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const keywordsInput = document.getElementById('scanner-keywords').value.trim();
    
    const sources = [];
    if (document.getElementById('src-linkedin').checked) sources.push('LinkedIn');
    if (document.getElementById('src-instagram').checked) sources.push('Instagram');
    if (document.getElementById('src-twitter').checked) sources.push('X (Twitter)');
    if (document.getElementById('src-gmaps').checked) sources.push('Google Maps');
    if (document.getElementById('src-upwork').checked) sources.push('Upwork');
    if (document.getElementById('src-reddit').checked) sources.push('Reddit');
    if (document.getElementById('src-wellfound').checked) sources.push('Wellfound');
    if (document.getElementById('src-github').checked) sources.push('GitHub');
    
    if (sources.length === 0) {
        showToast("Please select at least one target scanning source.", true);
        return;
    }
    
    const keywords = keywordsInput.split(',').map(k => k.trim()).filter(k => k.length > 0);
    const dateFilter = document.getElementById('scanner-date-filter').value;
    const timeFilter = document.getElementById('scanner-time-filter').value;
    const location = document.getElementById('scanner-location').value.trim() || 'any';
    const country = document.getElementById('scanner-country').value;
    const searchEngine = document.getElementById('scanner-search-engine').value;
    const targetCount = parseInt(document.getElementById('scanner-target-count').value) || 5;
    
    const terminal = document.getElementById('terminal-screen');
    terminal.innerHTML = '<div class="text-muted mb-2">[INFO] Handshaking secure platform protocol...</div>';
    
    const startBtn = document.getElementById('start-scan-btn');
    const badge = document.getElementById('console-status-badge');
    const summaryCard = document.getElementById('scan-results-summary');
    
    startBtn.disabled = true;
    badge.textContent = "SCANNING...";
    badge.classList.remove('bg-success-glow-pill');
    badge.classList.add('bg-danger');
    summaryCard.classList.add('d-none');
    
    try {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (state.token) {
            headers['Authorization'] = `Bearer ${state.token}`;
        }
        
        const response = await fetch(`${API_BASE}/api/scanner/scan`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                keywords: keywords,
                sources: sources,
                date_filter: dateFilter,
                time_filter: timeFilter,
                location: location,
                search_engine: searchEngine,
                target_count: targetCount,
                country: country,
                stream: true
            })
        });
        
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            const errMsg = errData.detail || `Error: ${response.statusText}`;
            throw new Error(errMsg);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let resultData = null;
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();
            
            for (const line of lines) {
                if (line.trim()) {
                    const parsed = JSON.parse(line);
                    if (parsed.log) {
                        const lineText = parsed.log;
                        let lineClass = 'console-info';
                        
                        if (lineText.includes('[SCAN]')) lineClass = 'console-scan';
                        else if (lineText.includes('[COMPLIANCE]')) lineClass = 'console-compliance';
                        else if (lineText.includes('[FOUND]')) lineClass = 'console-found';
                        else if (lineText.includes('[EXTRACT]')) lineClass = 'console-extract';
                        else if (lineText.includes('[SKIP]')) lineClass = 'console-skip';
                        else if (lineText.includes('[ERROR]')) lineClass = 'console-error';
                        
                        terminal.innerHTML += `<div class="console-log-line ${lineClass}">${lineText}</div>`;
                        terminal.scrollTop = terminal.scrollHeight;
                    } else {
                        resultData = parsed;
                    }
                }
            }
        }
        
        startBtn.disabled = false;
        badge.textContent = "CONSOLE IDLE";
        badge.classList.remove('bg-danger');
        badge.classList.add('bg-success-glow-pill');
        
        if (resultData && resultData.success) {
            summaryCard.classList.remove('d-none');
            document.getElementById('scan-summary-text').textContent = `Collected ${resultData.leads_collected} new business opportunities matching criteria.`;
            showToast(`Scan complete! Collected ${resultData.leads_collected} leads.`);
        } else {
            const errMsg = (resultData && resultData.error) ? resultData.error : "Unknown scan error occurred.";
            terminal.innerHTML += `<div class="console-log-line console-error">[ERROR] Scan failed: ${errMsg}</div>`;
            showToast(errMsg, true);
        }
        
    } catch (err) {
        startBtn.disabled = false;
        badge.textContent = "ERROR";
        terminal.innerHTML += `<div class="console-log-line console-error">[ERROR] Scan aborted: ${err.message}</div>`;
        showToast(err.message, true);
    }
});

function animateTerminalLogs(logs, callback) {
    const terminal = document.getElementById('terminal-screen');
    let lineIdx = 0;
    
    function printNextLine() {
        if (lineIdx < logs.length) {
            const line = logs[lineIdx];
            let lineClass = 'console-info';
            
            if (line.includes('[SCAN]')) lineClass = 'console-scan';
            else if (line.includes('[COMPLIANCE]')) lineClass = 'console-compliance';
            else if (line.includes('[FOUND]')) lineClass = 'console-found';
            else if (line.includes('[EXTRACT]')) lineClass = 'console-extract';
            else if (line.includes('[SKIP]')) lineClass = 'console-skip';
            else if (line.includes('[ERROR]')) lineClass = 'console-error';
            
            terminal.innerHTML += `<div class="console-log-line ${lineClass}">${line}</div>`;
            terminal.scrollTop = terminal.scrollHeight;
            
            lineIdx++;
            setTimeout(printNextLine, 120);
        } else {
            terminal.innerHTML += `<div class="text-success blink-cursor">> Scan completed. Terminal idle.</div>`;
            terminal.scrollTop = terminal.scrollHeight;
            if (callback) callback();
        }
    }
    
    printNextLine();
}

document.getElementById('scan-view-leads-btn').addEventListener('click', () => {
    document.querySelectorAll('#sidebar .nav-link').forEach(l => {
        l.classList.remove('active');
        if (l.getAttribute('data-view') === 'leads') {
            l.classList.add('active');
        }
    });
    switchView('leads');
});

/* ==========================================================================
   FOLLOW-UPS & REMINDERS VIEW
   ========================================================================== */

let remindersFilterCompleted = false;

document.getElementById('reminders-filter-active').addEventListener('click', () => {
    remindersFilterCompleted = false;
    document.getElementById('reminders-filter-active').classList.add('active');
    document.getElementById('reminders-filter-completed').classList.remove('active');
    refreshReminders();
});

document.getElementById('reminders-filter-completed').addEventListener('click', () => {
    remindersFilterCompleted = true;
    document.getElementById('reminders-filter-completed').classList.add('active');
    document.getElementById('reminders-filter-active').classList.remove('active');
    refreshReminders();
});

async function refreshReminders() {
    try {
        const queryStr = `?is_completed=${remindersFilterCompleted}`;
        const reminders = await apiRequest(`/api/reminders${queryStr}`);
        
        if (!remindersFilterCompleted) {
            const badge = document.getElementById('reminders-count-badge');
            badge.textContent = reminders.length;
            if (reminders.length > 0) {
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }
        
        renderRemindersList(reminders);
    } catch (err) {
        showToast("Error updating reminders board.", true);
    }
}

function renderRemindersList(reminders) {
    const tbody = document.getElementById('reminders-list-tbody');
    tbody.innerHTML = '';
    
    if (reminders.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No follow-ups scheduled in this category.</td></tr>`;
        return;
    }
    
    reminders.forEach(r => {
        const checkboxHtml = r.is_completed 
            ? `<i class="bi bi-check-circle-fill text-success fs-5"></i>`
            : `<input class="form-check-input ms-0 border-secondary-subtle" type="checkbox" style="cursor:pointer;" onchange="toggleReminderState(${r.id}, true)" title="Complete Task">`;
            
        const rowClass = r.is_completed ? 'text-muted' : '';
        const dateStr = `${r.date} ${r.time.slice(0,5)}`;
        
        tbody.innerHTML += `
            <tr class="${rowClass}">
                <td>${checkboxHtml}</td>
                <td>
                    <div class="fw-bold ${r.is_completed ? 'text-decoration-line-through text-muted' : 'text-dark'}">${r.lead ? r.lead.project_name : 'Deleted Lead'}</div>
                    <span class="badge bg-light text-muted border small mt-1">ID: ${r.lead_id}</span>
                </td>
                <td>
                    <span class="small ${r.is_completed ? '' : 'text-warning fw-semibold'}"><i class="bi bi-calendar-event me-1"></i>${dateStr}</span>
                </td>
                <td style="max-width: 250px;">
                    <div class="small text-dark">${r.note}</div>
                </td>
                <td>
                    <span class="badge bg-light text-dark border small">${r.assigned_user ? r.assigned_user.full_name : 'System'}</span>
                </td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger px-2 py-1" onclick="deleteReminderItem(${r.id})" title="Delete"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `;
    });
}

function populateLeadsSelect(leads) {
    const select = document.getElementById('reminder-lead-id');
    select.innerHTML = '<option value="">Choose Opportunity...</option>';
    
    leads.forEach(lead => {
        select.innerHTML += `<option value="${lead.id}">${lead.project_name} [${lead.source}]</option>`;
    });
}

document.getElementById('reminder-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const leadId = document.getElementById('reminder-lead-id').value;
    const dateVal = document.getElementById('reminder-date').value;
    const timeVal = document.getElementById('reminder-time').value;
    const noteVal = document.getElementById('reminder-note').value.trim();
    
    try {
        await apiRequest('/api/reminders', {
            method: 'POST',
            body: {
                lead_id: parseInt(leadId),
                date: dateVal,
                time: timeVal,
                note: noteVal,
                assigned_user_id: state.user.id
            }
        });
        
        document.getElementById('reminder-form').reset();
        showToast("Follow-up reminder scheduled!");
        refreshReminders();
        
    } catch (err) {
        showToast(err.message, true);
    }
});

async function toggleReminderState(reminderId, isCompleted) {
    try {
        await apiRequest(`/api/reminders/${reminderId}`, {
            method: 'PUT',
            body: { is_completed: isCompleted }
        });
        showToast("Reminder status updated!");
        refreshReminders();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deleteReminderItem(reminderId) {
    if (!confirm("Are you sure you want to delete this reminder?")) return;
    try {
        await apiRequest(`/api/reminders/${reminderId}`, { method: 'DELETE' });
        showToast("Reminder deleted!");
        refreshReminders();
    } catch (err) {
        showToast(err.message, true);
    }
}

/* ==========================================================================
   ADMIN PANEL: USER MANAGEMENT
   ========================================================================== */

let loadedUsers = [];
let editingUserId = null;

async function fetchSystemUsers() {
    try {
        const users = await apiRequest('/api/users');
        loadedUsers = users;
        
        const select = document.getElementById('assign-user-select');
        select.innerHTML = '<option value="">Select sales operator...</option>';
        users.forEach(u => {
            select.innerHTML += `<option value="${u.id}">${u.full_name} (${u.role.replace('_', ' ')})</option>`;
        });
        
    } catch (err) {
        console.error("Failed to load assignee directory:", err);
    }
}

async function refreshAdminPanel() {
    try {
        const users = await apiRequest('/api/users');
        loadedUsers = users;
        renderUsersList(users);
        
        const metrics = await apiRequest('/api/reports/dashboard');
        renderAuditLogs(metrics.recent_activities);
    } catch (err) {
        showToast("Access Denied: Admins/Managers only.", true);
    }
}

function renderUsersList(users) {
    const tbody = document.getElementById('admin-users-tbody');
    tbody.innerHTML = '';
    
    users.forEach(u => {
        const isSelf = state.user && state.user.id === u.id;
        const selfTag = isSelf ? ' <span class="badge bg-primary-subtle text-primary small ms-1">You</span>' : '';
        
        let roleBadgeClass = 'bg-secondary-subtle text-dark';
        if (u.role === 'admin') roleBadgeClass = 'bg-danger-subtle text-danger';
        else if (u.role === 'sales_manager') roleBadgeClass = 'bg-info-subtle text-info';
        
        const deleteBtnHtml = isSelf 
            ? `<button class="btn btn-sm btn-outline-secondary px-2 py-1" disabled><i class="bi bi-trash"></i></button>`
            : `<button class="btn btn-sm btn-outline-danger px-2 py-1" onclick="deleteUserAccount(${u.id})"><i class="bi bi-trash"></i></button>`;
            
        tbody.innerHTML += `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="avatar me-3">
                            <div class="avatar-letter bg-light text-dark rounded-circle d-flex align-items-center justify-content-center fw-bold small" style="width:34px; height:34px; border:1px solid var(--border-darker);">${u.full_name.charAt(0).toUpperCase()}</div>
                        </div>
                        <div>
                            <div class="fw-bold text-dark">${u.full_name}${selfTag}</div>
                            <small class="text-muted">Registered: ${u.created_at.slice(0, 10)}</small>
                        </div>
                    </div>
                </td>
                <td><code>${u.username}</code></td>
                <td>${u.email}</td>
                <td><span class="badge ${roleBadgeClass} text-uppercase small">${u.role.replace('_', ' ')}</span></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary px-2 py-1 me-1" onclick="startEditUser(${u.id})"><i class="bi bi-pencil"></i></button>
                    ${deleteBtnHtml}
                </td>
            </tr>
        `;
    });
}

document.getElementById('admin-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('admin-username').value.trim();
    const fullname = document.getElementById('admin-fullname').value.trim();
    const email = document.getElementById('admin-email').value.trim();
    const role = document.getElementById('admin-role').value;
    const password = document.getElementById('admin-password').value;
    
    try {
        if (editingUserId) {
            const body = { full_name: fullname, email: email, role: role };
            if (password) body.password = password;
            
            await apiRequest(`/api/users/${editingUserId}`, {
                method: 'PUT',
                body: body
            });
            showToast("User account profile updated!");
        } else {
            if (!password) {
                showToast("Password is required for new accounts.", true);
                return;
            }
            await apiRequest('/api/users', {
                method: 'POST',
                body: {
                    username: username,
                    password: password,
                    email: email,
                    full_name: fullname,
                    role: role
                }
            });
            showToast("New user registered successfully!");
        }
        
        cancelEditUser();
        refreshAdminPanel();
        fetchSystemUsers(); // Sync assignments
    } catch (err) {
        showToast(err.message, true);
    }
});

function startEditUser(userId) {
    const user = loadedUsers.find(u => u.id === userId);
    if (!user) return;
    
    editingUserId = userId;
    document.getElementById('admin-user-id').value = user.id;
    document.getElementById('admin-username').value = user.username;
    document.getElementById('admin-username').disabled = true;
    document.getElementById('admin-fullname').value = user.full_name;
    document.getElementById('admin-email').value = user.email;
    document.getElementById('admin-role').value = user.role;
    
    document.getElementById('admin-password-help').textContent = "Leave blank to keep existing password";
    document.getElementById('admin-user-form-title').innerHTML = `<i class="bi bi-pencil-square me-2 text-primary"></i>Modify User Profile`;
    document.getElementById('admin-user-submit-btn').textContent = "Save Profile Changes";
    document.getElementById('admin-user-cancel-btn').classList.remove('d-none');
}

function cancelEditUser() {
    editingUserId = null;
    document.getElementById('admin-user-id').value = '';
    document.getElementById('admin-username').value = '';
    document.getElementById('admin-username').disabled = false;
    document.getElementById('admin-fullname').value = '';
    document.getElementById('admin-email').value = '';
    document.getElementById('admin-role').value = 'sales_executive';
    document.getElementById('admin-password').value = '';
    
    document.getElementById('admin-password-help').textContent = "Password is required for new accounts";
    document.getElementById('admin-user-form-title').innerHTML = `<i class="bi bi-person-plus-fill me-2 text-primary"></i>Register User Account`;
    document.getElementById('admin-user-submit-btn').textContent = "Register User";
    document.getElementById('admin-user-cancel-btn').classList.add('d-none');
}

document.getElementById('admin-user-cancel-btn').addEventListener('click', cancelEditUser);

async function deleteUserAccount(userId) {
    if (!confirm("Are you sure you want to delete this user account?")) return;
    try {
        await apiRequest(`/api/users/${userId}`, { method: 'DELETE' });
        showToast("User account deleted!");
        refreshAdminPanel();
        fetchSystemUsers(); // Sync assignments
    } catch (err) {
        showToast(err.message, true);
    }
}

/* ==========================================================================
   INITIALIZATION PIPELINE
   ========================================================================== */

async function initApp() {
    document.getElementById('login-container').classList.add('d-none');
    document.getElementById('app-container').classList.remove('d-none');
    
    switchView('dashboard');
}

window.addEventListener('DOMContentLoaded', async () => {
    if (state.token) {
        try {
            await fetchUserProfile();
            initApp();
        } catch (err) {
            handleLogout();
        }
    } else {
        handleLogout();
    }
});

// Setup Hover Preview Card for Leads Vetting Audit
function setupLeadHoverCards() {
    const triggers = document.querySelectorAll('.lead-hover-trigger');
    const card = document.getElementById('lead-hover-card');
    if (!card) return;
    
    triggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            card.classList.remove('show');
            card.classList.add('d-none');
        });
        
        trigger.addEventListener('mouseenter', (e) => {
            const leadId = parseInt(trigger.getAttribute('data-lead-id'));
            const lead = loadedLeads.find(l => l.id === leadId);
            if (!lead) return;
            
            // Format Description (exclude Markdown headers for clean hover reading)
            let descSnippet = lead.project_description || '';
            if (descSnippet.includes('### Opportunity Overview')) {
                descSnippet = descSnippet.split('### Opportunity Overview')[1].split('###')[0].trim();
            }
            descSnippet = descSnippet.replace(/#+/g, '').trim();
            if (descSnippet.length > 220) descSnippet = descSnippet.substring(0, 220) + '...';
            
            // Determine tier classes
            const score = lead.trust_score || 85;
            let tierClass = 'tier-silver';
            let tierName = lead.authenticity_level || 'Tier 2: Silver Vetted Lead';
            if (score >= 95) {
                tierClass = 'tier-gold';
            } else if (score < 85) {
                tierClass = 'tier-bronze';
            }
            
            let progressBarClass = 'bg-info';
            if (score >= 90) progressBarClass = 'bg-success';
            else if (score < 80) progressBarClass = 'bg-warning';

            let srcClass = 'bg-secondary';
            if (lead.source === 'LinkedIn') srcClass = 'source-linkedin';
            else if (lead.source === 'Instagram') srcClass = 'source-instagram';
            else if (lead.source === 'X (Twitter)') srcClass = 'source-twitter';
            else if (lead.source === 'Google Maps') srcClass = 'source-google-maps';
            else if (lead.source === 'Upwork') srcClass = 'source-upwork';
            else if (lead.source === 'Reddit') srcClass = 'source-reddit';
            else if (lead.source === 'Wellfound') srcClass = 'source-wellfound';
            else if (lead.source === 'GitHub') srcClass = 'source-github';

            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
                    <span class="badge ${srcClass} badge-source" style="font-size: 0.65rem;">${lead.source}</span>
                    <span class="badge ${tierClass}" style="font-size: 0.65rem;">${tierName.split('(')[0].trim()}</span>
                </div>
                <h6 class="fw-bold text-dark mb-1" style="font-size: 0.95rem;">${lead.project_name}</h6>
                <div class="mb-2">
                    <div class="d-flex justify-content-between align-items-center mb-1" style="font-size: 0.7rem;">
                        <span class="text-muted font-monospace">Trust Match Score</span>
                        <span class="fw-bold text-dark font-monospace">${score}%</span>
                    </div>
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar ${progressBarClass}" style="width: ${score}%;"></div>
                    </div>
                </div>
                <p class="text-muted mb-2 font-sans-serif" style="font-size: 0.78rem; line-height: 1.45;">
                    ${descSnippet}
                </p>
                <div class="bg-light p-2 rounded border small text-secondary font-monospace" style="font-size: 0.7rem; line-height: 1.4;">
                    <div><i class="bi bi-search me-1 text-primary"></i><strong>Source:</strong> ${lead.lead_source_detail || 'N/A'}</div>
                    <div class="mt-1"><i class="bi bi-shield-check me-1 text-success"></i><strong>Trust:</strong> ${lead.trust_source || 'N/A'}</div>
                </div>
                <div class="mt-2 text-end">
                    <small class="text-primary font-semibold" style="font-size: 0.68rem;"><i class="bi bi-info-circle me-1"></i>Click eye icon for full vetting report</small>
                </div>
            `;
            
            card.classList.remove('d-none');
            // Force layout update
            card.offsetHeight;
            card.classList.add('show');
            
            positionCard(e);
        });
        
        trigger.addEventListener('mousemove', (e) => {
            positionCard(e);
        });
        
        trigger.addEventListener('mouseleave', () => {
            card.classList.remove('show');
            // Hide element from layout after fade out
            setTimeout(() => {
                if (!card.classList.contains('show')) {
                    card.classList.add('d-none');
                }
            }, 150);
        });
    });
    
    function positionCard(e) {
        const cardWidth = 380;
        const cardHeight = card.offsetHeight || 250;
        
        let left = e.pageX + 15;
        let top = e.pageY + 15;
        
        // Window boundaries checks to prevent overflow
        if (left + cardWidth > window.innerWidth + window.pageXOffset) {
            left = e.pageX - cardWidth - 15;
        }
        if (top + cardHeight > window.innerHeight + window.pageYOffset) {
            top = e.pageY - cardHeight - 15;
        }
        
        card.style.left = `${left}px`;
        card.style.top = `${top}px`;
    }
}