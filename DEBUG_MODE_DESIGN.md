# Debug 模式设计文档

## 问题分析

### 当前测试失败的根本原因

1. **语法错误**: `assert b"计算积分" in response.data` - bytes 字面量只能包含 ASCII 字符
2. **缺少 imports**: 测试文件缺少 `create_engine`, `Base`, `sessionmaker` 等导入
3. **fixture 缺失**: 缺少 pytest 的 `client` fixture
4. **QA Agent 无法定位真正问题**: 只知道 "0 total, 0 failed"，无法获取详细的语法错误信息

### 核心问题

- **测试执行失败时没有捕获详细错误** - pytest 收集阶段失败
- **QA 没有给 Developer 提供具体的错误分析** - 只是简单传递错误信息
- **缺少人工介入机制** - 无法在迭代过程中给 Agent 提供指导

## Debug 模式架构设计

### 1. 增强的错误反馈机制

```python
class QAAgent:
    async def run_tests_with_analysis(self, code_dir, test_dir):
        """运行测试并提供详细分析"""

        # Step 1: 执行测试
        test_result = await self.run_tests(code_dir, test_dir)

        # Step 2: 如果失败，分析根本原因
        if not test_result['passed']:
            analysis = await self.analyze_failure(test_result)
            test_result['root_cause_analysis'] = analysis

        return test_result

    async def analyze_failure(self, test_result):
        """使用 LLM 分析测试失败的根本原因"""

        error_output = test_result.get('output', '')

        prompt = f"""
作为 QA 工程师，分析以下测试失败的根本原因：

测试输出：
{error_output}

请提供：
1. 错误类型（语法错误/导入错误/逻辑错误/配置错误）
2. 具体错误位置（文件:行号）
3. 错误原因分析
4. 修复建议（给开发者的具体指导）

输出 JSON 格式：
{{
  "error_type": "...",
  "location": "...",
  "root_cause": "...",
  "fix_suggestions": ["建议1", "建议2"]
}}
"""
        return await self.chat(prompt)
```

### 2. 无限迭代模式

```python
class DevOrchestrator:
    def __init__(self, config, debug_mode=False):
        self.debug_mode = debug_mode
        self.max_iterations = float('inf') if debug_mode else config['workflow']['max_iterations']
        self.iteration_history = []  # 记录每次迭代的详细信息

    async def run(self, user_requirement, human_intervention_callback=None):
        """
        human_intervention_callback:
            可选的回调函数，在每次迭代后调用
            返回 None 继续自动迭代
            返回 dict 则注入新的指令给各个 Agent
        """

        while self.iteration < self.max_iterations:
            # ... 测试执行 ...

            if not test_result['passed']:
                # 记录迭代历史
                iteration_info = {
                    'iteration': self.iteration,
                    'test_result': test_result,
                    'analysis': test_result.get('root_cause_analysis'),
                    'timestamp': datetime.now().isoformat()
                }
                self.iteration_history.append(iteration_info)

                # 人工介入点
                if human_intervention_callback and self.debug_mode:
                    intervention = await human_intervention_callback(iteration_info)

                    if intervention:
                        # 注入新的指令
                        if 'architect_prompt' in intervention:
                            await self.inject_prompt('architect', intervention['architect_prompt'])
                        if 'developer_prompt' in intervention:
                            await self.inject_prompt('developer', intervention['developer_prompt'])
                        if 'qa_prompt' in intervention:
                            await self.inject_prompt('qa', intervention['qa_prompt'])

                        # 如果用户要求停止
                        if intervention.get('stop'):
                            break

                # 让 Developer 根据详细分析修复
                fixed_code = await self.developer.fix_issues_with_guidance(
                    test_result,
                    guidance=test_result.get('root_cause_analysis')
                )
```

### 3. Prompt 注入机制

```python
class BaseAgent:
    def __init__(self, ...):
        self.dynamic_instructions = []  # 动态注入的指令

    async def inject_instruction(self, instruction: str):
        """注入新的指令（像主管给员工开会）"""
        self.dynamic_instructions.append({
            'instruction': instruction,
            'timestamp': datetime.now().isoformat()
        })

    async def chat(self, prompt: str, context=None):
        """聊天时会考虑动态注入的指令"""

        # 构建完整 prompt
        full_prompt = prompt

        if self.dynamic_instructions:
            instructions_text = "\n\n".join([
                f"[主管指示 {i+1}]: {inst['instruction']}"
                for i, inst in enumerate(self.dynamic_instructions[-3:])  # 只保留最近3条
            ])
            full_prompt = f"{instructions_text}\n\n{prompt}"

        return await self._original_chat(full_prompt, context)
```

