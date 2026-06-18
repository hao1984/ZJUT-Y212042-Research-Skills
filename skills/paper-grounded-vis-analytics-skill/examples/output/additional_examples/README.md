# Additional Output Examples

本目录补充两个输出案例，用于展示 `paper-grounded-vis-analytics-skill` 的泛化能力。

## taxi_city_pulse_braid

真实数据集案例。输入来自 NYC Yellow Taxi 2024 年 1 月 parquet 数据和 taxi zone lookup，原始表规模为 2,964,624 行、19 字段。输出为一个 OD-time pulse braid 多视图分析工作台。

重点展示：

- 大规模真实数据读取与聚合。
- 出行 OD、时间 phase、机场门户和异常记录联动。
- 非 dashboard 的主视觉对象设计。
- 浏览器 QA、截图和 visual quality review。

## bnnvis_paper_grounded_demo

论文驱动案例。输入主题为 `BNNVis: Towards Visual Analytics for Bayesian Neural Networks`，系统从本地论文索引中检索相关 VIS 论文，抽取设计启发，再生成可运行 demo。

重点展示：

- 本地论文检索与 reference learning。
- 论文启发到前端结构的迁移。
- 无外部 CSV 数据集时的 paper-derived payload 构建。
- browser smoke report 和截图复查。
