"""
Mode 3 Engine: Collaborative Planning
Interactive portfolio optimization with Claude
"""
import anthropic
import os
import json
import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime


# ANSI color codes
class _C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    ORANGE = "\033[33m"
    YELLOW = "\033[93m"
    GREEN  = "\033[92m"
    CYAN   = "\033[96m"
    GREY   = "\033[90m"


# Keyword → color mapping for status indicators
_STATUS_COLORS = {
    # Priority / criticality
    "Critical": _C.RED    + _C.BOLD,
    "High":     _C.ORANGE + _C.BOLD,
    "Medium":   _C.YELLOW,
    "Low":      _C.GREEN,
    # Risk
    "High Risk":    _C.RED,
    "Medium Risk":  _C.YELLOW,
    "Low Risk":     _C.GREEN,
    # Project status
    "Approved":     _C.GREEN  + _C.BOLD,
    "Under Review": _C.YELLOW,
    "Proposed":     _C.CYAN,
    "Deferred":     _C.GREY,
}

_STATUS_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in _STATUS_COLORS) + r')\b'
)


def colorize(text: str) -> str:
    """Apply ANSI color codes to status/priority keywords in text."""
    def _replace(m):
        word = m.group(1)
        return _STATUS_COLORS[word] + word + _C.RESET
    return _STATUS_PATTERN.sub(_replace, text)

from app.core.database import SQLServerConnection
from app.mcp.sql_tools import SQLToolsProvider
from app.planning.optimization import OptimizationEngine
from app.planning.portfolio_builder import PortfolioBuilder
from app.planning.session_manager import SessionManager


