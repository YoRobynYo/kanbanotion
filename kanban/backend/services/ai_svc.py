 #updated by qwen3 
import asyncio
from typing import Optional
from app.services.ai_client import get_ai_client  # ← uses the client we created

# System prompt for e-commerce assistant
SYSTEM_PROMPT = (
    "You are an AI customer support assistant for an e-commerce platform "
    "that sells AI-powered landing page builder tools. "
    "Help users with product questions, pricing, features, and general support. "
    "Be helpful, concise, and professional. Do not mention you are an AI."
)

async def assistant_reply(user_input: str, user_email: Optional[str] = None) -> str:
    """
    Generate an AI reply to user input using Ollama (dev) or Groq (prod).
    
    Args:
        user_input: The message from the user
        user_email: Optional email for personalization (not used yet)
    
    Returns:
        AI-generated reply as string
    """
    try:
        # Get the appropriate AI client (Ollama or Groq)
        ai_client = get_ai_client()

        # Build messages (OpenAI-style format)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]

        # Since Ollama/Groq SDKs are synchronous, run in thread pool
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(
            None,
            ai_client.chat_completion,
            messages
        )
        return reply

    except Exception as e:
        error_msg = f"AI service error: {str(e)}"
        print(f"[AI Error] {error_msg}")  # Log to console
        raise RuntimeError(error_msg)




# updated by groq 
# from typing import Optional, List, Dict, Any
# import logging
# import httpx
# import os
# from datetime import datetime, timedelta

# logger = logging.getLogger(__name__)

# # Configuration from environment
# ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "support@maiway.com")  # Fallback for rate limit messages


# class DailyRateLimiter:
#     """Global daily rate limiter - 14,300 requests/day. Supports optional per-user tracking."""
    
#     def __init__(self, max_requests: int = 14300, track_per_user: bool = False):
#         self.max_requests = max_requests
#         self.track_per_user = track_per_user
#         self.requests: List[Dict[str, Any]] = []  # List of {'timestamp': dt, 'user_email': str or None}
#         self.current_date = datetime.now().date()
    
#     def check_limit(self, user_email: Optional[str] = None) -> Dict[str, Any]:
#         """Check if under daily limit. Returns status dict."""
#         today = datetime.now().date()
        
#         # Reset if new day
#         if today != self.current_date:
#             self.requests = []
#             self.current_date = today
#             logger.info(f"Rate limiter reset for new day: {today}")
        
#         # Clean requests older than 24 hours (safety net)
#         cutoff = datetime.now() - timedelta(hours=24)
#         self.requests = [req for req in self.requests if req['timestamp'] > cutoff]
        
#         # Filter by user if tracking
#         filtered_requests = self.requests
#         if self.track_per_user and user_email:
#             filtered_requests = [req for req in self.requests if req.get('user_email') == user_email]
        
#         current_count = len(filtered_requests)
#         remaining = max(0, self.max_requests - current_count)
#         percentage = round((current_count / self.max_requests) * 100, 1)
        
#         return {
#             "allowed": current_count < self.max_requests,
#             "current_count": current_count,
#             "remaining": remaining,
#             "percentage": percentage,
#             "user_email": user_email  # For logging
#         }
    
#     def add_request(self, user_email: Optional[str] = None):
#         """Record a request, optionally tied to a user."""
#         req = {"timestamp": datetime.now(), "user_email": user_email}
#         self.requests.append(req)
#         logger.debug(f"Rate limiter: Added request (total: {len(self.requests)})")


# class OllamaClient:
#     """Ollama client for local development."""
    
#     def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
#         self.base_url = base_url
#         self.model = model
    
#     async def chat(
#         self, 
#         message: str, 
#         context: str = "", 
#         history: Optional[List[Dict[str, str]]] = None
#     ) -> str:
#         """Send a chat message to Ollama. Supports optional history for context."""
#         try:
#             async with httpx.AsyncClient(timeout=30.0) as client:
#                 # Build prompt with history if provided
#                 prompt_parts = []
#                 if history:
#                     for msg in history:
#                         role = "User" if msg["role"] == "user" else "Assistant"
#                         prompt_parts.append(f"{role}: {msg['content']}")
#                 if context:
#                     prompt_parts.insert(0, context)
#                 prompt_parts.append(f"User: {message}")
#                 prompt_parts.append("Assistant:")
#                 full_prompt = "\n".join(prompt_parts)
                
#                 response = await client.post(
#                     f"{self.base_url}/api/generate",
#                     json={
#                         "model": self.model,
#                         "prompt": full_prompt,
#                         "stream": False
#                     }
#                 )
                
