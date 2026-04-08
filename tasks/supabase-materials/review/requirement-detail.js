/**
 * 需求详情页 - 子需求流水线可视化
 * URL 参数: ?id=<requirement_id>
 */

const sb = supabase.createClient(
  window.SUPABASE_DEFAULTS.url,
  window.SUPABASE_DEFAULTS.anonKey
);

// ===== 常量 =====
const AGENT_EMOJI = {
  eagle: '🦅', bee: '🐝', ant: '🐜',
  squirrel: '🐿️', owl: '🦉', pipi: '👤'
};

const STATUS_TEXT = {
  pending: '待处理', in_progress: '进行中',
  done: '已完成', success: '已发布', obsolete: '已归档'
};

const STATUS_CLASS = {
  pending: 'warning', in_progress: 'accent',
  done: 'success', success: 'success', obsolete: 'muted'
};

const SCENE_TYPE_TEXT = {
  lowfans: '低粉爆款', normal: '常态化', hot: '热点追踪'
};

// ===== 全局状态 =====
let reqData = null;
let subReqData = [];
let draftsData = [];
let imagesData = [];
let currentFilter = 'all';
let reqId = null;

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(location.search);
  reqId = params.get('id');
  if (!reqId) {
    showFatalError('缺少需求 ID，请从需求追踪页进入');
    return;
  }
  loadData();
  // 每30秒自动刷新
  setInterval(loadData, 30000);
});

// ===== 数据加载 =====
async function loadData() {
  try {
    const [reqResult, subResult, draftsResult, imagesResult] = await Promise.all([
      sb.from('requirement').select('*').eq('id', reqId).single(),
      sb.from('sub_requirement').select('*').eq('requirement_id', reqId).order('created_at', { ascending: true }),
      sb.from('note_drafts').select('id, persona_name, title, status, created_at, updated_at'),
      sb.from('generated_images').select('id, sub_requirement_id, status, image_url, created_at').eq('requirement_id', reqId)
    ]);

    if (reqResult.error) throw reqResult.error;
    if (subResult.error) throw subResult.error;

    reqData = reqResult.data;
    subReqData = subResult.data || [];
    draftsData = draftsResult.error ? [] : (draftsResult.data || []);
    imagesData = imagesResult.error ? [] : (imagesResult.data || []);

    renderOverview();
    renderProgressSummary();
    renderSubReqs();
    document.getElementById('loading').style.display = 'none';
    document.title = `需求详情 · ${reqData.description?.slice(0, 20) || reqId}`;
  } catch (err) {
    console.error(err);
    showFatalError('加载失败：' + err.message);
  }
}

// ===== 需求概览 =====
function renderOverview() {
  const el = document.getElementById('reqOverview');
  const sceneText = SCENE_TYPE_TEXT[reqData.scene_type] || reqData.scene_type || '未知';
  const timeRange = formatTimeRange(reqData.start_time, reqData.end_time);
  const createdAt = formatTime(reqData.created_at);
  el.innerHTML = `
    <div class="overview-meta">
      <span class="overview-tag">${sceneText}</span>
      <span class="overview-tag ${STATUS_CLASS[reqData.status] || ''}">${STATUS_TEXT[reqData.status] || reqData.status}</span>
      <span class="overview-id">#${reqData.id.slice(0, 8)}</span>
    </div>
    <h1 class="overview-title">${escapeHtml(reqData.description || '无描述')}</h1>
    <div class="overview-info">
      <span>📅 ${timeRange}</span>
      <span>🕐 创建于 ${createdAt}</span>
      <span>📎 ${subReqData.length} 个子需求</span>
    </div>
  `;
  el.classList.remove('skeleton-block');
}

