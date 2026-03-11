"""
Session Manager - Manages collaborative planning sessions
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class SessionManager:
    """
    Manages planning sessions and conversation history
    """
    
    def __init__(self, sessions_dir: str = "planning_sessions"):
        self.sessions_dir = sessions_dir
        
        # Create sessions directory if it doesn't exist
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)
        
        self.sessions = {}
    
    def create_session(
        self,
        user_id: str,
        initial_params: Dict
    ) -> str:
        """
        Create a new planning session
        
        Args:
            user_id: User identifier
            initial_params: Initial parameters (budget, constraints, etc.)
            
        Returns:
            session_id
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "parameters": initial_params,
            "conversation_history": [],
            "portfolio_history": [],
            "current_portfolio": None,
            "iterations": 0,
            "status": "active"
        }
        
        self.sessions[session_id] = session
        self._save_session(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        if session_id in self.sessions:
            return self.sessions[session_id]  
        
        # Try to load from file
        return self._load_session(session_id)
    
    def update_session(
        self,
        session_id: str,
        updates: Dict
    ):
        """Update session with new data"""
        if session_id not in self.sessions:
            session = self._load_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            self.sessions[session_id] = session
        
        # Update fields
        for key, value in updates.items():
            self.sessions[session_id][key] = value
        
        self.sessions[session_id]["last_updated"] = datetime.now().isoformat()
        
        # Save to file
        self._save_session(session_id)
    
    def add_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add a conversation turn to session history"""
        if session_id not in self.sessions:
            session = self._load_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            self.sessions[session_id] = session
        
        conversation_entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.sessions[session_id]["conversation_history"].append(conversation_entry)
        self.sessions[session_id]["last_updated"] = datetime.now().isoformat()
        
        self._save_session(session_id)
    
    def add_portfolio_snapshot(
        self,
        session_id: str,
        portfolio: Dict,
        iteration_note: str = ""
    ):
        """Save a portfolio snapshot"""
        if session_id not in self.sessions:
            session = self._load_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            self.sessions[session_id] = session
        
        snapshot = {
            "iteration": self.sessions[session_id]["iterations"] + 1,
            "timestamp": datetime.now().isoformat(),
            "portfolio": portfolio,
            "note": iteration_note
        }
        
        self.sessions[session_id]["portfolio_history"].append(snapshot)
        self.sessions[session_id]["current_portfolio"] = portfolio
        self.sessions[session_id]["iterations"] += 1
        self.sessions[session_id]["last_updated"] = datetime.now().isoformat()
        
        self._save_session(session_id)
    
    def close_session(self, session_id: str):
        """Close a session"""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "closed"
            self.sessions[session_id]["closed_at"] = datetime.now().isoformat()
            self._save_session(session_id)
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        List all sessions, optionally filtered by user or status
        """
        sessions = []
        
        # Load all session files
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]  # Remove .json
                session = self._load_session(session_id)
                
                if session:
                    # Apply filters
                    if user_id and session.get("user_id") != user_id:
                        continue
                    
                    if status and session.get("status") != status:
                        continue
                    
                    # Add summary info
                    sessions.append({
                        "session_id": session["session_id"],
                        "user_id": session["user_id"],
                        "created_at": session["created_at"],
                        "last_updated": session["last_updated"],
                        "status": session.get("status", "active"),
                        "iterations": session.get("iterations", 0),
                        "budget": session.get("parameters", {}).get("budget", 0)
                    })
        
        # Sort by last_updated (newest first)
        sessions.sort(key=lambda s: s["last_updated"], reverse=True)
        
        return sessions
    
    def _save_session(self, session_id: str):
        """Save session to file"""
        if session_id not in self.sessions:
            return
        
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.sessions[session_id], f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[Dict]:
        """Load session from file"""
        filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r') as f:
                session = json.load(f)
                self.sessions[session_id] = session
                return session
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get summary of a session"""
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        current_portfolio = session.get("current_portfolio", {})
        
        return {
            "session_id": session_id,
            "user_id": session["user_id"],
            "created_at": session["created_at"],
            "last_updated": session["last_updated"],
            "status": session.get("status", "active"),
            "iterations": session.get("iterations", 0),
            "conversation_turns": len(session.get("conversation_history", [])),
            "budget": session.get("parameters", {}).get("budget", 0),
            "current_portfolio_summary": {
                "project_count": current_portfolio.get("project_count", 0),
                "total_cost": current_portfolio.get("total_cost", 0),
                "total_npv": current_portfolio.get("total_npv", 0),
                "budget_utilization": current_portfolio.get("budget_utilization_pct", 0)
            } if current_portfolio else None
        }