---
name: validate-spec
description: 专门负责检查由 Agent 输出的 spec.json 是否在字段、结构上呈现闭环（检查必需字段如 body.paragraph 是否被遗漏），防止输出错误或不完整的 JSON。
---

# validate-spec 技能要求

这是一个纯粹的**结构与完整性验收技能**。
当完成提取或生成新的规范围 JSON 时，必须主动调用此技能对结果 JSON 进行完整性校验。

### API 用法：
```bash
python3 .claude/skills/validate-spec/scripts/validate.py <path_to_spec.json>
```

### 你的职责：
1. **多粒度校验反馈**：验证脚本会检测这份 JSON 是否包含了结构化所需的所有核心 `selector`（例如 `body.paragraph`, `body.heading.level1`, `abstract.body` 等）和 `layout` 属性。
2. **强制修补**：如果校验脚本报告类似于“缺失 `body.paragraph`”的错误，你不可以逃避！这说明你提取阶段漏掉了这个最重要的数据。你必须返回原始资料（或参考你脑海中的经验），针对确实缺失的部分进行修补，并将规则补齐，然后再次调用这个校验技能。
3. **输出把控**：只有当 `validate.py` 返回 `✅ SCHEMA VALIDATION PASSED` 时，你才可以相信这套 JSON 格式符合开发系统要求，进而交付任务。
