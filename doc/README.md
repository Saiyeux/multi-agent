## 🏗️ 系统架构

### 设计理念：像管理真实团队一样管理 AI

这个系统的设计灵感来自于软件公司的真实工作流程：

```
WorkflowEngine (项目经理)
   ↓ 协调
┌─────────────────────────────────────┐
│ 5 个工作阶段（Stage）               │
│ ┌────────────────────────────────┐ │
│ │ 1. 需求分析  → Architect       │ │
│ │ 2. 架构设计  → Architect       │ │
│ │ 3. 代码实现  → Developer       │ │
│ │ 4. 测试验证  → QA + Developer  │ │
│ │ 5. 打包发布  → QA              │ │
│ └────────────────────────────────┘ │
└─────────────────────────────────────┘
   ↓ 驱动
┌─────────────────────────────────────┐
│ 3 个 AI Agent（员工）              │
│                                     │
│ 🧠 Architect (温度 0.7)            │
│    - 发散思维，创造性设计           │
│    - 端口 11434                    │
│                                     │
│ 💻 Developer (温度 0.3)            │
│    - 严谨精确，确定性编码           │
│    - 端口 11435                    │
│                                     │
│ 🔍 QA Engineer (温度 0.5)          │
│    - 平衡模式，测试和分析           │
│    - 端口 11436                    │
└─────────────────────────────────────┘
```

### 关键创新：智能错误分析

传统自动化系统的问题：
```
测试失败 → 重新生成代码 → 又失败 → 再重新生成 → 还是失败 → 💀
```

我们的解决方案：
```
测试失败
   ↓
QA 用 LLM 分析：
   "这是一个语法错误，在 test_app.py 第 15 行，
    原因是 bytes 字面量不支持中文字符，
    建议改用 response.data.decode('utf-8')"
   ↓
Developer 根据详细分析修复（而不是瞎猜）
   ↓
测试通过 ✅
```

### 技术亮点

1. **接口驱动设计**（`src/core/interfaces.py`）
   - 7 个核心接口：`IStage`, `IAgent`, `IAnalyzer`, `IReporter`...
   - 想加新功能？实现接口即可，无需改核心代码

2. **策略模式分发**（`src/agents/base_agent.py`）
   ```python
   async def process(self, input_data):
       action = input_data['action']  # 'implement', 'test', 'fix'...
       handler = self._get_action_handler(action)
       return await handler(input_data)
   ```

3. **动态指令注入**（预留人工介入）
   ```python
   # 想象一下：测试失败第 3 次了，你想给 Developer 一个提示
   developer.inject_instruction("注意处理除零错误")
   # 下次 Developer 工作时会看到这个指令
   ```

4. **Debug 模式的秘密武器**
   ```yaml
   # config.yaml
   workflow:
     max_iterations: 3  # 普通模式：最多重试 3 次

   # --debug 参数
   max_iterations: ∞   # Debug 模式：无限重试，直到成功！
   ```

## 📖 使用场景

### 场景 1：快速原型（5分钟出 MVP）

```bash
python -m src.main -r "创建一个 TODO 列表 CLI 工具，支持增删改查"
```

**3 分钟后**：
- ✅ 完整的 Python 代码
- ✅ 单元测试（覆盖率 80%+）
- ✅ 可运行的 zip 包
- ✅ README 文档

### 场景 2：学习最佳实践

想学习如何写某个功能？让 AI 团队先做一遍：

```bash
python -m src.main -r "创建一个 Flask API，使用 JWT 认证和 SQLAlchemy ORM"
```

查看生成的代码，学习架构设计和代码组织方式。

### 场景 3：Debug 模式破解难题

遇到 AI 总是写不对的需求？

```bash
python -m src.main -r "实现辛普森积分法计算定积分" --debug
```

**效果**：
- 第 1 次：语法错误 → QA 分析 → Developer 修复
- 第 2 次：逻辑错误 → QA 分析 → Developer 修复
- 第 3 次：边界情况 → QA 分析 → Developer 修复
- 第 4 次：通过！ ✅

不限制次数，总能搞定。

## 🎨 配置调优

### config.yaml 核心参数解析

```yaml
ollama:
  architect:
    temperature: 0.7  # 🎨 创造力：高
                      # 设计架构需要发散思维

  developer:
    temperature: 0.3  # 🎯 精确度：高
                      # 写代码要严谨，少犯错

  qa:
    temperature: 0.5  # ⚖️ 平衡
                      # 测试既要严格也要灵活

workflow:
  max_iterations: 3   # 🔄 重试次数
                      # 建议：简单需求 3 次，复杂需求用 --debug

project:
  workspace: "./workspace"  # 📁 工作区
                            # 所有生成文件的家
```

### 性能优化建议

