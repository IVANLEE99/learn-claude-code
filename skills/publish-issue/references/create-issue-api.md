# GitHub API - Create Issue

## 认证 Token

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

## 获取仓库所有 Labels

```
GET https://api.github.com/repos/{owner}/{repo}/labels
```

Headers:
```
Authorization: token <TOKEN>
```

返回 label 列表，每个 label 包含 `name` 和 `color`。

## 上传文件到仓库

```
PUT https://api.github.com/repos/{owner}/{repo}/contents/{path}
```

Headers:
```
Authorization: token <TOKEN>
Content-Type: application/json
```

请求体：
```json
{
  "message": "commit message",
  "content": "base64-encoded-file-content"
}
```

**完整流程：**

```bash
# 1. Base64 编码文件并创建 JSON
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

# 2. 上传文件
curl -s -X PUT "https://api.github.com/repos/OWNER/REPO/contents/TARGET_PATH" \
  -H "Authorization: token TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/upload_payload.json
```

**注意事项：**
- 文件大小限制：100 MB
- 中文文件名需要 URL 编码
- 返回值中 `content.html_url` 为文件链接
- 返回值中 `content.sha` 用于后续更新

**URL 替换：**
- 上传后获取 raw URL：`https://github.com/OWNER/REPO/raw/main/PATH`
- 替换 Markdown 中的本地路径

## 创建 Issue

```
POST https://api.github.com/repos/{owner}/{repo}/issues
```

Headers:
```
Authorization: token <TOKEN>
Content-Type: application/json
```

请求体：
```json
{
  "title": "Issue 标题（取自 Markdown 第一个 # 标题）",
  "body": "Issue 内容（Markdown 剩余部分，已替换附件链接）",
  "labels": ["label1", "label2"]
}
```

curl 示例：
```bash
curl -s -X POST \
  -H "Authorization: token <TOKEN>" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/{owner}/{repo}/issues" \
  -d '{"title": "标题", "body": "内容", "labels": ["label1"]}'
```

## 更新 Issue

```
PATCH https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}
```

Headers:
```
Authorization: token <TOKEN>
Content-Type: application/json
```

请求体：
```json
{
  "body": "更新后的内容"
}
```

## 注意

- body 中的 JSON 字符串需要转义双引号
- 返回值中 `number` 为 Issue 编号，`html_url` 为链接
- `{owner}/{repo}` 由用户在第 1 步选择决定
- `<TOKEN>` 从 settings.json 动态读取，不要硬编码
- 上传大文件时注意超时设置（建议 60 秒）
- 临时文件使用后及时清理
