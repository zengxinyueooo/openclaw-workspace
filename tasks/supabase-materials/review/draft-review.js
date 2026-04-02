const state = {
  client: null,
  drafts: [],
  draft: null,
  images: [],
  imageOrder: [],
  selectedCoverId: null,
  selectedTitleIndex: 0,
  customTitle: "",
  selectedContentIndex: 0,
  contentEdits: [],
  selectedTags: new Set(),
  accountOptions: [],
  selectedAccountId: "",
  scheduledAt: "",
  isLoading: false
};

const el = {
  status: document.getElementById("status"),
  config: document.getElementById("config"),
  supabaseUrl: document.getElementById("supabase-url"),
  supabaseKey: document.getElementById("supabase-key"),
  connect: document.getElementById("connect"),
  draftList: document.getElementById("draft-list"),
  draftItems: document.getElementById("draft-items"),
  refreshDrafts: document.getElementById("refresh-drafts"),
  draftEditor: document.getElementById("draft-editor"),
  editorTitle: document.getElementById("editor-title"),
  draftMeta: document.getElementById("draft-meta"),
  imageList: document.getElementById("image-list"),
  imageCount: document.getElementById("image-count"),
  titleOptions: document.getElementById("title-options"),
  customTitle: document.getElementById("custom-title"),
  contentTabs: document.getElementById("content-tabs"),
  contentEditor: document.getElementById("content-editor"),
  tagOptions: document.getElementById("tag-options"),
  // accountSelect/accountCustom/scheduledAt removed
  backToList: document.getElementById("back-to-list"),
  reloadDraft: document.getElementById("reload-draft"),
  lightbox: document.getElementById("lightbox"),
  lightboxImage: document.getElementById("lightbox-image"),
  lightboxClose: document.getElementById("lightbox-close"),
  bottomBar: document.getElementById("bottom-bar"),
  bottomStatus: document.getElementById("bottom-status"),
  approveDraft: document.getElementById("approve-draft"),
  deleteDraft: document.getElementById("delete-draft")
};

const queryDraftId = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get("draft");
};

const setStatus = (text, tone = "default") => {
  el.status.textContent = text;
  el.status.className = 'status';
  if (tone === "ok") el.status.classList.add('ok');
  if (tone === "error") el.status.classList.add('error');
};

const formatTime = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false, timeZone: "Asia/Shanghai" });
};

const toDatetimeLocal = (value) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (num) => String(num).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

const fromDatetimeLocal = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
};

const initConfig = () => {
  const defaults = window.SUPABASE_DEFAULTS || {};
  const saved = JSON.parse(localStorage.getItem("draftReviewConfig") || "{}");
  // 如果默认 URL 变了，清掉旧缓存，避免连错库
  if (defaults.url && saved.url && saved.url !== defaults.url) {
    localStorage.removeItem("draftReviewConfig");
    el.supabaseUrl.value = defaults.url;
    el.supabaseKey.value = defaults.anonKey || "";
    return;
  }
  el.supabaseUrl.value = saved.url || defaults.url || "";
  el.supabaseKey.value = saved.key || defaults.anonKey || "";
};

const saveConfig = () => {
  localStorage.setItem(
    "draftReviewConfig",
    JSON.stringify({
      url: el.supabaseUrl.value.trim(),
      key: el.supabaseKey.value.trim()
    })
  );
};

const connectSupabase = async () => {
  const url = el.supabaseUrl.value.trim();
  const key = el.supabaseKey.value.trim();
  if (!url || !key) {
    setStatus("请先填写配置", "error");
    return;
  }
  const { createClient } = window.supabase;
  state.client = createClient(url, key);
  saveConfig();
  setStatus("已连接", "ok");
  el.config.style.display = "none";
  const draftId = queryDraftId();
  if (draftId) {
    await loadDraftEditor(draftId);
  } else {
    await loadDraftList();
  }
};

