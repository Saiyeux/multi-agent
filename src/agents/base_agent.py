"""Base Agent - Refactored to implement IAgent interface"""

from abc import abstractmethod
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import ollama

from ..core.interfaces import IAgent


class BaseAgent(IAgent):
    """重构后的 BaseAgent - 实现 IAgent 接口

    遵循开闭原则：
    - 子类通过实现 _get_action_handler() 来扩展功能
    - 核心 chat() 和 inject_instruction() 逻辑不需要修改
    """

    def __init__(self, agent_type: str, config: Dict[str, Any], system_prompt: str):
        """初始化 Agent

        Args:
            agent_type: Agent 类型 (architect/developer/qa)
            config: 配置字典，包含 host, model, temperature
            system_prompt: 系统提示词
        """
        self._agent_type = agent_type
        self.config = config
        self.system_prompt = system_prompt
        self.client = ollama.Client(host=config['host'])
        self.dynamic_instructions: List[Dict[str, str]] = []
        self.conversation_history: List[Dict[str, str]] = []

    @property
    def agent_type(self) -> str:
        """Agent 类型"""
        return self._agent_type

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务 - 根据 action 分发

        Args:
            input_data: 必须包含 'action' 字段

        Returns:
            处理结果

        Raises:
            ValueError: 如果 action 未知
        """
        action = input_data.get('action')
        if not action:
            raise ValueError("Missing 'action' in input_data")

        # 获取动作处理器（子类实现）
        handler = self._get_action_handler(action)
        if not handler:
            raise ValueError(f"Unknown action: {action} for {self.agent_type}")

        # 执行处理器
        return await handler(input_data)

    @abstractmethod
    def _get_action_handler(self, action: str) -> Optional[Callable]:
        """获取动作处理器（子类必须实现）

        Args:
            action: 动作名称

        Returns:
            处理器函数或 None
        """
        pass

    async def inject_instruction(self, instruction: str):
        """注入新指令（用于人工介入）

        Args:
            instruction: 指令内容
        """
        self.dynamic_instructions.append({
            'instruction': instruction,
            'timestamp': datetime.now().isoformat()
        })

    async def chat(self, prompt: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """与 LLM 对话

        Args:
            prompt: 用户提示
            context: 对话上下文（可选）

        Returns:
            LLM 的响应内容
        """
        # 构建消息列表
        messages = context or []

        # 如果没有提供上下文，使用历史记录
        if not messages and self.conversation_history:
            messages = self.conversation_history.copy()

        # 添加系统提示（如果还没有）
        if not messages or messages[0].get('role') != 'system':
            messages.insert(0, {'role': 'system', 'content': self.system_prompt})

        # 构建完整 prompt（包含动态指令）
        full_prompt = prompt
        if self.dynamic_instructions:
            # 只使用最近3条指令
            recent_instructions = self.dynamic_instructions[-3:]
            instructions_text = "\n\n".join([
                f"[主管最新指示 {i+1}]: {inst['instruction']}"
                for i, inst in enumerate(recent_instructions)
            ])
            full_prompt = f"{instructions_text}\n\n{prompt}"

        # 添加用户消息
        messages.append({'role': 'user', 'content': full_prompt})

        try:
            # 调用 Ollama API
            response = self.client.chat(
                model=self.config['model'],
                messages=messages,
                options={'temperature': self.config['temperature']}
            )

            assistant_message = response['message']['content']

            # 更新对话历史
            self.conversation_history.append({'role': 'user', 'content': prompt})
            self.conversation_history.append({'role': 'assistant', 'content': assistant_message})

            return assistant_message

        except Exception as e:
            raise RuntimeError(f"Failed to chat with {self.agent_type}: {str(e)}")

    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []

    def clear_instructions(self):
        """清空动态指令"""
        self.dynamic_instructions = []

    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            'agent_type': self.agent_type,
            'model': self.config['model'],
            'host': self.config['host'],
            'temperature': self.config['temperature'],
            'instructions_count': len(self.dynamic_instructions),
            'conversation_turns': len(self.conversation_history) // 2
        }