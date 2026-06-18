# Taxi City Pulse Braid

本案例展示 `paper-grounded-vis-analytics-skill` 对大规模真实数据集的处理能力。

## 输入来源

- NYC Yellow Taxi January 2024 parquet。
- Taxi zone lookup。
- 原始规模：2,964,624 行、19 字段。

## 输出说明

该 demo 生成了一个 city pulse braid 工作台，用同一个主视觉对象表达 OD 出行方向、时间 phase、机场门户、异常记录和证据追踪。

可复查文件：

- `demo_build_report.md`：构建报告和数据证据。
- `design_spec.md`：视觉系统设计说明。
- `visual_quality_review.json`：视觉质量检查。
- `app/`：可运行前端。
- `screenshot_1440.png`、`screenshot_1920.png`：浏览器截图。

## 本案例证明的能力

- 使用真实数据行和真实聚合结果，不依赖模拟数据。
- 能处理百万级表格并构造浏览器可加载 payload。
- 能避免输出退化为 KPI dashboard 或 chart gallery。
- 能保留数据 provenance、预处理逻辑和浏览器 QA 结果。
