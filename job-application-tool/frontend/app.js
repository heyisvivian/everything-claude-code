/**
 * Job Application Tool - Frontend JavaScript
 * Supports dual English/French CV generation with salary info
 */

const API_BASE = '/api';

// State
let state = {
    sessionId: null,
    parsedCV: null,
    currentDownloadIdEn: null,
    currentDownloadIdFr: null
};

// DOM Elements
const elements = {
    stepUpload: document.getElementById('step-upload'),
    stepPreview: document.getElementById('step-preview'),
    stepJob: document.getElementById('step-job'),
    stepResults: document.getElementById('step-results'),
    stepHistory: document.getElementById('step-history'),

    dropzone: document.getElementById('dropzone'),
    cvFile: document.getElementById('cv-file'),
    uploadStatus: document.getElementById('upload-status'),

    cvPreview: document.getElementById('cv-preview'),
    btnChangeCV: document.getElementById('btn-change-cv'),

    jobUrl: document.getElementById('job-url'),
    btnTailor: document.getElementById('btn-tailor'),
    tailorStatus: document.getElementById('tailor-status'),

    companyAnalysis: document.getElementById('company-analysis'),
    salaryInfo: document.getElementById('salary-info'),
    jobRequirements: document.getElementById('job-requirements'),
    tailoringNotes: document.getElementById('tailoring-notes'),
    btnDownloadEn: document.getElementById('btn-download-en'),
    btnDownloadFr: document.getElementById('btn-download-fr'),
    btnNewJob: document.getElementById('btn-new-job'),

    historyList: document.getElementById('history-list'),

    loadingOverlay: document.getElementById('loading-overlay'),
    loadingMessage: document.getElementById('loading-message')
};

function showSection(section) {
    [elements.stepUpload, elements.stepPreview, elements.stepJob, elements.stepResults]
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

// CV Upload
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
    if (files.length > 0) handleFile(files[0]);
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
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
        if (!response.ok) throw new Error(data.detail || 'Failed to upload CV');

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

    if (cv.name) html += `<h4>Name</h4><p><strong>${escapeHtml(cv.name)}</strong></p>`;

    if (cv.contact) {
        const contact = cv.contact;
        const parts = [contact.email, contact.phone, contact.location].filter(Boolean);
        if (parts.length > 0) html += `<h4>Contact</h4><p>${escapeHtml(parts.join(' | '))}</p>`;
    }

    if (cv.summary) html += `<h4>Summary</h4><p>${escapeHtml(cv.summary)}</p>`;

    if (cv.experience && cv.experience.length > 0) {
        html += '<h4>Experience</h4>';
        cv.experience.forEach(exp => {
            html += `<p><strong>${escapeHtml(exp.title || '')}</strong> at ${escapeHtml(exp.company || '')}`;
            if (exp.dates) html += ` (${escapeHtml(exp.dates)})`;
            html += '</p>';
            if (exp.bullets && exp.bullets.length > 0) {
                html += '<ul>';
                exp.bullets.slice(0, 2).forEach(b => html += `<li>${escapeHtml(b)}</li>`);
                if (exp.bullets.length > 2) html += `<li>... and ${exp.bullets.length - 2} more</li>`;
                html += '</ul>';
            }
        });
    }

    if (cv.skills && cv.skills.length > 0) {
        html += `<h4>Skills</h4><p>${cv.skills.slice(0, 10).map(s => escapeHtml(s)).join(', ')}</p>`;
    }

    elements.cvPreview.innerHTML = html || '<p>CV parsed successfully</p>';
}

// Tailor CV
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
    showLoading('Analyzing job posting and generating English + French CVs... This may take a moment.');

    try {
        const formData = new FormData();
        formData.append('session_id', state.sessionId);
        formData.append('job_url', jobUrl);

        const response = await fetch(`${API_BASE}/tailor`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to tailor CV');

        state.currentDownloadIdEn = data.download_id_en;
        state.currentDownloadIdFr = data.download_id_fr;

        renderResults(data.job_analysis, data.salary_info, data.tailoring_notes);
        showSection(elements.stepResults);
        loadHistory();

    } catch (error) {
        showStatus(elements.tailorStatus, error.message, true);
    } finally {
        hideLoading();
    }
}

