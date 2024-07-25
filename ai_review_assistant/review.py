from pathlib import Path
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.pydantic_v1 import SecretStr
from langchain_openai import ChatOpenAI


class CodeReviewAssistant:
    def __init__(
        self,
        repo_path: str,
        vendor_name: Literal["openai", "anthropic"],
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        code_depth: int = 0,
    ):
        """
        Initialize the CodeReviewAssistant.

        :param repo_path: Path to the Git repository.
        :param vendor_name: The name of the AI vendor ('openai' or 'anthropic').
        :param model_name: The model name or identifier provided by the vendor.
        :param api_key: The API key for the chosen vendor.
        :param temperature: The temperature setting for the LLM (0.0 to 1.0).
        :param code_depth: The depth of the code structure to include in the prompt.
        """
        self.repo_path = repo_path
        self.vendor_name = vendor_name.lower()
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.code_depth = code_depth

        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> BaseChatModel:
        if self.vendor_name == "openai":
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=SecretStr(self.api_key),
            )
        elif self.vendor_name == "anthropic":
            return ChatAnthropic(
                model_name=self.model_name,
                temperature=self.temperature,
                max_tokens_to_sample=1024,
                timeout=None,
                max_retries=2,
                api_key=SecretStr(self.api_key),
                stop=None,
                base_url="...",
            )
        else:
            raise ValueError(f"Vendor '{self.vendor_name}' is not supported.")

    def review_changes(self, file_path: str, before_code: str, after_code: str) -> str:
        prompt = self.construct_prompt(file_path, before_code, after_code)
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        if isinstance(response.content, str):
            return response.content
        elif isinstance(response.content, list):
            return " ".join(str(item) for item in response.content)
        else:
            return str(response.content)

    def construct_prompt(
        self,
        file_path: str,
        before_code: str,
        after_code: str,
    ) -> str:
        """
        Construct a comprehensive prompt for the LLM.

        :param file_path: The path of the file being reviewed.
        :param before_code: The code before changes.
        :param after_code: The code after changes.
        :return: A string containing the complete prompt.
        """
        project_structure = self.get_project_structure(self.repo_path, self.code_depth)

        return f"""
        You are an AI Code Review Assistant. Please review the following code changes and provide feedback:

        Project Structure:
        {project_structure}

        File being reviewed: {file_path}

        Code before changes:
        ```
        {before_code}
        ```

        Code after changes:
        ```
        {after_code}
        ```

        Please provide a detailed review, considering the following aspects:
        1. Code quality and readability
        2. Potential bugs or errors
        3. Performance implications
        4. Consistency with the overall project structure
        5. Suggestions for improvement

        Your review:
        """

    def get_project_structure(self, path: str, depth: int) -> str:
        """
        Get the project structure up to a certain depth.

        :param path: The starting path.
        :param depth: The depth of the structure to return.
        :return: A string representation of the project structure.
        """
        if depth == 0:
            return ""

        structure = []
        for item in Path(path).iterdir():
            if item.is_dir():
                structure.append(f"[DIR] {item.name}")
                structure.append(self.get_project_structure(str(item), depth - 1))
            else:
                structure.append(f"[FILE] {item.name}")

        return "\n".join(structure)
