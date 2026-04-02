# MVP 实施方案

## 1. 目标

跑通"参考文件 → spec.md → 检查报告"的完整闭环。

## 2. 现有资产

以下脚本已有实现基础，需要评估和适配：

| 现有路径 | 状态 |
|---------|------|
| `parse-word/scripts/run.py` | 可用，确认输出格式 |
| `query-word-text/scripts/run.py` | 可用 |
| `query-word-style/scripts/run.py` | 需确认继承链解析完整性 |
| `render-word-page/scripts/run.py` | 可用 |
| `check-thesis/scripts/run.py` | 需重构：去掉 spec.json 依赖，改为接受检查指令 |

## 3. 实施任务

### 任务 1：工具脚本适配

- [ ] 确认 parse_word 输出包含完整事实（段落、样式、布局、页眉页脚）
- [ ] 确认 query_style 正确解析样式继承链，返回最终值
- [ ] 重构 batch_check：接受检查指令 JSON，输出结构化结果
- [ ] 统一脚本入口和参数风格

### 任务 2：上游 Skill

- [ ] 编写 `extract-spec/SKILL.md`
  - 指导 Agent 识别文件类型（模板/成品/说明）
  - 指导 Agent 如何综合多来源信息
  - 定义 spec.md 的内容结构
- [ ] 编写 `evaluate-spec/SKILL.md`
  - 定义"好的 spec.md"的标准（完整、清晰、可执行）
  - 指导 Agent 逐项自评

### 任务 3：下游 Skill

- [ ] 编写 `check-thesis/SKILL.md`
  - 指导 Agent 拆分确定性规则 vs 语义性规则
  - 给出 batch_check 指令格式和示例
  - 要求检查完成后做 checklist 回溯
  - 定义报告格式（含来源标注）

### 任务 4：端到端验证

- [ ] 准备测试材料（模板 + 说明 + 论文）
- [ ] 上游测试：提取 spec.md → 用户审核
- [ ] 下游测试：检查论文 → 审核报告质量
- [ ] 验证完整性（spec.md 规则数 vs 报告检查项数）

## 4. 目录规划

```
.claude/skills/
├── extract-spec/
│   └── SKILL.md
├── evaluate-spec/
│   └── SKILL.md
├── check-thesis/
│   ├── SKILL.md
│   └── scripts/
│       └── batch_check.py
└── word/
    └── scripts/
        ├── docx_parser.py        # 文档解析核心
        ├── docx_parser_models.py  # 解析数据模型
        └── ...                    # query、render 等
```

## 5. 实施顺序

1. 工具脚本基础（parse_word、query_style 继承链）
2. 上游通路（extract-spec + evaluate-spec Skill）
3. batch_check 实现
4. 下游通路（check-thesis Skill）
5. 端到端验证

## 6. 风险与应对

| 风险 | 应对 |
|------|------|
| 样式继承链解析不完整 | 优先测试 query_style，用真实模板验证 |
| Agent 提取规则遗漏 | evaluate-spec 引导自评 + 用户精校 |
| batch_check 指令格式不清晰 | check-thesis SKILL.md 中给明确示例 |
| Agent 检查遗漏规则 | SKILL.md 要求 checklist 回溯 |
| 语义规则判断不稳定 | 报告标注来源，用户可识别 Agent 判断 |

## 7. 可清理的历史组件

新架构下不再需要：

| 组件 | 原因 |
|------|------|
| `infer-spec-fragment/` | 不再需要结构化 fragment |
| `merge-spec-fragments/` | 不再需要 fragment 合并 |
| `validate-spec/` 系列 | 改为 Agent 自评（evaluate-spec） |
| `agent-check-report/` | 下游 Agent 本身处理语义规则 |
| `spec.json` schema 和验证逻辑 | 产物改为 spec.md |
| `validate-spec-structure/` 等空壳 | 直接删除 |
