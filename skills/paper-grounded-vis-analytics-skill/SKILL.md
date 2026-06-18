---
name: paper-grounded-vis-analytics-skill
description: Build a paper-grounded visual analytics research workflow. Use it when a researcher needs to transform papers and real datasets into a reusable, evidence-grounded, runnable multi-view visual analytics demo rather than a generic dashboard or one-off ChatGPT answer.
---

# Paper-Grounded Visual Analytics Skill

## 1. Skill 目标

本 skill 面向可视分析、信息可视化和多媒体内容分析相关科研场景。它解决的问题不是“让大模型回答一个可视化想法”，而是把一个真实科研流程固化为可复用、可检查的 OpenClaw Research Skill：

1. 将论文 PDF 转换为结构化、本地可检索的论文知识库。
2. 从已有 VIS 论文中抽取可复用的系统设计模式、交互方式和证据展示方法。
3. 面向真实数据集生成可运行的多视图可视分析前端 demo。
4. 通过数据证据、论文证据、critic 检查和浏览器 smoke test 提高输出可靠性。

## 2. 适用场景

当研究生需要基于真实数据集快速构思、实现并验证一个可视分析系统原型时，可以使用本 skill。典型输入包括：

- 论文 PDF、论文 Markdown、`meta.json` 或已有论文目录。
- CSV、TSV、JSON、JSONL、Parquet、Excel 等数据集。
- 用户对数据集、研究问题或分析目标的自然语言描述。
- 本地论文知识库：`data/index.db`、`data/faiss.index`、`data/faiss_ids.json` 和 `data/papers/*`。

典型输出包括：

- 论文知识库与向量检索索引。
- paper-grounded idea contract。
- visual system specification。
- 可运行前端：`app/index.html`、`app/style.css`、`app/main.js`、`app/data/*`。
- demo build report、critic report、browser smoke report 和截图。

## 3. 工作流

### Stage A: 论文入库

使用 `components/paper-mineru-scholar-index/`：

1. 调用 MinerU 或读取已有 Markdown，将论文 PDF 解析为 `paper.md` 和 `images/`。
2. 规范化论文目录，生成 `paper.pdf`、`paper.md`、`images/`、`meta.json`。
3. 构建 L1-L4 论文层级：标题、摘要、LLM 总结、全文 Markdown。
4. 对 `L1 + L2 + L3` 建立 embedding。
5. 生成或刷新 `data/index.db`、`data/faiss.index` 和 `data/faiss_ids.json`。

### Stage B: 论文启发式系统设计

使用 `components/paper-grounded-vis-system-design/`：

1. 理解新论文、数据集或研究想法。
2. 从本地论文库检索相关 VIS 论文。
3. 抽取论文中的系统目标、视觉对象、多视图布局、交互机制和证据展示方式。
4. 生成 Mechanism-E 风格的 idea contract。
5. 生成 visual system spec。
6. 输出可运行的 paper-grounded 前端 demo。

### Stage C: 数据集到可视分析系统

使用 `components/dataset-paper-grounded-vis-analytics/`：

1. 读取并标准化真实数据。
2. 挖掘数据特定模式，而不是只做字段摘要或 KPI 列表。
3. 检索相关论文，并将论文设计经验映射到当前数据集。
4. 生成分析目标、任务-编码映射、反 dashboard 说明、协调视图和探索 affordance。
5. 编写可运行静态前端。
6. 通过 Internal E Critic 和浏览器 smoke check 检查结果。

## 4. 与普通 ChatGPT 问答的区别

普通 ChatGPT 问答通常依赖用户临时描述，输出结构不稳定，也不一定能追溯到原始数据或论文证据。本 skill 的核心价值在于固定科研工作流：

- 输入材料明确：论文、数据集、索引库、研究目标。
- 执行步骤明确：数据读取、模式挖掘、论文检索、idea contract、前端实现、critic 修复。
- 输出格式明确：每个阶段都有可检查文件。
- 证据链明确：数据行、聚合结果、论文来源和设计借鉴都需要保留 provenance。
- 可复用性更强：其他同学可以用同样目录结构替换数据集重新运行。

## 5. 可靠性检查

本 skill 不把大模型输出当作最终真相，而是要求每个结论尽量能回到证据：

- 数据证据：记录数据路径、行列数、缺失情况、聚合方式和是否采样。
- 论文证据：保留检索到的论文、摘要、`meta.json` 和相关段落来源。
- 不确定性标注：当论文启发不足或数据不支持时，需要标为 uncertain 或需要人工确认。
- 反 dashboard 检查：确认输出不是 KPI 卡片、图表拼盘或模板化页面。
- 浏览器验证：检查页面可打开、无控制台错误、主要图元真实渲染、截图可复查。

## 6. 目录说明

```text
paper-grounded-vis-analytics-skill/
├── SKILL.md
├── skill_card.md
├── components/
│   ├── paper-mineru-scholar-index/
│   ├── paper-grounded-vis-system-design/
│   └── dataset-paper-grounded-vis-analytics/
├── examples/
│   ├── input/
│   └── output/
└── tests/
```

`components/` 中保留了原始阶段 skill 的 `SKILL.md`、脚本和参考文档。根目录 `SKILL.md` 用于课程提交时说明整体 workflow，组件目录用于真正复用和扩展。

## 7. Demo

示例 demo 使用 Palmer Penguins morphology 数据集，目标是发现企鹅形态空间中的跨物种边界、相关性反转和容易混淆的记录。

输入见：

```text
examples/input/
```

输出见：

```text
examples/output/
```

示例输出包含可运行前端、构建报告、critic 报告和浏览器截图。

为了展示 skill 的泛化能力，`examples/output/additional_examples/` 还包含两个扩展示例：

- `taxi_city_pulse_braid/`：从 NYC Yellow Taxi parquet 和 taxi zone lookup 生成 OD-time pulse braid 可视分析工作台，展示大规模真实数据聚合、联动视图和浏览器 QA。
- `bnnvis_paper_grounded_demo/`：从 BNNVis 论文主题和本地论文检索结果生成 paper-grounded uncertainty diagnosis demo，展示没有外部 CSV 时的论文驱动系统设计能力。
