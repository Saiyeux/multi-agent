# 架构重构设计 - 符合 SOLID 原则

## 当前架构问题分析

### 1. 违反开闭原则的地方

```python
# ❌ 问题：硬编码的工作流状态转换
class DevOrchestrator:
    async def run(self, user_requirement):
        # Stage 1
        self.state = WorkflowState.ANALYZING
        req_doc = await self.architect.analyze_requirement(...)

        # Stage 2
        self.state = WorkflowState.CODING
        code_files = await self.developer.implement(...)

        # 如果要添加新阶段，必须修改这个方法 ❌
```

**问题**：
- 添加新的工作流阶段需要修改核心 `run()` 方法
- 无法动态调整工作流顺序
- Debug 模式和普通模式耦合在一起

### 2. 缺乏抽象层

```python
# ❌ 问题：直接依赖具体实现
class DevOrchestrator:
    def __init__(self, config):
        self.architect = ArchitectAgent(config)  # 硬编码依赖
        self.developer = DeveloperAgent(config)
        self.qa = QAAgent(config)
```

**问题**：
- 无法替换或扩展 Agent 实现
- 难以添加新类型的 Agent
- 测试时无法 mock

### 3. 职责混乱

```python
# ❌ QA Agent 既负责测试，又负责分析，又负责打包
class QAAgent:
    async def run_tests(...)
    async def analyze_failure(...)  # 应该是独立的分析器
    async def package_release(...)   # 应该是独立的打包器
```

## 重构后的架构设计

### 核心原则

1. **单一职责原则 (SRP)**: 每个类只做一件事
2. **开闭原则 (OCP)**: 对扩展开放，对修改封闭
3. **里氏替换原则 (LSP)**: 可以替换任何实现
4. **接口隔离原则 (ISP)**: 细粒度的接口
5. **依赖倒置原则 (DIP)**: 依赖抽象，不依赖具体

### 新架构图

```
┌─────────────────────────────────────────────────────────┐
│                  Workflow Engine (核心)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Pipeline: [Stage1] → [Stage2] → [Stage3] → ... │  │
│  └──────────────────────────────────────────────────┘  │
│         ↓ 依赖抽象接口                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Interface: IStage, IAgent, IAnalyzer, IReporter│  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓ 实现
┌─────────────────────────────────────────────────────────┐
│                    Plugins (插件层)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Agents   │  │Analyzers │  │ Reporters│             │
│  │  ├─Arch  │  │├─Error   │  │├─Console │             │
│  │  ├─Dev   │  │├─Code    │  │├─Web     │             │
│  │  └─QA    │  │└─Perf    │  │└─File    │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Stages   │  │ Tools    │  │Intervene │             │
│  │├─Analyze │  │├─Executor│  │├─Prompt  │             │
│  │├─Design  │  │├─Tester  │  │├─Manual  │             │
│  │├─Code    │  │├─Linter  │  │└─Auto    │             │
│  │├─Test    │  │└─Packager│  │          │             │
│  │└─Package │  └──────────┘  └──────────┘             │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
```

## 详细设计

### 1. 核心接口定义

```python
# src/core/interfaces.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class StageStatus(Enum):
    """阶段执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """阶段执行结果"""
    status: StageStatus
    output: Dict[str, Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class IStage(ABC):
    """工作流阶段接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """阶段名称"""
        pass

    @abstractmethod
    async def execute(self, context: 'WorkflowContext') -> StageResult:
        """执行阶段

        Args:
            context: 工作流上下文，包含所有共享数据

        Returns:
            StageResult: 执行结果
        """
        pass

    @abstractmethod
    async def can_execute(self, context: 'WorkflowContext') -> bool:
        """判断是否可以执行此阶段"""
        pass

    async def on_failure(self, context: 'WorkflowContext', error: Exception):
        """失败时的钩子"""
        pass


class IAgent(ABC):
    """Agent 接口"""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Agent 类型"""
        pass

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务"""
        pass

    @abstractmethod
    async def inject_instruction(self, instruction: str):
        """注入新指令"""
        pass


class IAnalyzer(ABC):
    """分析器接口"""

    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据并返回结果"""
        pass


class IReporter(ABC):
    """报告器接口"""

    @abstractmethod
    async def report(self, event: 'WorkflowEvent'):
        """报告工作流事件"""
        pass


class IInterventionHandler(ABC):
    """人工介入处理器接口"""

    @abstractmethod
    async def should_intervene(self, context: 'WorkflowContext') -> bool:
        """判断是否需要介入"""
        pass

    @abstractmethod
    async def handle_intervention(self, context: 'WorkflowContext') -> Dict[str, Any]:
        """处理介入，返回新的指令"""
        pass


@dataclass
class WorkflowEvent:
    """工作流事件"""
    event_type: str  # stage_start, stage_end, error, intervention
    stage_name: str
    data: Dict[str, Any]
    timestamp: str


class WorkflowContext:
    """工作流上下文 - 共享数据存储"""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.agents: Dict[str, IAgent] = {}
        self.memory: 'SharedMemory' = None
        self.config: Dict[str, Any] = {}
        self.iteration: int = 0
        self.history: List[WorkflowEvent] = []

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value

    def get_agent(self, agent_type: str) -> Optional[IAgent]:
        return self.agents.get(agent_type)
```

