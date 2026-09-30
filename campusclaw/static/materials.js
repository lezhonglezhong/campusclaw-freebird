const userContext = document.querySelector("#user-context");
const status = document.querySelector("#workspace-status");
const list = document.querySelector("#material-list");
const detail = document.querySelector("#material-detail");
const detailFields = document.querySelector("#material-detail-fields");
const detailActions = document.querySelector("#material-actions");
const teacherUpload = document.querySelector("#teacher-upload");
const searchForm = document.querySelector("#material-search-form");
const retrievalForm = document.querySelector("#content-retrieval-form");
const retrievalResults = document.querySelector("#content-retrieval-results");
const retrievalStatus = document.querySelector("#retrieval-status");
const askForm = document.querySelector("#ask-form");
const askStatus = document.querySelector("#ask-status");
const askAnswer = document.querySelector("#ask-answer");
const askCitations = document.querySelector("#ask-citations");
const teacherIndexing = document.querySelector("#teacher-indexing");
const indexingTemplate = document.querySelector("#teacher-indexing-template");
const auth = window.CampusClawAuth;
const request = auth.request;
let currentUser;
let retrievalRequestId = 0;
let askRequestId = 0;

function roleLabel(role) {
  return { teacher: "教师", student: "学生" }[role] || role;
}

function materialStatusLabel(value) {
  return { ready: "已入库" }[value] || value;
}

function clearProtectedView() {
  retrievalRequestId += 1;
  askRequestId += 1;
  currentUser = undefined;
  userContext.textContent = "";
  list.replaceChildren();
  detailFields.replaceChildren();
  detailActions.replaceChildren();
  retrievalResults.replaceChildren();
  retrievalStatus.textContent = "";
  askStatus.textContent = "";
  askAnswer.textContent = "";
  askAnswer.hidden = true;
  askCitations.replaceChildren();
  teacherUpload.replaceChildren();
  teacherUpload.hidden = true;
  teacherIndexing.replaceChildren();
  teacherIndexing.hidden = true;
  detail.hidden = true;
}

window.addEventListener("campusclaw:unauthorized", clearProtectedView);

function downloadFilename(response, fallbackName) {
  const disposition = response.headers.get("Content-Disposition") || "";
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (encoded) {
    try {
      return decodeURIComponent(encoded[1]);
    } catch {
      return fallbackName;
    }
  }
  const quoted = disposition.match(/filename="([^"]+)"/i);
  return quoted ? quoted[1] : fallbackName;
}

