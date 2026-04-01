# MVP 实施方案

## 1. MVP 目标

MVP 的目标不再是“做出 3 个固定技能”，而是验证下面这件事：

**agent 能否基于一组细粒度 skills，自主完成 `提取 spec -> 校验 -> 检查文档 -> 输出报告` 的闭环。**

因此，MVP 要验证的重点是：

- skill graph 是否足够清晰
- workflow 是否能稳定调用多个下层 skills
- artifacts 是否足够明确，能支撑回退与补偿
- gate skills 是否能形成闭环

## 2. MVP 交付物

- 一组可调用的 primitive skills
- 至少一个 workflow skill：`extract-spec`
- 至少一个 workflow skill：`check-thesis`
- 一组 gate skills，用于 spec/report 验收
- 明确的 artifact 约定
- 一组真实样本，用于回归验证

## 3. MVP 分层

### 3.1 Primitive Skills

第一批建议落地：

- `parse-word`
- `query-word-text`
- `query-word-style`
- `render-word-page`
- `read-text`

短期内，这些能力可以暂时仍由 `word` 目录承载；但在规划上，应把它们视为独立 skill，而不是 `word` 的附属脚本。

### 3.2 Analysis Skills

第一批建议落地：

- `infer-spec-fragment`
- `merge-spec-fragments`
- `compare-doc-layout`

这些 skills 可以一开始先只覆盖最小 thesis 场景，不追求通用化。

### 3.3 Gate Skills

第一批建议落地：

- `validate-spec-structure`
- `validate-spec-coverage`
- `validate-report`

其中 `validate-spec` 可以作为过渡实现，但后续应拆开，避免结构校验和场景覆盖耦合在一起。

### 3.4 Workflow Skills

MVP 先保留两条主 workflow：

- `extract-spec`
- `check-thesis`

`compare-docs` 可作为旁路 workflow，用于辅助分析和未来扩展。

## 4. Artifact 约定

### 4.1 `DocumentIR`

上游来源：

- `parse-word`

下游消费者：

- `query-word-*`
- `infer-spec-fragment`
- `check-thesis`
- `compare-docs`

### 4.2 `spec-fragment.json`

上游来源：

- `infer-spec-fragment`

下游消费者：

- `merge-spec-fragments`
- `validate-spec-coverage`

### 4.3 `spec.json`

上游来源：

- `merge-spec-fragments`

下游消费者：

- `validate-spec-*`
- `check-thesis`

### 4.4 `report.json`

上游来源：

- `check-thesis`

下游消费者：

- `validate-report`
- `report.md` 渲染

## 5. 推荐目录规划

目标目录形态：

```
.claude/
└── skills/
    ├── parse-word/
    ├── query-word-text/
    ├── query-word-style/
    ├── render-word-page/
    ├── read-text/
    ├── infer-spec-fragment/
    ├── merge-spec-fragments/
    ├── validate-spec-structure/
    ├── validate-spec-coverage/
    ├── validate-report/
    ├── extract-spec/
    ├── check-thesis/
    └── compare-docs/
```

现实迁移阶段允许保留：

```
.claude/skills/word/scripts/*
```

但需要把这些脚本在设计上重新映射为独立 skill 能力。

## 6. 任务分解

### 任务 1：定义 skill graph 与命名

产出：

- skill 分层清单
- skill 命名规范
- 上下游依赖图

验收标准：

- 能看出 primitive / analysis / gate / workflow 的边界
- 新能力能明确知道该落在哪一层

补充准则：

- 不以“函数数量”决定 skill 数量
- 优先按 artifact 边界、复用价值和回退价值拆分
- workflow skill 不承担本应下沉为 capability skill 的确定性执行细节

### 任务 2：定义 artifact 契约

产出：

- `DocumentIR` 约定
- `spec-fragment` 约定
- `spec.json` 约定
- `report.json` 约定

验收标准：

- 各 skill 之间不靠隐式口头约定传递结果

补充准则：

- 每个 artifact 都要明确生产者和消费者
- 能落盘的中间结果尽量可复用、可检查
- 对后续视觉核验有价值的中间结果，应显式保留引用关系

### 任务 3：把现有 `word` 能力重新命名和升格

产出：

- `parse-word`
- `query-word-text`
- `query-word-style`
- `render-word-page`

