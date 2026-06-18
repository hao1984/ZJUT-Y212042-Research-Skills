# BNNVis Paper-Grounded Demo

本案例展示 `paper-grounded-vis-analytics-skill` 的论文驱动 demo 生成能力。

## 输入来源

- 输入主题：`BNNVis: Towards Visual Analytics for Bayesian Neural Networks`。
- 本地论文库与检索索引。

## 输出说明

该 demo 从论文主题中抽取关键词，检索相关 VIS 论文，并将检索到的 uncertainty visualization、model diagnosis 和 evidence panel 等设计经验迁移到一个可运行前端 demo 中。

可复查文件：

- `vis_reference_report.md`：检索到的相关论文和 borrowed elements。
- `frontend_build_report.md`：前端构建报告。
- `design_spec.md`：视觉系统设计说明。
- `browser_smoke.json`：浏览器 smoke check。
- `app/`：可运行前端。
- `screenshot_1440.png`、`screenshot_1920.png`：浏览器截图。

## 本案例证明的能力

- 不依赖外部 CSV 时，也能从论文和本地索引构建 paper-derived payload。
- 能把论文检索结果转化为可视分析系统设计，而不是只做论文摘要。
- 输出包含 reference report、design spec、可运行 app 和浏览器验证材料。