const loadDraftList = async () => {
  if (!state.client) return;
  el.draftEditor.style.display = "none";
  el.bottomBar.style.display = "none";
  el.draftList.style.display = "block";
  el.draftItems.innerHTML = "";
  setStatus("加载草稿中...");

  const { data, error } = await state.client
    .from("note_drafts")
    .select("id, persona_name, image_ids, status, created_at")
    .in("status", ["content_ready", "draft"])
    .order("created_at", { ascending: false });

  if (error) {
    setStatus("加载失败", "error");
    el.draftItems.innerHTML = `<div class="draft-card disabled">${error.message}</div>`;
    return;
  }

  state.drafts = data || [];
  if (!state.drafts.length) {
    el.draftItems.innerHTML = "<div class=\"draft-card disabled\">暂无草稿</div>";
  }

  el.draftItems.innerHTML = state.drafts
    .map((draft) => {
      const imageCount = Array.isArray(draft.image_ids) ? draft.image_ids.length : 0;
      const hasContent = draft.status === "content_ready" || draft.status === "draft";
      const statusText = draft.status === "content_ready" ? "可终审" : draft.status === "draft" ? "草稿" : draft.status;
      const cardClass = hasContent ? "draft-card" : "draft-card disabled";
      const href = hasContent ? `?draft=${draft.id}` : "#";
      return `
        <a class="${cardClass}" href="${href}">
          <div class="draft-top">
            <div class="draft-name">${draft.persona_name || "未命名"}</div>
            <div class="draft-status ${draft.status === "draft" ? "draft" : ""}">${statusText}</div>
          </div>
          <div class="draft-meta">
            <div class="draft-badges">
              <span>图片 ${imageCount} 张</span>
              <span>状态 ${draft.status}</span>
            </div>
            <div>创建时间 ${formatTime(draft.created_at)}</div>
          </div>
        </a>
      `;
    })
    .join("");

  setStatus("草稿已加载", "ok");
};

const loadDraftEditor = async (draftId) => {
  if (!state.client) return;
  el.draftList.style.display = "none";
  el.draftEditor.style.display = "block";
  el.bottomBar.style.display = "block";
  setStatus("加载草稿中...");

  const { data, error } = await state.client
    .from("note_drafts")
    .select("*")
    .eq("id", draftId)
    .single();

  if (error) {
    setStatus("草稿加载失败", "error");
    el.draftEditor.style.display = "none";
    el.bottomBar.style.display = "none";
    return;
  }

  state.draft = data;
  await loadImages(data.image_ids || []);
  await loadAccounts();
  hydrateEditor();
  setStatus("草稿已加载", "ok");
};

const loadImages = async (imageIds) => {
  if (!state.client) return;
  if (!imageIds.length) {
    state.images = [];
    state.imageOrder = [];
    return;
  }
  const { data, error } = await state.client
    .from("generated_images")
    .select("id, image_url, local_path, status, aesthetic_score")
    .in("id", imageIds);

  if (error) {
    console.warn(error);
    state.images = [];
    state.imageOrder = [...imageIds];
    return;
  }
  const imageMap = new Map((data || []).map((img) => [img.id, img]));
  state.images = imageIds
    .map((id) => imageMap.get(id))
    .filter(Boolean);
  state.imageOrder = [...imageIds];
};

const loadAccounts = async () => {
  if (!state.client) return;
  state.accountOptions = [];
  let error = null;
  let data = null;
  try {
    let result = null;
    if (typeof state.client.schema === "function") {
      result = await state.client.schema("shared").from("accounts").select("id, name");
    } else {
      result = await state.client.from("shared.accounts").select("id, name");
    }
    error = result?.error;
    data = result?.data;
  } catch (err) {
    error = err;
  }

  if (error || !Array.isArray(data)) {
    state.accountOptions = [];
  } else {
    state.accountOptions = data;
  }
};

