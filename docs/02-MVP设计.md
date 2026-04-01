# MVP 设计

## 1. MVP 目标

验证两件事：

- 用户提供模板/成品文档后，系统能提取出可用的 schema
- 用户确认 schema 后，系统能对待检查文档输出可理解的问题报告

MVP 不追求"覆盖所有格式规则"，只追求"用最少能力打穿一个真实场景"。

## 2. MVP 范围

### 2.1 只支持

- 输入文档：`.docx`
- 场景：高校论文/毕业设计类文档
- 输出：schema JSON + 检查报告 Markdown/JSON
- 执行模式：先 `extract-schema`，后 `check-format`

### 2.2 不支持

- PDF 作为待检查对象
- 自动修复文档
- 页眉页脚的复杂节切换逻辑
- 公式、文本框、图形对象的精细检查
- 参考文献内容合规性

## 3. MVP 规则覆盖

首版只覆盖高频且易判定的规则：

- 页边距
- 正文字体（中文/英文）
- 正文字号
- 正文行距
- 正文首行缩进
- 正文段前段后距
- 一级/二级/三级标题样式
- 图题样式
- 表题样式

## 4. MVP 架构

```
技能层（.claude/skills）
├── extract-schema：提取 schema
├── check-format：检查格式
└── inspect-word：解析 docx

资源层（skills/resources）
├── inspector.py：文档解析
├── extractor.py：schema 提取
└── checker.py：格式检查
```

## 5. MVP 数据流

### 5.1 Schema 提取流程

```
用户输入：模板.docx, 成品.docx
     ↓
inspect-word 解析
     ↓
Document IR（段落、样式、属性）
     ↓
extract-schema 合并规则
     ↓
schema.json 输出
```

### 5.2 格式检查流程

```
用户输入：待检查.docx + schema.json
     ↓
inspect-word 解析
     ↓
Document IR
     ↓
check-format 比对规则
     ↓
report.md + report.json 输出
```

## 6. MVP Schema 示例

```json
{
  "spec_id": "demo-university-undergrad-v1",
  "version": "0.1.0",
  "rules": [
    {
      "id": "body-font",
      "selector": "body.paragraph",
      "properties": {
        "font_family_zh": "宋体",
        "font_size_pt": 12
      }
    },
    {
      "id": "body-spacing",
      "selector": "body.paragraph",
      "properties": {
        "line_spacing_pt": 20,
        "first_line_indent_chars": 2
      }
    },
    {
      "id": "figure-caption",
      "selector": "figure.caption",
      "properties": {
        "font_family_zh": "宋体",
        "font_size_pt": 9,
        "alignment": "center"
      }
    }
  ]
}
```

## 7. MVP 检查报告示例

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

### [minor] 图题未居中
- 规则：figure-caption
- 期望：center
- 实际：left
- 位置：图 1-1
```

## 8. MVP 成功标准

- 能处理至少 3 套不同学校模板
- 每套模板都能生成可用 schema
- schema 确认后，样本论文能稳定找出主要格式问题
- 代码以 skill 形式被 Claude Code 调用
