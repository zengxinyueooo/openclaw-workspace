/**
 * 需求追踪页面 - 功能实现
 * 需求 → 子需求 → 草稿 → 发布 全流程追踪
 */

// 动态加载共享导航栏（兼容旧版HTML没有引用nav.js的情况）
(function() {
  if (!document.querySelector('script[src*="nav.js"]')) {
    var s = document.createElement('script');
    s.src = 'nav.js?v=20260408e';
    document.head.appendChild(s);
  }
})();

// 初始化 Supabase
const sb = supabase.createClient(
  window.SUPABASE_DEFAULTS.url,
  window.SUPABASE_DEFAULTS.anonKey
);

// Agent Emoji 映射
const AGENT_EMOJI = {
  eagle: '🦅',   // 鹰眼 - 策划
  bee: '🐝',     // 蜜蜂 - 生产
  ant: '🐜',     // 蚂蚁 - 运营
  squirrel: '🐿️', // 松鼠 - 采集
  owl: '🦉',     // 猫头鹰 - 数据
  pipi: '👤'     // 皮皮 - 人工审核
};

// 状态显示文本
const STATUS_TEXT = {
  pending: '待处理',
  in_progress: '进行中',
  done: '已完成',
  success: '已成功',
  obsolete: '已归档'
};

// 场景类型显示
const SCENE_TYPE_TEXT = {
  lowfans: '低粉爆款',
  normal: '常态化',
  hot: '热点追踪'
};

// 全局数据缓存
let requirementsData = [];
let subRequirementsData = [];
let draftsData = [];
let refreshInterval = null;
let isFirstLoad = true;
// 记录展开状态
let expandedReqIds = new Set();

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', () => {
  loadData();
  // 每30秒自动刷新
  refreshInterval = setInterval(loadData, 30000);
});

/**
 * 加载所有数据
 */
async function loadData() {
  try {
    // 只有首次加载才显示 loading，刷新时静默更新
    if (isFirstLoad) showLoading(true);
    
    // 并行查询所有数据
    const [reqResult, subResult, draftsResult] = await Promise.all([
      sb.from('requirement').select('*').order('created_at', { ascending: false }),
      sb.from('sub_requirement').select('*'),
      sb.from('note_drafts').select('id, persona_name, title, status')
    ]);

    if (reqResult.error) throw reqResult.error;
    if (subResult.error) throw subResult.error;
    if (draftsResult.error) throw draftsResult.error;

    requirementsData = reqResult.data || [];
    subRequirementsData = subResult.data || [];
    draftsData = draftsResult.data || [];

    renderStats();
    renderRequirements();
    isFirstLoad = false;
  } catch (err) {
    console.error('加载数据失败:', err);
    if (isFirstLoad) showError('加载数据失败: ' + err.message);
  } finally {
    showLoading(false);
  }
}

/**
 * 显示/隐藏加载状态
 */
function showLoading(show) {
  const loadingEl = document.getElementById('loading');
  const reqListEl = document.getElementById('reqList');
  
  if (show) {
    loadingEl.style.display = 'block';
    reqListEl.style.display = 'none';
  } else {
    loadingEl.style.display = 'none';
    reqListEl.style.display = 'block';
  }
}

/**
 * 显示错误信息
 */
function showError(message) {
  const reqListEl = document.getElementById('reqList');
  reqListEl.innerHTML = `
    <div class="empty-state">
      <div class="empty-state-icon">⚠️</div>
      <p>${message}</p>
    </div>
  `;
}

/**
 * 渲染统计摘要
 */
function renderStats() {
  const totalReqs = requirementsData.length;
  const totalSubReqs = subRequirementsData.length;
  const doneSubReqs = subRequirementsData.filter(s => s.status === 'success').length;
  const completionRate = totalSubReqs > 0 
    ? Math.round((doneSubReqs / totalSubReqs) * 100) 
    : 0;

  const statsRow = document.getElementById('statsRow');
  statsRow.innerHTML = `
    <div class="stat-card">
      <div class="stat-value">${totalReqs}</div>
      <div class="stat-label">总需求数</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${totalSubReqs}</div>
      <div class="stat-label">子需求数</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${completionRate}%</div>
      <div class="stat-label">完成率</div>
    </div>
  `;
}

/**
 * 渲染需求列表
 */
