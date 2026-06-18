# Tests and Verification

本 skill 的验证重点不是单元测试覆盖率，而是科研输出是否可复查。

## 1. 文件结构检查

确认提交目录包含：

```text
SKILL.md
skill_card.md
examples/input/
examples/output/
components/
```

## 2. Demo 可运行性检查

在 `paper-grounded-vis-analytics-skill/` 目录下运行：

```bash
python -m http.server 4053 --directory examples/output/app
```

然后打开：

```text
http://localhost:4053
```

检查页面是否正常显示主分析视图、右侧说明/证据面板和交互控件。

## 3. 证据检查

阅读 `examples/output/demo_build_report.md`，确认：

- 是否说明了数据路径、行列数、缺失情况和是否采样。
- 是否列出真实数据发现，例如相关性、边界记录或异常记录。
- 是否说明论文启发如何影响布局、交互或证据展示。
- 是否标注了局限性。

## 4. Critic 检查

阅读 `examples/output/critic_report.md`，确认 hard-fail 项为 `False`，且 recommendation 为 `pass`。

## 5. 浏览器截图检查

打开：

- `examples/output/screenshot_1440.png`
- `examples/output/screenshot_1920.png`

确认不同视口下首屏可见、主要图元渲染完整，没有明显重叠或空白。
