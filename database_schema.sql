-- Enhanced Weighing Bridge System Database Schema for Manganese Mining
-- Compatible with Smart Weight machine specifications

-- Users Table for Authentication and Management
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(120) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'operator',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transport Companies Table
CREATE TABLE transport_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name VARCHAR(100) NOT NULL UNIQUE,
    contact_person VARCHAR(100),
    phone_number VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drivers Table
CREATE TABLE drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_name VARCHAR(100) NOT NULL,
    license_number VARCHAR(50),
    phone_number VARCHAR(20),
    transport_company_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transport_company_id) REFERENCES transport_companies(id)
);

-- Trucks Table with unique constraints
CREATE TABLE trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_number VARCHAR(20) NOT NULL UNIQUE,
    transporter_name VARCHAR(100) NOT NULL,
    axles INTEGER NOT NULL DEFAULT 4,
    transport_company_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transport_company_id) REFERENCES transport_companies(id)
);

-- Truck-Driver Assignment Table
CREATE TABLE truck_drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    assigned_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (truck_id) REFERENCES trucks(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    UNIQUE(truck_id, driver_id, assigned_date)
);

-- Products Table with LNG specifications
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name VARCHAR(100) NOT NULL UNIQUE,
    product_code VARCHAR(50),
    unit_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materials Table for manganese mining
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_name VARCHAR(50) NOT NULL UNIQUE,
    material_code VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Destinations Table
CREATE TABLE destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_name VARCHAR(100) NOT NULL UNIQUE,
    location_code VARCHAR(50),
    distance_km DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Operators Table
CREATE TABLE operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_name VARCHAR(100) NOT NULL UNIQUE,
    employee_id VARCHAR(50),
    department VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loaders Table
CREATE TABLE loaders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loader_name VARCHAR(100) NOT NULL UNIQUE,
    equipment_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main Weighing Records Table
CREATE TABLE weighing_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    date_in DATE NOT NULL,
    time_in TIME NOT NULL,
    date_out DATE,
    time_out TIME,
    way_bill VARCHAR(50) NOT NULL UNIQUE,
    registration VARCHAR(20) NOT NULL,
    axles INTEGER NOT NULL,
    trip_number INTEGER NOT NULL,
    transporter_name VARCHAR(100) NOT NULL,
    driver_name VARCHAR(100) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    material_id INTEGER,
    mass1 DECIMAL(10,2) NOT NULL,
    mass2 DECIMAL(10,2) NOT NULL,
    net_load DECIMAL(10,2) NOT NULL,
    operator_weigh VARCHAR(100) NOT NULL,
    loader VARCHAR(100) NOT NULL,
    destination VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

-- Offline Sync Table for online/offline capability
CREATE TABLE offline_sync (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_sync_attempt TIMESTAMP,
    sync_error TEXT,
    FOREIGN KEY (record_id) REFERENCES weighing_records(id)
);

-- System Settings for Smart Weight integration
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(50) NOT NULL UNIQUE,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_weighing_records_date ON weighing_records(date_in);
CREATE INDEX idx_weighing_records_waybill ON weighing_records(way_bill);
CREATE INDEX idx_weighing_records_registration ON weighing_records(registration);
CREATE INDEX idx_weighing_records_trip ON weighing_records(trip_number);
CREATE INDEX idx_weighing_records_transporter ON weighing_records(transporter_name);
CREATE INDEX idx_trucks_registration ON trucks(registration_number);
CREATE INDEX idx_offline_sync_status ON offline_sync(sync_status);

-- Insert default materials for manganese mining
INSERT INTO materials (material_name, material_code, description) VALUES
('HGL', 'HGL', 'High Grade Lump'),
('LGL', 'LGL', 'Low Grade Lump'),
('HGLogs', 'HGLOGS', 'High Grade Logs'),
('LGLogs', 'LGLOGS', 'Low Grade Logs'),
('HGF', 'HGF', 'High Grade Fines'),
('LGF', 'LGF', 'Low Grade Fines');

-- Insert default products for LNG specifications
INSERT INTO products (product_name, product_code, unit_price) VALUES
('LNG 24', 'LNG24', 0.00),
('LNG 25', 'LNG25', 0.00),
('LNG 26.5', 'LNG265', 0.00);

-- Insert default system settings for Smart Weight
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('smart_weight_port', 'COM1', 'Smart Weight machine communication port'),
('smart_weight_baudrate', '9600', 'Smart Weight machine baud rate'),
('auto_zero_interval', '300', 'Auto zero interval in seconds'),
('tare_timeout', '30', 'Tare operation timeout in seconds'),
('offline_mode', 'false', 'System offline mode status');