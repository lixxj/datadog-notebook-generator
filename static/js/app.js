// Global variables
let currentNotebookData = null;
let currentRequestData = null;

// Global variable to store integration patterns
let integrationPatterns = {};

// Load integration patterns on app initialization
async function loadIntegrationPatterns() {
    try {
        const response = await fetch('/integrations/patterns');
        const data = await response.json();
        integrationPatterns = data.patterns || {};
        console.log('Loaded integration patterns:', Object.keys(integrationPatterns));
    } catch (error) {
        console.error('Failed to load integration patterns:', error);
        // Fallback to basic patterns if loading fails
        integrationPatterns = {
            system: { prefixes: ['system.'] },
            azure_vm: { prefixes: ['azure.vm'] },
            aws: { prefixes: ['aws.'] },
            nginx: { prefixes: ['nginx.'] },
            mysql: { prefixes: ['mysql.'] },
            redis: { prefixes: ['redis.'] },
            docker: { prefixes: ['docker.'] },
            kubernetes: { prefixes: ['kubernetes.'] }
        };
    }
}

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
    
    // Load dynamic integration patterns
    loadIntegrationPatterns();
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
    alert(`📚 Datadog AI Generator Help

🔧 Quick Actions:
• Cmd/Ctrl + K: Quick search
• Cmd/Ctrl + Enter: Generate content
• Esc: Close modals

💡 Tips:
• Be specific about metrics and timeframes
• Use advanced settings for precise control
• Enable "Create in Datadog" for direct deployment
• Check system status in top-right corner

📖 For more help, visit our documentation.`);
}

// ====================================
// Enhanced Live Notebook Preview Functionality
// ====================================

let currentPreviewData = null;
let currentPreviewMode = 'preview';
let currentZoomLevel = 1.0;
let selectedCellIndex = -1;
let isPreviewDirty = false;

function showLivePreview(notebookData) {
    /**
     * Show the live preview section with notebook data
     * Enhanced to work with actual Datadog notebook structure
     */
    // Transform Datadog notebook structure to preview format
    currentPreviewData = transformNotebookData(notebookData);
    
    const previewSection = document.getElementById('livePreviewSection');
    if (previewSection) {
        previewSection.style.display = 'block';
        previewSection.classList.add('visible');
        
        // Populate preview content
        updatePreviewContent();
        updatePreviewSidebar();
        
        // Show the preview controls
        showPreviewControls();
        
        // Smooth scroll to preview
        setTimeout(() => {
            previewSection.scrollIntoView({ behavior: 'smooth' });
            showToast('📓 Live preview activated! You can now edit and see changes in real-time.', 'success');
        }, 300);
    }
}

function transformNotebookData(datadogNotebook) {
    /**
     * Transform Datadog notebook structure to our preview format
     */
    try {
        const attrs = datadogNotebook.data?.attributes || datadogNotebook.attributes || datadogNotebook;
        
        if (!attrs) {
            throw new Error('Invalid notebook structure');
        }
        
        const cells = (attrs.cells || []).map((cell, index) => {
            const definition = cell.attributes?.definition || cell.definition || cell;
            
            return {
                id: cell.id || `cell_${index}`,
                cell_type: definition.type || 'markdown',
                content: definition.text || definition.query || definition.requests?.[0]?.q || '',
                metadata: {
                    title: definition.title || '',
                    display_type: definition.display_type || definition.requests?.[0]?.display_type || 'line',
                    viz_type: definition.type || 'markdown'
                },
                definition: definition
            };
        });
        
        return {
            name: attrs.name || 'Generated Notebook',
            description: `Time Range: ${attrs.time?.live_span || '1h'} | Status: ${attrs.status || 'published'}`,
            cells: cells,
            metadata: {
                cell_count: cells.length,
                time_range: attrs.time?.live_span || '1h',
                status: attrs.status || 'published',
                type: attrs.metadata?.type || 'investigation'
            },
            original: datadogNotebook
        };
    } catch (error) {
        console.error('Error transforming notebook data:', error);
        return {
            name: 'Generated Notebook',
            description: 'Preview data transformation failed',
            cells: [],
            metadata: {
                cell_count: 0,
                status: 'error'
            }
        };
    }
}

function showPreviewControls() {
    /**
     * Show and initialize preview controls
     */
    const controls = document.querySelector('.preview-controls');
    if (controls) {
        // Update mode text
        updatePreviewModeText();
        
        // Add real-time update toggle
        if (!controls.querySelector('.realtime-toggle')) {
            const realtimeToggle = document.createElement('button');
            realtimeToggle.className = 'btn btn-small btn-outline realtime-toggle';
            realtimeToggle.innerHTML = `
                <span class="btn-icon">⚡</span>
                <span>Real-time Updates</span>
            `;
            realtimeToggle.onclick = toggleRealtimeUpdates;
            controls.insertBefore(realtimeToggle, controls.firstChild);
        }
    }
}

function updatePreviewModeText() {
    const modeText = document.getElementById('previewModeText');
    if (modeText) {
        switch (currentPreviewMode) {
            case 'preview':
                modeText.textContent = 'Switch to Edit Mode';
                break;
            case 'edit':
                modeText.textContent = 'Switch to Split Mode';
                break;
            case 'split':
                modeText.textContent = 'Switch to Preview Mode';
                break;
        }
    }
}

