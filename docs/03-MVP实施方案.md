# MVP 实施方案

## 1. MVP 开发目标

在最短路径内交付一个可演示、可验证、可继续演化的版本，重点验证"Schema 提取 -> 格式检查"闭环。

## 2. MVP 交付物

- `.docx` 解析器
- 三条 Skills（extract-schema, check-format, inspect-word）
- 脚本资源（skills/resources/）
- Schema JSON 输出
- 检查报告输出（JSON + Markdown）
- 一组真实 fixture 样本

## 3. 目录结构

```
.claude/
└── skills/
    ├── extract-schema/
    │   └── prompt.md
    ├── check-format/
    │   └── prompt.md
    └── inspect-word/
        └── prompt.md

skills/
└── resources/
    ├── inspector.py   # docx 解析
    ├── extractor.py   # schema 提取
    └── checker.py     # 格式检查

docs/
├── 00-背景与机会.md
├── 01-产品设计.md
├── 02-MVP 设计.md
├── 03-MVP 实施方案.md
└── 04-Spec-Schema 草案.md

tests/
├── fixtures/
│   ├── template.docx
│   ├── sample.docx
│   └── thesis-to-check.docx
└── test_*.py
```

## 4. 任务分解

### 任务 1：定义 Schema 结构

产出：
- `Spec` 顶层结构
- `Rule` 规则结构
- 属性字段约定

约束：
- 只定义首版必需字段
- selector 先当路由键使用

### 任务 2：实现 Word 文档解析

产出：`skills/resources/inspector.py`

首版仅解析：
- 段落、run
- 样式名
- 字体字号
- 行距、段前段后
- 缩进
- 页边距
- 表格和图片题注段落

### 任务 3：实现 Schema 提取

产出：`skills/resources/extractor.py`

逻辑：
- 从 Document IR 中提取稳定重复的格式
- 合并多个文档的规则（如有）
- 输出 schema JSON

### 任务 4：实现格式检查

产出：`skills/resources/checker.py`

逻辑：
- 根据 selector 找目标段落
- 按 property 比较
- 输出 issue 列表

### 任务 5：实现报告渲染

输出：
- `report.json`
- `report.md`

### 任务 6：建立 Skills

在 `.claude/skills/` 下创建：
- `extract-schema/prompt.md`
- `check-format/prompt.md`
- `inspect-word/prompt.md`

### 任务 7：建立样本集

至少准备：
- 1 份模板文档
- 1 份合格论文
- 2-3 份带典型错误的论文

## 5. 开发顺序

1. 先准备真实 fixture 并做 parser spike
2. 再收敛最小 schema
3. 再打通 schema 提取输出
4. 最后再接 checker

原因：
- 真实 `.docx` 脏数据会反向约束 schema
- parser 和 schema 提取是底盘
- 先把通用接口定稳，比后面返工重构成本低

## 6. 时间规划建议

### 第 1 周
- schema 结构定义
- fixture 收集
- DOCX parser 骨架

### 第 2 周
- parser 打通
- extractor 打通
- 基础报告输出

### 第 3 周
- checker 打通
- skills 封装
- 样本回归测试

## 7. MVP 验证方式

### 功能验证
- 模板文档能生成 schema
- schema 能驱动待检查文档输出 issue 列表
- 工具接口能被 skill 自然编排

### 质量验证
- 主要问题召回率是否足够高
- 误报是否可接受
- 报告是否对用户有可操作性

### 业务验证
- 换一套学校模板能否在低成本下接入
- 用户是否可以通过自然语言把任务交给 agent

## 8. MVP 风险

- 模板样式名不规范，导致抽取困难
- 用户文档未正确套用模板样式
- 题注识别可能依赖文本模式而不是样式

## 9. MVP 风险应对

- 首版同时支持样式识别与简单文本模式识别
- 对识别不确定项显式提示，不硬判
- 用真实学校模板驱动开发，不靠理想化样本
