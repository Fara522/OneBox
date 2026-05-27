CREATE DATABASE IF NOT EXISTS onebox_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE onebox_bot;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT UNIQUE DEFAULT NULL,
    username VARCHAR(100) DEFAULT NULL,
    full_name VARCHAR(200) NOT NULL,
    role ENUM('boss', 'admin', 'worker') NOT NULL,
    login VARCHAR(100) UNIQUE DEFAULT NULL,
    password_hash VARCHAR(255) DEFAULT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS machines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT DEFAULT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id INT NOT NULL,
    worker_id INT NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    assistant_name VARCHAR(200) DEFAULT NULL,
    machine_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    quantity INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME DEFAULT NULL,
    duration_minutes INT DEFAULT NULL,
    status ENUM('in_progress', 'completed') DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Default boss account: login=boss, password=boss123
INSERT IGNORE INTO users (full_name, role, login, password_hash)
VALUES (
    'Bosh Direktor',
    'boss',
    'boss',
    'default:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
);

-- Default machines
INSERT IGNORE INTO machines (name, description) VALUES
    ('Kashirovka', 'Kashirovka stanogi'),
    ('Govra stanok', 'Govra ishlab chiqarish stanogi'),
    ('Tigil', 'Tigil stanogi');
