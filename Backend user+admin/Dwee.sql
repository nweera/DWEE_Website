-- Create Database
CREATE DATABASE IF NOT EXISTS DWEE;
USE DWEE;

-- Roles Table
CREATE TABLE IF NOT EXISTS roles (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_country_code VARCHAR(10),
    phone_number VARCHAR(20),
    address_country VARCHAR(100),
    address_province VARCHAR(100),
    address_detail TEXT,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    role_id CHAR(36) NOT NULL,
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sales Representatives Table
CREATE TABLE IF NOT EXISTS sales_representatives (
    id CHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    company_name VARCHAR(255),
    fiscal_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Super Admins Table
CREATE TABLE IF NOT EXISTS super_admins (
    id CHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_country_code VARCHAR(10),
    phone_number VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    role_id CHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Devices Table
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    model VARCHAR(100),
    validated TINYINT(1) DEFAULT 0,
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    purchase_date DATE NULL,
    warranty_end DATE NULL,
    last_maintenance DATE NULL,
    next_maintenance_date DATE NULL,
    location VARCHAR(255) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Regular Maintenances Table
CREATE TABLE IF NOT EXISTS maintenances_regulieres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_serial_number VARCHAR(50) NOT NULL,
    description TEXT,
    datetime DATETIME NOT NULL,
    status ENUM('scheduled','confirmed', 'completed', 'cancelled') DEFAULT 'scheduled',
    technician_id CHAR(36),
    time_change_status TINYINT DEFAULT 0,
    requested_time DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_serial_number) REFERENCES devices(serial_number) ON DELETE CASCADE,
    FOREIGN KEY (technician_id) REFERENCES sales_representatives(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Urgent Maintenances Table
CREATE TABLE IF NOT EXISTS maintenances_urgentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_serial_number VARCHAR(50) NOT NULL,
    datetime DATETIME NOT NULL,
    status ENUM('scheduled', 'confirmed', 'completed', 'cancelled') DEFAULT 'scheduled',
    notes TEXT,
    technician_id CHAR(36),
    time_change_status TINYINT DEFAULT 0,
    requested_time DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_serial_number) REFERENCES devices(serial_number) ON DELETE CASCADE,
    FOREIGN KEY (technician_id) REFERENCES sales_representatives(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Device History Table
CREATE TABLE IF NOT EXISTS device_history (
    id CHAR(36) PRIMARY KEY,
    device_id INT NOT NULL,
    action TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'not active') DEFAULT 'active',
    maintenance_reguliere_id INT DEFAULT NULL,
    maintenance_urgente_id INT DEFAULT NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (maintenance_reguliere_id) REFERENCES maintenances_regulieres(id) ON DELETE SET NULL,
    FOREIGN KEY (maintenance_urgente_id) REFERENCES maintenances_urgentes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Device Status Table
CREATE TABLE IF NOT EXISTS device_status (
    id CHAR(36) PRIMARY KEY,
    device_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Commercial Registrations Table
CREATE TABLE IF NOT EXISTS commercial_registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    raison_sociale VARCHAR(255) NOT NULL,
    matricule_fiscale VARCHAR(100) NOT NULL,
    adresse TEXT NOT NULL,
    telephone VARCHAR(30) NOT NULL,
    email VARCHAR(255) NOT NULL,
    secteur_activite VARCHAR(100) NOT NULL,
    motivation TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id CHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Stock Table
CREATE TABLE IF NOT EXISTS stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    model VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'inactive') DEFAULT 'inactive'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Insert Initial Roles
INSERT INTO roles (id, name) VALUES
    (UUID(), 'user'),
    (UUID(), 'sales'),
    (UUID(), 'superadmin');

-- Insert Super Admin User
INSERT INTO super_admins (
    id, email, phone_country_code, phone_number, first_name, last_name, password_hash, role_id
) VALUES (
    UUID(), 'superadmin@example.com', '+216', '12345678', 'Super', 'Admin', '00000000',
    (SELECT id FROM roles WHERE name = 'superadmin')
);

-- Insert User Nour YKB
INSERT INTO users (
    email, phone_country_code, phone_number, address_country, address_province, address_detail,
    first_name, last_name, password_hash, role_id
) VALUES (
    'nourykb@gmail.com', '+216', '00000000', 'Tunisia', 'Tunis', 'Some address',
    'Nour', 'YKB', 'hashedpassword',
    (SELECT id FROM roles WHERE name = 'user')
);

-- Get the new user's id
SET @user_id = LAST_INSERT_ID();

-- Insert Devices
INSERT INTO devices (user_id, serial_number, purchase_date, location)
VALUES
    (@user_id, 'DKIT-001', '2024-06-01', 'Tunis'),
    (@user_id, 'DKIT-002', '2024-06-02', 'Tunis');

-- Get device ids
SELECT id INTO @dkit1 FROM devices WHERE user_id = @user_id ORDER BY id ASC LIMIT 1;
SELECT id INTO @dkit2 FROM devices WHERE user_id = @user_id ORDER BY id DESC LIMIT 1;

-- Mark first DKIT as approved, second as not approved
UPDATE devices SET validated = 1 WHERE id = @dkit1;
UPDATE devices SET validated = 0 WHERE id = @dkit2;

-- Get serial numbers for the devices
SELECT serial_number INTO @serial1 FROM devices WHERE id = @dkit1;
SELECT serial_number INTO @serial2 FROM devices WHERE id = @dkit2;

-- Insert a scheduled urgent maintenance for the approved DKIT
INSERT INTO maintenances_urgentes (device_serial_number, datetime, status, time_change_status, requested_time)
VALUES (@serial1, '2025-07-01 10:00:00', 'scheduled', 1, '2025-07-08 11:00:00');

-- Insert a scheduled urgent maintenance for the not approved DKIT
INSERT INTO maintenances_urgentes (device_serial_number, datetime, status)
VALUES (@serial1, '2025-07-05 14:00:00', 'confirmed');

-- Insert a scheduled regular maintenance for the approved DKIT
INSERT INTO maintenances_regulieres (device_serial_number, datetime, status)
VALUES (@serial1, '2025-07-10 09:00:00', 'confirmed');

-- Example: Confirm urgent maintenance by admin
-- UPDATE maintenances_urgentes SET status = 'confirmed', time_change_status = 0, requested_time = NULL WHERE id = @maintenance_id;

-- Example: User requests time change for urgent maintenance
-- UPDATE maintenances_urgentes SET status = 'scheduled', time_change_status = 1, requested_time = '2025-07-02 11:00:00' WHERE id = @maintenance_id;

-- Example: Admin approves time change
-- UPDATE maintenances_urgentes SET status = 'confirmed', time_change_status = 2, datetime = requested_time, requested_time = NULL WHERE id = @maintenance_id;

-- Example: Admin declines time change
-- UPDATE maintenances_urgentes SET status = 'cancelled', time_change_status = 4 WHERE id = @maintenance_id;