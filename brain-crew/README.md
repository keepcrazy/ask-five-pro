# Brain Crew

Ask Five Pro 内置专家模块：**40 位专家、5 个 pack、一个 Registry、一个共享匹配实现**。

## 目录

```text
expert-registry.json       唯一专家事实源
flash-profiles.md          40 位专家 Flash 速记
packs/                     完整专家 Skill
scripts/matching_core.py   共享评分、排序与去同质化
scripts/brain_crew_query.py Query API 薄适配
scripts/validate-expert-assets.py 文件完整性检查
docs/                      专家与匹配说明
```

## 数量

- core：6
- brand：10
- tech：7
- enterprise：12
- meta：5

合计 40。extension 是扩展说明目录，不是第六个正式 pack。

## 使用

Ask Five Pro 主链路通过根目录的 `scripts/match-experts.py` 调用共享匹配核心。Python 调用方可以导入 `scripts/brain_crew_query.py` 中的既有函数。

`turbo` 只表示批量 Query，不是会议模式。会议模式仍是共识、对抗、红队、陪审团、预审、淬火六种。

旧 `references/expert-registry.json` 已删除且不兼容。所有调用方必须使用本目录的 `expert-registry.json`。
