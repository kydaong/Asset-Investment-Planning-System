import anthropic
import os
import sys
import asyncio
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.core.database import SQLServerConnection
from app.mcp.sql_tools import SQLToolsProvider
from app.core.investigation_memory import InvestigationMemory
from app.core.trigger_system import TriggerSystem

# this is the mode 2 engine where it pulls claude api for the ai agent
class Mode2Engine:
    """
    Autonomous agent that continuously discovers insights from data
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        # pass the previous defined class into mode2engine
        self.client = anthropic.Anthropic(api_key=api_key)
        self.db = SQLServerConnection()
        self.sql_tools = SQLToolsProvider(self.db)
        self.investigation_memory = InvestigationMemory()
        self.trigger_system = TriggerSystem()

        # Configuration
        self.investigation_interval = int(os.getenv("MODE2_INTERVAL_SECONDS", 900))  # 15 minutes default
        self.max_insights_per_cycle = 5
    
    async def run_autonomous_loop(self):
        """
        Main autonomous loop - runs continuously
        """
        print("=" * 70)
        print("Mode 2: Autonomous Intelligence Engine Started")
        print(f"Investigation interval: {self.investigation_interval} seconds")
        print("=" * 70)
        
        cycle_number = 0
        
        while True:
            cycle_number += 1
            
            try:
                print(f"\n{'='*70}")
                print(f"Investigation Cycle #{cycle_number} - {datetime.now()}")
                print(f"{'='*70}")
                
                # Phase 1: Check triggers
                triggered_events = self.trigger_system.check_all_triggers()

                if not triggered_events:
                    print("⚠ No triggers fired — nothing to investigate at this time")
                    await asyncio.sleep(self.investigation_interval)
                    continue

                focus = self.trigger_system.get_investigation_focus(triggered_events)
                top_trigger = triggered_events[0]

                investigation_plan = {
                    "focus_area": focus,
                    "rationale": f"Triggered by: {top_trigger.get('trigger_name')} (severity: {top_trigger.get('severity')})",
                    "trigger_type": top_trigger.get("trigger_type"),
                    "trigger_details": top_trigger,
                    "data_sources": ["Assets", "MaintenanceHistory", "FailureEvents", "OperatingCosts", "ProductionMetrics", "AssetPerformanceMetrics"],
                    "all_triggers": triggered_events
                }

                print(f"\n📋 Investigation Plan:")
                print(f"   Focus: {investigation_plan.get('focus_area')}")
                print(f"   Rationale: {investigation_plan.get('rationale')}")
                print(f"   Triggers fired: {len(triggered_events)}")
                
                # Phase 2: Execute investigation
                findings = await self._investigate(investigation_plan)
                
                print(f"\n🔍 Investigation Complete:")
                print(f"   Data points analyzed: {len(findings.get('data', []))}")
                
                # Phase 3: Generate insights
                insights = await self._generate_insights(findings, investigation_plan)
                
                print(f"\n💡 Insights Generated: {len(insights)}")
                
                # Phase 4: Handle each insight
                for i, insight in enumerate(insights, 1):
                    print(f"\n   Insight #{i}:")
                    print(f"   Title: {insight.get('title')}")
                    print(f"   Urgency: {insight.get('urgency')}")
                    await self._handle_insight(insight)
                
                # Store in memory
                self.investigation_memory.store_investigation(
                    investigation_plan,
                    findings,
                    insights
                )
                
                # Show memory and trigger summary
                summary = self.investigation_memory.get_summary()
                trigger_summary = self.trigger_system.get_trigger_summary()
                print(f"\n📊 Memory Summary:")
                print(f"   Total investigations: {summary['total_investigations']}")
                print(f"   Total insights: {summary['total_insights']}")
                print(f"   Last 24h: {summary['recent_24h_insights']} insights")
                print(f"   Triggers fired (24h): {trigger_summary['total_triggers_24h']}")
                
            except Exception as e:
                print(f"\n✗ Error in investigation cycle: {e}")
                traceback.print_exc()
            
            # Wait before next cycle
            print(f"\n⏱ Waiting {self.investigation_interval} seconds until next cycle...")
            await asyncio.sleep(self.investigation_interval)
    
    async def _investigate(self, plan: Dict) -> Dict:
        """
        Agent executes investigation using MCP tools
        """
        
        investigation_prompt = f"""INVESTIGATION PLAN:
Focus: {plan.get('focus_area')}
Rationale: {plan.get('rationale')}
Data Sources: {plan.get('data_sources')}

Execute this investigation by:
1. Querying relevant data from the database
2. Analyzing trends, patterns, and anomalies
3. Comparing current state to baselines
4. Identifying deviations or opportunities

Use the available MCP tools to gather data. Be thorough and make multiple queries as needed.