#                 if response.status_code == 200:
#                     result = response.json()
#                     resp = result.get("response", "No response from AI")
#                     if ENVIRONMENT == "development":
#                         logger.debug(f"Ollama prompt: {message[:50]}... | Response: {resp[:50]}...")
#                     return resp
#                 else:
#                     logger.error(f"Ollama error: {response.status_code} - {response.text[:100]}")
#                     return "AI service temporarily unavailable"
                    
#         except httpx.ConnectError:
#             logger.error("Cannot connect to Ollama - is it running? Run 'ollama serve'")
#             return "AI assistant is offline. Please start Ollama with 'ollama serve'"
#         except Exception as e:
#             logger.error(f"Error calling Ollama: {e}")
#             return "I'm having trouble processing your request right now."


# class GroqClient:
#     """Groq client for production."""
    
#     def __init__(self, api_key: str):
#         if not api_key or api_key == "placeholder_get_this_later":
#             raise ValueError("Invalid GROQ_API_KEY provided")
#         self.api_key = api_key
#         try:
#             from groq import Groq
#             self.client = Groq(api_key=api_key)
#         except ImportError:
#             raise ImportError("groq package not installed. Run 'pip install groq'")
#         self.model = "llama-3.1-70b-versatile"
    
#     async def chat(
#         self, 
#         message: str, 
#         context: str = "", 
#         history: Optional[List[Dict[str, str]]] = None
#     ) -> str:
#         """Send a chat message to Groq. Supports optional history for context."""
#         try:
#             messages: List[Dict[str, str]] = []
#             if history:
#                 messages.extend(history)
#             if context:
#                 messages.append({"role": "system", "content": context})
#             messages.append({"role": "user", "content": message})
            
#             response = self.client.chat.completions.create(
#                 messages=messages,
#                 model=self.model,
#                 temperature=0.7,
#                 max_tokens=1024
#             )
            
#             resp = response.choices[0].message.content
#             if ENVIRONMENT == "development":  # Log in dev even for Groq
#                 logger.debug(f"Groq prompt: {message[:50]}... | Response: {resp[:50]}...")
#             return resp
            
#         except Exception as e:
#             logger.error(f"Groq error: {e}")
#             # Distinguish between rate limits and other errors
#             if "rate limit" in str(e).lower():
#                 return "AI service is temporarily rate-limited. Please try again soon."
#             return "AI service temporarily unavailable"


# # Global instances
# ai_client: Optional[Any] = None
# rate_limiter = DailyRateLimiter(max_requests=14300, track_per_user=False)  # Set to True for per-user limits


# def init_ai(retries: int = 2) -> bool:
#     """Initialize AI client based on environment. Returns True if successful."""
#     global ai_client
    
#     for attempt in range(retries + 1):
#         try:
#             if ENVIRONMENT == "development":
#                 # Use Ollama locally (unlimited)
#                 ai_client = OllamaClient()
#                 logger.info("Ollama chat service initialized (development)")
#                 return True
#             else:
#                 # Use Groq in production (14,300/day limit)
#                 if not GROQ_API_KEY or GROQ_API_KEY == "placeholder_get_this_later":
#                     logger.error("GROQ_API_KEY not configured for production")
#                     return False
                
#                 ai_client = GroqClient(api_key=GROQ_API_KEY)
#                 logger.info("Groq chat service initialized (production)")
#                 return True
                
#         except Exception as e:
#             logger.warning(f"Attempt {attempt + 1} failed to init AI: {e}")
#             if attempt == retries:
#                 logger.error(f"Failed to initialize AI after {retries + 1} attempts")
#                 ai_client = None
#                 return False
    
#     return False


# async def assistant_reply(
#     message: str, 
#     user_email: Optional[str] = None,
#     history: Optional[List[Dict[str, str]]] = None
# ) -> str:
#     """Generate AI assistant reply. Supports optional history for multi-turn chats."""
    
#     # Initialize if needed
#     if not ai_client:
#         success = init_ai()
#         if not success:
#             return "AI assistant is offline. Please check configuration."
    
#     if not ai_client:
#         # Fallback mock response for total failure
#         return "Hi! I'm here to help with your e-commerce questions. What's on your mind?"
    
#     # Check rate limit in production
#     if ENVIRONMENT != "development":
#         limit_status = rate_limiter.check_limit(user_email=user_email)
        
#         if not limit_status["allowed"]:
#             logger.warning(f"Rate limit exceeded: {limit_status}")
#             return f"""We've reached our daily chat limit for today ({limit_status['percentage']} used).

