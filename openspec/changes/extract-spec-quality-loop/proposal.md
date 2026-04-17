## Why

当前 extract-spec 架构存在三个核心问题：

1. **Token 消耗过高**：9 个并行 subagent 各约 20k tokens = 180k，每个独立加载上下文
2. **缺乏验证者**：主 Agent 只做形式检查，无法验证内容质量（如"宋体作为西文字体"）
3. **无自迭代机制**：用户必须手动发现问题，没有自动检测→修正→验证闭环

需要重构为：单 Agent 提取 + 主 Agent 验证 + 质量规则检查 + 自动迭代。

## What Changes

### 架构变更

- **合并 Extractor**：从 9 个并行 subagent 合并为 1 个 Unified Extractor Agent
- **新增验证角色**：主 Agent 获得验证能力，可直接调用 stats/query 抽样检查
- **质量规则系统**：定义确定性质量规则（西文字体≠中文字体等）
- **自迭代闭环**：发现问题→分类→重试/标注/询问用户

### IRON LAW 修订

- **旧版本**：主 Agent 不直接执行任务（限制过多）
- **新版本**：区分"执行"与"验证"边界，验证是允许的

### 文件变更

- `.claude/skills/extract-spec/SKILL.md` - 重写执行流程
- `.claude/skills/extract-spec/unified-extractor-prompt.md` - 新建统一提取 prompt
- `.claude/skills/extract-spec/quality-rules.md` - 新建质量规则定义
- 删除 9 个独立 extractor prompt 文件

## Capabilities

### New Capabilities

- `spec-quality-validation`: 规范输出质量验证能力，包括确定性规则检查、问题分类、自动迭代机制
- `unified-extraction`: 统一提取能力，一个 Agent 处理所有 section 的数据提取

### Modified Capabilities

无现有 spec 需修改（这是新架构，不改变 spec 格式）

## Impact

### 代码变更

- `.claude/skills/extract-spec/SKILL.md` - 完整重写
- `.claude/skills/extract-spec/` 目录下的 prompt 文件 - 合并删除

### Token 消耗

- 旧：~180k tokens
- 新：~40k tokens（节省约 78%）

### 用户体验

- 用户不再需要手动发现常识性问题
- 只需确认灰区问题和提供缺失上下文