# MVP 设计

## 1. MVP 目标

MVP 不是验证“固定 3 个 skills 是否能跑”，而是验证：

- agent 能否基于 skill graph 自主完成 spec 提取闭环
- agent 能否基于同一套 graph 完成文档检查闭环

MVP 不追求规则覆盖最全，只追求把一条真实论文场景打穿，并证明这种 skill 分层是可持续扩展的。

## 2. MVP 范围

### 2.1 支持

- 输入文档：`.docx`、`.dotm`
- 场景：高校论文 / 毕业设计类文档
- 输出：`spec.json`、`report.json`、`report.md`
- 执行模式：workflow skill 编排下层 skills

### 2.2 不支持

- PDF 作为主检查对象
- 自动修复文档
- 页面级精确分页判断
- 公式、文本框、图形对象的精细检查

## 3. MVP 最小 skill graph

### 3.1 Primitive

- `parse-word`
- `query-word-text`
- `query-word-style`
- `render-word-page`

### 3.2 Analysis

- `infer-spec-fragment`
- `merge-spec-fragments`

### 3.3 Gate

- `validate-spec-structure`
- `validate-spec-coverage`

### 3.4 Workflow

- `extract-spec`
- `check-thesis`

## 4. MVP 规则覆盖

首版只覆盖高频、易判定、且能从模板中稳定提取的规则：

- 页边距
- 正文字体
- 正文字号
- 正文行距
- 正文首行缩进
- 正文段前段后距
- 一级 / 二级 / 三级标题样式
- 图题样式
- 表题样式

## 5. MVP 数据流

### 5.1 Spec 提取

```
模板.docx / 成品.docx
    ↓
parse-word
    ↓
DocumentIR
    ↓
query-word-text / query-word-style / render-word-page
    ↓
spec fragments
    ↓
merge-spec-fragments
    ↓
spec.json
    ↓
validate-spec-structure / validate-spec-coverage
```

### 5.2 文档检查

```
待检查.docx + spec.json
    ↓
parse-word
    ↓
DocumentIR
    ↓
rule matching / selector routing
    ↓
report.json
    ↓
report.md
```

## 6. MVP Schema 目标

MVP 只要求 schema 能稳定表达：

- 顶层 `Spec`
- `rules`
- 少量稳定 selector
- 10 到 15 个高频 properties

schema 先服务 checker 与 gate，不追求一次性覆盖所有学校差异。

## 7. MVP 成功标准

- 至少有一套真实模板能通过 workflow 生成可用 `spec.json`
- gate skills 能指出缺失 selector 或结构问题
- 样本文档能稳定发现主要格式问题
- workflow 更换或新增下层 skill 时，不需要整体推翻设计

## 8. 设计判断

这版 MVP 的关键不是“有没有更多功能”，而是：

- 是否已经把能力拆成可重组的 skill
- workflow 是否只负责 orchestration
- gate 是否真的形成闭环