function toggleRealtimeUpdates() {
    /**
     * Toggle real-time updates for the preview
     */
    const toggle = document.querySelector('.realtime-toggle');
    const isActive = toggle.classList.contains('active');
    
    if (isActive) {
        toggle.classList.remove('active');
        toggle.querySelector('span:last-child').textContent = 'Real-time Updates';
        showToast('Real-time updates disabled', 'info');
    } else {
        toggle.classList.add('active');
        toggle.querySelector('span:last-child').textContent = 'Updates Active';
        showToast('Real-time updates enabled', 'success');
        
        // Start watching for changes
        startRealtimeUpdates();
    }
}

function startRealtimeUpdates() {
    /**
     * Start monitoring for changes and update preview
     */
    if (window.realtimeUpdateInterval) {
        clearInterval(window.realtimeUpdateInterval);
    }
    
    window.realtimeUpdateInterval = setInterval(() => {
        if (isPreviewDirty) {
            updatePreviewContent();
            updatePreviewSidebar();
            isPreviewDirty = false;
        }
    }, 1000); // Update every second if changes detected
}

function markPreviewDirty() {
    /**
     * Mark preview as needing update
     */
    isPreviewDirty = true;
}

function closeLivePreview() {
    /**
     * Close the live preview section
     */
    const previewSection = document.getElementById('livePreviewSection');
    if (previewSection) {
        previewSection.classList.remove('visible');
        setTimeout(() => {
            previewSection.style.display = 'none';
        }, 300);
    }
    
    // Clean up real-time updates
    if (window.realtimeUpdateInterval) {
        clearInterval(window.realtimeUpdateInterval);
        window.realtimeUpdateInterval = null;
    }
    
    showToast('Live preview closed', 'info');
}

function updatePreviewContent() {
    /**
     * Update the main preview content based on current mode
     */
    if (!currentPreviewData) return;
    
    const previewModeContent = document.getElementById('previewModeContent');
    const editModeContent = document.getElementById('editModeContent');
    const splitModeContent = document.getElementById('splitModeContent');
    
    // Hide all content areas
    previewModeContent.style.display = 'none';
    editModeContent.style.display = 'none';
    splitModeContent.style.display = 'none';
    
    switch (currentPreviewMode) {
        case 'preview':
            previewModeContent.style.display = 'block';
            renderPreviewMode();
            break;
        case 'edit':
            editModeContent.style.display = 'block';
            renderEditMode();
            break;
        case 'split':
            splitModeContent.style.display = 'block';
            renderSplitMode();
            break;
    }
}

function renderPreviewMode() {
    /**
     * Render the preview mode content
     */
    const content = document.getElementById('previewModeContent');
    
    if (!currentPreviewData || !currentPreviewData.cells) {
        content.innerHTML = `
            <div class="empty-preview">
                <div class="empty-icon">📓</div>
                <h4>No Cells to Preview</h4>
                <p>The notebook doesn't contain any cells to display</p>
            </div>
        `;
        return;
    }
    
    const cellsHtml = currentPreviewData.cells.map((cell, index) => {
        return renderNotebookCell(cell, index);
    }).join('');
    
    content.innerHTML = `
        <div class="notebook-cells">
            <div class="notebook-header">
                <h2>${currentPreviewData.name || 'Generated Notebook'}</h2>
                ${currentPreviewData.description ? `<p class="notebook-description">${currentPreviewData.description}</p>` : ''}
            </div>
            ${cellsHtml}
        </div>
    `;
    
    // Add click handlers for cell selection
    content.querySelectorAll('.notebook-cell').forEach((cell, index) => {
        cell.addEventListener('click', () => selectCell(index));
    });
}

function renderNotebookCell(cell, index) {
    /**
     * Render a single notebook cell with enhanced Datadog support
     */
    const cellTypeIcon = getCellTypeIcon(cell.cell_type);
    const cellTypeName = getCellTypeName(cell.cell_type);
    
    let cellContent = '';
    
    switch (cell.cell_type) {
        case 'markdown':
            cellContent = `
                <div class="cell-markdown">
                    ${formatMarkdown(cell.content)}
                </div>
            `;
            break;
        case 'timeseries':
            const queries = cell.definition?.requests || [];
            cellContent = `
                <div class="cell-timeseries">
                    <div class="timeseries-header">
                        <h4>📈 Time Series Visualization</h4>
                        ${cell.metadata?.title ? `<p class="chart-title">${cell.metadata.title}</p>` : ''}
                    </div>
                    <div class="timeseries-queries">
                        ${queries.map(req => `
                            <div class="query-item">
                                <code>${escapeHtml(req.q || req.query || 'No query')}</code>
                                <span class="query-meta">${req.display_type || 'line'}</span>
                            </div>
                        `).join('')}
                    </div>
                    <div class="chart-placeholder">
                        📊 Chart would render here with query results
                    </div>
                </div>
            `;
            break;
        case 'query_value':
            cellContent = `
                <div class="cell-query-value">
                    <div class="query-value-header">
                        <h4>🔢 Query Value</h4>
                    </div>
                    <div class="query-display">
                        <code>${escapeHtml(cell.content)}</code>
                    </div>
                    <div class="value-placeholder">
                        📊 Current value would display here
                    </div>
                </div>
            `;
            break;
        case 'log_stream':
            cellContent = `
                <div class="cell-log-stream">
                    <div class="log-stream-header">
                        <h4>📝 Log Stream</h4>
                    </div>
                    <div class="log-query">
                        <code>${escapeHtml(cell.content)}</code>
                    </div>
                    <div class="log-placeholder">
                        📄 Log entries would stream here
                    </div>
                </div>
            `;
            break;
        default:
            cellContent = `
                <div class="cell-content">
                    <div class="content-text">${escapeHtml(cell.content || 'Empty cell')}</div>
                    ${cell.metadata?.display_type ? `<small class="content-meta">Type: ${cell.metadata.display_type}</small>` : ''}
                </div>
            `;
    }
    
    return `
        <div class="notebook-cell ${selectedCellIndex === index ? 'selected' : ''}" 
             data-cell-index="${index}" 
             data-cell-type="${cell.cell_type}">
            <div class="cell-header">
                <div class="cell-type">
                    <span class="cell-type-icon">${cellTypeIcon}</span>
                    <span class="cell-type-name">${cellTypeName}</span>
                    <span class="cell-index">#${index + 1}</span>
                </div>
                <div class="cell-actions">
                    <button class="cell-action-btn" onclick="editCell(${index})" title="Edit cell">
                        ✏️
                    </button>
                    <button class="cell-action-btn" onclick="moveCell(${index}, 'up')" title="Move up" ${index === 0 ? 'disabled' : ''}>
                        ⬆️
                    </button>
                    <button class="cell-action-btn" onclick="moveCell(${index}, 'down')" title="Move down">
                        ⬇️
                    </button>
                    <button class="cell-action-btn" onclick="duplicateCell(${index})" title="Duplicate cell">
                        📋
                    </button>
                    <button class="cell-action-btn" onclick="deleteCell(${index})" title="Delete cell">
                        🗑️
                    </button>
                </div>
            </div>
            <div class="cell-content">
                ${cellContent}
            </div>
        </div>
    `;
}

