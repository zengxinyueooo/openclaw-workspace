/* global supabase */
const STATUS = { OK: "ok", ERROR: "error", DEFAULT: "default" };

let client = null;
let currentSubId = null;
let currentTaskIdParam = null;
let currentType = null; // "face" | "nail" | "all"
let images = [];
const selectedIds = new Set();

// ─── 类型处理器 ───────────────────────────────────────────────
// 每个内容类型定义自己的：如何查任务、如何查图、如何分组、如何打标
const TYPE_HANDLERS = {
  face: {
    label: "颜值",
    // 任务列表入口查询（用于"全部"tab时，也要返回每种类型的计数）
    tasksQuery: async (client) => {
      const { data, error } = await client
        .from("sub_requirement")
        .select("id,persona_name,status,draft_id,created_at,generated_images!inner(id,face_passed,status,human_verdict)")
        .is("deleted_at", null)
        .order("created_at", { ascending: false });
      if (error) throw error;
      return data || [];
    },
    // 从 raw 任务数据计算 pending 任务列表
    parseTasks: (rawData) => {
      const tasks = rawData.map((sub) => {
        const imgs = sub.generated_images || [];
        const passedCount = imgs.filter(i => i.face_passed && i.status !== "ai_rejected").length;
        const pendingReviewCount = imgs.filter(i => i.face_passed && i.status !== "ai_rejected" && i.human_verdict == null).length;
        return {
          id: sub.id,
          type: "face",
          contentType: "face",
          persona_name: sub.persona_name,
          status: sub.status,
          draft_id: sub.draft_id,
          created_at: sub.created_at,
          generated_count: imgs.length,
          face_passed_count: passedCount,
          pending_review_count: pendingReviewCount
        };
      }).filter(t => t.pending_review_count > 0);
      return tasks;
    },
    // 单个任务加载图片时的查询
    galleryQuery: async (client, subId) => {
      const { data: sub, error: subError } = await client
        .from("sub_requirement").select("id,persona_name,status,draft_id,created_at").eq("id", subId).single();
      if (subError) throw subError;

      const { data: imgs, error } = await client
        .from("generated_images")
        .select("id,task_id,image_url,aesthetic_score,face_distance,face_passed,status,ai_taste_score,human_verdict,reviewed_at")
        .eq("sub_requirement_id", subId)
        .order("face_passed", { ascending: false })
        .order("aesthetic_score", { ascending: false, nullsFirst: false });
      if (error) throw error;

      let styleUrl = null;
      const taskIds = [...new Set((imgs || []).map(i => i.task_id).filter(Boolean))];
      if (taskIds.length > 0) {
        const { data: tasks } = await client
          .from("generation_tasks").select("portrait_url,style_url").in("id", taskIds).not("style_url", "is", null).limit(1);
        if (tasks && tasks.length > 0) styleUrl = tasks[0].style_url;
      }

      return {
        sub,
        imgs: imgs || [],
        styleUrl,
        facePassedCount: (imgs || []).filter(i => i.face_passed && i.status !== "ai_rejected").length
      };
    },
    // 图片画廊分组
    imageGroups: (list) => {
      const good = list.filter(i => i.face_passed && i.status !== "ai_rejected" && i.human_verdict == null);
      const aiRejected = list.filter(i => i.face_passed && i.status === "ai_rejected");
      const faceFailed = list.filter(i => !i.face_passed);
      return [
        good.length && { label: "通过", tag: "passed", items: good },
        aiRejected.length && { label: "AI味过重", tag: "ai-taste", items: aiRejected },
        faceFailed.length && { label: "人脸未通过", tag: "failed", items: faceFailed }
      ].filter(Boolean);
    },
    // 卡片额外 class
    cardClass: (img) => {
      if (!img.face_passed) return " face-failed";
      if (img.status === "ai_rejected") return " ai-rejected";
      if (img.human_verdict === "approved") return " passed";
      return "";
    },
    // 驳回按钮过滤：待审核且未被选中的图
    rejectFilter: (img) => img.face_passed && img.status !== "ai_rejected" && img.human_verdict == null && !selectedIds.has(img.id),
    // 驳回-全部过滤
    rejectAllFilter: (img) => img.face_passed && img.status !== "ai_rejected" && img.human_verdict == null,
    // 是否显示参考图
    hasRefImages: true,
    // 是否显示美感/距离 badge
    hasScoreBadges: true
  },

  nail: {
    label: "美甲",
    tasksQuery: async (client) => {
      const { data, error } = await client
        .from("generated_images")
        .select("id,persona_name,image_url,status,human_verdict,sub_requirement_id,batch_id,created_at")
        .like("batch_id", "nail_%")
        .order("created_at", { ascending: false });
      if (error) throw error;
      return data || [];
    },
    parseTasks: (rawData) => {
      const groups = {};
      for (const img of rawData) {
        const key = img.sub_requirement_id || "unlinked";
        if (!groups[key]) {
          groups[key] = { id: key, type: "nail", contentType: "nail", persona_name: img.persona_name || "未知", status: "pending", created_at: img.created_at, images: [] };
        }
        groups[key].images.push(img);
      }
      return Object.values(groups).map(g => {
        const pending = g.images.filter(i => i.human_verdict == null).length;
        return {
          id: g.id,
          type: "nail",
          contentType: "nail",
          persona_name: g.persona_name,
          status: g.status,
          created_at: g.created_at,
          generated_count: g.images.length,
          face_passed_count: g.images.filter(i => i.human_verdict === "approved").length,
          pending_review_count: pending
        };
      }).filter(t => t.pending_review_count === t.generated_count);
    },
    galleryQuery: async (client, subId) => {
      const { data: imgs, error } = await client
        .from("generated_images")
        .select("id,task_id,image_url,status,human_verdict,reviewed_at,batch_id,created_at")
        .eq("sub_requirement_id", subId === "unlinked" ? null : subId)
        .order("created_at", { ascending: false });
      if (error) throw error;
      return {
        sub: { id: subId, persona_name: (imgs || [])[0]?.persona_name || "美甲", status: "pending", draft_id: null, created_at: (imgs || [])[0]?.created_at || new Date().toISOString() },
        imgs: imgs || [],
        styleUrl: null,
        facePassedCount: (imgs || []).filter(i => i.human_verdict === "approved").length
      };
    },
    imageGroups: (list) => {
      // 只显示待审核图片，已审核的不显示（审核后应视为已处理）
      const pending = list.filter(i => i.human_verdict == null);
      return pending.length ? [{ label: "待审核", tag: "", items: pending }] : [];
    },
    cardClass: (img) => {
      if (img.human_verdict === "rejected") return " face-failed";
      if (img.human_verdict === "approved") return " passed";
      return "";
    },
    rejectFilter: (img) => img.human_verdict == null && !selectedIds.has(img.id),
    rejectAllFilter: (img) => img.human_verdict == null,
    hasRefImages: false,
    hasScoreBadges: false
  }
};

