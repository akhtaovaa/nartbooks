const API_BASE = "http://localhost:8000";
const TOKEN_KEY = "nb_access_token";

let currentUser = null;

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

async function apiFetch(path, options = {}) {
    const headers = options.headers ? { ...options.headers } : {};
    const token = getToken();
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }

    // Убеждаемся, что path начинается с /
    const fullPath = path.startsWith('/') ? path : `/${path}`;
    const url = `${API_BASE}${fullPath}`;
    
    console.log('API Request:', url, options.method || 'GET'); // Отладка
    
    const response = await fetch(url, { ...options, headers });
    if (response.status === 204) {
        return null;
    }

    let data = null;
    try {
        data = await response.json();
    } catch (err) {
        // ignore json parsing errors for empty responses
    }

    if (!response.ok) {
        const message = data?.detail || data?.message || `Ошибка ${response.status}`;
        const error = new Error(message);
        error.status = response.status;
        error.data = data;
        throw error;
    }
    return data;
}

async function loadCurrentUser() {
    if (!getToken()) {
        currentUser = null;
        updateNavVisibility();
        return null;
    }
    try {
        currentUser = await apiFetch("/me");
    } catch (err) {
        if (err.status === 401) {
            clearToken();
            currentUser = null;
        } else {
            console.error("Не удалось получить профиль:", err);
        }
    }
    updateNavVisibility();
    return currentUser;
}

function updateNavVisibility() {
    const authOnly = document.querySelectorAll("[data-auth='true']");
    const guestOnly = document.querySelectorAll("[data-guest='true']");
    const adminOnly = document.querySelectorAll("[data-admin='true']");
    const userNameEl = document.querySelector("[data-user-name]");

    const isAuth = Boolean(currentUser);
    const isAdmin = currentUser?.role === "admin";

    authOnly.forEach((el) => el.classList.toggle("hidden", !isAuth));
    guestOnly.forEach((el) => el.classList.toggle("hidden", isAuth));
    adminOnly.forEach((el) => el.classList.toggle("hidden", !isAdmin));

    if (userNameEl) {
        userNameEl.textContent = isAuth
            ? currentUser.first_name || currentUser.email || "Профиль"
            : "";
    }
}

function initShell() {
    const logoutBtn = document.querySelector("[data-logout]");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            clearToken();
            currentUser = null;
            updateNavVisibility();
            window.location.href = "index.html";
        });
    }
}

function setStatus(el, message, type = "info") {
    if (!el) return;
    el.textContent = message;
    el.classList.remove("hidden", "error");
    if (type === "error") {
        el.classList.add("error");
    } else {
        el.classList.remove("error");
    }
}

function clearStatus(el) {
    if (!el) return;
    el.textContent = "";
    el.classList.add("hidden");
}

// Утилита для безопасного создания HTML с текстом
function escapeHTML(str) {
    if (!str) return '';
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// Алиас для совместимости
function escapeHtml(str) {
    return escapeHTML(str);
}

async function getCurrentUser() {
    if (!currentUser) {
        await loadCurrentUser();
    }
    return currentUser;
}

async function initAuth() {
    await loadCurrentUser();
    initShell();
}