function renderEditMode() {
    /**
     * Render the edit mode content
     */
    const content = document.getElementById('editModeContent');
    
    if (!currentPreviewData || !currentPreviewData.cells) {
        content.innerHTML = `
            <div class="empty-preview">
                <div class="empty-icon">✏️</div>
                <h4>No Cells to Edit</h4>
                <p>Add some cells to start editing</p>
                <button class="btn btn-primary" onclick="addTextCell()">
                    <span class="btn-icon">📝</span>
                    Add Text Cell
                </button>
            </div>
        `;
        return;
    }
    
    const editableHtml = currentPreviewData.cells.map((cell, index) => {
        return `
            <div class="editable-cell" data-cell-index="${index}">
                <div class="cell-header">
                    <div class="cell-type">
                        <span>${getCellTypeIcon(cell.cell_type)}</span>
                        <select onchange="changeCellType(${index}, this.value)">
                            <option value="text" ${cell.cell_type === 'text' ? 'selected' : ''}>Text</option>
                            <option value="query" ${cell.cell_type === 'query' ? 'selected' : ''}>Query</option>
                            <option value="visualization" ${cell.cell_type === 'visualization' ? 'selected' : ''}>Visualization</option>
                        </select>
                    </div>
                    <div class="cell-actions">
                        <button class="cell-action-btn" onclick="moveCell(${index}, -1)" title="Move up">⬆️</button>
                        <button class="cell-action-btn" onclick="moveCell(${index}, 1)" title="Move down">⬇️</button>
                        <button class="cell-action-btn" onclick="deleteCell(${index})" title="Delete">🗑️</button>
                    </div>
                </div>
                <textarea class="cell-editor-textarea" 
                         onchange="updateCellContent(${index}, this.value)"
                         placeholder="Enter cell content...">${escapeHtml(cell.content || '')}</textarea>
            </div>
        `;
    }).join('');
    
    content.innerHTML = `
        <div class="cell-editor">
            ${editableHtml}
            <button class="btn btn-outline" onclick="addTextCell()" style="margin-top: 1rem;">
                <span class="btn-icon">➕</span>
                Add New Cell
            </button>
        </div>
    `;
}

function renderSplitMode() {
    /**
     * Render the split mode content
     */
    const content = document.getElementById('splitModeContent');
    
    content.innerHTML = `
        <div class="split-left">
            <h5>📝 Editor</h5>
            <div class="split-editor" id="splitEditor">
                <!-- Editor content will be rendered here -->
            </div>
        </div>
        <div class="split-right">
            <h5>👁️ Preview</h5>
            <div class="split-preview" id="splitPreview">
                <!-- Preview content will be rendered here -->
            </div>
        </div>
    `;
    
    // Render editor and preview separately
    const editor = document.getElementById('splitEditor');
    const preview = document.getElementById('splitPreview');
    
    if (currentPreviewData && currentPreviewData.cells) {
        // Render simplified editor
        editor.innerHTML = currentPreviewData.cells.map((cell, index) => `
            <div class="simple-cell-editor" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>${getCellTypeName(cell.cell_type)}</strong>
                    <button onclick="selectCell(${index})" class="btn btn-small">Select</button>
                </div>
                <textarea onchange="updateCellContent(${index}, this.value)" 
                         style="width: 100%; min-height: 80px; font-family: monospace;">${escapeHtml(cell.content || '')}</textarea>
            </div>
        `).join('');
        
        // Render simplified preview
        preview.innerHTML = currentPreviewData.cells.map(cell => {
            switch (cell.cell_type) {
                case 'text':
                case 'markdown':
                    return `<div style="margin-bottom: 1rem; padding: 1rem; border: 1px solid #e5e9ec; border-radius: 8px;">${formatMarkdown(cell.content)}</div>`;
                case 'query':
                    return `<div style="margin-bottom: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; font-family: monospace;">${escapeHtml(cell.content)}</div>`;
                default:
                    return `<div style="margin-bottom: 1rem; padding: 1rem; border: 1px solid #e5e9ec; border-radius: 8px;">${escapeHtml(cell.content || '')}</div>`;
            }
        }).join('');
    }
}

