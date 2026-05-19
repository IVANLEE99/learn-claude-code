# GitHub API - Create Issue

## 认证 Token

Token 从 `~/.claude/settings.json` 动态读取：

```bash
cat ~/.claude/settings.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['mcpServers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN'])
"
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

## 上传图片到仓库

通过 Git Blobs API 上传图片，获得 raw URL 供 Issue 引用。

### 1. 创建 Blob

```
POST https://api.github.com/repos/{owner}/{repo}/git/blobs
```

```json
{
  "encoding": "base64",
  "content": "<base64编码的图片内容>"
}
```

返回 `sha` 用于后续引用。

### 2. 获取当前 ref

```
GET https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}
```

返回当前 commit SHA。

### 3. 创建新 Tree

```
POST https://api.github.com/repos/{owner}/{repo}/git/trees
```

```json
{
  "base_tree": "<当前commit SHA>",
  "tree": [
    {
      "path": "images/screenshot.png",
      "mode": "100644",
      "type": "blob",
      "sha": "<blob SHA>"
    }
  ]
}
```

### 4. 创建 Commit

```
POST https://api.github.com/repos/{owner}/{repo}/git/commits
```

```json
{
  "message": "Add image: images/screenshot.png",
  "tree": "<tree SHA>",
  "parents": ["<当前commit SHA>"]
}
```

### 5. 更新 Ref

```
PATCH https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}
```

```json
{
  "sha": "<新commit SHA>"
}
```

### 6. 获取 Raw URL

上传成功后，图片的 raw URL 格式为：

```
https://github.com/{owner}/{repo}/raw/main/{path}
```

在 Markdown 中引用：

```markdown
![alt text](https://github.com/{owner}/{repo}/raw/main/images/screenshot.png)
```

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
  "body": "Issue 内容（Markdown 剩余部分，图片已替换为 raw URL）",
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

## 注意

- body 中的 JSON 字符串需要转义双引号
- 返回值中 `number` 为 Issue 编号，`html_url` 为链接
- `{owner}/{repo}` 由用户在第 1 步选择决定
- `<TOKEN>` 从 settings.json 动态读取，不要硬编码
- 本地图片需先通过 Blobs API 上传，再替换为 raw URL
- 图片文件名建议保留原始名称，避免特殊字符