const hydrateEditor = () => {
  const draft = state.draft;
  if (!draft) return;

  el.editorTitle.textContent = `草稿终审 · ${draft.persona_name || ""}`;
  el.draftMeta.innerHTML = `
    <div class="draft-meta">
      <div>草稿 ID ${draft.id}</div>
      <div>当前状态 ${draft.status}</div>
      <div>创建时间 ${formatTime(draft.created_at)}</div>
      <div>最近更新 ${formatTime(draft.updated_at)}</div>
    </div>
  `;

  const candidateTitles = Array.isArray(draft.candidate_titles) ? draft.candidate_titles : [];
  const candidateContents = Array.isArray(draft.candidate_contents) ? draft.candidate_contents : [];
  const candidateTags = Array.isArray(draft.candidate_tags) ? draft.candidate_tags : [];

  state.selectedTitleIndex = 0;
  state.customTitle = "";
  el.customTitle.value = "";
  if (draft.title && !candidateTitles.includes(draft.title)) {
    state.customTitle = draft.title;
    el.customTitle.value = draft.title;
  }

  el.titleOptions.innerHTML = candidateTitles
    .map((title, index) => {
      const checked = draft.title ? draft.title === title : index === 0;
      if (checked) {
        state.selectedTitleIndex = index;
      }
      return `
        <label class="option-item">
          <input type="radio" name="title" value="${index}" ${checked ? "checked" : ""} />
          <span class="option-text">${title}</span>
        </label>
      `;
    })
    .join("");

  if (!candidateTitles.length) {
    el.titleOptions.innerHTML = "<div class=\"muted\">暂无候选标题</div>";
  }

  state.selectedContentIndex = 0;
  state.contentEdits = candidateContents.map((item) => item || "");
  if (!candidateContents.length) {
    state.contentEdits = [draft.content || ""];
  }

  el.contentTabs.innerHTML = state.contentEdits
    .map((_, index) => {
      const active = index === 0 ? "active" : "";
      return `<button type="button" class="tab ${active}" data-index="${index}">版本 ${index + 1}</button>`;
    })
    .join("");

  if (!state.contentEdits.length) {
    el.contentTabs.innerHTML = "";
  }

  el.contentEditor.value = state.contentEdits[state.selectedContentIndex] || draft.content || "";

  // 话题标签：优先用 candidate_tags，没有就用 tags
  const allTags = candidateTags.length ? candidateTags : (Array.isArray(draft.tags) ? draft.tags : []);
  state.selectedTags = new Set(draft.tags || allTags || []);
  el.tagOptions.innerHTML = allTags
    .map((tag) => {
      const checked = state.selectedTags.has(tag) ? "checked" : "";
      return `
        <label class="tag-chip">
          <input type="checkbox" value="${tag}" ${checked} />
          <span>${tag}</span>
        </label>
      `;
    })
    .join("");

  if (!allTags.length) {
    el.tagOptions.innerHTML = "<div class=\"muted\">暂无候选话题</div>";
  }

  // 配图建议/分镜文案（颜值类不显示）
  const imageNotesEl = document.getElementById("image-notes");
  const imageNotesField = imageNotesEl ? imageNotesEl.closest(".field") : null;
  if (imageNotesEl) {
    const imageNotes = candidateContents.length > 1 ? candidateContents[1] : null;
    if (imageNotes) {
      imageNotesEl.innerHTML = `<div class="image-notes-content">${imageNotes.replace(/\n/g, "<br>")}</div>`;
      if (imageNotesField) imageNotesField.style.display = "";
    } else {
      imageNotesEl.innerHTML = "";
      if (imageNotesField) imageNotesField.style.display = "none";
    }
  }

  if (draft.cover_image_id) {
    state.selectedCoverId = draft.cover_image_id;
  } else if (state.imageOrder.length) {
    state.selectedCoverId = state.imageOrder[0];
  }

  renderImages();
  updateBottomStatus();
};

const renderImages = () => {
  const imageMap = new Map(state.images.map((img) => [img.id, img]));
  const ordered = state.imageOrder
    .map((id) => imageMap.get(id))
    .filter(Boolean);
  el.imageList.innerHTML = ordered
    .map((img, index) => {
      const url = img.image_url || img.local_path || "";
      const isCover = state.selectedCoverId === img.id;
      return `
        <div class="image-card" draggable="true" data-id="${img.id}" data-index="${index}">
          <img src="${url}" alt="预览" />
          <div class="image-overlay">
            <div class="image-badges">
              <span class="badge">#${index + 1}</span>
              <span class="badge ${isCover ? "cover" : ""}">${isCover ? "封面" : "点击设封面"}</span>
            </div>
            <div></div>
            <div class="image-actions">
              <button type="button" data-action="preview" data-id="${img.id}">放大</button>
              <button type="button" data-action="cover" data-id="${img.id}">设为封面</button>
              <button type="button" data-action="delete" data-id="${img.id}" class="danger-btn">删除</button>
            </div>
          </div>
        </div>
      `;
    })
    .join("");

  el.imageCount.textContent = `${ordered.length} 张`;
  bindImageInteractions();
};

