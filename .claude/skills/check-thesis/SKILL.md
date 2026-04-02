---
name: check-thesis
description: 基于定稿 spec.md 检查论文格式，混合使用 Python 工具处理确定性规则，使用 Agent 处理语义性规则。
---

# check-thesis

检查论文文档是否符合给定的 `spec.md`，输出 Markdown 检查报告。

## 输入

- 待检查论文：`.docx`
- 定稿的 `spec.md`

不要要求或回推 `spec.json`。`spec.md` 本身就是下游输入。

## 工作方式

### 1. 读取规则

- 逐条阅读 `spec.md`
- 把规则拆成检查清单，不要漏掉任何一条
- 先区分“确定性规则”和“语义性规则”

### 2. 获取事实

- 调用 `parse-word` 解析论文结构
- 必要时调用 `query-word-text` 辅助定位摘要、目录、参考文献等语义区域
- 只有在文字证据和样式证据冲突时，才调用 `render-word-page`

### 3. 检查确定性规则

这类规则优先交给 Python 批量执行：

- 字体
- 字号
- 行距
- 页边距
- 缩进
- 段前段后
- 对齐
- 标题样式
- 图题/表题格式

目标接口是把 `spec.md` 中的规则翻译为结构化检查指令，再交给批量检查脚本执行。

脚本分层：

- `scripts/translate_spec.py`：`spec.md -> checks`
- `scripts/batch_check.py`：执行确定性检查
- `scripts/summarize_results.py`：把原始失败项压缩为 Agent / 用户都更容易消费的聚合摘要
- `scripts/run.py`：workflow 包装层，汇总 JSON 和 Markdown 报告

这些脚本默认使用论文域 profile，但不应假设所有学校都沿用同一组标题/样式名：

- 如果 `spec.md` 的章节命名、标题映射、图表题前缀与默认 profile 不一致，应优先通过 `--profile-json` 或覆盖参数调整
- 不要在 prompt 里暗示“正文一定是 Normal”“标题一定是 Heading 1/2/3”

指令示例：

```json
{
  "checks": [
    {"type": "font", "scope": "east_asia", "selector": "style:Normal", "expected": "宋体", "expected_display": "宋体"},
    {"type": "font_size", "selector": "style:Normal", "expected": 12, "expected_display": "小四（12pt）"},
    {"type": "line_spacing", "selector": "style:Normal", "expected": {"mode": "multiple", "value": 1.5}, "expected_display": "1.5倍行距"},
    {"type": "margin", "side": "left", "expected": 3.0, "expected_display": "3.0cm", "selector": "document:layout"}
  ]
}
```

### 4. 检查语义性规则

这类规则由 Agent 判断：

- 摘要格式
- 参考文献格式
- 目录结构
- 其他依赖位置、上下文或文本模式识别的规则

结论里要明确标注这是 `Agent 判断`，并给出匹配依据。

注意：

- Python workflow 可以先把这些规则识别并单独列出
- 真正的语义判定仍然需要 Agent 或人工复核

### 5. 输出报告

报告必须是 Markdown，每条结果至少包含：

- 规则描述
- 检查结果：通过 / 不通过 / 待人工确认
- 期望值 vs 实际值
- 定位信息：页、段落或文本片段
- 来源标注：`Python 检查` 或 `Agent 判断`

报告面向用户修文，不要重复堆叠同一类错误：

- 同一规则下的多处失败应聚合展示
- 主要输出“异常数量 + 位置样例 + 常见实际值”
- 重复性错误不要逐段展开成长列表

### 6. 完整性回溯

检查结束后，必须回到 `spec.md` 逐条核对：

- 每条规则都已检查，或明确说明为什么无法检查
- 没有因为中途改写清单而漏掉规则

## 中间产物

下游 workflow 应保留程序化中间产物，不要把整篇论文和全部失败项硬塞进 Agent 上下文：

- `facts.json`：论文结构化事实
- `translated_spec.json`：从 `spec.md` 翻译出的检查指令
- `batch_result.json`：确定性检查原始结果
- `grouped_failures.json`：聚合后的失败摘要
- `agent_payload.json`：供后续 Agent 消费的紧凑输入

## 约束

- 不要重新引入 `spec.json`
- 不要把“Python 跳过的规则”再拆成独立的旧式 `agent-check-report` 流程
- 报告首先服务用户复核，不是为了机器验收
