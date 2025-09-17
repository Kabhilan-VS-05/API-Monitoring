document.addEventListener('DOMContentLoaded', () => {
    // --- Element Refs ---
    const mainView = document.getElementById('mainView'),
          detailsView = document.getElementById('detailsView'),
          monitorListDiv = document.getElementById('monitorList'),
          addApiModal = document.getElementById('addApiModal'),
          reportModal = document.getElementById('reportModal'),
          addApiForm = document.getElementById('addApiForm'),
          addApiBtn = document.getElementById('addApiBtn'),
          cancelBtn = document.getElementById('cancelBtn'),
          modalTitle = document.getElementById('modalTitle'),
          modalSubmitBtn = document.getElementById('modalSubmitBtn'),
          apiEditId = document.getElementById('apiEditId'),
          tooltip = document.getElementById('tooltip');
    let detailChart = null;

    // --- Core Functions ---
    async function fetchMonitors() {
        try {
            const response = await fetch(`/api/advanced/monitors?_=${new Date().getTime()}`);
            const monitors = await response.json();
            renderMonitorList(monitors);
        } catch (error) {
            monitorListDiv.innerHTML = '<p class="placeholder">Failed to load monitors.</p>';
        }
    }

    async function handleFormSubmit(e) {
        e.preventDefault();
        const editId = apiEditId.value;
        const payload = {
            url: document.getElementById('apiUrl').value,
            category: document.getElementById('apiCategory').value,
            header_name: document.getElementById('apiHeaderName').value,
            header_value: document.getElementById('apiHeaderValue').value,
            notification_email: document.getElementById('apiEmail').value,
            frequency: parseInt(document.getElementById('apiFrequency').value, 10)
        };
        let url = '/api/advanced/add_monitor';
        if (editId) {
            url = '/api/advanced/update_monitor';
            payload.id = parseInt(editId, 10);
        }
        const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if (response.ok) { closeModal('addApiModal'); fetchMonitors(); }
        else { const error = await response.json(); alert(`Error: ${error.error}`); }
    }
    
    async function deleteMonitor(id) {
        if (!confirm("Are you sure you want to delete this monitor?")) return;
        await fetch('/api/advanced/delete_monitor', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
        fetchMonitors();
    }

    async function showDetails(monitor, page = 1) {
        mainView.classList.add('hidden');
        detailsView.classList.remove('hidden');
        detailsView.innerHTML = `
            <a href="#" id="backBtn" class="back-button"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>Back to Status List</a>
            <div class="details-header"><div><h2 style="word-break: break-all;">${monitor.url}</h2><p style="color: #6B7280;"><strong>Category:</strong> ${monitor.category || 'N/A'}</p></div></div>
            <h3>24-Hour Uptime</h3>
            <div class="daily-history-bar"><div class="daily-history-bar-inner" id="dailyHistoryBar"></div></div>
            <div style="height: 300px; margin-bottom: 2rem;"><canvas id="detailChartCanvas"></canvas></div>
            <div class="history-log-section" id="historyLogSection"></div>
            <div id="historyPagination" class="pagination-controls"></div>
        `;
        document.getElementById('backBtn').addEventListener('click', showMainView);
        fetchHistory(monitor, page);
        renderDailyHistoryBar(monitor.id);
    }
    
    async function fetchHistory(monitor, page = 1) {
        const response = await fetch(`/api/advanced/history?id=${monitor.id}&page=${page}`);
        const data = await response.json();
        renderHistoryLog(data.history);
        renderPagination('historyPagination', data.current_page, data.total_pages, (newPage) => fetchHistory(monitor, newPage));
        renderDetailChart(data.history);
    }

    async function showLogReport(logId) {
        const response = await fetch(`/api/advanced/log_details/${logId}`);
        const log = await response.json();
        let reportHtml = `<h3>Report for ${new Date(log.timestamp).toLocaleString()}</h3>`;
        if (log.is_up) {
            reportHtml += `<p>Status: <span class="status status-Up">Up</span> (${log.status_code})</p><h4>Latency Breakdown:</h4><ul>
                <li><strong>Total:</strong> ${log.total_latency_ms} ms</li><li>DNS Lookup: ${log.dns_lookup_ms} ms</li><li>TCP Connection: ${log.tcp_connection_ms} ms</li>
                <li>TLS Handshake: ${log.tls_handshake_ms} ms</li><li>Server Processing: ${log.server_processing_ms} ms</li><li>Content Download: ${log.content_download_ms} ms</li></ul>`;
        } else {
            reportHtml += `<p>Status: <span class="status status-Down">Down/Error</span></p><h4>Error Details:</h4><div class="error-message">${log.error_message || 'N/A'}</div>`;
        }
        reportHtml += '<div class="modal-actions"><button type="button" class="button-secondary" id="closeReportBtn">Close</button></div>';
        document.getElementById('reportModalContent').innerHTML = reportHtml;
        openModal('reportModal');
        document.getElementById('closeReportBtn').addEventListener('click', () => closeModal('reportModal'));
    }

    async function renderMonitorList(monitors) {
        if (monitors.length === 0) { monitorListDiv.innerHTML = '<p class="placeholder">No APIs are being monitored yet.</p>'; return; }
        monitorListDiv.innerHTML = '';
        for (const m of monitors) {
            const item = document.createElement('div');
            item.className = 'monitor-item';
            item.dataset.monitor = JSON.stringify(m);
            item.innerHTML = `
                <div class="monitor-item-info"><strong>${m.url}</strong><small>${m.category || 'No Category'}</small></div>
                <div class="monitor-item-right">
                    <div class="sparkline-container" id="sparkline-${m.id}"></div>
                    <span class="status status-${m.last_status}">${m.last_status}</span>
                    <div class="monitor-item-actions">
                        <button class="action-btn edit-btn" title="Edit"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" /><path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" /></svg></button>
                        <button class="action-btn delete-btn" title="Delete"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg></button>
                    </div>
                </div>`;
            monitorListDiv.appendChild(item);
            renderSparkline(m.id);
        }
    }
    
    function renderHistoryLog(logs) {
        const container = document.getElementById('historyLogSection');
        if (!logs || logs.length === 0) {
            container.innerHTML = '<p class="placeholder">No history found for this period.</p>';
            return;
        }
        
        container.innerHTML = `
            <table class="history-log-table">
                <thead><tr><th>Timestamp</th><th>Status</th><th>Latency</th><th></th></tr></thead>
                <tbody>
                    ${logs.map(log => `
                        <tr>
                            <td>${new Date(log.timestamp).toLocaleString()}</td>
                            <td><span class="status status-${log.is_up ? 'Up' : (log.error_message ? 'Error' : 'Down')}">${log.is_up ? 'Operational' : (log.error_message ? 'Error' : 'Outage')}</span></td>
                            <td>${log.total_latency_ms ? log.total_latency_ms + ' ms' : 'N/A'}</td>
                            <td><button class="report-btn" data-log-id="${log.id}">See Report</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    function openModal(modalId) { document.getElementById(modalId).classList.remove('hidden'); }
    function closeModal(modalId) { document.getElementById(modalId).classList.add('hidden'); }
    function showMainView() { detailsView.classList.add('hidden'); mainView.classList.remove('hidden'); }
    
    function setupInitialEventListeners() {
        addApiBtn.addEventListener('click', () => { resetForm(); openModal('addApiModal'); });
        cancelBtn.addEventListener('click', () => closeModal('addApiModal'));
        addApiForm.addEventListener('submit', handleFormSubmit);

        monitorListDiv.addEventListener('click', (e) => {
            const item = e.target.closest('.monitor-item');
            if (!item) return;
            const monitorData = JSON.parse(item.dataset.monitor);

            if (e.target.closest('.edit-btn')) {
                openEditModal(monitorData);
            } else if (e.target.closest('.delete-btn')) {
                deleteMonitor(monitorData.id);
            } else if (e.target.closest('.monitor-item-info')) {
                showDetails(monitorData);
            }
        });

        detailsView.addEventListener('click', (e) => {
            if (e.target.classList.contains('report-btn')) {
                showLogReport(e.target.dataset.logId);
            }
        });
        
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal(modal.id);
                }
            });
        });
    }

    function openEditModal(monitor) {
        document.getElementById('modalTitle').textContent = 'Edit Monitor';
        document.getElementById('modalSubmitBtn').textContent = 'Save Changes';
        document.getElementById('apiEditId').value = monitor.id;
        document.getElementById('apiUrl').value = monitor.url;
        document.getElementById('apiCategory').value = monitor.category || '';
        document.getElementById('apiHeaderName').value = monitor.header_name || '';
        document.getElementById('apiHeaderValue').value = monitor.header_value || '';
        document.getElementById('apiEmail').value = monitor.notification_email || '';
        document.getElementById('apiFrequency').value = monitor.check_frequency_minutes;
        openModal('addApiModal');
    }

    function resetForm() {
        addApiForm.reset();
        document.getElementById('modalTitle').textContent = 'Add New API to Monitor';
        document.getElementById('modalSubmitBtn').textContent = 'Add Monitor';
        document.getElementById('apiEditId').value = '';
    }

    async function renderSparkline(apiId) {
        const container = document.getElementById(`sparkline-${apiId}`);
        const response = await fetch(`/api/advanced/daily_summary?id=${apiId}`);
        const data = await response.json();
        if (data.length === 0) return;
        new Chart(container, {
            type: 'line',
            data: {
                labels: data.map(d => d.timestamp),
                datasets: [{
                    data: data.map(d => d.total_latency_ms || 0),
                    borderColor: '#4f46e5',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { x: { display: false }, y: { display: false, beginAtZero: true } },
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                animation: false
            }
        });
    }
    
    async function renderDailyHistoryBar(apiId) {
        const container = document.getElementById('dailyHistoryBar');
        const response = await fetch(`/api/advanced/daily_summary?id=${apiId}`);
        const data = await response.json();
        if (data.length === 0) return;
        container.innerHTML = data.map(log => {
            const color = log.is_up ? 'var(--status-up)' : (log.error_message ? 'var(--status-error)' : 'var(--status-down)');
            const status = log.is_up ? 'Up' : (log.error_message ? 'Error' : 'Down');
            const title = `${new Date(log.timestamp).toLocaleString()}: ${status} (${log.total_latency_ms || 'N/A'})`;
            return `<div class="history-bar-segment" style="background-color: ${color};" title="${title}"></div>`;
        }).join('');
    }
    
    function renderPagination(elementId, currentPage, totalPages, clickHandler) {
        const container = document.getElementById(elementId);
        if (!container || totalPages <= 1) {
            if (container) container.innerHTML = '';
            return;
        }
        let html = '';
        for (let i = 1; i <= totalPages; i++) {
            html += `<button class="${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        container.innerHTML = html;
        container.querySelectorAll('button').forEach(button => {
            button.addEventListener('click', (e) => {
                clickHandler(parseInt(e.target.dataset.page, 10));
            });
        });
    }
    
    function renderDetailChart(history) {
        const ctx = document.getElementById('detailChartCanvas');
        if (!ctx) return;
        const reversedHistory = [...history].reverse();
        if (detailChart) detailChart.destroy();
        detailChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: reversedHistory.map(h => new Date(h.timestamp).toLocaleString()),
                datasets: [{
                    label: 'Latency (ms)',
                    data: reversedHistory.map(h => h.total_latency_ms || 0),
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    fill: true,
                    tension: 0.2,
                    pointBackgroundColor: reversedHistory.map(h => h.is_up ? '#4f46e5' : (h.error_message ? '#8B5CF6' : '#EF4444')),
                    pointBorderColor: reversedHistory.map(h => h.is_up ? '#4f46e5' : (h.error_message ? '#8B5CF6' : '#EF4444')),
                    pointRadius: reversedHistory.map(h => h.is_up ? 3 : 5),
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: { beginAtZero: true, ticks: { color: '#6B7280' }, grid: { color: '#E5E7EB' }},
                  x: { ticks: { color: '#6B7280', maxRotation: 45, minRotation: 45 }, grid: { display: false } }
                },
                plugins: { legend: { labels: { color: '#111827' }}}
            }
        });
    }

    // --- Init ---
    setupInitialEventListeners();
    fetchMonitors();
});