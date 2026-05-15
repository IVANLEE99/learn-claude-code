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
  "body": "Issue 内容（Markdown 剩余部分）",
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
