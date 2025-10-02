"""Main orchestrator for multi-agent workflow"""

from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from .agents import ArchitectAgent, DeveloperAgent, QAAgent
from .core.shared_memory import SharedMemory


class WorkflowState(Enum):
    """工作流状态"""
    INIT = "init"
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    CODING = "coding"
    TESTING = "testing"
    REVIEWING = "reviewing"
    PACKAGING = "packaging"
    COMPLETED = "completed"
    FAILED = "failed"


class DevOrchestrator:
    """主协调器 - 管理整个开发流程"""

    def __init__(self, config: Dict[str, Any]):
        """初始化协调器

        Args:
            config: 配置字典（从config.yaml加载）
        """
        self.config = config
        self.memory = SharedMemory(config['project']['workspace'])

        # 初始化三个Agent
        self.architect = ArchitectAgent(config['ollama']['architect'])
        self.developer = DeveloperAgent(config['ollama']['developer'])
        self.qa = QAAgent(config['ollama']['qa'])

        self.state = WorkflowState.INIT
        self.iteration = 0
        self.max_iterations = config['workflow']['max_iterations']

    async def run(self, user_requirement: str) -> Dict[str, Any]:
        """执行完整开发流程

        Args:
            user_requirement: 用户需求描述

        Returns:
            开发结果 {
                'status': 'success' | 'failed' | 'error',
                'package': str (if success),
                'report': dict,
                'reason': str (if failed)
            }
        """
        try:
            print(f"[Orchestrator] Starting workflow with requirement: {user_requirement[:50]}...")

            # Stage 1: 需求分析和架构设计
            print(f"\n[Stage 1] {WorkflowState.ANALYZING.value}...")
            self.state = WorkflowState.ANALYZING
            req_doc = await self.architect.analyze_requirement(user_requirement)
            self.memory.save('requirements', 'requirement.md', req_doc)
            print(f"✓ Requirements saved")

            print(f"\n[Stage 1] {WorkflowState.DESIGNING.value}...")
            self.state = WorkflowState.DESIGNING
            design_doc = await self.architect.design_architecture(req_doc)
            self.memory.save('design', 'architecture.md', design_doc)
            print(f"✓ Architecture design saved")

            # Stage 2: 代码开发
            print(f"\n[Stage 2] {WorkflowState.CODING.value}...")
            self.state = WorkflowState.CODING
            code_files = await self.developer.implement(design_doc)
            for filename, content in code_files.items():
                self.memory.save('code', filename, content)
                print(f"✓ Code file saved: {filename}")

            test_files = await self.developer.write_tests(code_files)
            for filename, content in test_files.items():
                self.memory.save('tests', filename, content)
                print(f"✓ Test file saved: {filename}")

            # Stage 3: 测试和发布（带重试机制）
            while self.iteration < self.max_iterations:
                print(f"\n[Stage 3] {WorkflowState.TESTING.value} (Iteration {self.iteration + 1}/{self.max_iterations})...")
                self.state = WorkflowState.TESTING

                test_result = await self.qa.run_tests(
                    self.memory.workspace / 'code',
                    self.memory.workspace / 'tests'
                )

                print(f"Test results: {test_result['total']} total, {test_result['failed']} failed")

                if test_result['passed']:
                    # 测试通过，打包发布
                    print(f"\n✓ All tests passed! Proceeding to packaging...")
                    self.state = WorkflowState.PACKAGING
                    package_path = await self.qa.package_release(
                        self.memory.workspace / 'code'
                    )

                    self.state = WorkflowState.COMPLETED
                    print(f"\n🎉 Development completed successfully!")
                    print(f"Package location: {package_path}")

                    return {
                        'status': 'success',
                        'package': package_path,
                        'report': test_result
                    }
                else:
                    # 测试失败，尝试修复
                    print(f"\n✗ Tests failed. Attempting to fix issues...")
                    self.iteration += 1

                    if self.iteration >= self.max_iterations:
                        print(f"✗ Max iterations reached ({self.max_iterations})")
                        break

                    # 让Developer修复问题
                    fixed_code = await self.developer.fix_issues(test_result)
                    for filename, content in fixed_code.items():
                        self.memory.save('code', filename, content)
                        print(f"✓ Fixed code saved: {filename}")

            # 超过重试次数
            self.state = WorkflowState.FAILED
            print(f"\n✗ Development failed after {self.max_iterations} iterations")
            return {
                'status': 'failed',
                'reason': f'测试失败次数超过限制 ({self.max_iterations})',
                'last_result': test_result
            }

        except Exception as e:
            self.state = WorkflowState.FAILED
            print(f"\n✗ Error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'state': self.state.value,
            'iteration': self.iteration,
            'max_iterations': self.max_iterations
        }

    @staticmethod
    def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
        """加载配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)