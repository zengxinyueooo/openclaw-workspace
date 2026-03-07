#!/usr/bin/env node
const http = require('http');
const WebSocket = require('ws');

function cdpGet(path) {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:9222${path}`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch { resolve(data); }
      });
    }).on('error', reject);
  });
}

async function main() {
  console.log('🔌 连接 Chrome...');

  let wsUrl;
  try {
    const pages = await cdpGet('/json');
    const opxPage = pages.find(p => p.url.includes('opx-ai.sankuai.com'));
    if (opxPage) {
      console.log('✅ 找到 OPX 页面');
      wsUrl = opxPage.webSocketDebuggerUrl;
    } else {
      console.log('⚠️ 创建新页面...');
      const newPage = await cdpGet('/json/new?https://opx-ai.sankuai.com/opx-ai-manage/#/content-marketing/auto-publish');
      wsUrl = newPage.webSocketDebuggerUrl;
    }
  } catch (err) {
    console.error('❌ 连接失败:', err.message);
    console.log('\n💡 请先启动 Chrome：');
    console.log('  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222');
    process.exit(1);
  }

  console.log('🌐 启用网络监听...\n');
  const ws = new WebSocket(wsUrl);
  let result = { cookie: null, accessToken: null };

  ws.on('open', () => {
    ws.send(JSON.stringify({ id: 1, method: 'Network.enable' }));
  });

  ws.on('message', (data) => {
    const msg = JSON.parse(data);

    if (msg.method === 'Network.requestWillBeSent') {
      const { request } = msg.params;
      if (request.url.includes('/sso/web/auth')) {
        console.log('🎯 捕获 auth 请求');
        result.cookie = request.headers['Cookie'] || request.headers['cookie'] || null;
      }
    }

    if (msg.method === 'Network.responseReceived') {
      const { response, requestId } = msg.params;
      if (response.url.includes('/sso/web/auth')) {
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 2,
            method: 'Network.getResponseBody',
            params: { requestId }
          }));
        }, 300);
      }
    }

    if (msg.id === 2 && msg.result) {
      try {
        const json = JSON.parse(msg.result.body);
        if (json.code === 200 && json.data?.accessToken) {
          result.accessToken = json.data.accessToken;
          console.log('\n═══════════════════════════════════════════════════');
          console.log('🍪 Cookie:');
          console.log(result.cookie || '(未获取到)');
          console.log('\n🔑 AccessToken:');
          console.log(result.accessToken);
          console.log('═══════════════════════════════════════════════════\n');

          require('fs').writeFileSync('/tmp/opx-token.txt', JSON.stringify(result, null, 2));
          console.log('💾 已保存到 /tmp/opx-token.txt');
          ws.close();
          process.exit(0);
        }
      } catch (e) {}
    }
  });

  setTimeout(() => {
    console.log('\n⏱️ 超时');
    ws.close();
    process.exit(1);
  }, 30000);
}

main().catch(console.error);
