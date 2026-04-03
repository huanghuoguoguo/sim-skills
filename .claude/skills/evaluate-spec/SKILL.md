---
name: evaluate-spec
description: 评估 spec.md 的覆盖性、具体性和可执行性，帮助 Agent 在用户精校前发现遗漏和歧义。
---

# evaluate-spec

评估 `spec.md` 的质量，不负责把规则重新结构化。

评估结果是一个 gate：

- `pass`：可以进入用户精校 / 下游检查
- `needs_revision`：必须退回修订
- `blocked_user_input`：需用户裁决

## 评估维度

1. **覆盖性** — 是否包含页面设置、正文、标题、图题、表题、摘要、参考文献等主题
2. **具体性** — 规则是否为明确属性和值，而非模糊描述
3. **一致性** — 单位、字号写法、术语是否统一；不同来源之间是否有冲突
4. **可追溯性** — 规则是否标明来自哪个文件、样式或说明
5. **完备性** — 无法确认的项是否进入"待确认项"

## 辅助诊断脚本

- `scripts/check_structure.py <spec.md>` — 检查核心主题是否覆盖
- `scripts/check_conflicts.py <spec.md>` — 检查明显内部冲突（如"小四 vs 10.5pt"）

如果仍可访问上游源文件，可进一步做程序化复核：

```bash
# 1. 用 paragraph-stats 采样正文段落
python3 .claude/skills/paragraph-stats/scripts/run.py <file.docx> \
  --style-hint normal --min-length 20 --require-body-shape \
  --output evidence.json

# 2. Agent 根据 spec.md 构造正文相关的 check 指令 -> checks.json

# 3. 比对正文规则与实际分布
python3 .claude/skills/evaluate-spec/scripts/check_body_consistency.py \
  --evidence evidence.json --checks checks.json
```

**标题规则也应做类似验证**：对每级标题调用 `paragraph-stats --style-hint "heading N"`，比对实际段落的字体/字号与 spec.md 中的规则是否一致。样式定义和实际段落不一致是中文模板中的常见问题。

## 输出

简短评估结果，包含：通过项、缺失项、模糊项、冲突项、建议修改列表。

如果存在以下问题应判为 `needs_revision`：

- 同一规则内部矛盾
- 关键主题缺失
- 规则无法映射到明确检查范围
- 正文规则只引用默认样式，没有实际段落证据

## 约束

- 不要退化成纯格式检查或 schema 验证
- 发现遗漏时，指出缺的规则和缺的证据，不要泛泛而谈
- 最多往返 2-3 轮；仍 unresolved 的项转为"待用户确认项"
