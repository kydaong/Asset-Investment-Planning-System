"""
Populate AssetPerformanceMetrics and StrategicGoals tables
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SQLServerConnection
from datetime import datetime, timedelta
import random
import math

def populate_asset_performance_metrics(db, num_rows=500):
    """
    Populate AssetPerformanceMetrics with time-series performance data
    """
    print(f"\nPopulating AssetPerformanceMetrics table with {num_rows} rows...")
    
    # Get assets
    assets = db.execute_query("""
        SELECT AssetID, AssetType, Criticality 
        FROM dbo.Assets 
        WHERE Status = 'Operating'
    """)
    
    if not assets:
        print("  ⚠ No operating assets found")
        return
    
    asset_ids = [a['AssetID'] for a in assets]
    
    # Generate time-series data for past 60 days
    days_back = 60
    records_per_day = max(1, num_rows // (len(asset_ids) * days_back))
    
    record_count = 0
    
    for asset in assets[:min(10, len(assets))]:  # Focus on first 10 assets for 500 rows
        asset_id = asset['AssetID']
        asset_type = asset['AssetType']
        criticality = asset['Criticality']
        
        # Base performance varies by criticality
        if criticality == 'Critical':
            base_availability = random.uniform(95, 99)
            base_reliability = random.uniform(92, 98)
            base_efficiency = random.uniform(88, 95)
        elif criticality == 'High':
            base_availability = random.uniform(90, 97)
            base_reliability = random.uniform(85, 95)
            base_efficiency = random.uniform(82, 92)
        else:
            base_availability = random.uniform(85, 95)
            base_reliability = random.uniform(80, 92)
            base_efficiency = random.uniform(75, 88)
        
        # Generate daily records
        for day in range(days_back):
            if record_count >= num_rows:
                break
                
            timestamp = datetime.now() - timedelta(days=day, hours=random.randint(0, 23))
            
            # Add some degradation trend over time (older = slightly worse)
            degradation_factor = 1 - (day / 365) * 0.05  # 5% degradation per year
            
            # Add daily variation
            daily_variation = random.uniform(0.95, 1.05)
            
            availability = min(100, base_availability * degradation_factor * daily_variation)
            reliability = min(100, base_reliability * degradation_factor * daily_variation)
            efficiency = min(100, base_efficiency * degradation_factor * daily_variation)
            utilization = random.uniform(70, 95) * degradation_factor
            
            # Asset-type specific parameters
            if asset_type == 'Compressor':
                vibration = random.uniform(3, 12) * (1 + (100 - availability) / 200)
                temperature = random.uniform(45, 85)
                pressure = random.uniform(8, 15)
                flow_rate = random.uniform(800, 1500) * (efficiency / 100)
                power_consumption = random.uniform(200, 500)
            elif asset_type == 'Pump':
                vibration = random.uniform(2, 8) * (1 + (100 - availability) / 200)
                temperature = random.uniform(40, 70)
                pressure = random.uniform(5, 20)
                flow_rate = random.uniform(50, 200) * (efficiency / 100)
                power_consumption = random.uniform(50, 150)
            elif asset_type == 'Heat Exchanger':
                vibration = random.uniform(1, 3)
                temperature = random.uniform(60, 120)
                pressure = random.uniform(3, 10)
                flow_rate = random.uniform(100, 500)
                power_consumption = random.uniform(10, 50)
            else:  # Generic
                vibration = random.uniform(2, 10)
                temperature = random.uniform(40, 80)
                pressure = random.uniform(5, 15)
                flow_rate = random.uniform(100, 1000)
                power_consumption = random.uniform(50, 300)
            
            energy_efficiency = efficiency * random.uniform(0.9, 1.1)
            run_hours = random.uniform(20, 24) * (availability / 100)
            cycle_count = random.randint(0, 5)
            alarm_count = random.randint(0, 3) if availability < 90 else random.randint(0, 1)
            
            # Calculate health score (composite)
            health_score = (availability * 0.3 + reliability * 0.3 + efficiency * 0.2 + 
                           (100 - min(vibration * 5, 100)) * 0.1 + 
                           (100 - alarm_count * 10) * 0.1)
            
            # Performance index
            performance_index = (efficiency * utilization * availability) / 10000
            
            query = f"""
            INSERT INTO dbo.AssetPerformanceMetrics
            (AssetID, Timestamp, Availability, Efficiency,
             Vibration, Temperature, Pressure, FlowRate, PowerConsumption, Runtime)
            VALUES
            ('{asset_id}',
             '{timestamp.strftime("%Y-%m-%d %H:%M:%S")}',
             {availability:.2f}, {efficiency:.2f},
             {vibration:.3f}, {temperature:.2f}, {pressure:.2f}, {flow_rate:.2f},
             {power_consumption:.2f}, {run_hours:.2f})
            """

            db.execute_write(query)
            record_count += 1
            
            if record_count % 100 == 0:
                print(f"  Inserted {record_count} performance metrics...")
        
        if record_count >= num_rows:
            break
    
    print(f"✓ Completed: {record_count} performance metrics inserted")


def populate_strategic_goals(db, num_rows=500):
    """
    Populate StrategicGoals with corporate objectives
    """
    print(f"\nPopulating StrategicGoals table with {num_rows} rows...")
    
    categories = ['Reliability', 'Efficiency', 'Cost', 'Safety', 'Environmental', 'Production']
    priorities = ['Critical', 'High', 'Medium', 'Low']
    statuses = ['On Track', 'At Risk', 'Behind', 'Achieved']
    impact_areas = ['Plant-wide', 'Unit-1', 'Unit-2', 'Unit-3', 'Utilities']
    owners = ['Plant Manager', 'Maintenance Manager', 'Operations Manager', 
              'Safety Manager', 'Engineering Manager', 'Finance Director']
    
    # Predefined goal templates
    goal_templates = [
        # Reliability goals
        {'name': 'Improve Overall Equipment Availability', 'category': 'Reliability', 'unit': '%', 
         'target': (95, 99), 'current': (85, 95)},
        {'name': 'Reduce Unplanned Downtime Hours', 'category': 'Reliability', 'unit': 'hours',
         'target': (50, 150), 'current': (100, 300)},
        {'name': 'Increase Mean Time Between Failures', 'category': 'Reliability', 'unit': 'days',
         'target': (180, 365), 'current': (90, 180)},
        {'name': 'Achieve 99% Equipment Reliability', 'category': 'Reliability', 'unit': '%',
         'target': (98, 99.5), 'current': (92, 97)},
        
        # Efficiency goals
        {'name': 'Improve Plant Overall Equipment Effectiveness', 'category': 'Efficiency', 'unit': '%',
         'target': (85, 92), 'current': (75, 85)},
        {'name': 'Reduce Energy Consumption per Unit', 'category': 'Efficiency', 'unit': 'kWh/unit',
         'target': (50, 80), 'current': (80, 120)},
        {'name': 'Increase Production Throughput', 'category': 'Efficiency', 'unit': 'units/day',
         'target': (8000, 12000), 'current': (6000, 9000)},
        {'name': 'Reduce Waste Generation', 'category': 'Efficiency', 'unit': '%',
         'target': (2, 5), 'current': (5, 10)},
        
        # Cost goals
        {'name': 'Reduce Maintenance Costs', 'category': 'Cost', 'unit': '$',
         'target': (500000, 1000000), 'current': (1000000, 2000000)},
        {'name': 'Optimize Spare Parts Inventory', 'category': 'Cost', 'unit': '$',
         'target': (200000, 500000), 'current': (500000, 1000000)},
        {'name': 'Reduce Total Cost of Ownership', 'category': 'Cost', 'unit': '$',
         'target': (5000000, 10000000), 'current': (8000000, 15000000)},
        {'name': 'Improve Cost per Unit Produced', 'category': 'Cost', 'unit': '$/unit',
         'target': (50, 100), 'current': (100, 150)},
        
        # Safety goals
        {'name': 'Achieve Zero Lost Time Incidents', 'category': 'Safety', 'unit': 'incidents',
         'target': (0, 0), 'current': (1, 5)},
        {'name': 'Reduce Total Recordable Incident Rate', 'category': 'Safety', 'unit': 'per 200k hrs',
         'target': (0.5, 1.0), 'current': (1.5, 3.0)},
        {'name': 'Complete Safety Training for All Staff', 'category': 'Safety', 'unit': '%',
         'target': (100, 100), 'current': (80, 95)},
        
        # Environmental goals
        {'name': 'Reduce Carbon Emissions', 'category': 'Environmental', 'unit': 'tons CO2',
         'target': (5000, 10000), 'current': (15000, 25000)},
        {'name': 'Increase Water Recycling Rate', 'category': 'Environmental', 'unit': '%',
         'target': (70, 90), 'current': (50, 70)},
        {'name': 'Achieve Zero Environmental Incidents', 'category': 'Environmental', 'unit': 'incidents',
         'target': (0, 0), 'current': (1, 3)},
        
        # Production goals
        {'name': 'Meet Annual Production Target', 'category': 'Production', 'unit': 'units',
         'target': (3000000, 5000000), 'current': (2500000, 4000000)},
        {'name': 'Improve First Pass Yield', 'category': 'Production', 'unit': '%',
         'target': (95, 99), 'current': (88, 94)},
        {'name': 'Reduce Product Quality Defects', 'category': 'Production', 'unit': '%',
         'target': (0.5, 2), 'current': (2, 5)},
    ]
    
    # Get some asset IDs for asset-specific goals
    assets = db.execute_query("SELECT TOP 50 AssetID FROM dbo.Assets")
    asset_ids = [a['AssetID'] for a in assets]
    
    record_count = 0
    
    while record_count < num_rows:
        template = random.choice(goal_templates)
        
        # Generate unique goal name
        goal_name = template['name']
        if record_count > 20:  # Add variations for uniqueness
            variations = ['Phase 1', 'Phase 2', 'Q1', 'Q2', 'Q3', 'Q4', '2025', '2026']
            goal_name = f"{template['name']} - {random.choice(variations)}"
        
        category = template['category']
        unit = template['unit']
        
        # Generate target and current values
        target_range = template['target']
        current_range = template['current']
        
        # For cost/reduction goals, target < current
        if category in ['Cost'] or 'Reduce' in goal_name:
            target_value = random.uniform(*target_range)
            current_value = random.uniform(target_value, max(current_range))
        else:  # For improvement goals, target > current
            target_value = random.uniform(*target_range)
            current_value = random.uniform(min(current_range), min(target_value, max(current_range)))
        
        # Calculate progress
        if target_value > current_value:
            progress = (current_value / target_value) * 100
        elif target_value < current_value and current_value > 0:
            progress = (target_value / current_value) * 100
        else:
            progress = 100 if abs(target_value - current_value) < 0.01 else 50
        
        progress = min(100, max(0, progress))
        
        # Determine status based on progress
        if progress >= 95:
            status = 'Achieved'
        elif progress >= 80:
            status = 'On Track'
        elif progress >= 60:
            status = 'At Risk'
        else:
            status = 'Behind'
        
        # Set dates
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        target_date = start_date + timedelta(days=random.randint(180, 720))
        last_review = datetime.now() - timedelta(days=random.randint(1, 30))
        
        # Priority based on category and status
        if category in ['Safety', 'Environmental'] or status == 'Behind':
            priority = random.choice(['Critical', 'High'])
        else:
            priority = random.choice(priorities)
        
        # Impact area and related assets
        impact_area = random.choice(impact_areas)
        related_assets = ''
        if random.random() > 0.6:  # 40% are asset-specific
            num_assets = random.randint(1, 5)
            related_assets = ', '.join(random.sample(asset_ids, min(num_assets, len(asset_ids))))
        
        description = f"Strategic goal to {goal_name.lower()} from {current_value:.2f} to {target_value:.2f} {unit}"
        
        notes = f"Last reviewed on {last_review.strftime('%Y-%m-%d')}. "
        if status == 'Behind':
            notes += "Requires immediate attention and resource allocation."
        elif status == 'At Risk':
            notes += "Monitoring closely, may need additional support."
        elif status == 'On Track':
            notes += "Progressing as planned."
        else:
            notes += "Goal successfully achieved ahead of schedule."
        
        query = f"""
        INSERT INTO dbo.StrategicGoals
        (GoalName, MetricName, TargetValue, CurrentValue, Unit,
         TargetDate, Category, Status, Owner)
        VALUES
        ('{goal_name.replace("'", "''")}',
         '{category} Metric',
         {target_value:.2f},
         {current_value:.2f},
         '{unit}',
         '{target_date.strftime("%Y-%m-%d")}',
         '{category}',
         '{status}',
         '{random.choice(owners)}')
        """

        db.execute_write(query)
        record_count += 1
        
        if record_count % 100 == 0:
            print(f"  Inserted {record_count} strategic goals...")
    
    print(f"✓ Completed: {record_count} strategic goals inserted")


def main():
    print("=" * 70)
    print("Populate Additional Tables - Asset Performance & Strategic Goals")
    print("=" * 70)
    
    try:
        db = SQLServerConnection()
        
        if not db.test_connection():
            print("✗ Database connection failed!")
            return
        
        print("\nStarting data population...")
        
        populate_asset_performance_metrics(db, 500)
        populate_strategic_goals(db, 500)
        
        print("\n" + "=" * 70)
        print("✓ Additional tables populated successfully!")
        print("=" * 70)
        
        # Show summary
        print("\nTable Summary:")
        count1 = db.get_row_count('dbo.AssetPerformanceMetrics')
        count2 = db.get_row_count('dbo.StrategicGoals')
        print(f"  AssetPerformanceMetrics: {count1:,} rows")
        print(f"  StrategicGoals: {count2:,} rows")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()