// ===== 进度汇总 =====
function renderProgressSummary() {
  const total = subReqData.length;
  if (total === 0) return;

  const statusCounts = { pending: 0, in_progress: 0, success: 0, done: 0, obsolete: 0 };
  let hasError = 0;

  subReqData.forEach(s => {
    statusCounts[s.status] = (statusCounts[s.status] || 0) + 1;
    if (hasProgressError(s)) hasError++;
  });

  const completed = (statusCounts.success || 0) + (statusCounts.done || 0);
  const rate = Math.round((completed / total) * 100);

  // 各阶段通过率
  const hasMaterial = subReqData.filter(s => s.material_ids && s.material_ids.length > 0).length;
  const hasImage = subReqData.filter(s => {
    const imgs = imagesData.filter(img => img.sub_requirement_id === s.id);
    return imgs.length > 0;
  }).length;
  const hasDraft = subReqData.filter(s => s.draft_id).length;
  const hasPublished = subReqData.filter(s => s.status === 'success').length;

  document.getElementById('progressSummary').innerHTML = `
    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-big ${rate === 100 ? 'green' : rate > 50 ? 'blue' : 'orange'}">${rate}%</div>
        <div class="summary-label">整体完成率</div>
        <div class="summary-sub">${completed} / ${total} 子需求</div>
      </div>
      <div class="summary-card">
        <div class="pipeline-stages">
          ${pipelineStage('📦 素材填充', hasMaterial, total)}
          ${pipelineStage('🎨 图片生成', hasImage, total)}
          ${pipelineStage('📝 草稿生成', hasDraft, total)}
          ${pipelineStage('🚀 发布完成', hasPublished, total)}
        </div>
      </div>
      <div class="summary-card">
        <div class="status-breakdown">
          ${renderStatusPill('待处理', statusCounts.pending, 'warning')}
          ${renderStatusPill('进行中', statusCounts.in_progress, 'accent')}
          ${renderStatusPill('已完成', completed, 'success')}
          ${renderStatusPill('已归档', statusCounts.obsolete, 'muted')}
          ${hasError > 0 ? renderStatusPill('有错误', hasError, 'danger') : ''}
        </div>
        <div class="error-hint ${hasError > 0 ? 'visible' : ''}">
          ⚠️ ${hasError} 个子需求进度日志中含有错误
        </div>
      </div>
    </div>
  `;
}

function pipelineStage(label, count, total) {
  const rate = total > 0 ? Math.round((count / total) * 100) : 0;
  const colorClass = rate === 100 ? 'green' : rate > 0 ? 'blue' : 'gray';
  return `
    <div class="pipeline-stage">
      <div class="stage-label">${label}</div>
      <div class="stage-bar-wrap">
        <div class="stage-bar ${colorClass}" style="width:${rate}%"></div>
      </div>
      <div class="stage-count">${count}/${total}</div>
    </div>
  `;
}

function renderStatusPill(label, count, cls) {
  if (!count) return '';
  return `<span class="status-pill ${cls}">${label} <b>${count}</b></span>`;
}

// ===== 子需求网格 =====
function filterByStatus(status) {
  currentFilter = status;
  document.querySelectorAll('.filter-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.status === status);
  });
  renderSubReqs();
}

function getFilteredSubs() {
  if (currentFilter === 'all') return subReqData;
  if (currentFilter === 'error') return subReqData.filter(s => hasProgressError(s));
  return subReqData.filter(s => s.status === currentFilter);
}