IMPORTANT: Actually USE the tools - don't just describe what you would do. Query the database now."""

        findings = {"data": [], "observations": []}
        
        try:
            messages = [{"role": "user", "content": investigation_prompt}]

            # Claude investigates with tools
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                tools=self.sql_tools.get_tool_definitions(),
                messages=messages
            )

            # Process tool use
            while response.stop_reason == "tool_use":
                tool_results = []

                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input

                        print(f"      🔧 Using tool: {tool_name}")

                        result = self.sql_tools.execute_tool(tool_name, tool_input)

                        findings["data"].append({
                            "tool": tool_name,
                            "input": tool_input,
                            "result": result
                        })

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": str(result)
                        })

                # Append assistant response and tool results to messages
                messages.append({"role": "assistant", "content": [block.model_dump(exclude_none=True) for block in response.content]})
                messages.append({"role": "user", "content": tool_results})

                response = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4000,
                    tools=self.sql_tools.get_tool_definitions(),
                    messages=messages
                )
            
            # Extract final observations
            for block in response.content:
                if hasattr(block, "text"):
                    findings["observations"].append(block.text)
        
        except Exception as e:
            print(f"Error in investigation: {e}")
            findings["error"] = str(e)
        
        return findings
    
    async def _generate_insights(self, findings: Dict, plan: Dict) -> List[Dict]:
        """
        Agent reasons about findings to generate actionable insights
        """
        
        insight_prompt = f"""INVESTIGATION FINDINGS:

Focus Area: {plan.get('focus_area')}

Data Gathered:
{self._format_findings(findings)}

Analyze these findings and generate actionable insights.

For each insight, provide:
1. insight_id: Unique identifier (e.g., "INS-2026-001")
2. title: Clear, specific title
3. category: Type (Financial, Performance, Strategic, Risk, Opportunity)
4. observation: What is changing (specific, quantified)
5. impact: Business impact (quantified if possible)
6. recommendation: What should be done
7. urgency: critical/high/medium/low
8. confidence: high/medium/low

INSIGHT QUALITY RULES:
- Only generate if truly significant (don't create noise)
- Must be actionable (not just informational)
- Must be specific with numbers
- Must have clear business impact
- Maximum {self.max_insights_per_cycle} insights per investigation

Respond with JSON array:
[
    {{
        "insight_id": "INS-2026-XXX",
        "title": "Specific insight title",
        "category": "Performance",
        "observation": "Detailed observation with numbers",
        "impact": "Business impact quantified",
        "recommendation": "Specific action to take",
        "urgency": "high",
        "confidence": "high"
    }}
]

If no significant insights, return empty array []."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                messages=[{"role": "user", "content": insight_prompt}]
            )
            
            # Extract response
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text
            
            # Parse JSON - strip markdown and extract array
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if "```" in response_text:
                response_text = response_text[:response_text.index("```")]
            response_text = response_text.strip()

            # Extract only the JSON array portion
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start != -1 and end > start:
                response_text = response_text[start:end]

            insights = json.loads(response_text)
            
            # Add timestamp
            for insight in insights:
                insight["generated_at"] = datetime.now().isoformat()
                insight["investigation_focus"] = plan.get("focus_area")
            
            return insights
        
        except Exception as e:
            print(f"Error generating insights: {e}")
            return []
    
    async def _handle_insight(self, insight: Dict):
        """
        Determine what to do with each insight
        """
        
        # For now, just log it
        # In full implementation, this would:
        # - Send notifications (email, Slack, dashboard)
        # - Escalate to Mode 7 for complex decisions
        # - Create work orders or tickets
        
        print(f"      Category: {insight.get('category')}")
        print(f"      Impact: {insight.get('impact')}")
        print(f"      Recommendation: {insight.get('recommendation')}")
        
        # Save to file for now
        self._save_insight_to_file(insight)
    
    def _save_insight_to_file(self, insight: Dict):
        """Save insight to insights log file"""
        insights_file = "insights_log.json"
        
        try:
            # Load existing insights
            if os.path.exists(insights_file):
                with open(insights_file, 'r') as f:
                    all_insights = json.load(f)
            else:
                all_insights = []
            
            # Add new insight
            all_insights.append(insight)
            
            # Keep only last 1000 insights
            if len(all_insights) > 1000:
                all_insights = all_insights[-1000:]
            
            # Save
            with open(insights_file, 'w') as f:
                json.dump(all_insights, f, indent=2, default=str)
        
        except Exception as e:
            print(f"Error saving insight: {e}")
    
    def _format_findings(self, findings: Dict) -> str:
        """Format findings for prompt"""
        formatted = []
        
        for item in findings.get("data", []):
            tool = item.get("tool")
            result = item.get("result", [])

            if isinstance(result, list):
                data_summary = f"{len(result)} records"
            else:
                data_summary = str(result)
            formatted.append(f"- {tool}: {data_summary}")
        
        return "\n".join(formatted) if formatted else "No data gathered"


# Entry point for running Mode 2
async def main():
    """Run Mode 2 autonomous engine"""
    engine = Mode2Engine()
    await engine.run_autonomous_loop()

if __name__ == "__main__":
    asyncio.run(main())