function updatePreviewSidebar() {
    /**
     * Update the preview sidebar with enhanced notebook metadata and outline
     */
    if (!currentPreviewData) return;
    
    // Update metadata with enhanced information
    const metadata = currentPreviewData.metadata || {};
    
    document.getElementById('previewTitle').textContent = currentPreviewData.name || 'Untitled Notebook';
    document.getElementById('previewCellCount').textContent = metadata.cell_count || (currentPreviewData.cells ? currentPreviewData.cells.length : 0);
    document.getElementById('previewType').textContent = metadata.type || 'investigation';
    
    const statusElement = document.getElementById('previewStatus');
    if (statusElement) {
        statusElement.textContent = metadata.status || 'draft';
        statusElement.className = `metadata-value status ${metadata.status || 'draft'}`;
    }
    
    // Add time range metadata if not already present
    const metadataContainer = document.querySelector('.preview-metadata');
    if (metadataContainer && !metadataContainer.querySelector('.metadata-time-range')) {
        const timeRangeElement = document.createElement('div');
        timeRangeElement.className = 'metadata-item metadata-time-range';
        timeRangeElement.innerHTML = `
            <span class="metadata-label">Time Range:</span>
            <span class="metadata-value">${metadata.time_range || '1h'}</span>
        `;
        metadataContainer.insertBefore(timeRangeElement, metadataContainer.lastElementChild);
    }
    
    // Update outline with enhanced cell information
    const outlineList = document.getElementById('notebookOutline');
    if (outlineList) {
        if (currentPreviewData.cells && currentPreviewData.cells.length > 0) {
            const outlineItems = currentPreviewData.cells.map((cell, index) => {
                const title = getCellTitle(cell);
                const typeIcon = getCellTypeIcon(cell.cell_type);
                const typeName = getCellTypeName(cell.cell_type);
                
                return `
                    <div class="outline-item ${selectedCellIndex === index ? 'active' : ''}" 
                         onclick="selectCell(${index})"
                         data-cell-index="${index}"
                         title="${typeName}: ${title}">
                        <span class="outline-item-type">${typeIcon}</span>
                        <span class="outline-item-title">${title}</span>
                        <span class="outline-item-index">#${index + 1}</span>
                    </div>
                `;
            }).join('');
            
            outlineList.innerHTML = outlineItems;
        } else {
            outlineList.innerHTML = `
                <div class="outline-item empty">
                    <span class="outline-item-type">📄</span>
                    <span class="outline-item-title">No cells available</span>
                </div>
            `;
        }
    }
    
    // Update cell count in Quick Actions section
    const quickActions = document.querySelector('.preview-actions');
    if (quickActions && !quickActions.querySelector('.cell-count-display')) {
        const cellCountDisplay = document.createElement('div');
        cellCountDisplay.className = 'cell-count-display';
        cellCountDisplay.innerHTML = `
            <div class="count-item">
                <span class="count-label">📊 Charts:</span>
                <span class="count-value">${(currentPreviewData.cells || []).filter(cell => cell.cell_type === 'timeseries').length}</span>
            </div>
            <div class="count-item">
                <span class="count-label">📝 Text:</span>
                <span class="count-value">${(currentPreviewData.cells || []).filter(cell => cell.cell_type === 'markdown').length}</span>
            </div>
        `;
        quickActions.insertBefore(cellCountDisplay, quickActions.firstChild);
    }
}

// Helper functions for rendering
function getCellTypeIcon(cellType) {
    const icons = {
        'text': '📝',
        'markdown': '📝',
        'query': '🔍',
        'visualization': '📊',
        'code': '💻',
        'timeseries': '📈',
        'query_value': '🔢',
        'log_stream': '📝',
        'distribution': '📊',
        'hostmap': '🗺️',
        'change': '🔄',
        'image': '🖼️'
    };
    return icons[cellType] || '📄';
}

function getCellTypeName(cellType) {
    const names = {
        'text': 'Text',
        'markdown': 'Markdown',
        'query': 'Query',
        'visualization': 'Visualization',
        'code': 'Code',
        'timeseries': 'Time Series',
        'query_value': 'Query Value',
        'log_stream': 'Log Stream',
        'distribution': 'Distribution',
        'hostmap': 'Host Map',
        'change': 'Change',
        'image': 'Image'
    };
    return names[cellType] || 'Unknown';
}

function getCellTitle(cell) {
    if (!cell.content) return 'Empty Cell';
    
    // Extract first line or meaningful title
    const firstLine = cell.content.split('\n')[0].trim();
    if (firstLine.length > 40) {
        return firstLine.substring(0, 40) + '...';
    }
    return firstLine || 'Empty Cell';
}

function formatMarkdown(content) {
    if (!content) return '';
    
    // Simple markdown formatting
    return content
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Preview control functions
function setPreviewMode(mode) {
    currentPreviewMode = mode;
    
    // Update active button
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.mode === mode) {
            btn.classList.add('active');
        }
    });
    
    updatePreviewContent();
}

function togglePreviewMode() {
    const modes = ['preview', 'edit', 'split'];
    const currentIndex = modes.indexOf(currentPreviewMode);
    const nextMode = modes[(currentIndex + 1) % modes.length];
    setPreviewMode(nextMode);
    
    // Update button text
    const modeText = document.getElementById('previewModeText');
    if (modeText) {
        modeText.textContent = `Switch to ${modes[(modes.indexOf(nextMode) + 1) % modes.length]} Mode`;
    }
}

