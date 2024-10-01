import os
import json
from typing import Any

from yt import YouTubeDataAPI

from contexts.GroqContext import WebGroqContext, WebGroqMessage

from tinytune.prompt import prompt_job
from tinytune.pipeline import Pipeline

class YTChat:
    def __init__(self, apiKey: str, ytKey: str):
        self.LLM = WebGroqContext("llama-3.1-70b-versatile", apiKey)
        self.YTAgent = WebGroqContext("llama-3.1-70b-versatile", apiKey)

        self.YT = YouTubeDataAPI(ytKey)

        self.Functions = self.YT.get_function_map()

    def Prompt(self, inp: str):
        response: str = ""

        print("Input: ", inp)

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
            return (
                context.Prompt(WebGroqMessage("user", prevResult))
                .Run(stream=True)
                .Messages[-1]
                .Content
            )

        @prompt_job(id="YTAgentPrompt", context=self.YTAgent)
        def PromptJob(id: str, context: WebGroqContext, prevResult: Any):
            return (
                context.Prompt(WebGroqMessage("user", inp))
                .Run(stream=True)
                .Messages[-1]
                .Content
            )

        @prompt_job(id="Execute", context=self.YTAgent)
        def Execute(id: str, context: WebGroqContext, prevResult: Any):
            prevResult = prevResult.strip()

            print("Executing: ", prevResult)

            try:
                responses = {}

                for result in prevResult.split("\n"):
                    func: dict = json.loads(str(result))

                    if not "function" in func:
                        if "general" not in responses:
                            responses["general"] = []

                        responses["general"].append(json.dumps(func))

                        continue

                    resp = self.YT.call_method(func)

                    print("Call Response:", resp)

                    responses[func["function"]] = resp

                context.Messages.append(
                    WebGroqMessage("assistant", json.dumps(responses))
                )

            except Exception as e:
                context.Messages.append(
                    WebGroqMessage("assistant", json.dumps({"error": str(e)}))
                )

            return context.Messages[-1].Content

        ChatPipeline = Pipeline(None)

        ChatPipeline.AddJob(PromptJob).AddJob(Execute).AddJob(FormatJob)
        ChatPipeline.Run(stream=True)

        return ChatPipeline.Results["Formatter"][-1]

    def Setup(self):
        self.Functions = self.YT.get_function_map()

        self.LLM.Prompt(
            WebGroqMessage(
                "user",
                """
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
                                "publishedAt": string,
                                "thumbnailUrl": string,
                                "videoUrl": string,
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
                },
                "remarks": "Put an explanation of the response here. Consider the entire response, and mention all the info. Add formatting where necessary. If the response contains natural language, just include it as is without your intervention. for every general and follow up response, only put the message of that response here, do not brief it. If the response contains details and metrics, make sure to mention them all." 
           }

            You have the ability to repsond with specific chunks of the JSON response, based on the user's query. 
            Only include the properties that have some sort of data, and ignore the rest.
            Make sure you generate plain JSON text and nothing else, no backticks or extra text.
            Your task is to take the structured YouTube API responses and format them according to this schema. 
            Populate the relevant fields based on the data provided. Use the 'misc' object for any additional information that doesn't fit into the predefined categories. 
            Ensure all data is properly formatted and typed according to the schema.
        """,
            )
        )

        self.YTAgent.Prompt(
            WebGroqMessage(
                "user",
                f"""
                    You are an AI assistant designed to interact with YouTube. You have access to the following YouTube-related functions:

                    Use the following functions:
                    {json.dumps({key: {"name": key, "doc": self.Functions[key][0].__doc__} for key in self.Functions})}

                    If you choose to call a function to interact with YouTube, ONLY reply in the following format with no prefix or suffix:
                    {{"function": "function_name", "params": {{"param": "value"}}}}

                    For general responses or errors, use the following format:

                    {{"response": {{"message": "Your response here"}}}}

                    or

                    {{"error": {{"code": "error_code", "message": "error_message"}}}}

                    Reminder:
                    - ALWAYS respond with ONE LINE JSON ONLY, no multi-line formatting allowed
                    - STRICTLY check if the parameters match the function parameters exactly, including the type and case sensitivity
                    - NEVER include parameters that are not explicitly specified in the function parameters
                    - ALWAYS respond in JSON format for everything, including function calls, general responses, and errors, without exception
                    - Function calls MUST follow the specified format: {{"function": "function_name", "params": {{"param": "value"}}}}
                    - Every JSON response MUST be on a single line, with new lines only for new responses or function calls
                    - ALL required parameters MUST be specified, no omissions allowed
                    - ALWAYS call the correct function for the given task, double-check before responding
                    - ALWAYS use the correct parameters for the function you are calling, verify against the function definition
                    - ENSURE each parameter name matches exactly the parameter name specified in the function, character for character
                    - SEPARATE multiple function calls by new lines, never combine them
                    - PLACE each function call response on a separate line, never combine responses
                    - If NO YouTube-related function call is available, answer the question using your current knowledge about YouTube and NEVER mention function calls to the user
                    - LIMIT responses to one paragraph maximum if you don't have a YouTube-related function to call
                    - VERIFY that the params of the function call you return are EXACTLY the same as those specified for the YouTube-related functions, no variations allowed
                    - ABSOLUTELY NO backticks (`) or any other code formatting should be used in your responses
                    - DO NOT include any explanatory text or comments outside of the JSON structure
                    - ONLY plain, unformatted JSON should be returned, with no additional text or formatting of any kind
                    """,
            )
        )
