// --- Global State ---
let currentLogsPage = 1,
  currentUrlsPage = 1,
  latencyChart = null,
  isPulseVisionActive = false,
  pulseVisionData = null,
  isDetailsOpen = false;

// --- Theme Management ---
function initTheme() {
  const theme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  updateThemeToggleIcon(theme);
}

function updateThemeToggleIcon(theme) {
  const toggle = document.getElementById('themeToggle');
  const icon = toggle ? toggle.querySelector('i') : null;
  if (!icon) return;
  if (theme === 'dark') {
    icon.className = 'ri-moon-line';
  } else {
    icon.className = 'ri-sun-line';
  }
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  updateThemeToggleIcon(newTheme);

  if (latencyChart) updateChartTheme(newTheme);
}

function updateChartTheme(theme) {
  if (!latencyChart) return;
  const isDark = theme === 'dark';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
  const tickColor = isDark ? '#94a3b8' : '#64748b';

  latencyChart.options.scales.y.grid.color = gridColor;
  latencyChart.options.scales.x.grid.color = gridColor;
  latencyChart.options.scales.y.ticks.color = tickColor;
  latencyChart.options.scales.x.ticks.color = tickColor;
  latencyChart.update();
}

function calculateEco(latencyMs, statusCode) {
  const baseCO2 = 0.02; // grams
  const latencyFactor = (latencyMs / 1000) * 0.05;
  let totalCO2 = baseCO2 + latencyFactor;
  if (statusCode !== 200) totalCO2 += 0.01;

  return {
    co2: totalCO2.toFixed(3),
    energy: (totalCO2 * 0.4).toFixed(3)
  };
}

// --- SHOW MORE LOGIC ---
function toggleDetails() {
  const details = document.getElementById('moreDetails');
  const btn = document.getElementById('showMoreBtn');
  if (!details || !btn) return;

  const btnText = btn.querySelector('span');
  const icon = btn.querySelector('i');

  isDetailsOpen = !isDetailsOpen;

  if (isDetailsOpen) {
    details.style.display = 'block';
    details.classList.add('open');
    btn.classList.add('active');
    btn.setAttribute('aria-expanded', 'true');
    if (btnText) btnText.textContent = 'SHOW LESS';
    if (icon) icon.className = 'ri-arrow-up-s-line';
  } else {
    details.classList.remove('open');
    details.style.display = 'none';
    btn.classList.remove('active');
    btn.setAttribute('aria-expanded', 'false');
    if (btnText) btnText.textContent = 'SHOW MORE';
    if (icon) icon.className = 'ri-arrow-down-s-line';
  }
}


// --- API Logic ---
async function checkLatency() {
  const url = document.getElementById("urlInput").value.trim();
  const headerName = document.getElementById("headerNameInput").value;
  const headerValue = document.getElementById("headerValueInput").value;
  const button = document.getElementById("checkButton");

  if (!url) {
    showScanError("Missing URL target.");
    return;
  }

  setScanState(true);
  const startTime = Date.now();

  try {
    const response = await fetch("/check_api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, header_name: headerName, header_value: headerValue }),
    });

    if (!response.ok) throw new Error(`Status ${response.status}`);
    const data = await response.json();

    const elapsed = Date.now() - startTime;
    if (elapsed < 600) await new Promise(r => setTimeout(r, 600 - elapsed));

    displayResult(data);
    loadChartData(url);
    loadLastLogs();
    loadUrlsList();

  } catch (error) {
    displayResult({
      error: "Scan Failed: " + error.message,
      status_code: "ERR",
      up: false,
      api_url: url
    });
  } finally {
    setScanState(false);
  }
}


function setScanState(loading) {
  const button = document.getElementById("checkButton");
  const buttonText = button.querySelector("span");
  const icon = button.querySelector("i");

  if (loading) {
    button.disabled = true;
    buttonText.textContent = "SCANNING...";
    icon.className = "ri-loader-4-line ri-spin";
  } else {
    button.disabled = false;
    buttonText.textContent = "SCAN";
    icon.className = "ri-flashlight-fill";
  }
}

function showScanError(msg) {
  const resultHud = document.getElementById("resultHud");
  const result = document.getElementById("result");
  const details = document.getElementById('moreDetails');
  const showMoreBtn = document.getElementById('showMoreBtn');

  isDetailsOpen = false;
  if (details) {
    details.style.display = 'none';
    details.classList.remove('open');
  }
  if (showMoreBtn) {
    showMoreBtn.classList.remove('active');
    showMoreBtn.setAttribute('aria-expanded', 'false');
    const text = showMoreBtn.querySelector('span');
    const icon = showMoreBtn.querySelector('i');
    if (text) text.textContent = 'SHOW MORE';
    if (icon) icon.className = 'ri-arrow-down-s-line';
  }

  resultHud.style.display = "block";
  result.innerHTML = `<div class="result-status-large"><div class="status-icon-box down"><i class="ri-error-warning-line"></i></div><div class="status-text"><h2>Input Required</h2><p>${msg}</p></div></div>`;
}

