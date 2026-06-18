# DATA PATTERN MINING PRINCIPLES

> 适用于 E 机制（data-driven）的所有 pattern mining 工作。
> 本文档是 `contracts/prompts/data_profile_v0.1.md` 的依赖。
> 不在本文档定义的任何 mining 行为，应被视为"风险行为"，须慎重判断。

---

## 0. 核心定位

Pattern mining 在 E 机制中的角色：**侦探数据中值得用可视化形式探索的研究问题**。

它**不是**：
- BI 分析（不是为了出报告）
- 数据质量检查（quality 是 schema profiling 的副产物，不是 mining 目标）
- 标准统计分析（不是为了产出 summary statistics）
- 描述性统计可视化（不是为了画分布图）

它**是**：
- 从这份具体数据的领域语义出发，浮现领域相关、非平凡、值得追问的现象
- 寻找数据中"潜在的可视化研究 hook"

---

## 1. 通用 Pattern vs 数据特有 Pattern

这是本文档**最重要**的概念。所有 pattern 必须能被分类到这两类之一，且**至少 40% 的 pattern 必须是数据特有 pattern**。

### 通用 Pattern（generic pattern）

定义：**离开这份数据的领域语义，pattern 描述本身依然成立的 pattern。**

判定问题：把数据集名称和字段名替换成通用占位符（dataset X, var_1, var_2），pattern 描述还看得懂吗？如果是，它就是通用 pattern。

通用 pattern **可以浮现**，但只能作为起点，不能作为最终产出的主体。

通用 pattern 示例：
- "var_1 和 var_2 的 Pearson 相关系数为 0.72"
- "数据存在 3 个聚类（k-means, k=3）"
- "var_3 时间序列存在月度周期"
- "var_4 的分布呈右偏（skewness=1.8）"
- "var_5 的缺失率为 12%"
- "var_6 中存在 17 个统计意义上的异常点（IQR 法）"

### 数据特有 Pattern（data-specific pattern）

定义：**离开这份数据的领域语义，pattern 描述就失去意义的 pattern。**

判定问题：这个 pattern 的描述能否离开"这份数据的领域名词"？如果不能，它就是数据特有 pattern。

数据特有 pattern 示例：
- "沿海传感站的盐度-温度耦合在风暴前 12 小时出现方向反转，但内陆站没有，提示存在区域性水团交换边界"
- "医院急诊转运记录在周一上午呈现社区诊所 → 中心医院的单向流，但夜间该方向显著减弱，反向复诊流增强"
- "材料 A 类的强度-导电性 trade-off 比 B 类陡峭 3 倍，且陡峭度与温度梯度强耦合"
- "GitHub 仓库的 commit 频次在 release 前 2 周呈现 contributor 集中化，前 5 名贡献者 commit 占比从平时的 40% 升到 75%"

### ⚠ 警告：特有 ≠ 复杂

**判定一个 pattern 是不是"数据特有"，标准是它是否离不开这份具体数据的领域语义，不是它用了多复杂的统计方法。**

- 用复杂方法（深度学习、贝叶斯网络等）挖出的"X 和 Y 相关"仍然是通用 pattern
- 用简单方法（分组求均值）挖出的"特定子群在特定行为上偏离" 可以是数据特有 pattern

---

## 2. 多维度关联的明确定义

"多维度关联"是 E 机制 mining 的核心要求之一。它有非常具体的含义：

### 定义

**≥3 个变量之间的非线性、条件性、子集差异性的耦合。**

不是 N×N 相关性矩阵。不是"我用了多个字段"。

### 判定问题

**"如果我改变第三个变量，前两个变量之间的关系会改变吗？"**

只有这个问题的答案是肯定的，才算多维度关联。

### 多维度关联示例

