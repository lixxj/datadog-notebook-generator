// Global variables
let currentNotebookData = null;
let currentRequestData = null;

// DOM elements
const notebookForm = document.getElementById('notebookForm');
const generateBtn = document.getElementById('generateBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const statusIndicator = document.getElementById('statusIndicator');

// Side navigation elements
const sideNav = document.getElementById('sideNav');
const sideNavToggle = document.getElementById('sideNavToggle');

// Tab elements
const previewTab = document.getElementById('previewTab');
const jsonTab = document.getElementById('jsonTab');
const detailsTab = document.getElementById('detailsTab');

// Content elements
const previewContent = document.getElementById('previewContent');
const jsonContent = document.getElementById('jsonContent');
const detailsContent = document.getElementById('detailsContent');

// Message elements
const successMessage = document.getElementById('successMessage');
const errorMessage = document.getElementById('errorMessage');
const successDetails = document.getElementById('successDetails');
const errorDetails = document.getElementById('errorDetails');

// Side Navigation Functions
function initializeSideNavigation() {
    // Set up toggle functionality
    if (sideNavToggle) {
        sideNavToggle.addEventListener('click', toggleSideNavigation);
    }
    
    // Add tooltips for collapsed state
    addNavigationTooltips();
    
    // Handle mobile responsiveness
    handleMobileNavigation();
    
    // Set up keyboard shortcuts for navigation
    setupNavigationKeyboardShortcuts();
}

function toggleSideNavigation() {
    if (sideNav) {
        sideNav.classList.toggle('collapsed');
        
        // Save preference to localStorage
        const isCollapsed = sideNav.classList.contains('collapsed');
        localStorage.setItem('sideNavCollapsed', isCollapsed);
    }
}

function addNavigationTooltips() {
    const navItems = document.querySelectorAll('.side-nav-item');
    navItems.forEach(item => {
        const textElement = item.querySelector('.side-nav-text');
        if (textElement) {
            item.setAttribute('data-tooltip', textElement.textContent);
        }
    });
}

function handleMobileNavigation() {
    // Check if mobile
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        // Add mobile menu button to header if not exists
        addMobileMenuButton();
    }
    
    // Handle window resize
    window.addEventListener('resize', () => {
        const newIsMobile = window.innerWidth <= 768;
        if (newIsMobile !== isMobile) {
            if (newIsMobile) {
                addMobileMenuButton();
            } else {
                removeMobileMenuButton();
                sideNav.classList.remove('mobile-open');
            }
        }
    });
}

