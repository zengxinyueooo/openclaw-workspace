/* global supabase */
let client = null;
let materials = [];
let currentIndex = 0;
let approvedCount = 0;
let rejectedCount = 0;
let startX = 0;
let startY = 0;
let currentX = 0;
let dragging = false;
let maxMoveDistance = 0;
let blockClick = false;
let actionLocked = false;
let currentBatchId = null;
let actionHistory = []; // [{item, status, insertedAt}]

const statusEl = document.getElementById("status");
const connectBtn = document.getElementById("connect");
const urlInput = document.getElementById("supabase-url");
const keyInput = document.getElementById("supabase-key");
const card = document.getElementById("card");
const cardImage = document.getElementById("card-image");
const badgeApprove = document.getElementById("badge-approve");
const badgeReject = document.getElementById("badge-reject");
const metaTags = document.getElementById("meta-tags");
const metaMood = document.getElementById("meta-mood");
const metaRes = document.getElementById("meta-res");
const progressEl = document.getElementById("progress");
const approveBtn = document.getElementById("btn-approve");
const rejectBtn = document.getElementById("btn-reject");
const lightbox = document.getElementById("lightbox");
const lightboxImage = document.getElementById("lightbox-image");
const lightboxClose = document.getElementById("lightbox-close");
const batchListSection = document.getElementById("batch-list");
const batchItemsEl = document.getElementById("batch-items");
const doneScreen = document.getElementById("done-screen");
const doneStats = document.getElementById("done-stats");
const btnBack = document.getElementById("btn-back");
const pageTitle = document.getElementById("page-title");
const pageSubtitle = document.getElementById("page-subtitle");
const deckSection = document.querySelector(".deck");
const actionsSection = document.querySelector(".actions");
const footerSection = document.querySelector(".footer");

// 从 URL 获取 batch 参数
const urlParams = new URLSearchParams(window.location.search);
currentBatchId = urlParams.get("batch") || null;

const savedUrl = localStorage.getItem("supabaseUrl");
const savedKey = localStorage.getItem("supabaseAnonKey");
if (savedUrl) urlInput.value = savedUrl;
if (savedKey) keyInput.value = savedKey;

function setStatus(text) {
  statusEl.textContent = text;
}

function updateProgress() {
  const current = Math.min(currentIndex + 1, materials.length);
  progressEl.textContent = `已通过 ${approvedCount} · 已拒绝 ${rejectedCount} · ${current} / ${materials.length}`;
}

function resetCardTransform() {
  card.style.transition = "transform 0.2s ease";
  card.style.transform = "translate3d(0px, 0, 0) rotate(0deg)";
  badgeApprove.style.opacity = 0;
  badgeReject.style.opacity = 0;
  setTimeout(() => {
    card.style.transition = "";
  }, 200);
}

function preloadNextImage() {
  const offsets = [-2, -1, 1, 2];
  offsets.forEach((offset) => {
    const item = materials[currentIndex + offset];
    if (!item || !item.image_url) return;
    const img = new Image();
    img.src = item.image_url;
  });
}

function showReviewUI(show) {
  const d = show ? "" : "none";
  deckSection.style.display = show ? "" : "none";
  actionsSection.style.display = show ? "" : "none";
  footerSection.style.display = show ? "" : "none";
}

function showDoneScreen() {
  showReviewUI(false);
  doneScreen.style.display = "";
  doneStats.textContent = `已通过 ${approvedCount} 张 / 已拒绝 ${rejectedCount} 张`;
}

