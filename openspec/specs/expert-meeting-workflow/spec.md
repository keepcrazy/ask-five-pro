# expert-meeting-workflow Specification

## Purpose

固化 Ask Five Pro v2.2.3 由根 Skill 驱动的完整会议行为和执行职责，使目录与内容能够优化，但原由 Skill、宿主模型和脚本分别承担的逻辑不得互相迁移。

## Requirements

### Requirement: 原有执行职责保持
根 `SKILL.md` SHALL 继续作为会议运行协议的权威入口，负责阶段顺序、深度与模式路由、议题和约束处理、脚本调用、条件化名单确认、人格加载、会议组织、四级综合与七类输出；宿主模型 SHALL 继续完成其中的自然语言语义判断与人格演绎；脚本 SHALL 只执行原有 Boundary Guard 和专家匹配职责。

#### Scenario: 目录重组后执行会议
- **WHEN** 规范性说明或示例被重新组织
- **THEN** 根 Skill 仍明确包含全部阶段、分支、暂停和终止条件，且不依赖新增程序控制器完成会议

### Requirement: 深度路由保持
用户明确要求快速、Flash、闪聊或省 Token 时 SHALL 使用 Flash；用户明确要求 Pro、完整、认真开或完整人格时 SHALL 使用 Pro；无深度信号时 SHALL 使用 Pro；涉及金额、合同、对外承诺或不可逆决策时 SHALL 强制使用 Pro。程序化调用也 SHALL 显式声明 Flash，否则使用 Pro。深度判断继续由 Skill 指导宿主模型完成。

#### Scenario: 无深度信号
- **WHEN** 人类请求或程序化调用没有显式声明 Flash
- **THEN** 会议使用 Pro

#### Scenario: 高利害覆盖 Flash
- **WHEN** 请求声明 Flash 但议题涉及金额、合同、对外承诺或不可逆决策
- **THEN** 会议使用 Pro

### Requirement: 只有六种会议模式
Ask Five Pro SHALL 只提供共识、对抗、红队、陪审团、预审和淬火六种会议模式；没有模式信号时 SHALL 使用共识。`turbo` SHALL 仅作为 Brain Crew Query API 的批量查询标识，不得被路由或展示为会议模式。

#### Scenario: 默认会议模式
- **WHEN** 用户要求专家团开会但没有给出模式信号
- **THEN** 根 Skill 执行共识模式

#### Scenario: Query 使用 turbo
- **WHEN** Query API 收到 `turbo`
- **THEN** 它按批量查询标识处理，且不创建第七种会议模式

### Requirement: 议题类别与约束由 Skill 处理
宿主模型 SHALL 按根 Skill 判断议题清晰度、提取一至三个主类别并收集预算、时间、团队、已有资产和禁区；只追问可能实质改变结论的约束，其他缺失项标记为未提供后继续。Boundary Guard 的 `suggested_mode` 不得作为议题类别。

#### Scenario: 议题不清晰
- **WHEN** 用户没有提供可识别的具体议题
- **THEN** 根 Skill 先请求补充议题且不执行专家匹配

#### Scenario: 非关键约束缺失
- **WHEN** 议题清晰且缺失信息不影响首轮分析
- **THEN** 根 Skill 记录该约束未提供并继续

### Requirement: Boundary Guard 保持脚本实际行为
根 Skill SHALL 在专家匹配前调用原有 Boundary Guard，并按 `reject_and_refer`、`disclaimer_then_analyze`、`analyze` 三种结果继续或终止。脚本 SHALL 保持固定的领域和置信度扫描顺序，返回首个命中，不合并多个领域，也不在多个结果间计算“最严格结果”。

#### Scenario: 首个领域命中
- **WHEN** 一个输入同时匹配多个边界领域
- **THEN** Boundary Guard 按原固定扫描顺序返回首个命中结果

#### Scenario: 紧急危机终止
- **WHEN** Boundary Guard 返回 `reject_and_refer`
- **THEN** 根 Skill 输出转介信息并停止，不执行专家匹配

#### Scenario: 专业声明后继续
- **WHEN** Boundary Guard 返回 `disclaimer_then_analyze`
- **THEN** 根 Skill 先展示声明，再继续原会议流程

### Requirement: 条件化名单确认保持
高利害或不可逆议题、用户指定或排除专家、淬火模式 SHALL 触发名单确认；其他会议 SHALL 自动组队继续。点名、排除、替换、展示和确认继续由 Skill 与用户交互处理，不得新增程序确认状态机。

