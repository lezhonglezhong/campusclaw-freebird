const userContext = document.querySelector("#user-context");
const status = document.querySelector("#workspace-status");
const list = document.querySelector("#material-list");
const detail = document.querySelector("#material-detail");
const detailFields = document.querySelector("#material-detail-fields");

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
  for (const [label, value] of Object.entries({
    ID: material.id,
    "Display name": material.display_name,
    "Class ID": material.class_id,
    "Uploader ID": material.uploader_id,
    Status: material.status,
  })) {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = String(value);
    detailFields.append(term, description);
  }
  detail.hidden = false;
}

async function loadDetail(id) {
  status.textContent = "Loading material…";
  detail.hidden = true;
  try {
    const response = await request(`/api/materials/${id}`);
    if (response.status === 404) {
      status.textContent = "That material is no longer available.";
      return;
    }
    if (!response.ok) throw new Error("detail_failed");
    showDetail((await response.json()).material);
    status.textContent = "";
  } catch (error) {
    if (error.message !== "unauthorized") status.textContent = "Unable to load material details.";
  }
}

async function loadMaterials() {
  const response = await request("/api/materials");
  if (!response.ok) throw new Error("list_failed");
  const { materials } = await response.json();
  list.replaceChildren();
  for (const material of materials) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${material.display_name} · ${material.status}`;
    button.addEventListener("click", () => loadDetail(material.id));
    item.append(button);
    list.append(item);
  }
  if (!materials.length) status.textContent = "No materials are available for your class.";
}

async function initializeWorkspace() {
  try {
    const response = await request("/api/me");
    if (!response.ok) throw new Error("identity_failed");
    const { user } = await response.json();
    userContext.textContent = `${user.account} · ${user.role} · class ${user.class_id}`;
    await loadMaterials();
    window.campusClawUser = user;
  } catch (error) {
    if (error.message !== "unauthorized") status.textContent = "Unable to load your workspace.";
  }
}

document.querySelector("#logout-button").addEventListener("click", async () => {
  await fetch("/logout", { method: "POST" });
  redirectToLogin();
});

initializeWorkspace();
