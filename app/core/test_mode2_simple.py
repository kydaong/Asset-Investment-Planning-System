"""
Simplified Mode 2 test - Direct insight generation
"""
import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import SQLServerConnection
from app.mcp.sql_tools import SQLToolsProvider
import anthropic

async def simple_test():
    """Test insight generation with real data"""
    
    print("=" * 70)
    print("Simplified Mode 2 Test - Direct Insight Generation")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n✗ No API key found!")
        return
    
    print(f"\n✓ API Key: {api_key[:20]}...")
    
    # Get some real data
    print("\n📊 Fetching real data from database...")
    
    db = SQLServerConnection()
    sql_tools = SQLToolsProvider(db)

    # Get asset health data
    health_data = sql_tools.execute_tool(
        "execute_sql",
        {"query": "SELECT TOP 10 AssetID, Availability, Efficiency, Vibration, Temperature FROM dbo.AssetPerformanceMetrics ORDER BY Timestamp DESC"}
    )
    print(f"✓ Retrieved {len(health_data)} asset health records")

    # Get maintenance costs
    cost_data = sql_tools.execute_tool(
        "execute_sql",
        {"query": "SELECT a.AssetType, SUM(m.LaborCost + m.PartsCost + m.ContractorCost) AS TotalCost FROM dbo.MaintenanceHistory m JOIN dbo.Assets a ON m.AssetID = a.AssetID GROUP BY a.AssetType"}
    )
    print(f"✓ Retrieved {len(cost_data)} cost records")

    # Get recent failures
    failure_data = sql_tools.execute_tool(
        "execute_sql",
        {"query": "SELECT Severity, COUNT(*) AS Count, SUM(DowntimeHours) AS TotalDowntime FROM dbo.FailureEvents GROUP BY Severity"}
    )
    print(f"✓ Retrieved {len(failure_data)} failure records")
    
    # Now ask Claude to generate insights
    print("\n🤖 Asking Claude to generate insights...")
    
    insight_prompt = f"""You are analyzing manufacturing plant data. Based on the following real data, generate 2-3 actionable insights.

ASSET HEALTH DATA (Last 30 days):
{health_data[:10]}

MAINTENANCE COSTS (Last 90 days by Asset Type):
{cost_data}

FAILURES BY SEVERITY (Last 90 days):
{failure_data}

Generate insights in JSON format:
[
    {{
        "insight_id": "INS-TEST-001",
        "title": "Specific insight title",
        "category": "Performance|Cost|Risk",
        "observation": "What the data shows with specific numbers",
        "impact": "Business impact quantified",
        "recommendation": "What to do about it",
        "urgency": "high|medium|low",
        "confidence": "high|medium|low"
    }}
]

Generate 2-3 real insights based on this actual data."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": insight_prompt}]
        )
        
        # Extract response
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text
        
        print(f"\n✓ Claude responded ({len(response_text)} characters)")
        
        # Parse JSON
        response_text = response_text.strip()
        
        # Remove markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        print(f"\nRaw response:")
        print(response_text[:500])
        print("...")
        
        insights = json.loads(response_text)
        
        print(f"\n{'='*70}")
        print(f"INSIGHTS GENERATED: {len(insights)}")
        print(f"{'='*70}")
        
        for i, insight in enumerate(insights, 1):
            print(f"\n📊 Insight #{i}:")
            print(f"   Title: {insight.get('title')}")
            print(f"   Category: {insight.get('category')}")
            print(f"   Urgency: {insight.get('urgency')}")
            print(f"   Observation: {insight.get('observation')}")
            print(f"   Impact: {insight.get('impact')}")
            print(f"   Recommendation: {insight.get('recommendation')}")
        
        print(f"\n{'='*70}")
        print("✓ Test Successful!")
        print(f"{'='*70}")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())