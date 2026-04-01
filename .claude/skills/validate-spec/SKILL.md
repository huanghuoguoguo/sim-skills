---
name: validate-spec
description: 检查 spec.json 是否结构合法、字段自洽，确保下游 Agent 可以消费。
---

# validate-spec

这是唯一公开的 spec 校验入口。

**定位变化**：从"严格程序校验"改为"Agent 友好校验"。

目标很简单：

- `spec.json` 结构合法（JSON 闭合、必填字段存在）
- `rules` 基本形状正确（有 id、selector、properties）
- 不限制 selector 和 property 的具体内容

它不做的事情：

- 不限制 selector 必须是预定义列表中的值
- 不限制 property 必须是预定义类型
- 不要求规则必须能被当前 Python 程序执行

这类判断交给下游 Agent：
- 如果下游是 Python 检查器，它会自动跳过不认识的 selector
- 如果下游是 LLM Agent，它会理解并尝试判断

说明、依据、待确认项放在同目录下的 `spec.md`，由人类和 Agent 阅读与维护。

### API 用法

```bash
python3 .claude/skills/validate-spec/scripts/validate.py <path_to_spec.json>
```

执行顺序：

1. 结构校验（必填字段、类型检查）
2. 规则形状校验（id、selector、properties 存在性）
3. 基本自洽性（数值类型、severity 合法性）

校验通过即可交付，具体规则能否被执行交给下游判断。
