import os
import json
from typing import Any

from yt import YouTubeDataAPI
from contexts.GroqContext import WebGroqContext, WebGroqMessage
from tinytune.prompt import prompt_job
from tinytune.pipeline import Pipeline

class YTChat:
    def __init__(self, apiKey: str, ytKey: str):
        self.LLM = WebGroqContext("llama-3.1-70b-versatile", apiKey=apiKey)
        self.YTAgent = WebGroqContext("llama-3.1-70b-versatile", apiKey=apiKey)
        
        self.YT = YouTubeDataAPI(ytKey)
        
        self.Functions = self.YT.get_function_map()

    def Prompt(self, inp: str):
        response: str = ""

        def OnGenerate(x):
            nonlocal response
            response += x
            return response 

        self.LLM.OnGenerate = lambda x: None 

        @prompt_job(id="Formatter", context=self.LLM)
        def FormatJob(id: str, context: WebGroqContext, prevResult: Any):
            nonlocal response
            print("Formatting:", prevResult)
            response = ""
            self.LLM.OnGenerate = OnGenerate
            return context.Prompt(WebGroqMessage("user", prevResult)).Run(stream=True).Messages[-1].Content   

        @prompt_job(id="YTAgentPrompt", context=self.YTAgent)
        def PromptJob(id: str, context: WebGroqContext, prevResult: Any):
            return context.Prompt(WebGroqMessage("user", inp)).Run(stream=True).Messages[-1].Content
      
        @prompt_job(id="Execute", context=self.YTAgent)
        def Execute(id: str, context: WebGroqContext, prevResult: Any):
            print("Executing: ", prevResult)
            try:
                responses = {}
                for result in prevResult.split("\n"):
                    func: dict = json.loads(str(result))
                    
                    resp = self.YT.call_method(func)
                    
                    print("Call Response:", resp)
                    
                    responses[func['function']] = resp

                context.Messages.append(WebGroqMessage("assistant", json.dumps(responses)))

            except Exception as e:
                context.Messages.append(WebGroqMessage("assistant", json.dumps({"error": str(e)})))
            return context.Messages[-1].Content

        ChatPipeline = Pipeline(None)
        
        ChatPipeline.AddJob(PromptJob).AddJob(Execute).AddJob(FormatJob)
        ChatPipeline.Run(stream=True)

        return ChatPipeline.Results["Formatter"][-1]

    def Setup(self):
        self.Functions = self.YT.get_function_map()
        
        self.LLM.Prompt(WebGroqMessage("user", """
            You are a JSON formatter for YouTube API responses. You take in structured YouTube data and format it according to the following schema:

            {
                "response": {
                    "success": boolean,
                    "data": {
                        "videos": [
                            {
                                "id": string,
                                "title": string,
                                "description": string,
                                "publishedAt": string (ISO 8601 date),
                                "thumbnailUrl": string (URL),
                                "videoUrl": string (URL),
                                "viewCount": integer,
                                "likeCount": integer,
                                "commentCount": integer
                            }
                        ],
                        "channels": [
                            {
                                "id": string,
                                "title": string,
                                "description": string,
                                "subscriberCount": integer,
                                "videoCount": integer,
                                "viewCount": integer
                            }
                        ],
                        "playlists": [
                            {
                                "id": string,
                                "title": string,
                                "description": string,
                                "itemCount": integer
                            }
                        ],
                        "misc": {
                            // Additional data that doesn't fit into other categories
                        }
                    },
                    "misc": {
                        // Additional data that doesn't fit into other categories or misc
                    },
                    "error": {
                        "code": integer,
                        "message": string
                    }
                }
            }

            Make sure you generate plain JSON text and nothing else, no backticks or extra text.
            Your task is to take the structured YouTube API responses and format them according to this schema. 
            Populate the relevant fields based on the data provided. Use the 'misc' object for any additional information that doesn't fit into the predefined categories. 
            Ensure all data is properly formatted and typed according to the schema.
        """))

        self.YTAgent.Prompt(WebGroqMessage("user", f"""
                        You are an AI assistant designed to interact with YouTube. You have access to the following YouTube-related functions:

                        Use the following functions:
                        {json.dumps({key: {"name": key, "doc": self.Functions[key][0].__doc__} for key in self.Functions})}

                        If you choose to call a function to interact with YouTube, ONLY reply in the following format with no prefix or suffix:

                        {{
                            "function": "function_name",
                            "params": {{
                                "param": "value"
                            }}
                        }}

                        Reminder:
                        - Function calls MUST follow the specified format.
                        - Required parameters MUST be specified
                        - Make sure to call the correct function for the task you are given
                        - Make sure to call the correct parameters for the function you are calling
                        - Each parameter name should match the parameter name specified in the function
                        - Only call one YouTube-related function at a time
                        - Put the entire function call reply on one line
                        - If there is no YouTube-related function call available, answer the question like normal with your current knowledge about YouTube and do not tell the user about function calls
                        - Never make responses bigger than one paragraph if you don't have a YouTube-related function to call.
                        - Make sure the params of the function call you return are the same as the ones specified for the YouTube-related functions.
                        - Always respond in JSON format, even for errors.
                        """))
