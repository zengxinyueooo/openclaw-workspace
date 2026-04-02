/* global supabase, Chart */
let client = null;
let charts = {};

const statusEl = document.getElementById("status");
const connectBtn = document.getElementById("connect");
const urlInput = document.getElementById("supabase-url");
const keyInput = document.getElementById("supabase-key");
const configSection = document.getElementById("config");
const dashboardSection = document.getElementById("dashboard");

const savedUrl = localStorage.getItem("supabaseUrl");
const savedKey = localStorage.getItem("supabaseAnonKey");
if (savedUrl) urlInput.value = savedUrl;
if (savedKey) keyInput.value = savedKey;

function setStatus(text) {
  statusEl.textContent = text;
}

async function loadStats() {
  if (!client) return;
  setStatus("加载数据中...");

  // 总生成量
  const { count: totalGenerated } = await client
    .from("generated_images")
    .select("*", { count: "exact", head: true });
  document.getElementById("total-generated").textContent = totalGenerated || 0;
  document.getElementById("funnel-total-val").textContent = totalGenerated || 0;

  // 人脸通过
  const { count: facePassed } = await client
    .from("generated_images")
    .select("*", { count: "exact", head: true })
    .eq("face_passed", true);
  document.getElementById("funnel-face-val").textContent = facePassed || 0;
  const faceRate = totalGenerated ? (facePassed / totalGenerated * 100).toFixed(1) : 0;
  document.getElementById("funnel-face").style.width = faceRate + "%";

  // 人工审核通过
  const { count: humanApproved } = await client
    .from("generated_images")
    .select("*", { count: "exact", head: true })
    .eq("human_verdict", "approved");
  document.getElementById("human-approved").textContent = humanApproved || 0;
  document.getElementById("funnel-human-val").textContent = humanApproved || 0;
  const humanRate = facePassed ? (humanApproved / facePassed * 100).toFixed(1) : 0;
  document.getElementById("funnel-human").style.width = (humanRate * faceRate / 100) + "%";

  // 整体通过率
  const overallRate = totalGenerated ? (humanApproved / totalGenerated * 100).toFixed(1) : 0;
  document.getElementById("overall-rate").textContent = overallRate + "%";

  // 平均美感分
  const { data: aestheticData } = await client
    .from("generated_images")
    .select("aesthetic_score")
    .eq("human_verdict", "approved")
    .not("aesthetic_score", "is", null);
  if (aestheticData && aestheticData.length) {
    const avg = aestheticData.reduce((a, b) => a + b.aesthetic_score, 0) / aestheticData.length;
    document.getElementById("avg-aesthetic").textContent = avg.toFixed(1);
  } else {
    document.getElementById("avg-aesthetic").textContent = "-";
  }

  // 拒绝原因分布
  const { data: rejectData } = await client
    .from("generated_images")
    .select("reject_reason")
    .eq("human_verdict", "rejected")
    .not("reject_reason", "is", null);
  
  const reasonCounts = {};
  if (rejectData) {
    rejectData.forEach(d => {
      reasonCounts[d.reject_reason] = (reasonCounts[d.reject_reason] || 0) + 1;
    });
  }
  
  updatePieChart("reject-reason-chart", reasonCounts);

  // 各人设通过率
  const { data: personaData } = await client
    .from("generated_images")
    .select("persona_name,human_verdict");
  
  const personaStats = {};
  if (personaData) {
    personaData.forEach(d => {
      if (!personaStats[d.persona_name]) {
        personaStats[d.persona_name] = { total: 0, approved: 0 };
      }
      personaStats[d.persona_name].total++;
      if (d.human_verdict === "approved") {
        personaStats[d.persona_name].approved++;
      }
    });
  }
  
  const personaRates = {};
  Object.entries(personaStats).forEach(([name, stats]) => {
    personaRates[name] = stats.total ? (stats.approved / stats.total * 100).toFixed(1) : 0;
  });
  
  updateBarChart("persona-chart", personaRates);

  // 30天趋势
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  const { data: trendData } = await client
    .from("generation_tasks")
    .select("created_at,face_passed_count")
    .gte("created_at", thirtyDaysAgo.toISOString())
    .order("created_at", { ascending: true });
  
  updateTrendChart(trendData);
  
  setStatus("数据已加载");
}

function updatePieChart(canvasId, data) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  if (charts[canvasId]) charts[canvasId].destroy();
  
  const labels = Object.keys(data);
  const values = Object.values(data);
  
  charts[canvasId] = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels.length ? labels : ["暂无数据"],
      datasets: [{
        data: values.length ? values : [1],
        backgroundColor: ["#6366f1", "#22c55e", "#f97316", "#a855f7", "#64748b"]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "right", labels: { color: "#94a3b8" } } }
    }
  });
}

function updateBarChart(canvasId, data) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  if (charts[canvasId]) charts[canvasId].destroy();
  
  charts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: Object.keys(data),
      datasets: [{
        label: "通过率%",
        data: Object.values(data),
        backgroundColor: "#6366f1"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, max: 100, ticks: { color: "#94a3b8" } },
        x: { ticks: { color: "#94a3b8" } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

function updateTrendChart(data) {
  const ctx = document.getElementById("trend-chart").getContext("2d");
  if (charts.trend) charts.trend.destroy();
  
  if (!data || !data.length) {
    charts.trend = new Chart(ctx, {
      type: "line",
      data: { labels: ["暂无数据"], datasets: [{ data: [0] }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
    return;
  }
  
  const labels = data.map(d => new Date(d.created_at).toLocaleDateString("zh-CN"));
  const values = data.map(d => d.face_passed_count || 0);  
  charts.trend = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "人脸通过数",
        data: values,
        borderColor: "#6366f1",
        backgroundColor: "rgba(99, 102, 241, 0.1)",
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { ticks: { color: "#94a3b8" } },
        x: { ticks: { color: "#94a3b8" } }
      },
      plugins: { legend: { labels: { color: "#94a3b8" } } }
    }
  });
}

connectBtn.addEventListener("click", async () => {
  const url = urlInput.value.trim();
  const key = keyInput.value.trim();
  if (!url || !key) {
    setStatus("请输入地址和密钥");
    return;
  }
  
  localStorage.setItem("supabaseUrl", url);
  localStorage.setItem("supabaseAnonKey", key);
  
  client = supabase.createClient(url, key);
  setStatus("已连接");
  configSection.style.display = "none";
  dashboardSection.style.display = "";
  
  await loadStats();
});

const defaults = window.SUPABASE_DEFAULTS || {};
if (savedUrl || defaults.url) {
  urlInput.value = savedUrl || defaults.url;
}
if (savedKey || defaults.anonKey) {
  keyInput.value = savedKey || defaults.anonKey;
}

if (urlInput.value && keyInput.value) {
  connectBtn.click();
}
