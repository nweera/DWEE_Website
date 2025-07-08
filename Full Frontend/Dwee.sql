CREATE DATABASE DWEE;
USE DWEE;

-- Table for Roles
CREATE TABLE roles (
    id CHAR(36) PRIMARY KEY, -- UUID stored as CHAR(36)
    name VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for Users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_country_code VARCHAR(10), -- Country code for phone number
    phone_number VARCHAR(20), -- Local phone number
    address_country VARCHAR(100), -- Country for address
    address_province VARCHAR(100), -- Province for address
    address_detail TEXT, -- Detailed address
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    role_id CHAR(36) NOT NULL, -- Matches the UUID format in the roles table
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for Sales Representatives
CREATE TABLE sales_representatives (
    id CHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    company_name VARCHAR(255),
    fiscal_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    model VARCHAR(255) DEFAULT NULL,
    purchase_date DATE,
    warranty_end DATE,
    location VARCHAR(255),
    status ENUM('pending', 'active', 'maintenance', 'inactive') DEFAULT 'pending',
    validated TINYINT(1) DEFAULT 0, -- 0 = not validated, 1 = validated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_serial (serial_number),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Maintenances table
CREATE TABLE IF NOT EXISTS maintenances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_serial_number VARCHAR(50) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    status ENUM('scheduled', 'in_progress', 'completed', 'cancelled') DEFAULT 'scheduled',
    technician_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_serial_number) REFERENCES devices(serial_number) ON DELETE CASCADE,
    INDEX idx_device (device_serial_number),
    INDEX idx_date (date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for Notifications
CREATE TABLE notifications (
    id CHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    device_id INT,
    datetime DATETIME NOT NULL,
    type VARCHAR(100) NOT NULL,
    status ENUM('scheduled', 'confirmed', 'completed', 'cancelled') DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_datetime (datetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Support tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open',
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for Device History (FIXED)
CREATE TABLE device_history (
    id CHAR(36) PRIMARY KEY,
    device_id INT NOT NULL, -- Changed from CHAR(36) to INT to match devices(id)
    action TEXT NOT NULL,
    performed_by INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for Status (FIXED)
CREATE TABLE status (
    id CHAR(36) PRIMARY KEY,
    device_id INT NOT NULL, -- Changed from CHAR(36) to INT to match devices(id)
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS commercial_registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT, -- If the user is logged in, you can link to users(id)
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

-- Insert Initial Roles (CLEANED UP)
INSERT INTO roles (id, name) VALUES
((SELECT UUID()), 'user'),
((SELECT UUID()), 'sales'),
((SELECT UUID()), 'superadmin');

-- Insert Initial Status (FIXED - removed device_id requirement)
-- Note: Status should probably be a reference table, not tied to specific devices
-- If you want device-specific status, consider adding records after devices are created

-- Insert Super Admin User (FIXED)
INSERT INTO users (
    email, phone_country_code, phone_number, address_country, address_province, address_detail,
    first_name, last_name, password_hash, role_id, status
) VALUES (
    'superadmin@example.com', '+216', '12345678', 'Tunisia', 'Tunis', 'HQ',
    'Super', 'Admin', 'superadminpassword', 
    (SELECT id FROM roles WHERE name = 'superadmin'), 'active'
);