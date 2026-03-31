# sim-skills

基于 Claude Code Skills 的文档格式检查工具集，提供两条核心能力：

1. **Schema 提取**：从模板/成品文档中自动提取结构化格式规则
2. **格式检查**：基于已有 schema 检查文档是否合规

## 目标使用方式

只需要告诉 Claude Code：

- 自己的目的（提取 schema / 检查格式）
- 文件在哪里
- 哪些是模板/成品文档，哪些是待检查文档

Claude Code 会自动调用相应的 skill 完成工作。

## 两条主线

### 主线一：Schema 提取

```
输入：模板.docx + 成品.docx
输出：schema.json
```

从学校提供的模板或学长学姐的成品论文中，自动提取字体、字号、行距、缩进等格式规则，输出可复用的 schema JSON 文件。

### 主线二：格式检查

```
输入：待检查.docx + schema.json
输出：report.md + report.json
```

基于已有 schema，检查待检查文档的格式合规性，输出结构化的问题报告。

## 已实现能力

- 解析 `.docx`/`.dotm` 文件，提取段落、样式、字体、间距等属性
- 从模板/成品文档中提取格式规则，生成 schema JSON（支持样式 XML + AI 文本分析）
- 基于 schema 对文档进行格式合规检查
- 输出可读的 Markdown 报告和结构化 JSON 报告

## 目录结构

```
.claude/skills/          # Claude Code 技能目录
├── word/                # Word 文档解析基础服务
├── extract-spec/        # Schema 提取（样式 XML + AI 文本分析）
├── check-thesis/        # 格式检查（基于 spec 检查合规性）
├── compare-docs/        # 文档比对（两份文档的格式差异）
└── read-text/           # 文本文件读取工具

docs/                    # 设计文档
└── 00-背景与机会.md ...

fixtures/                # 测试样本
```

## 使用方式

**直接在 Claude Code 中对话即可完成工作**，无需手动运行命令。

只需要告诉 Claude Code：

| 目的 | 示例指令 |
|------|----------|
| 提取 schema | `帮我从模板文档中提取论文格式规范` |
| 检查格式 | `用这个 schema 检查我的论文格式是否符合要求` |
| 解析文档 | `分析一下这个 Word 文档的结构` |
| 比对文档 | `比对这两份文档的格式差异` |

Claude Code 会自动调用相应的 skill 完成工作。

## 输出示例

### Schema JSON

```json
{
  "spec_id": "spec-tjut-thesis",
  "version": "0.1.0",
  "rules": [
    {
      "id": "rule-body-paragraph",
      "selector": "body.paragraph",
      "properties": {
        "font_family_zh": "宋体",
        "font_size_pt": 10.5,
        "line_spacing_pt": 20.0,
        "first_line_indent_chars": 2
      },
      "severity": "major"
    }
  ]
}
```

### 检查报告

```markdown
# 格式检查报告

## 总览
- 检查规则：10 条
- 符合：8 条
- 不符合：2 条

## 问题列表

### [major] 正文字体不符
- 规则：body-font
- 期望：宋体
- 实际：微软雅黑
- 位置：第 3 段
```

## 工程边界

- 支持格式：`.docx`、`.dotm`（Word 模板）
- 不支持：`.doc`（旧版二进制格式）、`.pdf`
- 页面级精确判断（如真实页码、跨页元素）暂不支持
- 复杂表格、公式、图形对象的检查有限
- 自动修复功能暂未实现

## 开发阶段

当前处于 MVP 阶段，核心能力：
- Schema 提取流程已打通（样式 XML + AI 文本分析）
- 格式检查流程已打通
- 基础规则覆盖（字体、字号、行距、缩进、页边距、标题、题注）
