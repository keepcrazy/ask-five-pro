# compatibility-validation Specification

## Purpose

以 `4627911` 的 v2.2.3 产品行为、文件与职责分工为兼容基线，并用已确认的最小改动冲突清单约束重构，确保目录优化和重复逻辑收敛不会引入其他产品变化。

## Requirements

### Requirement: 行为与职责同时兼容
重构 SHALL 同时保持原有用户可见行为和执行职责：根 Skill 与宿主模型继续负责深度/模式路由、议题和约束、名单交互、人格加载、会议、综合和输出；Boundary Guard 与专家匹配继续由原有脚本职责承担。除已批准的冲突裁决外，任一职责迁移或行为变化 SHALL 使验收失败。

#### Scenario: 名单确认被程序接管
- **WHEN** 新增程序模块决定名单是否确认或处理用户拒绝
- **THEN** 兼容验收失败，即使最终名单与某个示例相同

### Requirement: 只接受已批准的冲突结果
冲突验证 SHALL 以本变更 design 中的完整裁决表为白名单。实现 SHALL 采用根 Skill优先、主链路脚本其次、Brain Crew API 向主链路收敛、说明文档和历史报告不反向定义产品行为的最小改动顺序；不得在实现阶段新增未批准裁决。

#### Scenario: 出现未列明差异
- **WHEN** 重构结果与基线不同且该差异不在裁决表中
- **THEN** 验收失败并报告该差异，不自动更新期望

### Requirement: Registry 破坏性删除被显式验证
验收 SHALL 确认唯一 Registry 位于 `brain-crew/expert-registry.json`，旧 Registry 与 `.bak` 已删除且没有路径重定向或兼容包装。调用旧路径失败 SHALL 被记录为本变更唯一明确的接口 breaking change。

#### Scenario: 旧路径被静默兼容
- **WHEN** 旧 `references/expert-registry.json` 路径仍能被生产入口重定向
- **THEN** 验收失败

### Requirement: 共享匹配只产生批准差异
共享匹配 SHALL 对基线 fixture 保持原 `match-experts.py` 的评分、模式加权、重新排序、目标规模和非正分停止结果。允许的结果差异 SHALL 仅为三组双向类别别名和敏感专家默认过滤规则；CLI 与 Query API 对等价输入 SHALL 返回同一业务结果。

#### Scenario: 非批准排序变化
- **WHEN** 固定输入的专家顺序变化且原因不是批准的别名或敏感过滤
- **THEN** 匹配兼容验收失败并输出首个差异

### Requirement: Boundary Guard 以实际脚本为准
Boundary Guard 回归 SHALL 固定验证领域/置信度扫描顺序、首个命中、单领域输出和三种 action；文档中的“合并多领域”或“取最严格结果”不得成为测试期望。

#### Scenario: 多领域输入
- **WHEN** 一个基线输入同时命中多个领域
- **THEN** 重构结果与原脚本的首个命中逐字段一致

### Requirement: 工作流裁决被完整验证
工作流验收 SHALL 覆盖：程序化调用显式 Flash、无信号 Pro、高利害强制 Pro、六种模式、名单拒绝不得静默继续、单个与全部人格缺失的不同处理、对抗 2–3 轮及结辩互认、淬火不同专家挑刺、组织者权限边界和七类外层输出。历史的额外输出模式、Phase 5 产出物确认和强制 `discussion` 容器 SHALL NOT 出现在现行运行规则中。

#### Scenario: 历史规则回流
- **WHEN** 根 Skill 或当前测试要求 Phase 5 产出物确认或强制 `discussion` 容器
- **THEN** 工作流兼容验收失败

### Requirement: 专家完整性验收仅检查源文件
基础验收 SHALL 覆盖 40 个专家主文件、被引用附属文件、唯一 Registry 路径、三层标识关系和 Flash 映射。该验收不得包含人格内容评分；修复内容 SHALL 与固定源版本一致。

#### Scenario: 模型补写缺失专家文件
- **WHEN** 缺失文件不是从记录的固定源原样恢复
- **THEN** 专家完整性验收失败

### Requirement: 当前检查失败必须非零退出
任一当前必需检查失败时，聚合检查入口 SHALL 返回非零退出码并保留失败详情；全部必需检查通过时才可返回零。

#### Scenario: 子检查失败
- **WHEN** Registry、脚本回归、资产或工作流检查中的任一项失败
- **THEN** 聚合命令返回非零状态

### Requirement: Registry 替换测试不得污染工作区
会临时替换、移动或改写 Registry 的测试 SHALL 在成功、断言失败和异常退出路径中恢复原文件。测试结束后工作区内容 SHALL 与执行前一致。

#### Scenario: 测试中途失败
- **WHEN** Registry 替换后的测试抛出异常
- **THEN** 清理逻辑恢复原 Registry，且工作区没有残留替换内容

### Requirement: 校验脚本不依赖启动目录
所有校验与测试脚本 SHALL 依据自身安装位置或显式输入解析项目资源，不得假定当前工作目录为仓库根。

#### Scenario: 从外部目录执行
- **WHEN** 用户在仓库外目录调用校验入口
- **THEN** 校验读取正确安装包资源并产生与仓库根执行一致的结果

### Requirement: 当前证据与历史证据分离
当前自动化检查 SHALL 与旧 LLM 输出、历史测试报告和评估材料分开。历史材料 SHALL 存放在 `tests/evidence/` 并标注版本、时间和“非当前通过证据”；当前入口不得读取历史报告决定通过状态。生产说明中的专家和 pack 数 SHALL 统一为 40 与 5。

#### Scenario: 历史报告为通过但当前失败
- **WHEN** `tests/evidence/` 中存在旧通过报告而当前检查失败
- **THEN** 当前验收失败并返回非零状态

### Requirement: 八个基线场景与最终门禁
系统 SHALL 保留原八个 Prompt 的意图，验证双深度、六种模式、Boundary Guard、条件化确认、人格降级、四级综合和七类输出信息结构。最终门禁 SHALL 包含 OpenSpec 严格校验、迁移覆盖、职责边界、唯一 Registry、脚本回归、八场景、40 人资产、临时安装和工作区差异检查。未执行的真实宿主验证 SHALL 明确标为未验证。

#### Scenario: 本地门禁通过但真实宿主未测
- **WHEN** 所有本地门禁通过而真实宿主验证未执行
- **THEN** 报告可以声明本地兼容验证通过，但不得声明真实宿主验证完成
