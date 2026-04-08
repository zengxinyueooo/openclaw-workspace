// 默认配置 - 部署时自动填充
// 新库：公司内部 Supabase (2026-03-12 迁移)
window.SUPABASE_DEFAULTS = {
  url: "https://db0x9oo2hn7xxw.database.sankuai.com",
  anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzQ2OTc5MjAwLCJleHAiOjE5MDQ3NDU2MDB9.kX7NwNx_SggFeq_wyjaGxWOpPRHlMyL_nMqQB9e8rf0"
};

// 自动注入 nav.js（保证所有旧 CDN 缓存页面都能加载导航栏）
(function() {
  if (document.querySelector('script[src*="nav.js"]')) return;
  var s = document.createElement('script');
  s.src = 'nav.js?v=' + Date.now();
  document.head.appendChild(s);
})();