说明：

- 短期不一定要移动脚本文件
- 但 skill 定义与调用语义要先拆开

验收检查：

- 这些能力是否会被多个 workflow 复用
- 是否存在明确输入输出
- 是否值得被独立替换或验收
- 是否失败后需要单独回退

只有大部分答案为“是”时，才升格为独立 skill。

### 任务 4：补齐 gate skills

产出：

- 结构验收
- 覆盖验收
- 报告验收

说明：

- 不再让单个 `validate-spec` 同时承担所有职责
- gate skill 必须能明确告诉 workflow “回退到哪一步补偿”

### 任务 5：收敛 `extract-spec` workflow

产出：

- 明确的阶段化编排
- 对失败场景的回退逻辑
- 对不确定项的补偿提取逻辑

关键要求：

- workflow skill 不直接等同于某个脚本
- workflow 要能替换下游 skill，而不是写死实现
- 遇到结构事实、文本说明、视觉观感冲突时，允许按优先级裁决

推荐裁决顺序：

1. 程序化事实
2. 文本规范线索
3. 视觉核验
4. gate 验收结论

### 任务 6：收敛 `check-thesis` workflow

产出：

- 文档解析
- selector 路由
- 规则比对
- 报告渲染
- 报告验收

关键要求：

- 把“检查”和“验收”拆开
- 为后续自动修复保留接口
- 如果当前模型支持视觉，可加入截图复核通道
- 如果当前模型不支持视觉，workflow 仍需能在纯程序化路径下完成

### 任务 7：建立样本集

至少准备：

- 1 份模板文档
- 1 份合格论文
- 2 到 3 份带典型错误的论文
- 1 份规范文本样本

## 7. 开发顺序

1. 先定 skill graph 和 artifact 契约
2. 再把现有 `word` 能力按原子 skill 重新命名
3. 再补 gate skills，形成闭环
4. 再收敛 `extract-spec` workflow
5. 最后收敛 `check-thesis` workflow 和报告出口

原因：

- 这次最怕的不是功能少，而是边界乱
- 如果先继续堆“大技能”，后面只会越来越难拆

## 8. MVP 验证方式

### 功能验证

- agent 能从模板文档出发，按 workflow 调用多个 skills 生成 `spec.json`
- gate skills 能指出缺漏并驱动补偿提取
- `spec.json` 能驱动待检查文档输出 `report.json`

### 架构验证

- 新增一个原子能力时，不需要重写整个 workflow
- 替换某个下层 skill 时，上层 workflow 只需调整编排，不需要整体推倒
- 文档中的每个 skill 都有明确输入、输出和下一跳

### 业务验证

- 换一套学校模板时，主要变的是提取结果，不是系统结构
- 用户仍然只需要用自然语言描述目标，不需要手动编排底层技能

## 9. 迁移策略

### 阶段 A：语义重构

- 先重写文档
- 先给现有能力重新命名和分层
- 暂不强求目录结构完全一致

### 阶段 B：skill 拆分

- 把 `word` 里的原子脚本逐步升格成独立 skill
- 把 `validate-spec` 拆成多个 gate skills

### 阶段 C：workflow 去脚本绑定

- `extract-spec` 和 `check-thesis` 从“脚本入口说明”演化成“编排说明”
- 逐步减少 workflow 中对具体文件路径的硬编码依赖

## 10. 风险与应对

### 风险 1：skill 爆炸

应对：

- 只在 artifact 边界稳定、调用价值明确时新增 skill
- 建立统一拆分检查表，避免“每个函数一个 skill”

### 风险 2：workflow 过薄，无法落地

应对：

- workflow 至少要定义阶段、判断条件、回退逻辑和验收门
- workflow 仍然可以调用细粒度脚本，但脚本通过 capability skill 暴露，而不是直接把脚本堆到用户层

### 风险 3：gate 规则仍然写死在 thesis 场景

应对：

- 把场景覆盖要求抽成 profile
- 允许不同 workflow 选择不同 coverage profile

### 风险 4：视觉能力引入后权重失控

应对：

- 视觉只作为增强取证通道，不覆盖全部程序化事实
- 只有在冲突、不确定、布局敏感的场景下才触发视觉核验
- workflow 必须支持“模型无视觉能力”的退化路径
