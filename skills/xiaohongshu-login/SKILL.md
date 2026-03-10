---
name: xiaohongshu-login
description: 通过浏览器自动化完成小红书（xiaohongshu.com）扫码登录并保持 cookie。当需要登录小红书、访问小红书需要登录态、其他 skill 依赖小红书登录状态、或用户提到小红书登录/扫码时触发。作为内容发布等业务 skill 的前置登录准备。
---

# 小红书扫码登录

通过 Chrome Browser Relay（profile=chrome）完成小红书网页端扫码登录，保持 cookie 供后续操作使用。

## 前置要求

- 用户已在 Chrome 中安装并启用 OpenClaw Browser Relay 扩展
- 用户已在目标 Tab 上点击扩展图标激活连接（badge ON）

## 登录流程

### 1. 检查当前登录状态

使用 `browser` 工具连接 Chrome，导航到小红书并检查是否已登录：

```
browser(action=open, targetUrl="https://www.xiaohongshu.com", profile="chrome")
```

**判断已登录**：页面快照中存在用户头像、"我"、个人主页入口等元素。
**判断未登录**：页面出现"登录"按钮、登录弹窗、或被重定向到登录页。

若已登录，直接告知用户并结束。

### 2. 触发登录弹窗

如果未登录，点击页面上的"登录"按钮，触发登录弹窗：

```
browser(action=snapshot, profile="chrome")  # 找到登录按钮的 ref
browser(action=act, request={kind:"click", ref:<登录按钮ref>}, profile="chrome")
```

### 3. 切换到扫码登录

登录弹窗可能默认显示手机号/验证码方式，需要切换到二维码扫码模式：

- 查找弹窗中的 "其他登录方式" 或二维码图标入口
- 点击切换到扫码登录 Tab

### 4. 截图发送二维码

扫码界面出现后，截取二维码截图发送给用户：

```
browser(action=screenshot, profile="chrome")
```

告知用户：**"宝宝，用小红书 APP 扫这个二维码登录哦～"**

### 5. 等待登录完成

轮询检查登录状态（间隔 3-5 秒，最多等待 120 秒）：

```
browser(action=snapshot, profile="chrome")
```

**登录成功标志**：
- 二维码弹窗消失
- 页面出现用户头像或个人信息
- URL 不再包含 login 相关路径

**登录失败/超时**：
- 二维码过期 → 刷新二维码，重新截图发送
- 超过 120 秒 → 提示用户超时，询问是否重试

### 6. 确认登录成功

登录成功后，做一次最终确认：

```
browser(action=snapshot, profile="chrome")
```

确认页面已进入登录态，告知用户登录成功。

## 注意事项

- **始终使用 `profile="chrome"`**，通过 Browser Relay 连接用户的 Chrome 浏览器
- 如果用户未连接 Browser Relay，提示：请先在 Chrome 中点击 OpenClaw Browser Relay 扩展图标，确保 badge 显示为 ON
- 二维码有效期通常约 60 秒，过期需刷新
- 不要尝试手机号/密码等其他登录方式，仅支持扫码
- 轮询等待时使用 `exec` + `sleep` 避免过快轮询消耗资源
- 登录完成后 cookie 自动保持在 Chrome 中，无需额外操作
