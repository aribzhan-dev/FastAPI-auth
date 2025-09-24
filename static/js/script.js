// === Настройки (для локали можно оставить пустым) ===
const API_BASE = 'http://127.0.0.1:9080';
const ROUTES = {
  REGISTER: '/auth/register',
  LOGIN_COOKIE: '/auth/login-cookie/',
  CHECK_COOKIE: '/auth/check-cookie/',
  LOGOUT_COOKIE: '/auth/logout-cookie/',
};

// === Утилиты ===
function $(sel, root = document) { return root.querySelector(sel); }
function showToast(msg, type = 'info') { alert(`${type.toUpperCase()}: ${msg}`); }
function setLoading(btn, loading) {
  if (!btn) return;
  btn.disabled = !!loading;
  btn.dataset.originalText ??= btn.textContent;
  btn.textContent = loading ? 'Загрузка…' : btn.dataset.originalText;
}

// Вкладки
window.switchTab = function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(p => p.classList.remove('active'));
  const btn = Array.from(document.querySelectorAll('.tab-btn'))
    .find(b => b.textContent.trim().toLowerCase().includes(name));
  if (btn) btn.classList.add('active');
  const pane = document.getElementById(`${name}-form`);
  if (pane) pane.classList.add('active');
};

// Показ/скрытие пароля
window.togglePassword = function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
};

// === Базовый fetch (JSON + ошибки) ===
async function apiFetch(path, opts = {}) {
  const res = await fetch(API_BASE + path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  });
  let data = null;
  try { data = await res.json(); } catch {}

  if (!res.ok) {
    const detail = data?.detail || data?.error || res.statusText || `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return data ?? {};
}

// === API операции ===
function registerUser({ email, username, password }) {
  return apiFetch(ROUTES.REGISTER, {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  });
}

function loginWithCookieJson({ email, password }) {
  return apiFetch(ROUTES.LOGIN_COOKIE, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

function checkSession() {
  return apiFetch(ROUTES.CHECK_COOKIE, { method: 'GET' });
}

function logoutCookie() {
  return apiFetch(ROUTES.LOGOUT_COOKIE, { method: 'GET' });
}

// === Общая логика после входа ===
async function afterLoginSuccess() {
  await checkSession();
  showToast('Вы успешно вошли!', 'success');
  ensureSessionBanner();
  // Например: window.location.href = '/dashboard';
}

// Баннер активной сессии
function ensureSessionBanner() {
  if (document.querySelector('.session-banner')) return;
  const card = document.querySelector('.card');
  if (!card) return;
  card.insertAdjacentHTML('beforebegin', `
    <div class="session-banner">
      <p>Сессия активна.</p>
      <button id="logout-btn" class="btn">Выйти</button>
    </div>
  `);
  $('#logout-btn')?.addEventListener('click', onLogout);
}

async function onLogout() {
  const btn = $('#logout-btn');
  try {
    setLoading(btn, true);
    await logoutCookie();
    showToast('Вы вышли из аккаунта', 'success');
    window.location.reload();
  } catch (e) {
    showToast(e.message || 'Ошибка при выходе', 'error');
  } finally {
    setLoading(btn, false);
  }
}

// === Обработчики форм ===
window.handleLogin = async function handleLogin(e) {
  e.preventDefault();
  const email = $('#login-email')?.value.trim();
  const password = $('#login-password')?.value || '';
  const btn = e.submitter || $('#login-submit');

  if (!email || !password) return showToast('Заполните email и пароль', 'error');

  try {
    setLoading(btn, true);
    await loginWithCookieJson({ email, password });
    await afterLoginSuccess();
  } catch (err) {
    console.error(err);
    showToast(err.message || 'Неверные данные или сервер недоступен', 'error');
  } finally {
    setLoading(btn, false);
  }
};

window.handleRegister = async function handleRegister(e) {
  e.preventDefault();
  const username = $('#register-name')?.value.trim();
  const email = $('#register-email')?.value.trim();
  const pass = $('#register-password')?.value || '';
  const pass2 = $('#register-confirm-password')?.value || '';
  const btn = e.submitter || $('#register-submit');

  if (!username || !email) return showToast('Заполните имя и email', 'error');
  if (pass.length < 6) return showToast('Пароль должен содержать минимум 6 символов', 'error');
  if (pass !== pass2) return showToast('Пароли не совпадают', 'error');

  try {
    setLoading(btn, true);
    await registerUser({ email, username, password: pass });
    await loginWithCookieJson({ email, password: pass }); // авто-вход
    await afterLoginSuccess();
  } catch (err) {
    console.error(err);
    showToast(err.message || 'Ошибка при регистрации', 'error');
  } finally {
    setLoading(btn, false);
  }
};

// === Проверка сессии при загрузке ===
document.addEventListener('DOMContentLoaded', async () => {
  try {
    await checkSession();
    ensureSessionBanner();
  } catch {
    // сессии нет — остаёмся на формах
  }
});