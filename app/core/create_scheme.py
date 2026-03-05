from app.core.database import SQLServerConnection
from dotenv import load_dotenv

load_dotenv()

# SQL statements to create all tables
SCHEMA_SQL = """
-- Drop existing tables if they exist (careful in production!)
IF OBJECT_ID('FailureEvents', 'U') IS NOT NULL DROP TABLE FailureEvents;
IF OBJECT_ID('OperatingCosts', 'U') IS NOT NULL DROP TABLE OperatingCosts;
IF OBJECT_ID('CapitalProjects', 'U') IS NOT NULL DROP TABLE CapitalProjects;
IF OBJECT_ID('ProductionMetrics', 'U') IS NOT NULL DROP TABLE ProductionMetrics;
IF OBJECT_ID('MaintenanceHistory', 'U') IS NOT NULL DROP TABLE MaintenanceHistory;
IF OBJECT_ID('AssetPerformanceMetrics', 'U') IS NOT NULL DROP TABLE AssetPerformanceMetrics;
IF OBJECT_ID('StrategicGoals', 'U') IS NOT NULL DROP TABLE StrategicGoals;
IF OBJECT_ID('Assets', 'U') IS NOT NULL DROP TABLE Assets;
GO

-- Create Assets table
CREATE TABLE Assets (
    AssetID VARCHAR(50) PRIMARY KEY,
    AssetName VARCHAR(200) NOT NULL,
    AssetType VARCHAR(100) NOT NULL,
    Manufacturer VARCHAR(100),
    ModelNumber VARCHAR(100),
    SerialNumber VARCHAR(100),
    InstallationDate DATE,
    DesignLife INT,
    Criticality VARCHAR(20),
    ReplacementCost DECIMAL(15,2),
    Location VARCHAR(200),
    Department VARCHAR(100),
    Status VARCHAR(50),
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE()
);
GO

-- Create AssetPerformanceMetrics table
CREATE TABLE AssetPerformanceMetrics (
    MetricID INT IDENTITY(1,1) PRIMARY KEY,
    AssetID VARCHAR(50) NOT NULL,
    Timestamp DATETIME NOT NULL,
    Efficiency DECIMAL(5,2),
    Temperature DECIMAL(6,2),
    Pressure DECIMAL(8,2),
    Vibration DECIMAL(6,2),
    FlowRate DECIMAL(10,2),
    PowerConsumption DECIMAL(10,2),
    Runtime DECIMAL(10,2),
    Availability DECIMAL(5,2),
    FOREIGN KEY (AssetID) REFERENCES Assets(AssetID)
);
GO

CREATE INDEX IX_AssetPerformance_AssetTime ON AssetPerformanceMetrics(AssetID, Timestamp DESC);
GO

-- Create MaintenanceHistory table
CREATE TABLE MaintenanceHistory (
    MaintenanceID INT IDENTITY(1,1) PRIMARY KEY,
    AssetID VARCHAR(50) NOT NULL,
    WorkOrderNumber VARCHAR(50) UNIQUE,
    MaintenanceType VARCHAR(50),
    Description TEXT,
    ScheduledDate DATE,
    StartDate DATETIME,
    CompletionDate DATETIME,
    DowntimeHours DECIMAL(8,2),
    LaborCost DECIMAL(12,2),
    PartsCost DECIMAL(12,2),
    ContractorCost DECIMAL(12,2),
    TotalCost AS (LaborCost + PartsCost + ContractorCost) PERSISTED,
    Technician VARCHAR(100),
    Status VARCHAR(50),
    FailureMode VARCHAR(200),
    RootCause TEXT,
    CreatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (AssetID) REFERENCES Assets(AssetID)
);
GO

CREATE INDEX IX_Maintenance_Asset ON MaintenanceHistory(AssetID, CompletionDate DESC);
GO

-- Create ProductionMetrics table
CREATE TABLE ProductionMetrics (
    ProductionID INT IDENTITY(1,1) PRIMARY KEY,
    Date DATE NOT NULL,
    Shift VARCHAR(20),
    ProductionLine VARCHAR(50),
    UnitsProduced INT,
    TargetUnits INT,
    QualityRejects INT,
    DowntimeMinutes INT,
    OEE DECIMAL(5,2),
    RevenueGenerated DECIMAL(15,2),
    CreatedDate DATETIME DEFAULT GETDATE()
);
GO

CREATE INDEX IX_Production_Date ON ProductionMetrics(Date DESC);
GO

-- Create CapitalProjects table
CREATE TABLE CapitalProjects (
    ProjectID VARCHAR(50) PRIMARY KEY,
    ProjectName VARCHAR(200) NOT NULL,
    AssetID VARCHAR(50),
    ProjectType VARCHAR(100),
    Description TEXT,
    StrategicAlignment VARCHAR(50),
    EstimatedCost DECIMAL(15,2),
    EstimatedBenefit DECIMAL(15,2),
    NPV DECIMAL(15,2),
    IRR DECIMAL(5,2),
    PaybackPeriod DECIMAL(5,2),
    RiskLevel VARCHAR(20),
    Priority INT,
    Status VARCHAR(50),
    ProposedStartDate DATE,
    ProposedEndDate DATE,
    ActualStartDate DATE,
    ActualEndDate DATE,
    BudgetYear INT,
    Department VARCHAR(100),
    CreatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (AssetID) REFERENCES Assets(AssetID)
);
GO

-- Create OperatingCosts table
CREATE TABLE OperatingCosts (
    CostID INT IDENTITY(1,1) PRIMARY KEY,
    AssetID VARCHAR(50) NOT NULL,
    YearMonth DATE NOT NULL,
    EnergyCost DECIMAL(12,2),
    MaintenanceCost DECIMAL(12,2),
    LaborCost DECIMAL(12,2),
    MaterialsCost DECIMAL(12,2),
    ContractorCost DECIMAL(12,2),
    OtherCost DECIMAL(12,2),
    TotalCost AS (EnergyCost + MaintenanceCost + LaborCost + MaterialsCost + ContractorCost + OtherCost) PERSISTED,
    BudgetedCost DECIMAL(12,2),
    Variance AS (BudgetedCost - (EnergyCost + MaintenanceCost + LaborCost + MaterialsCost + ContractorCost + OtherCost)) PERSISTED,
    FOREIGN KEY (AssetID) REFERENCES Assets(AssetID)
);
GO

CREATE INDEX IX_OperatingCosts_Asset ON OperatingCosts(AssetID, YearMonth DESC);
GO

-- Create StrategicGoals table
CREATE TABLE StrategicGoals (
    GoalID INT IDENTITY(1,1) PRIMARY KEY,
    GoalName VARCHAR(200) NOT NULL,
    MetricName VARCHAR(100),
    TargetValue DECIMAL(10,2),
    CurrentValue DECIMAL(10,2),
    Unit VARCHAR(50),
    TargetDate DATE,
    Category VARCHAR(100),
    Status VARCHAR(50),
    Owner VARCHAR(100),
    CreatedDate DATETIME DEFAULT GETDATE()
);
GO

-- Create FailureEvents table
CREATE TABLE FailureEvents (
    FailureID INT IDENTITY(1,1) PRIMARY KEY,
    AssetID VARCHAR(50) NOT NULL,
    FailureDate DATETIME NOT NULL,
    FailureMode VARCHAR(200),
    Severity VARCHAR(20),
    DowntimeHours DECIMAL(8,2),
    ProductionLoss INT,
    RepairCost DECIMAL(12,2),
    RootCause TEXT,
    CorrectiveActions TEXT,
    MTBF DECIMAL(10,2),
    FOREIGN KEY (AssetID) REFERENCES Assets(AssetID)
);
GO

PRINT 'Schema created successfully!';
"""

