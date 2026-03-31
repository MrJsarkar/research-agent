/* ═══════════════════════════════════════════════════════
   AUTONOMOUS RESEARCH AGENT — MAIN.JS
   ═══════════════════════════════════════════════════════ */

'use strict';

// ── Grid canvas background ────────────────────────────────
(function drawGrid() {
    const canvas = document.getElementById('grid-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 0.5;
        const gap = 50;
        for (let x = 0; x < canvas.width; x += gap) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += gap) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
        }
    }
    resize();
    window.addEventListener('resize', resize);
})();

// ── State ─────────────────────────────────────────────────
let researchId        = null;
let eventSource       = null;
let rawReportMarkdown = '';
let allSources        = [];

// ── DOM Refs ──────────────────────────────────────────────
const topicInput    = document.getElementById('topic-input');
const dropZone      = document.getElementById('drop-zone');
const fileUpload    = document.getElementById('file-upload');
const btnStart      = document.getElementById('btn-start');
const btnText       = document.getElementById('btn-text');
const btnReset      = document.getElementById('btn-reset');

const progressSummary = document.getElementById('progress-summary');
const progressFill    = document.getElementById('progress-fill');
const progressLabel   = document.getElementById('progress-label');

const phasePlan       = document.getElementById('phase-plan');
const phaseSearch     = document.getElementById('phase-search');
const phaseSynth      = document.getElementById('phase-synthesise');
const phaseReport     = document.getElementById('phase-report');

const statusDot  = document.querySelector('.status-dot');
const statusText = document.getElementById('status-text');

const eventStream   = document.getElementById('event-stream');
const streamEmpty   = document.getElementById('stream-empty');

const tabStream     = document.getElementById('tab-stream');
const tabReport     = document.getElementById('tab-report');
const tabSources    = document.getElementById('tab-sources');
const streamView    = document.getElementById('stream-view');
const reportView    = document.getElementById('report-view');
const sourcesView   = document.getElementById('sources-view');

const reportEmpty   = document.getElementById('report-empty');
const reportToolbar = document.getElementById('report-toolbar');
const reportContent = document.getElementById('report-content');
const reportBadge   = document.getElementById('report-badge');
const sourcesBadge  = document.getElementById('sources-badge');

const sourcesEmpty  = document.getElementById('sources-empty');
const sourcesList   = document.getElementById('sources-list');

const btnCopy       = document.getElementById('btn-copy-report');
const btnDownload   = document.getElementById('btn-download-report');

// ── Tab switching ─────────────────────────────────────────
function switchTab(tab) {
    [tabStream, tabReport, tabSources].forEach(t => t.classList.remove('active'));
    [streamView, reportView, sourcesView].forEach(v => v.classList.add('hidden'));
    tab.classList.add('active');
    const target = document.getElementById(tab.dataset.target);
    if (target) target.classList.remove('hidden');
}
tabStream.addEventListener('click', () => switchTab(tabStream));
tabReport.addEventListener('click', () => { switchTab(tabReport); reportBadge.classList.add('hidden'); });
tabSources.addEventListener('click', () => switchTab(tabSources));

// ── Example pills ─────────────────────────────────────────
document.querySelectorAll('.pill').forEach(pill => {
    pill.addEventListener('click', () => {
        topicInput.value = pill.dataset.q;
        topicInput.focus();
    });
});

// ── File upload ───────────────────────────────────────────
dropZone.addEventListener('click', (e) => {
    if (e.target !== topicInput) fileUpload.click();
});
fileUpload.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFileUpload(e.target.files[0]);
});
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]);
});

async function handleFileUpload(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'txt', 'md'].includes(ext)) {
        alert('Unsupported format. Please upload PDF, MD, or TXT.');
        return;
    }
    topicInput.value = 'Extracting text from document…';
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await fetch('/api/research/parse_file', { method: 'POST', body: formData });
        const data = await res.json();
        topicInput.value = data.parsed_text || '';
    } catch {
        topicInput.value = '';
        alert('Failed to parse document. Please paste the text manually.');
    }
}

// ── Phase Tracker ─────────────────────────────────────────
const PHASE_PROGRESS = { plan: 10, search: 55, synthesise: 80, report: 95, done: 100 };

