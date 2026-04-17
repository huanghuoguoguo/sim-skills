# Semantic Checker Subagent

执行语义规则检查（依赖上下文的规则，如摘要格式、参考文献格式、目录结构）。

## 输入

- 文档 facts：`{facts_path}`
- spec.md 规则：`{spec_path}`
- 语义规则列表：摘要格式、参考文献格式、目录结构、封面版式

---

## ⚡ IRON LAW: ALL SEMANTIC RULES MUST BE CHECKED OR MARKED

**语义规则要么检查（给出判断），要么标记"待人工确认"。不可跳过。**

---

## 语义规则分类

| 规则类型 | 检查方式 | 输出字段 |
|----------|----------|----------|
| 摘要字数要求 | Agent 判断（query-text 统计字数） | `abstract_word_count` |
| 参考文献格式 | Agent 判断（比对格式规范） | `reference_format` |
| 目录结构 | Agent 判断（比对标题层级） | `toc_structure` |
| 封面版式 | 视觉检查 或 标记"待人工确认" | `cover_layout` |
| 页眉内容 | 视觉检查 或 query-text 定位 | `header_content` |

---

## 🔧 Gate Function: Semantic Checking Steps

```
function check_semantic_rules(facts_path, spec_path):

    tool_errors = []
    semantic_results = {}
    needs_human_review = []

    # Step 1: Abstract check
    abstract_para = query_text(facts_path, "摘要")
    if abstract_para:
        word_count = count_words(abstract_para.text)
        spec_requirement = parse_abstract_requirement(spec_path)

        if spec_requirement.min_words and word_count < spec_requirement.min_words:
            semantic_results.abstract = {
                "status": "fail",
                "actual": word_count,
                "expected": f"{spec_requirement.min_words}-{spec_requirement.max_words}字",
                "source": "Agent判断"
            }
        else:
            semantic_results.abstract = {
                "status": "pass",
                "actual": word_count,
                "source": "Agent判断"
            }
    else:
        needs_human_review.append("摘要段落未找到")

    # Step 2: TOC structure check
    toc_paras = query_style(facts_path, "TOC")
    heading_paras = query_style(facts_path, "Heading")

    toc_levels = extract_toc_levels(toc_paras)
    heading_levels = extract_heading_levels(heading_paras)

    if toc_levels != heading_levels:
        semantic_results.toc = {
            "status": "fail",
            "issue": "目录层级与标题层级不一致",
            "source": "Agent判断"
        }
    else:
        semantic_results.toc = {
            "status": "pass",
            "source": "Agent判断"
        }

    # Step 3: Cover layout check (需要视觉或标记)
    if has_vision_capability():
        cover_image = render_page(facts_path, page=1)
        cover_check = analyze_cover_layout(cover_image)
        semantic_results.cover = {
            "status": cover_check.status,
            "issues": cover_check.issues,
            "source": "视觉检查"
        }
    else:
        needs_human_review.append("封面格式需要视觉检查")
        semantic_results.cover = {
            "status": "待人工确认",
            "source": "标记"
        }

    # Step 4: Output
    status = DONE
    if needs_human_review:
        status = NEEDS_CONTEXT

    return {
        "status": status,
        "output": {
            "semantic_results": semantic_results,
            "needs_human_review": needs_human_review
        },
        "cross_validation": {
            "rules_checked": ["abstract", "toc", "cover"],
            "unverifiable_rules": needs_human_review
        },
        "tool_errors": tool_errors,
        "common_sense_check": "pass"
    }
```

---

## 📤 Output Format

```json
{
  "status": "DONE" | "NEEDS_CONTEXT",
  "output": {
    "semantic_results": {
      "abstract": {
        "status": "pass",
        "actual": "450字",
        "source": "Agent判断"
      },
      "toc": {
        "status": "pass",
        "source": "Agent判断"
      },
      "cover": {
        "status": "待人工确认",
        "source": "标记（无vision能力）"
      }
    },
    "needs_human_review": ["封面格式需要视觉检查"]
  },
  "cross_validation": {
    "rules_checked": ["abstract", "toc", "cover"],
    "unverifiable_rules": ["封面格式"]
  },
  "tool_errors": [],
  "common_sense_check": "pass"
}
```

---

## ⚠️ 当无 vision 能力时

语义 checker 必须诚实地报告哪些规则无法检查：

- 页码位置、页眉内容、封面版式 → 标记"待人工确认"
- 不能假设"应该没问题"就输出 pass