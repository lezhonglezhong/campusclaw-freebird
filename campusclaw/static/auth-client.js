(() => {
  "use strict";

  const TOKEN_STORAGE_KEY = "campusclaw.access_token";

  class UnauthorizedError extends Error {
    constructor() {
      super("unauthorized");
      this.name = "UnauthorizedError";
    }
  }

  function getToken() {
    return window.sessionStorage.getItem(TOKEN_STORAGE_KEY);
  }

  function setToken(token) {
    if (typeof token !== "string" || !token) throw new TypeError("A non-empty access token is required");
    window.sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  }

  function clearToken() {
    window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  }

  function handleUnauthorized() {
    clearToken();
    window.dispatchEvent(new CustomEvent("campusclaw:unauthorized"));
    window.location.replace("/login");
  }

  async function request(path, options = {}) {
    const token = getToken();
    if (!token) {
      handleUnauthorized();
      throw new UnauthorizedError();
    }

    const headers = new Headers(options.headers || {});
    headers.set("Authorization", `Bearer ${token}`);
    const response = await window.fetch(path, { ...options, headers });
    if (response.status === 401) {
      handleUnauthorized();
      throw new UnauthorizedError();
    }
    return response;
  }

  window.CampusClawAuth = Object.freeze({
    TOKEN_STORAGE_KEY,
    UnauthorizedError,
    getToken,
    setToken,
    clearToken,
    handleUnauthorized,
    request,
  });
})();
