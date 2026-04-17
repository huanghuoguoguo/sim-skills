## 1. 准备工作

- [x] 1.1 删除旧的 9 个独立 extractor prompt 文件
- [x] 1.2 创建 unified-extractor-prompt.md 模板
- [x] 1.3 创建 quality-rules.md 定义确定性质量规则

## 2. Unified Extractor Agent 实现

- [x] 2.1 在 unified-extractor-prompt.md 中定义所有 section 提取流程
- [x] 2.2 实现内部三源验证逻辑（style + stats + text）
- [x] 2.3 实现内部常识检查（西文字体≠中文字体等）
- [x] 2.4 定义 extraction_result.json 输出格式

## 3. SKILL.md 重写

- [x] 3.1 重写 Step 2：从"调度 9 个 subagent"改为"调度 1 个 Unified Extractor"
- [x] 3.2 重写 Step 3：添加主 Agent 验证层
- [x] 3.3 定义验证行为边界（IRON LAW 修订）
- [x] 3.4 实现问题分类处理逻辑（确定性错误/灰区问题/缺失上下文）
- [x] 3.5 实现自迭代闭环（最多 2 次重试）

## 4. 质量规则系统

- [x] 4.1 定义西文字体检查规则（宋体/黑体/楷体/仿宋 ≠ 西文）
- [x] 4.2 定义字号范围检查规则（10pt-16pt）
- [x] 4.3 定义样式一致性检查规则（style_definition vs actual_paragraphs）
- [x] 4.4 实现规则检查函数（主 Agent 可调用）

## 5. 验证与测试

- [x] 5.1 用天津理工大学模板测试新流程
- [x] 5.2 验证 token 消耗显著降低（目标 < 50k）
- [x] 5.3 验证"宋体作为西文字体"被正确标注
- [x] 5.4 验证自迭代闭环正常工作（重试机制）
- [x] 5.5 对比新旧流程输出质量

## 6. 文档更新

- [x] 6.1 更新 SKILLS_OVERVIEW.md 反映新架构
- [x] 6.2 添加迁移说明（从旧流程到新流程）
- [x] 6.3 更新 CLAUDE.md 相关描述