// ─── DOM refs ─────────────────────────────────────────────────
const statusEl = document.getElementById("status");
const connectBtn = document.getElementById("connect");
const urlInput = document.getElementById("supabase-url");
const keyInput = document.getElementById("supabase-key");
const configSection = document.getElementById("config");
const taskListSection = document.getElementById("task-list");
const taskItemsEl = document.getElementById("task-items");
const refreshTasksBtn = document.getElementById("refresh-tasks");
const tabContainer = document.getElementById("tab-container");
const gallerySection = document.getElementById("gallery");
const imageGrid = document.getElementById("image-grid");
const galleryTitle = document.getElementById("gallery-title");
const taskMetaEl = document.getElementById("task-meta");
const refImagesEl = document.getElementById("ref-images");
const backToListBtn = document.getElementById("back-to-list");
const lightbox = document.getElementById("lightbox");
const lightboxImage = document.getElementById("lightbox-image");
const lightboxClose = document.getElementById("lightbox-close");
const bottomBar = document.getElementById("bottom-bar");
const selectedCountEl = document.getElementById("selected-count");
const confirmBtn = document.getElementById("confirm-selection");
const rejectAllBtn = document.getElementById("reject-all");
const pageTitle = document.getElementById("page-title");
const pageSubtitle = document.getElementById("page-subtitle");

