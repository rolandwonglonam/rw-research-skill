# Cross-model evaluation

这里保存 RW Research Skill 的跨模型配对评测。

- `protocol.md`：范围、门槛和证据边界。
- `models.json`：模型入口。
- `development-fixtures-v1.json`：第一次完整运行使用的开发任务。
- `fixtures.json`：第 2 组任务。
- `results/`：完整模型输出、判分和摘要。

检查任务和模型配置：

```bash
python3 scripts/cross_model_eval.py check
```

运行需要本机已有 Codex 和 Claude 登录状态。每个任务会分别运行带 Skill 和不带 Skill 条件。运行 ID 不能覆盖。

```bash
python3 scripts/cross_model_eval.py run \
  --run-id YYYY-MM-DD-cross-model \
  --repetitions 1 \
  --workers 4
```

CI 只检查评测定义和确定性工具，不发起付费模型调用。
