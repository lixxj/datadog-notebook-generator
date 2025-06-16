// Global variables
let currentNotebookData = null;
let currentRequestData = null;

// DOM elements
const notebookForm = document.getElementById('notebookForm');
const generateBtn = document.getElementById('generateBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const statusIndicator = document.getElementById('statusIndicator');

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

// Example data
const examples = {
    support: {
        description: "Investigate high memory usage on web servers causing timeouts and slow response times. Show memory metrics, CPU usage, and application performance indicators over the last 4 hours to identify patterns and potential memory leaks.",
        authorName: "Support Engineer",
        authorEmail: "support@company.com"
    },
    demo: {
        description: "Demonstrate metric rollup functions with different time windows (5m, 1h, 1d) and aggregation methods (avg, sum, max). Show how different rollup strategies affect data visualization and analysis accuracy.",
        authorName: "Demo User",
        authorEmail: "demo@company.com"
    },
    escalation: {
        description: "Comprehensive analysis of database performance degradation affecting multiple services. Include connection pool metrics, query execution times, disk I/O, and correlation with application error rates over the past 24 hours.",
        authorName: "SRE Team",
        authorEmail: "sre@company.com"
    },
    prototype: {
        description: "Quick monitoring setup for new microservice deployment with key performance indicators. Include request rates, response times, error rates, CPU and memory usage, and custom business metrics for a newly deployed payment processing service.",
        authorName: "DevOps Engineer", 
        authorEmail: "devops@company.com"
    }
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkSystemStatus();
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
    
    // Example cards
    const exampleCards = document.querySelectorAll('.example-card');
    exampleCards.forEach(card => {
        card.addEventListener('click', function() {
            const exampleType = this.getAttribute('onclick').match(/'(.+)'/)[1];
            fillExample(exampleType);
        });
    });
    
    // Auto-resize textarea
    const textarea = document.getElementById('description');
    if (textarea) {
        textarea.addEventListener('input', autoResizeTextarea);
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
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

async function handleFormSubmission(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const requestData = {
        description: formData.get('description'),
        author_name: formData.get('authorName'),
        author_email: formData.get('authorEmail'),
        create_in_datadog: formData.get('createInDatadog') === 'on'
    };
    
    // Validate form data
    if (!requestData.description.trim()) {
        showError('Please provide a description for your notebook.');
        return;
    }
    
    currentRequestData = requestData;
    
    try {
        showLoading(true);
        hideMessages();
        
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            handleGenerationSuccess(result);
        } else {
            handleGenerationError(result.message || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Generation failed:', error);
        handleGenerationError('Network error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function handleGenerationSuccess(result) {
    currentNotebookData = result;
    
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.classList.add('slide-up');
    
    // Populate tabs
    populatePreviewTab(result.preview);
    populateJsonTab(result.notebook_json);
    populateDetailsTab(result);
    
    // Show success message
    if (result.datadog_notebook_id) {
        const message = `Notebook created in Datadog with ID: ${result.datadog_notebook_id}`;
        const url = `https://app.datadoghq.com/notebook/${result.datadog_notebook_id}`;
        successDetails.innerHTML = `${message}<br><a href="${url}" target="_blank" style="color: inherit; text-decoration: underline;">View in Datadog →</a>`;
    } else {
        successDetails.textContent = 'Notebook generated successfully! Use the options above to download or create in Datadog.';
    }
    
    showSuccess();
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

function populateDetailsTab(result) {
    const details = [];
    
    if (currentRequestData) {
        details.push({ label: 'Description', value: currentRequestData.description });
        if (currentRequestData.author_name) {
            details.push({ label: 'Author', value: currentRequestData.author_name });
        }
        if (currentRequestData.author_email) {
            details.push({ label: 'Email', value: currentRequestData.author_email });
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

function fillExample(exampleType) {
    const example = examples[exampleType];
    if (!example) return;
    
    // Fill form fields
    document.getElementById('description').value = example.description;
    document.getElementById('authorName').value = example.authorName;
    document.getElementById('authorEmail').value = example.authorEmail;
    
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

// Add some helpful console messages
console.log('🐕 Datadog Notebook Generator');
console.log('💡 Use Ctrl/Cmd + Enter to quickly generate notebooks');
console.log('⚡ Click example cards to quickly fill the form');
console.log('🔧 Check the console for any errors or issues'); 