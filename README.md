# sim-skills

面向 Claude Code 的文档格式检查 skill 仓库。

提供一组通用工具，让 Agent 从任何来源读取格式规则，再自动检查文档合规性。

## 核心架构

```text
用户请求
  -> Agent 读取 SKILL.md
  -> Agent 自主规划
  -> 调用通用 Python 工具获取事实和执行比对
  -> Agent 推理语义规则
  -> 输出产物 (spec.md / 检查报告)
```

两个独立任务：

```text
上游: 参考文件 -> Agent + 工具 -> spec.md -> 用户精校
下游: 规则(任意来源) + 文档 -> Agent + 工具 -> 检查报告
```

## Skill 一览

### 工具层 (Generic Tools)

| Skill | 功能 |
|-------|------|
| `parse-word` | 解析 .docx/.dotm 为结构化事实 (DocumentIR) |
| `query-word-text` | 按关键词检索文档段落 |
| `query-word-style` | 查询样式的最终属性值 |
| `render-word-page` | 将指定页渲染为图片 |
| `batch-check` | 通用属性比对引擎（`--schema` 查看支持的 check 类型） |
| `paragraph-stats` | 按条件筛段落并统计属性分布 |
| `read-text` | 读取文本文件内容 (.txt / .md / .docx) |

### 工作流层 (Agent Guidance)

| Skill | 功能 |
|-------|------|
| `extract-spec` | 从参考文件提取格式规范，输出 spec.md |
| `check-thesis` | 基于规则检查文档格式，输出报告 |
| `compare-docs` | 比对两份 Word 文档的格式差异 |

### 质量门禁 (Gate)

| Skill | 功能 |
|-------|------|
| `evaluate-spec` | 评估 spec.md 的覆盖性、具体性和可执行性 |

## 检查方式

Agent 直接构造 check 指令，调用 `batch-check` 执行确定性比对：

- **Python** (`batch-check`)：字体、字号、行距、边距、缩进、对齐、题注等确定性规则
- **Agent**：摘要格式、参考文献、目录结构等语义规则

Agent 从任意来源（PDF / 纯文本 / 模板 / 口述）理解规则，无需中间翻译步骤。

## 当前范围

- 主场景：`.docx` / `.dotm` 文档格式检查
- 暂不支持：自动修复、`.doc` / PDF 作为主检查目标

## 文档

- [背景与机会](docs/00-背景与机会.md)
- [产品设计](docs/01-产品设计.md)
- [MVP 设计](docs/02-MVP设计.md)
- [MVP 实施方案](docs/03-MVP实施方案.md)
- [Spec Schema 草案](docs/04-Spec-Schema草案.md)
