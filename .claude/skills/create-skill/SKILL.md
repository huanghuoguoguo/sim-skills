---
name: create-skill
description: 创建或重构项目内 Skill 代码目录结构的标准指南。
---

# Create Skill Guidelines

当用户要求创建一个新的 Skill，或是让你重构整理已有的 Skill 时，必须遵循以下标准结构规约。

## 1. 标准的 Skill 目录树

一个标准的 Skill 是存放在 `.claude/skills/` 下的独立文件夹。为了保持清晰的工程结构，**不应该将业务代码脚本和 markdown 说明文件混杂在根目录**。

标准的子级结构如下：

```text
.claude/skills/<skill-name>/
├── SKILL.md          # 【必须】技能说明主干，首部必须包含 YAML 声明
├── scripts/          # 【强烈推荐】所有的业务代码、执行脚本（.py, .sh）都应放在这里
├── examples/         # 【可选】可运行的 Demo 脚本，输入/输出参考样例
└── resources/        # 【可选】技能执行时依赖的各种静态模板、配置项或附件
```

**反面模式（Anti-pattern）**：
- 直接在根目录下怼各种 `skill.py`、`test.py`、`run.sh`。

## 2. 关于 SKILL.md 的必备要素

`SKILL.md` 必须通过 Markdown 的 YAML Frontmatter 标明身份，后续必须包含执行指南：

```markdown
---
name: <这里填写技能名称，如 inspect-word>
description: <一句话描述这个技能干嘛用的>
---

# <Skill Name>

## 使用方式 (Usage)
提供准确的命令行调用方式，注意路径应指向 scripts 文件夹内。
例如：`python3 .claude/skills/<skill-name>/scripts/run.py <args>`

## 输入输出 (I/O)
明确描述脚本的入参结构和期望产生的产物（如 JSON 文件结构），或者控制台的输出格式。
```

## 3. 已有 Skill 迁移与重构的 Checklist

当你要帮忙整理（重构）一个旧的、不规范的 Skill 时（比如把 `skill.py` 移入 `scripts/`），一定要检查以下路径依赖问题：

1. **移动文件**：创建 `scripts/` 文件夹，把 `*.py` 和 `*.sh` 移动进去。
2. **修正相对路径**：由于 Python 脚本的所在层级下沉了一层（从 `skills/xxx/` 变成了 `skills/xxx/scripts/`），如果代码中存在基于 `__file__` 推导包路径或其它本地文件的代码（如 `libs_path = Path(__file__).parent.parent / "__libs__"`），**必须同步增加一层 `.parent` 以修正层级错误**。
3. **修正文档**：同步修改 `SKILL.md` 中对应的 Usage 脚本执行路径。