#### Scenario: 普通会议自动组队
- **WHEN** 低风险、非淬火会议中用户未指定或排除专家
- **THEN** 根 Skill 不询问名单确认并继续人格加载

#### Scenario: 必须确认的名单未确认
- **WHEN** 会议满足确认条件但用户尚未确认名单
- **THEN** 根 Skill 不得进入人格加载或专家发言

#### Scenario: 用户拒绝名单
- **WHEN** 用户拒绝待确认名单
- **THEN** 根 Skill 请求修改名单或取消会议，不得使用默认名单静默继续

### Requirement: 人格加载与降级保持
名单确定后，Pro SHALL 读取每位专家完整人格，Flash SHALL 读取对应速记人格；单个人格资源缺失时 SHALL 使用原有 fallback 并披露；全部 Pro 人格缺失时 SHALL 在专家发言前暂停并请求用户确认。该流程继续由 Skill 和宿主读取能力执行。

#### Scenario: 单个人格缺失
- **WHEN** panel 中一位专家的人格文件不可读而其他人格可读
- **THEN** 根 Skill 使用该专家的 fallback 并明确披露降级

#### Scenario: 全部 Pro 人格缺失
- **WHEN** Pro panel 的完整人格全部不可读
- **THEN** 根 Skill 暂停并等待用户确认是否以 fallback 继续

### Requirement: 六种会议机制保持
六种会议 SHALL 保持原有机制。对抗模式 SHALL 进行 2–3 轮交锋，后续轮次引用前一轮具体论点，双方结辩 SHALL 各自认可对方至少一点；2–3 轮是范围，固定三轮只可作为示例。淬火模式的挑刺专家 SHALL 与初议专家不同。

#### Scenario: 两轮对抗完成
- **WHEN** 对抗在两轮内已完成有效交锋
- **THEN** 双方完成结辩互认后可以进入综合，不得因示例为三轮而强制增加一轮

#### Scenario: 淬火挑刺
- **WHEN** 淬火会议从初议进入挑刺阶段
- **THEN** 挑刺由未参加初议的专家执行

### Requirement: 系统组织者不形成独立专家立场
系统组织者 SHALL 不占专家名额，可以归纳证据、判断多数意见和比较论证强弱，但不得产生独立专家观点、替用户做最终价值选择或把建议表述为无条件命令。行动建议 SHALL 明确适用条件。

#### Scenario: 专家意见分裂
- **WHEN** 多数意见和阻断性少数意见并存
- **THEN** 系统组织者呈现双方证据、论证强弱和成立条件，不自行增加第三种专家立场

### Requirement: 四级综合与七类外层输出保持
根 Skill SHALL 保持明确共识、条件共识、多数意见、无法形成共识四级判定及阻断性意见规则。所有模式 SHALL 使用七类外层输出：边界声明（如有）、会议信息、专家独立发言、模式结果、综合、条件化行动选项、结尾提醒。红队和预审材料中的“只输出” SHALL 只约束各自模式分析内容，不得删除统一外层结构。

#### Scenario: 无法形成共识
- **WHEN** 专家不能形成共同结论
- **THEN** 输出共同认识、核心分歧、各方案成立条件、待验证信息和用户价值选择，不编造共识

#### Scenario: 阻断性少数意见
- **WHEN** 单一专家指出安全、合规或不可逆风险
- **THEN** 综合保留该意见且不被多数票覆盖

#### Scenario: 红队模式输出
- **WHEN** 红队分析完成
- **THEN** 红队内容聚焦漏洞和失败路径，同时结果仍遵守七类外层输出契约

### Requirement: 非现行历史规则不得进入运行链路
重构后的规范性材料 SHALL 删除或明确标记为非现行的“结论优先/完整/极简”输出模式、Phase 5 产出物确认和强制 `discussion` 容器；这些历史表述不得改变现行阶段或输出契约。根 Skill frontmatter SHALL 保持当前 `default-enabled: false`，README 与 Changelog 不得给出相反说明。

#### Scenario: 执行现行会议
- **WHEN** 根 Skill 完成专家会议
- **THEN** 它不要求 Phase 5 产出物确认或强制 `discussion` 容器

#### Scenario: 检查默认启用状态
- **WHEN** 对比根 Skill frontmatter、README 和 Changelog
- **THEN** 三者一致说明该 Skill 默认不启用
