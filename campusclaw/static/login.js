const form = document.querySelector("#login-form");
const status = document.querySelector("#login-status");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const account = form.elements.account.value.trim();
  const password = form.elements.password.value;
  if (!account || !password) {
    status.textContent = "请输入账号和密码。";
    return;
  }

  const button = form.querySelector("button");
  button.disabled = true;
  status.textContent = "正在登录…";
  try {
    const response = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account, password }),
    });
    if (response.ok) {
      window.location.assign("/materials");
      return;
    }
    status.textContent = response.status === 401
      ? "账号或密码错误。"
      : "暂时无法登录，请稍后重试。";
  } catch {
    status.textContent = "暂时无法连接 CampusClaw，请稍后重试。";
  } finally {
    button.disabled = false;
  }
});