**硬件要求**：
- 最低：16GB RAM（能跑，但可能有点慢）
- 推荐：24GB RAM（M4 MacBook Air，流畅）
- 理想：32GB+ RAM（多任务无压力）

**速度优化**：
```bash
# 预加载模型（setup_ollama.sh 已自动执行）
# keep_alive=-1 表示模型常驻内存，响应更快
curl http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:3b","keep_alive":-1,"prompt":"hello"}'
```

## 🔧 高级扩展

### 添加新的工作阶段

想在代码实现后加一个代码审查阶段？

```python
# 1. 创建 src/stages/code_review.py
from src.core.interfaces import IStage, StageResult, StageStatus

class CodeReviewStage(IStage):
    @property
    def name(self) -> str:
        return "code_review"

    async def execute(self, context):
        architect = context.get_agent('architect')

        # Architect 审查 Developer 的代码
        review_result = await architect.process({
            'action': 'review_code',
            'code_files': context.memory.list_files('code')
        })

        return StageResult(
            status=StageStatus.SUCCESS,
            output=review_result
        )

# 2. 在 src/builders/workflow_builder.py 注册
stages = [
    RequirementAnalysisStage(),
    ArchitectureDesignStage(),
    CodingStage(),
    CodeReviewStage(),      # 👈 新增
    TestingStage(...),
    PackagingStage()
]
```

### 添加新的 Agent 能力

给 Developer 增加代码重构能力：

```python
# src/agents/developer.py
class DeveloperAgent(BaseAgent):
    def _get_action_handler(self, action):
        return {
            'implement': self._implement,
            'write_tests': self._write_tests,
            'fix_issues': self._fix_issues,
            'refactor': self._refactor  # 👈 新增
        }.get(action)

    async def _refactor(self, input_data):
        code_file = input_data['code_file']
        refactor_goal = input_data['goal']  # "提高可读性" / "优化性能"

        prompt = f"""
        重构以下代码，目标：{refactor_goal}

        原始代码：
        {code_file}

        请提供重构后的代码...
        """

        response = await self.chat(prompt)
        return {'refactored_code': response}
```

## 🐛 常见问题

### Q1: "Ollama 连接失败"

**原因**：`setup_ollama.sh` 没有运行或进程被杀死。

**解决**：
```bash
# 检查进程
ps aux | grep ollama

# 如果没有，重新启动
bash scripts/setup_ollama.sh
```

### Q2: "测试一直失败，重试 3 次都不行"

**原因**：需求太复杂，或模型能力有限。

**解决**：
```bash
# 开启 Debug 模式，无限重试
python -m src.main -r "你的需求" --debug

# 或者，简化需求，分步骤实现
```

### Q3: "生成的代码质量不高"

**限制认知**：qwen2.5:3b 是 30 亿参数的小模型，能力有限。

**改进方向**：
- 换更大的模型（如 qwen2.5:14b，需要更多内存）
- 提供更详细的需求描述
- 使用 Debug 模式多迭代几次
- 生成后人工 review 和优化

### Q4: "想看 AI 的思考过程"

**方法 1**：Web UI 显示实时日志

**方法 2**：查看对话历史
```python
# 在代码中添加
print(agent.conversation_history)
```

### Q5: "如何停止运行中的任务？"

**CLI 模式**：`Ctrl+C`

**Web UI 模式**：关闭浏览器标签页，然后：
```bash
pkill -f "python -m src.main"
```

**停止 Ollama**：
```bash
pkill ollama
```

## 📊 系统限制与未来计划

### 当前限制

- 🎯 **模型能力**：qwen2.5:3b 适合简单到中等复杂度的需求
- 🐍 **语言支持**：目前主要支持 Python 项目（测试和执行基于 Python）
- 💻 **资源消耗**：3 个 Ollama 实例同时运行，需要 16GB+ 内存
- 👀 **代码审查**：生成的代码需要人工 review 后再用于生产环境

### 未来计划

- [ ] **多语言支持**：JavaScript、Go、Java 项目生成
- [ ] **更大模型**：支持 qwen2.5:14b / qwen2.5:32b
- [ ] **人工介入 UI**：Web 界面实时注入指令给 Agent
- [ ] **Git 集成**：自动创建分支、提交代码、发 PR
- [ ] **CI/CD 集成**：生成 GitHub Actions / GitLab CI 配置
- [ ] **Docker 化部署**：一键启动整个系统

## 🙏 致谢

- **Ollama** - 让本地 LLM 运行变得简单
- **Qwen2.5** - 强大的开源中文模型
- **Streamlit** - 快速构建 Web UI

## 📜 开源协议

MIT License - 随意使用，但后果自负 😄

---

**现在，开始你的第一个 AI 协作项目吧！**

```bash
# 启动 AI 团队
bash scripts/setup_ollama.sh

# 发布第一个任务
python -m src.main -r "创建一个命令行计算器"

# 见证奇迹 ✨
```