# We'd still love to help you! Please email us at {ADMIN_EMAIL} and we'll respond as quickly as possible.

# Our chat feature will be back online tomorrow. We apologize for the inconvenience!"""
    
#     try:
#         # E-commerce context
#         context = """You are a helpful e-commerce assistant. 
# You help customers with their orders, products, and general inquiries.
# Keep responses concise and friendly."""
        
#         response = await ai_client.chat(message, context, history)
        
#         # Record request in production
#         if ENVIRONMENT != "development":
#             rate_limiter.add_request(user_email=user_email)
            
#             # Log usage
#             status = rate_limiter.check_limit(user_email=user_email)
#             user_str = f" for user {user_email}" if user_email else ""
#             logger.info(f"AI usage{user_str}: {status['current_count']}/14,300 ({status['percentage']}%)")
        
#         return response
        
#     except Exception as e:
#         logger.error(f"Error in assistant_reply: {e}")
#         return "I'm having trouble processing your request right now. Please try again."


# # Initialize on import
# init_ai()





# built by claude 

# from typing import Optional
# import logging
# import httpx
# import os
# from datetime import datetime, timedelta
# from collections import defaultdict

# logger = logging.getLogger(__name__)

# # Configuration from environment
# ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# class DailyRateLimiter:
#     """Global daily rate limiter - 14,300 requests/day"""
    
#     def __init__(self, max_requests: int = 14300):
#         self.max_requests = max_requests
#         self.requests = []
#         self.current_date = datetime.now().date()
    
#     def check_limit(self):
#         """Check if under daily limit"""
#         today = datetime.now().date()
        
#         # Reset if new day
#         if today != self.current_date:
#             self.requests = []
#             self.current_date = today
        
#         # Clean old requests (24 hours)
#         cutoff = datetime.now() - timedelta(hours=24)
#         self.requests = [ts for ts in self.requests if ts > cutoff]
        
#         current_count = len(self.requests)
#         remaining = max(0, self.max_requests - current_count)
#         percentage = round((current_count / self.max_requests) * 100, 1)
        
#         return {
#             "allowed": current_count < self.max_requests,
#             "current_count": current_count,
#             "remaining": remaining,
#             "percentage": percentage
#         }
    
#     def add_request(self):
#         """Record a request"""
#         self.requests.append(datetime.now())


# class OllamaClient:
#     """Ollama client for local development"""
    
#     def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
#         self.base_url = base_url
#         self.model = model
    
#     async def chat(self, message: str, context: str = "") -> str:
#         """Send a chat message to Ollama"""
#         try:
#             async with httpx.AsyncClient(timeout=30.0) as client:
#                 prompt = f"{context}\n\nUser: {message}\nAssistant:" if context else message
#                 response = await client.post(
#                     f"{self.base_url}/api/generate",
#                     json={
#                         "model": self.model,
#                         "prompt": prompt,
#                         "stream": False
#                     }
#                 )
                
#                 if response.status_code == 200:
#                     result = response.json()
#                     return result.get("response", "No response from AI")
#                 else:
#                     logger.error(f"Ollama error: {response.status_code}")
#                     return "AI service temporarily unavailable"
                    
#         except httpx.ConnectError:
#             logger.error("Cannot connect to Ollama - is it running?")
#             return "AI assistant is offline. Please start Ollama with 'ollama serve'"
#         except Exception as e:
#             logger.error(f"Error calling Ollama: {e}")
#             return "I'm having trouble processing your request right now."


# class GroqClient:
#     """Groq client for production"""
    
#     def __init__(self, api_key: str):
#         self.api_key = api_key
#         from groq import Groq
#         self.client = Groq(api_key=api_key)
#         self.model = "llama-3.1-70b-versatile"
    
#     async def chat(self, message: str, context: str = "") -> str:
#         """Send a chat message to Groq"""
#         try:
#             messages = []
#             if context:
#                 messages.append({"role": "system", "content": context})
#             messages.append({"role": "user", "content": message})
            
#             response = self.client.chat.completions.create(
#                 messages=messages,
#                 model=self.model,
#                 temperature=0.7,
#                 max_tokens=1024
#             )
            
#             return response.choices[0].message.content
            
#         except Exception as e:
#             logger.error(f"Groq error: {e}")
#             return "AI service temporarily unavailable"


# # Global instances
# ai_client = None
# rate_limiter = DailyRateLimiter(max_requests=14300)


# def init_ai():
#     """Initialize AI client based on environment"""
#     global ai_client
    
