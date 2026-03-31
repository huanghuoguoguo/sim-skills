---
name: thesis-format-checker
description: 论文格式检查工具集：Word 文档解析、规则提取、AI 校对、格式检查、文档比对。
---

# Thesis Format Checker Skills

用于论文格式检查的 skill 集合，基于统一的 Word 文档解析服务。

## 架构说明

```
                    word (基础解析服务)
                     /    |    \
                    /     |     \
                   /      |      \
        extract-spec  check-thesis  compare-docs
```

- **word**: 基础 Word 文档解析服务，所有解析操作都通过它完成
- **extract-spec**: 从模板提取格式规则（依赖 word）
- **check-thesis**: 检查论文格式合规性（依赖 word）
- **compare-docs**: 比对两份文档差异（依赖 word）

## 使用场景

### 场景 1：从模板提取规则

```
1. 找到模板文件（.docx 或 .dotm）
2. 调用 extract-spec
3. Review 生成的规则和待确认项
4. 向用户确认待确认项
```

### 场景 2：检查论文格式

```
1. 确认有 spec 文件（没有则先调用 extract-spec）
2. 找到待检查论文（.docx）
3. 调用 check-thesis
4. 汇报检查结果和主要问题
```

### 场景 3：比对两份文档

```
1. 找到参考文档和目标文档
2. 调用 compare-docs
3. 汇报主要差异
```

## 可用 Skills

| Skill | 功能 | 调用方式 |
|-------|------|----------|
| `word` | Word 文档解析 | `python3 .claude/skills/word/scripts/parse.py <file>` |
| `extract-spec` | 从模板提取规则 | `python3 .claude/skills/extract-spec/scripts/run.py <template>` |
| `check-thesis` | 检查论文格式 | `python3 .claude/skills/check-thesis/scripts/run.py <thesis> <spec>` |
| `compare-docs` | 比对文档差异 | `python3 .claude/skills/compare-docs/scripts/run.py <ref> <target>` |
| `read-text` | 读取文本文件 | `python3 .claude/skills/read-text/scripts/run.py <file>` |

## 完整 Workflow

```
模板.dotm → word (解析) → extract-spec → spec.json
                                              ↓
论文.docx → word (解析) → check-thesis → 检查报告.md
```

## 相关文件

- Word 解析服务：`.claude/skills/word/scripts/`
- 各技能目录：`.claude/skills/<skill-name>/scripts/`
