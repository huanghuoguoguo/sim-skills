# sim-skills

面向 Claude Code 的论文格式检查 skill 仓库。

目标是沉淀一组基础工具，让 Agent 从模板或成品文档中提取格式规范，再自动检查论文合规性。

## 核心架构

```text
用户请求
  -> Agent 读取 SKILL.md
  -> Agent 自主规划
  -> 调用 Python 工具脚本获取事实和执行检查
  -> Agent 推理语义规则
  -> 输出产物 (spec.md / 检查报告)
```

两条主工作流：

```text
上游: 参考文件 -> Agent + 工具 -> spec.md -> 用户精校
下游: 论文 + spec.md -> Agent + 工具 -> 检查报告
```

上游产物是 `spec.md`（自然语言规则），不生成 `spec.json`。

## Skill 一览

### 工具层 (Primitive)

| Skill | 功能 |
|-------|------|
| `parse-word` | 解析 .docx/.dotm 为结构化事实 (DocumentIR) |
| `query-word-text` | 按关键词检索文档段落 |
| `query-word-style` | 查询样式的最终属性值 |
| `render-word-page` | 将指定页渲染为图片 |
| `read-text` | 读取文本文件内容 (.txt / .md / .docx) |

### 工作流层 (Workflow)

| Skill | 功能 |
|-------|------|
| `extract-spec` | 从参考文件提取格式规范，输出 spec.md |
| `check-thesis` | 基于 spec.md 检查论文格式，输出报告 |
| `compare-docs` | 比对两份 Word 文档的格式差异 |

### 质量门禁 (Gate)

| Skill | 功能 |
|-------|------|
| `evaluate-spec` | 评估 spec.md 的覆盖性、具体性和可执行性 |

## 混合检查模式

`check-thesis` 采用 Python + Agent 混合方式：

- **Python** (`translate_spec.py` + `batch_check.py`)：字体、字号、行距、边距、缩进、对齐、标题样式、题注等确定性规则
- **Agent**：摘要格式、参考文献、目录结构等语义规则
- **人工**：无法自动翻译的规则标记为待人工确认

## 当前范围

- 主场景：高校论文 `.docx` / `.dotm`
- 主目标：提取规范、检查合规、输出结构化报告
- 暂不支持：自动修复、`.doc` / PDF 作为主检查目标

## 文档

- [背景与机会](docs/00-背景与机会.md)
- [产品设计](docs/01-产品设计.md)
- [MVP 设计](docs/02-MVP设计.md)
- [MVP 实施方案](docs/03-MVP实施方案.md)
- [Spec Schema 草案](docs/04-Spec-Schema草案.md)
