"""
Complete Trigger System for Mode 2 Autonomous Intelligence
Implements 5 trigger types: Time, Threshold, Pattern, Strategic, User-Request
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.database import SQLServerConnection
import json
import os

class TriggerSystem:
    """
    Multi-trigger system that determines when investigations should run
    """
    
    def __init__(self):
        self.db = SQLServerConnection()
        
        # Load configuration
        self.config = self._load_config()
        
        # Threshold configurations
        self.thresholds = {
            "health_score_min": 70,
            "health_score_critical": 60,
            "budget_overrun_pct": 15,
            "budget_overrun_critical_pct": 25,
            "failure_count_weekly": 3,
            "failure_count_critical": 5,
            "cost_std_dev_multiplier": 2,
            "degradation_points": 5,
            "availability_min": 85,
            "oee_min": 75,
            "maintenance_cost_increase_pct": 20
        }
        
        # Time-based trigger tracking
        self.trigger_history_file = "trigger_history.json"
        self.trigger_history = self._load_trigger_history()
    
    def _load_config(self) -> Dict:
        """Load trigger configuration from file or use defaults"""
        config_file = "trigger_config.json"
        
        default_config = {
            "time_based": {
                "enabled": True,
                "interval_minutes": 30,
                "daily_summary_time": "08:00"
            },
            "threshold_based": {
                "enabled": True,
                "check_interval_minutes": 5
            },
            "pattern_based": {
                "enabled": True,
                "check_interval_minutes": 30
            },
            "strategic_based": {
                "enabled": True,
                "check_interval_minutes": 60
            },
            "user_request": {
                "enabled": True
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                return default_config
        
        # Save default config
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _load_trigger_history(self) -> Dict:
        """Load trigger history"""
        if os.path.exists(self.trigger_history_file):
            try:
                with open(self.trigger_history_file, 'r') as f:
                    return json.load(f)
            except:
                return {"last_checks": {}, "triggered_events": []}
        
        return {"last_checks": {}, "triggered_events": []}
    
    def _save_trigger_history(self):
        """Save trigger history"""
        try:
            with open(self.trigger_history_file, 'w') as f:
                json.dump(self.trigger_history, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving trigger history: {e}")
    
    def check_all_triggers(self) -> List[Dict]:
        """
        Check ALL trigger types and return list of triggered events
        """
        all_triggered_events = []
        
        print("\n🔍 Checking all trigger types...")
        
        # 1. Time-based triggers
        if self.config["time_based"]["enabled"]:
            time_triggers = self._check_time_based_triggers()
            if time_triggers:
                print(f"   ⏰ Time-based: {len(time_triggers)} triggers")
                all_triggered_events.extend(time_triggers)
        
        # 2. Threshold-based triggers (Event triggers)
        if self.config["threshold_based"]["enabled"]:
            threshold_triggers = self._check_threshold_triggers()
            if threshold_triggers:
                print(f"   🎯 Threshold-based: {len(threshold_triggers)} triggers")
                all_triggered_events.extend(threshold_triggers)
        
        # 3. Pattern-based triggers
        if self.config["pattern_based"]["enabled"]:
            pattern_triggers = self._check_pattern_triggers()
            if pattern_triggers:
                print(f"   📈 Pattern-based: {len(pattern_triggers)} triggers")
                all_triggered_events.extend(pattern_triggers)
        
        # 4. Strategic goal triggers
        if self.config["strategic_based"]["enabled"]:
            strategic_triggers = self._check_strategic_triggers()
            if strategic_triggers:
                print(f"   🎯 Strategic-based: {len(strategic_triggers)} triggers")
                all_triggered_events.extend(strategic_triggers)
        
        # 5. User-requested triggers (checked separately, not here)
        
        # Save triggered events to history
        for event in all_triggered_events:
            self._record_triggered_event(event)
        
        self._save_trigger_history()
        
        return all_triggered_events
    
    # =========================================================================
    # TRIGGER TYPE 1: TIME-BASED TRIGGERS
    # =========================================================================
    
    def _check_time_based_triggers(self) -> List[Dict]:
        """
        Check if enough time has passed for scheduled investigation
        """
        triggers = []
        now = datetime.now()
        
        # Check last investigation time
        last_check = self.trigger_history["last_checks"].get("time_based")
        
        if last_check:
            last_check_time = datetime.fromisoformat(last_check)
            interval_minutes = self.config["time_based"]["interval_minutes"]
            time_since = (now - last_check_time).total_seconds() / 60
            
            if time_since < interval_minutes:
                # Not enough time passed
                return []
        
        # Time trigger activated
        triggers.append({
            "trigger_type": "time_based",
            "trigger_name": "scheduled_investigation",
            "severity": "routine",
            "interval_minutes": self.config["time_based"]["interval_minutes"],
            "investigation_focus": "Routine system health check",
            "priority": 5,
            "triggered_at": now.isoformat()
        })
        
        # Update last check time
        self.trigger_history["last_checks"]["time_based"] = now.isoformat()
        
        return triggers
    
    # =========================================================================
    # TRIGGER TYPE 2: THRESHOLD-BASED TRIGGERS (EVENT TRIGGERS)
    # =========================================================================
    
    def _check_threshold_triggers(self) -> List[Dict]:
        """
        Check for threshold breaches - immediate action needed
        """
        events = []
        
        # Threshold 1: Low health scores
        health_trigger = self._check_health_score_threshold()
        if health_trigger:
            events.append(health_trigger)
        
        # Threshold 2: Budget overrun
        budget_trigger = self._check_budget_threshold()
        if budget_trigger:
            events.append(budget_trigger)
        
        # Threshold 3: Failure spike
        failure_trigger = self._check_failure_threshold()
        if failure_trigger:
            events.append(failure_trigger)
        
        # Threshold 4: Low availability
        availability_trigger = self._check_availability_threshold()
        if availability_trigger:
            events.append(availability_trigger)
        
        # Threshold 5: Low OEE
        oee_trigger = self._check_oee_threshold()
        if oee_trigger:
            events.append(oee_trigger)
        
        return events
    
    def _check_health_score_threshold(self) -> Optional[Dict]:
        """Check if any assets have critically low health scores"""
        try:
            query = f"""
            SELECT
                AssetID,
                AVG(Availability) as AvgHealth,
                MIN(Availability) as MinHealth,
                COUNT(*) as DataPoints
            FROM dbo.AssetPerformanceMetrics
            WHERE Timestamp >= DATEADD(day, -7, GETDATE())
            GROUP BY AssetID
            HAVING AVG(Availability) < {self.thresholds['health_score_min']}
            ORDER BY AvgHealth ASC
            """

            low_health_assets = self.db.execute_query(query)

            if low_health_assets:
                critical_assets = [a for a in low_health_assets if a['AvgHealth'] < self.thresholds['health_score_critical']]
                
                severity = "critical" if critical_assets else "high"
                priority = 1 if critical_assets else 2
                
                return {
                    "trigger_type": "threshold",
                    "trigger_name": "low_health_score",
                    "severity": severity,
                    "asset_count": len(low_health_assets),
                    "critical_asset_count": len(critical_assets),
                    "assets": [a['AssetID'] for a in low_health_assets[:10]],
                    "worst_health": low_health_assets[0]['AvgHealth'],
                    "details": low_health_assets,
                    "investigation_focus": "Asset health degradation - identify root causes and recommend interventions",
                    "priority": priority,
                    "triggered_at": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error checking health scores: {e}")
        
        return None
    
    def _check_budget_threshold(self) -> Optional[Dict]:
        """Check if budget is being exceeded"""
        try:
            query = """
            SELECT
                SUM(TotalCost) as MTDCost,
                COUNT(*) as TransactionCount
            FROM dbo.OperatingCosts
            WHERE YearMonth >= DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)
            """
            
            result = self.db.execute_query(query)
            if result and result[0]['MTDCost']:
                mtd_cost = float(result[0]['MTDCost'] or 0)

                # Get days in month for pro-rating
                now = datetime.now()
                days_in_month = (datetime(now.year, now.month % 12 + 1, 1) - timedelta(days=1)).day
                day_of_month = now.day

                # Monthly budget (configure this)
                monthly_budget = 500000.0  # $500K
                prorated_budget = (monthly_budget / days_in_month) * day_of_month

                overrun_amount = mtd_cost - prorated_budget
                overrun_pct = (overrun_amount / prorated_budget) * 100
                
                if overrun_pct > self.thresholds["budget_overrun_pct"]:
                    severity = "critical" if overrun_pct > self.thresholds["budget_overrun_critical_pct"] else "high"
                    
                    return {
                        "trigger_type": "threshold",
                        "trigger_name": "budget_overrun",
                        "severity": severity,
                        "mtd_cost": mtd_cost,
                        "prorated_budget": prorated_budget,
                        "monthly_budget": monthly_budget,
                        "overrun_amount": overrun_amount,
                        "overrun_pct": overrun_pct,
                        "transaction_count": result[0]['TransactionCount'],
                        "investigation_focus": "Budget overrun analysis - identify cost drivers and recommend cost reduction measures",
                        "priority": 1 if severity == "critical" else 2,
                        "triggered_at": datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"Error checking budget: {e}")
        
        return None
    
    def _check_failure_threshold(self) -> Optional[Dict]:
        """Check for failure spike"""
        try:
            query = """
            SELECT 
                COUNT(*) as FailureCount,
                SUM(RepairCost) as TotalRepairCost,
                SUM(DowntimeHours) as TotalDowntime,
                SUM(ProductionLoss) as TotalProductionLoss
            FROM dbo.FailureEvents
            WHERE FailureDate >= DATEADD(day, -7, GETDATE())
              AND Severity IN ('Critical', 'Major')
            """
            
            result = self.db.execute_query(query)
            if result:
                failure_count = result[0]['FailureCount'] or 0
                
                if failure_count > self.thresholds["failure_count_weekly"]:
                    severity = "critical" if failure_count > self.thresholds["failure_count_critical"] else "high"
                    
                    return {
                        "trigger_type": "threshold",
                        "trigger_name": "failure_spike",
                        "severity": severity,
                        "failure_count": failure_count,
                        "total_repair_cost": result[0]['TotalRepairCost'] or 0,
                        "total_downtime_hours": result[0]['TotalDowntime'] or 0,
                        "total_production_loss": result[0]['TotalProductionLoss'] or 0,
                        "investigation_focus": "Failure spike analysis - identify failure patterns and recommend preventive measures",
                        "priority": 1,
                        "triggered_at": datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"Error checking failures: {e}")
        
        return None
    
    def _check_availability_threshold(self) -> Optional[Dict]:
        """Check for low asset availability"""
        try:
            query = f"""
            SELECT 
                AssetID,
                AVG(Availability) as AvgAvailability,
                COUNT(*) as DataPoints
            FROM dbo.AssetPerformanceMetrics
            WHERE Timestamp >= DATEADD(day, -7, GETDATE())
            GROUP BY AssetID
            HAVING AVG(Availability) < {self.thresholds['availability_min']}
            ORDER BY AvgAvailability ASC
            """
            
            low_availability = self.db.execute_query(query)
            
            if low_availability:
                return {
                    "trigger_type": "threshold",
                    "trigger_name": "low_availability",
                    "severity": "high",
                    "asset_count": len(low_availability),
                    "assets": [a['AssetID'] for a in low_availability[:10]],
                    "worst_availability": low_availability[0]['AvgAvailability'],
                    "details": low_availability,
                    "investigation_focus": "Low availability analysis - identify downtime causes and recommend improvements",
                    "priority": 2,
                    "triggered_at": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error checking availability: {e}")
        
        return None
    
    def _check_oee_threshold(self) -> Optional[Dict]:
        """Check for low OEE"""
        try:
            query = f"""
            SELECT
                ProductionLine,
                AVG(OEE) as AvgOEE,
                COUNT(*) as DataPoints
            FROM dbo.ProductionMetrics
            WHERE Date >= DATEADD(day, -30, GETDATE())
            GROUP BY ProductionLine
            HAVING AVG(OEE) < {self.thresholds['oee_min']}
            ORDER BY AvgOEE ASC
            """
            
            low_oee = self.db.execute_query(query)
            
            if low_oee:
                return {
                    "trigger_type": "threshold",
                    "trigger_name": "low_oee",
                    "severity": "medium",
                    "asset_count": len(low_oee),
                    "assets": [a['ProductionLine'] for a in low_oee[:10]],
                    "worst_oee": low_oee[0]['AvgOEE'],
                    "details": low_oee,
                    "investigation_focus": "OEE improvement analysis - identify bottlenecks and recommend optimization",
                    "priority": 3,
                    "triggered_at": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error checking OEE: {e}")
        
        return None
    
    # =========================================================================
    # TRIGGER TYPE 3: PATTERN-BASED TRIGGERS (TREND DETECTION)
    # =========================================================================
    
    def _check_pattern_triggers(self) -> List[Dict]:
        """
        Detect emerging patterns that require attention
        """
        patterns = []
        
        # Pattern 1: Health degradation trend
        degradation = self._detect_health_degradation_pattern()
        if degradation:
            patterns.append(degradation)
        
        # Pattern 2: Cost trend anomaly
        cost_anomaly = self._detect_cost_anomaly_pattern()
        if cost_anomaly:
            patterns.append(cost_anomaly)
        
        # Pattern 3: Increasing failure frequency
        failure_trend = self._detect_failure_frequency_pattern()
        if failure_trend:
            patterns.append(failure_trend)
        
        # Pattern 4: Maintenance cost increase trend
        maint_cost_trend = self._detect_maintenance_cost_trend()
        if maint_cost_trend:
            patterns.append(maint_cost_trend)
        
        return patterns
    
    def _detect_health_degradation_pattern(self) -> Optional[Dict]:
        """Detect assets with declining health trends"""
        try:
            query = f"""
            WITH WeeklyHealth AS (
                SELECT 
                    AssetID,
                    DATEPART(week, Timestamp) as WeekNum,
                    AVG(Availability) as AvgHealth
                FROM dbo.AssetPerformanceMetrics
                WHERE Timestamp >= DATEADD(day, -30, GETDATE())
                GROUP BY AssetID, DATEPART(week, Timestamp)
            ),
            HealthTrends AS (
                SELECT 
                    AssetID,
                    COUNT(DISTINCT WeekNum) as WeekCount,
                    MAX(AvgHealth) - MIN(AvgHealth) as HealthDrop,
                    MIN(AvgHealth) as CurrentHealth,
                    MAX(AvgHealth) as PeakHealth
                FROM WeeklyHealth
                GROUP BY AssetID
            )
            SELECT * FROM HealthTrends
            WHERE HealthDrop > {self.thresholds['degradation_points']}
              AND WeekCount >= 3
            ORDER BY HealthDrop DESC
            """
            
            degrading_assets = self.db.execute_query(query)
            
            if degrading_assets:
                return {
                    "trigger_type": "pattern",
                    "trigger_name": "health_degradation_trend",
                    "severity": "medium",
                    "asset_count": len(degrading_assets),
                    "assets": [a['AssetID'] for a in degrading_assets[:10]],
                    "max_degradation": degrading_assets[0]['HealthDrop'],
                    "details": degrading_assets,
                    "investigation_focus": "Health degradation trend analysis - predict failures and recommend proactive maintenance",
                    "priority": 3,
                    "triggered_at": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error detecting degradation pattern: {e}")
        
        return None
    
    def _detect_cost_anomaly_pattern(self) -> Optional[Dict]:
        """Detect unusual cost patterns using statistical analysis"""
        try:
            query = """
            WITH MonthlyCosts AS (
                SELECT
                    FORMAT(YearMonth, 'yyyy-MM') as Month,
                    SUM(TotalCost) as TotalCost
                FROM dbo.OperatingCosts
                WHERE YearMonth >= DATEADD(month, -6, GETDATE())
                GROUP BY FORMAT(YearMonth, 'yyyy-MM')
            ),
            Stats AS (
                SELECT 
                    AVG(TotalCost) as AvgCost,
                    STDEV(TotalCost) as StdDev
                FROM MonthlyCosts
            )
            SELECT TOP 1
                mc.Month,
                mc.TotalCost,
                s.AvgCost,
                s.StdDev,
                ABS(mc.TotalCost - s.AvgCost) / NULLIF(s.StdDev, 0) as ZScore
            FROM MonthlyCosts mc
            CROSS JOIN Stats s
            WHERE s.StdDev > 0
            ORDER BY mc.Month DESC
            """
            
            result = self.db.execute_query(query)
            
            if result and result[0].get('ZScore'):
                z_score = result[0]['ZScore']
                
                if z_score > self.thresholds["cost_std_dev_multiplier"]:
                    deviation_pct = ((result[0]['TotalCost'] - result[0]['AvgCost']) / result[0]['AvgCost']) * 100
                    
                    return {
                        "trigger_type": "pattern",
                        "trigger_name": "cost_anomaly",
                        "severity": "high" if z_score > 3 else "medium",
                        "current_cost": result[0]['TotalCost'],
                        "avg_cost": result[0]['AvgCost'],
                        "std_dev": result[0]['StdDev'],
                        "z_score": z_score,
                        "deviation_pct": deviation_pct,
                        "month": result[0]['Month'],
                        "investigation_focus": "Cost anomaly investigation - identify unusual expenses and validate legitimacy",
                        "priority": 2 if z_score > 3 else 3,
                        "triggered_at": datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"Error detecting cost anomaly: {e}")
        
        return None
    
    def _detect_failure_frequency_pattern(self) -> Optional[Dict]:
        """Detect increasing failure frequency over time"""
        try:
            query = """
            WITH MonthlyFailures AS (
                SELECT 
                    FORMAT(FailureDate, 'yyyy-MM') as Month,
                    COUNT(*) as FailureCount,
                    AVG(CAST(RepairCost as FLOAT)) as AvgRepairCost
                FROM dbo.FailureEvents
                WHERE FailureDate >= DATEADD(month, -6, GETDATE())
                GROUP BY FORMAT(FailureDate, 'yyyy-MM')
            )
            SELECT 
                Month,
                FailureCount,
                AvgRepairCost,
                LAG(FailureCount, 1) OVER (ORDER BY Month) as PrevMonthCount,
                LAG(FailureCount, 2) OVER (ORDER BY Month) as TwoMonthsAgoCount
            FROM MonthlyFailures
            ORDER BY Month DESC
            """
            
            result = self.db.execute_query(query)
            
            if result and len(result) >= 3:
                latest = result[0]
                
                # Check if failures are increasing
                if (latest['PrevMonthCount'] and latest['TwoMonthsAgoCount'] and
                    latest['FailureCount'] > latest['PrevMonthCount'] and
                    latest['PrevMonthCount'] > latest['TwoMonthsAgoCount']):
                    
                    increase_pct = ((latest['FailureCount'] - latest['TwoMonthsAgoCount']) / 
                                   latest['TwoMonthsAgoCount']) * 100
                    
                    return {
                        "trigger_type": "pattern",
                        "trigger_name": "increasing_failure_frequency",
                        "severity": "high",
                        "current_month_failures": latest['FailureCount'],
                        "prev_month_failures": latest['PrevMonthCount'],
                        "increase_pct": increase_pct,
                        "avg_repair_cost": latest['AvgRepairCost'],
                        "investigation_focus": "Failure frequency trend analysis - identify systemic issues causing increased failures",
                        "priority": 2,
                        "triggered_at": datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"Error detecting failure frequency pattern: {e}")
        
        return None
    
    def _detect_maintenance_cost_trend(self) -> Optional[Dict]:
        """Detect significant increase in maintenance costs"""
        try:
            query = """
            WITH MonthlyCosts AS (
                SELECT
                    FORMAT(CompletionDate, 'yyyy-MM') as Month,
                    SUM(LaborCost + PartsCost + ContractorCost) as TotalCost,
                    COUNT(*) as MaintenanceCount
                FROM dbo.MaintenanceHistory
                WHERE CompletionDate >= DATEADD(month, -6, GETDATE())
                GROUP BY FORMAT(CompletionDate, 'yyyy-MM')
            )
            SELECT 
                Month,
                TotalCost,
                MaintenanceCount,
                LAG(TotalCost, 1) OVER (ORDER BY Month) as PrevMonthCost,
                LAG(TotalCost, 3) OVER (ORDER BY Month) as ThreeMonthsAgoCost
            FROM MonthlyCosts
            ORDER BY Month DESC
            """
            
            result = self.db.execute_query(query)
            
            if result and len(result) >= 4:
                latest = result[0]
                
                if latest['ThreeMonthsAgoCost'] and latest['ThreeMonthsAgoCost'] > 0:
                    increase_pct = ((latest['TotalCost'] - latest['ThreeMonthsAgoCost']) / 
                                   latest['ThreeMonthsAgoCost']) * 100
                    
                    if increase_pct > self.thresholds["maintenance_cost_increase_pct"]:
                        return {
                            "trigger_type": "pattern",
                            "trigger_name": "maintenance_cost_increase",
                            "severity": "medium",
                            "current_cost": latest['TotalCost'],
                            "baseline_cost": latest['ThreeMonthsAgoCost'],
                            "increase_pct": increase_pct,
                            "maintenance_count": latest['MaintenanceCount'],
                            "investigation_focus": "Maintenance cost trend analysis - identify cost drivers and recommend efficiency improvements",
                            "priority": 3,
                            "triggered_at": datetime.now().isoformat()
                        }
        except Exception as e:
            print(f"Error detecting maintenance cost trend: {e}")
        
        return None
    
    # =========================================================================
    # TRIGGER TYPE 4: STRATEGIC GOAL TRIGGERS
    # =========================================================================
    
    def _check_strategic_triggers(self) -> List[Dict]:
        """
        Check strategic goals for issues
        """
        triggers = []
        
        # Check for goals at risk
        at_risk = self._check_goals_at_risk()
        if at_risk:
            triggers.append(at_risk)
        
        # Check for goals falling behind schedule
        behind_schedule = self._check_goals_behind_schedule()
        if behind_schedule:
            triggers.append(behind_schedule)
        
        return triggers
    
    def _check_goals_at_risk(self) -> Optional[Dict]:
        """Check for strategic goals that are at risk"""
        try:
            query = """
            SELECT
                GoalID,
                GoalName,
                Category,
                Status,
                TargetValue,
                CurrentValue,
                Unit,
                TargetDate,
                Owner
            FROM dbo.StrategicGoals
            WHERE Status IN ('Behind', 'At Risk')
              AND TargetDate >= GETDATE()
            ORDER BY TargetDate ASC
            """

            at_risk_goals = self.db.execute_query(query)

            if at_risk_goals:
                return {
                    "trigger_type": "strategic",
                    "trigger_name": "goals_at_risk",
                    "severity": "high",
                    "goal_count": len(at_risk_goals),
                    "goals": at_risk_goals,
                    "categories_affected": list(set([g['Category'] for g in at_risk_goals])),
                    "investigation_focus": "Strategic goal achievement analysis - identify barriers and recommend corrective actions",
                    "priority": 2,
                    "triggered_at": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error checking strategic goals: {e}")
        
        return None
    
    def _check_goals_behind_schedule(self) -> Optional[Dict]:
        """Check for goals that are falling behind schedule"""
        try:
            query = """
            SELECT
                GoalID,
                GoalName,
                Category,
                Status,
                TargetValue,
                CurrentValue,
                TargetDate,
                Owner,
                DATEDIFF(day, GETDATE(), TargetDate) as DaysRemaining
            FROM dbo.StrategicGoals
            WHERE Status = 'Behind'
              AND TargetDate >= GETDATE()
            """

            behind_goals = self.db.execute_query(query)

            if behind_goals:
                return {
                    "trigger_type": "strategic",
                    "trigger_name": "goals_behind_schedule",
                    "severity": "high",
                    "goal_count": len(behind_goals),
                    "goals": behind_goals,
                    "investigation_focus": "Behind schedule goals analysis - identify delays and recommend acceleration plans",
                    "priority": 2,
                    "triggered_at": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error checking behind schedule goals: {e}")
        
        return None
    
    # =========================================================================
    # TRIGGER TYPE 5: USER-REQUESTED TRIGGERS
    # =========================================================================
    
    def create_user_request_trigger(
        self, 
        focus_area: str, 
        details: Optional[Dict] = None,
        priority: int = 1
    ) -> Dict:
        """
        Create a user-requested investigation trigger
        
        Args:
            focus_area: What the user wants investigated
            details: Additional context
            priority: Urgency (1=highest, 5=lowest)
        """
        trigger = {
            "trigger_type": "user_request",
            "trigger_name": "user_requested_investigation",
            "severity": "user_defined",
            "focus_area": focus_area,
            "details": details or {},
            "investigation_focus": focus_area,
            "priority": priority,
            "triggered_at": datetime.now().isoformat(),
            "requested_by": details.get("user_id", "unknown") if details else "unknown"
        }
        
        # Record in history
        self._record_triggered_event(trigger)
        self._save_trigger_history()
        
        return trigger
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _record_triggered_event(self, event: Dict):
        """Record triggered event in history"""
        self.trigger_history["triggered_events"].append({
            "timestamp": datetime.now().isoformat(),
            "event": event
        })
        
        # Keep only last 1000 events
        if len(self.trigger_history["triggered_events"]) > 1000:
            self.trigger_history["triggered_events"] = self.trigger_history["triggered_events"][-1000:]
    
    def get_trigger_summary(self) -> Dict:
        """Get summary of trigger system status"""
        recent_24h = [
            e for e in self.trigger_history["triggered_events"]
            if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(hours=24)
        ]
        
        trigger_type_counts = {}
        for event in recent_24h:
            t_type = event["event"]["trigger_type"]
            trigger_type_counts[t_type] = trigger_type_counts.get(t_type, 0) + 1
        
        return {
            "total_triggers_24h": len(recent_24h),
            "trigger_type_breakdown": trigger_type_counts,
            "last_checks": self.trigger_history["last_checks"],
            "config": self.config
        }
    
    def should_investigate(self) -> bool:
        """
        Simple check: should we investigate now?
        """
        triggered_events = self.check_all_triggers()
        return len(triggered_events) > 0
    
    def get_investigation_focus(self, triggered_events: List[Dict]) -> str:
        """
        Determine investigation focus based on highest priority trigger
        """
        if not triggered_events:
            return "General system health check"
        
        # Sort by priority (1 = highest)
        triggered_events.sort(key=lambda x: x.get('priority', 999))
        
        # Return focus from highest priority trigger
        return triggered_events[0].get('investigation_focus', 'System analysis')