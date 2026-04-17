## Context

当前 extract-spec skill 采用 9 个并行 subagent 架构：
- 每个 subagent 独立加载 facts.json 和 prompt 模板
- 主 Agent 只做形式检查（字段存在性），无法验证内容质量
- IRON LAW 禁止主 Agent 调用工具，导致无法抽样验证
- 用户必须手动发现常识性问题（如"宋体作为西文字体")

约束：
- 保持 subagent 架构（不改为主 Agent 直接执行）
- 必须有独立验证机制
- Token 消耗需显著降低

## Goals / Non-Goals

**Goals:**
- 将 9 个 subagent 合并为 1 个 Unified Extractor Agent
- 主 Agent 获得验证能力（可调用 stats/query 抽样）
- 定义确定性质量规则（可自动检测的问题）
- 建立自迭代闭环（发现问题→分类→处理）

**Non-Goals:**
- 不改变 spec.md 输出格式
- 不改变 parse-word 等底层工具
- 不实现 AI 自动推断缺失值（保持用户确认机制）

## Decisions

### Decision 1: 合并 Extractor 为单 Agent

**选择**: 1 个 Unified Extractor Agent 处理所有 section

**备选方案**:
- A: 9 个并行 subagent（当前） - 180k tokens，无验证
- B: 2-3 个分组 subagent（layout+font, text-based, structure） - 约 60k
- C: 1 个 Unified Extractor - 约 30k + 主 Agent 验证 10k

**理由**: C 最精简，且主 Agent 验证能力弥补单 Agent 漏检风险

### Decision 2: 验证者角色归属

**选择**: 主 Agent 担任验证者，可直接调用工具

**备选方案**:
- A: 新增 Validator Agent - 增加复杂度
- B: 主 Agent 验证（修订 IRON LAW） - 最精简

**理由**: B 不增加 Agent 数量，验证逻辑简单（规则检查），主 Agent 可胜任

### Decision 3: IRON LAW 修订

**选择**: 区分"执行"与"验证"边界

**修订内容**:
```
主 Agent 禁止执行:
- 解析原始文档
- 从零提取规则内容
- 自己推断缺失值

主 Agent 允许验证:
- 读取中间结果
- 调用 stats/query 抽样检查
- 执行质量规则（确定性检查）
- 标注问题
- 要求重试

区分标准:
执行 = 从原始数据产生新内容
验证 = 检查已有内容是否正确
```

**理由**: 保持"调度者"角色，但赋予必要验证能力

### Decision 4: 质量规则类型

**选择**: 只定义确定性规则，灰区问题标注待用户确认

**规则示例**:
| 规则 | 检查方式 | 处理 |
|------|----------|------|
| 西文字体≠宋体/黑体/楷体/仿宋 | 字面检查 | 标注"⚠️ 待确认" |
| 字号∈[10pt,16pt] | 范围检查 | 超范围标注异常 |
| 样式定义vs实际段落一致 | stats 抽样 | 冲突标注 |

**灰区问题**（无法自动裁决）:
- 模板确实要求中文字体作为西文字体 → 标注待用户确认
- 多种字号混用 → 标注分布情况

### Decision 5: 自迭代闭环设计

**选择**: 最多 2 次重试，超过则标注待用户确认

```
迭代流程:
─────────────────────────────────────
Extractor Agent → extraction_result.json
         │
         ▼
主 Agent 验证
         │
         ├─ Pass → 合并输出
         │
         ├─ 确定性错误 → 重试 Extractor (最多2次)
         │
         ├─ 灰区问题 → 标注"⚠️待确认"
         │
         └─ 缺失上下文 → 询问用户
         │
         ▼
合并最终输出
```

## Risks / Trade-offs

### Risk 1: 单 Agent 漏检

**风险**: Unified Extractor 可能遗漏某些 section

**缓解**:
- 主 Agent 可调用 stats 验证各 section 是否覆盖
- 质量规则定义最低覆盖标准

### Risk 2: 主 Agent 验证能力滥用

**风险**: 主 Agent 可能"越权"开始执行提取

**缓解**:
- IRON LAW 明确禁止执行行为
- 只允许"读取"和"抽样验证"，不允许"提取"

### Risk 3: 质量规则覆盖不全

**风险**: 无法定义所有质量问题

**缓解**:
- 灰区问题标注待用户确认，不强制自动解决
- 逐步迭代补充规则库