// ─── State ────────────────────────────────────────────────────
let currentSub = null;

const savedUrl = localStorage.getItem("supabaseUrl");
const savedKey = localStorage.getItem("supabaseAnonKey");
if (savedUrl) urlInput.value = savedUrl;
if (savedKey) keyInput.value = savedKey;

const urlParams = new URLSearchParams(window.location.search);
currentSubId = urlParams.get("sub");
currentTaskIdParam = urlParams.get("task");
const urlType = urlParams.get("type");
currentType = urlType || "all";

function setStatus(text, type = STATUS.DEFAULT) {
  statusEl.textContent = text;
  statusEl.className = type === STATUS.OK ? 'status ok'
                     : type === STATUS.ERROR ? 'status error'
                     : 'status';
}

function formatDate(iso) {
  if (!iso) return "--";
  const date = new Date(iso);
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Shanghai" }).format(date);
}

function showTaskList() {
  taskListSection.style.display = "";
  gallerySection.style.display = "none";
  bottomBar.style.display = "none";
  pageTitle.textContent = "生成图审核";
  pageSubtitle.textContent = "选择通过的内容图";
}

function showGallery() {
  taskListSection.style.display = "none";
  gallerySection.style.display = "";
  bottomBar.style.display = "";
}

function updateSelectedCount() {
  selectedCountEl.textContent = String(selectedIds.size);
  confirmBtn.disabled = selectedIds.size === 0;
}

// ─── Tab 渲染 ─────────────────────────────────────────────────
function renderTabs() {
  tabContainer.innerHTML = "";
  const types = [
    { key: "all", label: "全部" },
    { key: "face", label: "颜值" },
    { key: "nail", label: "美甲" }
  ];
  types.forEach(t => {
    const btn = document.createElement("button");
    btn.className = "tab-btn" + (currentType === t.key || (!currentType && t.key === "all") ? " active" : "");
    btn.textContent = t.label;
    btn.dataset.type = t.key;
    btn.addEventListener("click", () => {
      currentType = t.key;
      renderTabs();
      fetchTasks();
    });
    tabContainer.appendChild(btn);
  });
}

// ─── 任务列表 ─────────────────────────────────────────────────
async function fetchTasks() {
  if (!client) return;
  setStatus("正在加载任务...", "default");
  taskItemsEl.innerHTML = '<div class="skeleton" style="height: 100px;"></div><div class="skeleton" style="height: 100px;"></div>';
  selectedIds.clear();
  updateSelectedCount();

  try {
    let tasks = [];

    if (currentType === "all") {
      // 全部 = 颜值任务 + 美甲任务，各自解析后合并
      const [faceRaw, nailRaw] = await Promise.all([
        TYPE_HANDLERS.face.tasksQuery(client),
        TYPE_HANDLERS.nail.tasksQuery(client)
      ]);
      const faceTasks = TYPE_HANDLERS.face.parseTasks(faceRaw);
      const nailTasks = TYPE_HANDLERS.nail.parseTasks(nailRaw);
      tasks = [...faceTasks, ...nailTasks].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else {
      const handler = TYPE_HANDLERS[currentType];
      const raw = await handler.tasksQuery(client);
      tasks = handler.parseTasks(raw);
    }

    renderTaskList(tasks);
    setStatus(`已连接 · ${tasks.length} 个待审核`, "ok");
    showTaskList();
  } catch (err) {
    setStatus(`加载失败：${err.message}`, "error");
  }
}

function renderTaskList(tasks) {
  taskItemsEl.innerHTML = "";
  if (!tasks.length) {
    taskItemsEl.innerHTML = "<div class=\"task-meta\">暂无待审核任务</div>";
    return;
  }
  tasks.forEach(task => {
    const card = document.createElement("a");
    card.className = "task-card";
    const createdAt = formatDate(task.created_at);
    const isReviewed = task.status === "reviewed";
    const isNeedsRegen = task.status === "needs_regen";
    if (isReviewed) card.className += " reviewed";
    if (isNeedsRegen) card.className += " needs-regen";

    const typeLabel = task.contentType === "nail" ? "美甲" : "颜值";
    const typeClass = task.contentType === "nail" ? "type-nail" : "type-face";

    card.href = `?sub=${encodeURIComponent(task.id)}&type=${task.contentType}`;

    card.innerHTML = `
      <div class="task-top">
        <div class="task-name">${task.persona_name}</div>
        <div class="task-actions">
          <span class="type-badge ${typeClass}">${typeLabel}</span>
          <div class="task-status ${isNeedsRegen ? 'needs-regen' : isReviewed ? 'reviewed' : ''}">${isNeedsRegen ? '待重新生成' : isReviewed ? '已审核 ✓' : '待审核'}</div>
          <button class="task-delete-btn" data-task-id="${task.id}" data-task-type="${task.type}">删除</button>
        </div>
      </div>
      <div class="task-meta">
        <div class="task-counts">
          <span>生成 ${task.generated_count ?? 0}</span>
          <span>通过 ${task.face_passed_count ?? 0}</span>
        </div>
        <div>创建时间：${createdAt}</div>
      </div>
    `;

    card.querySelector(".task-delete-btn").addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      const name = task.persona_name;
      const count = task.generated_count ?? 0;
      if (!confirm(`确认删除「${name}」的任务记录？将同时删除 ${count} 张生成图。`)) return;
      const delBtn = card.querySelector(".task-delete-btn");
      delBtn.disabled = true;
      delBtn.textContent = "删除中...";
      try {
        if (task.contentType === "face" || task.type === "sub") {
          await client.from("generated_images").delete().eq("sub_requirement_id", task.id);
          await client.from("sub_requirement").update({ deleted_at: new Date().toISOString() }).eq("id", task.id);
        } else {
          await client.from("generated_images").delete().eq("sub_requirement_id", task.id);
        }
        card.style.transition = "opacity 0.3s, transform 0.3s";
        card.style.opacity = "0";
        card.style.transform = "translateX(-20px)";
        setTimeout(() => card.remove(), 300);
      } catch (err) {
        alert("删除失败：" + err.message);
        delBtn.disabled = false;
        delBtn.textContent = "删除";
      }
    });

    taskItemsEl.appendChild(card);
  });
}