### 2. 工作流引擎（核心）

```python
# src/core/workflow_engine.py

from typing import List, Optional, Callable
from .interfaces import IStage, IReporter, IInterventionHandler, WorkflowContext, WorkflowEvent, StageStatus


class WorkflowEngine:
    """工作流引擎 - 负责协调各个阶段的执行"""

    def __init__(
        self,
        stages: List[IStage],
        reporters: Optional[List[IReporter]] = None,
        intervention_handler: Optional[IInterventionHandler] = None,
        max_iterations: int = 3
    ):
        self.stages = stages
        self.reporters = reporters or []
        self.intervention_handler = intervention_handler
        self.max_iterations = max_iterations
        self.context = WorkflowContext()

    async def run(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流

        Args:
            initial_input: 初始输入（如用户需求）

        Returns:
            最终结果
        """
        # 初始化上下文
        self.context.set('initial_input', initial_input)

        try:
            # 执行所有阶段
            for stage in self.stages:
                await self._execute_stage(stage)

            return {
                'status': 'success',
                'output': self.context.get('final_output'),
                'history': self.context.history
            }

        except Exception as e:
            await self._report_event(WorkflowEvent(
                event_type='error',
                stage_name='workflow',
                data={'error': str(e)},
                timestamp=self._now()
            ))

            return {
                'status': 'error',
                'message': str(e),
                'history': self.context.history
            }

    async def _execute_stage(self, stage: IStage):
        """执行单个阶段"""

        # 检查是否可以执行
        if not await stage.can_execute(self.context):
            await self._report_event(WorkflowEvent(
                event_type='stage_skipped',
                stage_name=stage.name,
                data={},
                timestamp=self._now()
            ))
            return

        # 报告开始
        await self._report_event(WorkflowEvent(
            event_type='stage_start',
            stage_name=stage.name,
            data={},
            timestamp=self._now()
        ))

        try:
            # 执行阶段
            result = await stage.execute(self.context)

            # 保存结果到上下文
            self.context.set(f'{stage.name}_result', result)

            # 报告结束
            await self._report_event(WorkflowEvent(
                event_type='stage_end',
                stage_name=stage.name,
                data={'result': result},
                timestamp=self._now()
            ))

            # 如果失败，检查是否需要人工介入
            if result.status == StageStatus.FAILED:
                if self.intervention_handler:
                    if await self.intervention_handler.should_intervene(self.context):
                        intervention_result = await self.intervention_handler.handle_intervention(self.context)

                        # 根据介入结果决定是否重试
                        if intervention_result.get('retry'):
                            await self._execute_stage(stage)
                        elif intervention_result.get('skip'):
                            return
                        elif intervention_result.get('abort'):
                            raise Exception("Workflow aborted by user")

        except Exception as e:
            await stage.on_failure(self.context, e)
            raise

    async def _report_event(self, event: WorkflowEvent):
        """报告事件给所有 Reporter"""
        self.context.history.append(event)
        for reporter in self.reporters:
            await reporter.report(event)

    def _now(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
```

### 3. 阶段实现（插件）