function renderResults(jobAnalysis, salaryInfo, tailoringNotes) {
    // Company Analysis
    const company = jobAnalysis.company || {};
    let companyHtml = '';
    if (company.name) companyHtml += `<p><strong>Company:</strong> ${escapeHtml(company.name)}</p>`;
    if (company.industry) companyHtml += `<p><strong>Industry:</strong> ${escapeHtml(company.industry)}</p>`;
    if (company.description) companyHtml += `<p><strong>About:</strong> ${escapeHtml(company.description)}</p>`;
    elements.companyAnalysis.innerHTML = companyHtml || '<p>Company information not available</p>';

    // Salary Info
    let salaryHtml = '';
    if (salaryInfo && salaryInfo.estimated_range) {
        const range = salaryInfo.estimated_range;
        const currency = range.currency || 'EUR';
        const symbol = currency === 'EUR' ? '€' : currency === 'USD' ? '$' : currency;
        salaryHtml += `<p class="salary-range">${symbol}${range.min?.toLocaleString()} - ${symbol}${range.max?.toLocaleString()}</p>`;
        salaryHtml += `<span class="salary-confidence ${salaryInfo.confidence}">${salaryInfo.confidence} confidence</span>`;
        if (salaryInfo.notes) salaryHtml += `<p style="margin-top:0.5rem;font-size:0.85rem">${escapeHtml(salaryInfo.notes)}</p>`;
    } else {
        salaryHtml = '<p>Salary information not available</p>';
    }
    elements.salaryInfo.innerHTML = salaryHtml;

    // Job Requirements
    const job = jobAnalysis.job || {};
    const requirements = jobAnalysis.requirements || {};
    let reqHtml = '';
    if (job.title) reqHtml += `<p><strong>Position:</strong> ${escapeHtml(job.title)}</p>`;
    if (job.location) reqHtml += `<p><strong>Location:</strong> ${escapeHtml(job.location)}</p>`;
    if (job.level) reqHtml += `<p><strong>Level:</strong> ${escapeHtml(job.level)}</p>`;
    if (requirements.must_have && requirements.must_have.length > 0) {
        reqHtml += '<p><strong>Key Requirements:</strong></p><ul>';
        requirements.must_have.slice(0, 4).forEach(req => reqHtml += `<li>${escapeHtml(req)}</li>`);
        reqHtml += '</ul>';
    }
    elements.jobRequirements.innerHTML = reqHtml || '<p>Job requirements not available</p>';

    // Tailoring Notes
    const notes = tailoringNotes || {};
    let notesHtml = '';
    if (notes.match_score) {
        notesHtml += `<p><strong>Match:</strong> <span class="match-score">${escapeHtml(notes.match_score)}</span></p>`;
    }
    if (notes.emphasis_areas && notes.emphasis_areas.length > 0) {
        notesHtml += `<p><strong>Emphasized:</strong> ${notes.emphasis_areas.map(e => escapeHtml(e)).join(', ')}</p>`;
    }
    if (notes.keywords_added && notes.keywords_added.length > 0) {
        notesHtml += '<p><strong>Keywords:</strong></p><div class="keywords">';
        notes.keywords_added.forEach(kw => notesHtml += `<span class="keyword">${escapeHtml(kw)}</span>`);
        notesHtml += '</div>';
    }
    elements.tailoringNotes.innerHTML = notesHtml || '<p>CVs tailored for this position</p>';
}

function downloadEnglish() {
    if (state.currentDownloadIdEn) {
        window.location.href = `${API_BASE}/download/${state.currentDownloadIdEn}`;
    }
}

function downloadFrench() {
    if (state.currentDownloadIdFr) {
        window.location.href = `${API_BASE}/download/${state.currentDownloadIdFr}`;
    }
}

// History
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`);
        const data = await response.json();

        if (response.ok && data.applications && data.applications.length > 0) {
            renderHistory(data.applications);
        } else {
            elements.historyList.innerHTML = '<p class="no-history">No applications yet.</p>';
        }
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function renderHistory(applications) {
    let html = '';
    applications.slice().reverse().forEach(app => {
        const salaryText = app.salary_info?.estimated_range
            ? `${app.salary_info.estimated_range.currency || 'EUR'} ${app.salary_info.estimated_range.min?.toLocaleString()} - ${app.salary_info.estimated_range.max?.toLocaleString()}`
            : 'N/A';

        html += `
            <div class="history-item">
                <div class="history-item-info">
                    <h4>${escapeHtml(app.job_title)} at ${escapeHtml(app.company)}</h4>
                    <p>${escapeHtml(app.location || '')} | Salary: ${salaryText}</p>
                    <p>${new Date(app.created_at).toLocaleDateString()}</p>
                    <a href="${escapeHtml(app.job_url)}" target="_blank">${escapeHtml(app.job_url)}</a>
                </div>
                <div class="history-item-actions">
                    <button class="btn btn-primary" onclick="downloadHistoryItem('${app.download_id_en}')">EN</button>
                    <button class="btn btn-french" onclick="downloadHistoryItem('${app.download_id_fr}')">FR</button>
                </div>
            </div>
        `;
    });
    elements.historyList.innerHTML = html;
}

function downloadHistoryItem(downloadId) {
    window.location.href = `${API_BASE}/download/${downloadId}`;
}

// Utilities
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
        if (e.key === 'Enter') tailorCV();
    });

    elements.btnDownloadEn.addEventListener('click', downloadEnglish);
    elements.btnDownloadFr.addEventListener('click', downloadFrench);

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
                'Warning: ANTHROPIC_API_KEY not configured.',
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
    loadHistory();
});
