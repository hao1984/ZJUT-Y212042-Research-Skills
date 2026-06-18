# Example Input

本示例演示如何使用 `paper-grounded-vis-analytics-skill` 从真实数据集生成可运行的可视分析 demo。

## 文件

- `palmer_penguins_morphology.csv`：Palmer Penguins morphology 数据集，344 行、8 个字段。
- `demo_request.md`：示例用户请求，描述数据集和分析目标。

## 使用意图

该 demo 不是让模型简单画几张图，而是要求 skill：

1. 读取真实数据并保留缺失值说明。
2. 挖掘企鹅形态空间中的数据特定模式。
3. 检索或参考可视分析论文中的多视图设计经验。
4. 生成可运行的多视图分析工作台。
5. 输出可复查的 build report、critic report 和浏览器截图。