// ─── 画廊 ─────────────────────────────────────────────────────
async function fetchGallery(subId) {
  if (!client) return;
  if (!subId) { fetchTasks(); return; }

  setStatus("正在加载...", "default");
  imageGrid.innerHTML = '<div class="skeleton" style="height: 220px; grid-column: 1 / -1;"></div><div class="skeleton" style="height: 220px;"></div>';

  try {
    // 从 URL 判断类型：nail 图的 batch_id 含 nail_
    let handler;
    if (currentType === "nail") {
      handler = TYPE_HANDLERS.nail;
    } else if (currentType === "face") {
      handler = TYPE_HANDLERS.face;
    } else {
      // "all" 模式下点击任务，根据 subId 判断类型
      // 如果该 sub_requirement 有 nail 图，走 nail handler
      const { data: probe } = await client
        .from("generated_images")
        .select("batch_id")
        .eq("sub_requirement_id", subId)
        .limit(1);
      const isNail = probe && probe.length > 0 && probe[0].batch_id && probe[0].batch_id.startsWith("nail_");
      handler = isNail ? TYPE_HANDLERS.nail : TYPE_HANDLERS.face;
    }

    const { sub, imgs, styleUrl, facePassedCount } = await handler.galleryQuery(client, subId);

    currentSub = {
      id: sub.id,
      persona_name: sub.persona_name,
      status: sub.status,
      draft_id: sub.draft_id,
      created_at: sub.created_at,
      generated_count: imgs.length,
      face_passed_count: facePassedCount,
      contentType: handler === TYPE_HANDLERS.nail ? "nail" : "face"
    };

    images = imgs;
    currentSubId = subId;
    galleryTitle.textContent = `图片画廊 · ${sub.persona_name}`;

    renderTaskMeta(currentSub);

    if (handler.hasRefImages) {
      renderRefImages(sub.persona_name, styleUrl);
    } else {
      refImagesEl.style.display = "none";
    }

    selectedIds.clear();
    updateSelectedCount();
    renderImages(images, handler);
    setStatus(`已加载 ${images.length} 张`, "ok");
    showGallery();
  } catch (err) {
    setStatus(`加载失败：${err.message}`, "error");
  }
}