```python
# src/stages/requirement_analysis.py

from ..core.interfaces import IStage, StageResult, StageStatus, WorkflowContext


class RequirementAnalysisStage(IStage):
    """需求分析阶段"""

    @property
    def name(self) -> str:
        return "requirement_analysis"

    async def execute(self, context: WorkflowContext) -> StageResult:
        """执行需求分析"""

        # 获取 Architect Agent
        architect = context.get_agent('architect')
        if not architect:
            return StageResult(
                status=StageStatus.FAILED,
                output={},
                error="Architect agent not found"
            )

        # 获取用户需求
        requirement = context.get('initial_input', {}).get('requirement')

        try:
            # 执行分析
            result = await architect.process({
                'action': 'analyze_requirement',
                'requirement': requirement
            })

            # 保存到共享内存
            context.memory.save('requirements', 'requirement.md', result['document'])

            return StageResult(
                status=StageStatus.SUCCESS,
                output=result
            )

        except Exception as e:
            return StageResult(
                status=StageStatus.FAILED,
                output={},
                error=str(e)
            )

    async def can_execute(self, context: WorkflowContext) -> bool:
        """总是可以执行"""
        return True
```

```python
# src/stages/testing_stage.py

class TestingStage(IStage):
    """测试阶段 - 支持迭代重试"""

    def __init__(self, analyzer: IAnalyzer, max_retries: int = 3):
        self.analyzer = analyzer  # 错误分析器
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "testing"

    async def execute(self, context: WorkflowContext) -> StageResult:
        """执行测试，失败时自动重试"""

        qa_agent = context.get_agent('qa')
        dev_agent = context.get_agent('developer')

        retries = 0
        while retries < self.max_retries:
            # 运行测试
            test_result = await qa_agent.process({
                'action': 'run_tests',
                'code_dir': context.memory.workspace / 'code',
                'test_dir': context.memory.workspace / 'tests'
            })

            if test_result['passed']:
                return StageResult(
                    status=StageStatus.SUCCESS,
                    output=test_result
                )

            # 测试失败 - 分析原因
            analysis = await self.analyzer.analyze(test_result)

            # 让开发者修复
            fix_result = await dev_agent.process({
                'action': 'fix_issues',
                'test_result': test_result,
                'analysis': analysis
            })

            # 保存修复后的代码
            for filename, content in fix_result['fixed_files'].items():
                context.memory.save('code', filename, content)

            retries += 1
            context.iteration = retries

        # 超过重试次数
        return StageResult(
            status=StageStatus.FAILED,
            output=test_result,
            error=f"Tests failed after {self.max_retries} retries"
        )

    async def can_execute(self, context: WorkflowContext) -> bool:
        # 只有在有代码和测试时才执行
        code_files = context.memory.list_files('code')
        test_files = context.memory.list_files('tests')
        return len(code_files) > 0 and len(test_files) > 0
```

### 4. Agent 重构（实现接口）

```python
# src/agents/base_agent.py (重构后)

from ..core.interfaces import IAgent


class BaseAgent(IAgent):
    """重构后的 BaseAgent - 实现 IAgent 接口"""

    def __init__(self, agent_type: str, config: Dict[str, Any], system_prompt: str):
        self._agent_type = agent_type
        self.config = config
        self.system_prompt = system_prompt
        self.client = ollama.Client(host=config['host'])
        self.dynamic_instructions: List[str] = []

    @property
    def agent_type(self) -> str:
        return self._agent_type

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务 - 根据 action 分发"""
        action = input_data.get('action')

        # 使用策略模式分发不同的操作
        handler = self._get_action_handler(action)
        if not handler:
            raise ValueError(f"Unknown action: {action}")

        return await handler(input_data)

    @abstractmethod
    def _get_action_handler(self, action: str) -> Optional[Callable]:
        """获取动作处理器（子类实现）"""
        pass

    async def inject_instruction(self, instruction: str):
        """注入新指令"""
        self.dynamic_instructions.append({
            'instruction': instruction,
            'timestamp': datetime.now().isoformat()
        })

    async def chat(self, prompt: str) -> str:
        """聊天 - 自动包含动态指令"""

        # 构建完整 prompt
        full_prompt = prompt
        if self.dynamic_instructions:
            recent_instructions = self.dynamic_instructions[-3:]
            instructions_text = "\n\n".join([
                f"[主管最新指示]: {inst['instruction']}"
                for inst in recent_instructions
            ])
            full_prompt = f"{instructions_text}\n\n{prompt}"

        # 调用 LLM
        response = self.client.chat(
            model=self.config['model'],
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': full_prompt}
            ],
            options={'temperature': self.config['temperature']}
        )

        return response['message']['content']
```

