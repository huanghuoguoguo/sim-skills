---
name: extract-spec
description: 从模板或成品 Word 文档提取格式规范，输出 spec.json（给程序和 Agent 消费）和 spec.md（给人类阅读）。
---

# extract-spec

这个 workflow skill 负责：

**从文档中全面提取格式特征，输出一个完整、可维护的 spec 包。**

输出建议：

```text
spec/
└── <spec-id>/
    ├── spec.json
    └── spec.md
```

其中：

- `spec.json`
  给程序和下游 Agent 消费，包含所有可结构化的规则
- `spec.md`
  给人类阅读、审阅和修改，记录说明、依据、疑问和待确认项

## 提取流程

### 1. 读取基础事实

使用这些基础工具：

- `parse-word` - 解析文档结构
- `query-word-text` - 按关键词检索文本段落
- `query-word-style` - 查询样式定义
- `render-word-page` - 仅在需要视觉验证时使用

### 2. 全面提取规则（重要变化）

**不再限制提取范围**。尽可能提取所有格式规则：

**封面/封皮**
- `frontmatter.title_page.title` - 论文题目
- `frontmatter.title_page.info` - 学科、专业、作者、导师等

**中英文摘要**
- `frontmatter.abstract.zh` - 中文摘要
- `frontmatter.abstract.en` - 英文摘要
- `frontmatter.keywords.zh` - 中文关键词
- `frontmatter.keywords.en` - 英文关键词

**目录**
- `frontmatter.toc.entry` - 目录条目

**正文**
- `body.paragraph` - 正文段落
- `body.heading.level1` ~ `level6` - 各级标题

**图表**
- `body.figure.caption` - 图题
- `body.table.caption` - 表题

**参考文献**
- `backmatter.references.entry` - 参考文献条目

**其他**
- `backmatter.acknowledgements` - 致谢
- `backmatter.appendix` - 附录
- `layout.headers` - 页眉
- `layout.footers` - 页脚

### 3. 写出 `spec.json`

`spec.json` 保持结构化。

推荐形状：

```json
{
  "spec_id": "tjut-thesis",
  "name": "天津理工大学硕士学位论文格式规范",
  "version": "1.0.0",
  "source_files": ["template.dotm"],
  "layout": {
    "page_size": {"width_cm": 21.0, "height_cm": 29.7},
    "page_margins": {"top_cm": 2.54, "bottom_cm": 2.54, "left_cm": 3.57, "right_cm": 2.77}
  },
  "rules": [
    {
      "id": "body-paragraph",
      "selector": "body.paragraph",
      "properties": {
        "font_family": "宋体",
        "font_family_east_asia": "宋体",
        "font_family_ascii": "Times New Roman",
        "font_size_pt": 10.5,
        "alignment": "justify",
        "line_spacing_pt": 18.0,
        "first_line_indent_pt": 24.0
      },
      "severity": "major"
    }
  ]
}
```

规则：

- **全面提取**：不要自我限制，把所有能识别的规则都提取出来
- **中英文字体分离**：如果底层解析器支持，分别记录 `font_family_east_asia` 和 `font_family_ascii`
- **非标量属性也可以**：复杂结构如 `numbering` 可以嵌套记录
- **说明性规则也记录**：如"参考文献不少于 50 篇"，可以用字符串形式记录

### 4. 写出 `spec.md`

`spec.md` 负责承载这些内容：

- 规则的人类可读说明
- 提取依据（来自模板的原文）
- 模板中观察到的格式说明
- 当前不确定项
- 无法结构化的模糊规则（如"参考文献应符合 GB/T 7714"）

用户如果要人工修改，优先修改 `spec.md`，再让 Agent 同步回 `spec.json`。

### 5. 验证 `spec.json`

最终调用：

```bash
python3 .claude/skills/validate-spec/scripts/validate.py <spec.json>
```

验证只检查基本结构和自洽性，不再限制 selector 和 property 的具体内容。
