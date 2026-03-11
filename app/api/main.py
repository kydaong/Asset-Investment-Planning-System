"""
FastAPI Backend for Mode 2 and Mode 3
Provides REST API and WebSocket endpoints
"""
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import os

from app.core.mode2_engine import Mode2Engine
from app.planning.engine import Mode3Engine

app = FastAPI(title="Asset Intelligence Platform API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
mode2_engine = None
mode3_engine = Mode3Engine()

# Store active WebSocket connections
active_connections: List[WebSocket] = []


# ============================================================================
# Pydantic Models
# ============================================================================

class Mode3SessionRequest(BaseModel):
    user_id: str
    budget: float
    filters: Optional[Dict] = None


class Mode3MessageRequest(BaseModel):
    session_id: str
    message: str


class ExportRequest(BaseModel):
    session_id: str
    format: str = "json"


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "Asset Intelligence Platform For Industry (AIPI)",
        "version": "1.0.0",
        "modes": ["Mode 2: Autonomous Intelligence", "Mode 3: Collaborative Planning"]
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "mode2_running": mode2_engine is not None,
        "mode3_available": True
    }


# ============================================================================
# MODE 2 ENDPOINTS
# ============================================================================

@app.get("/api/mode2/status")
async def get_mode2_status():
    """Get Mode 2 engine status"""
    
    # Check if insights log exists
    insights_count = 0
    recent_insights = []

    if os.path.exists("insights_log.json"):
        try:
            with open("insights_log.json", "r") as f:
                insights = json.load(f)
                insights_count = len(insights)
                recent_insights = insights[-10:]  # Last 10
        except:
            pass
    
    # Check trigger history
    trigger_count = 0
    if os.path.exists("trigger_history.json"):
        try:
            with open("trigger_history.json", "r") as f:
                history = json.load(f)
                trigger_count = len(history.get("triggered_events", []))
        except:
            pass
    
    return {
        "running": mode2_engine is not None,
        "total_insights": insights_count,
        "total_triggers": trigger_count,
        "recent_insights": recent_insights
    }


@app.get("/api/mode2/insights")
async def get_insights(limit: int = 50, severity: Optional[str] = None):
    """Get insights from Mode 2"""
    
    if not os.path.exists("insights_log.json"):
        return {"insights": []}
    
    try:
        with open("insights_log.json", "r") as f:
            insights = json.load(f)
        
        # Filter by severity if provided
        if severity:
            insights = [i for i in insights if i.get("urgency") == severity]
        
        # Return most recent first
        insights.reverse()
        
        return {
            "insights": insights[:limit],
            "total": len(insights)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mode2/triggers")
async def get_triggers(limit: int = 50):
    """Get trigger history"""
    
    if not os.path.exists("trigger_history.json"):
        return {"triggers": []}
    
    try:
        with open("trigger_history.json", "r") as f:
            history = json.load(f)
        
        triggered_events = history.get("triggered_events", [])
        triggered_events.reverse()
        
        return {
            "triggers": triggered_events[:limit],
            "total": len(triggered_events)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mode2/start")
async def start_mode2():
    """Start Mode 2 autonomous engine"""
    global mode2_engine
    
    if mode2_engine is not None:
        return {"message": "Mode 2 already running", "status": "running"}
    
    try:
        mode2_engine = Mode2Engine()
        
        # Start in background
        asyncio.create_task(mode2_engine.run_autonomous_loop())
        
        return {"message": "Mode 2 started successfully", "status": "running"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mode2/stop")  #needed this endpoint to stop the autonomous function
async def stop_mode2():
    """Stop Mode 2 autonomous engine"""
    global mode2_engine
    
    # Note: Actual stopping requires implementing a shutdown flag in Mode2Engine
    mode2_engine = None
    
    return {"message": "Mode 2 stopped", "status": "stopped"}


# WebSocket for real-time Mode 2 updates
@app.websocket("/ws/mode2")
async def websocket_mode2(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial status
        status = await get_mode2_status()
        await websocket.send_json({"type": "status", "data": status})
        
        # Keep connection alive and send updates
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            # Send latest insights
            insights = await get_insights(limit=5)
            await websocket.send_json({"type": "insights", "data": insights})
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    finally:
        active_connections.remove(websocket)


# ============================================================================
# MODE 3 ENDPOINTS
# ============================================================================

@app.post("/api/mode3/session/start")
async def start_mode3_session(request: Mode3SessionRequest):
    """Start a new Mode 3 planning session"""
    
    try:
        additional_params = {}
        if request.filters:
            additional_params["filters"] = request.filters
        
        result = mode3_engine.start_session(
            user_id=request.user_id,
            budget=request.budget,
            additional_params=additional_params
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mode3/session/message")
async def send_mode3_message(request: Mode3MessageRequest):
    """Send message in Mode 3 session"""
    
    try:
        response = mode3_engine.process_user_input(
            session_id=request.session_id,
            user_message=request.message
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mode3/sessions")
async def list_mode3_sessions(user_id: Optional[str] = None):
    """List all Mode 3 sessions"""
    
    try:
        sessions = mode3_engine.list_sessions(user_id=user_id)
        return {"sessions": sessions}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mode3/session/{session_id}")
async def get_mode3_session(session_id: str):
    """Get Mode 3 session details"""
    
    try:
        session = mode3_engine.session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mode3/session/{session_id}/summary")
async def get_mode3_session_summary(session_id: str):
    """Get Mode 3 session summary"""
    
    try:
        summary = mode3_engine.get_session_summary(session_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mode3/session/export")
async def export_mode3_portfolio(request: ExportRequest):
    """Export Mode 3 portfolio"""
    
    try:
        filepath = mode3_engine.export_portfolio(
            session_id=request.session_id,
            format=request.format
        )
        
        return {"filepath": filepath, "format": request.format}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4333)