### 4. 代码架构可视化

```python
class SharedMemory:
    def get_code_structure(self) -> Dict[str, Any]:
        """获取代码结构树"""

        def build_tree(path: Path, prefix=""):
            tree = {}
            for item in sorted(path.iterdir()):
                if item.is_file():
                    tree[item.name] = {
                        'type': 'file',
                        'size': item.stat().st_size,
                        'lines': len(item.read_text().splitlines())
                    }
                elif item.is_dir():
                    tree[item.name] = {
                        'type': 'directory',
                        'children': build_tree(item, prefix + "  ")
                    }
            return tree

        return {
            'code': build_tree(self.workspace / 'code'),
            'tests': build_tree(self.workspace / 'tests')
        }
```

## Web UI 增强设计

### 新增功能

1. **代码架构面板**
   - 树形结构显示所有生成的文件
   - 点击文件查看代码
   - 显示文件统计（行数、大小）

2. **迭代历史面板**
   - 时间线显示每次迭代
   - 展开查看详细错误分析
   - 高亮显示根本原因

3. **三个 Agent 控制窗口**
   ```
   [Architect 控制台]  [Developer 控制台]  [QA 控制台]

   当前状态: IDLE      当前状态: CODING     当前状态: TESTING

   [输入新指令]        [输入新指令]         [输入新指令]
   _______________    _______________     _______________
   |             |    |             |     |             |
   |_____________|    |_____________|     |_____________|

   [发送]  [清空历史]  [发送]  [清空历史]  [发送]  [清空历史]

   历史指令:          历史指令:           历史指令:
   - 指令1           - 指令1             - 指令1
   - 指令2           - 指令2             - 指令2
   ```

4. **实时日志流**
   - 显示每个 Agent 的实时输出
   - 不同颜色区分不同 Agent
   - 支持搜索和过滤

## 实现优先级

### Phase 1: 错误分析增强 ✅ 优先
- [ ] 修复 QA Agent 的测试执行逻辑
- [ ] 实现 `analyze_failure()` 方法
- [ ] 增强 Developer Agent 的 `fix_issues()` 接收详细分析

### Phase 2: 无限迭代模式
- [ ] 添加 `debug_mode` 参数
- [ ] 实现迭代历史记录
- [ ] 移除迭代次数限制（debug 模式下）

### Phase 3: Prompt 注入
- [ ] 在 BaseAgent 添加 `inject_instruction()`
- [ ] 修改 Orchestrator 支持回调机制
- [ ] 实现 Web UI 的控制台界面

### Phase 4: 可视化增强
- [ ] 代码结构树组件
- [ ] 迭代历史时间线
- [ ] 实时日志流

## 配置文件扩展

```yaml
# config.yaml
workflow:
  debug_mode: true          # 开启 Debug 模式
  max_iterations: 3         # 非 debug 模式的限制
  unlimited_iterations: true # debug 模式下无限迭代
  detailed_analysis: true    # QA 提供详细分析
  human_intervention: true   # 允许人工介入
```

## 使用示例

```python
# 启动 debug 模式
config = DevOrchestrator.load_config('config.yaml')
config['workflow']['debug_mode'] = True

orchestrator = DevOrchestrator(config)

# 定义人工介入回调
async def intervention_callback(iteration_info):
    print(f"\n迭代 {iteration_info['iteration']} 失败")
    print(f"根本原因: {iteration_info['analysis']}")

    # 可以从 Web UI 获取用户输入
    user_input = await get_user_intervention()

    if user_input['continue']:
        return {
            'developer_prompt': user_input.get('dev_instruction'),
            'qa_prompt': user_input.get('qa_instruction')
        }
    else:
        return {'stop': True}

result = await orchestrator.run(
    "创建定积分计算器",
    human_intervention_callback=intervention_callback
)
```