function setPhase(type) {
    const map = {
        plan:       [phasePlan],
        search:     [phasePlan, phaseSearch],
        synthesise: [phasePlan, phaseSearch, phaseSynth],
        report:     [phasePlan, phaseSearch, phaseSynth, phaseReport],
        done:       [phasePlan, phaseSearch, phaseSynth, phaseReport],
    };
    const allPhases = [phasePlan, phaseSearch, phaseSynth, phaseReport];
    allPhases.forEach(p => { p.classList.remove('active', 'complete'); });
    const active = map[type] || [];
    active.forEach((p, i) => {
        if (i < active.length - 1 || type === 'done') p.classList.add('complete');
        else p.classList.add('active');
    });
    const pct = PHASE_PROGRESS[type] ?? 0;
    progressFill.style.width = pct + '%';
    progressLabel.textContent = {
        plan:       'Planning research…',
        search:     'Searching the web…',
        synthesise: 'Synthesising findings…',
        report:     'Writing final report…',
        done:       'Research complete!',
        error:      'An error occurred.',
    }[type] || 'Working…';
}

// ── Markdown-safe render for event messages ───────────────
function formatMessage(msg) {
    return msg
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// ── Append event card ─────────────────────────────────────
const ICONS = {
    plan:       '🧠',
    search:     '🔍',
    synthesise: '⚗️',
    report:     '📝',
    done:       '🎉',
    error:      '❌',
};

function appendEvent(type, message, data) {
    if (streamEmpty) streamEmpty.style.display = 'none';

    const card = document.createElement('div');
    card.className = `event-card type-${type}`;

    const timeStr = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    let extra = '';
    // Show sub-questions list on plan complete
    if (type === 'plan' && Array.isArray(data)) {
        extra = `<div class="sub-q-list">${data.map(q => `<div class="sub-q-item">${q}</div>`).join('')}</div>`;
    }

    card.innerHTML = `
        <div class="event-icon">${ICONS[type] || '•'}</div>
        <div class="event-body">
            <div class="event-message">${formatMessage(message)}</div>
            ${extra}
            <div class="event-time">${timeStr}</div>
        </div>
    `;
    eventStream.appendChild(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

// ── Render report ─────────────────────────────────────────
function renderReport(markdown) {
    rawReportMarkdown = markdown;
    reportEmpty.classList.add('hidden');
    reportToolbar.classList.remove('hidden');

    // Configure marked
    marked.setOptions({ breaks: true, gfm: true });
    reportContent.innerHTML = marked.parse(markdown);

    // Signal the tab
    reportBadge.classList.remove('hidden');
    reportBadge.classList.add('report-ready');
    reportBadge.textContent = '●';
}

// ── Render sources ────────────────────────────────────────
function renderSources(sources) {
    if (!sources || sources.length === 0) return;
    sourcesEmpty.classList.add('hidden');
    sourcesBadge.classList.remove('hidden');
    sourcesBadge.textContent = sources.length;

    sourcesList.innerHTML = '';
    sources.forEach(s => {
        const a = document.createElement('a');
        a.className = 'source-card';
        a.href = s.url ? `https://${s.url}` : '#';
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.innerHTML = `
            <div class="source-title">${s.title || 'Source'}</div>
            <div class="source-snippet">${s.snippet || ''}</div>
            ${s.url ? `<div class="source-url">${s.url}</div>` : ''}
        `;
        sourcesList.appendChild(a);
    });
}

// ── Status helpers ────────────────────────────────────────
function setStatus(state, text) {
    statusDot.className = 'status-dot' + (state ? ` ${state}` : '');
    statusText.textContent = text;
}

// ── Start Research ────────────────────────────────────────
btnStart.addEventListener('click', async () => {
    const topic = topicInput.value.trim();
    if (!topic) {
        topicInput.focus();
        topicInput.style.borderColor = 'var(--accent-red)';
        setTimeout(() => topicInput.style.borderColor = '', 1200);
        return;
    }

    // Reset UI
    eventStream.innerHTML = '';
    streamEmpty.style.display = 'none';
    reportContent.innerHTML = '';
    reportEmpty.classList.remove('hidden');
    reportToolbar.classList.add('hidden');
    reportBadge.classList.add('hidden');
    sourcesList.innerHTML = '';
    sourcesEmpty.classList.remove('hidden');
    sourcesBadge.classList.add('hidden');
    rawReportMarkdown = '';
    allSources = [];
    switchTab(tabStream);

    btnStart.disabled = true;
    btnText.textContent = 'Starting…';
    progressSummary.classList.remove('hidden');
    btnReset.classList.add('hidden');
    progressFill.style.width = '3%';
    setStatus('running', 'Researching…');

    try {
        const res = await fetch('/api/research/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic }),
        });
        if (!res.ok) throw new Error(await res.text());
        const { research_id } = await res.json();
        researchId = research_id;
        btnText.textContent = 'Researching…';
        openStream(research_id);
    } catch (err) {
        btnText.textContent = 'Start Research';
        btnStart.disabled = false;
        setStatus('error', 'Error');
        appendEvent('error', `Failed to start: ${err.message}`);
    }
});

// ── Open SSE Stream ───────────────────────────────────────
function openStream(id) {
    if (eventSource) { eventSource.close(); eventSource = null; }

    eventSource = new EventSource(`/api/research/${id}/stream`);

    const handleEvent = (type) => (e) => {
        try {
            const payload = JSON.parse(e.data);
            setPhase(type);
            appendEvent(type, payload.message, payload.data);

            // If plan complete, show sub-questions
            if (type === 'plan' && Array.isArray(payload.data)) {
                /* already handled in appendEvent */
            }

            // When done: fetch report + sources
            if (type === 'done') {
                fetchReport(id);
                setStatus('', 'Complete');
                btnStart.disabled = false;
                btnText.textContent = 'Start Research';
                btnReset.classList.remove('hidden');
                eventSource.close();
            }

            if (type === 'error') {
                setStatus('error', 'Error');
                btnStart.disabled = false;
                btnText.textContent = 'Retry';
                btnReset.classList.remove('hidden');
                eventSource.close();
            }
        } catch (_) { /* ignore parse errors */ }
    };

    ['plan', 'search', 'synthesise', 'report', 'done', 'error'].forEach(t => {
        eventSource.addEventListener(t, handleEvent(t));
    });

    eventSource.addEventListener('close', () => eventSource.close());

    eventSource.onerror = () => {
        if (eventSource.readyState === EventSource.CLOSED) return;
        setStatus('error', 'Stream error');
        btnStart.disabled = false;
        btnText.textContent = 'Retry';
        appendEvent('error', 'Connection to agent lost. Please try again.');
        eventSource.close();
    };
}

// ── Fetch completed report ────────────────────────────────
async function fetchReport(id) {
    try {
        const res = await fetch(`/api/research/${id}/report`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.report) renderReport(data.report);
        if (data.sources) renderSources(data.sources);
    } catch { /* silent */ }
}

// ── Copy / Download ───────────────────────────────────────
btnCopy.addEventListener('click', async () => {
    if (!rawReportMarkdown) return;
    await navigator.clipboard.writeText(rawReportMarkdown);
    btnCopy.textContent = '✓ Copied!';
    setTimeout(() => (btnCopy.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy Markdown`), 2000);
});

btnDownload.addEventListener('click', () => {
    if (!rawReportMarkdown) return;
    const blob = new Blob([rawReportMarkdown], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `research-report-${Date.now()}.md`;
    a.click();
});

// ── Reset ─────────────────────────────────────────────────
btnReset.addEventListener('click', () => {
    topicInput.value = '';
    topicInput.disabled = false;
    progressSummary.classList.add('hidden');
    btnReset.classList.add('hidden');
    btnStart.disabled = false;
    btnText.textContent = 'Start Research';
    progressFill.style.width = '0%';
    [phasePlan, phaseSearch, phaseSynth, phaseReport].forEach(p => p.classList.remove('active', 'complete'));
    eventStream.innerHTML = '';
    streamEmpty.style.display = '';
    reportContent.innerHTML = '';
    reportEmpty.classList.remove('hidden');
    reportToolbar.classList.add('hidden');
    reportBadge.classList.add('hidden');
    sourcesList.innerHTML = '';
    sourcesEmpty.classList.remove('hidden');
    sourcesBadge.classList.add('hidden');
    setStatus('', 'Ready');
    switchTab(tabStream);
    if (eventSource) { eventSource.close(); eventSource = null; }
    researchId = null;
    rawReportMarkdown = '';
    allSources = [];
});