function adjustZoom(delta) {
    currentZoomLevel = Math.max(0.5, Math.min(2.0, currentZoomLevel + delta));
    
    const viewport = document.getElementById('previewViewport');
    if (viewport) {
        viewport.style.transform = `scale(${currentZoomLevel})`;
        viewport.style.transformOrigin = 'top left';
    }
    
    document.getElementById('zoomLevel').textContent = `${Math.round(currentZoomLevel * 100)}%`;
}

function refreshPreview() {
    updatePreviewContent();
    updatePreviewSidebar();
    showToast('Preview refreshed', 'success');
}

function savePreviewChanges() {
    if (currentPreviewData) {
        // In a real implementation, this would save to the backend
        showToast('Changes saved locally', 'success');
        console.log('Saving preview changes:', currentPreviewData);
    }
}

// Cell manipulation functions
function selectCell(index) {
    selectedCellIndex = index;
    updatePreviewContent();
    updatePreviewSidebar();
}

function addTextCell() {
    if (!currentPreviewData) {
        currentPreviewData = { cells: [] };
    }
    if (!currentPreviewData.cells) {
        currentPreviewData.cells = [];
    }
    
    const newCell = {
        cell_type: 'text',
        content: 'New text cell...'
    };
    
    currentPreviewData.cells.push(newCell);
    selectedCellIndex = currentPreviewData.cells.length - 1;
    
    updatePreviewContent();
    updatePreviewSidebar();
    showToast('Text cell added', 'success');
}

function addQueryCell() {
    if (!currentPreviewData) {
        currentPreviewData = { cells: [] };
    }
    if (!currentPreviewData.cells) {
        currentPreviewData.cells = [];
    }
    
    const newCell = {
        cell_type: 'query',
        content: 'avg:system.cpu.user{*}'
    };
    
    currentPreviewData.cells.push(newCell);
    selectedCellIndex = currentPreviewData.cells.length - 1;
    
    updatePreviewContent();
    updatePreviewSidebar();
    showToast('Query cell added', 'success');
}

function addVisualizationCell() {
    if (!currentPreviewData) {
        currentPreviewData = { cells: [] };
    }
    if (!currentPreviewData.cells) {
        currentPreviewData.cells = [];
    }
    
    const newCell = {
        cell_type: 'visualization',
        content: 'Visualization cell',
        graph_definition: {
            title: 'New Visualization',
            viz_type: 'timeseries'
        }
    };
    
    currentPreviewData.cells.push(newCell);
    selectedCellIndex = currentPreviewData.cells.length - 1;
    
    updatePreviewContent();
    updatePreviewSidebar();
    showToast('Visualization cell added', 'success');
}

function duplicateCell(index) {
    if (!currentPreviewData || !currentPreviewData.cells || index < 0 || index >= currentPreviewData.cells.length) {
        return;
    }
    
    const cellToDuplicate = { ...currentPreviewData.cells[index] };
    currentPreviewData.cells.splice(index + 1, 0, cellToDuplicate);
    selectedCellIndex = index + 1;
    
    updatePreviewContent();
    updatePreviewSidebar();
    showToast('Cell duplicated', 'success');
}

function deleteCell(index) {
    if (!currentPreviewData || !currentPreviewData.cells || index < 0 || index >= currentPreviewData.cells.length) {
        return;
    }
    
    if (confirm('Are you sure you want to delete this cell?')) {
        currentPreviewData.cells.splice(index, 1);
        if (selectedCellIndex >= index) {
            selectedCellIndex = Math.max(-1, selectedCellIndex - 1);
        }
        
        updatePreviewContent();
        updatePreviewSidebar();
        showToast('Cell deleted', 'warning');
    }
}

function editCell(index) {
    selectCell(index);
    setPreviewMode('edit');
}

function updateCellContent(index, newContent) {
    if (!currentPreviewData || !currentPreviewData.cells || index < 0 || index >= currentPreviewData.cells.length) {
        return;
    }
    
    currentPreviewData.cells[index].content = newContent;
    
    // Update preview if in split mode
    if (currentPreviewMode === 'split') {
        renderSplitMode();
    }
}

function changeCellType(index, newType) {
    if (!currentPreviewData || !currentPreviewData.cells || index < 0 || index >= currentPreviewData.cells.length) {
        return;
    }
    
    currentPreviewData.cells[index].cell_type = newType;
    updatePreviewContent();
    updatePreviewSidebar();
    showToast(`Cell type changed to ${getCellTypeName(newType)}`, 'info');
}

function moveCell(index, direction) {
    if (!currentPreviewData || !currentPreviewData.cells || index < 0 || index >= currentPreviewData.cells.length) {
        return;
    }
    
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= currentPreviewData.cells.length) {
        return;
    }
    
    // Swap cells
    const temp = currentPreviewData.cells[index];
    currentPreviewData.cells[index] = currentPreviewData.cells[newIndex];
    currentPreviewData.cells[newIndex] = temp;
    
    selectedCellIndex = newIndex;
    
    updatePreviewContent();
    updatePreviewSidebar();
    showToast('Cell moved', 'info');
}

function scrollToGenerator() {
    const generatorSection = document.querySelector('.generator-section');
    if (generatorSection) {
        generatorSection.scrollIntoView({ behavior: 'smooth' });
    }
}

// Toast notification function
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-header">
            <span class="toast-title">${message}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 3000);
}

