from typing import Optional, Dict, Any, List

from google import genai
from groq import AsyncGroq
from openai import AsyncOpenAI
from langsmith import traceable
from pydantic import BaseModel
from google.genai import types

from config import (
    settings,
    OpenAIConfig,
    GoogleConfig,
    GroqConfig
)

def conditional_decorator(decorator, condition):
    def wrapper(func):
        return decorator(func) if condition else func
    return wrapper

# -------------------- Provider classes -------------------- #
class OpenAIProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self._client:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate_chat_completion(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = OpenAIConfig.GPT_MODEL,
        temperature: float = OpenAIConfig.TEMPERATURE,
        response_format: Optional[Dict] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = settings.LANGCHAIN_PROJECT,

        build_response_callback=None,
    ) -> Dict[str, Any]:
        """
        Uses the lazy-loaded OpenAI client to call chat completions,
        with optional model, temperature, response_format, etc.
        """
       
        @conditional_decorator(traceable(
            run_type="llm",
            name=chat_name or "OpenAI Chat",
            project_name=project_name,
            metadata={"ls_provider": "OpenAI", "ls_model_name": model}
        ), project_name)
        async def inner_openai_call(messages: Optional[List[Dict[str, str]]] = None):
            if response_format:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages or [],
                    response_format=response_format,
                    temperature=temperature
                )
                usage = {
                            "input_tokens": response.usage.prompt_tokens,
                            "output_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                           
                            "input_token_details": {
                                "audio": response.usage.prompt_tokens_details.audio_tokens,
                                "cache_read": response.usage.prompt_tokens_details.cached_tokens,
                                },
                           
                            "output_token_details": {
                                "audio": response.usage.completion_tokens_details.audio_tokens,
                                "reasoning": response.usage.completion_tokens_details.reasoning_tokens
                                }
                        }
                content = response.choices[0].message.content
                return build_response_callback(
                    content=content, usage_metadata=usage, parse_json=True
                )
            else:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages or [],
                    temperature=temperature
                )
                usage = {
                            "input_tokens": response.usage.prompt_tokens,
                            "output_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                           
                            "input_token_details": {
                                "audio": response.usage.prompt_tokens_details.audio_tokens,
                                "cache_read": response.usage.prompt_tokens_details.cached_tokens,
                                },
                           
                            "output_token_details": {
                                "audio": response.usage.completion_tokens_details.audio_tokens,
                                "reasoning": response.usage.completion_tokens_details.reasoning_tokens
                                }
                        }
                content = response.choices[0].message.content
                return build_response_callback(content, usage, parse_json=False)

        return await inner_openai_call(messages)


class GroqProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    @property
    def client(self) -> AsyncGroq:
        if not self._client:
            self._client = AsyncGroq(api_key=self.api_key)
        return self._client

    async def generate_chat_completion(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = GroqConfig.GROQ_MODEL,
        temperature: float = GroqConfig.TEMPERATURE,
        response_format: Optional[Dict] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = settings.LANGCHAIN_PROJECT,
        build_response_callback=None,
    ) -> Dict[str, Any]:
       
        @conditional_decorator(traceable(
            run_type="llm",
            name=chat_name or "Groq Chat",
            project_name=project_name,
            metadata={"ls_provider": "Groq", "ls_model_name": model}
        ), project_name)
        async def inner_groq_call(messages: Optional[List[Dict[str, str]]] = None):
            if response_format:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages or [],
                    response_format=response_format,
                    temperature=temperature
                )
                usage =  {
                            "input_tokens": response.usage.prompt_tokens,
                            "output_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                           
                            "input_token_details": {
                                "audio": response.usage.prompt_tokens_details.audio_tokens,
                                "cache_read": response.usage.prompt_tokens_details.cached_tokens,
                                },
                           
                            "output_token_details": {
                                "audio": response.usage.completion_tokens_details.audio_tokens,
                                "reasoning": response.usage.completion_tokens_details.reasoning_tokens
                                }
                        }
                content = response.choices[0].message.content
                return build_response_callback(
                    content=content, usage_metadata=usage, parse_json=True
                )
            else:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages or [],
                    temperature=temperature
                )
                usage =  {
                            "input_tokens": response.usage.prompt_tokens,
                            "output_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                           
                            "input_token_details": {
                                "audio": response.usage.prompt_tokens_details.audio_tokens,
                                "cache_read": response.usage.prompt_tokens_details.cached_tokens,
                                },
                           
                            "output_token_details": {
                                "audio": response.usage.completion_tokens_details.audio_tokens,
                                "reasoning": response.usage.completion_tokens_details.reasoning_tokens
                                }
                        }
                content = response.choices[0].message.content
                return build_response_callback(content, usage, parse_json=False)

        return await inner_groq_call(messages)


class GeminiProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """
        We'll configure google.generativeai on first use and store
        the module-level handle in self._client.
        """
        if not self._client:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def generate_chat_completion(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = GoogleConfig.GEMINI_MODEL,
        temperature: float = GoogleConfig.TEMPERATURE,
        top_p: float = GoogleConfig.TOP_P,
        top_k: int = GoogleConfig.TOP_K,
        max_tokens: int = GoogleConfig.MAX_TOKENS,
        response_format: Optional[Dict] = None,
        response_schema: Optional[BaseModel] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = settings.LANGCHAIN_PROJECT,
        build_response_callback=None,
    ) -> Dict[str, Any]:
        
        @conditional_decorator(traceable(
            run_type="llm",
            name=chat_name or "Gemini Chat",
            project_name=project_name,
            metadata={"ls_provider": "Google", "ls_model_name": model}
        ), project_name)
        async def inner_gemini_call(messages: Optional[List[Dict[str, str]]] = None):
            system_instructions = (
                messages[0]["content"] if messages[0]["role"] == "system" else "You are a helpful assistant."
            )

            # Build conversation history
            conversation_history = []
            if messages:
                for msg in messages:
                    if msg["role"]=="system":
                        pass
                    else:
                        role = "model" if msg["role"] == "assistant" else "user"
    
                        conversation_history.append(types.Content(role=role, 
                                                                  parts=[types.Part.from_text(text=msg["content"])]
                                                              ))
            if response_format:
                if response_schema:
                    generation_config = {
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "max_output_tokens": max_tokens,
                        "system_instruction":system_instructions,
                        "response_mime_type": "application/json",
                        "response_schema": response_schema,
                        
                    }
        
                else:
                    generation_config = {
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "max_output_tokens": max_tokens,
                        "system_instruction":system_instructions,
                        "response_mime_type": "application/json",
                    }
            else:
                generation_config = {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "max_output_tokens": max_tokens,
                    "system_instruction":system_instructions,
                }
        
            response = self.client.models.generate_content(
                model=model,
                config=generation_config,
                contents=conversation_history,
            )
           
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }
            content = response.text
 

            parse_json = bool(response_format)

            return build_response_callback(
                content=content,
                usage_metadata=usage,
                parse_json=parse_json
            )

        return await inner_gemini_call(messages)


