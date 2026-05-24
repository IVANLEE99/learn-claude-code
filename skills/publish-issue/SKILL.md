# Publish Markdown to GitHub Issue

将 Markdown 内容发布为 GitHub Issue，支持自动上传附件（图片、音频等）

## 触发条件

当用户提到以下关键词时，自动触发此 Skill：
- 发布 issue / publish issue
- 提交 issue / submit issue
- 将 markdown 发布到 github
- 新建 issue / create issue
- 写完文档要发布

## 执行步骤

### 第 1 步：选择目标仓库

向用户展示以下选项：

```
请选择目标仓库：
1. IVANLEE99/IVANLEE99.github.io（个人站点）
2. 当前目录对应的 GitHub 仓库（通过 git remote 获取）
3. 自定义仓库（格式：owner/repo）
```

- 选项 1：固定为 `IVANLEE99/IVANLEE99.github.io`
- 选项 2：执行 `git remote get-url origin` 获取仓库地址，解析出 `owner/repo`
- 选项 3：让用户输入 `owner/repo` 格式的仓库名

### 第 2 步：读取 GitHub Token

按以下顺序尝试读取 token：

1. **settings.json**：
```bash
cat ~/.claude/settings.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['mcpServers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN'])
"
```

2. **settings.local.json**（如果 settings.json 失败）：
```bash
cat ~/.claude/settings.local.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['mcpServers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN'])
"
```

3. **环境变量**（如果以上都失败）：
```bash
echo $GITHUB_PERSONAL_ACCESS_TOKEN
```

如果都失败，提示用户手动输入 token。

### 第 3 步：获取并选择标签

使用 token 调用 GitHub API 获取目标仓库的所有 labels：

```bash
curl -s -H "Authorization: token <TOKEN>" \
  "https://api.github.com/repos/<OWNER>/<REPO>/labels"
```

将 **所有标签** 展示为独立选项，支持多选：

```
选择标签（可多选，输入 Other 添加自定义标签）：

 [x] Claude Code ⭐（推荐）
 [ ] mcp
 [ ] bug
 [ ] enhancement
 [ ] documentation
 [ ] docker
 [ ] git
 [ ] github
 [ ] k8s
 [ ] Kubernetes
 [ ] mac
 [ ] node
 [ ] npm
 [ ] about
 [ ] AI
 [ ] Ai Prompt(Ai 提示词)
 [ ] CC Switch
 [ ] Charles
 [ ] codex
 [ ] duplicate
 [ ] Fetch
 [ ] Gemini CLI
 [ ] good first issue
 [ ] help wanted
 [ ] html2pdf.js
 [ ] invalid
 [ ] Navicat Premium
 [ ] open
 [ ] OpenClaw
 [ ] OpenCode
 [+ ] 自定义标签（输入 Other 添加新标签）

已选中：Claude Code
```

交互规则：
- **每个标签是一个独立选项**，全部列出
- 标记 ⭐ 的为推荐标签（默认预选）
- **多选**：可同时选择多个标签
- **自定义标签**：选择"自定义标签"选项后输入新标签名，会自动创建
- **回车**：确认当前选择并继续

### 第 4 步：读取 Markdown 内容

读取用户提供的 Markdown 文件或内容：
1. 提取第一个 `#` 标题作为 Issue 标题
2. 剩余内容作为 Issue body

### 第 5 步：扫描并上传附件

扫描 Markdown 内容中的本地文件引用，自动上传到仓库：

**支持的文件类型：**
- 图片：`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`
- 音频：`.mp3`, `.wav`, `.ogg`, `.m4a`
- 视频：`.mp4`, `.webm`
- 文档：`.pdf`

**扫描规则：**
- 匹配 Markdown 图片语法：`![alt](path)`
- 匹配 Markdown 链接语法：`[text](path)`
- 排除 URL（以 `http://` 或 `https://` 开头）
- 排除锚点链接（以 `#` 开头）

**上传流程：**

1. 扫描所有本地文件引用
2. 如果有文件需要上传，向用户确认：
```
发现以下本地文件引用，是否上传到仓库？
- mimo-tts/examples/逍遥游.wav (3.7 MB)
- images/screenshot.png (245 KB)

上传位置：assets/attachments/
```

3. 对每个文件：
   - 读取文件并 Base64 编码
   - 上传到仓库的 `assets/attachments/` 目录
   - 获取 raw URL
   - 替换 Markdown 中的本地路径为 GitHub raw URL

**上传 API：**
```bash
# 创建 JSON payload
python3 -c "
import base64, json
with open('FILE_PATH', 'rb') as f:
    content = base64.b64encode(f.read()).decode('utf-8')
data = {
    'message': 'feat: 添加附件 FILE_NAME',
    'content': content
}
with open('/tmp/upload_payload.json', 'w') as f:
    json.dump(data, f)
"

# 上传文件
curl -s -X PUT "https://api.github.com/repos/OWNER/REPO/contents/TARGET_PATH" \
  -H "Authorization: token TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/upload_payload.json
```

**URL 替换规则：**
- 本地路径：`mimo-tts/examples/逍遥游.wav`
- 替换为：`https://github.com/OWNER/REPO/raw/main/assets/attachments/逍遥游.wav`

### 第 6 步：创建 Issue

使用 GitHub API 创建 Issue（详见 [create-issue-api.md](references/create-issue-api.md)）

```bash
curl -s -X POST "https://api.github.com/repos/OWNER/REPO/issues" \
  -H "Authorization: token TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Issue 标题",
    "body": "Issue 内容（已替换附件链接）",
    "labels": ["label1", "label2"]
  }'
```

### 第 7 步：输出结果

返回 Issue 编号和链接：
```
Issue 已创建：
- #41 GitHub MCP Server 配置指南
- https://github.com/IVANLEE99/IVANLEE99.github.io/issues/41
- Labels: Claude Code, mcp
- 附件：2 个文件已上传
```

## 错误处理

### Token 相关
- **401 Unauthorized**：Token 无效或过期，提示用户重新生成
- **403 Forbidden**：Token 权限不足，需要 `repo` 权限

### 文件上传相关
- **413 Payload Too Large**：文件超过 GitHub 限制（100MB），提示用户压缩或分割
- **422 Unprocessable Entity**：文件路径无效或已存在，提示用户检查

### Issue 创建相关
- **404 Not Found**：仓库不存在或无权访问
- **422 Validation Failed**：标签不存在或内容格式错误

## 最佳实践

1. **附件管理**：
   - 建议上传到 `assets/attachments/` 目录，保持仓库整洁
   - 文件名使用有意义的名称，避免中文乱码
   - 大文件考虑使用 Git LFS

2. **内容优化**：
   - 确保图片链接可访问
   - 音频/视频文件建议添加描述
   - 本地路径使用相对路径

3. **安全考虑**：
   - 不要上传敏感信息（API Key、密码等）
   - 检查文件内容是否包含敏感数据

## 参考

- [GitHub API - Create Issue](references/create-issue-api.md)
- [GitHub API - Create or Update File](https://docs.github.com/rest/repos/contents#create-or-update-file-contents)
- [仓库和标签配置](references/publish-config.md)