const bindImageInteractions = () => {
  const cards = Array.from(el.imageList.querySelectorAll(".image-card"));
  cards.forEach((card) => {
    card.addEventListener("dragstart", handleDragStart);
    card.addEventListener("dragover", handleDragOver);
    card.addEventListener("drop", handleDrop);
  });

  el.imageList.querySelectorAll("button[data-action='preview']").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      const id = btn.dataset.id;
      const img = state.images.find((item) => item.id === id);
      if (img) showLightbox(img.image_url || img.local_path || "");
    });
  });

  el.imageList.querySelectorAll("button[data-action='cover']").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      const id = btn.dataset.id;
      state.selectedCoverId = id;
      renderImages();
    });
  });

  el.imageList.querySelectorAll("button[data-action='delete']").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      const id = btn.dataset.id;
      state.imageOrder = state.imageOrder.filter((imgId) => imgId !== id);
      state.images = state.images.filter((img) => img.id !== id);
      if (state.selectedCoverId === id) {
        state.selectedCoverId = state.imageOrder[0] || null;
      }
      renderImages();
      updateBottomStatus();
    });
  });

  el.imageList.querySelectorAll(".image-badges").forEach((badgeRow) => {
    badgeRow.addEventListener("click", (event) => {
      const card = event.currentTarget.closest(".image-card");
      if (!card) return;
      state.selectedCoverId = card.dataset.id;
      renderImages();
    });
  });
};

let draggedId = null;

const handleDragStart = (event) => {
  draggedId = event.currentTarget.dataset.id;
  event.dataTransfer.effectAllowed = "move";
};

const handleDragOver = (event) => {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
};

const handleDrop = (event) => {
  event.preventDefault();
  const targetId = event.currentTarget.dataset.id;
  if (!draggedId || draggedId === targetId) return;
  const current = [...state.imageOrder];
  const fromIndex = current.indexOf(draggedId);
  const toIndex = current.indexOf(targetId);
  if (fromIndex === -1 || toIndex === -1) return;
  current.splice(fromIndex, 1);
  current.splice(toIndex, 0, draggedId);
  state.imageOrder = current;
  if (!state.selectedCoverId && state.imageOrder.length) {
    state.selectedCoverId = state.imageOrder[0];
  }
  renderImages();
};

const showLightbox = (url) => {
  el.lightboxImage.src = url;
  el.lightbox.classList.add("show");
};

const hideLightbox = () => {
  el.lightbox.classList.remove("show");
  el.lightboxImage.src = "";
};

const updateBottomStatus = () => {
  const title = getSelectedTitle();
  const content = getSelectedContent();
  const tags = getSelectedTags();
  el.bottomStatus.textContent = `标题 ${title ? "已选" : "未选"} · 正文 ${content ? "已填" : "未填"} · 话题 ${tags.length} 个`;
};

const getSelectedTitle = () => {
  if (state.customTitle.trim()) return state.customTitle.trim();
  const titles = Array.isArray(state.draft?.candidate_titles) ? state.draft.candidate_titles : [];
  return titles[state.selectedTitleIndex] || "";
};

const getSelectedContent = () => {
  return (state.contentEdits[state.selectedContentIndex] || "").trim();
};

const getSelectedTags = () => Array.from(state.selectedTags);

const handleTitleChange = (event) => {
  const value = Number(event.target.value);
  if (Number.isNaN(value)) return;
  state.selectedTitleIndex = value;
  updateBottomStatus();
};

const handleCustomTitleInput = () => {
  state.customTitle = el.customTitle.value;
  updateBottomStatus();
};

const handleContentTabClick = (event) => {
  const button = event.target.closest(".tab");
  if (!button) return;
  const index = Number(button.dataset.index);
  if (Number.isNaN(index)) return;
  state.contentEdits[state.selectedContentIndex] = el.contentEditor.value;
  state.selectedContentIndex = index;
  el.contentEditor.value = state.contentEdits[index] || "";
  el.contentTabs.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", Number(tab.dataset.index) === index);
  });
  updateBottomStatus();
};