async function downloadMaterial(url, fallbackName) {
  const response = await request(url);
  if (!response.ok) throw new Error("download_failed");
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = downloadFilename(response, fallbackName);
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

function showDetail(material) {
  detailFields.replaceChildren();
  detailActions.replaceChildren();
  for (const [label, value] of Object.entries({
    "材料编号": material.id,
    "材料名称": material.display_name,
    "班级": material.class_name,
    "上传者编号": material.uploader_id,
    "入库状态": materialStatusLabel(material.status),
  })) {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = String(value);
    detailFields.append(term, description);
  }
  const download = document.createElement("button");
  download.type = "button";
  download.textContent = "下载材料";
  download.addEventListener("click", async () => {
    download.disabled = true;
    try {
      await downloadMaterial(`/api/materials/${material.id}/download`, material.display_name);
    } catch (error) {
      if (error.message !== "unauthorized") status.textContent = "下载材料失败，请稍后重试。";
    } finally {
      download.disabled = false;
    }
  });
  detailActions.append(download);
  if (currentUser.role === "teacher") {
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "删除材料";
    remove.addEventListener("click", async () => {
      if (!window.confirm(`确定删除“${material.display_name}”吗？`)) return;
      remove.disabled = true;
      try {
        const response = await request(`/api/materials/${material.id}`, { method: "DELETE" });
        if (response.status === 204) {
          detail.hidden = true;
          await loadMaterials();
          status.textContent = "材料已删除。";
        } else if (response.status === 403) {
          status.textContent = "你没有删除材料的权限。";
        } else {
          status.textContent = "删除材料失败，请稍后重试。";
        }
      } catch (error) {
        if (error.message !== "unauthorized") status.textContent = "删除材料失败，请稍后重试。";
      } finally {
        remove.disabled = false;
      }
    });
    detailActions.append(" ", remove);
  }
  detail.hidden = false;
}

async function loadDetail(id) {
  status.textContent = "正在加载材料…";
  detail.hidden = true;
  try {
    const response = await request(`/api/materials/${id}`);
    if (response.status === 404) {
      status.textContent = "该材料已不存在或无权访问。";
      return;
    }
    if (!response.ok) throw new Error("detail_failed");
    showDetail((await response.json()).material);
    status.textContent = "";
  } catch (error) {
    if (error.message !== "unauthorized") status.textContent = "无法加载材料详情，请稍后重试。";
  }
}

async function loadMaterials(query = "") {
  const response = query
    ? await request(`/api/materials?${new URLSearchParams({ q: query })}`)
    : await request("/api/materials");
  if (!response.ok) throw new Error("list_failed");
  const { materials } = await response.json();
  list.replaceChildren();
  for (const material of materials) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${material.display_name} · ${materialStatusLabel(material.status)}`;
    button.addEventListener("click", () => loadDetail(material.id));
    item.append(button);
    list.append(item);
  }
  const reindexMaterial = teacherIndexing.querySelector("#reindex-material");
  if (reindexMaterial) {
    reindexMaterial.replaceChildren();
    for (const material of materials) {
      const option = document.createElement("option");
      option.value = String(material.id);
      option.textContent = material.display_name;
      reindexMaterial.append(option);
    }
  }
  if (!materials.length) status.textContent = query ? "未找到名称匹配的材料。" : "当前班级暂无材料。";
}

function renderTeacherIndexing(user) {
  if (user.role !== "teacher") return;
  teacherIndexing.replaceChildren(indexingTemplate.content.cloneNode(true));
  teacherIndexing.hidden = false;
  const form = teacherIndexing.querySelector("#reindex-form");
  const strategy = form.elements.strategy;
  const custom = teacherIndexing.querySelector("#custom-chunk-options");
  const reindexStatus = teacherIndexing.querySelector("#reindex-status");
  strategy.addEventListener("change", () => {
    custom.hidden = strategy.value !== "custom";
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const materialId = Number(form.elements.material_id.value);
    if (!Number.isInteger(materialId) || materialId < 1) {
      reindexStatus.textContent = "请先选择材料。";
      return;
    }
    const options = strategy.value === "custom" ? {
      max_length: Number(form.elements.max_length.value),
      overlap_percent: Number(form.elements.overlap_percent.value),
      separator: form.elements.separator.value,
      remove_urls: form.elements.remove_urls.checked,
      remove_emails: form.elements.remove_emails.checked,
      collapse_whitespace: form.elements.collapse_whitespace.checked,
    } : {};
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    reindexStatus.textContent = "正在重建索引…";
    try {
      const response = await request(`/api/materials/${materialId}/reindex`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ strategy: strategy.value, options }),
      });
      if (response.ok) {
        const result = await response.json();
        reindexStatus.textContent = result.vector_status === "ready"
          ? `已重建 ${result.chunk_count} 个切片。`
          : `已生成 ${result.chunk_count} 个文本切片；语义索引暂不可用。`;
      } else if (response.status === 400) {
        reindexStatus.textContent = "切片参数无效，请检查后重试。";
      } else if (response.status === 403) {
        reindexStatus.textContent = "你没有重建索引的权限。";
      } else if (response.status === 404) {
        reindexStatus.textContent = "材料已不存在或无权访问。";
      } else {
        reindexStatus.textContent = "重建索引失败，请稍后重试。";
      }
    } catch (error) {
      if (error.message !== "unauthorized") reindexStatus.textContent = "重建索引失败，请稍后重试。";
    } finally {
      button.disabled = false;
    }
  });
}

function renderTeacherUpload(user) {
  if (user.role !== "teacher") return;
  teacherUpload.hidden = false;
  teacherUpload.innerHTML = `
    <h2 id="upload-title">上传材料</h2>
    <form id="text-upload-form" novalidate>
      <h3>直接输入文字</h3>
      <label for="display-name">材料名称</label>
      <input id="display-name" name="display_name" required>
      <label for="content">材料正文</label>
      <textarea id="content" name="content" rows="7" required></textarea>
      <button type="submit">上传文字材料</button>
    </form>
    <form id="file-upload-form" novalidate>
      <h3>选择文件上传</h3>
      <label for="file-display-name">材料名称</label>
      <input id="file-display-name" name="display_name" required>
      <label for="material-file">材料文件</label>
      <input id="material-file" name="file" type="file" accept=".txt,.md,text/plain,text/markdown" required>
      <button type="submit">上传文件材料</button>
    </form>`;
  const textForm = teacherUpload.querySelector("#text-upload-form");
  textForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const displayName = textForm.elements.display_name.value.trim();
    const content = textForm.elements.content.value.trim();
    if (!displayName || !content) {
      status.textContent = "请填写材料名称和正文。";
      return;
    }
    const button = textForm.querySelector("button");
    button.disabled = true;
    status.textContent = "正在上传材料…";
    try {
      const response = await request("/api/materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: displayName, content }),
      });
      if (response.status === 201) {
        textForm.reset();
        await loadMaterials();
        status.textContent = "材料上传成功。";
      } else if (response.status === 403) {
        status.textContent = "你没有上传材料的权限。";
      } else {
        status.textContent = "上传材料失败，请稍后重试。";
      }
    } catch (error) {
      if (error.message !== "unauthorized") status.textContent = "上传材料失败，请稍后重试。";
    } finally {
      button.disabled = false;
    }
  });
  const fileForm = teacherUpload.querySelector("#file-upload-form");
  fileForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const displayName = fileForm.elements.display_name.value.trim();
    const file = fileForm.elements.file.files[0];
    if (!displayName || !file) {
      status.textContent = "请填写材料名称并选择一个 .txt 或 .md 文件。";
      return;
    }
    const button = fileForm.querySelector("button");
    button.disabled = true;
    status.textContent = "正在上传材料…";
    try {
      const formData = new FormData();
      formData.append("display_name", displayName);
      formData.append("file", file);
      const response = await request("/api/materials", { method: "POST", body: formData });
      if (response.status === 201) {
        fileForm.reset();
        await loadMaterials();
        status.textContent = "材料上传成功。";
      } else if (response.status === 403) {
        status.textContent = "你没有上传材料的权限。";
      } else {
        status.textContent = "上传材料失败，请稍后重试。";
      }
    } catch (error) {
      if (error.message !== "unauthorized") status.textContent = "上传材料失败，请稍后重试。";
    } finally {
      button.disabled = false;
    }
  });
}

async function initializeWorkspace() {
  if (!auth.getToken()) {
    auth.handleUnauthorized();
    return;
  }
  try {
    const response = await request("/api/me");
    if (!response.ok) throw new Error("identity_failed");
    const { user } = await response.json();
    currentUser = user;
    userContext.textContent = `${user.account} · ${roleLabel(user.role)} · ${user.class_name} 班`;
    renderTeacherUpload(user);
    renderTeacherIndexing(user);
    await loadMaterials();
  } catch (error) {
    if (error.message !== "unauthorized") status.textContent = "无法加载材料页面，请稍后重试。";
  }
}

document.querySelector("#logout-button").addEventListener("click", async () => {
  try {
    if (auth.getToken()) await request("/logout", { method: "POST" });
  } finally {
    clearProtectedView();
    auth.clearToken();
    window.location.replace("/login");
  }
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await loadMaterials(searchForm.elements.q.value.trim());
});

retrievalForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = retrievalForm.elements.q.value.trim();
  if (!query) return;
  const mode = retrievalForm.elements.mode.value;
  const requestId = ++retrievalRequestId;
  retrievalResults.replaceChildren();
  retrievalStatus.textContent = "正在检索…";
  const button = retrievalForm.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const response = await request(`/api/retrieval?${new URLSearchParams({ q: query, mode })}`);
    if (requestId !== retrievalRequestId) return;
    if (response.status === 400) {
      retrievalStatus.textContent = "请输入有效的检索内容和方式。";
      return;
    }
    if (response.status === 503) {
      retrievalStatus.textContent = "语义检索服务暂不可用；可切换关键词检索。";
      return;
    }
    if (!response.ok) throw new Error("retrieval_failed");
    const { hits } = await response.json();
    for (const hit of hits) {
      const item = document.createElement("li");
      item.className = "result-card";
      const source = document.createElement("button");
      source.type = "button";
      source.textContent = `来源：${hit.material_title} · 切片 ${hit.chunk_index + 1}`;
      source.addEventListener("click", () => loadDetail(hit.material_id));
      const meta = document.createElement("p");
      meta.className = "source-meta";
      meta.textContent = `字符位置 ${hit.start_offset}–${hit.end_offset}`;
      const excerpt = document.createElement("p");
      excerpt.textContent = hit.excerpt;
      item.append(source, meta, excerpt);
      retrievalResults.append(item);
    }
    retrievalStatus.textContent = hits.length ? `找到 ${hits.length} 个相关切片。` : "资料中未找到相关内容。";
  } catch (error) {
    if (error.message !== "unauthorized" && requestId === retrievalRequestId) {
      retrievalStatus.textContent = "检索失败，请稍后重试。";
    }
  } finally {
    button.disabled = false;
  }
});

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = askForm.elements.question.value.trim();
  if (!question) return;
  const requestId = ++askRequestId;
  askAnswer.textContent = "";
  askAnswer.hidden = true;
  askCitations.replaceChildren();
  askStatus.textContent = "正在查找相关资料并生成答案…";
  const button = askForm.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const response = await request("/api/ask", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (requestId !== askRequestId) return;
    if (response.status === 400) {
      askStatus.textContent = "请输入有效的问题。";
      return;
    }
    if (response.status === 503) {
      askStatus.textContent = "问答服务暂不可用，请稍后重试。";
      return;
    }
    if (!response.ok) throw new Error("ask_failed");
    const { answer, citations } = await response.json();
    askAnswer.textContent = answer;
    askAnswer.hidden = false;
    for (const citation of citations) {
      const item = document.createElement("li");
      item.className = "citation-card";
      const source = document.createElement("button");
      source.type = "button";
      source.textContent = `[${citation.number}] ${citation.material_title} · 切片 ${citation.chunk_index + 1}`;
      source.addEventListener("click", () => loadDetail(citation.material_id));
      const excerpt = document.createElement("p");
      excerpt.textContent = citation.excerpt;
      item.append(source, excerpt);
      askCitations.append(item);
    }
    askStatus.textContent = citations.length ? "答案与来源已显示。" : "资料中未找到相关内容。";
  } catch (error) {
    if (error.message !== "unauthorized" && requestId === askRequestId) {
      askStatus.textContent = "问答失败，请稍后重试。";
    }
  } finally {
    button.disabled = false;
  }
});

initializeWorkspace();
