"""Workflow Builder - Constructs workflow from configuration"""

from typing import Dict, Any
import yaml

from ..core.workflow_engine import WorkflowEngine
from ..core.shared_memory import SharedMemory
from ..stages import (
    RequirementAnalysisStage,
    ArchitectureDesignStage,
    CodingStage,
    TestingStage,
    PackagingStage
)
from ..agents import ArchitectAgent, DeveloperAgent, QAAgent
from ..analyzers import ErrorAnalyzer
from ..reporters import ConsoleReporter


class WorkflowBuilder:
    """工作流构建器 - 根据配置构建完整的工作流引擎

    遵循建造者模式，将复杂的构建过程封装起来
    """

    @staticmethod
    def build_from_config(config_path: str = "config.yaml") -> WorkflowEngine:
        """从配置文件构建工作流

        Args:
            config_path: 配置文件路径

        Returns:
            配置好的 WorkflowEngine 实例
        """
        # 1. 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return WorkflowBuilder.build_from_dict(config)

    @staticmethod
    def build_from_dict(config: Dict[str, Any]) -> WorkflowEngine:
        """从配置字典构建工作流

        Args:
            config: 配置字典

        Returns:
            配置好的 WorkflowEngine 实例
        """
        # 2. 创建 Agent
        agents = {
            'architect': ArchitectAgent(config['ollama']['architect']),
            'developer': DeveloperAgent(config['ollama']['developer']),
            'qa': QAAgent(config['ollama']['qa'])
        }

        # 3. 创建分析器
        error_analyzer = ErrorAnalyzer(agents['qa'])

        # 4. 创建阶段
        stages = [
            RequirementAnalysisStage(),
            ArchitectureDesignStage(),
            CodingStage(),
            TestingStage(
                analyzer=error_analyzer,
                max_retries=config.get('workflow', {}).get('max_iterations', 3)
            ),
            PackagingStage()
        ]

        # 5. 创建报告器
        reporters = [
            ConsoleReporter(verbose=True)
        ]

        # 6. 人工介入处理器（暂时不实现，后续扩展）
        intervention_handler = None

        # 7. 构建引擎
        debug_mode = config.get('debug', {}).get('enabled', False)
        max_iterations = config.get('workflow', {}).get('max_iterations', 3)

        engine = WorkflowEngine(
            stages=stages,
            reporters=reporters,
            intervention_handler=intervention_handler,
            max_iterations=max_iterations,
            debug_mode=debug_mode
        )

        # 8. 设置上下文
        engine.context.agents = agents
        engine.context.memory = SharedMemory(config['project']['workspace'])
        engine.context.config = config

        return engine