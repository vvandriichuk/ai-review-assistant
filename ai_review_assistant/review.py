from pathlib import Path
from typing import Literal

import tiktoken
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
        temperature: float = 0.0,
        code_depth: int = 0,
        program_language: list[str] | None = None,
        result_output_language: str = "English",
        batch_size: int = 100000,
    ):
        """
        Initialize the CodeReviewAssistant.

        :param repo_path: Path to the Git repository.
        :param vendor_name: The name of the AI vendor ('openai' or 'anthropic').
        :param model_name: The model name or identifier provided by the vendor.
        :param api_key: The API key for the chosen vendor.
        :param temperature: The temperature setting for the LLM (0.0 to 1.0).
        :param code_depth: The depth of the code structure to include in the prompt.
        :param program_language: List of programming languages of the code being reviewed.
        :param result_output_language: The language for the output review.
        :param batch_size: The maximum number of tokens to process in a single batch when reviewing large files.
                       Defaults to 100000. Larger values may improve performance but increase memory usage.
        """
        self.repo_path = repo_path
        self.vendor_name = vendor_name.lower()
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.code_depth = code_depth
        self.program_language = program_language
        self.result_output_language = result_output_language
        self.batch_size = batch_size

        self.llm = self._initialize_llm()

        if self.vendor_name == "openai":
            self.tokenizer = tiktoken.encoding_for_model(self.model_name)
        elif self.vendor_name == "anthropic":
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            raise ValueError(f"Vendor '{self.vendor_name}' is not supported.")

    def _initialize_llm(self) -> BaseChatModel:
        if self.vendor_name == "openai":
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                timeout=None,
                max_retries=2,
                api_key=SecretStr(self.api_key),
            )
        elif self.vendor_name == "anthropic":
            return ChatAnthropic(
                model_name=self.model_name,
                temperature=self.temperature,
                timeout=None,
                max_retries=2,
                api_key=SecretStr(self.api_key),
                stop=None,
                base_url=None,
            )
        else:
            raise ValueError(f"Vendor '{self.vendor_name}' is not supported.")

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the given text.

        :param text: The text to count tokens for.
        :return: The number of tokens in the text.
        """
        return len(self.tokenizer.encode(text))

    def review_changes(self, file_path: str, before_code: str, after_code: str) -> str:
        """
        Review the changes made to a file.

        :param file_path: The path of the file being reviewed.
        :param before_code: The code before changes.
        :param after_code: The code after changes.
        :return: A string containing the review of the changes.
        """
        project_structure = self.get_project_structure(self.repo_path, self.code_depth)
        base_prompt = self.construct_base_prompt(file_path, project_structure)

        before_tokens = self.count_tokens(before_code)
        after_tokens = self.count_tokens(after_code)

        if before_tokens + after_tokens <= self.batch_size:
            full_prompt = self.construct_prompt(file_path, before_code, after_code)
            return self.get_review(full_prompt)

        # If the code is too large, split it into parts
        reviews = []
        for i in range(0, len(before_code), self.batch_size):
            before_batch = before_code[i : i + self.batch_size]
            after_batch = after_code[i : i + self.batch_size]
            batch_prompt = (
                f"{base_prompt}\n\n"
                f"Code before changes (part {i // self.batch_size + 1}):\n"
                f"```{self.program_language}\n{before_batch}\n```\n\n"
                f"Code after changes (part {i // self.batch_size + 1}):\n"
                f"```{self.program_language}\n{after_batch}\n```\n\n"
                f"Please provide your review for this part in {self.result_output_language}."
            )
            reviews.append(self.get_review(batch_prompt))

        return "\n\n".join(reviews)

    def get_review(self, prompt: str) -> str:
        """
        Get a review from the Language Model based on the given prompt.

        :param prompt: The prompt to send to the Language Model.
        :return: The review generated by the Language Model.
        """
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        if isinstance(response.content, str):
            return response.content
        elif isinstance(response.content, list):
            return " ".join(str(item) for item in response.content)
        else:
            return str(response.content)

    def construct_base_prompt(self, file_path: str, project_structure: str) -> str:
        """
        Construct the base prompt for the code review.

        :param file_path: The path of the file being reviewed.
        :param project_structure: The structure of the project.
        :return: The base prompt as a string.
        """
        return f"""
        You are an AI Code Review Assistant and you know {self.program_language} as an expert. You are a {self.program_language} senior developer. Please review the following code changes and provide feedback:

        Project Structure:
        {project_structure}

        File being reviewed: {file_path}

        Please provide a detailed review, considering the following aspects:
        1. Code quality and readability
        2. Potential bugs or errors
        3. Performance implications
        4. Consistency with the overall project structure
        5. Suggestions for improvement
        6. Best practices specific to {self.program_language}

        Please provide your review in {self.result_output_language}.
        """

    def construct_prompt(
        self,
        file_path: str,
        before_code: str,
        after_code: str,
    ) -> str:
        """
        Construct the full prompt for the code review.

        :param file_path: The path of the file being reviewed.
        :param before_code: The code before changes.
        :param after_code: The code after changes.
        :return: The full prompt as a string.
        """
        base_prompt = self.construct_base_prompt(
            file_path,
            self.get_project_structure(self.repo_path, self.code_depth),
        )
        return f"""
        {base_prompt}

        Code before changes:
        ```{self.program_language}
        {before_code}
        ```

        Code after changes:
        ```{self.program_language}
        {after_code}
        ```

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

    def __repr__(self) -> str:
        """
        Return a string representation of the CodeReviewAssistant.

        :return: A string representation of the object.
        """
        return (
            f"CodeReviewAssistant(repo_path='{self.repo_path}', "
            f"vendor_name='{self.vendor_name}', "
            f"model_name='{self.model_name}', "
            f"temperature={self.temperature}, "
            f"code_depth={self.code_depth}, "
            f"program_language={self.program_language}, "
            f"result_output_language='{self.result_output_language}')"
        )

    def __str__(self) -> str:
        """
        Return a human-readable string representation of the CodeReviewAssistant.

        :return: A human-readable string representation of the object.
        """
        languages = ", ".join(self.program_language or ["Unknown"])
        return (
            f"Code Review Assistant for {languages} using {self.vendor_name.capitalize()} "
            f"with model {self.model_name} (output in {self.result_output_language})"
        )