#     try:
#         if ENVIRONMENT == "development":
#             # Use Ollama locally (unlimited)
#             ai_client = OllamaClient()
#             logger.info("Ollama chat service initialized (development)")
#         else:
#             # Use Groq in production (14,300/day limit)
#             if not GROQ_API_KEY or GROQ_API_KEY == "placeholder_get_this_later":
#                 logger.error("GROQ_API_KEY not configured for production")
#                 ai_client = None
#                 return
            
#             ai_client = GroqClient(api_key=GROQ_API_KEY)
#             logger.info("Groq chat service initialized (production)")
            
#     except Exception as e:
#         logger.error(f"Error initializing AI: {e}")
#         ai_client = None


# async def assistant_reply(message: str, user_email: Optional[str] = None) -> str:
#     """Generate AI assistant reply"""
    
#     # Initialize if needed
#     if not ai_client:
#         init_ai()
    
#     if not ai_client:
#         return "AI assistant is offline. Please check configuration."
    
#     # Check rate limit in production
#     if ENVIRONMENT != "development":
#         limit_status = rate_limiter.check_limit()
        
#         if not limit_status["allowed"]:
#             support_email = os.getenv("ADMIN_EMAIL", "support@maiway.com")
#             return f"""We've reached our daily chat limit for today.

# We'd still love to help you! Please email us at {support_email} and we'll respond as quickly as possible.

# Our chat feature will be back online tomorrow. We apologize for the inconvenience!"""
    
#     try:
#         # E-commerce context
#         context = """You are a helpful e-commerce assistant. 
# You help customers with their orders, products, and general inquiries.
# Keep responses concise and friendly."""
        
#         response = await ai_client.chat(message, context)
        
#         # Record request in production
#         if ENVIRONMENT != "development":
#             rate_limiter.add_request()
            
#             # Log usage
#             status = rate_limiter.check_limit()
#             logger.info(f"AI usage: {status['current_count']}/14,300 ({status['percentage']}%)")
        
#         return response
        
#     except Exception as e:
#         logger.error(f"Error in assistant_reply: {e}")
#         return "I'm having trouble processing your request right now. Please try again."


# # Initialize on import
# init_ai()



# original file 

# from typing import Optional
# import logging
# import httpx

# logger = logging.getLogger(__name__)

# # Ollama configuration
# OLLAMA_BASE_URL = "http://localhost:11434"
# OLLAMA_MODEL = "llama3.1:latest"  # or llama2, mistral, etc.

# class OllamaClient:
#     """Simple Ollama client for chat"""
    
#     def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
#         self.base_url = base_url
#         self.model = model
    
#     async def chat(self, message: str, context: str = "") -> str:
#         """Send a chat message to Ollama"""
#         try:
#             async with httpx.AsyncClient(timeout=30.0) as client:
#                 prompt = f"{context}\n\nUser: {message}\nAssistant:" if context else message
                
#                 response = await client.post(
#                     f"{self.base_url}/api/generate",
#                     json={
#                         "model": self.model,
#                         "prompt": prompt,
#                         "stream": False
#                     }
#                 )
                
#                 if response.status_code == 200:
#                     result = response.json()
#                     return result.get("response", "No response from AI")
#                 else:
#                     logger.error(f"Ollama error: {response.status_code}")
#                     return "AI service temporarily unavailable"
                    
#         except httpx.ConnectError:
#             logger.error("Cannot connect to Ollama - is it running? Run 'ollama serve'")
#             return "AI assistant is offline. Please start Ollama with 'ollama serve'"
#         except Exception as e:
#             logger.error(f"Error calling Ollama: {e}")
#             return "I'm having trouble processing your request right now."

# # Global client
# ollama_client = None

# def init_ai():
#     """Initialize Ollama client"""
#     global ollama_client
#     try:
#         ollama_client = OllamaClient()
#         logger.info("Ollama chat service initialized")
#     except Exception as e:
#         logger.error(f"Error initializing Ollama: {e}")
#         ollama_client = None

# async def assistant_reply(message: str, user_email: Optional[str] = None) -> str:
#     """Generate AI assistant reply using Ollama"""
#     try:
#         if not ollama_client:
#             init_ai()
        
#         if not ollama_client:
#             return "AI assistant is offline. Make sure Ollama is running ('ollama serve')"
        
#         # Add context to make responses more helpful
#         context = """You are a helpful e-commerce assistant. 
# You help customers with their orders, products, and general inquiries.
# Keep responses concise and friendly."""
        
#         response = await ollama_client.chat(message, context)
#         return response
        
#     except Exception as e:
#         logger.error(f"Error in assistant_reply: {e}")
#         return "I'm having trouble processing your request right now. Please try again."

# # Initialize on import
# init_ai()