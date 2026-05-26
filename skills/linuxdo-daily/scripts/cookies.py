#!/usr/bin/env python3
"""
linux.do Cookies 持久化工具

用法:
  # 从 Playwright MCP 导出 cookies（通过 browser_evaluate 输出）
  python3 cookies.py export --cookies 'JSON_STRING'

  # 导出到文件
  python3 cookies.py export --file data/cookies.json --cookies 'JSON_STRING'

  # 查看当前保存的 cookies
  python3 cookies.py show

  # 生成加载 cookies 的 JS 代码（用于 browser_evaluate）
  python3 cookies.py load-js
"""

import json, sys, os, argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
COOKIES_FILE = DATA_DIR / "cookies.json"


def export_cookies(cookies_json, filepath=None):
    """保存 cookies 到文件"""
    filepath = filepath or COOKIES_FILE
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(cookies_json, str):
        cookies = json.loads(cookies_json)
    else:
        cookies = cookies_json

    filepath.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
    print(f"✅ Saved {len(cookies)} cookies to {filepath}")
    return filepath


def show_cookies(filepath=None):
    """显示已保存的 cookies"""
    filepath = filepath or COOKIES_FILE
    if not filepath.exists():
        print(f"❌ No cookies file found at {filepath}")
        return

    cookies = json.loads(filepath.read_text())
    print(f"📋 Cookies ({len(cookies)} entries):")
    for c in cookies:
        name = c.get("name", "?")
        domain = c.get("domain", "?")
        httpOnly = c.get("httpOnly", False)
        secure = c.get("secure", False)
        flags = []
        if httpOnly:
            flags.append("httpOnly")
        if secure:
            flags.append("secure")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"  • {name} @ {domain}{flag_str}")


def generate_load_js(filepath=None):
    """生成用于 browser_evaluate 加载 cookies 的 JS 代码"""
    filepath = filepath or COOKIES_FILE
    if not filepath.exists():
        print(f"❌ No cookies file found at {filepath}")
        return

    cookies = json.loads(filepath.read_text())
    cookies_json = json.dumps(cookies)

    # Playwright MCP 的 browser_evaluate 只能在页面上下文执行
    # 无法直接调用 context.addCookies()，需要用 browser_run_code_unsafe
    print("Use browser_run_code_unsafe with this code:")
    print()
    js_code = f"""async (page) => {{
  const cookies = {cookies_json};
  await page.context().addCookies(cookies);
  return `Loaded ${{cookies.length}} cookies`;
}}"""
    print(js_code)


def main():
    parser = argparse.ArgumentParser(description="linux.do Cookies 持久化")
    parser.add_argument("action", choices=["export", "show", "load-js"])
    parser.add_argument("--cookies", help="Cookies JSON string")
    parser.add_argument("--file", help="Cookies file path", default=str(COOKIES_FILE))
    args = parser.parse_args()

    filepath = Path(args.file)

    if args.action == "export":
        if not args.cookies:
            print("❌ --cookies required for export")
            sys.exit(1)
        export_cookies(args.cookies, filepath)
    elif args.action == "show":
        show_cookies(filepath)
    elif args.action == "load-js":
        generate_load_js(filepath)


if __name__ == "__main__":
    main()
