---
id: brain-crew
name: brain-crew
displayName: Brain Crew
version: 2.3.0
description: Ask Five Pro 内置的 40 位专家资产与共享专家匹配接口。
default-enabled: false
---

# Brain Crew

Brain Crew 是 Ask Five Pro 的专家资产模块。它提供 40 位专家、5 个 pack、唯一 Registry、Flash profiles 和查询接口，但不负责用户名单确认、人格演绎、会议组织或综合。

## 唯一 Registry

唯一事实源是：

```text
brain-crew/expert-registry.json
```

不得复制到 references，也不得为旧 `references/expert-registry.json` 建立重定向。

Registry 标识契约：

| 字段 | 含义 |
|---|---|
| Registry/frontmatter `id` | 稳定机器 ID |
| frontmatter `name` | Skill 名和目录名 |
| Registry `name` | 用户可见显示名 |

专家路径相对于 Registry 所在目录解析，因此安装包可整体移动。

## 专家分布

| pack | 数量 |
|---|---:|
| core | 6 |
| brand | 10 |
| tech | 7 |
| enterprise | 12 |
| meta | 5 |
| 合计 | 40 |

## 匹配接口

### 主链路 CLI

根 Skill 使用：

```bash
python3 scripts/match-experts.py \
  --registry brain-crew/expert-registry.json \
  --topic "议题" \
  --mode consensus \
  --categories "产品,战略"
```

### Python Query API

```python
from brain_crew_query import (
    load_registry,
    query_experts,
    query_panels,
    load_expert_content,
    resolve_expert_path,
    get_registry_stats,
)
```

- `query_experts()`：单议题查询。
- `query_panels()`：多个子议题的批量查询。
- `load_expert_content()`：在入选后延迟加载完整人格。
- `turbo`：仅表示 Query API 批量查询，不是 Ask Five Pro 会议模式。

CLI 和 Query API 都调用 `scripts/matching_core.py`，不得维护第二套评分权重。

## 匹配边界

- 主类别数量 1/2/3 对应目标 panel 3/4/5 人。
- 调整后得分不大于零时停止补人。
- 只支持团队↔组织、技术↔工程、风险↔风控三组双向类别别名。
- 敏感专家默认排除；用户明确点名或对抗模式时才可进入候选。
- 谈判、权力和舆论主题不会自动启用敏感专家。
- 匹配模块只返回候选，不处理用户确认。
- Registry 为空或损坏时报告安装异常，不进入 onboarding。

## 人格资产

- 完整人格：`packs/<pack>/<skill-name>/SKILL.md`
- Flash 速记：`flash-profiles.md`
- 资产检查：`scripts/validate-expert-assets.py`

完整性修复只能从记录的固定源版本原样恢复，不进行人格质量评分或模型补写。
