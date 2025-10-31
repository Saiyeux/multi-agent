"""Core interfaces for the multi-agent system - SOLID principles"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


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
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEvent:
    """工作流事件"""
    event_type: str  # stage_start, stage_end, error, intervention
    stage_name: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class WorkflowContext:
    """工作流上下文 - 共享数据存储"""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.agents: Dict[str, 'IAgent'] = {}
        self.memory: Optional['SharedMemory'] = None
        self.config: Dict[str, Any] = {}
        self.iteration: int = 0
        self.history: List[WorkflowEvent] = []

    def get(self, key: str, default=None) -> Any:
        """获取数据"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """设置数据"""
        self.data[key] = value

    def get_agent(self, agent_type: str) -> Optional['IAgent']:
        """获取 Agent"""
        return self.agents.get(agent_type)

    def add_event(self, event: WorkflowEvent):
        """添加事件到历史"""
        self.history.append(event)


class IStage(ABC):
    """工作流阶段接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """阶段名称"""
        pass

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> StageResult:
        """执行阶段

        Args:
            context: 工作流上下文，包含所有共享数据

        Returns:
            StageResult: 执行结果
        """
        pass

    async def can_execute(self, context: WorkflowContext) -> bool:
        """判断是否可以执行此阶段（默认总是可以）"""
        return True

    async def on_failure(self, context: WorkflowContext, error: Exception):
        """失败时的钩子（可选覆盖）"""
        pass


class IAgent(ABC):
    """Agent 接口"""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Agent 类型 (architect/developer/qa)"""
        pass

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务

        Args:
            input_data: 输入数据，必须包含 'action' 字段

        Returns:
            处理结果
        """
        pass

    @abstractmethod
    async def inject_instruction(self, instruction: str):
        """注入新指令（用于人工介入）"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息（可选覆盖）"""
        return {'agent_type': self.agent_type}


class IAnalyzer(ABC):
    """分析器接口"""

    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据并返回结果

        Args:
            data: 需要分析的数据

        Returns:
            分析结果
        """
        pass


class IReporter(ABC):
    """报告器接口"""

    @abstractmethod
    async def report(self, event: WorkflowEvent):
        """报告工作流事件

        Args:
            event: 工作流事件
        """
        pass


class IInterventionHandler(ABC):
    """人工介入处理器接口"""

    @abstractmethod
    async def should_intervene(self, context: WorkflowContext) -> bool:
        """判断是否需要介入

        Args:
            context: 工作流上下文

        Returns:
            是否需要介入
        """
        pass

    @abstractmethod
    async def handle_intervention(self, context: WorkflowContext) -> Dict[str, Any]:
        """处理介入，返回新的指令

        Args:
            context: 工作流上下文

        Returns:
            介入结果，可能包含:
            - retry: bool - 是否重试
            - skip: bool - 是否跳过
            - abort: bool - 是否中止
            - instructions: Dict[str, str] - 给各个 Agent 的指令
        """
        pass