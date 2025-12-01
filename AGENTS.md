# Repository Guidelines

## Project Structure & Module Organization
- 源码位于 `src/`，按领域拆分模块，如 `src/core`, `src/routers`, `src/services`.
- API 入口为 `src/main.py` 中的 FastAPI 应用。
- 数据迁移配置在 `alembic.ini` 与 `migrations/` 目录。
- 测试代码位于 `tests/`，结构与 `src/` 模块基本对应。

## Build, Test, and Development Commands
- 安装依赖（含开发工具）：`just dev`（等价于 `uv sync`）。
- 启动开发服务器：`just run` 或 `just r`，默认端口 `8000`。
  - 自定义端口示例：`just run port=9000`
- 运行测试：`just test` 或 `just t`。
- 预提交检查/格式与 lint：`just check` 或 `just c`。
- 安装 pre-commit 钩子：`just hooks`。

## Coding Style & Naming Conventions
- 使用 Python 3.12，遵循 PEP 8，缩进为 4 空格。
- 使用 `ruff` 作为主要静态检查工具，请保持无 lint 报错。
- 模块与文件名使用小写下划线风格，例如：`user_service.py`。
- 类名使用帕斯卡命名（如 `UserService`），函数与变量使用蛇形命名（如 `get_current_user`）。

## Testing Guidelines
- 使用 `pytest`/`pytest-asyncio`，测试文件命名为 `test_*.py` 或 `*_test.py`。
- 测试放在 `tests/` 对应子目录下，紧贴功能模块。
- 新功能须附带至少一个测试用例，修复 bug 请添加回归测试。
- 本地运行全部测试：`just test`。

## Commit & Pull Request Guidelines
- 提交信息建议采用简洁英文动词祈使句，如 `Add user auth service`。
- 每个提交尽量聚焦单一变更，便于代码审查。
- PR 需包含：
  - 变更简介与动机说明；
  - 相关 issue 链接（如有）；
  - 手动验证步骤或关键截图（前端相关变更时）。
- 确保 `just check` 与 `just test` 在本地通过后再提交 PR。

## Agent-Specific Instructions
- 本仓库面向智能代理协助开发，请保持文件编码为 UTF-8。
- 自动工具或代理生成的代码需符合上述风格与测试要求。