// ─── 图片渲染 ─────────────────────────────────────────────────
function renderTaskMeta(task) {
  if (!task) { taskMetaEl.innerHTML = ""; return; }
  taskMetaEl.className = "badge-row";
  const typeLabel = task.contentType === "nail" ? "美甲" : "颜值";
  const typeClass = task.contentType === "nail" ? "type-nail" : "type-face";
  taskMetaEl.innerHTML = `
    <span class="type-badge ${typeClass}">${typeLabel}</span>
    <span class="badge">人物：${task.persona_name}</span>
    <span class="badge">生成 ${task.generated_count ?? 0}</span>
    <span class="badge">通过 ${task.face_passed_count ?? 0}</span>
    <span class="badge">创建 ${formatDate(task.created_at)}</span>
  `;
}

function renderRefImages(personaName, taskStyleUrl) {
  const PERSONA_REFS = {
    "先叫Momo": "https://img.meituan.net/dzusergrowthcontent/1141d96c336f309ca08a94b5c1bc26e81155511.png",
    "沐沐木有烦恼": "https://img.meituan.net/dzusergrowthcontent/0783f10c44757bb91f44b7db8b972663306584.jpg",
    "李慢慢曼妙": "https://img.meituan.net/dzusergrowthcontent/38b2f56baa655ea28ddcecaa7d63f4931364959.png",
    "一只小糕糕": "https://img.meituan.net/dzusergrowthcontent/987cb0ec713970b38ce121e915bdc718965767.png",
    "Momo不默默": "https://img.meituan.net/dzusergrowthcontent/82eefd3030cf510cca831343338db9c11178247.png",
    "小Lin晓晓": "https://img.meituan.net/dzusergrowthcontent/42e3679ecdab745d0aa424e83e2dd7d01103459.png",
    "乌拉拉": "https://img.meituan.net/dzusergrowthcontent/63f46da406965f6a6bbb9143d147c68c584044.png"
  };
  const portraitUrl = PERSONA_REFS[personaName] || "";
  const styleUrl = taskStyleUrl || portraitUrl;
  if (!portraitUrl) { refImagesEl.style.display = "none"; return; }
  refImagesEl.style.display = "";
  refImagesEl.innerHTML = '<div class="ref-header">参考图</div><div class="ref-grid">' +
    `<div class="ref-card"><img src="${portraitUrl}" alt="肖像参考" /><div class="ref-label">肖像参考</div></div>` +
    (styleUrl !== portraitUrl ? `<div class="ref-card"><img src="${styleUrl}" alt="风格参考" /><div class="ref-label">风格参考</div></div>` : '') +
    '</div>';
  refImagesEl.querySelectorAll("img").forEach(img => {
    img.addEventListener("click", () => {
      lightboxImage.src = img.src;
      lightbox.classList.add("show");
    });
  });
}

function renderImages(list, handler) {
  imageGrid.innerHTML = "";
  if (!list.length) { imageGrid.innerHTML = "<div class=\"task-meta\">暂无图片</div>"; return; }

  const groups = handler.imageGroups(list);
  groups.forEach(group => {
    const header = document.createElement("div");
    header.className = "grid-section-header";
    header.innerHTML = `<span class="section-tag ${group.tag}">${group.label}</span> ${group.items.length} 张`;
    imageGrid.appendChild(header);
    group.items.forEach(img => renderOneImage(img, handler));
  });
}

