# 文档格式检查 Skills MVP 实施方案

## 1. MVP 开发目标

在最短路径内交付一个可演示、可验证、可继续演化的版本，重点验证规则抽取和格式检查闭环。

同时确保一点：

- MVP 虽然只服务 `.docx`，但代码骨架按“通用内核 + docx adapter”组织

## 2. MVP 交付物

- `.docx` 解析器
- 通用 artifact 内核
- 简化版 IR
- 简化版 spec schema
- 模板 -> spec draft 脚本
- spec -> 文档检查脚本
- JSON 报告
- Markdown 报告
- 一组真实 fixture 样本

## 3. MVP 技术取舍

### 3.1 先做本地工具，不先做复杂平台

首版形式建议：

- CLI 工具
- 或极简 FastAPI 服务

不先做：

- 完整前端
- 用户系统
- 异步任务编排
- 多租户管理

### 3.2 先做 deterministic pipeline

即：

- parser 输出固定
- rule engine 输出固定
- AI 只参与生成 spec 草稿

这样更容易调试和建立信心。

## 4. MVP 任务拆分

### 任务 1：定义 schema 与 IR

产出：

- `Artifact`
- `DocumentIR`
- `Fact`
- `Spec`
- `Rule`
- `Issue`

### 任务 2：实现 DOCX 解析

首版仅解析：

- 段落
- run
- 样式名
- 字体字号
- 行距
- 段前段后
- 缩进
- 页边距
- 表格和图片题注段落

实现要求：

- 对外暴露为 `docx adapter`
- 不把后续模块命名成 Word 专用模块

### 任务 3：实现模板规则抽取

逻辑：

- 从模板中抓正文样式、标题样式、题注样式
- 用规则映射生成 spec draft
- 对无法确认字段打 `pending_confirmations`

### 任务 4：实现规则检查

逻辑：

- 根据 selector 找目标段落
- 按 property 比较
- 输出 issue 列表

实现要求：

- comparator 接口预留双输入模式
- 当前只落地 `spec -> artifact` 这一种执行方式

### 任务 5：实现报告渲染

输出：

- `report.json`
- `report.md`

### 任务 6：建立样本集

至少准备：

- 1 份模板文档
- 1 份合格论文
- 3 份带典型错误的论文

## 5. 推荐开发顺序

1. 先定义 schema 和测试样例
2. 再做 parser
3. 再做 checker
4. 再接 spec draft builder
5. 最后接 AI 辅助抽取

原因：

- parser 和 checker 是底盘
- AI 流程放太前面会掩盖真实工程问题
- 先把通用接口定稳，比后面返工重构成本低

## 6. 时间规划建议

### 第 1 周

- schema
- fixture 收集
- DOCX parser 骨架

### 第 2 周

- parser 打通
- rule engine 打通
- issue 模型落地

### 第 3 周

- spec draft builder
- AI normalize 实验
- 基础报告输出

### 第 4 周

- 样本回归
- 文档补齐
- MVP 演示准备

## 7. MVP 验证方式

### 功能验证

- 模板能生成 spec draft
- 待检查文档能输出 issue 列表
- 内核接口能自然容纳未来的双 artifact 比对

### 质量验证

- 主要问题召回率是否足够高
- 误报是否可接受
- 报告是否帮助用户快速修改

### 业务验证

- 换一套学校模板能否在低成本下接入
- 用户是否愿意接受“先检查后修正”的产品形态

## 8. MVP 风险

- 模板样式名不规范，导致抽取困难
- 用户文档未正确套用模板样式
- 题注识别可能依赖文本模式而不是样式
- 抽象设计不到位，后续扩展时出现命名和模块耦合

## 9. MVP 风险应对

- 首版同时支持样式识别与简单文本模式识别
- 对识别不确定项显式提示，不硬判
- 用真实学校模板驱动开发，不靠理想化样本
- 在 MVP 阶段只抽象稳定接口，不提前实现多格式能力
