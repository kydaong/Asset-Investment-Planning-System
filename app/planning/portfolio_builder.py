"""
Portfolio Builder - Constructs candidate project portfolios from database
"""
from typing import List, Dict, Any, Optional
from app.core.database import SQLServerConnection

class PortfolioBuilder:
    """
    Builds candidate project portfolios from asset and operational data
    """
    
    def __init__(self):
        self.db = SQLServerConnection()
    
    def get_candidate_projects(self) -> List[Dict]:
        """
        Get all candidate projects from database
        Tries CapitalProjects table first, falls back to generating from assets
        """
        
        # Try to get from CapitalProjects table
        try:
            query = """
            SELECT 
                ProjectID,
                ProjectName,
                AssetID,
                ProjectType,
                EstimatedCost,
                EstimatedBenefit,
                NPV,
                IRR,
                RiskLevel,
                Priority,
                Status,
                Description
            FROM dbo.CapitalProjects
            WHERE Status IN ('Proposed', 'Under Review', 'Approved')
            ORDER BY Priority DESC, NPV DESC
            """
            
            projects = self.db.execute_query(query)
            
            if projects and len(projects) > 0:
                # Normalize field names
                return self._normalize_projects(projects)
        
        except Exception as e:
            print(f"CapitalProjects table not found or error: {e}")
        
        # Fallback: Generate projects from assets
        return self._generate_projects_from_assets()
    
    def _generate_projects_from_assets(self) -> List[Dict]:
        """
        Generate candidate projects from assets that need investment
        Based on health scores, costs, failures, and criticality
        """
        
        # Get assets needing attention
        query = """
        WITH AssetMetrics AS (
            SELECT
                a.AssetID,
                a.AssetName,
                a.AssetType,
                a.Criticality,
                a.InstallationDate,
                a.DesignLife,
                AVG(apm.Availability) as AvgAvailability,
                MIN(apm.Availability) as MinAvailability,
                AVG(apm.Vibration) as AvgVibration,
                AVG(apm.Temperature) as AvgTemperature
            FROM dbo.Assets a
            LEFT JOIN dbo.AssetPerformanceMetrics apm
                ON a.AssetID = apm.AssetID
                AND apm.Timestamp >= DATEADD(day, -30, GETDATE())
            WHERE a.Status = 'Operating'
            GROUP BY a.AssetID, a.AssetName, a.AssetType, a.Criticality, a.InstallationDate, a.DesignLife
        ),
        AssetCosts AS (
            SELECT
                AssetID,
                SUM(LaborCost + PartsCost + ContractorCost) as YTDMaintenanceCost,
                COUNT(*) as MaintenanceCount
            FROM dbo.MaintenanceHistory
            WHERE CompletionDate >= DATEADD(year, -1, GETDATE())
            GROUP BY AssetID
        ),
        AssetFailures AS (
            SELECT 
                AssetID,
                COUNT(*) as FailureCount,
                SUM(RepairCost) as TotalRepairCost,
                SUM(DowntimeHours) as TotalDowntime
            FROM dbo.FailureEvents
            WHERE FailureDate >= DATEADD(year, -1, GETDATE())
            GROUP BY AssetID
        )
        SELECT 
            am.AssetID,
            am.AssetName,
            am.AssetType,
            am.Criticality,
            am.AvgAvailability,
            am.MinAvailability,
            am.AvgVibration,
            am.AvgTemperature,
            DATEDIFF(year, am.InstallationDate, GETDATE()) as AssetAge,
            am.DesignLife,
            ISNULL(ac.YTDMaintenanceCost, 0) as YTDMaintenanceCost,
            ISNULL(ac.MaintenanceCount, 0) as MaintenanceCount,
            ISNULL(af.FailureCount, 0) as FailureCount,
            ISNULL(af.TotalRepairCost, 0) as TotalRepairCost,
            ISNULL(af.TotalDowntime, 0) as TotalDowntime
        FROM AssetMetrics am
        LEFT JOIN AssetCosts ac ON am.AssetID = ac.AssetID
        LEFT JOIN AssetFailures af ON am.AssetID = af.AssetID
        WHERE
            am.AvgAvailability < 80                        -- Poor availability
            OR ISNULL(ac.YTDMaintenanceCost, 0) > 50000   -- High maintenance cost
            OR ISNULL(af.FailureCount, 0) > 2             -- Multiple failures
            OR DATEDIFF(year, am.InstallationDate, GETDATE()) > am.DesignLife  -- Beyond design life
        ORDER BY
            CASE am.Criticality
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                ELSE 3
            END,
            am.AvgAvailability ASC,
            ISNULL(ac.YTDMaintenanceCost, 0) DESC
        """
        
        assets = self.db.execute_query(query)
        
        if not assets:
            return []
        
        # Convert assets to projects
        projects = []
        
        for i, asset in enumerate(assets[:40], 1):  # Limit to top 40 candidates
            project = self._asset_to_project(asset, i)
            projects.append(project)
        
        return projects
    
    def _asset_to_project(self, asset: Dict, project_num: int) -> Dict:
        """
        Convert an asset into a candidate capital project
        """
        
        asset_id = asset['AssetID']
        asset_name = asset['AssetName']
        asset_type = asset['AssetType']
        health = float(asset.get('AvgAvailability') or 75)
        age = int(asset.get('AssetAge') or 10)
        maintenance_cost = float(asset.get('YTDMaintenanceCost') or 0)
        failure_count = int(asset.get('FailureCount') or 0)
        criticality = asset.get('Criticality', 'Medium')
        
        # Estimate replacement cost based on asset type
        base_costs = {
            'Compressor': 2500000,
            'Pump': 800000,
            'Heat Exchanger': 1200000,
            'Reactor': 3500000,
            'Turbine': 4000000,
            'Motor': 150000,
            'Valve': 50000,
            'Tank': 600000,
            'Separator': 900000,
            'Boiler': 2000000
        }
        
        estimated_cost = float(base_costs.get(asset_type, 500000))
        
        # Adjust cost based on criticality
        if criticality == 'Critical':
            estimated_cost *= 1.2  # Critical assets need more robust solutions
        
        # Estimate NPV based on maintenance savings + downtime reduction
        annual_savings = maintenance_cost * 0.6  # 60% reduction in maintenance
        downtime_reduction_value = failure_count * 50000  # $50K per failure prevented
        annual_benefit = annual_savings + downtime_reduction_value
        
        # Simple NPV calculation (5-year horizon, 10% discount rate)
        years = 5
        discount_rate = 0.10
        npv = sum(annual_benefit / ((1 + discount_rate) ** year) for year in range(1, years + 1))
        npv -= estimated_cost
        
        # IRR approximation
        irr = (annual_benefit / estimated_cost) * 100 if estimated_cost > 0 else 0
        
        # Determine project type
        if health < 60:
            project_type = "Emergency Replacement"
            priority = "Critical"
            risk_level = "High"
        elif age > asset.get('DesignLife', 20):
            project_type = "End-of-Life Replacement"
            priority = "High" if criticality in ['Critical', 'High'] else "Medium"
            risk_level = "Medium"
        elif failure_count > 3:
            project_type = "Reliability Improvement"
            priority = "High"
            risk_level = "Medium"
        else:
            project_type = "Preventive Replacement"
            priority = "Medium"
            risk_level = "Low"
        
        return {
            "project_id": f"PROJ-{project_num:03d}",
            "project_name": f"Replace {asset_name}",
            "asset_id": asset_id,
            "asset_name": asset_name,
            "asset_type": asset_type,
            "project_type": project_type,
            "estimated_cost": round(estimated_cost, 0),
            "estimated_benefit": round(annual_benefit * years, 0),
            "npv": round(npv, 0),
            "irr": round(irr, 1),
            "risk_level": risk_level,
            "priority": priority,
            "status": "Proposed",
            "description": self._generate_project_description(asset, project_type),
            "health_score": round(health, 1),
            "asset_age": age,
            "failure_count": failure_count,
            "maintenance_cost": round(maintenance_cost, 0),
            "criticality": criticality
        }
    
    def _generate_project_description(self, asset: Dict, project_type: str) -> str:
        """Generate project description based on asset condition"""
        
        asset_name = asset['AssetName']
        health = asset.get('AvgAvailability', 75)
        age = asset.get('AssetAge', 10)
        failures = asset.get('FailureCount', 0)
        
        if project_type == "Emergency Replacement":
            return f"{asset_name} showing critical health score of {health:.1f}. Immediate replacement required to prevent catastrophic failure."
        
        elif project_type == "End-of-Life Replacement":
            return f"{asset_name} is {age} years old, exceeding design life. Replacement recommended to avoid reliability issues."
        
        elif project_type == "Reliability Improvement":
            return f"{asset_name} has experienced {failures} failures in past year. Replacement will improve reliability and reduce downtime."
        
        else:
            return f"Preventive replacement of {asset_name} to maintain operational efficiency and avoid future issues."
    
    def _normalize_projects(self, projects: List[Dict]) -> List[Dict]:
        """Normalize project field names to standard format"""
        normalized = []
        
        for p in projects:
            normalized.append({
                "project_id": p.get("ProjectID"),
                "project_name": p.get("ProjectName"),
                "asset_id": p.get("AssetID"),
                "project_type": p.get("ProjectType"),
                "estimated_cost": p.get("EstimatedCost", 0),
                "estimated_benefit": p.get("EstimatedBenefit", 0),
                "npv": p.get("NPV", 0),
                "irr": p.get("IRR", 0),
                "risk_level": p.get("RiskLevel", "Medium"),
                "priority": p.get("Priority", "Medium"),
                "status": p.get("Status", "Proposed"),
                "description": p.get("Description", "")
            })
        
        return normalized
    
    def filter_projects(
        self,
        projects: List[Dict],
        filters: Dict
    ) -> List[Dict]:
        """
        Filter projects based on criteria
        
        Args:
            projects: List of projects
            filters: Dictionary of filters
                - min_npv: Minimum NPV
                - max_cost: Maximum cost
                - priority: List of acceptable priorities
                - project_type: List of acceptable types
                - risk_level: List of acceptable risk levels
        """
        filtered = projects
        
        if "min_npv" in filters:
            filtered = [p for p in filtered if p.get("npv", 0) >= filters["min_npv"]]
        
        if "max_cost" in filters:
            filtered = [p for p in filtered if p.get("estimated_cost", 0) <= filters["max_cost"]]
        
        if "priority" in filters:
            allowed_priorities = filters["priority"] if isinstance(filters["priority"], list) else [filters["priority"]]
            filtered = [p for p in filtered if p.get("priority") in allowed_priorities]
        
        if "project_type" in filters:
            allowed_types = filters["project_type"] if isinstance(filters["project_type"], list) else [filters["project_type"]]
            filtered = [p for p in filtered if p.get("project_type") in allowed_types]
        
        if "risk_level" in filters:
            allowed_risks = filters["risk_level"] if isinstance(filters["risk_level"], list) else [filters["risk_level"]]
            filtered = [p for p in filtered if p.get("risk_level") in allowed_risks]
        
        return filtered