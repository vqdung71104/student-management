-- ============================================
-- Student Management System - Database Initialization
-- ============================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS student_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE student_management;

-- Set timezone
SET time_zone = '+07:00';

-- Enable event scheduler (for scheduled tasks)
SET GLOBAL event_scheduler = ON;

-- ============================================
-- Initial Configuration
-- ============================================

-- Grant privileges (if needed)
-- GRANT ALL PRIVILEGES ON student_management.* TO 'root'@'%';
-- FLUSH PRIVILEGES;

-- ============================================
-- Notes
-- ============================================
-- Tables will be created automatically by SQLAlchemy
-- This file is for initial database setup only
