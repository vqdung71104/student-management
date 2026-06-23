/**
 * Central API base path.
 * In production, Nginx proxies /api/* → backend:8000/api/*
 * Use this constant instead of hardcoding a machine-local backend URL.
 */
export const API_BASE = '/api';
