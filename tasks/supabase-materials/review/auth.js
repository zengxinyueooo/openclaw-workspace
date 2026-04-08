(function () {
  const STORAGE_USERS = 'mcn_users';
  const STORAGE_CURRENT = 'mcn_current_user';
  const ADMIN_USERS = ['ninghaoran', 'zengxinyue', 'lipengyu'];
  const ADMIN_PASSWORD_HASH = '56760663';

  function safeParse(json, fallback) {
    try {
      const parsed = JSON.parse(json);
      return parsed ?? fallback;
    } catch (err) {
      return fallback;
    }
  }

  function normalizeUsername(username) {
    return String(username || '').trim();
  }

  function readUsers() {
    const raw = localStorage.getItem(STORAGE_USERS);
    const users = safeParse(raw, []);
    return Array.isArray(users) ? users : [];
  }

  function writeUsers(users) {
    localStorage.setItem(STORAGE_USERS, JSON.stringify(users));
  }

  function hashPassword(password) {
    // Simple hash for local use (no crypto.subtle needed for HTTP)
    var str = String(password);
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
      var c = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + c;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
  }

  function setCurrentUser(user) {
    localStorage.setItem(STORAGE_CURRENT, JSON.stringify(user));
  }

  function getCurrentUser() {
    const raw = localStorage.getItem(STORAGE_CURRENT);
    return safeParse(raw, null);
  }

  function clearCurrentUser() {
    localStorage.removeItem(STORAGE_CURRENT);
  }

  function isAdminUser(username) {
    return ADMIN_USERS.includes(username);
  }

  function injectStyles() {
    if (document.getElementById('auth-styles')) return;
    const style = document.createElement('style');
    style.id = 'auth-styles';
    style.textContent = `
      .auth-user-bar {
        position: fixed;
        top: 16px;
        right: 16px;
        z-index: 10000;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.78);
        color: #e2e8f0;
        border: 1px solid rgba(148, 163, 184, 0.22);
        font-size: 12px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.25);
      }
      .auth-user-name {
        font-weight: 600;
        letter-spacing: 0.02em;
      }
      .auth-user-role {
        font-size: 10px;
        opacity: 0.7;
      }
      .auth-logout-btn {
        border: none;
        background: #ef4444;
        color: #fff;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 999px;
        cursor: pointer;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
      }
      .auth-logout-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(239, 68, 68, 0.3);
      }
      @media (max-width: 640px) {
        .auth-user-bar { top: 10px; right: 10px; }
      }
    `;
    document.head.appendChild(style);
  }

  function ensureUserBar() {
    if (document.getElementById('auth-user-bar')) return;
    const user = getCurrentUser();
    if (!user) return;
    injectStyles();
    const bar = document.createElement('div');
    bar.id = 'auth-user-bar';
    bar.className = 'auth-user-bar';
    const roleLabel = user.role === 'admin' ? '超级管理员' : '普通用户';
    bar.innerHTML = `
      <span class="auth-user-name">${user.username}</span>
      <span class="auth-user-role">${roleLabel}</span>
      <button class="auth-logout-btn" type="button">退出</button>
    `;
    bar.querySelector('.auth-logout-btn').addEventListener('click', () => {
      logout();
    });
    document.body.appendChild(bar);
  }

  function redirectToLogin() {
    if (window.location.pathname.endsWith('login.html')) return;
    window.location.href = 'login.html';
  }

  // 补丁：给旧版硬编码导航栏注入缺失的链接
  // 必须在 DOMContentLoaded 后执行，确保 nav 已渲染
  function patchNav() {
    var EXTRA_LINKS = [
      { after: 'requirement.html', href: 'requirement-detail.html', label: '需求详情' }
    ];
    function doInject() {
      var nav = document.getElementById('mcn-nav');
      if (!nav) return;
      var page = location.pathname.split('/').pop() || 'index.html';
      EXTRA_LINKS.forEach(function(item) {
        if (nav.querySelector('a[href="' + item.href + '"]')) return; // 已存在
        var afterEl = nav.querySelector('a[href="' + item.after + '"]');
        var a = document.createElement('a');
        a.href = item.href;
        a.textContent = item.label;
        var isActive = page === item.href;
        a.style.cssText = 'color:' + (isActive ? '#6366f1' : '#94a3b8') + ';text-decoration:none;' + (isActive ? 'font-weight:600;' : '');
        a.addEventListener('mouseover', function() { this.style.color = '#e2e8f0'; });
        a.addEventListener('mouseout', function() {
          this.style.color = (page === this.getAttribute('href')) ? '#6366f1' : '#94a3b8';
        });
        if (afterEl && afterEl.nextSibling) {
          nav.insertBefore(a, afterEl.nextSibling);
        } else {
          nav.appendChild(a);
        }
      });
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', doInject);
    } else {
      doInject();
    }
  }

  function requireLogin() {
    const user = getCurrentUser();
    if (!user) {
      redirectToLogin();
      return;
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        ensureUserBar();
        patchNav();
      });
    } else {
      ensureUserBar();
      patchNav();
    }
  }

  function requireAdmin() {
    const user = getCurrentUser();
    if (!user) {
      redirectToLogin();
      return;
    }
    if (user.role !== 'admin') {
      alert('仅超级管理员可访问用户管理页面。');
      window.location.href = 'index.html';
      return;
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        ensureUserBar();
        patchNav();
      });
    } else {
      ensureUserBar();
      patchNav();
    }
  }

  function login(username, password) {
    const cleaned = normalizeUsername(username);
    if (!cleaned || !password) {
      return { ok: false, message: '请输入用户名和密码。' };
    }
    const hash = hashPassword(password);
    if (isAdminUser(cleaned)) {
      if (hash === ADMIN_PASSWORD_HASH) {
        setCurrentUser({ username: cleaned, role: 'admin' });
        return { ok: true, role: 'admin' };
      }
      return { ok: false, message: '用户名或密码错误。' };
    }

    const users = readUsers();
    const match = users.find((u) => u.username === cleaned);
    if (!match || match.passwordHash !== hash) {
      return { ok: false, message: '用户名或密码错误。' };
    }
    setCurrentUser({ username: cleaned, role: 'user' });
    return { ok: true, role: 'user' };
  }

  function logout() {
    clearCurrentUser();
    window.location.href = 'login.html';
  }

  function redirectIfLoggedIn() {
    const user = getCurrentUser();
    if (!user) return;
    window.location.href = 'index.html';
  }

  function addUser(username, password) {
    const cleaned = normalizeUsername(username);
    if (!cleaned || !password) {
      return { ok: false, message: '用户名和密码不能为空。' };
    }
    if (isAdminUser(cleaned)) {
      return { ok: false, message: '该用户名为超级管理员保留。' };
    }
    const users = readUsers();
    if (users.some((u) => u.username === cleaned)) {
      return { ok: false, message: '该用户已存在。' };
    }
    const passwordHash = hashPassword(password);
    users.push({ username: cleaned, passwordHash });
    writeUsers(users);
    return { ok: true };
  }

  function removeUser(username) {
    const cleaned = normalizeUsername(username);
    const users = readUsers();
    const next = users.filter((u) => u.username !== cleaned);
    writeUsers(next);
  }

  window.Auth = {
    ADMIN_USERS,
    hashPassword,
    getCurrentUser,
    getUsers: readUsers,
    login,
    logout,
    requireLogin,
    requireAdmin,
    redirectIfLoggedIn,
    addUser,
    removeUser,
    normalizeUsername
  };
})();
