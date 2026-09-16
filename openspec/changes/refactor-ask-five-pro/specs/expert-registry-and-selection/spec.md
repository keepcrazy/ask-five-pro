## Purpose

在保持 Ask Five Pro 原有专家选择职责和主链路结果的前提下，建立唯一专家 Registry、收敛重复匹配实现，并明确 CLI、Query API 与 Skill 交互的边界。

## ADDED Requirements

### Requirement: 只保留一个权威 Registry
系统 SHALL 只保留 `brain-crew/expert-registry.json` 作为权威专家 Registry，其中包含 40 个唯一专家 ID 和 core 6、brand 10、tech 7、enterprise 12、meta 5 的分布。根 Skill、匹配 CLI、Query API、完整性检查和测试 SHALL 读取该文件。

#### Scenario: Registry 单一来源
- **WHEN** 搜索生产文件中的专家 Registry 消费者
- **THEN** 所有消费者指向 `brain-crew/expert-registry.json`，不存在第二份可独立修改的业务数据

### Requirement: 旧 Registry 文件和路径被删除
`references/expert-registry.json` 及其 `.bak` SHALL 从产品中删除。旧文件、旧路径重定向和兼容包装 SHALL NOT 保留；调用方 SHALL 迁移到唯一 Registry。该变化 SHALL 作为 breaking change 记录。

#### Scenario: 调用旧 Registry 路径
- **WHEN** 调用方显式传入已删除的 `references/expert-registry.json`
- **THEN** 系统报告路径不存在或无效，不得静默重定向到新 Registry

#### Scenario: 检查生产包
- **WHEN** 构建或检查重构后的产品目录
- **THEN** 生产材料中不存在旧 Registry 和空 `.bak`

### Requirement: 三层专家标识契约
Registry/frontmatter `id` SHALL 是跨入口稳定的机器 ID；frontmatter `name` SHALL 与 Skill 名和目录名对应；Registry `name` SHALL 是用户可见显示名。校验与匹配不得混用三者。

#### Scenario: 加载专家元数据
- **WHEN** 系统解析任一专家记录及其 frontmatter
- **THEN** 它使用 `id` 做机器关联、frontmatter `name` 做 Skill/目录对应、Registry `name` 做展示

### Requirement: Registry 字段最小化
原版缺少 `default_enabled` 的 5 个专家 SHALL 显式补为 `false`；冗余 `bundled` 字段 SHALL 从全部记录删除。除唯一 Registry 路径、这两项字段规范化和已记录的可移植路径表达外，40 位专家的业务元数据 SHALL 保持基线值，且专家源文件内容 SHALL NOT 因 Registry 清理而修改。

#### Scenario: 缺失默认值
- **WHEN** Registry 迁移到新结构
- **THEN** 原本缺少 `default_enabled` 的 5 条记录具有显式 `false`

#### Scenario: 删除冗余字段
- **WHEN** 检查全部 Registry 记录
- **THEN** 不存在 `bundled` 字段

### Requirement: Registry 路径可随安装包移动
唯一 Registry 中的人格路径 SHALL 使用安装包内可解析的表达，使完整 Skill 复制到任意目录后仍能定位 40 个专家文件；路径解析不得依赖仓库外 Brain Crew 副本或进程启动目录。

#### Scenario: 临时目录安装
- **WHEN** 完整 Skill 被复制到临时目录并从另一个工作目录调用
- **THEN** Registry 的 40 条人格路径全部解析到临时安装包内部

### Requirement: 匹配逻辑只有一个业务实现
`scripts/match-experts.py` 与 `brain_crew_query.py` SHALL 调用同一共享匹配实现。共享实现 SHALL 以原 `match-experts.py` 的评分、模式加权、重新排序、目标人数和调整后非正分停止行为为兼容基线，不得增加新的匹配维度、确认状态或会议控制逻辑。

#### Scenario: 跨入口等价输入
- **WHEN** CLI 和 Query API 收到等价议题、类别和模式
- **THEN** 两个入口产生相同的专家顺序、分数和入选理由，差异只允许出现在接口格式适配层

### Requirement: 仅支持三组双向类别别名
共享匹配实现 SHALL 双向等价处理团队与组织、技术与工程、风险与风控。除这三组已批准别名外，不得借重构增加其他类别扩展或语义推断。

#### Scenario: 团队类别匹配组织专家
- **WHEN** 输入主类别为“团队”
- **THEN** 共享匹配按与“组织”等价的类别信号评分

#### Scenario: 未批准近义词
- **WHEN** 输入包含不在三组别名中的近义词
- **THEN** 共享匹配不因本次重构自动新增映射

### Requirement: Panel 规模和不足处理保持
一个主类别 SHALL 目标选择 3 人，两个主类别 SHALL 目标选择 4 人，三个主类别 SHALL 目标选择 5 人；调整后得分不大于零的候选不得用于凑数。最终 panel 少于 3 人时，根 Skill SHALL 请求类别确认。Registry 为空、损坏或无法解析时 SHALL 作为安装异常停止，不得进入历史 onboarding 流程。

#### Scenario: 非正分候选不足
- **WHEN** 达到目标人数前剩余候选调整后得分均不大于零
- **THEN** 匹配停止补人，且少于 3 人时由根 Skill 请求类别确认

#### Scenario: Registry 损坏
- **WHEN** 唯一 Registry 为空或无法解析
- **THEN** 调用失败并报告安装异常，不执行 onboarding

### Requirement: 用户名单交互仍由 Skill 负责
用户点名、排除、替换、名单展示和最终确认 SHALL 继续由根 Skill 与宿主模型处理。共享匹配实现只提供原有候选评分与排序能力，不得新增程序确认状态机，也不得决定用户拒绝后的流程。

#### Scenario: 用户替换专家
- **WHEN** 用户在名单确认中要求替换专家
- **THEN** 根 Skill 处理交互并形成最终名单，匹配程序不发起二次确认

### Requirement: 敏感专家默认排除
`sensitivity: sensitive` 的专家 SHALL 默认不进入候选，仅当用户明确点名或使用对抗模式时才可按原有评分进入候选。谈判、权力、舆论或相近主题 SHALL NOT 自动启用敏感专家。

#### Scenario: 普通共识会议
- **WHEN** 用户没有明确点名敏感专家且会议不是对抗模式
- **THEN** 候选中不包含敏感专家

#### Scenario: 明确点名
- **WHEN** 用户明确点名一位敏感专家
- **THEN** 该专家可以进入候选，并继续遵循根 Skill 的名单流程

### Requirement: 既有入口只做薄适配
根 Skill SHALL 继续调用 `scripts/match-experts.py`。`brain_crew_query.py` SHALL 保留既有函数入口，但删除自身的重复评分业务逻辑，只适配参数、资源路径和返回格式。`turbo` SHALL 只影响 Query API 的批量查询方式，不改变共享匹配规则或会议模式集合。

#### Scenario: 根 Skill 匹配
- **WHEN** 根 Skill 需要生成专家候选
- **THEN** 它仍调用 `scripts/match-experts.py`

#### Scenario: Query 函数调用
- **WHEN** 现有调用方使用原 Query API 函数入口
- **THEN** 入口继续可用并返回共享匹配结果，不维护第二套评分实现
