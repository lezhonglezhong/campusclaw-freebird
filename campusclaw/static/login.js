const form = document.querySelector("#login-form");
const status = document.querySelector("#login-status");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const account = form.elements.account.value.trim();
  const password = form.elements.password.value;
  if (!account || !password) {
    status.textContent = "Enter both your account and password.";
    return;
  }

  const button = form.querySelector("button");
  button.disabled = true;
  status.textContent = "Signing in…";
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
      ? "Account or password is incorrect."
      : "Unable to sign in. Please try again.";
  } catch {
    status.textContent = "Unable to reach CampusClaw. Please try again.";
  } finally {
    button.disabled = false;
  }
});
