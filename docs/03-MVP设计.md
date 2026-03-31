# 文档格式检查 Skills MVP 设计

## 1. MVP 目标

验证三件事：

- 用户上传一个学校模板或规范后，系统能生成一份可执行的规则草稿
- 用户上传自己的 `.docx` 后，系统能发现主要格式错误
- 报告足够清楚，让用户知道下一步怎么改

MVP 不追求“覆盖所有格式规则”，只追求“用最少能力打穿一个真实场景”。

这里的“真实场景”是通用引擎下的第一个垂直切片：

- 引擎层：通用 artifact comparison/compliance 抽象
- 业务层：高校论文 `.docx` 格式检查

同时明确一点：

- [06-Spec-Schema草案.md](./06-Spec-Schema草案.md) 与 [07-ArtifactIR与DocumentIR草案.md](./07-ArtifactIR与DocumentIR草案.md) 是 MVP 的目标数据模型
- 首版实现不按“先完整写完 schema/IR/selector engine 再接业务”的顺序推进
- 代码上采用 bottom-up 路径：先跑通真实文档，再把稳定重复模式提炼成抽象

## 2. MVP 范围

### 2.1 只支持

- 输入文档：`.docx`
- 场景：高校论文/毕业设计类文档
- 规则来源：Word 模板 + 文本规范摘要
- 输出：JSON 报告 + Markdown 报告
- 执行模式：`spec -> artifact` 合规检查

### 2.2 不支持

- PDF 作为待检查对象
- 自动修复文档
- 页眉页脚的复杂节切换逻辑
- 公式、文本框、图形对象的精细检查
- 参考文献内容合规性

## 3. MVP 用户路径

### 路径 A：模板建模

1. 上传学校模板 `.docx`
2. 可选上传规范说明文本或 PDF 摘要
3. 系统生成规则草稿 JSON
4. 用户人工确认并保存

### 路径 B：文档检查

1. 选择已保存的规则 spec
2. 上传待检查 `.docx`
3. 系统输出问题报告

## 4. MVP 规则覆盖

首版只覆盖高频且易判定的规则：

- 页边距
- 正文字体
- 正文字号
- 正文行距
- 正文首行缩进
- 正文段前段后距
- 一级标题样式
- 二级标题样式
- 图题样式
- 表题样式

这批规则已经能覆盖用户最关心的格式错误。

## 5. MVP 规则来源策略

MVP 不做复杂多源融合，只采用以下优先级：

1. Word 模板显式样式
2. 用户补充的规范文本
3. 默认推断

若发生冲突：

- 保留模板值为主
- 输出冲突项到 `pending_confirmations`

## 6. MVP 规则 JSON 示例

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
        "line_spacing_mode": "exact",
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
  ],
  "pending_confirmations": []
}
```

## 7. MVP 架构简化

```text
artifact core
  -> docx adapter
  -> 简化 IR
  -> spec draft builder
  -> rule engine
  -> report renderer
```

MVP 不需要复杂后台，命令行或简单 API 即可。

关键要求是：

- 命名上不要写死 `docx checker`
- 代码结构上允许未来增加 `pdf/html/image` adapter

实现降级约束：

- selector 在 MVP 中先视为路由键，不实现通用 DSL 引擎
- IR 先保留可稳定读取的事实，不追求完整样式级联求值
- 定位信息以“用户可修改”为目标，不追求底层 XML 级精确回溯

## 8. MVP 成功标准

- 能处理至少 3 套不同学校模板
- 每套模板都能生成 spec draft
- 在样本论文上能稳定找出主要格式问题
- 报告中的问题描述对用户可理解
- 代码结构允许后续扩展新 artifact，而不重写内核

## 9. MVP 失败标准

以下任一项持续出现，则说明 MVP 范围仍过大或设计有误：

- 规则抽取严重依赖人工重写
- checker 结果不稳定，重复运行不一致
- 定位信息过于模糊，用户无法据此修改
- 为接入新模板需要大改代码
