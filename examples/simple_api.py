import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, query, ResultMessage
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Claude Code API", version="1.0.0")

class QueryRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    session_id: str

@app.post("/query")
async def query_claude(request: QueryRequest) -> QueryResponse:
    """
    Send a query to Claude Code.
    
    - If session_id is provided, it will resume that session
    - If not, it will start a new session
    - Returns the response and the session_id for future use
    """
    try:
        response_text = ""
        current_session_id = request.session_id
        
        # Build options based on whether we have a session_id
        options = ClaudeCodeOptions(
            resume=request.session_id,
            max_turns=1
        ) if request.session_id else ClaudeCodeOptions(max_turns=1)
        
        # Execute query
        async for message in query(prompt=request.prompt, options=options):
            if isinstance(message, ResultMessage):
                response_text = message.result
                current_session_id = message.session_id
                logger.info(f"Session ID: {current_session_id}")
            else:
                # Accumulate any other message types as text
                response_text += str(message)
        
        if not current_session_id:
            raise HTTPException(status_code=500, detail="Failed to get session ID from Claude")
        
        return QueryResponse(
            response=response_text,
            session_id=current_session_id
        )
        
    except Exception as e:
        logger.error(f"Error querying Claude: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)