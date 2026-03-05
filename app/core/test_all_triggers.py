"""
Test all 5 trigger types
"""
# Note that this function test_all_triggers only test the whether it triggers fire. not a specific tool to generate insights
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
load_dotenv()

from app.core.trigger_system import TriggerSystem
from datetime import datetime

def test_all_triggers():
    """Test each trigger type"""
    
    print("=" * 70)
    print("Testing All 5 Trigger Types")
    print("=" * 70)
    
    trigger_system = TriggerSystem()
    
    # Test 1: Time-based trigger
    print("\n TEST 1: Time-Based Trigger")
    print("-" * 70)
    time_triggers = trigger_system._check_time_based_triggers()
    if time_triggers:
        print(f"✓ Time trigger activated:")
        for t in time_triggers:
            print(f"   {t['trigger_name']}: {t['investigation_focus']}")
    else:
        print("⚠ No time trigger (investigated too recently)")
    
    # Test 2: Threshold-based triggers
    print("\n TEST 2: Threshold-Based Triggers")
    print("-" * 70)
    threshold_triggers = trigger_system._check_threshold_triggers()
    if threshold_triggers:
        print(f"✓ {len(threshold_triggers)} threshold trigger(s) activated:")
        for t in threshold_triggers:
            print(f"   {t['trigger_name']} ({t['severity']}): {t['investigation_focus']}")
            # Show key metrics
            if 'asset_count' in t:
                print(f"      Assets affected: {t['asset_count']}")
            if 'overrun_pct' in t:
                print(f"      Budget overrun: {t['overrun_pct']:.1f}%")
            if 'failure_count' in t:
                print(f"      Failures: {t['failure_count']}")
    else:
        print("✓ No threshold breaches detected (system healthy)")
    
    # Test 3: Pattern-based triggers
    print("\n TEST 3: Pattern-Based Triggers")
    print("-" * 70)
    pattern_triggers = trigger_system._check_pattern_triggers()
    if pattern_triggers:
        print(f"✓ {len(pattern_triggers)} pattern(s) detected:")
        for t in pattern_triggers:
            print(f"   {t['trigger_name']} ({t['severity']}): {t['investigation_focus']}")
            if 'asset_count' in t:
                print(f"      Assets with pattern: {t['asset_count']}")
            if 'increase_pct' in t:
                print(f"      Increase: {t['increase_pct']:.1f}%")
    else:
        print("✓ No concerning patterns detected")
    
    # Test 4: Strategic triggers
    print("\n TEST 4: Strategic Goal Triggers")
    print("-" * 70)
    strategic_triggers = trigger_system._check_strategic_triggers()
    if strategic_triggers:
        print(f"✓ {len(strategic_triggers)} strategic issue(s) detected:")
        for t in strategic_triggers:
            print(f"   {t['trigger_name']} ({t['severity']}): {t['investigation_focus']}")
            if 'goal_count' in t:
                print(f"      Goals affected: {t['goal_count']}")
                if 'critical_goal_count' in t:
                    print(f"      Critical goals: {t['critical_goal_count']}")
    else:
        print("✓ All strategic goals on track")
    
    # Test 5: User request trigger
    print("\n TEST 5: User-Requested Trigger")
    print("-" * 70)
    user_trigger = trigger_system.create_user_request_trigger(
        focus_area="Analyze compressor maintenance costs and identify optimization opportunities",
        details={"user_id": "test_user", "request_source": "manual_test"},
        priority=1
    )
    print(f"✓ User trigger created:")
    print(f"   Focus: {user_trigger['focus_area']}")
    print(f"   Priority: {user_trigger['priority']}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TRIGGER SYSTEM SUMMARY")
    print("=" * 70)
    
    all_triggers = trigger_system.check_all_triggers()
    print(f"\nTotal triggers detected: {len(all_triggers)}")
    
    if all_triggers:
        print("\nTrigger Breakdown:")
        by_type = {}
        by_severity = {}
        
        for t in all_triggers:
            t_type = t.get('trigger_type', 'unknown')
            severity = t.get('severity', 'unknown')
            
            by_type[t_type] = by_type.get(t_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        print("\n  By Type:")
        for t_type, count in by_type.items():
            print(f"    {t_type}: {count}")
        
        print("\n  By Severity:")
        for severity, count in by_severity.items():
            print(f"    {severity}: {count}")
        
        print("\n  Top 3 Priorities:")
        sorted_triggers = sorted(all_triggers, key=lambda x: x.get('priority', 999))
        for i, t in enumerate(sorted_triggers[:3], 1):
            print(f"    {i}. {t.get('trigger_name')} (Priority {t.get('priority')}, {t.get('severity')})")
    
    # Show summary stats
    summary = trigger_system.get_trigger_summary()
    print(f"\n  Last 24h trigger count: {summary['total_triggers_24h']}")
    
    print("\n" + "=" * 70)
    print("✓ All trigger tests complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_all_triggers()