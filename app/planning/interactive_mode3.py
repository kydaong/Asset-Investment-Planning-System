"""
Interactive Mode 3 Session
Real-time conversation with Claude for capital planning
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
load_dotenv()

from app.planning.engine import Mode3Engine
import json


class InteractivePlanning:
    """
    Interactive CLI for Mode 3 planning sessions
    """
    
    def __init__(self):
        self.engine = Mode3Engine()
        self.session_id = None
        self.current_portfolio = None
    
    def start(self):
        """Start interactive session"""
        
        print("\n" + "=" * 70)
        print("   ASSET INTELLIGENCE PLATFORM - MODE 3")
        print("   Interactive Capital Planning Session")
        print("=" * 70)
        
        # Get session parameters
        print("\n Let's set up your planning session:\n")
        
        # User ID
        user_id = input("Enter your name or ID (default: user): ").strip() or "user"
        
        # Budget
        while True:
            budget_input = input("Enter budget in millions (e.g., 15 for $15M): ").strip()
            try:
                budget = float(budget_input) * 1_000_000
                break
            except ValueError:
                print("Please enter a valid number")
        
        # Filters (optional)
        print("\n🔍 Optional filters (press Enter to skip):")
        
        filters = {}
        
        # Priority filter
        priority_input = input("  Filter by priority (Critical/High/Medium/Low, comma-separated): ").strip()
        if priority_input:
            filters["priority"] = [p.strip() for p in priority_input.split(",")]
        
        # Min NPV filter
        min_npv_input = input("  Minimum NPV in millions (e.g., 1 for $1M, or Enter to skip): ").strip()
        if min_npv_input:
            try:
                filters["min_npv"] = float(min_npv_input) * 1_000_000
            except ValueError:
                pass
        
        # Start session
        print("\n Starting planning session...\n")
        
        additional_params = {}
        if filters:
            additional_params["filters"] = filters  # add in additional_params if you need further filter criteria
        
        result = self.engine.start_session(
            user_id=user_id,
            budget=budget,
            additional_params=additional_params
        )
        
        self.session_id = result["session_id"]
        self.current_portfolio = result["portfolio"]
        
        # Display initial portfolio
        print("\n" + "=" * 70)
        print("INITIAL PORTFOLIO RECOMMENDATION")
        print("=" * 70 + "\n")
        
        print(result["message"])
        
        # Show quick stats
        self._show_portfolio_stats()
        
        # Start conversation loop
        self._conversation_loop()
    
    def _conversation_loop(self):
        """Main conversation loop"""
        
        print("\n" + "=" * 70)
        print("Interactive Planning Session Started")
        print("=" * 70)
        print("\nYou can now iterate on the portfolio. Try asking:")
        print("  • 'What if we increase budget to $18M?'")
        print("  • 'Show only Critical priority projects'")
        print("  • 'What's the risk profile?'")
        print("  • 'Remove Project X and add Project Y'")
        print("  • 'Export this portfolio'")
        print("\nType 'help' for more examples, 'stats' for portfolio stats, or 'quit' to exit.")
        print("=" * 70 + "\n")
        
        while True:
            # Get user input
            user_input = input("\n You: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                self._exit_session()
                break
            
            if user_input.lower() == 'help':
                self._show_help()
                continue
            
            if user_input.lower() == 'stats':
                self._show_portfolio_stats()
                continue
            
            if user_input.lower() == 'export':
                self._export_portfolio()
                continue
            
            if user_input.lower() == 'history':
                self._show_conversation_history()
                continue
            
            if user_input.lower() == 'projects':
                self._show_projects()
                continue
            
            # Process with Claude
            print("\n AIPI: ", end="", flush=True)
            
            try:
                response = self.engine.process_user_input(
                    self.session_id,
                    user_input
                )
                
                # Print Claude's response
                print(response["message"])
                
                # Update current portfolio if modified
                if response.get("updated_portfolio"):
                    self.current_portfolio = response["updated_portfolio"]
                    print("\n✓ Portfolio updated")
                    self._show_portfolio_stats()
            
            except Exception as e:
                print(f"\n Error: {e}")
                import traceback
                traceback.print_exc()
    
    def _show_portfolio_stats(self):
        """Display current portfolio statistics"""
        
        if not self.current_portfolio:
            print("\n No portfolio available")
            return
        
        pf = self.current_portfolio
        
        print("\n" + "─" * 70)
        print("📊 CURRENT PORTFOLIO STATS")
        print("─" * 70)
        print(f"  Projects Selected:      {pf['project_count']}")
        print(f"  Total Investment:       ${pf['total_cost']:,.0f}")
        print(f"  Total NPV:              ${pf['total_npv']:,.0f}")
        print(f"  Budget Utilization:     {pf['budget_utilization_pct']:.1f}%")
        print(f"  Budget Remaining:       ${pf['budget_remaining']:,.0f}")
        print(f"  Average IRR:            {pf['avg_irr']:.1f}%")
        
        if pf.get('priority_breakdown'):
            print(f"\n  Priority Breakdown:")
            for priority, count in pf['priority_breakdown'].items():
                print(f"    {priority}: {count} projects")
        
        if pf.get('category_breakdown'):
            print(f"\n  Project Type Breakdown:")
            for category, count in pf['category_breakdown'].items():
                print(f"    {category}: {count} projects")
        
        print(f"\n  Deferred Projects:      {len(pf.get('deferred_projects', []))}")
        print("─" * 70)
    
    def _show_projects(self):
        """Display list of selected and deferred projects"""
        
        if not self.current_portfolio:
            print("\n⚠️  No portfolio available")
            return
        
        selected = self.current_portfolio.get('selected_projects', [])
        deferred = self.current_portfolio.get('deferred_projects', [])
        
        print("\n" + "=" * 70)
        print("SELECTED PROJECTS")
        print("=" * 70)
        
        for i, p in enumerate(selected, 1):
            print(f"\n{i}. {p.get('project_name', 'Unknown')}")
            print(f"   ID: {p.get('project_id', 'N/A')}")
            print(f"   Type: {p.get('project_type', 'N/A')}")
            print(f"   Cost: ${p.get('estimated_cost', 0):,.0f}")
            print(f"   NPV: ${p.get('npv', 0):,.0f}")
            print(f"   IRR: {p.get('irr', 0):.1f}%")
            print(f"   Priority: {p.get('priority', 'N/A')}")
            print(f"   Risk: {p.get('risk_level', 'N/A')}")
        
        print(f"\n{'=' * 70}")
        print(f"DEFERRED PROJECTS ({len(deferred)} total)")
        print("=" * 70)
        
        # Show first 10 deferred
        for i, p in enumerate(deferred[:10], 1):
            print(f"\n{i}. {p.get('project_name', 'Unknown')}")
            print(f"   Cost: ${p.get('estimated_cost', 0):,.0f} | NPV: ${p.get('npv', 0):,.0f}")
        
        if len(deferred) > 10:
            print(f"\n... and {len(deferred) - 10} more deferred projects")
    
    def _show_help(self):
        """Show help menu"""
        
        print("\n" + "=" * 70)
        print("HELP - Example Questions You Can Ask")
        print("=" * 70)
        
        print("\n Budget Scenarios:")
        print("  • 'What if we increase budget to $18M?'")
        print("  • 'What if budget is reduced to $12M?'")
        print("  • 'Show me sensitivity analysis for different budgets'")
        
        print("\n Filtering & Prioritization:")
        print("  • 'Show only Critical priority projects'")
        print("  • 'Filter by High and Critical priority'")
        print("  • 'Show only projects with NPV > $2M'")
        print("  • 'Remove all high-risk projects'")
        
        print("\n Analysis & Insights:")
        print("  • 'What's the risk profile of this portfolio?'")
        print("  • 'Which projects have the highest ROI?'")
        print("  • 'What's the payback period?'")
        print("  • 'Compare this to an all-critical-priority portfolio'")
        
        print("\n Modifications:")
        print("  • 'Add Project X back into the portfolio'")
        print("  • 'Remove Project Y from the portfolio'")
        print("  • 'Swap Project A for Project B'")
        
        print("\n Special Commands:")
        print("  • 'stats'    - Show current portfolio statistics")
        print("  • 'projects' - List all selected and deferred projects")
        print("  • 'export'   - Export portfolio to file")
        print("  • 'history'  - Show conversation history")
        print("  • 'help'     - Show this help menu")
        print("  • 'quit'     - Exit session")
        
        print("=" * 70)
    
    def _show_conversation_history(self):
        """Show conversation history"""
        
        session = self.engine.session_manager.get_session(self.session_id)
        if not session:
            print("\n  Session not found")
            return
        
        history = session.get("conversation_history", [])
        
        print("\n" + "=" * 70)
        print(f"CONVERSATION HISTORY ({len(history)} turns)")
        print("=" * 70)
        
        for i, turn in enumerate(history, 1):
            role = " You" if turn['role'] == 'user' else " AIPI"
            timestamp = turn.get('timestamp', 'N/A')
            content = turn['content'][:200]  # Truncate long messages
            
            print(f"\n[{i}] {role} ({timestamp}):")
            print(f"    {content}...")
        
        print("=" * 70)
    
    def _export_portfolio(self):
        """Export portfolio to file"""
        
        print("\n📁 Export Options:")
        print("  1. JSON (detailed)")
        print("  2. CSV (spreadsheet)")
        
        choice = input("\nSelect format (1 or 2): ").strip()
        
        format_map = {"1": "json", "2": "csv"}
        export_format = format_map.get(choice, "json")
        
        try:
            filepath = self.engine.export_portfolio(
                self.session_id,
                format=export_format
            )
            print(f"\n✓ Portfolio exported to: {filepath}")
        except Exception as e:
            print(f"\n Export failed: {e}")
    
    def _exit_session(self):
        """Exit session gracefully"""
        
        print("\n" + "=" * 70)
        print("SESSION SUMMARY")
        print("=" * 70)
        
        summary = self.engine.get_session_summary(self.session_id)
        
        if summary:
            print(f"\nSession ID: {summary['session_id']}")
            print(f"Duration: {summary['created_at']} to {summary['last_updated']}")
            print(f"Iterations: {summary['iterations']}")
            print(f"Conversation turns: {summary['conversation_turns']}")
            
            if summary.get('current_portfolio_summary'):
                pf = summary['current_portfolio_summary']
                print(f"\nFinal Portfolio:")
                print(f"  Projects: {pf['project_count']}")
                print(f"  Total Cost: ${pf['total_cost']:,.0f}")
                print(f"  Total NPV: ${pf['total_npv']:,.0f}")
                print(f"  Budget Utilization: {pf['budget_utilization']:.1f}%")
        
        # Ask if they want to export
        export = input("\n💾 Export final portfolio? (y/n): ").strip().lower()
        if export == 'y':
            self._export_portfolio()
        
        print("\n✓ Session closed. Thank you for using Mode 3!")
        print("=" * 70 + "\n")


def main():
    """Main entry point"""
    session = InteractivePlanning()
    
    try:
        session.start()
    except KeyboardInterrupt:
        print("\n\n⚠️  Session interrupted by user")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()