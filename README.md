# Ask Five Pro

> **说一句话，让专家团替你吵架。**

不是专家的集合，而是让专家高效协作的机制。安装后无需配置，直接说「专家团开会」即可调用。

> 📌 当前版本与变更历史：见 `SKILL.md` 顶部 changelog（唯一权威来源）

---

## 快速开始

### 安装

```bash
# 方式一：从 GitHub clone 后本地安装（推荐）
git clone https://github.com/nico-zhuang/ask-five-pro.git
install_skill source={ type: 'path', path: './ask-five-pro' }

# 方式二：Codex
codex skill install https://github.com/nico-zhuang/ask-five-pro
```

> 注：GitHub 仓库 stars 不足时，部分客户端的 github_url 直装会被安全策略拒绝，请用方式一。

### 使用

```
叫专家团来开会，议题是：我们该不该 all-in 短视频矩阵？
```

真实输出长这样（节选）：

```
### 综合：共识判定——条件共识

结论一致（先验证、后扩张），但各位专家的放行条件不同：

| 专家 | 放行条件 |
| MrBeast | 「标题+封面+前 5 秒」公式被 CTR×AVD 数据验证 |
| 运营官  | 单账号过验收线：抖音完播 >10%、小红书点击 >5% |
| Naval  | 内容含 specific knowledge，且有复利结构 |

### 条件化行动选项
- 如果验证速度优先：单平台单账号起步，每天 1 条垂直内容……
- 如果品牌安全优先：先用 GET/WHO/TO/BY 四问定品牌信息架构……
```

---

## 它是什么 / 不是什么

**是**：思维工具。40 位跨领域专家（真人思维框架 + 方法论化身）按六种议会模式协作，输出结构化会议纪要、风险清单与条件化行动选项。

**不是**：决策替代品、权威答案、医生/律师/投资顾问。它不替代决策，只提供多元视角、找出盲区、挑明漏洞。

## 六种议会模式

| 模式 | 触发词 | 输出重点 |
|---|---|---|
| 共识（默认） | 开个会、商量一下 | 各方观点 + 共识判定（四级） |
| 对抗 | 让他们吵一架 | 回合制交锋 + 裁判 verdict |
| 红队 | 红队、找问题 | 漏洞清单 + 风险等级 |
| 陪审团 | 投票、二选一 | 多数意见 + 少数意见 + 关键假设 |
| 预审 | 先想怎么失败 | 失败路径 + 预警信号 + 预防方向 |
| 淬火 | 严格一点、再挑挑刺 | 初议 → 挑刺 → 带置信度结论 |

## flash / pro 双模式

| 模式 | 加载 | 成本 | 适用 |
|---|---|---|---|
| **pro**（人类默认） | 完整人格文件 | ~12K token/次 | 重大决策；涉及金额/合同/不可逆事项**强制** |
| **flash** | 人格速记 | ~500 token/次 | 快速咨询、程序化调用（声明「以 flash 模式」） |

路由只认显式信号，不向用户提问；flash 输出强制标注「⚡ 速记人格演绎」。

## 专家库

内置 `brain-crew` 专家库，按 pack 分六大领域：

```
brain-crew/packs/
├── core/        # 产品与战略（乔布斯、张一鸣、Paul Graham、芒格、费曼、马斯克）
├── tech/        # 工程与系统（Karpathy、Ilya、Rob Pike、黄仁勋、雷军、张小龙、AI 产品经理）
├── brand/       # 内容与品牌（MrBeast、Naval、奥格威、GWTB、鲁迅、郭德纲、X 导师、
│                #   抖红运营官、私域运营官、直播电商操盘手）
├── enterprise/  # 投资与商业（巴菲特、贝佐斯、段永平、塔勒布、特朗普、弗洛伊德、求是、
│                #   稻盛和夫、王阳明、张雪峰、定价分析师、供应链策略师）
└── meta/        # 元与系统（达尔文、花叔蜂群/女娲、苏格拉底、孙子）
```

> 📌 完整名单与元数据以 `references/expert-registry.json` 为唯一权威来源（人数随版本增长，不在本文档手抄）。

每位专家含：角色扮演规则、心智模型、语气指纹、失败模式、反例黑名单、能力边界；真人均为基于公开资料提炼的思维框架，不代表本人当前观点。

## 目录结构

```
ask-five-pro/
├── SKILL.md                    # 引擎入口与完整工作流
├── brain-crew/                 # 内置专家库（人格文件 packs/ + Query API）
├── references/                 # registry、人格速记 flash-profiles.md、模式模板等
├── scripts/                    # boundary-guard.py、match-experts.py、check-experts.sh
├── tests/                      # 集成测试（8 项联调）
└── test-prompts.json           # 六模式 + 边界场景测试用例
```

## 验证

```bash
# 专家库完整性
bash scripts/check-experts.sh

# 边界检查示例
python3 scripts/boundary-guard.py "买入特斯拉股票靠谱吗？"

# 集成测试（8 项：registry 同步/路径解析/规范校验/匹配/边界等）
python3 tests/brain-crew-integration-test.py
```

## 边界与真实性声明

- 人身安全/紧急危机：直接拒绝并提供求助路径，不召集专家团
- 医疗/法律/投资/实时数据：先输出免责声明，再分析
- 全部专家发言为思维框架模拟，关键事实请自行核实，专业问题请咨询对应领域专家

## 与 Ask Five Engine 的关系

- `ask-five-pro` = 引擎 + 内置专家库，开箱即用
- 需要自定义专家组合或二次开发，建议使用拆分版（`ask-five-engine` + `brain-crew`）

---

*Ask Five Pro 提供的是多元视角，不是最终答案。*
