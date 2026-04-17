## Why

sim_docs 系统已从早期的分散 skill 脚本架构迁移到统一的 Python 包，但两份 README（`sim_docs/README.md` 和项目根 `README.md`）以及 `CLAUDE.md` 之间存在文档与实际代码的偏差，同时代码本身也有若干工程问题需要修正。这些不一致会误导 Agent 和开发者，降低系统可靠性。

## What Changes

- 修复 `pdf_engine.py` 中 `extract_tables` 参数名遮蔽同名函数的 bug（运行时 TypeError）
- 清理 `compare_engine.py` 与 `cli.py` 中重复的 `_generate_diff_report` 逻辑
- 统一 `sys.path` 操作：消除多处重复的路径注入，集中到一个入口点
- 更新 `sim_docs/README.md`：补充 Skill Layout 中缺失的 `docx_parser.py`、`docx_parser_models.py`、`tests/` 目录
- 更新根 `README.md`：确认 Legacy Skill Scripts 段落中引用的脚本路径仍然有效（git status 显示旧 word/ 脚本已删除）
- 更新 `CLAUDE.md` Legacy Skill Scripts 段落：移除已不存在的旧脚本引用
- 补齐 `__init__.py` 中缺失的 `HeaderFooterFact` 导出

## Capabilities

### New Capabilities
- `fix-pdf-engine-bug`: 修复 `pdf_engine.py` 中参数遮蔽导致的 TypeError
- `consolidate-sys-path`: 统一 sys.path 操作，消除分散的路径注入
- `sync-documentation`: 同步三份文档（两个 README + CLAUDE.md）与代码实际状态

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- `sim_docs/pdf_engine.py` — 修复运行时 bug
- `sim_docs/__init__.py` — 新增导出
- `sim_docs/compare_engine.py` / `sim_docs/cli.py` — 去重 diff report 逻辑
- `sim_docs/adapters/word.py`、`service.py`、`check_engine.py`、`stats_engine.py`、`spec_engine.py` — sys.path 集中化
- `sim_docs/README.md`、`README.md`、`CLAUDE.md` — 文档更新
