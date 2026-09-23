const userContext = document.querySelector("#user-context");
const status = document.querySelector("#workspace-status");
const list = document.querySelector("#material-list");
const detail = document.querySelector("#material-detail");
const detailFields = document.querySelector("#material-detail-fields");
const detailActions = document.querySelector("#material-actions");
const teacherUpload = document.querySelector("#teacher-upload");
const searchForm = document.querySelector("#material-search-form");
let currentUser;

function roleLabel(role) {
  return { teacher: "教师", student: "学生" }[role] || role;
}

function materialStatusLabel(value) {
  return { ready: "已入库" }[value] || value;
}

function redirectToLogin() {
  list.replaceChildren();
  detail.hidden = true;
  window.location.replace("/login");
}

async function request(path, options) {
  const response = await fetch(path, options);
  if (response.status === 401) {
    redirectToLogin();
    throw new Error("unauthorized");
  }
  return response;
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
  const download = document.createElement("a");
  download.href = `/api/materials/${material.id}/download`;
  download.textContent = "下载材料";
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
  if (!materials.length) status.textContent = query ? "未找到名称匹配的材料。" : "当前班级暂无材料。";
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
  try {
    const response = await request("/api/me");
    if (!response.ok) throw new Error("identity_failed");
    const { user } = await response.json();
    currentUser = user;
    userContext.textContent = `${user.account} · ${roleLabel(user.role)} · ${user.class_name} 班`;
    renderTeacherUpload(user);
    await loadMaterials();
  } catch (error) {
    if (error.message !== "unauthorized") status.textContent = "无法加载材料页面，请稍后重试。";
  }
}

document.querySelector("#logout-button").addEventListener("click", async () => {
  await fetch("/logout", { method: "POST" });
  redirectToLogin();
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await loadMaterials(searchForm.elements.q.value.trim());
});

initializeWorkspace();
