## Why

Ask Five Pro v2.2.3 的产品逻辑完整，但当前 `develop` 已删除产品文件，原版同时存在两份 Registry、两套专家匹配实现，以及 Skill、脚本、Brain Crew API、说明文档之间互相冲突的表述。本次以 `4627911` 为只读基线，在不改变原有产品逻辑和执行职责的前提下恢复产品、收敛重复实现，并按已经确认的最小改动原则统一冲突。

## What Changes

- 完整恢复由根 `SKILL.md` 驱动的原有工作流：Flash/Pro、六种会议模式、边界检查、条件化名单确认、人格加载与降级、会议组织、四级综合和七类输出继续由原责任主体执行。
- 优化目录与文档结构；根 Skill 保留完整、可执行的规范性流程，references 只承载展开说明、示例和历史材料，不成为新的运行规则入口。
- **BREAKING**：只保留 `brain-crew/expert-registry.json` 作为唯一 Registry；删除 `references/expert-registry.json` 及其 `.bak`，不提供旧文件、旧路径重定向或兼容包装。
- 明确三层专家标识：Registry/frontmatter `id` 是稳定机器 ID，frontmatter `name` 是 Skill/目录名，Registry `name` 是显示名；为 5 个缺失的 `default_enabled` 显式补 `false`，删除 Registry 冗余的 `bundled` 字段，不修改专家源文件内容。
- 根 Skill 继续调用 `scripts/match-experts.py`；`brain_crew_query.py` 保留既有函数入口但改为共享匹配实现的薄适配层。共享实现以原 `match-experts.py` 的评分、模式加权、重新排序和非正分停止行为为基线。
- 仅加入三组双向类别别名（团队↔组织、技术↔工程、风险↔风控），并统一敏感专家规则：默认排除，仅在用户明确点名或对抗模式时进入候选；谈判、权力、舆论不构成自动启用条件。
- 保持 Ask Five Pro 只有共识、对抗、红队、陪审团、预审、淬火六种会议模式；`turbo` 仅是 Query API 的批量查询标识，不是第七种会议模式。
- 名单点名、排除、替换和确认继续由 Skill/大模型处理，不新增程序确认状态机；必须确认的名单未确认时不得继续，用户拒绝后只能修改名单或取消。
- 保持 Boundary Guard 的脚本实际行为：按固定领域/置信度顺序扫描、首个命中、不合并多领域、不计算“最严格结果”；只修正文档冲突，不改变脚本职责或逻辑。
- 统一工作流冲突：程序化调用也必须显式声明 Flash，否则使用 Pro；高利害强制 Pro；单个人格缺失使用 fallback 并披露，全部 Pro 人格缺失时暂停确认；对抗保持 2–3 轮且必须结辩互认；淬火挑刺专家必须与初议专家不同。
- 七类输出是所有模式的统一外层契约；红队、预审的“只输出”只限制各自模式分析内容。删除旧材料中“结论优先/完整/极简”、Phase 5 产出物确认、强制 `discussion` 容器等非现行运行规则。
- 系统组织者可以综合证据、判断多数意见和论证强弱，但不得产生独立专家立场或替用户决策；行动建议必须条件化。
- 专家组审核仅核查 40 个 Skill 的文件完整性；发现缺失、损坏或未经批准的差异时，从记录的源仓库固定版本原样恢复，不做质量评分、人格改写或模型补写。
- 修复验证工程缺陷：当前检查失败返回非零退出码；Registry 替换测试始终恢复现场；校验脚本不依赖启动目录；统一当前数量为 40 位专家、5 个 pack；历史报告移入 `tests/evidence/`，旧 Engine-only 说明和空 `.bak` 退出生产材料。

## Capabilities

### New Capabilities

- `expert-meeting-workflow`: 固化原有 Skill 驱动的完整会议链路、六种模式、确认与降级语义，以及 Skill、脚本和宿主模型的职责边界。
- `expert-registry-and-selection`: 定义唯一 Registry、专家元数据契约、共享匹配基线、类别别名、敏感专家规则和既有调用入口边界。
- `expert-skill-quality`: 定义 40 个专家 Skill 的文件完整性核对、固定源追溯和缺失资产原样恢复。
- `compatibility-validation`: 定义批准冲突清单、职责兼容、脚本回归、验证可靠性和最终验收门禁。

### Modified Capabilities

<!-- 当前 OpenSpec 没有既有 capability；本变更以新规格固化原有产品行为。 -->

## Impact

- 产品入口与说明：`SKILL.md`、`README.md`、`references/`、`brain-crew/SKILL.md`。
- 专家数据与资产：`brain-crew/expert-registry.json`、`brain-crew/packs/**`、Flash profiles。
- 原有脚本：`scripts/boundary-guard.py`、`scripts/match-experts.py`、`brain-crew/scripts/brain_crew_query.py` 及共享匹配模块。
- 测试与工具：Registry、匹配、Boundary Guard、工作流契约、40 人资产完整性、临时安装和历史证据分层。
- 不新增路由控制器、名单确认状态机、会议控制器、结果校验运行时、在线服务、数据库、真实多 Agent 调度或外部实时数据依赖。
