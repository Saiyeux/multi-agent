"""Base agent class for all agents"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import ollama


class BaseAgent(ABC):
    """所有Agent的基类"""

    def __init__(self, name: str, config: Dict[str, Any], system_prompt: str):
        """初始化Agent

        Args:
            name: Agent名称
            config: 配置字典，包含host, model, temperature
            system_prompt: 系统提示词
        """
        self.name = name
        self.host = config['host']
        self.model = config['model']
        self.temperature = config['temperature']
        self.system_prompt = system_prompt
        self.client = ollama.Client(host=self.host)
        self.conversation_history: List[Dict[str, str]] = []

    async def chat(self, prompt: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """与LLM对话

        Args:
            prompt: 用户提示
            context: 对话上下文（可选）

        Returns:
            LLM的响应内容
        """
        # 构建消息列表
        messages = context or []

        # 如果没有提供上下文，使用历史记录
        if not messages and self.conversation_history:
            messages = self.conversation_history.copy()

        # 添加系统提示（如果还没有）
        if not messages or messages[0].get('role') != 'system':
            messages.insert(0, {'role': 'system', 'content': self.system_prompt})

        # 添加用户消息
        messages.append({'role': 'user', 'content': prompt})

        try:
            # 调用Ollama API
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={'temperature': self.temperature}
            )

            assistant_message = response['message']['content']

            # 更新对话历史
            self.conversation_history.append({'role': 'user', 'content': prompt})
            self.conversation_history.append({'role': 'assistant', 'content': assistant_message})

            return assistant_message

        except Exception as e:
            raise RuntimeError(f"Failed to chat with {self.name}: {str(e)}")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务（子类实现）

        Args:
            input_data: 输入数据

        Returns:
            处理结果
        """
        pass

    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []

    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            'name': self.name,
            'host': self.host,
            'model': self.model,
            'temperature': self.temperature
        }