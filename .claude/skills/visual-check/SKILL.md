---
name: visual-check
description: "Use this skill when the Agent has vision capability and needs to visually verify document formatting that cannot be checked by structured parsing alone. Triggers: after batch-check completes and there are rules that require visual verification (page numbers, headers/footers layout, TOC dot leaders, cover page layout, watermarks, figure/table placement, multi-column layout). Also triggers when batch-check results conflict with expectations and visual arbitration is needed. Requires: model with vision capability + render-word-page tool. Do NOT use for properties that batch-check can handle (font, size, spacing, margins)."
---

# visual-check

视觉辅助检查工作流——利用多模态 Agent 的 vision 能力，对结构化工具无法覆盖的格式规则进行视觉核验。

## 定位

这是 check-thesis 的补充能力，**不替代** batch-check。只用于以下场景：

1. 结构化工具无法检查的规则
2. batch-check 结果与预期矛盾，需要视觉仲裁
3. 用户明确要求"看一下"

## 适用规则类型

| 规则类型 | 需要看的页面 | 检查要点 |
|---------|------------|---------|
| 页码格式和位置 | 首页 + 正文首页 | 页码是否居中/右对齐，起始页码是否正确 |
| 页眉页脚内容 | 多个章节首页 | 内容是否正确，是否有分隔线，奇偶页是否不同 |
| 封面版式 | 第 1 页 | 校名、标题、作者信息布局是否符合要求 |
| 目录格式 | 目录页 | 点线引导符、缩进层级、页码对齐 |
| 图表位置 | 含图表的页面 | 图在下/表在上、题注位置、与正文间距 |
| 多栏排版 | 特定页面 | 分栏是否正确 |
| 水印/背景 | 任意页 | 是否存在水印 |
| 装订线 | 任意页 | 内侧边距是否预留装订空间 |

## 工作流程

### 1. 确定需要视觉检查的规则

从原始格式规则中筛出上表中的类型。如果所有规则都能被 batch-check 覆盖，则**不需要**启动视觉检查。

### 2. 选择目标页面

不需要渲染所有页面——按规则类型选择关键页面：

```python
# 典型的页面选择策略
pages_to_check = {
    "cover": 1,           # 封面
    "toc": "query '目录'", # 目录页（先用 query-word-text 定位）
    "body_first": "query '第一章' or '1 引言'",  # 正文首页
    "body_middle": "total_pages // 2",            # 中间页
    "references": "query '参考文献'",             # 参考文献页
}
```

### 3. 渲染目标页面

```bash
# 渲染指定页
python3 .claude/skills/render-word-page/scripts/run.py <file.docx> --page <N> --output page_<N>.png
```

### 4. Agent 视觉分析

对每张渲染图片，Agent 逐条检查适用的视觉规则。

**分析模板**（Agent 应按此格式输出判断）：

```
## 视觉检查 - 第 N 页

### 规则：页码位于页面底部居中
- 判断：通过 / 不通过 / 不确定
- 依据：页面底部可见页码 "3"，位于水平居中位置
- 置信度：高 / 中 / 低

### 规则：页眉包含章节标题
- 判断：通过
- 依据：页眉区域显示 "第三章 系统设计"，与当前章节一致
- 置信度：高
```

### 5. 输出结论

每条视觉检查结论必须包含：

- **规则描述**
- **判断**：通过 / 不通过 / 不确定（需人工确认）
- **依据**：具体看到了什么
- **置信度**：高（明确可见）/ 中（大致符合但细节不清）/ 低（图片模糊或规则模糊）
- **来源标注**：`视觉检查（Agent vision）`

置信度为"低"的项应标记为"待人工确认"。

## 可用工具

| 工具 | 用途 |
|------|------|
| `render-word-page` | 渲染指定页为 PNG |
| `query-word-text` | 定位目录、参考文献等页面位置 |
| `parse-word` | 获取总页数和章节结构信息 |

## 关键约束

- **不要渲染全部页面** — 按需选择 3-5 张关键页面
- **不要重复检查** — batch-check 已覆盖的属性（字体、字号、行距等）不要再用视觉检查
- **明确标注置信度** — vision 判断可能不准确，必须给用户足够的信息来决定是否采信
- **优先结构化工具** — 视觉检查是最后手段，不是默认路径
