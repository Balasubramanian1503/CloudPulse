const cpuHistory = [];
const labels = [];
let chart;

function initChart() {
  const ctx = document.getElementById("cpuChart");
  chart = new Chart(ctx, {
    type: "line",
    data: { labels, datasets: [{ label: "CPU utilization", data: cpuHistory, borderColor: "#5575ed", backgroundColor: "rgba(85,117,237,.10)", fill: true, tension: .35, pointRadius: 2, borderWidth: 2 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: "#9aa5b5", maxTicksLimit: 6, font: { size: 9 } } }, y: { min: 0, max: 100, grid: { color: "#eef1f6" }, ticks: { color: "#9aa5b5", font: { size: 9 }, callback: v => v + "%" } } } }
  });
}

function setBar(id, value) {
  const el = document.getElementById(id);
  el.style.width = value == null ? "0%" : Math.max(0, Math.min(100, value)) + "%";
}

async function refresh() {
  try {
    const response = await fetch("/api/metrics");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Unable to load metrics");
    document.getElementById("cpuValue").innerHTML = (data.cpu == null ? "--" : data.cpu) + "<small>%</small>";
    document.getElementById("memoryValue").innerHTML = (data.memory == null ? "N/A" : data.memory) + (data.memory == null ? "" : "<small>%</small>");
    setBar("cpuBar", data.cpu);
    setBar("memoryBar", data.memory);
    document.getElementById("cpuCaption").textContent = "Alert threshold: " + data.threshold + "%";
    const cpuTag = document.getElementById("cpuTag");
    cpuTag.textContent = data.cpu == null ? "No data" : (data.cpu >= data.threshold ? "High usage" : "Normal");
    cpuTag.className = "status-tag " + (data.cpu != null && data.cpu < data.threshold ? "good" : "");
    document.getElementById("memoryTag").textContent = data.memory == null ? "Agent required" : "Measured";
    document.getElementById("serverStatus").textContent = data.status;
    document.getElementById("serverName").textContent = data.server;
    document.getElementById("serverTag").textContent = data.status.includes("Issue") ? "Check required" : "Available";
    document.getElementById("serverTag").className = "status-tag " + (data.status.includes("Issue") ? "" : "good");
    document.getElementById("metricSource").textContent = data.source;
    document.getElementById("detailServer").textContent = data.server;
    document.getElementById("thresholdValue").textContent = data.threshold + "%";
    document.getElementById("lastUpdated").textContent = "Updated " + new Date(data.timestamp).toLocaleTimeString();
    const notice = document.getElementById("sourceNotice");
    if (data.mode === "aws") {
      notice.innerHTML = "<span>☁</span><div><b>AWS CloudWatch mode</b><p>CPU and EC2 status-check metrics are retrieved from your configured AWS account. " + (data.note || "") + "</p></div>";
    } else {
      notice.innerHTML = "<span>ⓘ</span><div><b>Demo mode</b><p>Showing simulated sample metrics. Connect AWS CloudWatch to display real EC2 measurements.</p></div>";
    }
    if (data.cpu != null) {
      labels.push(new Date(data.timestamp).toLocaleTimeString());
      cpuHistory.push(data.cpu);
      if (labels.length > 12) { labels.shift(); cpuHistory.shift(); }
      chart.update();
    }
    await loadIncidents();
  } catch (error) {
    document.getElementById("sourceNotice").innerHTML = "<span>⚠</span><div><b>Monitoring error</b><p>" + error.message + "</p></div>";
  }
}

async function loadIncidents() {
  const response = await fetch("/api/incidents");
  const rows = await response.json();
  document.getElementById("incidentCount").textContent = rows.length;
  document.getElementById("incidentPill").textContent = rows.length + " events";
  const body = document.getElementById("incidentRows");
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="4" class="empty">No incidents recorded yet.</td></tr>';
    return;
  }
  body.innerHTML = rows.map(item => `<tr><td>${escapeHtml(item.incident_type)}</td><td>${escapeHtml(item.message)}</td><td><span class="severity ${escapeHtml(item.severity)}">${escapeHtml(item.severity)}</span></td><td>${new Date(item.created_at).toLocaleString()}</td></tr>`).join("");
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
document.getElementById("testAlert").addEventListener("click", async () => {
  await fetch("/api/test-alert", { method: "POST" });
  await loadIncidents();
});
initChart();
refresh();
setInterval(refresh, 10000);
