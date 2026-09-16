## Purpose

仅核查权威 Registry 中 40 个专家 Skill 的文件资产是否完整；发现缺失、损坏或未经批准的差异时，从可追溯的源仓库固定版本原样恢复，不评价或改写专家内容。

## ADDED Requirements

### Requirement: 完整性检查覆盖全部 40 位专家
检查 SHALL 覆盖唯一 Registry 中全部 40 个唯一专家 ID，不得抽样，并 SHALL 确认每条记录都能解析到一个可读的 `SKILL.md`。专家数量和 pack 数的当前说明 SHALL 统一为 40 位专家、5 个 pack。

#### Scenario: 全量覆盖
- **WHEN** 执行专家资产完整性检查
- **THEN** 结果覆盖 40 个唯一 ID 和 5 个 pack，且每个 ID 都对应一个可读主文件

### Requirement: 固定源可追溯
每位专家 SHALL 有可验证的源仓库、固定 commit/tag 或等价不可变版本以及源路径记录；多个专家可以共享同一来源记录。无法验证固定来源时，该专家不得标记为完整性核对完成。

#### Scenario: 查询恢复依据
- **WHEN** 查看任一专家的资产记录
- **THEN** 可以定位其源仓库、固定版本和源路径

### Requirement: 只检查文件完整性
检查 SHALL 对照固定源版本核对主 `SKILL.md`、源目录中随 Skill 发布且被其本地引用的附属文件、唯一 Registry 路径和 Flash profile 映射。检查范围 SHALL 限于文件是否存在、可读、完整、路径有效以及是否与固定源一致；不得进行人格质量、真实性、差异化、方法论或内容充分性评审。

#### Scenario: 缺少被引用附属文件
- **WHEN** 专家 `SKILL.md` 引用的源文件在当前安装包中缺失
- **THEN** 该专家被标记为不完整并列出缺失路径

#### Scenario: 文件齐全但内容不符合主观预期
- **WHEN** 专家资产与固定源一致但评审者认为内容可以更丰富
- **THEN** 完整性检查仍按文件事实判定，不修改或扩写内容

### Requirement: 三层标识关系被校验
检查 SHALL 验证 Registry/frontmatter `id` 的稳定机器关联、frontmatter `name` 与 Skill/目录名的对应关系，以及 Registry `name` 的显示用途；不得要求这三个值彼此相同。

#### Scenario: 显示名不同于目录名
- **WHEN** 某专家 Registry `name` 与 frontmatter `name` 不同但各自符合契约
- **THEN** 检查通过该关系，不把显示名差异视为资产损坏

### Requirement: 缺失资产从固定源原样恢复
发现缺失、损坏或未经批准的源文件差异时，实施 SHALL 从记录的固定源版本原样恢复对应文件。不得由模型推断补写，不得借恢复修改人物观点、人格结构、来源说明或方法论。

#### Scenario: 恢复缺失主文件
- **WHEN** 某专家主 `SKILL.md` 缺失且固定源可用
- **THEN** 从固定版本恢复原文件，并验证恢复文件与源 blob 一致

#### Scenario: 固定源不可用
- **WHEN** 缺失资产的固定源无法取得或验证
- **THEN** 完整性检查保持失败并报告阻塞，不生成替代内容

### Requirement: Registry 与 Flash 映射完整
唯一 Registry SHALL 包含 40 个有效专家路径；每个专家 SHALL 按原有映射找到对应 Flash profile，不得存在缺失、重复或孤立映射。完整性修复不得自动生成新的 Flash 人格。

#### Scenario: Flash 映射缺失
- **WHEN** Registry 中某专家没有对应 Flash profile
- **THEN** 检查失败并定位该专家，不为其生成新 profile

### Requirement: 路径迁移差异单独记录
因本次目录优化产生且已批准的路径表达变化 SHALL 记录在迁移映射中，不得被误判为专家内容差异；除这类记录外，专家源资产 SHALL 与固定源保持一致。

#### Scenario: 仅安装路径变化
- **WHEN** 专家文件内容与固定源一致但安装包内路径已按迁移表调整
- **THEN** 检查验证新路径有效，并依据迁移记录接受该差异

### Requirement: 恢复后全量复验
所有恢复完成后 SHALL 重新检查 40 个主文件、必需附属文件、唯一 Registry 路径和 Flash 映射；任一专家仍不完整时不得声明专家组完整。

#### Scenario: 一位专家仍缺文件
- **WHEN** 复验发现任一缺失、损坏或未经说明的差异
- **THEN** 全量检查失败并保留具体清单