function renderCard() {
  // 更新批次信息展示
  const batchInfoEl = document.getElementById("batch-info");
  if (batchInfoEl && materials.length > 0 && currentIndex < materials.length) {
    const current = materials[currentIndex];
    const category = current.category || '未分类';
    const contextType = current.context_type || 'general';
    const contextName = current.context_name || '';
    let contextDisplay = '';
    if (contextType === 'store') contextDisplay = contextName ? `📍 ${contextName}` : '📍 门店';
    else if (contextType === 'campaign') contextDisplay = contextName ? `🎯 ${contextName}` : '🎯 活动';
    else contextDisplay = '🌐 通用';
    batchInfoEl.innerHTML = `<span class="badge-category">${category}</span> <span class="badge-context">${contextDisplay}</span>`;
  }

  if (!materials.length || currentIndex >= materials.length) {
    cardImage.src = "";
    metaTags.innerHTML = "";
    metaMood.textContent = "--";
    metaRes.textContent = "--";
    card.style.opacity = 1;
    updateProgress();
    if (approvedCount + rejectedCount > 0) {
      showDoneScreen();
    } else {
      setStatus("暂无待审核素材");
    }
    return;
  }

  const item = materials[currentIndex];
  card.style.opacity = 0;
  cardImage.onload = () => {
    card.style.opacity = 1;
  };
  cardImage.onerror = () => {
    card.style.opacity = 1;
  };
  cardImage.src = item.image_url;
  // 渲染标签
  const tags = item.tags || [];
  metaTags.innerHTML = tags.map(t => `<span class="tag">${t}</span>`).join("");
  metaMood.textContent = item.mood ? `🌈 ${item.mood}` : "";
  metaRes.textContent = item.resolution ?? "";
  updateProgress();
  preloadNextImage();
}

async function fetchBatchList() {
  if (!client) return;
  setStatus("正在加载批次列表...");

  // 从 materials 表实时统计，加入 category 字段用于左右分栏
  const { data: allMaterials, error } = await client
    .from("materials")
    .select("batch_id,status,category");
  if (error) { setStatus(`加载失败：${error.message}`); return; }
  if (!allMaterials || !allMaterials.length) {
    document.getElementById("batch-items-face").innerHTML = '<div class="empty-state" style="padding:var(--space-4) 0; font-size:0.875rem;">暂无素材</div>';
    document.getElementById("batch-items-nail").innerHTML = '<div class="empty-state" style="padding:var(--space-4) 0; font-size:0.875rem;">暂无素材</div>';
    showReviewUI(false);
    batchListSection.style.display = "";
    setStatus("已连接");
    return;
  }

  // 按 batch_id 分组统计，并记录 category
  const batchMap = {};
  allMaterials.forEach((m) => {
    const bid = m.batch_id || "未分类";
    if (!batchMap[bid]) batchMap[bid] = { total: 0, pending: 0, approved: 0, rejected: 0, category: m.category };
    batchMap[bid].total += 1;
    if (m.status === "pending") batchMap[bid].pending += 1;
    else if (m.status === "approved") batchMap[bid].approved += 1;
    else if (m.status === "rejected") batchMap[bid].rejected += 1;
  });

  const batchIds = Object.keys(batchMap).sort().reverse();

  // 分离 face 和 nail 批次
  const faceBatches = [];
  const nailBatches = [];
  const nailFaceBatches = [];
  batchIds.forEach((bid) => {
    const b = batchMap[bid];
    if (b.pending === 0) return; // 跳过已全部审核完的
    // 优先按 batch_id 前缀判断，避免旧数据 category 不准确导致归类错误
    if (bid.startsWith("nail-face")) nailFaceBatches.push({ bid, ...b });
    else if (bid.startsWith("nail")) nailBatches.push({ bid, ...b });
    else faceBatches.push({ bid, ...b });
  });

  const faceContainer = document.getElementById("batch-items-face");
  const nailContainer = document.getElementById("batch-items-nail");
  const nailFaceContainer = document.getElementById("batch-items-nail-face");

  function renderBatchList(container, batches) {
    container.innerHTML = "";
    if (!batches.length) {
      container.innerHTML = '<div class="empty-state" style="padding:var(--space-4) 0; font-size:0.875rem;">暂无</div>';
      return;
    }
    batches.forEach(({ bid, total, pending, approved, rejected }) => {
      const el = document.createElement("a");
      el.className = "task-card";
      el.href = `?batch=${encodeURIComponent(bid)}`;
      el.innerHTML = `
        <div class="task-top">
          <div class="task-name">${bid}</div>
          <div class="badge" style="background:var(--accent-soft); color:var(--accent);">待审核 ${pending}</div>
        </div>
        <div class="task-meta">
          <div class="task-counts">
            <span>总计 ${total}</span>
            <span>通过 ${approved}</span>
            <span>拒绝 ${rejected}</span>
          </div>
        </div>`;
      container.appendChild(el);
    });
  }

  renderBatchList(faceContainer, faceBatches);
  renderBatchList(nailContainer, nailBatches);
  renderBatchList(nailFaceContainer, nailFaceBatches);

  showReviewUI(false);
  batchListSection.style.display = "";
  setStatus("已连接");
}