function addMobileMenuButton() {
    const header = document.querySelector('.header-content');
    if (header && !header.querySelector('.mobile-menu-btn')) {
        const menuBtn = document.createElement('button');
        menuBtn.className = 'mobile-menu-btn';
        menuBtn.innerHTML = '☰';
        menuBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.5rem;
            margin-right: 1rem;
        `;
        
        menuBtn.addEventListener('click', () => {
            sideNav.classList.toggle('mobile-open');
        });
        
        header.insertBefore(menuBtn, header.firstChild);
    }
}

function removeMobileMenuButton() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    if (menuBtn) {
        menuBtn.remove();
    }
}

function setupNavigationKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Ctrl/Cmd + B to toggle sidebar
        if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
            event.preventDefault();
            toggleSideNavigation();
        }
        
        // Escape to close mobile menu
        if (event.key === 'Escape' && sideNav.classList.contains('mobile-open')) {
            sideNav.classList.remove('mobile-open');
        }
    });
}

function restoreSideNavigationState() {
    // Restore collapsed state from localStorage
    const isCollapsed = localStorage.getItem('sideNavCollapsed') === 'true';
    if (isCollapsed && sideNav) {
        sideNav.classList.add('collapsed');
    }
}

// Example data
const examples = {
    performance: {
        description: "Create a comprehensive performance monitoring notebook showing CPU usage, memory consumption, disk I/O, and network metrics for our web application servers. Include response time analysis, error rate tracking, and resource utilization trends over the past 24 hours. Focus on identifying bottlenecks and performance degradation patterns.",
        metricNames: "system.cpu.user, system.mem.used, system.disk.used, system.net.bytes_rcvd",
        timeframes: "1d",
        spaceAggregation: "avg",
        rollup: "5m"
    },
    troubleshooting: {
        description: "Build a troubleshooting guide notebook for diagnosing application issues including error analysis, log correlation, database performance metrics, and infrastructure health checks. Include automated alerts setup and incident response workflows with step-by-step diagnostic procedures.",
        metricNames: "system.cpu.system, system.mem.free, system.load.1",
        timeframes: "4h",
        spaceAggregation: "max",
        rollup: "1m"
    },
    capacity: {
        description: "Design a capacity planning notebook analyzing resource trends, growth patterns, and forecasting future infrastructure needs. Include CPU, memory, storage, and network utilization analysis with predictive modeling for scaling decisions and budget planning.",
        metricNames: "system.cpu.idle, system.mem.total, system.disk.free",
        timeframes: "1m",
        spaceAggregation: "avg",
        rollup: "1h"
    }
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initializeSideNavigation();
    setupEventListeners();
    checkSystemStatus();
    loadMetricsInfo();
    restoreSideNavigationState();
});

function initializeApp() {
    console.log('🚀 Datadog Notebook Generator initialized');
    
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
    
    // Focus on description field
    const descriptionField = document.getElementById('description');
    if (descriptionField) {
        descriptionField.focus();
    }
}

function setupEventListeners() {
    // Form submission
    if (notebookForm) {
        notebookForm.addEventListener('submit', handleFormSubmission);
    }
    
    // Mode selection change
    const modeRadios = document.querySelectorAll('input[name="generationMode"]');
    modeRadios.forEach(radio => {
        radio.addEventListener('change', handleModeChange);
    });
    
    // Example cards - Updated to work with new examples
    const exampleCards = document.querySelectorAll('.example-card');
    exampleCards.forEach(card => {
        card.addEventListener('click', function() {
            // Get the example type from the onclick attribute or data attribute
            const onclickAttr = this.getAttribute('onclick');
            if (onclickAttr) {
                const match = onclickAttr.match(/'(.+)'/);
                if (match) {
                    fillExample(match[1]);
                }
            }
        });
    });
    
    // Side navigation links
    setupSideNavigationLinks();
    
    // Auto-resize textarea
    const textarea = document.getElementById('description');
    if (textarea) {
        textarea.addEventListener('input', autoResizeTextarea);
        textarea.addEventListener('input', debounce(handleDescriptionChange, 500));
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

function setupSideNavigationLinks() {
    // Add click handlers for side navigation items
    const sideNavItems = document.querySelectorAll('.side-nav-item');
    
    sideNavItems.forEach(item => {
        const link = item.querySelector('.side-nav-link');
        const text = item.querySelector('.side-nav-text');
        
        if (link && text) {
            const linkText = text.textContent.trim();
            
            // Add click handler based on the navigation item
            link.addEventListener('click', (e) => {
                e.preventDefault();
                handleSideNavClick(linkText, item);
            });
            
            // Add cursor pointer
            link.style.cursor = 'pointer';
        }
    });
}

function handleSideNavClick(linkText, item) {
    // Remove active class from all items
    document.querySelectorAll('.side-nav-item').forEach(navItem => {
        navItem.classList.remove('active');
    });
    
    // Add active class to clicked item
    item.classList.add('active');
    
    // Handle different navigation items
    switch (linkText) {
        case 'Go to...':
            // Simulate command palette (could implement search functionality)
            alert('⌘K - Command palette functionality would go here');
            break;
            
        case 'Dashboards':
            window.open('https://app.datadoghq.com/dashboard/lists', '_blank');
            break;
            
        case 'Notebooks':
            window.open('https://app.datadoghq.com/notebook/list', '_blank');
            break;
            
        case 'Metrics':
            window.open('https://app.datadoghq.com/metric/explorer', '_blank');
            break;
            
        case 'Infrastructure':
            window.open('https://app.datadoghq.com/infrastructure', '_blank');
            break;
            
        case 'APM':
            window.open('https://app.datadoghq.com/apm/home', '_blank');
            break;
            
        case 'Logs':
            window.open('https://app.datadoghq.com/logs', '_blank');
            break;
            
        case 'Security':
            window.open('https://app.datadoghq.com/security', '_blank');
            break;
            
        case 'Synthetics':
            window.open('https://app.datadoghq.com/synthetics/list', '_blank');
            break;
            
        case 'RUM':
            window.open('https://app.datadoghq.com/rum/list', '_blank');
            break;
            
        case 'CI/CD':
            window.open('https://app.datadoghq.com/ci', '_blank');
            break;
            
        case 'System Overview':
            window.open('https://app.datadoghq.com/dashboard/lists', '_blank');
            break;
            
        case 'Performance Analysis':
            window.open('https://app.datadoghq.com/notebook/list', '_blank');
            break;
            
        case 'Host Map':
            window.open('https://app.datadoghq.com/infrastructure/map', '_blank');
            break;
            
        case 'Settings':
            window.open('https://app.datadoghq.com/organization-settings', '_blank');
            break;
            
        case 'Help':
            window.open('https://docs.datadoghq.com/', '_blank');
            break;
            
        default:
            console.log(`Navigation clicked: ${linkText}`);
    }
    
    // Close mobile menu if open
    if (window.innerWidth <= 768) {
        sideNav.classList.remove('mobile-open');
    }
}

async function checkSystemStatus() {
    try {
        const response = await fetch('/health');
        const status = await response.json();
        
        updateStatusIndicator(status);
    } catch (error) {
        console.error('Failed to check system status:', error);
        updateStatusIndicator({ status: 'error', message: 'Connection failed' });
    }
}

function updateStatusIndicator(status) {
    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = statusIndicator.querySelector('.status-text');
    
    if (status.status === 'healthy' && status.openai_configured && status.datadog_configured) {
        statusDot.className = 'status-dot connected';
        statusText.textContent = 'All systems ready';
    } else if (status.status === 'healthy') {
        statusDot.className = 'status-dot';
        let missing = [];
        if (!status.openai_configured) missing.push('OpenAI');
        if (!status.datadog_configured) missing.push('Datadog');
        statusText.textContent = `Missing: ${missing.join(', ')}`;
    } else {
        statusDot.className = 'status-dot error';
        statusText.textContent = 'System error';
    }
}

function handleModeChange() {
    const selectedMode = document.querySelector('input[name="generationMode"]:checked').value;
    const descriptionLabel = document.getElementById('descriptionLabel');
    const descriptionHint = document.getElementById('descriptionHint');
    const createInDatadogText = document.getElementById('createInDatadogText');
    const generateBtnText = document.getElementById('generateBtnText');
    
    if (selectedMode === 'dashboard') {
        descriptionLabel.textContent = 'Describe Your Dashboard';
        descriptionHint.textContent = 'Be specific about what widgets, metrics, and visualizations you need';
        createInDatadogText.textContent = 'Create dashboard directly in Datadog';
        generateBtnText.textContent = 'Generate Dashboard';
    } else {
        descriptionLabel.textContent = 'Describe Your Notebook';
        descriptionHint.textContent = 'Be specific about what metrics, timeframes, and analysis you need';
        createInDatadogText.textContent = 'Create notebook directly in Datadog';
        generateBtnText.textContent = 'Generate Notebook';
    }
}

async function handleFormSubmission(event) {
    event.preventDefault();
    
    const formData = new FormData(notebookForm);
    const selectedMode = document.querySelector('input[name="generationMode"]:checked').value;
    
    const requestData = {
        description: formData.get('description'),
        metric_names: formData.get('metricNames') || null,
        timeframes: formData.get('timeframes') || null,
        space_aggregation: formData.get('spaceAggregation') || null,
        rollup: formData.get('rollup') || null,
        create_in_datadog: formData.get('createInDatadog') === 'on'
    };

    currentRequestData = requestData;

    try {
        showLoading(true);
        hideMessages();

        const endpoint = selectedMode === 'dashboard' ? '/generate-dashboard' : '/generate';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || `HTTP error! status: ${response.status}`);
        }

        // Store the generated data
        if (selectedMode === 'dashboard') {
            currentNotebookData = result.dashboard_json;
        } else {
            currentNotebookData = result.notebook_json;
        }

        handleGenerationSuccess(result, selectedMode);

    } catch (error) {
        console.error('Generation failed:', error);
        handleGenerationError(error.message);
    } finally {
        showLoading(false);
    }
}

function handleGenerationSuccess(result, mode = 'notebook') {
    console.log(`${mode} generated successfully:`, result);
    
    // Update results header based on mode
    const resultsHeader = document.querySelector('.results-header h3');
    if (resultsHeader) {
        resultsHeader.textContent = mode === 'dashboard' ? 'Generated Dashboard' : 'Generated Notebook';
    }

    // Populate tabs with the results
    populatePreviewTab(result.preview);
    
    if (mode === 'dashboard') {
        populateJsonTab(result.dashboard_json);
    } else {
        populateJsonTab(result.notebook_json);
    }
    
    populateDetailsTab(result, mode);

    // Show results section with animation
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });

    // Show success message
    let successMsg = `${mode === 'dashboard' ? 'Dashboard' : 'Notebook'} generated successfully!`;
    if (mode === 'dashboard' && result.datadog_dashboard_id) {
        successMsg += ` Dashboard ID: ${result.datadog_dashboard_id}`;
    } else if (mode === 'notebook' && result.datadog_notebook_id) {
        successMsg += ` Notebook ID: ${result.datadog_notebook_id}`;
    }
    
    showSuccess(successMsg);
}

function handleGenerationError(message) {
    errorDetails.textContent = message;
    showError();
    
    // Hide results section
    resultsSection.style.display = 'none';
}

function populatePreviewTab(preview) {
    previewContent.textContent = preview || 'No preview available';
}

function populateJsonTab(notebookJson) {
    if (notebookJson) {
        jsonContent.textContent = JSON.stringify(notebookJson, null, 2);
    } else {
        jsonContent.textContent = 'No JSON data available';
    }
}

function populateDetailsTab(result, mode = 'notebook') {
    const details = [];
    
    if (currentRequestData) {
        details.push({ label: 'Description', value: currentRequestData.description });
        if (currentRequestData.metric_names) {
            details.push({ label: 'Specific Metrics', value: currentRequestData.metric_names });
        }
        if (currentRequestData.timeframes) {
            details.push({ label: 'Timeframe', value: currentRequestData.timeframes });
        }
        if (currentRequestData.space_aggregation) {
            details.push({ label: 'Space Aggregation', value: currentRequestData.space_aggregation });
        }
        if (currentRequestData.rollup) {
            details.push({ label: 'Rollup', value: currentRequestData.rollup });
        }
        details.push({ label: 'Create in Datadog', value: currentRequestData.create_in_datadog ? 'Yes' : 'No' });
    }
    
    if (result.notebook_json && result.notebook_json.data && result.notebook_json.data.attributes) {
        const attrs = result.notebook_json.data.attributes;
        details.push({ label: 'Notebook Name', value: attrs.name });
        details.push({ label: 'Number of Cells', value: attrs.cells ? attrs.cells.length : 0 });
        details.push({ label: 'Time Range', value: attrs.time ? attrs.time.live_span : 'Not specified' });
        details.push({ label: 'Status', value: attrs.status || 'Draft' });
    }
    
    if (result.datadog_notebook_id) {
        details.push({ label: 'Datadog ID', value: result.datadog_notebook_id });
    }
    
    details.push({ label: 'Generated At', value: new Date().toLocaleString() });
    
    // Render details
    detailsContent.innerHTML = details.map(detail => `
        <div class="detail-item">
            <span class="detail-label">${detail.label}:</span>
            <span class="detail-value">${detail.value}</span>
        </div>
    `).join('');
}

function showTab(tabName) {
    // Hide all tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab pane
    const selectedPane = document.getElementById(tabName + 'Tab');
    if (selectedPane) {
        selectedPane.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

async function fillExample(exampleType) {
    try {
        // Fetch example suggestions from the API
        const response = await fetch(`/examples/${exampleType}`);
        if (!response.ok) {
            throw new Error('Failed to fetch example suggestions');
        }
        
        const example = await response.json();
        
        // Fill form fields
        document.getElementById('description').value = example.description;
        
        // Fill advanced settings
        if (example.suggested_metrics) {
            document.getElementById('metricNames').value = example.suggested_metrics.join(', ');
        }
        if (example.timeframe) {
            document.getElementById('timeframes').value = example.timeframe;
        }
        if (example.space_aggregation) {
            document.getElementById('spaceAggregation').value = example.space_aggregation;
        }
        if (example.rollup) {
            document.getElementById('rollup').value = example.rollup;
        }
        
        // Show suggestions modal/tooltip
        showExampleSuggestions(exampleType, example);
        
        // Add visual feedback
        const descriptionField = document.getElementById('description');
        descriptionField.style.background = 'rgba(99, 44, 166, 0.05)';
        setTimeout(() => {
            descriptionField.style.background = '';
        }, 1000);
        
        // Auto-resize textarea
        autoResizeTextarea.call(descriptionField);
        
        // Focus on description field
        descriptionField.focus();
        
        // Scroll to form
        document.querySelector('.generator-section').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
        
    } catch (error) {
        console.error('Error loading example:', error);
        // Fallback to local examples if API fails
        const localExample = examples[exampleType];
        if (localExample) {
            fillLocalExample(localExample);
        }
    }
}

function fillLocalExample(example) {
    // Fill form fields with local example data (fallback)
    document.getElementById('description').value = example.description;
    
    if (example.metricNames) {
        document.getElementById('metricNames').value = example.metricNames;
    }
    if (example.timeframes) {
        document.getElementById('timeframes').value = example.timeframes;
    }
    if (example.spaceAggregation) {
        document.getElementById('spaceAggregation').value = example.spaceAggregation;
    }
    if (example.rollup) {
        document.getElementById('rollup').value = example.rollup;
    }
}

function showExampleSuggestions(exampleType, example) {
    const modal = document.createElement('div');
    modal.className = 'suggestions-modal';
    modal.innerHTML = `
        <div class="suggestions-modal-content">
            <div class="suggestions-header">
                <h3>${getExampleTitle(exampleType)} Suggestions</h3>
                <button class="suggestions-close" onclick="closeSuggestionsModal()">&times;</button>
            </div>
            <div class="suggestions-body">
                <div class="suggestions-section">
                    <h4>📊 Suggested Metrics</h4>
                    <div class="metrics-tags">
                        ${example.suggested_metrics.map(metric => `
                            <span class="metric-tag">${metric}</span>
                        `).join('')}
                    </div>
                </div>
                
                <div class="suggestions-section">
                    <h4>⚙️ Recommended Settings</h4>
                    <div class="settings-grid">
                        <div class="setting-item">
                            <span class="setting-label">Timeframe:</span>
                            <span class="setting-value">${example.timeframe}</span>
                        </div>
                        <div class="setting-item">
                            <span class="setting-label">Space Aggregation:</span>
                            <span class="setting-value">${example.space_aggregation}</span>
                        </div>
                        <div class="setting-item">
                            <span class="setting-label">Rollup:</span>
                            <span class="setting-value">${example.rollup}</span>
                        </div>
                    </div>
                </div>
                
                <div class="suggestions-section">
                    <h4>💡 Pro Tips</h4>
                    <ul class="tips-list">
                        ${example.tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            </div>
            <div class="suggestions-footer">
                <button class="btn btn-primary" onclick="closeSuggestionsModal()">Got it, thanks!</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listener to close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeSuggestionsModal();
        }
    });
}

