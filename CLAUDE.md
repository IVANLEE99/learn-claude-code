# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose
This repository is primarily a Chinese documentation project about using Claude Code, with two long-form guides and supporting screenshots. It also contains a minimal JavaScript sample in `src/index.js`.

## High-level structure
- `Claude Code安装文档/Claude Code安装文档.md`: installation-focused guide (environment setup, installation, login, and basic security notes).
- `AI工具飞速上手之Claude Code/AI工具飞速上手之Claude Code.md`: broader tutorial (background, setup, slash commands, workflows, IDE integration).
- `*/images/`: screenshot assets referenced by the Markdown guides.
- `src/index.js`: minimal executable JS example (`console.log('hello')`).

## Development commands
There is no build system, linter, or test framework configured yet (no `package.json`, test config, or task runner found).

Current runnable command:
```bash
node src/index.js
```

## Maintenance guidance for future edits
- Treat this repo as documentation-first: preserve image links and relative paths when editing Markdown.
- The two guide documents overlap in content; if updating instructions, keep both aligned or intentionally document differences.
- If a package manager or test framework is added later, update this file with exact commands for:
  - install dependencies
  - build/lint/test
  - run a single test
