### 达尔文 Skill（darwin）
- 核心模型：9 维 rubric 满分 100（实测 23/具体性 17）；棘轮机制——新分须严格 > 旧分，连续 2 轮 Δ<2 自动停
- 标志案例：nuwa-skill 因「Claude Code」措辞被拒装，催生 runtime 红灯 grep 扫描
- 语气指纹：直接、有结构、有观点；禁「视情况而定」类软化措辞；禁同 context 自评自改
- 能力边界：LLM-as-judge 准确率仅 46.4%，只能识别 gross degradation，细粒度差异必须人审
