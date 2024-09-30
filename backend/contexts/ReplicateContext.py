import json
from tinytune.llmcontext import LLMContext, Model, Message
from typing import Any, override
import replicate

class ReplicateMessage(Message):
    __slots__ = ("Role", "Content", "Type")
    def __init__(self, role: str, content: str, type: str = "message"):
        super().__init__(role, content)
        self.Type = type

    def __str__(self) -> str:
        if self.Role == "user":
            return f"[INST] {self.Content} [/INST]"
        return self.Content

    def ToDict(self):
        return {"role": self.Role, "content": self.Content, "type": self.Type}

class ReplicateContext(LLMContext[ReplicateMessage]):
    def __init__(self, model: str, apiKey: str, promptFile: str | None = None):
        super().__init__(model)
        self.APIKey: str = apiKey
        self.Messages: list[ReplicateMessage] = []
        self.QueuePointer: int = 0
        self.Model = replicate.models.get(model)
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

    def Prompt(self, message: ReplicateMessage):
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
            response = replicate.stream(
                self.Model,
                input={
                    "prompt": " ".join([str(message) for message in messages]),
                },
            )
            content = ""
            for event in response:
                if event is not None:
                    content += str(event)
                    if stream:
                        self.OnGenerate(event)

            if content != "" and content:
                self.Messages.append(ReplicateMessage("assistant", content))
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e
        return ReplicateMessage("assistant", content)