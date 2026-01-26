/**
 * Job Application Tool - Frontend JavaScript
 */

const API_BASE = '/api';

// State
let state = {
    sessionId: null,
    parsedCV: null,
    currentDownloadId: null
};

// DOM Elements
const elements = {
    // Sections
    stepUpload: document.getElementById('step-upload'),
    stepPreview: document.getElementById('step-preview'),
    stepJob: document.getElementById('step-job'),
    stepResults: document.getElementById('step-results'),
    stepHistory: document.getElementById('step-history'),

    // Upload
    dropzone: document.getElementById('dropzone'),
    cvFile: document.getElementById('cv-file'),
    uploadStatus: document.getElementById('upload-status'),

    // Preview
    cvPreview: document.getElementById('cv-preview'),
    btnChangeCV: document.getElementById('btn-change-cv'),

    // Job
    jobUrl: document.getElementById('job-url'),
    outputLanguage: document.getElementById('output-language'),
    btnTailor: document.getElementById('btn-tailor'),
    tailorStatus: document.getElementById('tailor-status'),

    // Results
    companyAnalysis: document.getElementById('company-analysis'),
    jobRequirements: document.getElementById('job-requirements'),
    tailoringNotes: document.getElementById('tailoring-notes'),
    btnDownload: document.getElementById('btn-download'),
    btnNewJob: document.getElementById('btn-new-job'),

    // History
    historyList: document.getElementById('history-list'),

    // Loading
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingMessage: document.getElementById('loading-message')
};

// Utility Functions
function showSection(section) {
    [elements.stepUpload, elements.stepPreview, elements.stepJob, elements.stepResults, elements.stepHistory]
        .forEach(s => s.classList.add('hidden'));
    section.classList.remove('hidden');
}

function showLoading(message = 'Processing...') {
    elements.loadingMessage.textContent = message;
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

function showStatus(element, message, isError = false) {
    element.textContent = message;
    element.className = `status ${isError ? 'error' : 'success'}`;
    element.classList.remove('hidden');
}

function hideStatus(element) {
    element.classList.add('hidden');
}

// CV Upload Handlers
function setupDropzone() {
    const dropzone = elements.dropzone;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'));
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'));
    });

    dropzone.addEventListener('drop', handleDrop);
    elements.cvFile.addEventListener('change', handleFileSelect);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

