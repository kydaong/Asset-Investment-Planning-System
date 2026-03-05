"""
Populate database tables with realistic synthetic data
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import SQLServerConnection
from datetime import datetime, timedelta
import random


def populate_assets(db, num_rows=500):
    """Populate Assets table"""
    print(f"\nPopulating Assets table with {num_rows} rows...")

    asset_types = ['Compressor', 'Pump', 'Heat Exchanger', 'Reactor', 'Separator', 'Turbine', 'Motor', 'Valve']
    locations = ['Unit-1', 'Unit-2', 'Unit-3', 'Utilities', 'Storage']
    departments = ['Production', 'Utilities', 'Maintenance']
    manufacturers = ['Atlas Copco', 'Siemens', 'GE', 'Sulzer', 'KSB', 'Flowserve', 'Yokogawa']
    criticalities = ['Critical', 'High', 'Medium', 'Low']
    statuses = ['Operating', 'Maintenance', 'Standby']

    for i in range(1, num_rows + 1):
        asset_type = random.choice(asset_types)
        asset_id = f"{asset_type[:3].upper()}-{i:04d}"
        install_date = datetime.now() - timedelta(days=random.randint(365, 3650))
        criticality = random.choices(criticalities, weights=[10, 30, 40, 20])[0]
        status = random.choices(statuses, weights=[85, 10, 5])[0]
        replacement_cost = round(random.uniform(10000, 2000000), 2)

        query = f"""
        INSERT INTO dbo.Assets
        (AssetID, AssetName, AssetType, Manufacturer, ModelNumber, SerialNumber,
         InstallationDate, DesignLife, Criticality, ReplacementCost, Location, Department, Status)
        VALUES
        ('{asset_id}',
         '{asset_type} {i}',
         '{asset_type}',
         '{random.choice(manufacturers)}',
         'MDL-{random.randint(1000, 9999)}',
         'SN-{random.randint(10000, 99999)}',
         '{install_date.strftime("%Y-%m-%d")}',
         {random.choice([15, 20, 25, 30])},
         '{criticality}',
         {replacement_cost},
         '{random.choice(locations)}',
         '{random.choice(departments)}',
         '{status}')
        """
        db.execute_write(query)

        if i % 100 == 0:
            print(f"  Inserted {i} assets...")

    print(f"✓ Completed: {num_rows} assets inserted")


def populate_maintenance_history(db, num_rows=500):
    """Populate MaintenanceHistory table"""
    print(f"\nPopulating MaintenanceHistory table with {num_rows} rows...")

    assets = db.execute_query("SELECT AssetID FROM dbo.Assets")
    asset_ids = [a['AssetID'] for a in assets]

    maintenance_types = ['Preventive', 'Corrective', 'Predictive', 'Emergency']
    technicians = ['John Smith', 'Mary Johnson', 'David Lee', 'Sarah Chen', 'Mike Wilson']
    statuses = ['Completed', 'In Progress', 'Scheduled']
    failure_modes = ['Bearing failure', 'Seal leakage', 'Motor burnout', 'Valve sticking', None, None, None]

    for i in range(1, num_rows + 1):
        asset_id = random.choice(asset_ids)
        maintenance_type = random.choice(maintenance_types)
        scheduled_date = datetime.now() - timedelta(days=random.randint(0, 365))
        start_date = scheduled_date + timedelta(days=random.randint(-2, 5))
        completion_date = start_date + timedelta(hours=random.uniform(1, 24))
        downtime = random.uniform(0, 36)
        labor_cost = round(random.uniform(500, 5000), 2)
        parts_cost = round(random.uniform(0, 10000), 2)
        contractor_cost = round(random.uniform(0, 8000), 2)
        status = random.choices(statuses, weights=[80, 15, 5])[0]
        failure_mode = random.choice(failure_modes)
        failure_val = f"'{failure_mode}'" if failure_mode else 'NULL'

        query = f"""
        INSERT INTO dbo.MaintenanceHistory
        (AssetID, WorkOrderNumber, MaintenanceType, Description, ScheduledDate,
         StartDate, CompletionDate, DowntimeHours, LaborCost, PartsCost,
         ContractorCost, Technician, Status, FailureMode)
        VALUES
        ('{asset_id}',
         'WO-{i:05d}-{random.randint(100, 999)}',
         '{maintenance_type}',
         '{maintenance_type} maintenance on {asset_id}',
         '{scheduled_date.strftime("%Y-%m-%d")}',
         '{start_date.strftime("%Y-%m-%d %H:%M:%S")}',
         '{completion_date.strftime("%Y-%m-%d %H:%M:%S")}',
         {downtime:.2f},
         {labor_cost},
         {parts_cost},
         {contractor_cost},
         '{random.choice(technicians)}',
         '{status}',
         {failure_val})
        """
        db.execute_write(query)

        if i % 100 == 0:
            print(f"  Inserted {i} maintenance records...")

    print(f"✓ Completed: {num_rows} maintenance records inserted")


def populate_failure_events(db, num_rows=500):
    """Populate FailureEvents table"""
    print(f"\nPopulating FailureEvents table with {num_rows} rows...")

    assets = db.execute_query("SELECT AssetID FROM dbo.Assets")
    asset_ids = [a['AssetID'] for a in assets]

    failure_modes = ['Mechanical', 'Electrical', 'Control', 'Instrumentation']
    severities = ['Critical', 'Major', 'Minor']
    root_causes = [
        'Normal wear and tear', 'Inadequate lubrication', 'Contamination',
        'Improper installation', 'Operating beyond design limits',
        'Age-related degradation', 'Poor maintenance', 'Material defect'
    ]
    corrective_actions = [
        'Replaced component', 'Increased inspection frequency',
        'Updated maintenance procedure', 'Installed monitoring sensor',
        'Retrained technicians', 'Upgraded to better material'
    ]

    for i in range(1, num_rows + 1):
        asset_id = random.choice(asset_ids)
        failure_date = datetime.now() - timedelta(days=random.randint(0, 730))
        severity = random.choices(severities, weights=[10, 30, 60])[0]

        if severity == 'Critical':
            downtime = random.uniform(24, 168)
            repair_cost = random.uniform(50000, 200000)
            production_loss = random.uniform(100000, 500000)
        elif severity == 'Major':
            downtime = random.uniform(8, 48)
            repair_cost = random.uniform(10000, 50000)
            production_loss = random.uniform(20000, 100000)
        else:
            downtime = random.uniform(1, 12)
            repair_cost = random.uniform(2000, 15000)
            production_loss = random.uniform(5000, 30000)

        mtbf = random.randint(30, 365)

        query = f"""
        INSERT INTO dbo.FailureEvents
        (AssetID, FailureDate, FailureMode, Severity, DowntimeHours,
         ProductionLoss, RepairCost, RootCause, CorrectiveActions, MTBF)
        VALUES
        ('{asset_id}',
         '{failure_date.strftime("%Y-%m-%d %H:%M:%S")}',
         '{random.choice(failure_modes)}',
         '{severity}',
         {downtime:.2f},
         {production_loss:.2f},
         {repair_cost:.2f},
         '{random.choice(root_causes)}',
         '{random.choice(corrective_actions)}',
         {mtbf})
        """
        db.execute_write(query)

        if i % 100 == 0:
            print(f"  Inserted {i} failure events...")

    print(f"✓ Completed: {num_rows} failure events inserted")


def populate_operating_costs(db, num_rows=500):
    """Populate OperatingCosts table"""
    print(f"\nPopulating OperatingCosts table with {num_rows} rows...")

    assets = db.execute_query("SELECT AssetID FROM dbo.Assets")
    asset_ids = [a['AssetID'] for a in assets]

    for i in range(1, num_rows + 1):
        asset_id = random.choice(asset_ids)
        year_month = datetime.now() - timedelta(days=random.randint(0, 365))
        energy = round(random.uniform(1000, 10000), 2)
        maintenance = round(random.uniform(500, 15000), 2)
        labor = round(random.uniform(1000, 8000), 2)
        materials = round(random.uniform(200, 5000), 2)
        contractor = round(random.uniform(0, 10000), 2)
        other = round(random.uniform(0, 2000), 2)
        budgeted = round((energy + maintenance + labor + materials + contractor + other) * random.uniform(0.9, 1.2), 2)

        query = f"""
        INSERT INTO dbo.OperatingCosts
        (AssetID, YearMonth, EnergyCost, MaintenanceCost, LaborCost,
         MaterialsCost, ContractorCost, OtherCost, BudgetedCost)
        VALUES
        ('{asset_id}',
         '{year_month.strftime("%Y-%m-01")}',
         {energy}, {maintenance}, {labor},
         {materials}, {contractor}, {other}, {budgeted})
        """
        db.execute_write(query)

        if i % 100 == 0:
            print(f"  Inserted {i} cost records...")

    print(f"✓ Completed: {num_rows} operating cost records inserted")


def populate_production_metrics(db, num_rows=500):
    """Populate ProductionMetrics table"""
    print(f"\nPopulating ProductionMetrics table with {num_rows} rows...")

    production_lines = ['Line-A', 'Line-B', 'Line-C', 'Line-D']
    shifts = ['Day', 'Afternoon', 'Night']

    for i in range(1, num_rows + 1):
        metric_date = datetime.now() - timedelta(days=random.randint(0, 365))
        availability = random.uniform(75, 99)
        performance = random.uniform(70, 98)
        quality = random.uniform(95, 99.5)
        oee = round((availability * performance * quality) / 10000, 2)
        target = random.randint(800, 1200)
        produced = int(target * (oee / 100))
        rejects = random.randint(0, int(produced * 0.05))
        downtime = random.randint(0, 120)
        revenue = round(produced * random.uniform(50, 200), 2)

        query = f"""
        INSERT INTO dbo.ProductionMetrics
        (Date, Shift, ProductionLine, UnitsProduced, TargetUnits,
         QualityRejects, DowntimeMinutes, OEE, RevenueGenerated)
        VALUES
        ('{metric_date.strftime("%Y-%m-%d")}',
         '{random.choice(shifts)}',
         '{random.choice(production_lines)}',
         {produced}, {target}, {rejects},
         {downtime}, {oee}, {revenue})
        """
        db.execute_write(query)

        if i % 100 == 0:
            print(f"  Inserted {i} production metrics...")

    print(f"✓ Completed: {num_rows} production metrics inserted")


def main():
    print("=" * 70)
    print("Asset Intelligence System - Database Population Script")
    print("=" * 70)

    try:
        db = SQLServerConnection()

        if not db.test_connection():
            print("✗ Database connection failed!")
            return

        print("\nClearing existing data...")
        # Truncate child tables first (foreign key order), then parent
        for table in ['FailureEvents', 'MaintenanceHistory', 'OperatingCosts', 'AssetPerformanceMetrics', 'CapitalProjects', 'ProductionMetrics', 'StrategicGoals', 'Assets']:
            db.execute_write(f"DELETE FROM dbo.{table}")
            print(f"  Cleared {table}")

        print("\nStarting data population...")

        populate_assets(db, 500)
        populate_maintenance_history(db, 500)
        populate_failure_events(db, 500)
        populate_operating_costs(db, 500)
        populate_production_metrics(db, 500)

        print("\n" + "=" * 70)
        print("✓ Database population completed successfully!")
        print("=" * 70)

        print("\nTable Summary:")
        tables = ['Assets', 'MaintenanceHistory', 'FailureEvents', 'OperatingCosts', 'ProductionMetrics']
        for table in tables:
            count = db.get_row_count(f'dbo.{table}')
            print(f"  {table}: {count:,} rows")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
