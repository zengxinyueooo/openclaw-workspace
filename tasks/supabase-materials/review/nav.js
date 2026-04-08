/**
 * 共享导航栏 - nav.js
 * 所有页面引入此文件，导航栏统一管理，改一处全站生效
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

  function renderNav() {
    const user = localStorage.getItem('mcn_current_user');
    if (!user) return;

    const nav = document.getElementById('mcn-nav');
    if (!nav) return;

    nav.innerHTML = NAV_ITEMS.map(item => {
      const active = isActive(item.href);
      return `<a href="${item.href}" style="color:${active ? '#6366f1' : '#94a3b8'};text-decoration:none;${active ? 'font-weight:600;' : ''}">${item.label}</a>`;
    }).join('');

    nav.style.display = 'flex';

    // hover 效果
    nav.querySelectorAll('a').forEach(a => {
      a.addEventListener('mouseover', function () { this.style.color = '#e2e8f0'; });
      a.addEventListener('mouseout', function () {
        this.style.color = isActive(this.getAttribute('href')) ? '#6366f1' : '#94a3b8';
      });
    });
  }

  // DOM ready 后执行
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderNav);
  } else {
    renderNav();
  }
})();