class Mode3Engine:
    """
    Collaborative planning engine - interactive portfolio optimization
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.db = SQLServerConnection()
        self.sql_tools = SQLToolsProvider(self.db)
        self.optimizer = OptimizationEngine()
        self.portfolio_builder = PortfolioBuilder()
        self.session_manager = SessionManager()
    
    def start_session(
        self,
        user_id: str,
        budget: float,
        additional_params: Optional[Dict] = None
    ) -> Dict:
        """
        Start a new collaborative planning session
        
        Args:
            user_id: User identifier
            budget: Budget constraint (e.g., 15000000 for $15M)
            additional_params: Additional parameters (filters, constraints, etc.)
            
        Returns:
            Session info with initial portfolio
        """
        
        print("=" * 70)
        print("Mode 3: Collaborative Planning Session Started")
        print(f"User: {user_id}")
        print(f"Budget: ${budget:,.0f}")
        print("=" * 70)
        
        # Create session
        params = {
            "budget": budget,
            **(additional_params or {})
        }
        
        session_id = self.session_manager.create_session(user_id, params)
        
        print(f"\n Session created: {session_id}")
        
        # Get candidate projects
        print("\n Fetching candidate projects from database...")
        candidate_projects = self.portfolio_builder.get_candidate_projects()
        
        print(f"✓ Found {len(candidate_projects)} candidate projects")

        # Save full unfiltered list to session so it's always available for analysis
        self.session_manager.update_session(
            session_id,
            {"all_candidate_projects": candidate_projects}
        )

        # Apply filters if specified
        if additional_params and "filters" in additional_params:
            print("\n Applying filters...")
            candidate_projects = self.portfolio_builder.filter_projects(
                candidate_projects,
                additional_params["filters"]
            )
            print(f"✓ {len(candidate_projects)} projects after filtering")
        
        # Calculate total requested funding
        total_requested = sum(p.get("estimated_cost", 0) for p in candidate_projects)
        
        print(f"\n Total funding requested: ${total_requested:,.0f}")
        print(f"   Available budget: ${budget:,.0f}")
        print(f"   Oversubscription: {(total_requested / budget - 1) * 100:.1f}%")
        
        # Optimize portfolio
        print("\n Optimizing portfolio...")
        portfolio = self.optimizer.optimize(
            candidate_projects,
            budget,
            algorithm="greedy"
        )
        
        print(f"✓ Portfolio optimized")
        print(f"   Selected: {portfolio['project_count']} projects")
        print(f"   Total cost: ${portfolio['total_cost']:,.0f}")
        print(f"   Total NPV: ${portfolio['total_npv']:,.0f}")
        print(f"   Budget utilization: {portfolio['budget_utilization_pct']:.1f}%")
        
        # Save to session
        self.session_manager.add_portfolio_snapshot(
            session_id,
            portfolio,
            "Initial optimized portfolio"
        )
        
        # Generate Claude's initial explanation
        initial_message = self._generate_initial_explanation(
            portfolio,
            candidate_projects,
            budget
        )
        
        self.session_manager.add_conversation(
            session_id,
            "assistant",
            initial_message
        )
        
        return {
            "session_id": session_id,
            "portfolio": portfolio,
            "message": colorize(initial_message),
            "candidate_count": len(candidate_projects),
            "selected_count": portfolio["project_count"],
            "deferred_count": len(portfolio["deferred_projects"])
        }
    
    def process_user_input(
        self,
        session_id: str,
        user_message: str
    ) -> Dict:
        """
        Process user input during planning session
        
        Args:
            session_id: Session identifier
            user_message: User's message/request
            
        Returns:
            Claude's response with updated portfolio if applicable
        """
        
        print(f"\n{'='*70}")
        print(f"Processing User Input - Session: {session_id}")
        print(f"{'='*70}")
        print(f"User: {user_message}")
        
        # Get session
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}
        
        # Add user message to history
        self.session_manager.add_conversation(
            session_id,
            "user",
            user_message
        )
        
        # Build context for Claude
        context = self._build_planning_context(session)
        
        # Get Claude's response
        print("AIPI is analyzing your request...")
        response = self._call_claude_for_planning(context, user_message, session)
        
        # Colorize status keywords before returning
        response["message"] = colorize(response["message"])

        # Add Claude's response to history (plain text, no ANSI codes)
        self.session_manager.add_conversation(
            session_id,
            "assistant",
            response["message"]
        )
        
        # If Claude modified portfolio, update it
        if response.get("updated_portfolio"):
            print(f"\n✓ Portfolio updated")
            print(f"   Projects: {response['updated_portfolio']['project_count']}")
            print(f"   Cost: ${response['updated_portfolio']['total_cost']:,.0f}")
            print(f"   NPV: ${response['updated_portfolio']['total_npv']:,.0f}")
            
            self.session_manager.add_portfolio_snapshot(
                session_id,
                response["updated_portfolio"],
                f"User requested: {user_message[:50]}..."
            )
        
        return response
    
    def _generate_initial_explanation(
        self,
        portfolio: Dict,
        all_projects: List[Dict],
        budget: float
    ) -> str:
        """
        Generate Claude's initial portfolio explanation
        """
        
        prompt = f"""You are a capital planning advisor. Generate a clear, professional explanation of this optimized portfolio.

PORTFOLIO DETAILS:
Budget: ${budget:,.0f}
Selected Projects: {portfolio['project_count']}
Total Cost: ${portfolio['total_cost']:,.0f}
Total NPV: ${portfolio['total_npv']:,.0f}
Average IRR: {portfolio['avg_irr']:.1f}%

SELECTED PROJECTS:
{json.dumps(portfolio['selected_projects'][:10], indent=2, default=str)}

DEFERRED PROJECTS:
{len(portfolio['deferred_projects'])} projects deferred

Generate a response that:
1. Summarizes the portfolio in 2-3 sentences
2. Highlights top 3-5 high-priority projects with brief rationale
3. Mentions key metrics (NPV, IRR, budget utilization)
4. Invites the user to iterate ("What if..." scenarios)

Keep it professional, concise, and actionable. Use bullet points sparingly - prefer prose.
Format numbers with commas and dollar signs. Do not use any emojis or icons. Do not refer to yourself as Claude — if you must reference the system, use the name AIPI."""

        try:
            response = self._call_claude_with_retry(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        
        except Exception as e:
            # Fallback to simple summary
            return self._simple_portfolio_summary(portfolio, budget)
    
    def _simple_portfolio_summary(self, portfolio: Dict, budget: float) -> str:
        """Fallback summary if Claude call fails"""
        
        summary = f"""Portfolio Optimization Complete

