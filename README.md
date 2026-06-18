# ZJUT-Y212042 Research Skills

本目录是课程期末项目的 GitHub 提交整理版。当前提交包含 1 个 OpenClaw Research Skill：

- `skills/paper-grounded-vis-analytics-skill/`

该 skill 面向可视分析研究中的真实科研流程：先将论文 PDF 构建为本地可检索论文知识库，再从相关 VIS 论文中抽取系统设计经验，最后结合真实数据集生成可运行、可复查的多视图可视分析前端 demo。

## 提交内容

```text
ZJUT-Y212042-Research-Skills/
├── README.md
├── CONTRIBUTE.md
└── skills/
    └── paper-grounded-vis-analytics-skill/
        ├── SKILL.md
        ├── skill_card.md
        ├── components/
        ├── examples/
        │   ├── input/
        │   └── output/
        └── tests/
```

其中 `components/` 保留了三个可复用的阶段组件：

1. `paper-mineru-scholar-index`
2. `paper-grounded-vis-system-design`
3. `dataset-paper-grounded-vis-analytics`

三个组件共同形成从论文库构建到真实数据可视分析系统生成的完整工作流。
