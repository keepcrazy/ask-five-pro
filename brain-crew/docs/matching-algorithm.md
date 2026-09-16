# Ask Five Pro 专家匹配算法

本文件解释 `brain-crew/scripts/matching_core.py` 的现行实现。它不定义名单确认、人格加载或会议流程。

## 输入与输出

输入包括议题文本、1–3 个主类别、六种会议模式之一，以及可选的显式 include/exclude ID。输出是评分列表和经过同质化调整后的候选 panel。

## 主链路评分

```text
score = domain_score * 3
      + tag_score * 2
      + style_score
      + mode_tag_bonus
```

- `domain_score`：专家核心领域与主类别的重叠比例。
- `tag_score`：专家 topic tag 在议题文本中的命中比例。
- `style_score`：专家风格与会议模式偏好的重叠比例。
- `mode_tag_bonus`：红队、预审、淬火对原有风险/验证标签的加权。

该公式以 v2.2.3 的 `scripts/match-experts.py` 为兼容基线。

## 类别别名

只支持以下双向等价：

- 团队 ↔ 组织
- 技术 ↔ 工程
- 风险 ↔ 风控

实现通过类别规范化比较，不增加第四组近义词。

## 敏感专家

敏感专家默认在评分前排除。以下两种情况可以进入候选：

1. 用户明确点名，对应 ID 通过 include 传入；
2. 会议模式为对抗。

谈判、权力、舆论等主题本身不构成授权。

## 选择与去同质化

目标人数：

| 主类别数量 | 目标人数 |
|---:|---:|
| 1 | 3 |
| 2 | 4 |
| 3 | 5 |

候选按原始分数排序。每加入一位专家，对后续与已选专家核心领域重叠比例大于 0.5 的候选减 0.2，再重新排序。最高调整分不大于零时停止，不用零分专家凑数。

Panel 少于 3 人只作为匹配结果返回，由根 Skill 请求类别确认。Registry 缺失、为空、损坏或 ID 重复时直接报告安装异常。

## 两个入口

- `scripts/match-experts.py`：根 Skill 调用的 CLI。
- `brain-crew/scripts/brain_crew_query.py`：保留的 Python Query API。

两个入口都调用 `matching_core.py`。`turbo` 仅在 Query API 中表示批量查询，并映射为普通共识风格评分，不加入会议模式枚举。
