<?php
/**
 * Sistema de Autenticación
 */

class Auth {
    
    /**
     * Verificar si está logueado
     */
    public static function check() {
        return isset($_SESSION['admin_logged']) && $_SESSION['admin_logged'] === true;
    }
    
    /**
     * Login
     */
    public static function login($username, $password) {
        // Credenciales por defecto (cambiar en producción)
        $valid_users = [
            'admin' => 'kairos2024',
            'supervisor' => 'super2024'
        ];
        
        if (isset($valid_users[$username]) && $valid_users[$username] === $password) {
            $_SESSION['admin_logged'] = true;
            $_SESSION['admin_user'] = $username;
            $_SESSION['admin_role'] = ($username === 'admin') ? 'admin' : 'supervisor';
            $_SESSION['login_time'] = time();
            
            return true;
        }
        
        return false;
    }
    
    /**
     * Logout
     */
    public static function logout() {
        session_unset();
        session_destroy();
    }
    
    /**
     * Obtener usuario actual
     */
    public static function user() {
        return $_SESSION['admin_user'] ?? null;
    }
    
    /**
     * Obtener rol
     */
    public static function role() {
        return $_SESSION['admin_role'] ?? null;
    }
    
    /**
     * Verificar si es admin
     */
    public static function isAdmin() {
        return self::role() === 'admin';
    }
    
    /**
     * Requerir login (redirect si no está logueado)
     */
    public static function require_login() {
        if (!self::check()) {
            header('Location: ' . BASE_URL . 'index.php');
            exit;
        }
    }
}