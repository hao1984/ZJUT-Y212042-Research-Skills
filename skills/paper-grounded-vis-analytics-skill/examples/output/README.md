# Example Output

本目录保存 1 个主 demo 和 2 个扩展示例输出。主 demo 使用 Palmer Penguins morphology 数据集；扩展示例分别展示大规模 taxi 出行数据生成和论文驱动 demo 生成能力。

## 文件

- `demo_build_report.md`：demo 构建报告，说明分析目标、数据使用、真实数据证据、论文启发、反 dashboard 检查和验证结果。
- `critic_report.md`：Internal E Critic 检查结果。
- `app/`：可运行前端 demo。
- `screenshot_1440.png`、`screenshot_1920.png`：浏览器 smoke check 截图。
- `additional_examples/`：更多输出案例，包含 taxi city pulse braid 和 BNNVis paper-grounded demo。

## 查看主 demo

可以在本地用静态服务器打开：

```bash
python -m http.server 4053 --directory examples/output/app
```

然后访问：

```text
http://localhost:4053
```

如果直接打开 `app/index.html`，浏览器可能因本地文件访问策略限制数据加载；推荐使用静态服务器。

## 核心结果

demo 输出显示：

- 真实输入数据为 344 行、8 字段。
- 主视图使用 342 条完整形态记录。
- 系统保留 2 条缺失形态记录与 11 条未知性别记录。
- PC1 与 PC2 解释了 88.15% 的四维标准化形态方差。
- pooled correlation 与 within-species correlation 出现方向差异，形成可探索的 reversal boundary。
- critic 报告通过，未发现 mock data、缺失 provenance、dashboard 退化或 unsupported claims。

## 扩展示例

### Example 2: Taxi City Pulse Braid

路径：

```text
additional_examples/taxi_city_pulse_braid/
```

该案例展示 skill 处理大规模真实出行数据的能力。输入来自 NYC Yellow Taxi 2024 年 1 月 parquet 数据和 taxi zone lookup，原始表规模为 2,964,624 行、19 字段。输出不是常规地图或 KPI dashboard，而是一个 OD-time pulse braid 分析工作台。

可复查文件：

- `demo_build_report.md`
- `design_spec.md`
- `visual_quality_review.json`
- `app/`
- `screenshot_1440.png`
- `screenshot_1920.png`

报告中记录了真实数据 pipeline、聚合策略、浏览器 QA 结果和反 dashboard 检查。

### Example 3: BNNVis Paper-Grounded Demo

路径：

```text
additional_examples/bnnvis_paper_grounded_demo/
```

该案例展示在没有外部 CSV 数据集时，skill 也可以从论文标题、论文索引和本地论文库检索结果生成 paper-grounded 可视分析 demo。输入主题为 `BNNVis: Towards Visual Analytics for Bayesian Neural Networks`。

可复查文件：

- `frontend_build_report.md`
- `design_spec.md`
- `vis_reference_report.md`
- `browser_smoke.json`
- `app/`
- `screenshot_1440.png`
- `screenshot_1920.png`

其中 `vis_reference_report.md` 记录了检索到的相关论文和被借鉴的设计元素，`browser_smoke.json` 记录浏览器验证结果。
