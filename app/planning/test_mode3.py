"""
Test Mode 3 - Collaborative Planning
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
load_dotenv()

from app.planning.engine import Mode3Engine


def test_mode3_session():
    """Test a complete Mode 3 planning session"""
    
    print("=" * 70)
    print("Mode 3: Collaborative Planning - Test Session")
    print("=" * 70)
    
    # Initialize Mode 3
    engine = Mode3Engine()
    
    # Start session with $15M budget
    print("\n🚀 Starting planning session...")
    result = engine.start_session(
        user_id="test_user",
        budget=15000000,  # $15M
        additional_params={
            "filters": {
                "min_npv": 0  # Only projects with positive NPV
            }
        }
    )
    
    session_id = result["session_id"]
    
    print("\n" + "=" * 70)
    print("INITIAL PORTFOLIO")
    print("=" * 70)
    print(result["message"])
    
    # Test iteration 1: Increase budget
    print("\n\n" + "=" * 70)
    print("ITERATION 1: What if we increase budget to $18M?")
    print("=" * 70)
    
    response1 = engine.process_user_input(
        session_id,
        "What if we increase the budget to $18M? What additional projects should we include?"
    )
    
    print("\n" + response1["message"])
    
    # Test iteration 2: Focus on critical priority
    print("\n\n" + "=" * 70)
    print("ITERATION 2: Focus on critical priority only")
    print("=" * 70)
    
    response2 = engine.process_user_input(
        session_id,
        "Show me a portfolio with only Critical and High priority projects. What's the NPV?"
    )
    
    print("\n" + response2["message"])
    
    # Test iteration 3: Risk analysis
    print("\n\n" + "=" * 70)
    print("ITERATION 3: Risk analysis")
    print("=" * 70)
    
    response3 = engine.process_user_input(
        session_id,
        "What's the risk profile of this portfolio? How many high-risk projects do we have?"
    )
    
    print("\n" + response3["message"])
    
    # Export portfolio
    print("\n\n" + "=" * 70)
    print("EXPORT PORTFOLIO")
    print("=" * 70)
    
    try:
        json_file = engine.export_portfolio(session_id, format="json")
        print(f"\n✓ Portfolio exported to: {json_file}")
        
        csv_file = engine.export_portfolio(session_id, format="csv")
        print(f"✓ Portfolio exported to: {csv_file}")
    except Exception as e:
        print(f"Export error: {e}")
    
    # Show session summary
    print("\n\n" + "=" * 70)
    print("SESSION SUMMARY")
    print("=" * 70)
    
    summary = engine.get_session_summary(session_id)
    if summary:
        print(f"\nSession ID: {summary['session_id']}")
        print(f"User: {summary['user_id']}")
        print(f"Created: {summary['created_at']}")
        print(f"Iterations: {summary['iterations']}")
        print(f"Conversation turns: {summary['conversation_turns']}")
        
        if summary['current_portfolio_summary']:
            pf = summary['current_portfolio_summary']
            print(f"\nCurrent Portfolio:")
            print(f"  Projects: {pf['project_count']}")
            print(f"  Total Cost: ${pf['total_cost']:,.0f}")
            print(f"  Total NPV: ${pf['total_npv']:,.0f}")
            print(f"  Budget Utilization: {pf['budget_utilization']:.1f}%")
    
    print("\n" + "=" * 70)
    print("✓ Mode 3 test complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_mode3_session()