```python
# src/agents/developer.py (重构后)

class DeveloperAgent(BaseAgent):
    """开发者 Agent - 职责单一"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__('developer', config, DEVELOPER_SYSTEM_PROMPT)

    def _get_action_handler(self, action: str):
        """返回动作处理器"""
        handlers = {
            'implement': self._handle_implement,
            'write_tests': self._handle_write_tests,
            'fix_issues': self._handle_fix_issues
        }
        return handlers.get(action)

    async def _handle_implement(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """实现代码"""
        architecture_doc = input_data['architecture_doc']
        code_files = await self._generate_code(architecture_doc)
        return {'code_files': code_files}

    async def _handle_write_tests(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """编写测试"""
        code_files = input_data['code_files']
        test_files = await self._generate_tests(code_files)
        return {'test_files': test_files}

    async def _handle_fix_issues(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """修复问题 - 接收详细分析"""
        test_result = input_data['test_result']
        analysis = input_data.get('analysis', {})

        # 使用分析结果来指导修复
        prompt = self._build_fix_prompt(test_result, analysis)
        response = await self.chat(prompt)

        fixed_files = self._parse_code_files(response)
        return {'fixed_files': fixed_files}
```

### 5. 分析器（独立组件）

```python
# src/analyzers/error_analyzer.py

from ..core.interfaces import IAnalyzer


class ErrorAnalyzer(IAnalyzer):
    """错误分析器 - 使用 LLM 分析测试失败原因"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试失败"""

        error_output = data.get('output', '')

        prompt = f"""
作为专业的 QA 工程师，分析以下测试失败的根本原因：

测试输出：
{error_output}

请提供详细分析（JSON 格式）：
{{
  "error_type": "语法错误/导入错误/逻辑错误/配置错误",
  "location": "file:line",
  "root_cause": "详细原因",
  "fix_suggestions": ["具体建议1", "具体建议2"],
  "priority": "high/medium/low"
}}
"""

        response = await self.llm_client.chat(prompt)

        # 解析 JSON
        import json, re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        return {'raw_analysis': response}
```

### 6. 配置驱动的工作流构建

```python
# src/builders/workflow_builder.py

from typing import Dict, Any
from ..core.workflow_engine import WorkflowEngine
from ..core.interfaces import IStage
from ..stages import *
from ..agents import *
from ..analyzers import *


class WorkflowBuilder:
    """工作流构建器 - 根据配置构建工作流"""

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> WorkflowEngine:
        """从配置构建工作流"""

        # 1. 创建 Agent
        agents = {
            'architect': ArchitectAgent(config['ollama']['architect']),
            'developer': DeveloperAgent(config['ollama']['developer']),
            'qa': QAAgent(config['ollama']['qa'])
        }

        # 2. 创建分析器
        error_analyzer = ErrorAnalyzer(agents['qa'].client)

        # 3. 创建阶段（根据配置）
        stages = []
        for stage_config in config.get('workflow', {}).get('stages', []):
            stage = WorkflowBuilder._create_stage(stage_config, error_analyzer)
            if stage:
                stages.append(stage)

        # 4. 创建报告器
        reporters = [
            ConsoleReporter(),  # 控制台输出
        ]
        if config.get('web_ui', {}).get('enabled'):
            reporters.append(WebReporter())

        # 5. 创建介入处理器
        intervention_handler = None
        if config.get('workflow', {}).get('human_intervention'):
            intervention_handler = ManualInterventionHandler()

        # 6. 构建引擎
        engine = WorkflowEngine(
            stages=stages,
            reporters=reporters,
            intervention_handler=intervention_handler,
            max_iterations=config.get('workflow', {}).get('max_iterations', 3)
        )

        # 7. 设置上下文
        engine.context.agents = agents
        engine.context.memory = SharedMemory(config['project']['workspace'])
        engine.context.config = config

        return engine

    @staticmethod
    def _create_stage(stage_config: Dict, analyzer) -> Optional[IStage]:
        """创建阶段实例"""
        stage_type = stage_config['type']

        stage_classes = {
            'requirement_analysis': RequirementAnalysisStage,
            'architecture_design': ArchitectureDesignStage,
            'coding': CodingStage,
            'testing': lambda: TestingStage(analyzer=analyzer),
            'packaging': PackagingStage
        }

        stage_cls = stage_classes.get(stage_type)
        if callable(stage_cls):
            return stage_cls()
        return None
```

