/**
 * Central API base path.
 * In production, Nginx proxies /api/* → backend:8000/api/*
 * Use this constant instead of hardcoding http://localhost:8000/api
 */
export const API_BASE = '/api';
