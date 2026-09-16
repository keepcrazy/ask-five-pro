# Ask Five Pro

Ask Five Pro 是由 Skill 驱动的专家议会系统，内置 **40 位专家、5 个 pack、6 种会议模式**。它不替用户决策；程序只执行边界检查和专家匹配，议题理解、名单确认、人格演绎、会议和综合仍由 Skill 与宿主模型完成。

> 根 Skill 当前保持 `default-enabled: false`，需要由触发词或宿主配置显式启用。

## 能力

- 深度：Flash 速记人格 / Pro 完整人格
- 模式：共识、对抗、红队、陪审团、预审、淬火
- 专家：core 6、brand 10、tech 7、enterprise 12、meta 5
- 输出：边界声明、会议信息、专家发言、模式结果、综合、条件化行动选项、结尾提醒
- 安全：`scripts/boundary-guard.py` 识别危机及专业边界

`turbo` 仅是 Brain Crew Query API 的批量查询标识，不是第七种会议模式。

## 触发示例

```text
专家团开会：我们应该先做精品还是先做爆款？
红队模式：检查进入东南亚市场的失败路径。
Flash，陪审团模式：两个产品方向应该选哪个？
```

未显式声明 Flash 时使用 Pro；金额、合同、对外承诺和不可逆决策强制 Pro。

## 安装

```bash
git clone https://github.com/nico-zhuang/ask-five-pro.git
```

把仓库作为本地 Skill 安装。产品不依赖仓库外的 Brain Crew 副本。

## 运行结构

```text
SKILL.md                              完整规范性工作流
brain-crew/expert-registry.json       唯一专家 Registry
brain-crew/flash-profiles.md          Flash 人格速记
brain-crew/packs/                     40 位专家完整人格
scripts/boundary-guard.py             边界检查
scripts/match-experts.py              根 Skill 的匹配入口
brain-crew/scripts/matching_core.py   两个入口共享的匹配实现
brain-crew/scripts/brain_crew_query.py Query API 薄适配
references/                           模板、示例和 fallback
tests/                                当前验证与历史证据分层
```

## Breaking migration

v2.3.0 只保留：

```text
brain-crew/expert-registry.json
```

`references/expert-registry.json` 和对应 `.bak` 已删除，不提供旧路径重定向或兼容包装。调用方必须迁移到唯一 Registry。

Registry 中：

- `id` 是稳定机器 ID；
- 专家 frontmatter `name` 是 Skill/目录名；
- Registry `name` 是显示名；
- 专家路径相对于 `brain-crew/expert-registry.json` 所在目录解析。

## 验证

```bash
python3 tests/run-validation.py
```

历史 LLM 输出和旧测试报告位于 `tests/evidence/`，不参与当前通过判定。

完整工作流以 [SKILL.md](SKILL.md) 为准，匹配接口参见 [brain-crew/SKILL.md](brain-crew/SKILL.md)。