const handleContentInput = () => {
  state.contentEdits[state.selectedContentIndex] = el.contentEditor.value;
  updateBottomStatus();
};

const handleTagChange = (event) => {
  const checkbox = event.target;
  if (!checkbox || !checkbox.value) return;
  if (checkbox.checked) {
    state.selectedTags.add(checkbox.value);
  } else {
    state.selectedTags.delete(checkbox.value);
  }
  updateBottomStatus();
};

const getSelectedAccount = () => "";

const handleApprove = async () => {
  if (!state.client || !state.draft) return;
  if (state.isLoading) return;
  state.isLoading = true;
  el.approveDraft.disabled = true;

  const payload = {
    status: "approved",
    title: getSelectedTitle(),
    content: getSelectedContent(),
    tags: getSelectedTags(),
    cover_image_id: state.selectedCoverId || null,
    image_ids: state.imageOrder.length ? state.imageOrder : state.draft.image_ids,
    account_id: null,
    scheduled_at: null
  };

  const { error } = await state.client
    .from("note_drafts")
    .update(payload)
    .eq("id", state.draft.id);

  if (error) {
    setStatus("保存失败", "error");
    state.isLoading = false;
    el.approveDraft.disabled = false;
  } else {
    setStatus("已通过 ✅ 正在返回列表...", "ok");
    setTimeout(() => {
      window.location.href = window.location.pathname;
    }, 800);
  }
};

const handleDelete = async () => {
  if (!state.client || !state.draft) return;
  if (state.isLoading) return;
  if (!confirm(`确定要删除这条草稿吗？\n\n「${state.draft.title || state.draft.persona_name || '未命名'}」\n\n删除后不可恢复。`)) return;
  state.isLoading = true;
  el.deleteDraft.disabled = true;

  const { error } = await state.client
    .from("note_drafts")
    .delete()
    .eq("id", state.draft.id);

  if (error) {
    setStatus("删除失败: " + error.message, "error");
  } else {
    setStatus("已删除", "ok");
    window.location.href = window.location.pathname;
    return;
  }

  state.isLoading = false;
  el.deleteDraft.disabled = false;
};

el.connect.addEventListener("click", connectSupabase);
el.refreshDrafts.addEventListener("click", loadDraftList);
el.backToList.addEventListener("click", () => {
  window.location.href = window.location.pathname;
});
el.reloadDraft.addEventListener("click", () => {
  if (state.draft) loadDraftEditor(state.draft.id);
});
el.lightboxClose.addEventListener("click", hideLightbox);
el.lightbox.addEventListener("click", (event) => {
  if (event.target === el.lightbox) hideLightbox();
});
el.titleOptions.addEventListener("change", handleTitleChange);
el.customTitle.addEventListener("input", handleCustomTitleInput);
el.contentTabs.addEventListener("click", handleContentTabClick);
el.contentEditor.addEventListener("input", handleContentInput);
el.tagOptions.addEventListener("change", handleTagChange);
el.approveDraft.addEventListener("click", handleApprove);
el.deleteDraft.addEventListener("click", handleDelete);

const customTagInput = document.getElementById("custom-tag");
const addTagBtn = document.getElementById("add-tag");

const addCustomTag = () => {
  const raw = customTagInput.value.trim();
  if (!raw) return;
  const tag = raw.startsWith("#") ? raw : `#${raw}`;
  if (state.selectedTags.has(tag)) {
    customTagInput.value = "";
    return;
  }
  state.selectedTags.add(tag);
  // append a new chip to the tag options
  const label = document.createElement("label");
  label.className = "tag-chip";
  label.innerHTML = `<input type="checkbox" value="${tag}" checked /><span>${tag}</span>`;
  label.querySelector("input").addEventListener("change", (e) => {
    if (e.target.checked) state.selectedTags.add(tag);
    else state.selectedTags.delete(tag);
    updateBottomStatus();
  });
  el.tagOptions.appendChild(label);
  customTagInput.value = "";
  updateBottomStatus();
};

addTagBtn.addEventListener("click", addCustomTag);
customTagInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    addCustomTag();
  }
});

initConfig();
connectSupabase();