// Integrate preview with existing notebook generation
function enhanceHandleGenerationSuccess(originalFunction) {
    return function(result, mode = 'notebook') {
        // Call original function
        originalFunction.call(this, result, mode);
        
        // Show live preview for notebooks only
        if (mode === 'notebook' && result.notebook_json) {
            // Add a button to show live preview
            const resultsActions = document.querySelector('.results-actions');
            if (resultsActions) {
                const previewBtn = document.createElement('button');
                previewBtn.className = 'btn btn-small btn-primary';
                previewBtn.innerHTML = `
                    <span class="btn-icon">👁️</span>
                    Live Preview
                `;
                previewBtn.onclick = () => showLivePreview(result.notebook_json);
                resultsActions.appendChild(previewBtn);
            }
        }
    };
}

// Override the original function
if (typeof handleGenerationSuccess !== 'undefined') {
    handleGenerationSuccess = enhanceHandleGenerationSuccess(handleGenerationSuccess);
}

// Metric Analysis Functions
async function analyzeGeneratedMetrics(result, mode = 'notebook') {
    const analysisContent = document.getElementById('analysisContent');
    if (!analysisContent) return;

    try {
        // Show loading state
        showAnalysisLoading();
        
        // Extract metrics from the generated content
        const suggestedMetrics = extractMetricsFromResult(result, mode);
        
        if (suggestedMetrics.length === 0) {
            showEmptyAnalysis();
            return;
        }

        // Call the metric analysis API
        const response = await fetch('/metrics/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                suggested_metrics: suggestedMetrics,
                customer_id: 'current_user' // Can be made dynamic
            })
        });

        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }

        const analysisResult = await response.json();
        displayMetricAnalysis(analysisResult);

    } catch (error) {
        console.error('Metric analysis failed:', error);
        showAnalysisError(error.message);
    }
}

function extractMetricsFromResult(result, mode) {
    const suggestedMetrics = [];
    const content = mode === 'notebook' ? result.notebook_json : result.dashboard_json;
    
    if (!content) return suggestedMetrics;

    try {
        // Extract metrics from notebook cells or dashboard widgets
        if (mode === 'notebook' && content.data?.attributes?.cells) {
            content.data.attributes.cells.forEach(cell => {
                if (cell.definition?.requests) {
                    cell.definition.requests.forEach(request => {
                        if (request.queries) {
                            request.queries.forEach(query => {
                                if (query.metric) {
                                    suggestedMetrics.push({
                                        metric_name: query.metric,
                                        type: 'gauge', // Default type
                                        description: `Metric from ${cell.type || 'query'} cell`
                                    });
                                }
                            });
                        }
                    });
                }
            });
        } else if (mode === 'dashboard' && content.widgets) {
            content.widgets.forEach(widget => {
                if (widget.definition?.requests) {
                    widget.definition.requests.forEach(request => {
                        if (request.queries) {
                            request.queries.forEach(query => {
                                if (query.metric) {
                                    suggestedMetrics.push({
                                        metric_name: query.metric,
                                        type: widget.definition.type || 'gauge',
                                        description: `Metric from ${widget.definition.title || 'widget'}`
                                    });
                                }
                            });
                        }
                    });
                }
            });
        }

        // Also try to extract from a simpler structure using dynamic patterns
        if (suggestedMetrics.length === 0) {
            // Look for metric names in the content as strings using loaded patterns
            const contentStr = JSON.stringify(content);
            
            // Build regex patterns from loaded integration patterns
            const metricPatterns = [];
            Object.values(integrationPatterns).forEach(integration => {
                if (integration.prefixes) {
                    integration.prefixes.forEach(prefix => {
                        // Escape dots and create pattern for prefix + any additional parts
                        const escapedPrefix = prefix.replace(/\./g, '\\.');
                        metricPatterns.push(new RegExp(`${escapedPrefix}\\.\\w+(?:\\.\\w+)*`, 'g'));
                    });
                }
            });
            
            // If no patterns loaded, use fallback patterns
            if (metricPatterns.length === 0) {
                metricPatterns.push(
                    /system\.\w+\.\w+/g,
                    /aws\.\w+\.\w+/g,
                    /azure\.vm\.\w+/g,
                    /azure\.\w+\.\w+/g,
                    /nginx\.\w+\.\w+/g,
                    /mysql\.\w+\.\w+/g,
                    /redis\.\w+\.\w+/g,
                    /docker\.\w+\.\w+/g,
                    /kubernetes\.\w+\.\w+/g
                );
            }
            
            metricPatterns.forEach(pattern => {
                const matches = contentStr.match(pattern);
                if (matches) {
                    matches.forEach(match => {
                        if (!suggestedMetrics.find(m => m.metric_name === match)) {
                            suggestedMetrics.push({
                                metric_name: match,
                                type: 'gauge',
                                description: `Detected metric in generated content`
                            });
                        }
                    });
                }
            });
        }

        // Remove duplicates
        const uniqueMetrics = suggestedMetrics.filter((metric, index, self) =>
            index === self.findIndex(m => m.metric_name === metric.metric_name)
        );

        return uniqueMetrics;
    } catch (error) {
        console.error('Failed to extract metrics:', error);
        return [];
    }
}

function showAnalysisLoading() {
    const analysisContent = document.getElementById('analysisContent');
    analysisContent.innerHTML = `
        <div class="loading-analysis">
            <div class="analysis-spinner"></div>
            <h4>🔍 Analyzing Metrics</h4>
            <p>Checking which metrics exist in your Datadog account...</p>
        </div>
    `;
}

function showEmptyAnalysis() {
    const analysisContent = document.getElementById('analysisContent');
    analysisContent.innerHTML = `
        <div class="empty-analysis">
            <div class="empty-analysis-icon">📊</div>
            <h4>No Metrics to Analyze</h4>
            <p>Generate a notebook or dashboard first to see metric analysis.</p>
        </div>
    `;
}

