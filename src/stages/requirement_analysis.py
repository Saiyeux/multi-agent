"""Requirement Analysis Stage"""

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
                error="Architect agent not found"
            )

        # 获取用户需求
        requirement = context.get('initial_input', {}).get('requirement')
        if not requirement:
            return StageResult(
                status=StageStatus.FAILED,
                error="No requirement provided"
            )

        try:
            # 执行分析
            result = await architect.process({
                'action': 'analyze_requirement',
                'requirement': requirement
            })

            # 保存到共享内存
            doc = result['document']
            context.memory.save('requirements', 'requirement.md', doc)

            return StageResult(
                status=StageStatus.SUCCESS,
                output={'document': doc}
            )

        except Exception as e:
            return StageResult(
                status=StageStatus.FAILED,
                error=str(e)
            )