# api/rest_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import uvicorn
import json
from datetime import datetime

# Global state to store the last agent results
_state = {
    "intent": None, 
    "plan": None, 
    "validation": None,
    "timestamp": None,
    "session_id": None
}

class Health(BaseModel):
    status: str = "ok"
    message: str = "LLM/Voice pipeline up"
    timestamp: str = ""

class AgentState(BaseModel):
    intent: Optional[Dict[str, Any]] = None
    plan: Optional[Dict[str, Any]] = None  
    validation: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    session_id: Optional[str] = None

class CommandRequest(BaseModel):
    text: str
    mode: str = "text"  # "text" or "voice"

class CommandResponse(BaseModel):
    success: bool
    intent: Optional[Dict[str, Any]] = None
    plan: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    message: str = ""
    timestamp: str = ""

app = FastAPI(
    title="EMO Bot Agent API",
    description="RESTful API for the EMO Options Bot AI Agent",
    version="1.0.0"
)

@app.get("/health", response_model=Health)
def health():
    """Health check endpoint"""
    return Health(
        timestamp=datetime.now().isoformat()
    )

@app.get("/last", response_model=AgentState)
def get_last_state():
    """Get the last agent processing state"""
    return AgentState(**_state)

@app.get("/status")
def get_status():
    """Get detailed system status"""
    from voice import get_voice_status, get_tts_status
    
    return {
        "api": {
            "status": "running",
            "timestamp": datetime.now().isoformat()
        },
        "voice": get_voice_status(),
        "tts": get_tts_status(),
        "last_processing": _state.get("timestamp"),
        "session_id": _state.get("session_id")
    }

@app.post("/process", response_model=CommandResponse)
def process_command(request: CommandRequest):
    """Process a trading command through the agent pipeline"""
    try:
        from agents import parse, build_plan, risk_check
        from voice import speak
        
        # Parse intent
        intent = parse(request.text)
        
        # Build plan if strategy requested
        plan = None
        validation = None
        
        if intent.kind == "build_strategy" and intent.symbol and intent.strategy:
            plan = build_plan(intent.symbol, intent.strategy, intent.params)
            validation = risk_check(plan)
            
            # Update global state
            update_state(intent, plan, validation)
            
            # Generate response message
            if validation.ok:
                message = f"Successfully created {plan.strategy.replace('_', ' ')} plan for {plan.symbol}"
                if validation.warnings:
                    message += f" with {len(validation.warnings)} warning(s)"
            else:
                message = f"Plan validation failed with {len(validation.errors)} error(s)"
                
        elif intent.kind == "status":
            message = "System status requested"
            update_state(intent, None, None)
            
        elif intent.kind == "diagnose": 
            message = "Portfolio diagnosis requested"
            update_state(intent, None, None)
            
        else:
            message = f"Processed {intent.kind} request"
            update_state(intent, None, None)
        
        # Speak response if voice mode
        if request.mode == "voice":
            speak(message)
        
        return CommandResponse(
            success=True,
            intent=intent.__dict__ if intent else None,
            plan=_serialize_plan(plan) if plan else None,
            validation=validation.__dict__ if validation else None,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        error_msg = f"Error processing command: {str(e)}"
        if request.mode == "voice":
            speak(error_msg)
            
        return CommandResponse(
            success=False,
            message=error_msg,
            timestamp=datetime.now().isoformat()
        )

@app.get("/plans")
def get_recent_plans():
    """Get recent trading plans (placeholder - would integrate with database)"""
    if _state.get("plan"):
        return {
            "plans": [_state["plan"]],
            "count": 1,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "plans": [],
            "count": 0,
            "timestamp": datetime.now().isoformat()
        }

@app.delete("/clear")
def clear_state():
    """Clear the current agent state"""
    global _state
    _state = {
        "intent": None,
        "plan": None, 
        "validation": None,
        "timestamp": None,
        "session_id": None
    }
    return {"message": "State cleared", "timestamp": datetime.now().isoformat()}

def update_state(intent, plan, validation, session_id: str = "default"):
    """Update the global state with new agent results"""
    global _state
    _state["intent"] = intent.__dict__ if intent else None
    _state["plan"] = _serialize_plan(plan) if plan else None
    _state["validation"] = validation.__dict__ if validation else None
    _state["timestamp"] = datetime.now().isoformat()
    _state["session_id"] = session_id

def _serialize_plan(plan):
    """Serialize a plan object for JSON response"""
    if not plan:
        return None
        
    return {
        **plan.__dict__,
        "legs": [l.__dict__ for l in plan.legs] if hasattr(plan, 'legs') else []
    }

def serve(host="0.0.0.0", port=8085, reload=False):
    """Start the REST API server"""
    print(f"Starting EMO Bot Agent API on {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=reload)

if __name__ == "__main__":
    # Start server in development mode
    serve(host="127.0.0.1", port=8085, reload=True)