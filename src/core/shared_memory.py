"""Shared workspace for agent collaboration"""

from pathlib import Path
from typing import Any, Dict, Optional


class SharedMemory:
    """Agent间共享的工作区"""

    def __init__(self, workspace: str = "./workspace"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(exist_ok=True)

        # 创建子目录
        self.categories = ['requirements', 'design', 'code', 'tests', 'reports', 'releases']
        for subdir in self.categories:
            (self.workspace / subdir).mkdir(exist_ok=True)

    def save(self, category: str, filename: str, content: str) -> str:
        """保存文件到工作区

        Args:
            category: 文件类别 (requirements/design/code/tests/reports/releases)
            filename: 文件名（可以包含子目录，如 "module/file.py"）
            content: 文件内容

        Returns:
            文件的完整路径
        """
        if category not in self.categories:
            raise ValueError(f"Invalid category: {category}. Must be one of {self.categories}")

        filepath = self.workspace / category / filename

        # 确保父目录存在（如果文件名包含子目录）
        filepath.parent.mkdir(parents=True, exist_ok=True)

        filepath.write_text(content, encoding='utf-8')
        return str(filepath)

    def load(self, category: str, filename: str) -> str:
        """从工作区加载文件

        Args:
            category: 文件类别
            filename: 文件名

        Returns:
            文件内容
        """
        filepath = self.workspace / category / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        return filepath.read_text(encoding='utf-8')

    def get_context(self) -> Dict[str, Dict[str, str]]:
        """获取项目完整上下文

        Returns:
            字典结构: {category: {filename: content}}
        """
        context = {}
        for category in self.categories:
            category_path = self.workspace / category
            # 递归查找所有文件（包括子目录）
            files = list(category_path.rglob('*'))
            context[category] = {
                str(f.relative_to(category_path)): f.read_text(encoding='utf-8')
                for f in files
                if f.is_file()
            }
        return context

    def list_files(self, category: str) -> list[str]:
        """列出某个类别下的所有文件（包括子目录）

        Args:
            category: 文件类别

        Returns:
            文件名列表（相对路径）
        """
        category_path = self.workspace / category
        # 递归查找所有文件
        return [str(f.relative_to(category_path)) for f in category_path.rglob('*') if f.is_file()]

    def clear_category(self, category: str):
        """清空某个类别下的所有文件和子目录

        Args:
            category: 文件类别
        """
        import shutil
        category_path = self.workspace / category
        for item in category_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)