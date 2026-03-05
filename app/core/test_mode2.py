"""
Test Mode 2 - Run one investigation cycle
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.mode2_engine import Mode2Engine

async def test_single_cycle():
    """Run a single investigation cycle for testing"""
    
    print("=" * 70)
    print("Mode 2 Test - Single Investigation Cycle")
    print("=" * 70)
    
    engine = Mode2Engine()
    
    # Override interval for testing
    engine.investigation_interval = 10  # 10 seconds for test
    
    # Run one cycle
    print("\nPlanning investigation...")
    plan = await engine._plan_next_investigation()
    
    if not plan:
        print("No investigation planned")
        return
    
    print(f"\nPlan: {plan}")
    
    print("\nExecuting investigation...")
    findings = await engine._investigate(plan)
    
    print(f"\nFindings gathered: {len(findings.get('data', []))} data points")
    
    print("\nGenerating insights...")
    insights = await engine._generate_insights(findings, plan)
    
    print(f"\n{'='*70}")
    print(f"Generated {len(insights)} insights:")
    print(f"{'='*70}")
    
    for i, insight in enumerate(insights, 1):
        print(f"\nInsight #{i}:")
        print(f"  ID: {insight.get('insight_id')}")
        print(f"  Title: {insight.get('title')}")
        print(f"  Category: {insight.get('category')}")
        print(f"  Urgency: {insight.get('urgency')}")
        print(f"  Observation: {insight.get('observation')}")
        print(f"  Impact: {insight.get('impact')}")
        print(f"  Recommendation: {insight.get('recommendation')}")
    
    print(f"\n{'='*70}")
    print("Test complete!")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(test_single_cycle())