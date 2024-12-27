##################################
# init_db.sql
##################################
CREATE DATABASE IF NOT EXISTS crypto_video;

USE crypto_video;

-- Table pour stocker les articles du flux RSS
CREATE TABLE IF NOT EXISTS rss_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    title VARCHAR(255),
    link VARCHAR(255),
    published DATETIME
);

-- Table pour le sentiment du marché (ex. via LunarCrush)
CREATE TABLE IF NOT EXISTS market_sentiment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    positive INT,
    neutral INT,
    negative INT
);

-- Table pour les transactions importantes (ex-Whale Alert, désormais BitQuery)
CREATE TABLE IF NOT EXISTS whale_activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    transaction_hash VARCHAR(100),
    amount FLOAT,
    from_address VARCHAR(100),
    to_address VARCHAR(100)
);

-- Table pour les mouvements de stablecoins (via Etherscan)
CREATE TABLE IF NOT EXISTS stablecoin_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    token VARCHAR(50),
    transaction_count INT,
    total_value FLOAT
);