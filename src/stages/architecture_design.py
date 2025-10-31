"""Architecture Design Stage"""

from ..core.interfaces import IStage, StageResult, StageStatus, WorkflowContext


class ArchitectureDesignStage(IStage):
    """架构设计阶段"""

    @property
    def name(self) -> str:
        return "architecture_design"

    async def execute(self, context: WorkflowContext) -> StageResult:
        """执行架构设计"""
        architect = context.get_agent('architect')
        if not architect:
            return StageResult(
                status=StageStatus.FAILED,
                error="Architect agent not found"
            )

        # 获取需求文档
        req_result = context.get('requirement_analysis_result')
        if not req_result or req_result.status != StageStatus.SUCCESS:
            return StageResult(
                status=StageStatus.FAILED,
                error="Requirement analysis not completed"
            )

        requirement_doc = req_result.output.get('document')

        try:
            # 执行设计
            result = await architect.process({
                'action': 'design_architecture',
                'requirement_doc': requirement_doc
            })

            # 保存到共享内存
            doc = result['document']
            context.memory.save('design', 'architecture.md', doc)

            return StageResult(
                status=StageStatus.SUCCESS,
                output={'document': doc}
            )

        except Exception as e:
            return StageResult(
                status=StageStatus.FAILED,
                error=str(e)
            )