- "X 和 Y 在 Z=低 时正相关，在 Z=高 时负相关"（关系的方向被 Z 调节）
- "X 和 Y 的耦合斜率在子群 A 中是 0.3，在子群 B 中是 2.1"（关系的强度被子群调节）
- "在时间 t<T 的窗口里 X→Y，t>T 之后 Y→X"（关系的因果方向被时间调节）

### 不是多维度关联的情况

- "X, Y, Z 两两都相关"（这是三个独立的双变量相关，不是三维耦合）
- "X 影响 Y，Y 影响 Z"（这是链式，不是真正的多维耦合）
- "X, Y, Z 联合分布是高斯分布"（这是描述，不是耦合 pattern）

---

## 3. Banned Mining Outputs

以下产出**不算 mining pattern**，即使它们出现在 profile 里也只能放在 schema profiling 或 data quality 段，**不能进入 `patterns` 段，更不能成为候选 RQ 的支撑**：

- "字段 X 的分布是 [均匀/正态/长尾/...]" → 这是 schema profiling
- "数据总览：N 条记录，M 个字段" → 这是 metadata
- "Top 10 类别 / 高频值 / 排行" → 这是 ranking
- "缺失率 X%" → 这是数据质量
- "字段 X 的 mean / median / std 是 ..." → 这是描述性统计
- "X 和 Y 的相关性矩阵" → 这是关系总览，必须降级为某个具体 pattern 的证据
- "数据可以被聚成 K 类（无领域解释）" → 这是无意义聚类

⚠ 这些产出本身没错，但它们不能算 mining 成果。Mining 成果必须能回答"数据中浮现了什么值得追问的现象"。

---

## 4. 主动质疑用户说明

用户提供的"数据说明"是重要输入，但**不是绝对权威**。Agent 应该：

### 验证用户假设

用户说明里如果包含"我认为数据中有 X 模式"这类陈述，agent 应该**去验证**它，而不是**默认确认**它。

- 如果数据证据支持用户假设：在 pattern 里明确标记"用户假设得到证据支持"
- 如果数据证据**反驳**用户假设：这是**高价值发现**，必须显式记录
- 如果数据证据**不足以判断**：明确标记"用户假设无法被当前数据证实或证伪"

### 区分两类陈述

在 profile 输出中，必须明确区分：

- **用户假设（user_hypothesis）**：用户在数据说明中提出的、未被验证的陈述
- **数据证据（data_evidence）**：agent 通过 mining 浮现的、有统计/数值证据的发现

绝不允许把用户假设当成数据证据。

### 浮现"用户没明说但数据自身呈现"的 pattern

最有价值的 pattern 往往是用户说明里**没提到**的。Agent 应主动留意：
- 用户没关注但数据中显眼的子群差异
- 用户没预期但数据中存在的耦合关系
- 用户没意识到的数据质量问题（不是缺失率，而是结构性偏差）

---

## 5. Mining 完成的标准

Agent 在 mining 阶段需要自主判断"什么时候停"。停止标准：

### 必要条件（满足才算合格 mining）

- 浮现 **≥ 5 个候选 pattern**
- 其中 **≥ 2 个是数据特有 pattern**（按本文档第 1 节判定）
- 浮现 **3-7 个候选研究问题**
- 每个 pattern 有可重复的统计/数值证据（不能只有自然语言描述）

### 充分条件（建议达到）

- 至少有 1 个多维度关联 pattern（按本文档第 2 节定义）
- 至少有 1 个与用户假设相关的 pattern（验证、反驳或扩展）
- 至少有 1 个用户说明里没提到、agent 主动发现的 pattern

### 停止条件

- 满足必要条件后，且最近 3 次新挖出的 pattern 都是通用 pattern，可以停止
- Stage 1 mining 用时超过 30 分钟，强制停止并保存当前结果
- 计算资源（内存/CPU）触及上限，停止并标记 partial

---

## 6. 不要做的事

### 不要列出"mining 算法清单"然后逐个执行

如果 agent 把 mining 任务理解成"做完聚类、异常检测、关联规则、时序分解、PCA、t-SNE..."，那它已经走错了路。