I've analyzed all candidate projects and created an optimized portfolio:

**Portfolio Summary:**
- Budget: ${budget:,.0f}
- Selected Projects: {portfolio['project_count']}
- Total Investment: ${portfolio['total_cost']:,.0f} ({portfolio['budget_utilization_pct']:.1f}% of budget)
- Total NPV: ${portfolio['total_npv']:,.0f}
- Average IRR: {portfolio['avg_irr']:.1f}%

**Top Priority Projects:**
"""
        
        # Add top 5 projects
        for i, project in enumerate(portfolio['selected_projects'][:5], 1):
            summary += f"\n{i}. {project['project_name']} - ${project['estimated_cost']:,.0f} (NPV: ${project['npv']:,.0f})"
        
        summary += f"\n\n**Deferred Projects:** {len(portfolio['deferred_projects'])} projects deferred to future periods"
        
        summary += "\n\nYou can now iterate on this portfolio. Try asking:\n- 'What if budget increases to $X?'\n- 'Show me only critical priority projects'\n- 'What's the ROI if we defer Project Y?'"
        
        return summary
    
    def _build_planning_context(self, session: Dict) -> str:
        """
        Build context string for Claude with session state
        """
        
        current_portfolio = session.get("current_portfolio", {})
        params = session.get("parameters", {})
        
        context = f"""PLANNING SESSION CONTEXT:

Session ID: {session['session_id']}
Budget: ${params.get('budget', 0):,.0f}
Iterations: {session.get('iterations', 0)}

CURRENT PORTFOLIO:
- Selected Projects: {current_portfolio.get('project_count', 0)}
- Total Cost: ${current_portfolio.get('total_cost', 0):,.0f}
- Total NPV: ${current_portfolio.get('total_npv', 0):,.0f}
- Budget Used: {current_portfolio.get('budget_utilization_pct', 0):.1f}%

CONVERSATION HISTORY (last 5 turns):
"""
        
        # Add last 5 conversation turns
        history = session.get("conversation_history", [])[-5:]
        for turn in history:
            role = turn['role'].upper()
            content = turn['content'][:200]  # Truncate long messages
            context += f"\n{role}: {content}...\n"
        
        return context
    
    def _call_claude_for_planning(
        self,
        context: str,
        user_message: str,
        session: Dict
    ) -> Dict:
        """
        Call Claude to process user's planning request
        """
        
        current_portfolio = session.get("current_portfolio", {})
        # Use the full unfiltered project list saved at session start, fall back to portfolio projects
        all_projects = session.get("all_candidate_projects") or (
            current_portfolio.get("selected_projects", []) + current_portfolio.get("deferred_projects", [])
        )
        budget = session.get("parameters", {}).get("budget", 0)
        
        # Build planning prompt
        planning_prompt = f"""{context}

USER REQUEST:
{user_message}

AVAILABLE PROJECTS:
{json.dumps(all_projects[:30], indent=2, default=str)}

CURRENT PORTFOLIO DETAILS:
{json.dumps(current_portfolio, indent=2, default=str)}

You are an AI capital planning advisor. The user wants to modify or understand their portfolio.

ANALYZE THE REQUEST:
1. Does the user want to:
   - Change budget?
   - Add/remove specific projects?
   - Apply filters (priority, type, risk)?
   - Run sensitivity analysis?
   - Get explanations?
   - Compare scenarios?

2. If modification requested:
   - Determine new constraints
   - Re-optimize portfolio
   - Explain changes and trade-offs
   
3. If explanation requested:
   - Provide clear, data-driven answer
   - Reference specific projects and metrics

RESPONSE FORMAT:
{{
    "action": "modify" | "explain" | "analyze",
    "message": "Your response to the user (conversational, professional)",
    "modifications": {{
        "new_budget": number or null,
        "filters": {{}} or null,
        "add_projects": [] or null,
        "remove_projects": [] or null
    }} or null
}}