function renderOneImage(img, handler) {
  const card = document.createElement("div");
  card.className = "image-card" + handler.cardClass(img);
  if (selectedIds.has(img.id)) card.classList.add("selected");

  const imageEl = document.createElement("img");
  imageEl.src = img.image_url;
  imageEl.alt = img.id;
  imageEl.addEventListener("click", () => {
    lightboxImage.src = img.image_url;
    lightbox.classList.add("show");
  });

  const overlay = document.createElement("div");
  overlay.className = "image-overlay";

  if (handler.hasScoreBadges) {
    const score = document.createElement("div");
    score.className = "score-badge";
    score.textContent = `美感 ${typeof img.aesthetic_score === "number" ? img.aesthetic_score.toFixed(2) : "--"}`;
    const aiTaste = document.createElement("div");
    aiTaste.className = "ai-taste-badge";
    if (typeof img.ai_taste_score === "number") {
      aiTaste.textContent = `AI味 ${img.ai_taste_score}`;
      if (img.ai_taste_score >= 60) aiTaste.classList.add("high");
    }
    const distance = document.createElement("div");
    distance.className = "distance-text";
    distance.textContent = `距离 ${typeof img.face_distance === "number" ? img.face_distance.toFixed(3) : "--"}`;
    overlay.appendChild(score);
    overlay.appendChild(aiTaste);
    overlay.appendChild(document.createElement("div"));
    overlay.appendChild(distance);
  } else {
    // 美甲图显示 batch 信息
    const batchBadge = document.createElement("div");
    batchBadge.className = "score-badge";
    batchBadge.textContent = img.batch_id || "";
    overlay.appendChild(batchBadge);
  }

  const actions = document.createElement("div");
  actions.className = "image-actions";

  const previewBtn = document.createElement("button");
  previewBtn.className = "preview-btn";
  previewBtn.textContent = "预览";
  previewBtn.addEventListener("click", e => { e.stopPropagation(); lightboxImage.src = img.image_url; lightbox.classList.add("show"); });

  const checkboxWrap = document.createElement("label");
  checkboxWrap.className = "checkbox-wrap";
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = selectedIds.has(img.id);
  const checkboxText = document.createElement("span");
  checkboxText.textContent = "选择";
  checkbox.addEventListener("change", () => {
    if (checkbox.checked) { selectedIds.add(img.id); card.classList.add("selected"); }
    else { selectedIds.delete(img.id); card.classList.remove("selected"); }
    updateSelectedCount();
  });
  checkboxWrap.appendChild(checkbox);
  checkboxWrap.appendChild(checkboxText);
  actions.appendChild(previewBtn);
  actions.appendChild(checkboxWrap);

  card.appendChild(imageEl);
  card.appendChild(overlay);
  card.appendChild(actions);
  imageGrid.appendChild(card);
}

// ─── 审核操作 ─────────────────────────────────────────────────
async function confirmSelection() {
  if (!client) { setStatus("未连接到 Supabase", "error"); return; }
  if (!currentSub) { setStatus("未选择任务", "error"); return; }
  if (selectedIds.size === 0) { setStatus("请先选择至少一张图片", "error"); return; }

  const handler = currentSub.contentType === "nail" ? TYPE_HANDLERS.nail : TYPE_HANDLERS.face;
  confirmBtn.disabled = true;
  confirmBtn.textContent = "提交中...";
  setStatus("正在提交选择...", "default");

  const imageIdArray = Array.from(selectedIds);
  const now = new Date().toISOString();

  const { error: approveError } = await client
    .from("generated_images")
    .update({ human_verdict: "approved", reviewed_at: now })
    .in("id", imageIdArray);

  if (approveError) {
    setStatus(`更新图片失败：${approveError.message}`, "error");
    confirmBtn.disabled = false;
    confirmBtn.textContent = "确认选择";
    return;
  }

  const rejectedIds = images.filter(img => handler.rejectFilter(img)).map(img => img.id);
  if (rejectedIds.length > 0) {
    await client.from("generated_images").update({ human_verdict: "rejected", reviewed_at: now }).in("id", rejectedIds);
  }

  setStatus("审核完成 ✓", "ok");
  confirmBtn.textContent = "已完成";
  // 标记已审核的图片不显示
  images = images.map(img => {
    if (imageIdArray.includes(img.id)) {
      return { ...img, human_verdict: "approved" };
    }
    return img;
  });
  renderImages(images, handler);
  selectedIds.clear();
  updateSelectedCount();
  // 更新任务列表中的计数（不跳转）
  const taskCard = document.querySelector(`.task-card[data-task-id="${currentSubId}"]`);
  if (taskCard) {
    const pendingCount = images.filter(img => handler.rejectFilter(img)).length;
    const passedCount = images.filter(img => img.human_verdict === "approved").length;
    const countEl = taskCard.querySelector(".task-counts");
    if (countEl) countEl.innerHTML = `<span>生成 ${images.length}</span><span>通过 ${passedCount}</span>`;
    if (pendingCount === 0) {
      taskCard.style.opacity = "0.4";
      taskCard.style.pointerEvents = "none";
      setTimeout(() => { window.location.href = window.location.pathname + "?type=" + currentType; }, 800);
    }
  }
}

