# 最小智能体运行时：示例实现

这个示例用于展示智能体运行时的必要组件，不作为生产框架。

## 目录

```text
minimal-agent/
├─ agents/          # Agent 抽象与简单实现
├─ core/            # 消息、模型接口、解析器与执行循环
├─ tools/           # 工具协议、注册、执行与适配器
├─ tests/tools/     # 按组件职责组织的验证脚本
└─ run_minimal.py   # 最小运行入口
```

## 组件关系

1. `core/messages.py` 定义统一消息；
2. `core/llm.py` 隔离模型接口；
3. `tools/registry.py` 管理工具定义；
4. `tools/runner.py` 校验并执行工具；
5. `core/agent_loop.py` 维护模型与工具之间的循环。

## 验证

不依赖真实模型的核心验证可以从 `tests/tools/test_agent_loop.py`、`test_registry.py` 和 `test_tool_runner.py` 开始。需要外部模型的示例应通过环境变量提供配置，不在仓库中保存凭据。