function displayResult(data) {
  const container = document.getElementById("result");
  const resultHud = document.getElementById("resultHud");
  const isUp = data.up;
  const eco = calculateEco(data.total_latency_ms || 0, data.status_code || 500);

  resultHud.style.display = "block";

  if (data.error) {
    container.innerHTML = `
      <div class="result-status-large">
          <div class="status-icon-box down"><i class="ri-close-circle-line"></i></div>
          <div class="status-text">
              <h2 style="color: var(--danger);">Connection Fault</h2>
              <p>${data.error}</p>
          </div>
      </div>
    `;
    populateDetails(data, true);
    return;
  }

  container.innerHTML = `
    <div class="result-status-large">
        <div class="status-icon-box ${isUp ? 'up' : 'down'}">
            <i class="ri-${isUp ? 'shield-check-line' : 'shield-cross-line'}"></i>
        </div>
        <div class="status-text">
            <h2 style="color: ${isUp ? 'var(--success)' : 'var(--danger)'};">${isUp ? 'Services Operational' : 'Offline'}</h2>
            <p>${data.api_url} • <strong>${data.status_code}</strong></p>
        </div>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-tile">
            <span class="metric-val">${(data.total_latency_ms || 0).toFixed(0)} <small>ms</small></span>
            <span class="metric-label">Total Time</span>
        </div>
        <div class="metric-tile">
            <span class="metric-val">${(data.server_processing_latency_ms || 0).toFixed(0)} <small>ms</small></span>
            <span class="metric-label">Processing</span>
        </div>
        <div class="metric-tile">
            <span class="metric-val">${(data.tcp_latency_ms || 0).toFixed(0)} <small>ms</small></span>
            <span class="metric-label">Transport</span>
        </div>
    </div>
    
    <div class="eco-metrics">
        <div class="eco-badge"><i class="ri-leaf-line"></i> ECO TRACKER</div>
        <div class="eco-val">${eco.co2} gCO₂</div>
        <div class="eco-val" style="opacity:0.6;">${eco.energy} Wh</div>
    </div>
  `;
  populateDetails(data, false);
}

function populateDetails(data, isError) {
  const detailContent = document.getElementById("detailContent");
  const certSection = document.getElementById("certSection");
  const certContent = document.getElementById("certContent");

  const snippet = data.body_snippet || "No response body captured.";
  const type = data.url_type || "Unknown";
  const contentType = data.content_type?.split(';')[0] || 'N/A';

  detailContent.innerHTML = `
    <div class="detail-card">
       <div class="detail-grid-mini">
          <div class="detail-item">
             <small>URL Type</small>
             <strong>${type}</strong>
          </div>
          <div class="detail-item">
             <small>Content Format</small>
             <strong>${contentType}</strong>
          </div>
       </div>
       
       <div class="snippet-header">
          <div class="snippet-title"><i class="ri-code-s-slash-fill"></i> Response Inspector</div>
          <div class="snippet-actions">
             <button class="mini-btn" onclick="copySnippet()"><i class="ri-file-copy-line"></i> COPY</button>
          </div>
       </div>
       <div class="snippet-box">
          <pre id="rawSnippet">${highlightSnippet(beautifySnippet(snippet, contentType))}</pre>
       </div>
    </div>
  `;

  if (data.certificate_details && !data.certificate_details.error) {
    certSection.style.display = 'block';
    const cert = data.certificate_details;
    certContent.innerHTML = `
      <div class="detail-card">
         <div class="cert-grid">
            <div class="cert-row"><strong>Issuer</strong> <span>${cert.issuer || 'Unknown'}</span></div>
            <div class="cert-row"><strong>Valid Until</strong> <span>${new Date(cert.valid_until).toLocaleDateString()}</span></div>
            <div class="cert-row"><strong>Cipher Suite</strong> <span style="font-family: monospace; font-size: 0.75rem;">${cert.cipher || 'N/A'}</span></div>
         </div>
      </div>
    `;
  } else {
    certSection.style.display = 'none';
  }
}

function beautifySnippet(text, type) {
  if (!text) return "";
  try {
    if (type.includes('json') || text.trim().startsWith('{') || text.trim().startsWith('[')) {
      return JSON.stringify(JSON.parse(text), null, 2);
    }
    if (type.includes('html') || text.trim().startsWith('<!')) {
      // Minimal HTML indent logic
      let indent = 0;
      return text.replace(/(<[^>]+>)/g, (match) => {
        if (match.startsWith('</')) indent--;
        const line = '  '.repeat(Math.max(0, indent)) + match;
        if (!match.startsWith('</') && !match.endsWith('/>') && !['<br>', '<hr>', '<img>'].some(s => match.startsWith(s))) indent++;
        return '\n' + line;
      }).trim();
    }
  } catch (e) { }
  return text;
}