SAMPLE_DATA_SQL = """
-- Insert sample Assets
INSERT INTO Assets (AssetID, AssetName, AssetType, Manufacturer, ModelNumber, SerialNumber, InstallationDate, DesignLife, Criticality, ReplacementCost, Location, Department, Status) 
VALUES 
('COMP-101', 'Main Air Compressor 1', 'Compressor', 'Atlas Copco', 'GA-110', 'AC12345', '2018-03-15', 15, 'Critical', 250000, 'Building A - Level 2', 'Production', 'Operating'),
('COMP-102', 'Backup Air Compressor', 'Compressor', 'Atlas Copco', 'GA-90', 'AC54321', '2020-08-05', 15, 'High', 180000, 'Building A - Level 2', 'Production', 'Standby'),
('PUMP-201', 'Cooling Water Pump 1', 'Pump', 'Grundfos', 'CR-64', 'P67890', '2019-06-20', 12, 'High', 45000, 'Pump House 1', 'Utilities', 'Operating'),
('PUMP-202', 'Cooling Water Pump 2', 'Pump', 'Grundfos', 'CR-64', 'P67891', '2019-06-20', 12, 'High', 45000, 'Pump House 1', 'Utilities', 'Operating'),
('HX-301', 'Heat Exchanger 301', 'Heat Exchanger', 'Alfa Laval', 'AlfaNova-27', 'HX98765', '2017-01-10', 20, 'Medium', 85000, 'Process Area B', 'Production', 'Operating'),
('REACTOR-401', 'Primary Reactor', 'Reactor', 'Yokogawa', 'RX-2000', 'RX11111', '2015-05-01', 25, 'Critical', 1200000, 'Process Area A', 'Production', 'Operating'),
('TURBINE-501', 'Steam Turbine Generator', 'Turbine', 'Siemens', 'SST-900', 'TB55555', '2016-09-15', 30, 'Critical', 2500000, 'Power Plant', 'Utilities', 'Operating');
GO

-- Insert sample MaintenanceHistory
INSERT INTO MaintenanceHistory (AssetID, WorkOrderNumber, MaintenanceType, Description, ScheduledDate, StartDate, CompletionDate, DowntimeHours, LaborCost, PartsCost, ContractorCost, Technician, Status, FailureMode, RootCause)
VALUES 
('COMP-101', 'WO-2024-001', 'Preventive', 'Quarterly inspection and oil change', '2024-01-15', '2024-01-15 08:00', '2024-01-15 14:00', 6, 1200, 450, 0, 'John Smith', 'Completed', NULL, NULL),
('COMP-101', 'WO-2024-045', 'Corrective', 'Bearing replacement - high vibration detected', '2024-09-20', '2024-09-20 09:00', '2024-09-21 17:00', 32, 3200, 8500, 5000, 'Mike Johnson', 'Completed', 'Bearing failure', 'Inadequate lubrication'),
('PUMP-201', 'WO-2024-023', 'Preventive', 'Impeller inspection and seal replacement', '2024-06-10', '2024-06-10 08:00', '2024-06-10 16:00', 8, 1600, 1200, 0, 'Sarah Lee', 'Completed', NULL, NULL),
('HX-301', 'WO-2024-067', 'Predictive', 'Cleaning due to fouling (efficiency drop detected)', '2024-12-05', '2024-12-05 06:00', '2024-12-06 18:00', 36, 2400, 800, 3500, 'Tom Brown', 'Completed', 'Fouling', 'Process fluid contamination'),
('REACTOR-401', 'WO-2024-012', 'Preventive', 'Annual catalyst inspection', '2024-03-01', '2024-03-01 06:00', '2024-03-05 18:00', 108, 12000, 45000, 25000, 'External Team', 'Completed', NULL, NULL);
GO

-- Insert sample CapitalProjects
INSERT INTO CapitalProjects (ProjectID, ProjectName, AssetID, ProjectType, Description, StrategicAlignment, EstimatedCost, EstimatedBenefit, NPV, IRR, PaybackPeriod, RiskLevel, Priority, Status, ProposedStartDate, ProposedEndDate, BudgetYear, Department)
VALUES 
('PROJ-2025-001', 'Replace COMP-101 with Variable Speed Drive', 'COMP-101', 'Upgrade', 'Install VSD to improve efficiency and reduce energy costs', 'Cost Reduction', 180000, 45000, 125000, 18.5, 4.0, 'Low', 2, 'Approved', '2025-03-01', '2025-04-15', 2025, 'Production'),
('PROJ-2025-002', 'New Backup Pump Installation', NULL, 'New Installation', 'Install redundant pump to improve reliability', 'Reliability', 65000, 120000, 85000, 22.0, 3.5, 'Low', 1, 'Proposed', '2025-02-01', '2025-03-01', 2025, 'Utilities'),
('PROJ-2025-003', 'Heat Exchanger Network Optimization', 'HX-301', 'Upgrade', 'Implement advanced process control to optimize heat recovery', 'Cost Reduction', 250000, 85000, 180000, 16.0, 2.9, 'Medium', 3, 'Proposed', '2025-06-01', '2025-09-30', 2025, 'Production'),
('PROJ-2025-004', 'Predictive Maintenance System', NULL, 'New Installation', 'IoT sensors and analytics platform for condition monitoring', 'Reliability', 320000, 150000, 275000, 24.0, 2.1, 'Medium', 1, 'Approved', '2025-01-15', '2025-05-30', 2025, 'Maintenance');
GO

-- Insert sample StrategicGoals
INSERT INTO StrategicGoals (GoalName, MetricName, TargetValue, CurrentValue, Unit, TargetDate, Category, Status, Owner)
VALUES 
('Achieve 92% OEE', 'Overall Equipment Effectiveness', 92.0, 87.5, '%', '2025-12-31', 'Production', 'At Risk', 'Production Manager'),
('Reduce Maintenance Costs by 15%', 'Annual Maintenance Cost', 850000, 950000, 'USD', '2025-12-31', 'Cost', 'Behind', 'Maintenance Manager'),
('Zero Lost Time Incidents', 'LTI Count', 0, 0, 'incidents', '2025-12-31', 'Safety', 'On Track', 'Safety Manager'),
('Reduce Energy Consumption 10%', 'Energy per Unit', 45, 50, 'kWh/unit', '2025-12-31', 'Environmental', 'At Risk', 'Sustainability Manager');
GO

-- Insert sample FailureEvents
INSERT INTO FailureEvents (AssetID, FailureDate, FailureMode, Severity, DowntimeHours, ProductionLoss, RepairCost, RootCause, CorrectiveActions, MTBF)
VALUES 
('COMP-101', '2024-09-20 14:30', 'Bearing Failure', 'Major', 32, 3200, 16700, 'Inadequate lubrication due to low oil level', 'Implemented automated oil level monitoring', 12500),
('PUMP-201', '2024-07-15 10:15', 'Seal Leak', 'Minor', 8, 800, 1850, 'Seal wear from abrasive particles in fluid', 'Installed upstream filtration', 8200),
('COMP-101', '2023-12-10 09:00', 'Control Valve Stuck', 'Major', 24, 2400, 5200, 'Valve seat corrosion', 'Replaced with corrosion-resistant material', 11200);
GO

PRINT 'Sample data inserted successfully!';
"""

