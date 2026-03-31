-- 初始化数据库
USE legal_saas;

-- 租户表
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan ENUM('free', 'pro', 'enterprise') DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 工作区表
CREATE TABLE IF NOT EXISTS workspaces (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    wx_openid VARCHAR(100),
    wx_unionid VARCHAR(100),
    password_hash VARCHAR(255),
    role ENUM('admin', 'member') DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_email (email),
    INDEX idx_wx_openid (wx_openid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 合同表
CREATE TABLE IF NOT EXISTS contracts (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(500),
    file_path VARCHAR(1000),
    file_hash VARCHAR(64),
    contract_type VARCHAR(50),
    content_text TEXT,
    review_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    review_result JSON,
    risk_level ENUM('low', 'medium', 'high'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_workspace_id (workspace_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (review_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 法律知识库表
CREATE TABLE IF NOT EXISTS legal_knowledge (
    id VARCHAR(36) PRIMARY KEY,
    content_type ENUM('law', 'case', 'template', 'rule') NOT NULL,
    title VARCHAR(500),
    content TEXT NOT NULL,
    metadata JSON,
    tenant_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_content_type (content_type),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