function showAnalysisError(message) {
    const analysisContent = document.getElementById('analysisContent');
    analysisContent.innerHTML = `
        <div class="empty-analysis">
            <div class="empty-analysis-icon">❌</div>
            <h4>Analysis Failed</h4>
            <p>${message}</p>
        </div>
    `;
}

function displayMetricAnalysis(analysisResult) {
    const analysisContent = document.getElementById('analysisContent');
    
    const coveragePercentage = analysisResult.coverage_percentage || 0;
    const existingMetrics = analysisResult.existing_metrics || [];
    const missingMetrics = analysisResult.missing_metrics || [];
    const recommendations = analysisResult.recommendations || [];
    
    // Group existing metrics by integration
    const groupedExistingMetrics = groupMetricsByIntegration(existingMetrics);
    
    analysisContent.innerHTML = `
        <div class="metric-analysis-header">
            <h3>🔍 Metric Coverage Analysis</h3>
            <p>Analysis of suggested metrics against your Datadog account</p>
        </div>

        <div class="analysis-summary">
            <div class="coverage-stats">
                <div class="coverage-stat">
                    <span class="coverage-stat-number coverage-percentage">${coveragePercentage.toFixed(1)}%</span>
                    <span class="coverage-stat-label">Coverage</span>
                </div>
                <div class="coverage-stat">
                    <span class="coverage-stat-number">${existingMetrics.length}</span>
                    <span class="coverage-stat-label">Available</span>
                </div>
                <div class="coverage-stat">
                    <span class="coverage-stat-number">${missingMetrics.length}</span>
                    <span class="coverage-stat-label">Missing</span>
                </div>
                <div class="coverage-stat">
                    <span class="coverage-stat-number">${Object.keys(groupedExistingMetrics).length}</span>
                    <span class="coverage-stat-label">Integrations</span>
                </div>
            </div>
        </div>

        <div class="metrics-sections">
            <div class="metrics-section existing">
                <h4>
                    <span>✅</span>
                    Available Metrics by Integration (${existingMetrics.length} total)
                </h4>
                <div class="integration-groups">
                    ${Object.keys(groupedExistingMetrics).length > 0 ? Object.entries(groupedExistingMetrics).map(([integration, metrics]) => `
                        <div class="integration-group">
                            <div class="integration-header" onclick="toggleIntegrationGroup('existing-${integration}')">
                                <div class="integration-info">
                                    <span class="integration-icon">${getIntegrationIcon(integration)}</span>
                                    <span class="integration-name">${getIntegrationDisplayName(integration)}</span>
                                    <span class="integration-count">(${metrics.length} metrics)</span>
                                </div>
                                <span class="toggle-icon">▼</span>
                            </div>
                            <div class="integration-metrics" id="existing-${integration}" style="display: none;">
                                ${metrics.map(metric => `
                                    <div class="analysis-metric-item existing">
                                        <div class="metric-info">
                                            <div class="metric-name-display">${metric}</div>
                                        </div>
                                        <div class="metric-status">
                                            <span class="status-indicator-metric exists">Available</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('') : '<p style="color: var(--text-secondary); text-align: center; padding: var(--space-4);">No existing metrics found</p>'}
                </div>
            </div>

            <div class="metrics-section missing">
                <h4>
                    <span>❌</span>
                    Missing Metrics (${missingMetrics.length})
                </h4>
                <div class="analysis-metric-list">
                    ${missingMetrics.length > 0 ? missingMetrics.map(metric => `
                        <div class="analysis-metric-item missing">
                            <div class="metric-info">
                                <div class="metric-name-display">${metric.metric_name}</div>
                                <div class="metric-description">${metric.description || ''}</div>
                            </div>
                            <div class="metric-status">
                                <span class="status-indicator-metric missing">Missing</span>
                                <span class="priority-badge ${metric.priority}">${metric.priority}</span>
                            </div>
                        </div>
                    `).join('') : '<p style="color: var(--text-secondary); text-align: center; padding: var(--space-4);">All metrics are available! 🎉</p>'}
                </div>
            </div>
        </div>

        ${recommendations.length > 0 ? `
            <div class="recommendations-section">
                <h4>
                    <span>🛠️</span>
                    Setup Recommendations
                </h4>
                <div class="recommendation-list">
                    ${recommendations.map(rec => `
                        <div class="recommendation-item">
                            <div class="recommendation-header">
                                <div class="integration-name">${rec.integration}</div>
                                <div class="recommendation-metrics">
                                    <span class="metrics-count">${rec.missing_metrics_count} metrics</span>
                                    <span class="priority-badge ${rec.priority}">${rec.priority} priority</span>
                                </div>
                            </div>
                            <p style="color: var(--text-secondary); margin-bottom: var(--space-3);">
                                ${rec.description || `Set up ${rec.integration} integration to monitor ${rec.missing_metrics_count} missing metrics`}
                            </p>
                            <div class="recommendation-actions">
                                <a href="${rec.setup_url || '#'}" target="_blank" class="setup-btn">
                                    <span>🚀</span>
                                    Setup Guide
                                </a>
                                <button class="docs-btn" onclick="showIntegrationDetails('${rec.integration}')">
                                    <span>📚</span>
                                    View Details
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}
    `;
}

function groupMetricsByIntegration(metrics) {
    const grouped = {};
    
    metrics.forEach(metric => {
        const integration = detectMetricIntegration(metric);
        if (!grouped[integration]) {
            grouped[integration] = [];
        }
        grouped[integration].push(metric);
    });
    
    // Sort metrics within each integration
    Object.keys(grouped).forEach(integration => {
        grouped[integration].sort();
    });
    
    return grouped;
}

function detectMetricIntegration(metricName) {
    const metric = metricName.toLowerCase();
    
    // Use the loaded integration patterns if available
    if (integrationPatterns && Object.keys(integrationPatterns).length > 0) {
        for (const [integrationKey, patternInfo] of Object.entries(integrationPatterns)) {
            const prefixes = patternInfo.prefixes || [];
            for (const prefix of prefixes) {
                if (metric.startsWith(prefix.toLowerCase())) {
                    return integrationKey;
                }
            }
        }
    }
    
    // Fallback to basic pattern matching
    if (metric.startsWith('azure.vm')) return 'azure_vm';
    if (metric.startsWith('azure.')) return 'azure';
    if (metric.startsWith('aws.')) return 'aws';
    if (metric.startsWith('system.')) return 'system';
    if (metric.startsWith('nginx.')) return 'nginx';
    if (metric.startsWith('mysql.')) return 'mysql';
    if (metric.startsWith('redis.')) return 'redis';
    if (metric.startsWith('docker.')) return 'docker';
    if (metric.startsWith('kubernetes.')) return 'kubernetes';
    
    return 'other';
}

function getIntegrationIcon(integration) {
    const icons = {
        'azure_vm': '☁️',
        'azure': '🔵',
        'aws': '🟠',
        'amazon_ec2': '🟠',
        'amazon_s3': '🪣',
        'amazon_sqs': '📬',
        'amazon_vpc': '🌐',
        'system': '🖥️',
        'nginx': '🌐',
        'mysql': '🐬',
        'redis': '🔴',
        'docker': '🐳',
        'kubernetes': '⚙️',
        'other': '📊'
    };
    return icons[integration] || '📊';
}

function getIntegrationDisplayName(integration) {
    const names = {
        'azure_vm': 'Azure VM',
        'azure': 'Azure',
        'aws': 'AWS',
        'amazon_ec2': 'Amazon EC2',
        'amazon_s3': 'Amazon S3',
        'amazon_sqs': 'Amazon SQS',
        'amazon_vpc': 'Amazon VPC',
        'azure_functions': 'Azure Functions',
        'system': 'System',
        'nginx': 'NGINX',
        'mysql': 'MySQL',
        'redis': 'Redis',
        'docker': 'Docker',
        'kubernetes': 'Kubernetes',
        'other': 'Other'
    };
    return names[integration] || integration.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function toggleIntegrationGroup(groupId) {
    const group = document.getElementById(groupId);
    const header = group.previousElementSibling;
    const toggleIcon = header.querySelector('.toggle-icon');
    
    if (group.style.display === 'none') {
        group.style.display = 'block';
        toggleIcon.textContent = '▲';
        header.classList.add('expanded');
    } else {
        group.style.display = 'none';
        toggleIcon.textContent = '▼';
        header.classList.remove('expanded');
    }
}

async function showIntegrationDetails(integrationName) {
    try {
        const response = await fetch(`/integration/${integrationName}/setup`);
        if (!response.ok) {
            throw new Error('Failed to fetch integration details');
        }
        
        const result = await response.json();
        const setupGuide = result.setup_guide;
        
        // Create a simple alert/modal for now (can be enhanced later)
        const details = `
Integration: ${integrationName.toUpperCase()}
Description: ${setupGuide.description}
Estimated Time: ${setupGuide.estimated_setup_time}

Setup Steps:
${setupGuide.setup_steps.map((step, i) => `${i + 1}. ${step}`).join('\n')}

Available Metrics: ${setupGuide.available_metrics.length} total
First 10: ${setupGuide.available_metrics.slice(0, 10).join(', ')}${setupGuide.available_metrics.length > 10 ? '...' : ''}

Documentation: ${setupGuide.setup_url}
        `;
        
        alert(details);
        
    } catch (error) {
        console.error('Failed to show integration details:', error);
        showToast('Failed to load integration details', 'error');
    }
}

// Enhanced generation success handler to include metric analysis
function enhanceHandleGenerationSuccessWithAnalysis(originalFunction) {
    return function(result, mode = 'notebook') {
        // Call the original function first
        originalFunction.call(this, result, mode);
        
        // Add metric analysis
        setTimeout(() => {
            analyzeGeneratedMetrics(result, mode);
        }, 1000); // Delay to ensure tabs are ready
        
        // Show live preview for notebooks only
        if (mode === 'notebook' && result.notebook_json) {
            const resultsActions = document.querySelector('.results-actions');
            if (resultsActions && !resultsActions.querySelector('.live-preview-btn')) {
                const previewBtn = document.createElement('button');
                previewBtn.className = 'btn btn-small btn-primary live-preview-btn';
                previewBtn.innerHTML = `
                    <span class="btn-icon">👁️</span>
                    Live Preview
                `;
                previewBtn.onclick = () => showLivePreview(result.notebook_json);
                resultsActions.appendChild(previewBtn);
            }
        }
    };
}

// Override the enhanced function
if (typeof handleGenerationSuccess !== 'undefined') {
    handleGenerationSuccess = enhanceHandleGenerationSuccessWithAnalysis(handleGenerationSuccess);
}

// Add some helpful console messages
console.log('🐕 Datadog Notebook Generator');
console.log('💡 Use Ctrl/Cmd + Enter to quickly generate notebooks');
console.log('⚡ Click example cards to quickly fill the form');
console.log('🔧 Check the console for any errors or issues');
console.log('📊 Metric analysis will show after generation'); 