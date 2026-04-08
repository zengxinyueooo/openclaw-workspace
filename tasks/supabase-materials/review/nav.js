/**
 * 共享导航栏 - nav.js
 * 两种模式：
 * 1. 新版 HTML：nav 为空，由本文件完整渲染
 * 2. 旧版 HTML：nav 已有硬编码内容，本文件 patch 插入缺失的链接
 */
(function () {
  const NAV_ITEMS = [
    { href: 'requirement.html',        label: '需求追踪' },
    { href: 'requirement-detail.html', label: '需求详情' },
    { href: 'index.html',              label: '素材审核' },
    { href: 'materials-pool.html',     label: '素材池' },
    { href: 'image-select.html',       label: '生图审核' },
    { href: 'gen-stats.html',          label: '生图统计' },
    { href: 'draft-review.html',       label: '草稿审核' },
    { href: 'dashboard.html',          label: '数据看板' },
    { href: 'tasks.html',              label: '任务看板' },
    { href: 'command-log.html',        label: '指令日志' },
    { href: 'user-manage.html',        label: '用户管理' },
  ];

  function getCurrentPage() {
    return location.pathname.split('/').pop() || 'index.html';
  }

  function isActive(href) {
    const page = getCurrentPage();
    if (href === 'requirement-detail.html' && page.startsWith('requirement-detail')) return true;
    return page === href;
  }

  function makeLink(item) {
    const active = isActive(item.href);
    const a = document.createElement('a');
    a.href = item.href;
    a.textContent = item.label;
    a.style.cssText = `color:${active ? '#6366f1' : '#94a3b8'};text-decoration:none;${active ? 'font-weight:600;' : ''}`;
    a.addEventListener('mouseover', function () { this.style.color = '#e2e8f0'; });
    a.addEventListener('mouseout', function () {
      this.style.color = isActive(this.getAttribute('href')) ? '#6366f1' : '#94a3b8';
    });
    return a;
  }

  function renderNav() {
    const user = localStorage.getItem('mcn_current_user');
    if (!user) return;

    const nav = document.getElementById('mcn-nav');
    if (!nav) return;

    // 检查 nav 里已有哪些链接
    const existingHrefs = new Set(
      Array.from(nav.querySelectorAll('a')).map(a => a.getAttribute('href'))
    );

    if (existingHrefs.size === 0) {
      // 新版 HTML：nav 为空，完整渲染
      NAV_ITEMS.forEach(item => nav.appendChild(makeLink(item)));
      nav.style.display = 'flex';
    } else {
      // 旧版 HTML：nav 已有内容，只插入缺失的
      nav.style.display = 'flex';
      NAV_ITEMS.forEach((item, idx) => {
        if (existingHrefs.has(item.href)) return; // 已存在，跳过
        // 找插入位置：在 idx 对应的前一个已有链接后面插入
        const allLinks = nav.querySelectorAll('a');
        // 找到紧挨着的前一个存在于 nav 中的 item
        let insertAfter = null;
        for (let i = idx - 1; i >= 0; i--) {
          const prevHref = NAV_ITEMS[i].href;
          const prevEl = nav.querySelector(`a[href="${prevHref}"]`);
          if (prevEl) { insertAfter = prevEl; break; }
        }
        const newLink = makeLink(item);
        if (insertAfter && insertAfter.nextSibling) {
          nav.insertBefore(newLink, insertAfter.nextSibling);
        } else if (insertAfter) {
          nav.appendChild(newLink);
        } else {
          nav.insertBefore(newLink, nav.firstChild);
        }
      });
    }
  }

  // DOM ready 后执行（旧版 HTML 的内联 script 也在 DOMContentLoaded 后跑，加延迟保证在它之后）
  function init() {
    renderNav();
    // 对旧版页面，内联 script 可能在 nav.js 之后跑并覆盖样式，用 MutationObserver 补救
    const nav = document.getElementById('mcn-nav');
    if (!nav) return;
    const observer = new MutationObserver(function() {
      const existingHrefs = new Set(
        Array.from(nav.querySelectorAll('a')).map(a => a.getAttribute('href'))
      );
      NAV_ITEMS.forEach(item => {
        if (!existingHrefs.has(item.href)) {
          observer.disconnect(); // 断开后重新渲染，避免无限循环
          setTimeout(renderNav, 0);
        }
      });
    });
    observer.observe(nav, { childList: true, subtree: false });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