function renderRequirements() {
  const reqListEl = document.getElementById('reqList');
  
  if (requirementsData.length === 0) {
    reqListEl.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <p>暂无需求数据</p>
      </div>
    `;
    return;
  }

  // 保存滚动位置
  const scrollY = window.scrollY;
  
  reqListEl.innerHTML = '<div class="req-list">' + 
    requirementsData.map(req => renderRequirementCard(req)).join('') +
    '</div>';
  
  // 恢复展开状态
  expandedReqIds.forEach(reqId => {
    const card = document.querySelector(`.req-card[data-req-id="${reqId}"]`);
    if (card) card.classList.add('expanded');
  });
  
  // 恢复滚动位置
  requestAnimationFrame(() => window.scrollTo(0, scrollY));
}

/**
 * 渲染单个需求卡片
 */
function renderRequirementCard(req) {
  const sceneTypeText = SCENE_TYPE_TEXT[req.scene_type] || req.scene_type;
  const timeRange = formatTimeRange(req.start_time, req.end_time);
  const subReqs = subRequirementsData.filter(s => s.requirement_id === req.id);
  
  return `
    <div class="req-card" data-req-id="${req.id}">
      <div class="req-header" onclick="toggleExpand('${req.id}')">
        <div class="req-header-left">
          <div class="req-id">#${req.id.slice(0, 8)} · ${sceneTypeText}</div>
          <div class="req-title">${escapeHtml(req.description)}</div>
          <div class="req-meta">
            <span>📅 ${timeRange}</span>
            <span>📎 ${subReqs.length} 个子需求</span>
          </div>
        </div>
        <div class="req-header-right">
          ${req.id ? `<a href="requirement-detail.html?id=${req.id}" class="detail-btn" onclick="event.stopPropagation()" title="查看子需求详情">📊 详情</a>` : ''}
          <span class="status-badge ${req.status}">${STATUS_TEXT[req.status] || req.status}</span>
          <span class="expand-icon">▼</span>
        </div>
      </div>
      <div class="sub-req-container">
        <div class="sub-req-list">
          ${subReqs.length > 0 
            ? subReqs.map(sub => renderSubRequirementCard(sub)).join('')
            : '<div class="empty-state" style="padding: var(--space-6);"><p>暂无子需求</p></div>'
          }
        </div>
      </div>
    </div>
  `;
}

/**
 * 渲染子需求卡片
 */
function renderSubRequirementCard(sub) {
  const draft = sub.draft_id ? draftsData.find(d => d.id === sub.draft_id) : null;
  const timeline = generateTimeline(sub);
  
  return `
    <div class="sub-req-card">
      <div class="sub-req-header">
        <div class="sub-req-persona">
          ${escapeHtml(sub.persona_name)}
        </div>
        <div class="sub-req-badges">
          <span class="status-badge ${sub.status}">${STATUS_TEXT[sub.status] || sub.status}</span>
          ${renderDraftBadge(draft, sub.draft_id)}
        </div>
      </div>
      <div class="sub-req-desc">${escapeHtml(sub.content_description || '')}</div>
      ${timeline}
    </div>
  `;
}

/**
 * 渲染草稿徽章
 */
function renderDraftBadge(draft, draftId) {
  if (!draftId) {
    return '<span class="draft-badge no-draft">无草稿</span>';
  }
  
  const title = draft ? escapeHtml(draft.title || '未命名草稿') : '草稿加载中...';
  return `<a href="draft-review.html?id=${draftId}" class="draft-badge">📝 ${title}</a>`;
}

/**
 * 生成进度时间线
 */
function generateTimeline(sub) {
  // progress 可能存成 [array] 或 [{progress: array}]（嵌套结构），标准化为 array
  let progress = sub.progress;
  if (!progress) progress = [];
  if (typeof progress === 'string') {
    try { progress = JSON.parse(progress); } catch { progress = []; }
  }
  // 兼容 {data: [...]} 结构（必须在 isArray 检查之前）
  if (!Array.isArray(progress) && progress?.data) {
    try { progress = progress.data; } catch { progress = []; }
  }
  if (!Array.isArray(progress)) progress = [];
  // 兼容嵌套：如果是 [{progress: [...]}] 结构，提取内层
  if (progress.length === 1 && Array.isArray(progress[0]?.progress)) {
    progress = progress[0].progress;
  }
  if (progress.length === 0) {
    return '<div class="timeline"><div class="timeline-item"><div class="timeline-content"><div class="timeline-action">暂无进度</div></div></div></div>';
  }
  // 按时间排序
  const sorted = [...progress].sort((a, b) => new Date(a.at) - new Date(b.at));
  return `
    <div class="timeline">
      ${sorted.map(item => `
        <div class="timeline-item completed">
          <div class="timeline-content">
            <div class="timeline-action">
              <span class="agent-emoji">${AGENT_EMOJI[item.agent] || '⚙️'}</span>
              ${escapeHtml(item.action || '')}
              ${item.image_count ? ' (' + item.image_count + '张)' : ''}
              ${item.error ? ' ⚠️ ' + escapeHtml(item.error) : ''}
            </div>
            <div class="timeline-time">${formatTime(item.at)}</div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

/**
 * 展开/收起需求卡片
 */
function toggleExpand(reqId) {
  const card = document.querySelector(`.req-card[data-req-id="${reqId}"]`);
  if (card) {
    card.classList.toggle('expanded');
    // 记录展开状态，刷新后恢复
    if (card.classList.contains('expanded')) {
      expandedReqIds.add(reqId);
    } else {
      expandedReqIds.delete(reqId);
    }
  }
}

/**
 * 格式化时间范围
 */
function formatTimeRange(start, end) {
  if (!start && !end) return '未设置时间';
  if (!start) return `截止 ${formatDate(end)}`;
  if (!end) return `从 ${formatDate(start)}`;
  return `${formatDate(start)} ~ ${formatDate(end)}`;
}

/**
 * 格式化时间
 */
function formatTime(time) {
  if (!time) return '';
  const date = new Date(time);
  return date.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * 格式化日期
 */
function formatDate(date) {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * HTML 转义
 */
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
