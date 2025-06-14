import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from core.config import (
    settings,
    OpenAIConfig,
    GoogleConfig,
    GroqConfig
)

from services.llm.providers import OpenAIProvider, GroqProvider, GeminiProvider


class WrappedAIClient:
    """
    Orchestrates calls to the four providers above.
    Retains the same optional arguments from your original code
    but delegates the actual calls to provider classes.
    """
    def __init__(self, api_key: Optional[str] = None, chat_name: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.chat_name = chat_name or "One Click Optimizer"

        # Provider objects (lazy loading at each provider-level)
        self.openai_provider = OpenAIProvider(api_key=self.api_key)
        self.groq_provider = GroqProvider(api_key=settings.GROQ_API_KEY)
        self.gemini_provider = GeminiProvider(api_key=settings.GOOGLE_API_KEY)

    def _build_chat_response(
        self,
        content: str,
        usage_metadata: Dict[str, int],
        parse_json: bool = False
    ) -> Dict[str, Any]:
        """
        Central helper that standardizes the shape of the returned response.
        If parse_json=True, it attempts to load JSON either via json.loads
        """
        if parse_json:
            content = json.loads(content)
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": content
                    }
                }
            ],
            "usage_metadata": usage_metadata,
        }

    async def generate_chat_completion(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> str | Dict:
        """
        Example aggregator method that tries Gemini first, 
        then falls back to OpenAI if there's an exception.
        """
        # Use default config if user doesn't pass a temperature

        try:
            #################################
            # UNCOMMENT BEFORE MOVING TO PROD
            #################################
            
            # chosen_temp = temperature if temperature is not None else GoogleConfig.TEMPERATURE
            # response = await self.generate_chat_completion_openai(
            #     messages=messages,
            #     model=GoogleConfig.GEMINI_MODEL,
            #     temperature=chosen_temp,
            #     top_p=GoogleConfig.TOP_P,
            #     top_k=GoogleConfig.TOP_K,
            #     max_tokens=GoogleConfig.MAX_TOKENS,
            #     response_format=response_format,
            #     chat_name=chat_name or self.chat_name
            # )

            fallback_temp = temperature if temperature is not None else OpenAIConfig.TEMPERATURE
            response = await self.generate_chat_completion_openai(
                messages=messages,
                model=OpenAIConfig.GPT_MODEL,
                temperature=fallback_temp,
                response_format=response_format,
                chat_name=chat_name or self.chat_name,
                project_name=project_name
            )
        except Exception:
            # fallback to OpenAI with possibly a different default temperature
            fallback_temp = temperature if temperature is not None else OpenAIConfig.TEMPERATURE
            response = await self.generate_chat_completion_openai(
                messages=messages,
                model=OpenAIConfig.GPT_MODEL,
                temperature=fallback_temp,
                response_format=response_format,
                chat_name=chat_name or self.chat_name,
                project_name=project_name
            )
        return response["choices"][0]["message"]["content"]

    # Direct calls to each underlying provider
    async def generate_chat_completion_openai(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = OpenAIConfig.GPT_MODEL,
        temperature: float = OpenAIConfig.TEMPERATURE,
        response_format: Optional[Dict] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.openai_provider.generate_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format=response_format,
            chat_name=chat_name or self.chat_name,
            project_name=project_name,
            build_response_callback=self._build_chat_response
        )

    async def generate_chat_completion_groq(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = GroqConfig.GROQ_MODEL,
        temperature: float = GroqConfig.TEMPERATURE,
        response_format: Optional[Dict] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.groq_provider.generate_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format=response_format,
            chat_name=chat_name or self.chat_name,
            project_name=project_name,
            build_response_callback=self._build_chat_response
        )

    async def generate_chat_completion_gemini(
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
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.gemini_provider.generate_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens,
            response_format=response_format,
            response_schema=response_schema,
            chat_name=chat_name or self.chat_name,
            project_name=project_name,
            build_response_callback=self._build_chat_response
        )

ai_client = WrappedAIClient()