The "message" field must be professional prose with no emojis or icons. Do not refer to yourself as Claude — if you must reference the system, use the name AIPI.
Respond ONLY with valid JSON."""

        try:
            response = self._call_claude_with_retry(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                messages=[{"role": "user", "content": planning_prompt}]
            )
            
            # Parse JSON response
            response_text = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Extract JSON
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                response_text = response_text[start:end]
            
            claude_response = json.loads(response_text)
            
            # If Claude wants to modify portfolio, do it
            if claude_response.get("action") == "modify" and claude_response.get("modifications"):
                updated_portfolio = self._apply_modifications(
                    current_portfolio,
                    all_projects,
                    claude_response["modifications"],
                    budget
                )
                
                return {
                    "message": claude_response["message"],
                    "action": "modify",
                    "updated_portfolio": updated_portfolio
                }
            
            else:
                return {
                    "message": claude_response["message"],
                    "action": claude_response.get("action", "explain"),
                    "updated_portfolio": None
                }
        
        except Exception as e:
            print(f"Error in Claude planning call: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback response
            return {
                "message": f"I encountered an error processing your request. Please try rephrasing or simplifying your question.",
                "action": "error",
                "updated_portfolio": None,
                "error": str(e)
            }
    
    def _apply_modifications(
        self,
        current_portfolio: Dict,
        all_projects: List[Dict],
        modifications: Dict,
        current_budget: float
    ) -> Dict:
        """
        Apply user-requested modifications to portfolio
        """
        
        # Get new budget or use current (handle explicit null from AI response)
        new_budget = modifications.get("new_budget") or current_budget
        
        # Get filters
        filters = modifications.get("filters")
        
        # Start with all projects
        candidate_projects = all_projects.copy()
        
        # Apply filters
        if filters:
            candidate_projects = self.portfolio_builder.filter_projects(
                candidate_projects,
                filters
            )
        
        # Remove specific projects if requested
        remove_projects = modifications.get("remove_projects", [])
        if remove_projects:
            candidate_projects = [
                p for p in candidate_projects 
                if p.get("project_id") not in remove_projects
            ]
        
        # Re-optimize with new constraints
        new_portfolio = self.optimizer.optimize(
            candidate_projects,
            new_budget,
            algorithm="greedy"
        )
        
        return new_portfolio
    
    def _call_claude_with_retry(self, max_retries: int = 3, wait_seconds: int = 65, **kwargs):
        """Call Claude API with retry on rate limit errors"""
        for attempt in range(max_retries):
            try:
                return self.client.messages.create(**kwargs)
            except Exception as e:
                is_rate_limit = (
                    isinstance(e, anthropic.RateLimitError) or
                    (hasattr(e, 'status_code') and e.status_code == 429) or
                    "rate_limit_error" in str(e)
                )
                if is_rate_limit and attempt < max_retries - 1:
                    print(f"      ⏳ Rate limit hit — waiting {wait_seconds}s before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_seconds)
                else:
                    raise
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get summary of a session"""
        return self.session_manager.get_session_summary(session_id)
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict]:
        """List all sessions for a user"""
        return self.session_manager.list_sessions(user_id=user_id)
    
    def export_portfolio(
        self,
        session_id: str,
        format: str = "json"
    ) -> str:
        """
        Export portfolio to file
        
        Args:
            session_id: Session identifier
            format: "json" or "csv"
            
        Returns:
            Filepath of exported file
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        portfolio = session.get("current_portfolio")
        if not portfolio:
            raise ValueError(f"No portfolio in session {session_id}")
        
        # Create exports directory
        exports_dir = "portfolio_exports"
        if not os.path.exists(exports_dir):
            os.makedirs(exports_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            filepath = os.path.join(exports_dir, f"portfolio_{session_id}_{timestamp}.json")
            with open(filepath, 'w') as f:
                json.dump(portfolio, f, indent=2, default=str)
        
        elif format == "csv":
            import csv
            filepath = os.path.join(exports_dir, f"portfolio_{session_id}_{timestamp}.csv")
            
            with open(filepath, 'w', newline='') as f:
                if portfolio.get("selected_projects"):
                    fieldnames = portfolio["selected_projects"][0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(portfolio["selected_projects"])
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return filepath