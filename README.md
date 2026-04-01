# sim-skills

面向 Claude Code 的文档格式检查 skill 规划仓库。

这个项目的目标不是做一个写死流程的“小应用”，而是沉淀一组**可编排的细粒度 skills**，让 agent 按 workflow 自主选择、组合、校验和回退。

## 核心思路

围绕论文/文档格式场景，skills 不再只按“提取 schema / 检查格式”两个成品能力组织，而是按能力层次组织：

1. **Primitive Skills**
   负责读取、查询、渲染、抽取底层事实。
2. **Analysis Skills**
   负责从事实中推断 section、候选规则、差异和 spec 片段。
3. **Gate Skills**
   负责结构校验、覆盖校验、质量验收，形成闭环。
4. **Workflow Skills**
   只负责编排，不把完整流程硬编码在单个脚本里。

## 目标形态

```
用户目标
  ↓
workflow skill
  ↓
primitive / analysis / gate skills
  ↓
artifacts（DocumentIR / spec fragment / spec.json / report.json）
```

Agent 根据 workflow 指示，按需调用多个 skills：

- 需要底层结构时，调用解析类 skill
- 需要定位规范文本时，调用检索类 skill
- 需要处理页面观感冲突时，调用渲染类 skill
- 需要收敛成 spec 时，调用合成与校验类 skill

## 当前 skill 角色

仓库里已有的技能可以先理解为这几类：

- `word`
  当前是基础服务聚合层，内部已经包含 `parse`、`query_text`、`query_style`、`render_page` 这些原子能力
- `extract-spec`
  当前是一个 workflow skill，已经体现出 agentic workflow
- `validate-spec`
  当前是一个 gate skill
- `check-thesis`
  当前是一个成品 workflow，后续应继续拆细
- `compare-docs`
  当前是一个分析型/工作流混合 skill
- `read-text`
  通用辅助 skill

## 下一步规划

推荐把 skill 体系收敛成一张明确的 graph，而不是继续围绕少数“大技能”堆功能。

### 1. Primitive Skills

- `parse-word`
- `query-word-text`
- `query-word-style`
- `render-word-page`
- `read-text`

### 2. Analysis Skills

- `infer-section-types`
- `infer-spec-fragment`
- `merge-spec-fragments`
- `compare-doc-layout`

### 3. Gate Skills

- `validate-spec-structure`
- `validate-spec-coverage`
- `validate-report`

### 4. Workflow Skills

- `extract-spec`
- `check-thesis`
- `compare-docs`

## Skill 设计约束

每个 skill 在定义时都应明确：

- 输入 artifact 是什么
- 输出 artifact 是什么
- 适合在什么阶段调用
- 调完后通常接哪个 skill
- 失败或不确定时如何升级或回退

这比“某个脚本能不能跑”更重要，因为真正的目标是让 agent 稳定编排。

## 当前范围

- 主场景：高校论文 `.docx` / `.dotm`
- 主目标：抽取规范、检查合规、输出结构化报告
- 暂不优先：自动修复、PDF 主检查流、复杂公式/图形对象的精细校验

## 文档

- [产品设计](docs/01-产品设计.md)
- [MVP 实施方案](docs/03-MVP实施方案.md)
- [Spec Schema 草案](docs/04-Spec-Schema草案.md)
