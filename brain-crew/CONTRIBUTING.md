# Contributing expert assets

Brain Crew 是 Ask Five Pro 的专家资产模块。新增专家属于产品扩展；本次内置 40 位专家的维护只做固定源文件完整性检查。

## 新增专家

1. 在 `packs/<pack>/<skill-name>/` 添加完整 Skill 及其附属文件。
2. frontmatter `id` 使用稳定机器 ID，`name` 与目录名一致。
3. 在唯一 `expert-registry.json` 添加记录，Registry `name` 使用显示名。
4. 在 `flash-profiles.md` 添加同一机器 ID 的速记人格。
5. 运行当前验证：

```bash
python3 ../tests/run-validation.py
```

正式 pack 为 core、brand、tech、enterprise、meta。extension 目录只保存扩展说明，不计入 pack 数。

## 修改现有专家

现有专家必须可追溯到固定源版本。修复缺失或损坏文件时，从记录的源版本原样恢复，不用模型补写，不借完整性修复评价或扩写人格。

## 匹配逻辑

评分业务只存在于 `scripts/matching_core.py`。Query API 只做适配，根 Skill 仍通过顶层 `scripts/match-experts.py` 调用。

## 兼容边界

- 不创建第二份 Registry。
- 不为旧 `references/expert-registry.json` 提供兼容。
- 不把名单确认、人格加载或会议综合放进 Brain Crew 脚本。
- `turbo` 只表示批量查询。
