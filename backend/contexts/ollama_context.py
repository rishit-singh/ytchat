import json
from tinytune.llmcontext import LLMContext, Model, Message
from typing import Any, override
import openai

class OllamaMessage(Message):
    __slots__ = ("Role", "Content", "Type")

    def __init__(self, role: str, content: str, type: str = "message"):
        super().__init__(role, content)
        self.Type = type

class OllamaContext(LLMContext[OllamaMessage]):
    def __init__(self, baseUrl: str, model: str, promptFile: str | None = None):
        super().__init__(Model("openai", model))

        self.Messages: list[OllamaMessage] = []
        self.QueuePointer: int = 0
        self.Client = openai.OpenAI(base_url=baseUrl, api_key="ollama")

        self.PromptFile = promptFile

    def LoadMessages(self, promptFile: str = "prompts.json") -> None:
        self.PromptFile = promptFile

        with open(promptFile, "r") as fp:
            self.Messages = json.load(fp)

    def Save(self, promptFile: str = "prompts.json") -> Any:
        try:
            promptFile = promptFile if self.PromptFile is None else self.PromptFile

            with open(promptFile, "w") as fp:
                json.dump([message.ToDict() for message in self.Messages], fp, indent=2)

        except:
            print("An error occurred in saving messages.")
            return self

        return self

    def Prompt(self, message: OllamaMessage):
        self.MessageQueue.append(message)
        return self

    @override
    def OnRun(self, *args, **kwargs):
        messages = [message.ToDict() for message in self.Messages] + [
            self.MessageQueue[self.QueuePointer].ToDict()
        ]

        stream: bool | None = kwargs.get("stream")

        if stream is None:
            stream = False

        try:
            response = self.Client.chat.completions.create(
                model=self.Model.Name,
                messages=messages,
                temperature=0,
                stream=stream,
            )

            content = ""

            if stream:
                for chunk in response:
                    chunk_content = chunk.choices[0].delta.content
                    if chunk_content is not None:
                        content += chunk_content
                        self.OnGenerate(chunk_content)
            else:
                content = response.choices[0].message.content
                self.OnGenerate(content)

            if content != "" and content:
                self.Messages.append(OllamaMessage("assistant", content))

        except Exception as e:
            print(f"An error occurred: {e}")
            raise e

        return OllamaMessage("assistant", content)

class O1Context(LLMContext[OllamaMessage]):
    def __init__(self, model: str, apiKey: str, promptFile: str | None = None):
        super().__init__(Model("openai", model))

        self.APIKey: str = apiKey
        self.Messages: list[OllamaMessage] = []
        self.QueuePointer: int = 0

        openai.api_key = self.APIKey

        self.PromptFile = promptFile

    def LoadMessages(self, promptFile: str = "prompts.json") -> None:
        self.PromptFile = promptFile

        with open(promptFile, "r") as fp:
            self.Messages = json.load(fp)

    def Save(self, promptFile: str = "prompts.json") -> Any:
        try:
            promptFile = promptFile if self.PromptFile is None else self.PromptFile

            with open(promptFile, "w") as fp:
                json.dump([message.ToDict() for message in self.Messages], fp, indent=2)

        except:
            print("An error occurred in saving messages.")
            return self

        return self

    def Prompt(self, message: OllamaMessage):
        self.MessageQueue.append(message)
        return self

    @override
    def OnRun(self, *args, **kwargs):
        messages = [message.ToDict() for message in self.Messages] + [
            self.MessageQueue[self.QueuePointer].ToDict()
        ]

        stream: bool | None = kwargs.get("stream")

        if stream is None:
            stream = False

        try:
            response = openai.chat.completions.create(
                model=self.Model.Name,
                messages=messages,
                temperature=0,
                stream=stream,
            )

            content = ""

            if stream:
                for chunk in response:
                    chunk_content = chunk.choices[0].delta.content
                    if chunk_content is not None:
                        content += chunk_content
                        self.OnGenerate(chunk_content)
            else:
                content = response.choices[0].message.content
                self.OnGenerate(content)

            if content != "" and content:
                self.Messages.append(OllamaMessage("assistant", content))

        except Exception as e:
            print(f"An error occurred: {e}")
            raise e

        return OllamaMessage("assistant", content)