function renderSubReqs() {
  const subs = getFilteredSubs();
  const label = document.getElementById('subCountLabel');
  label.textContent = `共 ${subs.length} 条`;

  const grid = document.getElementById('subReqGrid');
  if (subs.length === 0) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🔍</div><p>没有符合条件的子需求</p></div>`;
    return;
  }
  grid.innerHTML = subs.map(s => renderSubReqCard(s)).join('');
}

function renderSubReqCard(sub) {
  const draft = sub.draft_id ? draftsData.find(d => d.id === sub.draft_id) : null;
  const images = imagesData.filter(img => img.sub_requirement_id === sub.id);
  const progress = parseProgress(sub.progress);
  const hasError = hasProgressError(sub);
  const statusCls = STATUS_CLASS[sub.status] || 'muted';
  const hasMaterial = sub.material_ids && sub.material_ids.length > 0;

  return `
    <div class="sub-card ${hasError ? 'has-error' : ''}" id="sub-${sub.id}">
      <!-- 卡片头部 -->
      <div class="sub-card-header">
        <div class="sub-card-left">
          <div class="sub-persona">${escapeHtml(sub.persona_name || '未知账号')}</div>
          <div class="sub-desc">${escapeHtml(sub.content_description || '')}</div>
        </div>
        <div class="sub-card-right">
          <span class="badge ${statusCls}">${STATUS_TEXT[sub.status] || sub.status}</span>
          ${hasError ? '<span class="badge danger">⚠️ 有错误</span>' : ''}
        </div>
      </div>

      <!-- 流水线步骤 -->
      <div class="pipeline-row">
        ${pipelineStep('📦', '素材', hasMaterial, hasMaterial ? `${sub.material_ids.length} 张` : '未填充')}
        <div class="pipeline-arrow">→</div>
        ${pipelineStep('🎨', '生图', images.length > 0, images.length > 0 ? `${images.length} 张` : '未生成')}
        <div class="pipeline-arrow">→</div>
        ${pipelineStep('📝', '草稿', !!sub.draft_id, sub.draft_id ? '已生成' : '未生成', sub.draft_id ? `draft-review.html?id=${sub.draft_id}` : null)}
        <div class="pipeline-arrow">→</div>
        ${pipelineStep('🚀', '发布', sub.status === 'success', sub.status === 'success' ? '已发布' : '待发布')}
      </div>

      <!-- 进度日志 -->
      <div class="progress-log-wrap">
        <div class="progress-log-title" onclick="toggleLog('${sub.id}')">
          <span>📋 进度日志 (${progress.length} 条)</span>
          <span class="toggle-icon" id="toggle-${sub.id}">▼</span>
        </div>
        <div class="progress-log" id="log-${sub.id}" style="display:none">
          ${progress.length === 0
            ? '<div class="log-empty">暂无进度记录</div>'
            : progress.map(p => renderLogItem(p)).join('')
          }
        </div>
      </div>

      <!-- 底部元信息 -->
      <div class="sub-card-footer">
        <span class="footer-meta">🕐 更新：${formatTime(sub.updated_at)}</span>
        ${sub.category ? `<span class="footer-meta">📂 ${escapeHtml(sub.category)}</span>` : ''}
        <span class="footer-meta">ID: ${sub.id.slice(0, 8)}</span>
      </div>
    </div>
  `;
}

function pipelineStep(icon, label, done, detail, link) {
  const cls = done ? 'step-done' : 'step-pending';
  const content = `
    <div class="pipeline-step ${cls}">
      <div class="step-icon">${icon}</div>
      <div class="step-label">${label}</div>
      <div class="step-detail">${detail}</div>
    </div>
  `;
  if (link) return `<a href="${link}" class="pipeline-step-link">${content}</a>`;
  return content;
}

function renderLogItem(p) {
  const isError = !!p.error;
  return `
    <div class="log-item ${isError ? 'log-error' : ''}">
      <div class="log-agent">${AGENT_EMOJI[p.agent] || '⚙️'}</div>
      <div class="log-body">
        <div class="log-action">
          ${escapeHtml(p.action || '')}
          ${p.image_count ? ` <span class="log-badge">${p.image_count}张</span>` : ''}
          ${p.count !== undefined ? ` <span class="log-badge">${p.count}条</span>` : ''}
        </div>
        ${isError ? `<div class="log-error-msg">⚠️ ${escapeHtml(p.error)}</div>` : ''}
        ${p.note ? `<div class="log-note">${escapeHtml(p.note)}</div>` : ''}
        <div class="log-time">${formatTime(p.at)}</div>
      </div>
    </div>
  `;
}

function toggleLog(subId) {
  const log = document.getElementById('log-' + subId);
  const icon = document.getElementById('toggle-' + subId);
  if (log.style.display === 'none') {
    log.style.display = 'block';
    icon.textContent = '▲';
  } else {
    log.style.display = 'none';
    icon.textContent = '▼';
  }
}

// ===== 工具函数 =====
function parseProgress(raw) {
  if (!raw) return [];
  if (typeof raw === 'string') {
    try { raw = JSON.parse(raw); } catch { return []; }
  }
  if (!Array.isArray(raw) && raw?.data) raw = raw.data;
  if (!Array.isArray(raw)) return [];
  if (raw.length === 1 && Array.isArray(raw[0]?.progress)) raw = raw[0].progress;
  return [...raw].sort((a, b) => new Date(a.at) - new Date(b.at));
}

function hasProgressError(sub) {
  const progress = parseProgress(sub.progress);
  return progress.some(p => !!p.error);
}

function formatTimeRange(start, end) {
  if (!start && !end) return '未设置时间';
  if (!start) return `截止 ${formatDate(end)}`;
  if (!end) return `从 ${formatDate(start)}`;
  return `${formatDate(start)} ~ ${formatDate(end)}`;
}

function formatTime(time) {
  if (!time) return '-';
  return new Date(time).toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

function formatDate(date) {
  if (!date) return '';
  return new Date(date).toLocaleDateString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    month: 'short', day: 'numeric'
  });
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showFatalError(msg) {
  document.getElementById('loading').style.display = 'none';
  document.getElementById('subReqGrid').innerHTML = `
    <div class="empty-state">
      <div class="empty-state-icon">⚠️</div>
      <p>${msg}</p>
      <a href="requirement.html" class="back-btn" style="margin-top:16px;display:inline-block;">← 返回需求列表</a>
    </div>
  `;
}