function highlightSnippet(text) {
  if (!text) return "";
  return escapeHtml(text)
    .replace(/(&lt;\/?[a-z1-6]+(?:\s+[^&]+)?&gt;)/gi, '<span class="tok-tag">$1</span>')
    .replace(/(\"[^\"]+\"):?/g, (m) => m.endsWith(':') ? `<span class="tok-key">${m}</span>` : `<span class="tok-val">${m}</span>`)
    .replace(/(\b\d+\b)/g, '<span class="tok-num">$1</span>');
}

window.copySnippet = () => {
  const text = document.getElementById('rawSnippet').textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.querySelector('.mini-btn');
    const original = btn.innerHTML;
    btn.innerHTML = '<i class="ri-check-line"></i> COPIED';
    setTimeout(() => btn.innerHTML = original, 2000);
  });
};

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function loadLastLogs(page = 1) {
  try {
    const response = await fetch(`/last_logs?page=${page}`);
    const data = await response.json();
    renderLogs(data.logs);
    renderPagination("logs-pagination", data.total_pages, data.current_page, loadLastLogs);
  } catch (err) { }
}

function renderLogs(logs) {
  const container = document.getElementById("logs-body");
  if (!logs || logs.length === 0) {
    container.innerHTML = `<tr><td style="padding:1rem; text-align:center; color: var(--text-dim);">No recent activity.</td></tr>`;
    return;
  }
  container.innerHTML = logs.map(log => {
    const statusClass = log.up ? "success" : "error";
    const timeStr = new Date(log.timestamp).toLocaleTimeString([], { hour12: false });
    return `
      <tr class="log-entry" onclick="setScanUrl('${log.api_url}')">
        <td>
            <span class="log-badge ${statusClass}">${log.status_code || "ERR"}</span>
            <span class="log-url">${log.api_url.split('//')[1]}</span>
            <span class="log-time">${timeStr}</span>
        </td>
      </tr>`;
  }).join("");
}

async function loadUrlsList(page = 1) {
  try {
    const response = await fetch(`/monitored_urls?page=${page}`);
    const data = await response.json();
    renderUrlsList(data.urls_data || []);
  } catch (err) { }
}

function renderUrlsList(urls) {
  const container = document.getElementById("urls-list");
  if (!urls || urls.length === 0) {
    container.innerHTML = `<p style="text-align:center; padding: 2rem; color: var(--text-dim); font-style: italic;">No active nodes.</p>`;
    return;
  }
  container.innerHTML = urls.map(u => `
    <div class="url-card" onclick="setScanUrl('${u.api_url}')">
      <div class="url-link">${u.api_url.split('//')[1]}</div>
      <div class="url-meta">
        <span style="color: ${u.up ? 'var(--success)' : 'var(--danger)'}">● ${u.up ? 'Online' : 'Offline'}</span>
        <span style="float:right;">${(u.total_latency_ms || 0).toFixed(0)}ms</span>
      </div>
    </div>
  `).join("");
}

function setScanUrl(url) {
  document.getElementById("urlInput").value = url;
  checkLatency();
}

function renderPagination(id, total, current, cb) {
  const el = document.getElementById(id);
  if (!el || total <= 1) { el.innerHTML = ""; return; }
  el.innerHTML = `
    <button ${current === 1 ? 'disabled' : ''} onclick="window.goPage('${id}', ${current - 1})"><i class="ri-arrow-left-s-line"></i></button>
    <span>${current}/${total}</span>
    <button ${current === total ? 'disabled' : ''} onclick="window.goPage('${id}', ${current + 1})"><i class="ri-arrow-right-s-line"></i></button>
  `;
  window.goPage = (id, page) => cb(page);
}

async function loadChartData(url) {
  try {
    const response = await fetch(`/chart_data?url=${encodeURIComponent(url)}`);
    const data = await response.json();
    renderChart(data.labels, data.data);
  } catch (err) { }
}

function renderChart(labels, data) {
  const ctx = document.getElementById("latencyChart").getContext("2d");
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

  if (latencyChart) latencyChart.destroy();

  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
  gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');

  latencyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Latency",
        data,
        borderColor: "#6366f1",
        backgroundColor: gradient,
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: "#10b981",
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { display: false },
        y: {
          grid: { color: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' },
          ticks: { color: isDark ? '#64748b' : '#94a3b8' }
        }
      }
    }
  });
}

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  loadLastLogs();
  loadUrlsList();

  const checkButton = document.getElementById("checkButton");
  const urlInput = document.getElementById("urlInput");
  const themeToggle = document.getElementById("themeToggle");
  const showMoreBtn = document.getElementById("showMoreBtn");

  if (checkButton) checkButton.addEventListener("click", checkLatency);
  if (urlInput) urlInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") checkLatency();
  });
  if (themeToggle) themeToggle.addEventListener("click", toggleTheme);
  if (showMoreBtn) {
    showMoreBtn.setAttribute('aria-expanded', 'false');
    showMoreBtn.addEventListener("click", toggleDetails);
  }
});
