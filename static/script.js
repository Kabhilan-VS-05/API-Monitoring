// --- Global State ---
let currentLogsPage = 1, currentUrlsPage = 1, latencyChart = null;

// --- Main Functions ---
async function checkLatency(urlFromClick = null) {
  const url = urlFromClick || document.getElementById("urlInput").value;
  if (!url) { alert("Please enter an API URL"); return; }
  const checkButton = document.getElementById("checkButton"), headerName = document.getElementById("headerNameInput").value, headerValue = document.getElementById("headerValueInput").value;
  checkButton.disabled = true; checkButton.classList.add('loading');
  document.getElementById('result').innerHTML = `<p class="placeholder">Running check...</p>`;
  try {
    const response = await fetch(`/check_api`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_url: url, header_name: headerName, header_value: headerValue })
    });
    const data = await response.json();
    renderResult(data);
    updateChart(url);
    loadLastLogs();
    loadUrlsList();
  } catch (err) {
    document.getElementById('result').innerHTML = `<span style="color:red">Error: ${err}</span>`;
  } finally {
    checkButton.disabled = false;
    checkButton.classList.remove('loading');
  }
}

async function updateChart(url) {
  try {
    const response = await fetch(`/chart_data?url=${encodeURIComponent(url)}`);
    const chartData = await response.json();
    const ctx = document.getElementById('latencyChart').getContext('2d');
    if (latencyChart) { latencyChart.destroy(); }
    latencyChart = new Chart(ctx, {
      type: 'line', data: { labels: chartData.labels, datasets: [{
          label: 'Total Latency (ms)', data: chartData.data, borderColor: 'rgba(0, 123, 255, 1)',
          backgroundColor: 'rgba(0, 123, 255, 0.1)', borderWidth: 2, pointBackgroundColor: 'rgba(0, 123, 255, 1)',
          tension: 0.4, fill: true
      }]},
      options: { responsive: true, maintainAspectRatio: false, scales: {
          y: { beginAtZero: true },
          x: { ticks: { maxRotation: 45, minRotation: 45 } }
      }}
    });
  } catch (error) { console.error("Failed to update chart:", error); }
}

function loadUrlsList() {
  fetch(`/monitored_urls`).then(res => res.json()).then(data => {
      const listElement = document.getElementById("urls-list");
      if (data.error || !data.urls_data || data.urls_data.length === 0) {
        listElement.innerHTML = `<span class="placeholder">No URLs monitored yet.</span>`;
        return;
      }
      let html = "";
      data.urls_data.forEach(log => {
        html += `<span class="url-tag" data-url="${log.api_url}" data-header-name="${log.header_name || ''}" data-header-value="${log.header_value || ''}">${log.api_url}</span>`;
      });
      listElement.innerHTML = html;
    });
}

function loadLastLogs(page = 1) {
  currentLogsPage = page;
  fetch(`/last_logs?page=${page}&per_page=10`).then(res => res.json()).then(data => {
      const logsDiv = document.getElementById("logs");
      if (data.error || !data.logs || data.logs.length === 0) {
        logsDiv.innerHTML = `<span class="placeholder">No logs yet.</span>`;
        document.getElementById("logs-pagination").innerHTML = ''; return;
      }
      let html = `<div class="logs-container"><table class="log-table"><thead><tr><th>API/URL</th><th>Status</th><th>Health</th><th>Response Time (ms)</th></tr></thead><tbody>`;
      data.logs.forEach(log => {
        const statusColor = log.up ? 'status-up' : 'status-down';
        html += `<tr class="log-row" data-url="${log.api_url}" data-header-name="${log.header_name || ''}" data-header-value="${log.header_value || ''}"><td>${log.api_url}</td><td><b class="${statusColor}">${log.up ? 'Up' : 'Down'}</b> (${log.status_code})</td><td>${getHealthDiagnosis(log)}</td><td>${log.total_latency_ms}</td></tr>`;
      });
      html += `</tbody></table></div>`;
      logsDiv.innerHTML = html;
      renderPagination('logs-pagination', data.current_page, data.total_pages, 'loadLastLogs');
    });
}

// --- UI Rendering Helpers ---
function renderPagination(elementId, currentPage, totalPages, clickHandlerName) {
  const container = document.getElementById(elementId);
  if (totalPages <= 1) { container.innerHTML = ''; return; }
  let html = `<button onclick="${clickHandlerName}(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>«</button>`;
  for (let i = 1; i <= totalPages; i++) { html += `<button onclick="${clickHandlerName}(${i})" class="${i === currentPage ? 'active' : ''}">${i}</button>`; }
  html += `<button onclick="${clickHandlerName}(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>»</button>`;
  container.innerHTML = html;
}

function renderResult(data) {
  const resultDiv = document.getElementById("result");
  if (data.error) { resultDiv.innerHTML = `<span style="color:red">${data.error}</span>`; return; }
  const statusColor = data.up ? 'status-up' : 'status-down';
  let diagnosisHtml = data.diagnosis ? `<tr><td><b>Diagnosis</b></td><td>${data.diagnosis}</td></tr>` : '';
  const urlTypeHtml = `<tr><td><b>URL Type</b></td><td>${data.url_type || 'N/A'}</td></tr>`;
  resultDiv.innerHTML = `<h2>Last Check: ${data.api_url}</h2><table class="data-table"><tr><td>Status</td><td><b class="${statusColor}">${data.up ? 'Up' : 'Down'}</b> (${data.status_code})</td></tr>${urlTypeHtml}<tr><td>Total Latency</td><td><b>${data.total_latency_ms} ms</b></td></tr><tr><td>DNS / TCP / TLS</td><td>${data.dns_lookup_ms} / ${data.tcp_connection_ms} / ${data.tls_handshake_ms} ms</td></tr><tr><td>Server / Download</td><td>${data.server_processing_ms} / ${data.content_download_ms} ms</td></tr>${diagnosisHtml}</table>`;
}

function getHealthDiagnosis(log) {
    const latency = log.total_latency_ms;
    const type = log.url_type;
    const thresholds = { 'API': { good: 500, fair: 1200 }, 'Other': { good: 1000, fair: 2500 } };
    const activeThresholds = thresholds[type] || thresholds['Other'];
    if (latency < activeThresholds.good) { return '<span class="traffic-low">Good</span>'; } 
    else if (latency < activeThresholds.fair) { return '<span class="traffic-medium">Fair</span>'; } 
    else { return '<span class="traffic-high">Poor</span>'; }
}

// --- Event Listeners ---
document.addEventListener('click', function(event) {
  const clickableTarget = event.target.closest('.url-tag, .log-row');
  if (clickableTarget) {
    const url = clickableTarget.dataset.url, headerName = clickableTarget.dataset.headerName, headerValue = clickableTarget.dataset.headerValue;
    if (url) {
      document.getElementById('urlInput').value = url;
      document.getElementById('headerNameInput').value = headerName || '';
      document.getElementById('headerValueInput').value = headerValue || '';
      checkLatency(url);
    }
  }
});

// --- Initial Load ---
window.onload = function () {
  loadLastLogs();
  loadUrlsList();
};