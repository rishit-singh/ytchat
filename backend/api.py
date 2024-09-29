from fastapi import FastAPI, Body
from pydantic import BaseModel
from ytchat import YTChat
from dotenv import load_dotenv
import os
import json
import uuid

load_dotenv()

app = FastAPI()
chats = {}

class PromptInput(BaseModel):
    input: str
    chat_id: str = None

@app.post("/prompt")
async def prompt(prompt_input: PromptInput):
    if prompt_input.chat_id not in chats:
        if prompt_input.chat_id is None:
            prompt_input.chat_id = str(uuid.uuid4())
        chats[prompt_input.chat_id] = YTChat(os.getenv("GROQ_API_KEY"), os.getenv("YT_KEY"))
        chats[prompt_input.chat_id].Setup()

    yt_chat = chats[prompt_input.chat_id]
    response = yt_chat.Prompt(prompt_input.input)

    print("Response:", response)
    return {"response": json.loads(response), "chat_id": prompt_input.chat_id}

# Example curl command:
# curl -X POST "http://localhost:8000/prompt" -H "Content-Type: application/json" -d '{"input": "Search for videos about cats"}'