async function fetchPending() {
  if (!client) return;

  // 无 batch 参数则显示批次列表
  if (!currentBatchId) { fetchBatchList(); return; }

  pageTitle.textContent = `审核 · ${currentBatchId}`;
  setStatus("正在加载待审核...");
  let query = client
    .from("materials")
    .select("id,image_url,tags,mood,resolution,storage_path,batch_id,created_at,category,context_type,context_id,context_name")
    .eq("status", "pending")
    .eq("batch_id", currentBatchId)
    .order("score", { ascending: false })
    .order("created_at", { ascending: false });

  const { data, error } = await query;

  if (error) {
    setStatus(`加载失败：${error.message}`);
    return;
  }

  materials = data || [];
  currentIndex = 0;
  approvedCount = 0;
  rejectedCount = 0;
  actionHistory = [];
  updateUndoButton();
  setStatus(`已加载 ${materials.length} 条`);
  renderCard();
}

function updateUndoButton() {
  const btn = document.getElementById("btn-undo");
  if (!btn) return;
  btn.disabled = actionHistory.length === 0;
  btn.style.opacity = actionHistory.length === 0 ? "0.3" : "1";
}

async function updateStatus(newStatus) {
  if (!client || !materials.length || currentIndex >= materials.length) return;
  const item = materials[currentIndex];
  setStatus("正在保存...");

  const { error } = await client
    .from("materials")
    .update({ status: newStatus, reviewed_at: new Date().toISOString() })
    .eq("id", item.id);

  if (error) {
    setStatus(`保存失败：${error.message}`);
    return;
  }

  // 记录操作历史（只保留最近 10 步）
  actionHistory.push({ item, status: newStatus, insertedAt: currentIndex });
  if (actionHistory.length > 10) actionHistory.shift();
  updateUndoButton();

  if (newStatus === "approved") {
    approvedCount += 1;
  } else {
    rejectedCount += 1;
  }
  materials.splice(currentIndex, 1);
  if (currentIndex >= materials.length) {
    currentIndex = materials.length - 1;
  }
  setStatus("已保存");
  renderCard();
}

async function undoLast() {
  if (actionLocked || actionHistory.length === 0) return;
  actionLocked = true;
  const { item, status, insertedAt } = actionHistory.pop();
  setStatus("正在撤回...");

  const { error } = await client
    .from("materials")
    .update({ status: "pending", reviewed_at: null })
    .eq("id", item.id);

  if (error) {
    setStatus(`撤回失败：${error.message}`);
    actionHistory.push({ item, status, insertedAt }); // 恢复
    actionLocked = false;
    updateUndoButton();
    return;
  }

  // 恢复计数
  if (status === "approved") approvedCount = Math.max(0, approvedCount - 1);
  else rejectedCount = Math.max(0, rejectedCount - 1);

  // 把 item 插回原位
  const insertPos = Math.min(insertedAt, materials.length);
  materials.splice(insertPos, 0, item);
  currentIndex = insertPos;

  // 如果完成屏正在显示，切回审核界面
  if (doneScreen.style.display !== "none") {
    doneScreen.style.display = "none";
    showReviewUI(true);
  }

  updateUndoButton();
  setStatus("已撤回");
  renderCard();
  actionLocked = false;
}

async function animateAndUpdate(newStatus, direction) {
  if (actionLocked) return;
  if (!materials.length || currentIndex >= materials.length) return;
  actionLocked = true;
  if (navigator.vibrate) {
    navigator.vibrate(50);
  }
  const travel = 150 * direction;
  const rotation = 20 * direction;

  // 飞出动画
  card.style.transition = "transform 0.3s ease, opacity 0.3s ease";
  card.style.transform = `translate3d(${travel}vw, 0, 0) rotate(${rotation}deg)`;
  card.style.opacity = 0;
  badgeApprove.style.opacity = direction > 0 ? 1 : 0;
  badgeReject.style.opacity = direction < 0 ? 1 : 0;

  // 用固定 setTimeout 代替 transitionend（更可靠）
  await new Promise((resolve) => setTimeout(resolve, 320));

  // 瞬间复位（不可见状态下）
  card.style.transition = "none";
  card.style.transform = "translate3d(0, 0, 0) rotate(0deg)";
  badgeApprove.style.opacity = 0;
  badgeReject.style.opacity = 0;

  try {
    await updateStatus(newStatus);
  } finally {
    // renderCard 里的 onload 会把 opacity 恢复为 1
    // 但如果图已缓存，onload 可能在 .src 赋值时同步触发，此时补一下
    if (cardImage.complete && cardImage.naturalWidth > 0) {
      card.style.opacity = 1;
    }
    actionLocked = false;
  }
}

