"""Architect Agent - Requirements analysis and architecture design"""

from typing import Dict, Any
from .base_agent import BaseAgent
from ..llm.prompts import ARCHITECT_SYSTEM_PROMPT


class ArchitectAgent(BaseAgent):
    """产品架构师 - 需求分析与架构设计"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("Architect", config, ARCHITECT_SYSTEM_PROMPT)

    async def analyze_requirement(self, user_requirement: str) -> str:
        """分析用户需求，生成需求文档

        Args:
            user_requirement: 用户原始需求

        Returns:
            需求分析文档（Markdown格式）
        """
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

    async def design_architecture(self, requirement_doc: str) -> str:
        """根据需求文档设计系统架构

        Args:
            requirement_doc: 需求文档

        Returns:
            架构设计文档（Markdown格式）
        """
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

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理架构设计任务

        Args:
            input_data: {'requirement': str}

        Returns:
            {'requirement_doc': str, 'architecture_doc': str}
        """
        requirement = input_data.get('requirement')
        if not requirement:
            raise ValueError("Missing 'requirement' in input_data")

        # 第一步：需求分析
        requirement_doc = await self.analyze_requirement(requirement)

        # 第二步：架构设计
        architecture_doc = await self.design_architecture(requirement_doc)

        return {
            'requirement_doc': requirement_doc,
            'architecture_doc': architecture_doc
        }