### 7. 配置文件（完全驱动）

```yaml
# config.yaml (增强版)

ollama:
  architect:
    host: "http://localhost:11434"
    model: "qwen2.5:3b"
    temperature: 0.7
  developer:
    host: "http://localhost:11435"
    model: "qwen2.5:3b"
    temperature: 0.3
  qa:
    host: "http://localhost:11436"
    model: "qwen2.5:3b"
    temperature: 0.5

workflow:
  # 工作流阶段（可配置顺序）
  stages:
    - type: requirement_analysis
      enabled: true

    - type: architecture_design
      enabled: true

    - type: coding
      enabled: true

    - type: testing
      enabled: true
      config:
        max_retries: 3
        use_analyzer: true

    - type: packaging
      enabled: true
      condition: "testing.status == 'success'"  # 条件执行

  # 迭代控制
  max_iterations: 3
  unlimited_in_debug: true

  # 人工介入
  human_intervention: true
  intervention_triggers:
    - testing_failed_3_times
    - syntax_error_detected

project:
  workspace: "./workspace"
  output_format: ["zip"]

# Debug 模式
debug:
  enabled: false
  detailed_logging: true
  code_structure_view: true
  iteration_history: true

# Web UI
web_ui:
  enabled: true
  port: 8501
  features:
    - agent_consoles
    - code_viewer
    - iteration_timeline
```

## 使用示例

```python
# main.py (重构后)

from src.builders.workflow_builder import WorkflowBuilder
from src.core.workflow_engine import WorkflowEngine

async def main():
    # 1. 加载配置
    config = load_yaml('config.yaml')

    # 2. 构建工作流
    engine = WorkflowBuilder.build_from_config(config)

    # 3. 运行
    result = await engine.run({
        'requirement': "创建定积分计算器..."
    })

    print(result)
```

## 扩展性验证

### 添加新阶段（无需修改核心代码）

```python
# 1. 实现新阶段
class CodeReviewStage(IStage):
    @property
    def name(self) -> str:
        return "code_review"

    async def execute(self, context):
        # 实现逻辑
        pass

# 2. 在配置中启用
# config.yaml
workflow:
  stages:
    - type: coding
    - type: code_review  # 新增
      enabled: true
    - type: testing
```

### 替换 Agent 实现（无需修改核心代码）

```python
# 使用 GPT-4 替换 Qwen
class GPT4Agent(IAgent):
    # 实现接口
    pass

# 在 WorkflowBuilder 中注册
agents['developer'] = GPT4Agent(config)
```

### 添加新的分析器（无需修改核心代码）

```python
class PerformanceAnalyzer(IAnalyzer):
    async def analyze(self, data):
        # 分析性能
        pass

# 注入到需要的阶段
stage = TestingStage(
    analyzer=CompositeAnalyzer([
        ErrorAnalyzer(),
        PerformanceAnalyzer()  # 新增
    ])
)
```

## 架构优势总结

✅ **开闭原则**: 添加新功能只需实现接口，不修改核心代码
✅ **单一职责**: 每个类职责明确（Engine 协调，Stage 执行，Agent 处理）
✅ **依赖倒置**: 核心依赖抽象接口，不依赖具体实现
✅ **可测试性**: 所有组件可独立测试，可 mock
✅ **可配置性**: 工作流完全由配置驱动
✅ **可扩展性**: 插件化架构，随时添加新组件

## 下一步实施计划

1. ✅ **架构设计完成** - 本文档
2. ⏭️ **实现核心接口和引擎** - `core/interfaces.py`, `core/workflow_engine.py`
3. ⏭️ **重构现有 Agent** - 实现 IAgent 接口
4. ⏭️ **实现基础阶段** - 5个核心 Stage
5. ⏭️ **实现分析器和报告器** - ErrorAnalyzer, ConsoleReporter
6. ⏭️ **实现 WorkflowBuilder** - 配置驱动构建
7. ⏭️ **编写单元测试** - 验证架构健壮性
8. ⏭️ **实现 Web UI 增强** - 基于新架构

这个架构可以保证：
- ✅ 添加/删除功能不影响核心
- ✅ 不会出现需要修改底层逻辑的 bug
- ✅ 代码整洁，职责清晰
- ✅ 符合 SOLID 原则