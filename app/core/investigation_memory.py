"""
Investigation Memory - Tracks what Mode 2 has already investigated
Prevents redundant analyses and maintains context
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class InvestigationMemory:
    """
    Stores investigation history to avoid redundant work
    """
    
    def __init__(self, memory_file: str = "investigation_memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict:
        """Load memory from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
                return {"investigations": [], "insights_generated": []}
        return {"investigations": [], "insights_generated": []}
    
    def _save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def store_investigation(
        self, 
        investigation_plan: Dict,
        findings: Dict,
        insights: List[Dict]
    ):
        """Store completed investigation"""
        investigation_record = {
            "timestamp": datetime.now().isoformat(),
            "plan": investigation_plan,
            "findings_summary": {
                "data_points": len(findings.get("data", [])),
                "focus_area": investigation_plan.get("focus_area")
            },
            "insights_count": len(insights),
            "insight_ids": [i.get("insight_id") for i in insights]
        }
        
        self.memory["investigations"].append(investigation_record)
        
        # Store insights separately
        for insight in insights:
            self.memory["insights_generated"].append({
                "timestamp": datetime.now().isoformat(),
                "insight": insight
            })



        # Keep only last 100 investigations
        if len(self.memory["investigations"]) > 100:
            self.memory["investigations"] = self.memory["investigations"][-100:]
        
        # Keep only last 200 insights
        if len(self.memory["insights_generated"]) > 200:
            self.memory["insights_generated"] = self.memory["insights_generated"][-200:]
        
        self._save_memory()
    
    def get_recent_investigations(self, hours: int = 24) -> List[Dict]:
        """Get investigations from last N hours"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        recent = []
        for inv in self.memory["investigations"]:
            inv_time = datetime.fromisoformat(inv["timestamp"]).timestamp()
            if inv_time > cutoff:
                recent.append(inv)
        
        return recent
    
    def get_recent_insights(self, hours: int = 24) -> List[Dict]:
        """Get insights from last N hours"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        recent = []
        for insight_record in self.memory["insights_generated"]:
            insight_time = datetime.fromisoformat(insight_record["timestamp"]).timestamp()
            if insight_time > cutoff:
                recent.append(insight_record["insight"])
        
        return recent
    
    def has_investigated_recently(self, focus_area: str, hours: int = 6) -> bool:
        """Check if focus area was investigated recently"""
        recent = self.get_recent_investigations(hours)
        
        for inv in recent:
            if inv.get("plan", {}).get("focus_area") == focus_area:
                return True
        
        return False
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            "total_investigations": len(self.memory["investigations"]),
            "total_insights": len(self.memory["insights_generated"]),
            "recent_24h_investigations": len(self.get_recent_investigations(24)),
            "recent_24h_insights": len(self.get_recent_insights(24))
        }