# Skill Card: Paper-Grounded Visual Analytics Skill

## 基本信息

| 项目 | 内容 |
|---|---|
| Skill 名称 | paper-grounded-vis-analytics-skill |
| 科研场景 | 可视分析系统设计、真实数据集分析、论文启发式原型构建 |
| 主要用户 | 做信息可视化、可视分析、多媒体内容分析相关课题的研究生 |
| GitHub 路径 | `skills/paper-grounded-vis-analytics-skill/` |
| 核心输出 | 可运行多视图可视分析前端 demo，以及可复查的设计与验证报告 |

## 解决的科研问题

研究生在做可视分析或多媒体内容分析项目时，常常需要从论文中学习系统设计经验，再把这些经验迁移到自己的数据集上。这个过程通常包含论文检索、论文阅读、数据理解、分析问题选择、视图设计、前端实现和 demo 验证，人工完成耗时且容易变成临时性的图表拼凑。

本 skill 将这个流程标准化：先构建本地论文知识库，再检索相关 VIS 论文，最后基于真实数据生成可运行、多视图、证据可追踪的可视分析工作台。

## 输入

- 论文 PDF、论文 Markdown 或已有论文目录。
- CSV、TSV、JSON、JSONL、Parquet、Excel 等真实数据集。
- 用户对研究目标、数据集背景或希望探索现象的描述。
- 可选：MinerU、LLM 和 embedding API 配置。

## 输出

- `data/papers/*/meta.json`、`paper.md` 和论文索引。
- `stage1_profile/`：数据画像、模式证据和候选研究问题。
- `stage2_idea/`：paper-grounded idea contract 和反 dashboard 检查。
- `stage3_visual_spec/`：可视系统规格。
- `app/`：可运行前端 demo。
- `artifacts/`：构建报告、截图、critic 报告和 smoke check 结果。

## 与普通 ChatGPT 问答的区别

| 对比项 | 普通 ChatGPT 问答 | 本 Skill |
|---|---|---|
| 任务目标 | 临时回答一个想法或建议 | 固化一个论文到数据集再到 demo 的科研流程 |
| 输入材料 | 用户随意描述 | 明确要求论文、数据、索引或研究目标 |
| 分析流程 | 不固定 | 分阶段：入库、检索、挖掘、设计、实现、检查 |
| 输出格式 | 不稳定 | 每个阶段都有固定文件和报告 |
| 可复用性 | 依赖用户提问能力 | 可替换数据集和论文库重复运行 |
| 可验证性 | 较弱 | 输出需要对应数据证据、论文来源和浏览器验证 |

## 可靠性设计

1. 保留数据 provenance：数据路径、行数、字段、缺失值、采样和聚合方式。
2. 保留论文 provenance：检索到的论文、摘要、`meta.json`、`paper.md` 证据段落。
3. 区分确定结论和不确定推测。
4. 用 Internal E Critic 检查是否退化为 dashboard 或 chart gallery。
5. 用浏览器 smoke check 检查前端是否真实渲染、无控制台错误、核心图元数量正确。

## Demo 概述

示例输入使用 Palmer Penguins morphology 数据集。示例输出生成了一个形态空间分析工作台，用真实数据展示企鹅物种之间的形态边界、局部混淆记录和 flipper-length/bill-depth 相关性反转。

核心验证结果：

- 使用 344 行真实数据，无模拟数据。
- 342 行完整形态数据进入主视图，2 行缺失形态记录作为 badge 保留。
- 生成可运行前端和 1440x810、1920x1080 浏览器截图。
- critic 报告结果为 `pass`。

整理版还额外提供 2 个输出案例：

| 示例 | 输入类型 | 输出特点 | 复查材料 |
|---|---|---|---|
| Taxi City Pulse Braid | NYC Yellow Taxi parquet + taxi zone lookup | 从 2,964,624 行出行数据生成 OD-time pulse braid 工作台 | build report、design spec、visual quality review、截图、可运行 app |
| BNNVis Paper-Grounded Demo | 论文主题 + 本地论文索引 | 从相关论文检索结果生成 uncertainty diagnosis 可视分析 demo | reference report、frontend build report、browser smoke、截图、可运行 app |