function getExampleTitle(exampleType) {
    const titles = {
        'performance': '⚡ Performance Analysis',
        'troubleshooting': '🔧 Troubleshooting Guide',
        'capacity': '📊 Capacity Planning'
    };
    return titles[exampleType] || exampleType;
}

function closeSuggestionsModal() {
    const modal = document.querySelector('.suggestions-modal');
    if (modal) {
        modal.remove();
    }
}

function clearForm() {
    if (notebookForm) {
        notebookForm.reset();
        hideMessages();
        resultsSection.style.display = 'none';
        currentNotebookData = null;
        currentRequestData = null;
        
        // Reset textarea height
        const textarea = document.getElementById('description');
        if (textarea) {
            textarea.style.height = 'auto';
        }
        
        // Focus on description field
        const descriptionField = document.getElementById('description');
        if (descriptionField) {
            descriptionField.focus();
        }
    }
}

function autoResizeTextarea() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
}

function downloadJSON() {
    if (!currentNotebookData || !currentNotebookData.notebook_json) {
        showError('No notebook data available to download');
        return;
    }
    
    const jsonString = JSON.stringify(currentNotebookData.notebook_json, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `datadog-notebook-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Show feedback
    const btn = event.target.closest('.btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="btn-icon">✅</span>Downloaded!';
    setTimeout(() => {
        btn.innerHTML = originalText;
    }, 2000);
}

async function copyToClipboard() {
    if (!currentNotebookData || !currentNotebookData.notebook_json) {
        showError('No notebook data available to copy');
        return;
    }
    
    try {
        const jsonString = JSON.stringify(currentNotebookData.notebook_json, null, 2);
        await navigator.clipboard.writeText(jsonString);
        
        // Show feedback
        const btn = event.target.closest('.btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="btn-icon">✅</span>Copied!';
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
        
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showError('Failed to copy to clipboard');
    }
}

function showLoading(show) {
    if (show) {
        loadingOverlay.style.display = 'flex';
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="btn-icon">⏳</span>Generating...';
    } else {
        loadingOverlay.style.display = 'none';
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<span class="btn-icon">🚀</span>Generate Notebook';
    }
}

function showSuccess(message = null) {
    hideMessages();
    if (message) {
        successDetails.textContent = message;
    }
    successMessage.style.display = 'flex';
    successMessage.classList.add('fade-in');
}

function showError(message = null) {
    hideMessages();
    if (message) {
        errorDetails.textContent = message;
    }
    errorMessage.style.display = 'flex';
    errorMessage.classList.add('fade-in');
}

function hideMessages() {
    successMessage.style.display = 'none';
    errorMessage.style.display = 'none';
    successMessage.classList.remove('fade-in');
    errorMessage.classList.remove('fade-in');
}

function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + Enter to submit form
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        if (document.activeElement && document.activeElement.form === notebookForm) {
            notebookForm.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape to close loading overlay or clear form
    if (event.key === 'Escape') {
        if (loadingOverlay.style.display === 'flex') {
            // Don't close loading overlay - let the request complete
            return;
        }
        
        if (resultsSection.style.display === 'block') {
            clearForm();
        }
    }
}

// Make functions globally available
window.showTab = showTab;
window.fillExample = fillExample;
window.clearForm = clearForm;
window.downloadJSON = downloadJSON;
window.copyToClipboard = copyToClipboard;

// Periodic status check
setInterval(checkSystemStatus, 30000); // Check every 30 seconds

// Metrics functionality
async function loadMetricsInfo() {
    try {
        const response = await fetch('/metrics/info');
        const metricsInfo = await response.json();
        
        updateMetricsDisplay(metricsInfo);
    } catch (error) {
        console.error('Failed to load metrics info:', error);
        updateMetricsDisplay(null);
    }
}

function updateMetricsDisplay(metricsInfo) {
    const totalMetricsEl = document.getElementById('totalMetrics');
    const totalIntegrationsEl = document.getElementById('totalIntegrations');
    const integrationsListEl = document.getElementById('integrationsList');
    
    if (metricsInfo) {
        totalMetricsEl.textContent = metricsInfo.total_metrics.toLocaleString();
        totalIntegrationsEl.textContent = metricsInfo.integrations;
        
        const integrations = Object.keys(metricsInfo.integration_breakdown);
        integrationsListEl.textContent = integrations.map(name => 
            name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
        ).join(', ');
    } else {
        totalMetricsEl.textContent = 'Error';
        totalIntegrationsEl.textContent = 'Error';
        integrationsListEl.textContent = 'Failed to load metrics information';
    }
}

async function handleDescriptionChange() {
    const description = document.getElementById('description').value.trim();
    const suggestedMetricsEl = document.getElementById('suggestedMetrics');
    const metricsListEl = document.getElementById('metricsList');
    
    if (description.length < 10) {
        suggestedMetricsEl.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch('/metrics/suggest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ description: description })
        });
        
        const result = await response.json();
        
        if (result.suggested_metrics && result.suggested_metrics.length > 0) {
            displaySuggestedMetrics(result.suggested_metrics);
            suggestedMetricsEl.style.display = 'block';
        } else {
            suggestedMetricsEl.style.display = 'none';
        }
    } catch (error) {
        console.error('Failed to get suggested metrics:', error);
        suggestedMetricsEl.style.display = 'none';
    }
}

function displaySuggestedMetrics(metrics) {
    const metricsListEl = document.getElementById('metricsList');
    
    metricsListEl.innerHTML = metrics.map(metric => `
        <div class="metric-item">
            <div class="metric-name">${metric.name}</div>
            <div class="metric-description">${metric.description}</div>
            <div class="metric-meta">
                <span class="metric-type">Type: ${metric.type}</span>
                ${metric.unit ? `<span class="metric-unit">Unit: ${metric.unit}</span>` : ''}
                <span class="metric-integration">Source: ${metric.integration.replace('_', ' ')}</span>
            </div>
        </div>
    `).join('');
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Helper functions for footer links
function showAbout() {
    const aboutMessage = `
🚀 Datadog Notebook Generator

This application helps you create comprehensive Datadog notebooks using AI. 
Simply describe what you want to monitor, and our AI will generate a complete 
notebook with relevant metrics, visualizations, and analysis.

Features:
• 319+ real Datadog metrics from 6 integrations
• AI-powered notebook generation
• Direct Datadog integration
• Professional monitoring templates
• Real-time metric suggestions

Built with ❤️ for better monitoring and observability.
    `;
    
    alert(aboutMessage);
}

function showHelp() {
    const helpMessage = `
📚 Help & Tips

Getting Started:
1. Describe your monitoring needs in detail
2. Include specific metrics, timeframes, and use cases
3. Optionally provide your name and email
4. Choose whether to create directly in Datadog

Tips for Better Results:
• Be specific about what you want to monitor
• Mention timeframes (e.g., "last 24 hours")
• Include context about your infrastructure
• Specify if you need alerts or thresholds

Keyboard Shortcuts:
• Ctrl/Cmd + B: Toggle sidebar
• Escape: Close mobile menu

Need more help? Visit the Datadog documentation or contact support.
    `;
    
    alert(helpMessage);
}

// Add some helpful console messages
console.log('🐕 Datadog Notebook Generator');
console.log('💡 Use Ctrl/Cmd + Enter to quickly generate notebooks');
console.log('⚡ Click example cards to quickly fill the form');
console.log('🔧 Check the console for any errors or issues'); 