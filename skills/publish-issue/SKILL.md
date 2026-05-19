# Publish Markdown to GitHub Issue

将 Markdown 内容发布为 GitHub Issue

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

从 `~/.claude/settings.json` 中读取 `mcpServers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN` 作为认证 token。

```bash
cat ~/.claude/settings.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['mcpServers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN'])
"
```

如果读取失败，提示用户手动输入 token。

### 第 3 步：获取并选择标签

使用 token 调用 GitHub API 获取目标仓库的所有 labels：

```bash
curl -s -H "Authorization: token <TOKEN>" \
  "https://api.github.com/repos/<OWNER>/<REPO>/labels" | python3 -c "
import sys, json
labels = json.load(sys.stdin)
for i, l in enumerate(labels, 1):
    print(f'{i}. {l[\"name\"]}')
"
```

将标签列表展示给用户选择（使用 AskUserQuestion 工具）。

- 用户选择 → 对应标签
- 默认推荐选择 `Claude Code` + `mcp`
- 如果标签不存在 → 跳过，不新建

### 第 4 步：读取 Markdown 内容并上传图片

读取用户提供的 Markdown 文件或内容：
1. 提取第一个 `#` 标题作为 Issue 标题
2. 扫描所有本地图片引用（`![...](...png/jpg/jpeg/gif/webp)`）
3. 上传本地图片到 GitHub 仓库，替换为 raw URL

**图片上传流程：**

对每个本地图片引用，执行以下操作：

```python
import base64, hashlib, re, json, subprocess

# 1. 读取本地图片文件
with open(image_path, 'rb') as f:
    content = f.read()

# 2. 计算 blob SHA
blob_sha = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\n' + content).hexdigest()

# 3. 通过 GitHub API 创建 blob
blob_data = json.dumps({
    'encoding': 'base64',
    'content': base64.b64encode(content).decode()
})
# POST https://api.github.com/repos/{owner}/{repo}/git/blobs

# 4. 获取仓库默认分支的 tree SHA
# GET https://api.github.com/repos/{owner}/{repo}/git/refs/heads/main

# 5. 创建新 tree（包含图片文件）
# POST https://api.github.com/repos/{owner}/{repo}/git/trees

# 6. 创建 commit
# POST https://api.github.com/repos/{owner}/{repo}/git/commits

# 7. 更新 refs/heads/main 指向新 commit
# PATCH https://api.github.com/repos/{owner}/{repo}/git/refs/heads/main

# 8. 替换 markdown 中的图片引用为 raw URL
# ![alt](https://github.com/{owner}/{repo}/raw/main/{image_path})
```

**使用 Python 脚本批量处理：**

```bash
python3 << 'PYEOF'
import base64, hashlib, json, re, sys, urllib.request

OWNER = "<OWNER>"
REPO = "<REPO>"
TOKEN = "<TOKEN>"
MARKDOWN_FILE = "<FILE_PATH>"
DEFAULT_BRANCH = "main"

def github_api(method, path, data=None):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Content-Type", "application/json")
    if data:
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# 读取 markdown
with open(MARKDOWN_FILE) as f:
    content = f.read()

# 提取标题
lines = content.split('\n')
title = lines[0].lstrip('# ').strip()
body_lines = lines[1:]

# 查找本地图片引用
img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
local_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')

for match in img_pattern.finditer('\n'.join(body_lines)):
    alt, src = match.group(1), match.group(2)
    if any(src.lower().endswith(ext) for ext in local_exts) and not src.startswith('http'):
        # 读取图片
        with open(src, 'rb') as f:
            img_content = f.read()
        
        # 创建 blob
        blob_sha = hashlib.sha1(
            b'blob ' + str(len(img_content)).encode() + b'\n' + img_content
        ).hexdigest()
        
        blob = github_api("POST", f"/repos/{OWNER}/{REPO}/git/blobs", {
            "encoding": "base64",
            "content": base64.b64encode(img_content).decode()
        })
        
        # 获取当前 tree
        ref = github_api("GET", f"/repos/{OWNER}/{REPO}/git/refs/heads/{DEFAULT_BRANCH}")
        base_tree = ref["object"]["sha"]
        
        # 创建新 tree
        tree = github_api("POST", f"/repos/{OWNER}/{REPO}/git/trees", {
            "base_tree": base_tree,
            "tree": [{"path": src, "mode": "100644", "type": "blob", "sha": blob["sha"]}]
        })
        
        # 创建 commit
        commit = github_api("POST", f"/repos/{OWNER}/{REPO}/git/commits", {
            "message": f"Add image: {src}",
            "tree": tree["sha"],
            "parents": [base_tree]
        })
        
        # 更新 ref
        github_api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/{DEFAULT_BRANCH}", {
            "sha": commit["sha"]
        })
        
        # 替换为 raw URL
        raw_url = f"https://github.com/{OWNER}/{REPO}/raw/main/{src}"
        body_content = '\n'.join(body_lines)
        body_content = body_content.replace(src, raw_url)
        body_lines = body_content.split('\n')

# 输出结果
print(json.dumps({"title": title, "body": '\n'.join(body_lines)}))
PYEOF
```

### 第 5 步：创建 Issue

使用 Python 脚本创建 Issue（避免 JSON 转义问题）：

```bash
curl -s -X POST "https://api.github.com/repos/<OWNER>/<REPO>/issues" \
  -H "Authorization: token <TOKEN>" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json
body = open('<FILE_PATH>').read()
lines = body.split('\n')
# Skip title line and image references
content_lines = [l for l in lines[1:] if '![' not in l]
content = '\n'.join(content_lines)
print(json.dumps({
    'title': '<TITLE>',
    'body': content,
    'labels': [<LABELS>]
}))
")"
```

### 第 6 步：输出结果

返回 Issue 编号和链接：
```
Issue 已创建：
- #53 知乎搜索 MCP 接入指南
- https://github.com/IVANLEE99/IVANLEE99.github.io/issues/53
- Labels: Claude Code, mcp
```

## 参考

- [GitHub API - Create Issue](references/create-issue-api.md)
- [仓库和标签配置](references/publish-config.md)
