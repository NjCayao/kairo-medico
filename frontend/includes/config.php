<?php
/**
 * Configuración del Sistema Kairos
 */

// Iniciar sesión
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Configuración de base de datos
define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
define('DB_USER', getenv('DB_USER') ?: 'root');
define('DB_PASS', getenv('DB_PASSWORD') ?: '');
define('DB_NAME', getenv('DB_NAME') ?: 'kairos_medico');
define('DB_PORT', getenv('DB_PORT') ?: '3306');

// URLs - Detectar automáticamente
$protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https://' : 'http://';
$host = $_SERVER['HTTP_HOST'];

define('BASE_URL', $protocol . $host . '/kairos-medico/frontend/admin/');
define('ASSETS_URL', BASE_URL . 'assets/');

// API
define('API_URL', 'http://localhost:5000/api/');

// Rutas absolutas
define('ROOT_PATH', dirname(__DIR__) . '/');
define('ADMIN_PATH', ROOT_PATH . 'admin/');
define('INCLUDES_PATH', ROOT_PATH . 'includes/');

// Excel
define('EXCEL_PATH', dirname(dirname(dirname(__FILE__))) . '/backend/data/');

// Timezone
date_default_timezone_set('America/Lima');

// Error reporting (cambiar en producción)
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Configuración PHP
ini_set('memory_limit', '256M');
ini_set('max_execution_time', '300');