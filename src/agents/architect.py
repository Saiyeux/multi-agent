"""Architect Agent - Requirements analysis and architecture design (Refactored)"""

from typing import Dict, Any, Optional, Callable
from .base_agent import BaseAgent
from ..llm.prompts import ARCHITECT_SYSTEM_PROMPT


class ArchitectAgent(BaseAgent):
    """产品架构师 - 需求分析与架构设计

    支持的 actions:
    - analyze_requirement: 分析需求
    - design_architecture: 设计架构
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("architect", config, ARCHITECT_SYSTEM_PROMPT)

    def _get_action_handler(self, action: str) -> Optional[Callable]:
        """获取动作处理器"""
        handlers = {
            'analyze_requirement': self._handle_analyze_requirement,
            'design_architecture': self._handle_design_architecture
        }
        return handlers.get(action)

    async def _handle_analyze_requirement(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理需求分析"""
        user_requirement = input_data.get('requirement')
        if not user_requirement:
            raise ValueError("Missing 'requirement' in input_data")

        requirement_doc = await self._analyze_requirement(user_requirement)
        return {'document': requirement_doc}

    async def _handle_design_architecture(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理架构设计"""
        requirement_doc = input_data.get('requirement_doc')
        if not requirement_doc:
            raise ValueError("Missing 'requirement_doc' in input_data")

        architecture_doc = await self._design_architecture(requirement_doc)
        return {'document': architecture_doc}

    async def _analyze_requirement(self, user_requirement: str) -> str:
        """分析用户需求，生成需求文档"""
        prompt = f"""
请分析以下用户需求，输出结构化的需求文档：

用户需求：
{user_requirement}

请按以下格式输出需求文档：

# 需求分析

## 1. 核心功能
- 列出主要功能点

## 2. 功能优先级
- P0（必须有）: ...
- P1（重要）: ...
- P2（可选）: ...

## 3. 非功能需求
- 性能要求
- 可用性要求
- 兼容性要求

## 4. 用户故事
作为[角色]，我希望[功能]，以便[价值]

## 5. 验收标准
- 列出可测试的验收标准
"""
        return await self.chat(prompt)

    async def _design_architecture(self, requirement_doc: str) -> str:
        """根据需求文档设计系统架构"""
        prompt = f"""
基于以下需求文档，设计系统架构：

{requirement_doc}

请按以下格式输出架构设计文档：

# 系统架构设计

## 1. 技术选型
- 编程语言：[语言] - [选择理由]
- 框架/库：[框架名] - [选择理由]
- 依赖项：列出主要依赖

## 2. 模块划分
```
项目结构：
module_name/
├── file1.py    # 功能说明
├── file2.py    # 功能说明
└── ...
```

## 3. 核心模块说明
### 模块1：[名称]
- 职责：...
- 接口：...
- 依赖：...

### 模块2：[名称]
- 职责：...
- 接口：...
- 依赖：...

## 4. 数据流程
描述数据如何在模块间流动

## 5. 关键设计决策
列出重要的设计决策及理由
"""
        return await self.chat(prompt)