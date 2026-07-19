# Contributing

欢迎提交问题和改动。这个仓库接受以下内容：

- 不能正确路由的合成任务。
- Skill 指令中的边界冲突、状态冲突或缺失步骤。
- 可以重放的确定性工具测试。
- 不依赖个人研究材料的公开方法和来源入口。
- README、安装说明和错误信息修正。

## 提交 Issue

请说明：

- 使用的 Skill 和版本。
- 输入是否为合成材料。
- 实际结果和预期结果。
- 模型、工具和运行环境。
- 这个问题会造成什么影响。

不要提交论文全文、未公开数据、真实参与者信息、评审记录、凭证、个人路径或联系方式。

## 提交 Pull Request

1. 每个 Pull Request 处理一个问题。
2. 说明改了什么、为什么改、怎样验证。
3. 新增案例和评测任务时使用合成输入。
4. 不把静态检查写成模型行为已经通过。
5. 不把合成任务结果写成真实科研效果。

提交前运行：

```bash
python3 scripts/check_public_privacy.py
python3 scripts/check_repository.py
python3 -m unittest discover -s tests -v
```

需要修改跨模型评测时，先阅读 [`evals/cross-model/protocol.md`](evals/cross-model/protocol.md)。已经运行过的任务不能改分后继续标记为 held-out。

提交的内容按仓库 [Apache-2.0 License](LICENSE) 发布。