rejectAllBtn.addEventListener("click", async () => {
  if (!client) { setStatus("未连接到 Supabase", "error"); return; }
  if (!currentSub) { setStatus("未选择任务", "error"); return; }
  if (!confirm("确认全部不合格？将标记所有待审核图片为拒绝。")) return;

  const handler = currentSub.contentType === "nail" ? TYPE_HANDLERS.nail : TYPE_HANDLERS.face;
  rejectAllBtn.disabled = true;
  rejectAllBtn.textContent = "处理中...";
  setStatus("正在标记全部不合格...", "default");

  const now = new Date().toISOString();
  const allIds = images.filter(img => handler.rejectAllFilter(img)).map(img => img.id);
  if (allIds.length > 0) {
    await client.from("generated_images").update({ human_verdict: "rejected", reviewed_at: now }).in("id", allIds);
  }

  setStatus("已标记全部不合格 ✓", "ok");
  rejectAllBtn.textContent = "已标记";
  // 标记已审核的图片不显示
  images = images.map(img => {
    if (allIds.includes(img.id)) {
      return { ...img, human_verdict: "rejected" };
    }
    return img;
  });
  renderImages(images, handler);
  // 更新任务列表
  const taskCard = document.querySelector(`.task-card[data-task-id="${currentSubId}"]`);
  if (taskCard) {
    const pendingCount = images.filter(img => handler.rejectFilter(img)).length;
    if (pendingCount === 0) {
      taskCard.style.opacity = "0.4";
      taskCard.style.pointerEvents = "none";
      setTimeout(() => { window.location.href = window.location.pathname + "?type=" + currentType; }, 800);
    }
  }
});

// ─── 事件绑定 ─────────────────────────────────────────────────
refreshTasksBtn.addEventListener("click", fetchTasks);
backToListBtn.addEventListener("click", () => {
  window.location.href = window.location.pathname + (currentType && currentType !== "all" ? "?type=" + currentType : "");
});
lightboxClose.addEventListener("click", () => lightbox.classList.remove("show"));
lightbox.addEventListener("click", e => { if (e.target === lightbox) lightbox.classList.remove("show"); });
confirmBtn.addEventListener("click", confirmSelection);

async function initConnection(url, key, isAuto = false) {
  if (!url || !key) { setStatus("请输入 Supabase 地址和匿名密钥", STATUS.ERROR); return false; }
  setStatus(isAuto ? "正在自动连接..." : "正在连接...", STATUS.DEFAULT);
  if (!isAuto) connectBtn.disabled = true;

  try {
    client = supabase.createClient(url, key);
    localStorage.setItem("supabaseUrl", url);
    localStorage.setItem("supabaseAnonKey", key);
    configSection.style.display = "none";

    // 初始化 tab 状态
    const urlType = new URLSearchParams(window.location.search).get("type");
    currentType = urlType || "all";
    renderTabs();

    if (currentSubId) {
      await fetchGallery(currentSubId);
    } else {
      await fetchTasks();
    }
    return true;
  } catch (err) {
    setStatus(`连接失败: ${err.message}`, STATUS.ERROR);
    client = null;
    return false;
  } finally {
    if (!isAuto) connectBtn.disabled = false;
  }
}

connectBtn.addEventListener("click", () => initConnection(urlInput.value.trim(), keyInput.value.trim(), false));

const defaults = window.SUPABASE_DEFAULTS || {};
if (savedUrl || defaults.url) urlInput.value = savedUrl || defaults.url;
if (savedKey || defaults.anonKey) keyInput.value = savedKey || defaults.anonKey;

if (urlInput.value && keyInput.value) {
  initConnection(urlInput.value.trim(), keyInput.value.trim(), true);
} else {
  setStatus("请填写 Supabase 连接信息", STATUS.DEFAULT);
  renderTabs();
  showTaskList();
}
