"""Packaging Stage"""

from ..core.interfaces import IStage, StageResult, StageStatus, WorkflowContext


class PackagingStage(IStage):
    """打包发布阶段"""

    @property
    def name(self) -> str:
        return "packaging"

    async def execute(self, context: WorkflowContext) -> StageResult:
        """执行打包"""
        qa_agent = context.get_agent('qa')
        if not qa_agent:
            return StageResult(
                status=StageStatus.FAILED,
                error="QA agent not found"
            )

        # 检查测试是否通过
        testing_result = context.get('testing_result')
        if not testing_result or testing_result.status != StageStatus.SUCCESS:
            return StageResult(
                status=StageStatus.FAILED,
                error="Testing stage not passed"
            )

        try:
            # 打包发布
            result = await qa_agent.process({
                'action': 'package_release',
                'code_dir': context.memory.workspace / 'code'
            })

            package_path = result['package_path']

            # 保存到上下文
            context.set('final_output', package_path)

            return StageResult(
                status=StageStatus.SUCCESS,
                output={'package_path': package_path}
            )

        except Exception as e:
            return StageResult(
                status=StageStatus.FAILED,
                error=str(e)
            )

    async def can_execute(self, context: WorkflowContext) -> bool:
        """只有测试通过后才能执行打包"""
        testing_result = context.get('testing_result')
        return testing_result and testing_result.status == StageStatus.SUCCESS