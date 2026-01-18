"""LLM API client wrapper for ASIC-Agent (Mistral and OpenRouter compatible)"""

from openai import OpenAI
from mistralai import Mistral
from typing import List, Dict, Optional, Any
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper for LLM API (Mistral/OpenRouter) with retry logic and error handling"""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "mistral-large-latest",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        provider: str = "mistral",
        rate_limit_enabled: bool = True,
        rate_limit_delay: float = 6.0,
    ):
        """Initialize LLM client
        
        Args:
            api_key: API key (Mistral or OpenRouter)
            model_name: Model name
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens to generate
            provider: 'mistral' or 'openrouter'
            rate_limit_enabled: Enable rate limiting
            rate_limit_delay: Minimum seconds between API calls
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = provider
        self.rate_limit_enabled = rate_limit_enabled
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = None
        
        if provider == "mistral":
            # Configure Mistral client
            self.client = Mistral(api_key=api_key)
            logger.info(f"Initialized Mistral client with model: {model_name}")
        else:
            # Configure OpenRouter client
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            logger.info(f"Initialized OpenRouter client with model: {model_name}")
        
        if rate_limit_enabled:
            logger.info(f"Rate limiting enabled: {rate_limit_delay}s delay between requests ({60/rate_limit_delay:.1f} req/min)")
    
    def _apply_rate_limit(self):
        """Apply rate limiting delay if enabled"""
        if not self.rate_limit_enabled:
            return
        
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
    ) -> str:
        """Generate response from prompt with retry logic
        
        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            max_retries: Maximum number of retries on failure
            
        Returns:
            Generated text response
        """
        for attempt in range(max_retries):
            try:
                # Apply rate limiting before making request
                self._apply_rate_limit()
                
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})
                
                if self.provider == "mistral":
                    # Generate response via Mistral
                    response = self.client.chat.complete(
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                    )
                    
                    # Extract text from Mistral response
                    if response.choices and response.choices[0].message.content:
                        return response.choices[0].message.content
                    else:
                        logger.warning(f"Empty response on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                else:
                    # Generate response via OpenRouter
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                    )
                    
                    # Extract text
                    if response.choices and response.choices[0].message.content:
                        return response.choices[0].message.content
                    else:
                        logger.warning(f"Empty response on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        return ""
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
    ) -> str:
        """Chat with conversation history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_instruction: Optional system instruction
            
        Returns:
            Generated response
        """
        # Apply rate limiting before making request
        self._apply_rate_limit()
        
        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})
        
        # Convert messages to provider format
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Generate response
        if self.provider == "mistral":
            response = self.client.chat.complete(
                model=self.model_name,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        
        return response.choices[0].message.content if response.choices else ""
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens (rough estimate)
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
