"""Workflow Engine - Core orchestration logic"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from .interfaces import (
    IStage, IReporter, IInterventionHandler,
    WorkflowContext, WorkflowEvent, StageStatus, StageResult
)


class WorkflowEngine:
    """工作流引擎 - 负责协调各个阶段的执行

    这是系统的核心，遵循开闭原则：
    - 对扩展开放：可以添加新的 Stage、Reporter
    - 对修改封闭：核心逻辑不需要修改
    """

    def __init__(
        self,
        stages: List[IStage],
        reporters: Optional[List[IReporter]] = None,
        intervention_handler: Optional[IInterventionHandler] = None,
        max_iterations: int = 3,
        debug_mode: bool = False
    ):
        """初始化工作流引擎

        Args:
            stages: 工作流阶段列表（有序）
            reporters: 报告器列表（可选）
            intervention_handler: 人工介入处理器（可选）
            max_iterations: 最大迭代次数（debug模式下可无限）
            debug_mode: 是否开启Debug模式
        """
        self.stages = stages
        self.reporters = reporters or []
        self.intervention_handler = intervention_handler
        self.max_iterations = float('inf') if debug_mode else max_iterations
        self.debug_mode = debug_mode
        self.context = WorkflowContext()
        self._current_stage = None

    async def run(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流

        Args:
            initial_input: 初始输入（如用户需求）

        Returns:
            最终结果 {
                'status': 'success' | 'error' | 'aborted',
                'output': Any,
                'history': List[WorkflowEvent],
                'iterations': int
            }
        """
        # 初始化上下文
        self.context.set('initial_input', initial_input)
        self.context.set('start_time', datetime.now().isoformat())

        try:
            # 执行所有阶段
            for stage in self.stages:
                self._current_stage = stage
                await self._execute_stage(stage)

                # 检查是否中止
                if self.context.get('aborted'):
                    return self._build_result('aborted', 'Workflow aborted by user')

            # 成功完成
            return self._build_result('success', self.context.get('final_output'))

        except Exception as e:
            # 记录错误
            await self._report_event(WorkflowEvent(
                event_type='error',
                stage_name='workflow',
                data={'error': str(e), 'type': type(e).__name__}
            ))

            return self._build_result('error', None, str(e))

    async def _execute_stage(self, stage: IStage):
        """执行单个阶段"""

        # 检查是否可以执行
        if not await stage.can_execute(self.context):
            await self._report_event(WorkflowEvent(
                event_type='stage_skipped',
                stage_name=stage.name,
                data={'reason': 'Conditions not met'}
            ))
            return

        # 报告开始
        await self._report_event(WorkflowEvent(
            event_type='stage_start',
            stage_name=stage.name,
            data={}
        ))

        try:
            # 执行阶段
            result = await stage.execute(self.context)

            # 保存结果到上下文
            self.context.set(f'{stage.name}_result', result)
            self.context.set(f'{stage.name}_status', result.status.value)

            # 报告结束
            await self._report_event(WorkflowEvent(
                event_type='stage_end',
                stage_name=stage.name,
                data={
                    'status': result.status.value,
                    'output': result.output,
                    'error': result.error
                }
            ))

            # 如果失败，尝试人工介入
            if result.status == StageStatus.FAILED:
                await self._handle_stage_failure(stage, result)

        except Exception as e:
            # 阶段执行异常
            await stage.on_failure(self.context, e)
            await self._report_event(WorkflowEvent(
                event_type='stage_error',
                stage_name=stage.name,
                data={'error': str(e), 'type': type(e).__name__}
            ))
            raise

    async def _handle_stage_failure(self, stage: IStage, result: StageResult):
        """处理阶段失败"""

        # 检查是否有人工介入处理器
        if not self.intervention_handler:
            return

        # 检查是否需要介入
        if not await self.intervention_handler.should_intervene(self.context):
            return

        # 报告介入开始
        await self._report_event(WorkflowEvent(
            event_type='intervention_start',
            stage_name=stage.name,
            data={'reason': result.error}
        ))

        # 执行介入
        intervention_result = await self.intervention_handler.handle_intervention(self.context)

        # 报告介入结束
        await self._report_event(WorkflowEvent(
            event_type='intervention_end',
            stage_name=stage.name,
            data=intervention_result
        ))

        # 处理介入结果
        if intervention_result.get('abort'):
            self.context.set('aborted', True)
            await self._report_event(WorkflowEvent(
                event_type='workflow_aborted',
                stage_name=stage.name,
                data={'reason': 'User aborted'}
            ))

        elif intervention_result.get('retry'):
            # 增加迭代计数
            self.context.iteration += 1

            # 检查是否超过最大迭代次数
            if self.context.iteration < self.max_iterations:
                # 注入新指令给 Agent
                instructions = intervention_result.get('instructions', {})
                for agent_type, instruction in instructions.items():
                    agent = self.context.get_agent(agent_type)
                    if agent:
                        await agent.inject_instruction(instruction)

                # 重试阶段
                await self._execute_stage(stage)
            else:
                await self._report_event(WorkflowEvent(
                    event_type='max_iterations_reached',
                    stage_name=stage.name,
                    data={'iterations': self.context.iteration}
                ))

        elif intervention_result.get('skip'):
            # 跳过当前阶段
            await self._report_event(WorkflowEvent(
                event_type='stage_skipped_by_user',
                stage_name=stage.name,
                data={}
            ))

    async def _report_event(self, event: WorkflowEvent):
        """报告事件给所有 Reporter"""
        self.context.add_event(event)
        for reporter in self.reporters:
            try:
                await reporter.report(event)
            except Exception as e:
                # Reporter 失败不应影响主流程
                print(f"Warning: Reporter failed: {e}")

    def _build_result(self, status: str, output: Any, error: str = None) -> Dict[str, Any]:
        """构建最终结果"""
        return {
            'status': status,
            'output': output,
            'error': error,
            'history': self.context.history,
            'iterations': self.context.iteration,
            'duration': self._calculate_duration()
        }

    def _calculate_duration(self) -> str:
        """计算执行时长"""
        start_time_str = self.context.get('start_time')
        if not start_time_str:
            return 'unknown'

        start_time = datetime.fromisoformat(start_time_str)
        duration = datetime.now() - start_time
        return f"{duration.total_seconds():.2f}s"

    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态（用于 UI 显示）"""
        return {
            'current_stage': self._current_stage.name if self._current_stage else None,
            'iteration': self.context.iteration,
            'max_iterations': self.max_iterations if self.max_iterations != float('inf') else 'unlimited',
            'debug_mode': self.debug_mode,
            'total_events': len(self.context.history)
        }