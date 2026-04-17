# MVP Implementation Notes

> **Status**: MVP 已完成实施。本文档记录当时的实施方案和任务状态。
> 
> **更新说明**: 工具脚本已整合为 `sim_docs` 统一服务层。详见 `sim_docs/README.md`。

## 1. 目标

跑通"参考文件 → spec.md → 检查报告"的完整闭环。（已完成 ✅）

## 2. 现有资产

工具脚本已整合为 `sim_docs` CLI：

| CLI 命令 | 状态 |
|----------|------|
| `python3 -m sim_docs parse` | ✅ 可用，输出完整事实 |
| `python3 -m sim_docs query-text` | ✅ 可用 |
| `python3 -m sim_docs query-style` | ✅ 继承链解析完整 |
| `python3 -m sim_docs render` | ✅ 可用 |
| `python3 -m sim_docs check` | ✅ 接受检查指令，输出结构化结果 |
| `python3 -m sim_docs stats` | ✅ 段落统计 |
| `python3 -m sim_docs validate` | ✅ XSD 校验 + 自动修复 |
| `python3 -m sim_docs inspect` | ✅ XML 解包查看 |

## 3. 实施任务

### 任务 1：工具脚本适配

- [x] 确认 parse 输出包含完整事实（段落、样式、布局、页眉页脚）
- [x] 确认 query-style 正确解析样式继承链，返回最终值
- [x] 重构 check：接受检查指令 JSON，输出结构化结果
- [x] 统一 CLI 入口（`python3 -m sim_docs`）
- [x] 添加 stats 命令（段落统计）
- [x] 添加 validate 命令（XSD 校验）
- [x] 添加 inspect 命令（XML 解包）

### 任务 2：上游 Skill

- [x] 编写 `extract-spec/SKILL.md`
  - 指导 Agent 识别文件类型（模板/成品/说明）
  - 指导 Agent 如何综合多来源信息
  - 定义 spec.md 的内容结构
- [x] 编写 `evaluate-spec/SKILL.md`
  - 定义"好的 spec.md"的标准（完整、清晰、可执行）
  - 指导 Agent 逐项自评

### 任务 3：下游 Skill

- [x] 编写 `check-thesis/SKILL.md`
  - 指导 Agent 拆分确定性规则 vs 语义性规则
  - 给出 check 指令格式和示例
  - 要求检查完成后做 checklist 回溯
  - 定义报告格式（含来源标注）
- [x] 编写 `visual-check/SKILL.md`
- [x] 编写 `compare-docs/SKILL.md`

### 任务 4：端到端验证

- [x] 准备测试材料（模板 + 说明 + 论文）
- [x] 上游测试：提取 spec.md → 用户审核
- [x] 下游测试：检查论文 → 审核报告质量
- [x] 验证完整性（spec.md 规则数 vs 报告检查项数）

## 4. 当前目录结构

```
sim_docs/                       # Unified document service layer
├── __init__.py                 # Package exports
├── cli.py                      # CLI entry point (python3 -m sim_docs)
├── service.py                  # DocumentService facade (with LRU cache)
├── cache.py                    # LRU cache implementation
├── docx_parser.py              # Core Word parser
├── docx_parser_models.py       # Parser dataclasses
├── check_engine.py             # Batch check logic
├── stats_engine.py             # Paragraph statistics
├── pdf_engine.py               # PDF extraction
├── inspect_engine.py           # XML inspection
├── compare_engine.py           # Document comparison
├── validate_engine.py          # XSD validation
├── spec_engine.py              # Spec evaluation
├── adapters/
│   └── word.py                 # Adapter interface
└── tests/
    ├── test_cache.py
    ├── test_spec_engine.py
    └── test_stats_engine.py

.claude/skills/
├── SKILLS_OVERVIEW.md          # Skills navigation map
├── batch-check/SKILL.md
├── parse-word/SKILL.md
├── query-word-text/SKILL.md
├── query-word-style/SKILL.md
├── paragraph-stats/SKILL.md
├── render-word-page/SKILL.md
├── read-pdf/SKILL.md
├── read-text/SKILL.md
├── validate-word/SKILL.md
├── inspect-word-xml/SKILL.md
├── compare-docs/SKILL.md
├── extract-spec/SKILL.md
├── check-thesis/SKILL.md
├── evaluate-spec/SKILL.md
├── visual-check/SKILL.md
├── openspec-propose/SKILL.md
├── openspec-apply-change/SKILL.md
├── openspec-archive-change/SKILL.md
├── openspec-explore/SKILL.md
├── peek-thinking/SKILL.md
└── __libs__/                   # shared utilities
    ├── utils.py
    ├── spec_rules.py
    ├── thesis_profiles.py
    ├── text_sources.py
    └── soffice.py
```

## 5. 已归档的历史组件

以下组件已在新架构下移除或整合：

| 组件 | 处理方式 |
|------|----------|
| `infer-spec-fragment/` | 已移除 |
| `merge-spec-fragments/` | 已移除 |
| `validate-spec/` 系列 | 整合为 `evaluate-spec` |
| `agent-check-report/` | 整合为 `check-thesis` |
| `spec.json` schema | 移除，改为 `spec.md` |
| `scripts/run.py` | 整合为 `sim_docs` CLI |