# Troubleshooting Guide

## Common Issues

### Git SSH Key 问题

**Symptom**: `git clone` / `git fetch` 报错，如 `Permission denied (publickey)`、`Connection refused`、`REMOTE HOST IDENTIFICATION CHANGED` 等。

完整参考文档：https://km.sankuai.com/collabpage/1465033066

#### 快速诊断

```bash
ssh -V          # 查看 OpenSSH 版本，>=8.8 不支持 RSA
cat ~/.ssh/id_ed25519.pub   # 检查是否有 ed25519 公钥
cat ~/.ssh/id_rsa.pub       # 检查是否有 rsa 公钥
```

#### 方案 A：生成新 SSH Key（推荐 ED25519）

```bash
# 一键生成，无需交互
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ''

# 复制公钥到剪贴板（Mac）
tr -d '\n' < ~/.ssh/id_ed25519.pub | pbcopy
```

然后访问 https://dev.sankuai.com/code/home 手动添加 SSH Key。

#### 方案 B：修复 ~/.ssh/config（保留现有 RSA Key）

若 OpenSSH >= 8.8 且本地仍想用 RSA，编辑 `~/.ssh/config`：

```
Host *
    HostkeyAlgorithms +ssh-rsa
    PubkeyAcceptedKeyTypes +ssh-rsa
```

若使用 ed25519：

```
Host *
    HostkeyAlgorithms +ssh-ed25519
    PubkeyAcceptedKeyTypes +ssh-ed25519
```

修改后清除 known_hosts 并重试：

```bash
rm -rf ~/.ssh/known_hosts
git fetch origin    # 根据提示输入 yes
```

#### 方案 C：REMOTE HOST IDENTIFICATION CHANGED

```bash
# 删除 known_hosts 或只删除对应行
rm -rf ~/.ssh/known_hosts
```

#### 方案 D：Connection refused

```bash
# 检查 /etc/hosts 是否有异常绑定
cat /etc/hosts | grep git.sankuai.com
```

#### 文件权限问题（仍提示输入密码）

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

---

### Authentication Errors (401)

**Symptom**: `km` command fails with authentication error or "Unable to get cookies".

**Solutions**:
1. Open https://km.sankuai.com in browser and log in
2. Verify SSO config: `cat ~/.meituan_local_config.json | grep -A5 sso`
3. Test with: `km search "test" --limit 1`

If still failing, update `~/.meituan_local_config.json`:
```json
"sso": {
  "default_browser": "chrome",
  "cookie_file": "~/Library/Application Support/Google/Chrome/Default/Cookies"
}
```
Then manually navigate to https://km.sankuai.com in Chrome to refresh cookies.

### Permission Denied (403)

**Symptom**: "对不起，您没有权限"

**Solutions**:
1. Verify you have the required permission on the target document/space
   - For `create`: need "添加" permission on parent
   - For `delete`/`move`: need "编辑" or "管理" permission
2. Check space membership: `km hierarchy-info --doc-id=PARENT_ID`
3. Ask the space admin to grant you access

### km Command Not Found

```bash
# Activate the virtual environment
source ~/.meituan-local-tools/.venv/bin/activate

# Or re-run setup
bash ~/.meituan-local-tools/setup.sh
```

### Content Too Large

**Symptom**: Upload fails for large documents.

**Solutions**:
1. Document content limit is 10 MB
2. Split large documents into multiple sub-documents
3. Reduce embedded image sizes
4. Use `--compression` flag with `read-file` to reduce file sizes

### Markdown Rendering Issues

**Symptom**: Content doesn't render correctly in 学城.

**Solutions**:
1. Avoid complex nested tables
2. Use standard markdown syntax
3. Test with simple content first, then add complexity

### Title Too Long

**Symptom**: Title exceeds limit error.

**Solution**: Document title is limited to 100 characters. Shorten the title.

### Space/Parent Hierarchy Limits

- Space root: max 1000 first-level documents
- Each document: max 500 sub-documents
- Max depth: 15 levels

### move / copy Fails

**Symptom**: Target location not found or permission denied.

**Solutions**:
1. Verify target parent ID with `km hierarchy-info --doc-id=TARGET_PARENT_ID`
2. Cross-space moves require both `--parent` and `--space`
3. Confirm write permission on target space/document

### restore Fails

**Symptom**: Document not found in trash.

**Solutions**:
1. Confirm the document was soft-deleted (not permanently deleted)
2. Check with admin if trash has been emptied
