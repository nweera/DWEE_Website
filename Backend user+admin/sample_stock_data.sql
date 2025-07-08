-- Sample data for stock table
-- Run these queries to populate your stock table with test data

-- First, ensure the stock table exists
CREATE TABLE IF NOT EXISTS stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    model VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'inactive') DEFAULT 'inactive'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample D-KITs into stock
INSERT INTO stock (serial_number, model, status) VALUES 
    ('DKIT-2025-001', 'D-KIT Pro v2.1', 'inactive'),
    ('DKIT-2025-002', 'D-KIT Standard v1.5', 'inactive'),
    ('DKIT-2025-003', 'D-KIT Pro Max v3.0', 'active'),
    ('DKIT-2025-004', 'D-KIT Basic v1.0', 'inactive'),
    ('DKIT-2025-005', 'D-KIT Pro v2.1', 'active'),
    ('DKIT-2025-006', 'D-KIT Standard v1.5', 'inactive'),
    ('DKIT-2025-007', 'D-KIT Pro Max v3.0', 'inactive'),
    ('DKIT-2025-008', 'D-KIT Basic v1.0', 'active'),
    ('DKIT-2025-009', 'D-KIT Enterprise v4.0', 'inactive'),
    ('DKIT-2025-010', 'D-KIT Pro v2.1', 'inactive'),
    ('DKIT-2025-011', 'D-KIT Standard v1.5', 'active'),
    ('DKIT-2025-012', 'D-KIT Pro Max v3.0', 'inactive'),
    ('DKIT-2025-013', 'D-KIT Basic v1.0', 'inactive'),
    ('DKIT-2025-014', 'D-KIT Enterprise v4.0', 'active'),
    ('DKIT-2025-015', 'D-KIT Pro v2.1', 'inactive'),
    ('DKIT-2025-016', 'D-KIT Standard v1.5', 'inactive'),
    ('DKIT-2025-017', 'D-KIT Pro Max v3.0', 'active'),
    ('DKIT-2025-018', 'D-KIT Basic v1.0', 'inactive'),
    ('DKIT-2025-019', 'D-KIT Enterprise v4.0', 'inactive'),
    ('DKIT-2025-020', 'D-KIT Pro v2.1', 'active');

-- Verify the data was inserted
SELECT 
    COUNT(*) as total_devices,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_devices,
    COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_devices
FROM stock;

-- View all devices by model
SELECT model, COUNT(*) as quantity, status
FROM stock 
GROUP BY model, status
ORDER BY model, status;

-- View recent additions
SELECT * FROM stock ORDER BY created_at DESC LIMIT 10;