def create_schema():
    """Create database schema"""
    import pyodbc
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    server = os.getenv("MSSQL_LOCAL_SERVER")
    database = os.getenv("MSSQL_LOCAL_DATABASE")
    username = os.getenv("MSSQL_LOCAL_USER")
    password = os.getenv("MSSQL_LOCAL_PWD")
    
    if password and (';' in password or '{' in password or '}' in password):
        password = '{' + password + '}'

    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
    )
    
    def execute_batches(cursor, sql):
        batches = [b.strip() for b in sql.split("\nGO") if b.strip()]
        for batch in batches:
            if batch:
                cursor.execute(batch)

    try:
        print("=" * 70)
        print("CREATING DATABASE SCHEMA")
        print("=" * 70)

        conn = pyodbc.connect(connection_string)
        conn.autocommit = True
        cursor = conn.cursor()

        # Execute schema creation
        print("\n1. Creating tables...")
        execute_batches(cursor, SCHEMA_SQL)
        print("Tables created successfully!")

        # Execute sample data insertion
        print("\n2. Inserting sample data...")
        execute_batches(cursor, SAMPLE_DATA_SQL)
        print("Sample data inserted successfully!")
        
        # Verify tables
        print("\n3. Verifying tables...")
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n✓ Created {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("DATABASE SETUP COMPLETE!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n Error creating schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_schema()