async function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showStatus(elements.uploadStatus, 'Please upload a PDF file', true);
        return;
    }

    hideStatus(elements.uploadStatus);
    showLoading('Uploading and analyzing your CV...');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/upload-cv`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to upload CV');
        }

        state.sessionId = data.session_id;
        state.parsedCV = data.parsed_cv;

        renderCVPreview(data.parsed_cv);
        showSection(elements.stepPreview);
        elements.stepJob.classList.remove('hidden');

    } catch (error) {
        showStatus(elements.uploadStatus, error.message, true);
    } finally {
        hideLoading();
    }
}

function renderCVPreview(cv) {
    let html = '';

    if (cv.name) {
        html += `<h4>Name</h4><p><strong>${escapeHtml(cv.name)}</strong></p>`;
    }

    if (cv.contact) {
        const contact = cv.contact;
        const contactParts = [];
        if (contact.email) contactParts.push(contact.email);
        if (contact.phone) contactParts.push(contact.phone);
        if (contact.location) contactParts.push(contact.location);
        if (contactParts.length > 0) {
            html += `<h4>Contact</h4><p>${escapeHtml(contactParts.join(' | '))}</p>`;
        }
    }

    if (cv.summary) {
        html += `<h4>Summary</h4><p>${escapeHtml(cv.summary)}</p>`;
    }

    if (cv.experience && cv.experience.length > 0) {
        html += '<h4>Experience</h4>';
        cv.experience.forEach(exp => {
            html += `<p><strong>${escapeHtml(exp.title || '')}</strong> at ${escapeHtml(exp.company || '')}`;
            if (exp.dates) html += ` (${escapeHtml(exp.dates)})`;
            html += '</p>';
            if (exp.bullets && exp.bullets.length > 0) {
                html += '<ul>';
                exp.bullets.slice(0, 3).forEach(bullet => {
                    html += `<li>${escapeHtml(bullet)}</li>`;
                });
                if (exp.bullets.length > 3) {
                    html += `<li>... and ${exp.bullets.length - 3} more</li>`;
                }
                html += '</ul>';
            }
        });
    }

    if (cv.skills && cv.skills.length > 0) {
        html += `<h4>Skills</h4><p>${cv.skills.map(s => escapeHtml(s)).join(', ')}</p>`;
    }

    if (cv.education && cv.education.length > 0) {
        html += '<h4>Education</h4>';
        cv.education.forEach(edu => {
            html += `<p><strong>${escapeHtml(edu.degree || '')}</strong>`;
            if (edu.institution) html += ` - ${escapeHtml(edu.institution)}`;
            if (edu.dates) html += ` (${escapeHtml(edu.dates)})`;
            html += '</p>';
        });
    }

    elements.cvPreview.innerHTML = html || '<p>CV parsed successfully</p>';
}

// Tailor CV Handlers
async function tailorCV() {
    const jobUrl = elements.jobUrl.value.trim();

    if (!jobUrl) {
        showStatus(elements.tailorStatus, 'Please enter a job posting URL', true);
        return;
    }

    if (!isValidUrl(jobUrl)) {
        showStatus(elements.tailorStatus, 'Please enter a valid URL', true);
        return;
    }

    hideStatus(elements.tailorStatus);
    const outputLanguage = elements.outputLanguage.value;
    const langLabel = outputLanguage === 'french' ? 'French' : 'English';
    showLoading(`Analyzing job posting and tailoring your CV in ${langLabel}... This may take a moment.`);

    try {
        const formData = new FormData();
        formData.append('session_id', state.sessionId);
        formData.append('job_url', jobUrl);
        formData.append('output_language', outputLanguage);

        const response = await fetch(`${API_BASE}/tailor`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to tailor CV');
        }

        state.currentDownloadId = data.download_id;

        renderResults(data.job_analysis, data.tailored_cv);
        showSection(elements.stepResults);
        elements.stepHistory.classList.remove('hidden');
        loadHistory();

    } catch (error) {
        showStatus(elements.tailorStatus, error.message, true);
    } finally {
        hideLoading();
    }
}

function renderResults(jobAnalysis, tailoredCV) {
    // Company Analysis
    const company = jobAnalysis.company || {};
    let companyHtml = '';
    if (company.name) companyHtml += `<p><strong>Company:</strong> ${escapeHtml(company.name)}</p>`;
    if (company.industry) companyHtml += `<p><strong>Industry:</strong> ${escapeHtml(company.industry)}</p>`;
    if (company.description) companyHtml += `<p><strong>About:</strong> ${escapeHtml(company.description)}</p>`;
    if (company.culture) companyHtml += `<p><strong>Culture:</strong> ${escapeHtml(company.culture)}</p>`;
    elements.companyAnalysis.innerHTML = companyHtml || '<p>Company information not available</p>';

    // Job Requirements
    const job = jobAnalysis.job || {};
    const requirements = jobAnalysis.requirements || {};
    let reqHtml = '';
    if (job.title) reqHtml += `<p><strong>Position:</strong> ${escapeHtml(job.title)}</p>`;
    if (job.location) reqHtml += `<p><strong>Location:</strong> ${escapeHtml(job.location)}</p>`;
    if (job.level) reqHtml += `<p><strong>Level:</strong> ${escapeHtml(job.level)}</p>`;
    if (requirements.must_have && requirements.must_have.length > 0) {
        reqHtml += '<p><strong>Key Requirements:</strong></p><ul>';
        requirements.must_have.slice(0, 5).forEach(req => {
            reqHtml += `<li>${escapeHtml(req)}</li>`;
        });
        reqHtml += '</ul>';
    }
    elements.jobRequirements.innerHTML = reqHtml || '<p>Job requirements not available</p>';

    // Tailoring Notes
    const notes = tailoredCV.tailoring_notes || {};
    let notesHtml = '';
    if (notes.match_score) {
        notesHtml += `<p><strong>Match Assessment:</strong> <span class="match-score">${escapeHtml(notes.match_score)}</span></p>`;
    }
    if (notes.emphasis_areas && notes.emphasis_areas.length > 0) {
        notesHtml += `<p><strong>Emphasized:</strong> ${notes.emphasis_areas.map(e => escapeHtml(e)).join(', ')}</p>`;
    }
    if (notes.keywords_added && notes.keywords_added.length > 0) {
        notesHtml += '<p><strong>Keywords Added:</strong></p><div class="keywords">';
        notes.keywords_added.forEach(kw => {
            notesHtml += `<span class="keyword">${escapeHtml(kw)}</span>`;
        });
        notesHtml += '</div>';
    }
    elements.tailoringNotes.innerHTML = notesHtml || '<p>CV has been tailored for this position</p>';
}

// Download Handler
function downloadCV() {
    if (state.currentDownloadId) {
        window.location.href = `${API_BASE}/download/${state.currentDownloadId}`;
    }
}

// History
async function loadHistory() {
    if (!state.sessionId) return;

    try {
        const response = await fetch(`${API_BASE}/history/${state.sessionId}`);
        const data = await response.json();

        if (response.ok && data.applications && data.applications.length > 0) {
            renderHistory(data.applications);
        }
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function renderHistory(applications) {
    let html = '';
    applications.forEach(app => {
        html += `
            <div class="history-item">
                <div class="history-item-info">
                    <h4>${escapeHtml(app.job_title)} at ${escapeHtml(app.company)}</h4>
                    <p>${new Date(app.created_at).toLocaleDateString()}</p>
                </div>
                <button class="btn btn-secondary" onclick="downloadHistoryItem('${app.download_id}')">
                    Download
                </button>
            </div>
        `;
    });
    elements.historyList.innerHTML = html;
}

function downloadHistoryItem(downloadId) {
    window.location.href = `${API_BASE}/download/${downloadId}`;
}

// Utility
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Event Listeners
function setupEventListeners() {
    setupDropzone();

    elements.btnChangeCV.addEventListener('click', () => {
        showSection(elements.stepUpload);
        elements.stepPreview.classList.add('hidden');
        elements.stepJob.classList.add('hidden');
        elements.stepResults.classList.add('hidden');
        state.sessionId = null;
        state.parsedCV = null;
        elements.cvFile.value = '';
    });

    elements.btnTailor.addEventListener('click', tailorCV);

    elements.jobUrl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            tailorCV();
        }
    });

    elements.btnDownload.addEventListener('click', downloadCV);

    elements.btnNewJob.addEventListener('click', () => {
        elements.jobUrl.value = '';
        showSection(elements.stepPreview);
        elements.stepJob.classList.remove('hidden');
        elements.stepResults.classList.add('hidden');
        hideStatus(elements.tailorStatus);
    });
}

// Health Check
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        if (!data.api_key_configured) {
            showStatus(elements.uploadStatus,
                'Warning: ANTHROPIC_API_KEY not configured. Please set it as an environment variable.',
                true
            );
        }
    } catch (error) {
        showStatus(elements.uploadStatus,
            'Cannot connect to server. Please ensure the backend is running.',
            true
        );
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkHealth();
});