Mining 是**侦探工作**，不是**算法 checklist 执行**。

对小数据集尤其如此。小数据集的计算部分通常应很短，真正的时间应该花在判断哪些证据能形成 data-specific pattern，而不是反复尝试互相替代的方法。不要为了“显得深”而跑一串 generic algorithms。

正确顺序：
1. 先看数据
2. 结合用户说明形成"这份数据可能藏着什么"的猜想
3. 用适合验证猜想的方法去验证
4. 浮现新的猜想，循环

错误顺序：
1. 看到这是 tabular 数据
2. 跑完一套"标准分析方法"
3. 把结果整理成 pattern 输出

预算纪律：

- 已经满足必要停止条件时，立即落档，不继续挖“也许还能有”的 pattern。
- 默认不画中间图。只有当图直接帮助验证或否定某个候选 pattern 时才保存。
- 终端输出保持简短；证据写入 artifact，不写成长篇过程叙述。

### 不要让"覆盖度"压倒"深度"

宁可深挖 1 个数据特有 pattern，也不要浮浅地浮现 10 个通用 pattern。
评估 mining 质量的标准是**最深的 pattern 有多深**，不是**总数有多少**。

### 不要在数据之外编造领域知识

Agent 可能基于 LLM 内部领域知识"补充"pattern。这是 hallucination 风险。
- 允许：基于数据浮现 pattern，用领域知识解释 pattern 的可能含义
- 禁止：基于领域知识编造"数据应该有的 pattern"

明确分界：解释（interpretation）允许，但 pattern 本身必须有数据证据。

### 不要急于给可视化方向

Mining 阶段的产出是 **patterns + candidate research questions**，不是可视化设计。

candidate research questions 里可以包含"可视化方向的直觉"（hint），但**不强求**，也**不应当**让可视化设计反过来约束 mining。

---

## 7. Anti-Dashboard 在 Mining 阶段的体现

虽然 anti-dashboard 主要在 idea 和 demo 阶段执行，mining 阶段也有责任：

**Mining 不能产出 dashboard 思维的 RQ**。

候选 research question **必须被拒绝**的形态：
- "数据分布概览"
- "字段相关性总览"
- "各类别的 Top N 排行"
- "X 字段的时序趋势"（仅 X 一个字段，没有 cross-cutting）
- "按 Y 分组的统计指标 dashboard"

候选 research question **应当呈现**的形态：
- "在某个具体子群/条件下，多变量之间出现某种耦合或断裂"
- "数据中存在一个特定的边界/相变/异常区域，值得探索其结构"
- "两个看似无关的维度之间存在条件性关联"
- "用户假设的某个模式实际上以一种意外的方式存在/不存在"

---

## 8. Pattern 输出的最小信息单元

每个 pattern 在 `data_profile.yaml` 中必须包含：

- `description`：自然语言描述（一句话）
- `category`：`generic | data_specific`
- `involved_fields`：涉及的字段列表
- `evidence`：可重复的统计/数值证据（数值、检验统计量、子集大小等）
- `why_interesting`：为什么这个 pattern 值得关注（一句话）
- `relation_to_user_description`：`supports | refutes | extends | unrelated`

最后一项尤其重要——它告诉下游 stage 这个 pattern 和用户关注点的关系。

---

## 9. 给 Agent 的最终原则

> **Mine like a detective, not like a librarian.**
>
> 你的任务不是整理这份数据有什么，而是发现这份数据在说什么。
>
> 通用 pattern 是起点，不是终点。
> 数据特有 pattern 是目标。
> 多维度关联是奖励。
> 反驳用户假设是宝藏。
> Dashboard 思维是陷阱。

---

## 固定实现约定

- mining 阶段默认预算上限：30 分钟。
- `evidence` 字段使用自由 dict，但必须包含可核验的数值、分组统计、样本 id、文件路径或中间 artifact 引用；不能只写自然语言判断。
