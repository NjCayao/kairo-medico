<?php
/**
 * Funciones comunes del sistema
 */

/**
 * Escapar HTML
 */
function e($string) {
    return htmlspecialchars($string, ENT_QUOTES, 'UTF-8');
}

/**
 * Formatear fecha
 */
function formatFecha($fecha, $formato = 'd/m/Y H:i') {
    if (!$fecha) return '-';
    $dt = new DateTime($fecha);
    return $dt->format($formato);
}

/**
 * Formatear precio
 */
function formatPrecio($precio) {
    return 'S/. ' . number_format($precio, 2);
}

/**
 * Mensaje de alerta
 */
function alerta($mensaje, $tipo = 'success') {
    $icono = [
        'success' => 'check',
        'error' => 'times',
        'warning' => 'exclamation-triangle',
        'info' => 'info-circle'
    ][$tipo] ?? 'info-circle';
    
    return '<div class="alert alert-' . $tipo . ' alert-dismissible fade show" role="alert">
        <i class="fas fa-' . $icono . '"></i> ' . e($mensaje) . '
        <button type="button" class="close" data-dismiss="alert">
            <span>&times;</span>
        </button>
    </div>';
}

/**
 * Redireccionar
 */
function redirect($url) {
    header('Location: ' . $url);
    exit;
}

/**
 * Obtener estadísticas del día
 */
function getEstadisticasHoy($db) {
    $hoy = date('Y-m-d');
    
    $stats = [
        'consultas' => 0,
        'usuarios_nuevos' => 0,
        'sesiones' => 0,
        'productos_usados' => 0
    ];
    
    // Consultas
    $result = $db->query(
        "SELECT COUNT(*) as total FROM consultas_medicas WHERE DATE(fecha) = ?",
        [$hoy]
    );
    $stats['consultas'] = $result[0]['total'] ?? 0;
    
    // Usuarios nuevos
    $result = $db->query(
        "SELECT COUNT(*) as total FROM usuarios WHERE DATE(created_at) = ?",
        [$hoy]
    );
    $stats['usuarios_nuevos'] = $result[0]['total'] ?? 0;
    
    // Sesiones autónomas
    $result = $db->query(
        "SELECT COUNT(*) as total FROM sesiones_autonomas WHERE DATE(fecha_inicio) = ?",
        [$hoy]
    );
    $stats['sesiones'] = $result[0]['total'] ?? 0;
    
    return $stats;
}

/**
 * Validar DNI
 */
function validarDNI($dni) {
    return preg_match('/^\d{8}$/', $dni);
}

/**
 * Generar código único
 */
function generarCodigo($prefix = 'K') {
    return $prefix . date('Ymd') . '-' . strtoupper(substr(uniqid(), -6));
}

/**
 * Truncar texto
 */
function truncate($text, $length = 100, $suffix = '...') {
    if (strlen($text) <= $length) {
        return $text;
    }
    return substr($text, 0, $length - strlen($suffix)) . $suffix;
}

/**
 * Badge de estado
 */
function badgeEstado($estado) {
    $badges = [
        'activo' => '<span class="badge badge-success">Activo</span>',
        'inactivo' => '<span class="badge badge-secondary">Inactivo</span>',
        'completado' => '<span class="badge badge-info">Completado</span>',
        'cancelado' => '<span class="badge badge-danger">Cancelado</span>',
        'en_proceso' => '<span class="badge badge-warning">En Proceso</span>'
    ];
    
    return $badges[$estado] ?? '<span class="badge badge-secondary">' . e($estado) . '</span>';
}

/**
 * Obtener conteo de productos
 */
function getProductosCount($db) {
    $result = $db->query("SELECT COUNT(*) as total FROM productos_naturales WHERE activo = TRUE");
    return $result[0]['total'] ?? 0;
}

/**
 * Obtener conteo de usuarios
 */
function getUsuariosCount($db) {
    $result = $db->query("SELECT COUNT(*) as total FROM usuarios");
    return $result[0]['total'] ?? 0;
}

/**
 * Debug (solo en desarrollo)
 */
function dd($var) {
    echo '<pre>';
    var_dump($var);
    echo '</pre>';
    die();
}