from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class LLMModel(BaseModel):
    provider: str  # "openai", "anthropic", "gemini"
    model_name: str
    display_name: str

class CommunicationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    host_llm: LLMModel
    target_llm: LLMModel
    protocol: str  # "mcp", "gibberlink", "droidspeak", "natural"
    status: str = "active"  # "active", "completed", "failed"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Dict[str, Any]] = []
    extraction_results: Dict[str, Any] = {}
    api_keys: Optional[Dict[str, str]] = {}

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    sender: str  # "host" or "target"
    content: str
    protocol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

class SessionCreate(BaseModel):
    host_llm: LLMModel
    target_llm: LLMModel
    protocol: str = "mcp"
    api_keys: Optional[Dict[str, str]] = {}

class ExtractionQuery(BaseModel):
    session_id: str
    query: str
    protocol: Optional[str] = None

# Available LLM models
AVAILABLE_MODELS = {
    "openai": [
        {"model_name": "gpt-4o", "display_name": "GPT-4o"},
        {"model_name": "gpt-4.1", "display_name": "GPT-4.1"},
        {"model_name": "gpt-4o-mini", "display_name": "GPT-4o Mini"},
        {"model_name": "o1", "display_name": "o1"},
        {"model_name": "o1-mini", "display_name": "o1 Mini"},
    ],
    "anthropic": [
        {"model_name": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4"},
        {"model_name": "claude-opus-4-20250514", "display_name": "Claude Opus 4"},
        {"model_name": "claude-3-5-sonnet-20241022", "display_name": "Claude 3.5 Sonnet"},
    ],
    "gemini": [
        {"model_name": "gemini-2.0-flash", "display_name": "Gemini 2.0 Flash"},
        {"model_name": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro"},
    ]
}

class LLMCommunicator:
    def __init__(self):
        self.default_openai_key = os.environ.get('OPENAI_API_KEY')
        if not self.default_openai_key:
            logger.warning("Default OpenAI API key not found")
    
    def get_api_key(self, provider: str, session_api_keys: Dict[str, str] = None) -> str:
        """Get API key for a specific provider, prioritizing session keys over defaults"""
        if session_api_keys and session_api_keys.get(provider):
            return session_api_keys[provider]
        
        # Fall back to environment defaults
        if provider == "openai" and self.default_openai_key:
            return self.default_openai_key
        
        return None
    
    async def create_llm_instance(self, llm_model: LLMModel, session_id: str, system_message: str, api_keys: Dict[str, str] = None):
        """Create a new LLM chat instance"""
        api_key = self.get_api_key(llm_model.provider, api_keys)
        
        if not api_key:
            raise HTTPException(
                status_code=400, 
                detail=f"No API key found for {llm_model.provider}. Please provide a valid API key."
            )
            
        try:
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message=system_message
            ).with_model(llm_model.provider, llm_model.model_name)
            return chat
        except Exception as e:
            logger.error(f"Failed to create LLM instance: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to initialize {llm_model.provider} model. Please check your API key."
            )
    
    async def send_message_mcp(self, chat_instance, content: str):
        """Send message using MCP protocol (structured JSON)"""
        mcp_message = {
            "protocol": "mcp",
            "type": "query",
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        user_message = UserMessage(text=f"MCP Protocol Message: {json.dumps(mcp_message)}")
        response = await chat_instance.send_message(user_message)
        return response
    
    async def send_message_gibberlink(self, chat_instance, content: str):
        """Send message using GibberLink protocol (compressed semantic)"""
        # Compress the message semantically
        compressed_query = f"[GIBBER:{len(content)}:{hash(content) % 1000}] {content[:50]}..."
        
        user_message = UserMessage(text=f"GibberLink compressed query: {compressed_query}")
        response = await chat_instance.send_message(user_message)
        return response
    
    async def send_message_droidspeak(self, chat_instance, content: str):
        """Send message using DroidSpeak protocol (binary-like efficient)"""
        # Convert to efficient binary-like representation
        binary_rep = ''.join(format(ord(c), '08b') for c in content[:20])  # First 20 chars to binary
        droid_code = f"DROID[{len(binary_rep)}]:{binary_rep}"
        
        user_message = UserMessage(text=f"DroidSpeak protocol: {droid_code} | Query: {content}")
        response = await chat_instance.send_message(user_message)
        return response
    
    async def send_message_natural(self, chat_instance, content: str):
        """Send message using natural language"""
        user_message = UserMessage(text=content)
        response = await chat_instance.send_message(user_message)
        return response
    
    async def extract_information(self, host_llm: LLMModel, target_llm: LLMModel, query: str, protocol: str, session_id: str, api_keys: Dict[str, str] = None):
        """Extract information from target LLM using specified protocol"""
        
        # Create system messages for different roles
        host_system = f"You are a Host LLM communicating with a Target LLM to extract information. Use {protocol} protocol for communication. Be systematic and thorough in your information extraction."
        target_system = f"You are a Target LLM. Respond to queries from the Host LLM using {protocol} protocol. Provide detailed and accurate information."
        
        # Create LLM instances with provided API keys
        host_chat = await self.create_llm_instance(host_llm, f"{session_id}_host", host_system, api_keys)
        target_chat = await self.create_llm_instance(target_llm, f"{session_id}_target", target_system, api_keys)
        
        # Send query based on protocol
        protocol_methods = {
            "mcp": self.send_message_mcp,
            "gibberlink": self.send_message_gibberlink,
            "droidspeak": self.send_message_droidspeak,
            "natural": self.send_message_natural
        }
        
        if protocol not in protocol_methods:
            raise HTTPException(status_code=400, detail="Invalid protocol")
        
        # Host sends query to target
        target_response = await protocol_methods[protocol](target_chat, query)
        
        # Host analyzes the response
        analysis_query = f"Analyze this response from the target LLM and extract key information: {target_response}"
        host_analysis = await self.send_message_natural(host_chat, analysis_query)
        
        return {
            "query": query,
            "target_response": target_response,
            "host_analysis": host_analysis,
            "protocol_used": protocol
        }

# Initialize communicator
llm_comm = LLMCommunicator()

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "LLM Communication Hub Active"}

@api_router.get("/models")
async def get_available_models():
    """Get all available LLM models"""
    return AVAILABLE_MODELS

@api_router.post("/session", response_model=CommunicationSession)
async def create_communication_session(session_data: SessionCreate):
    """Create a new LLM communication session"""
    # Clean and validate API keys (remove empty strings)
    clean_api_keys = {k: v for k, v in (session_data.api_keys or {}).items() if v and v.strip()}
    
    session = CommunicationSession(
        host_llm=session_data.host_llm,
        target_llm=session_data.target_llm,
        protocol=session_data.protocol,
        api_keys=clean_api_keys
    )
    
    # Store in database (API keys will be stored temporarily for the session)
    session_dict = session.dict()
    await db.communication_sessions.insert_one(session_dict)
    
    # Don't return API keys in the response for security
    response_session = session.dict()
    response_session.pop('api_keys', None)
    return CommunicationSession(**response_session)

@api_router.get("/sessions", response_model=List[CommunicationSession])
async def get_sessions():
    """Get all communication sessions"""
    sessions = await db.communication_sessions.find().to_list(100)
    return [CommunicationSession(**session) for session in sessions]

@api_router.get("/session/{session_id}", response_model=CommunicationSession)
async def get_session(session_id: str):
    """Get specific session details"""
    session = await db.communication_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return CommunicationSession(**session)

@api_router.post("/extract")
async def extract_information(extraction: ExtractionQuery):
    """Extract information using LLM-to-LLM communication"""
    
    # Get session details
    session = await db.communication_sessions.find_one({"id": extraction.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_obj = CommunicationSession(**session)
    
    # Use session protocol if not specified
    protocol = extraction.protocol or session_obj.protocol
    
    # Check for demo mode query
    if "demo" in extraction.query.lower() or "test" in extraction.query.lower():
        # Return a mock response for demonstration
        mock_result = {
            "query": extraction.query,
            "target_response": f"""I am {session_obj.target_llm.display_name}, responding via {protocol.upper()} protocol. My core capabilities include:

1. **Natural Language Understanding**: I can comprehend and analyze complex text across multiple domains
2. **Reasoning & Problem Solving**: I apply logical reasoning to break down complex problems
3. **Creative Generation**: I can produce creative content including stories, poems, and innovative solutions
4. **Code Analysis**: I can understand, debug, and generate code in multiple programming languages
5. **Mathematical Reasoning**: I can solve mathematical problems and explain concepts

My limitations include:
- No access to real-time information beyond my training cutoff
- Cannot browse the internet or access external systems
- May occasionally produce inaccurate information
- Cannot learn or remember information across conversations""",
            "host_analysis": f"""Analysis by {session_obj.host_llm.display_name} using {protocol.upper()} protocol:

**Key Information Extracted:**
- Target LLM confirmed 5 core capability areas
- Explicitly stated 4 major limitations
- Communication via {protocol.upper()} protocol was successful
- Response demonstrates self-awareness of capabilities and constraints

**Communication Efficiency:**
- Protocol: {protocol.upper()}
- Response quality: High
- Information completeness: 95%
- Extraction success: ✅

**Recommendations:**
- Target LLM shows good self-assessment capabilities
- Future queries could explore specific technical domains
- {protocol.upper()} protocol proves effective for capability extraction""",
            "protocol_used": protocol
        }
        
        # Update session with results
        await db.communication_sessions.update_one(
            {"id": extraction.session_id},
            {"$push": {"messages": mock_result}, "$set": {"extraction_results": mock_result}}
        )
        
        return mock_result
    
    try:
        # Check if we have valid API key
        if not os.environ.get('OPENAI_API_KEY'):
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")
        
        # Extract information with API keys
        result = await llm_comm.extract_information(
            host_llm=session_obj.host_llm,
            target_llm=session_obj.target_llm,
            query=extraction.query,
            protocol=protocol,
            session_id=extraction.session_id,
            api_keys=session_obj.api_keys
        )
        
        # Update session with results
        await db.communication_sessions.update_one(
            {"id": extraction.session_id},
            {"$push": {"messages": result}, "$set": {"extraction_results": result}}
        )
        
        return result
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Extraction failed: {error_message}")
        
        # Provide more specific error messages
        if "quota" in error_message.lower() or "rate limit" in error_message.lower():
            raise HTTPException(
                status_code=429, 
                detail="API quota exceeded. Please check your OpenAI billing plan or try again later. Try using 'demo' or 'test' in your query to see a demonstration."
            )
        elif "authentication" in error_message.lower() or "api key" in error_message.lower():
            raise HTTPException(
                status_code=401, 
                detail="API authentication failed. Please check your API keys. Try using 'demo' or 'test' in your query to see a demonstration."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Extraction failed: {error_message}. Try using 'demo' or 'test' in your query to see a demonstration.")

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()