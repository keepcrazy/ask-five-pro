# Changelog

## 2.3.0 - 2026-09-16

- 保持根 Skill `default-enabled: false`。
- 恢复 v2.2.3 的 40 位专家、五个 pack、六种会议模式与七类输出。
- 只保留 `brain-crew/expert-registry.json`；删除旧 Registry、空备份和旧路径兼容，这是 breaking change。
- 将 CLI 与 Query API 的重复匹配实现收敛为共享核心。
- 只新增三组批准的类别别名，并统一敏感专家过滤规则。
- 保持 Boundary Guard 的首个命中行为，保持名单确认、人格加载和会议综合由 Skill/宿主模型负责。
- 将历史报告移入 `tests/evidence/`，使当前检查失败返回非零。

此前版本历史保留在 Git 基线 `4627911`，不再嵌入根 Skill 的运行协议。