function handleSwipeEnd() {
  const deltaX = currentX - startX;
  const threshold = 80;

  if (Math.abs(deltaX) > threshold) {
    if (deltaX > 0) {
      animateAndUpdate("approved", 1);
    } else {
      animateAndUpdate("rejected", -1);
    }
  } else {
    resetCardTransform();
  }
}

card.addEventListener("touchstart", (event) => {
  if (!materials.length || actionLocked) return;
  const touch = event.touches[0];
  startX = touch.clientX;
  startY = touch.clientY;
  currentX = startX;
  dragging = true;
  maxMoveDistance = 0;
  blockClick = false;
});

card.addEventListener(
  "touchmove",
  (event) => {
  if (!dragging) return;
  event.preventDefault();
  const touch = event.touches[0];
  currentX = touch.clientX;
  const deltaX = currentX - startX;
  const deltaY = touch.clientY - startY;
  maxMoveDistance = Math.max(maxMoveDistance, Math.hypot(deltaX, deltaY));
  if (Math.abs(deltaY) > Math.abs(deltaX)) return;
  const rotation = deltaX / 20;
  card.style.transform = `translate3d(${deltaX}px, 0, 0) rotate(${rotation}deg)`;
  badgeApprove.style.opacity = deltaX > 0 ? Math.min(deltaX / 120, 1) : 0;
  badgeReject.style.opacity = deltaX < 0 ? Math.min(Math.abs(deltaX) / 120, 1) : 0;
  },
  { passive: false }
);

card.addEventListener("touchend", () => {
  if (!dragging) return;
  dragging = false;
  blockClick = maxMoveDistance > 10;
  handleSwipeEnd();
});

card.addEventListener("click", () => {
  if (!materials.length || currentIndex >= materials.length) return;
  if (blockClick) return;
  lightboxImage.src = materials[currentIndex].image_url;
  lightbox.classList.add("show");
});

lightboxClose.addEventListener("click", () => {
  lightbox.classList.remove("show");
});

approveBtn.addEventListener("click", () => animateAndUpdate("approved", 1));
rejectBtn.addEventListener("click", () => animateAndUpdate("rejected", -1));

const undoBtn = document.getElementById("btn-undo");
if (undoBtn) {
  undoBtn.addEventListener("click", undoLast);
}

btnBack.addEventListener("click", () => {
  window.location.href = window.location.pathname;
});

connectBtn.addEventListener("click", () => {
  const url = urlInput.value.trim();
  const key = keyInput.value.trim();
  if (!url || !key) {
    setStatus("请输入 Supabase 地址和匿名密钥");
    return;
  }

  localStorage.setItem("supabaseUrl", url);
  localStorage.setItem("supabaseAnonKey", key);
  client = supabase.createClient(url, key);
  setStatus("已连接");
  fetchPending();
});

// 自动加载默认配置
const defaults = window.SUPABASE_DEFAULTS || {};
if (savedUrl || defaults.url) {
  urlInput.value = savedUrl || defaults.url;
}
if (savedKey || defaults.anonKey) {
  keyInput.value = savedKey || defaults.anonKey;
}

// 如果有配置，自动连接
if (urlInput.value && keyInput.value) {
  const url = urlInput.value.trim();
  const key = keyInput.value.trim();
  localStorage.setItem("supabaseUrl", url);
  localStorage.setItem("supabaseAnonKey", key);
  client = supabase.createClient(url, key);
  setStatus("已自动连接");
  document.getElementById("config").style.display = "none";
  fetchPending();
} else {
  setStatus("请填写 Supabase 连接信息");
  renderCard();
}
