<?php
define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/auth.php';

Auth::require_login();

$db_instance = new Database();
$db = $db_instance->connect();

$id = $_GET['id'] ?? 0;

if ($id > 0) {
    try {
        $sql = "DELETE FROM productos_naturales WHERE id = ?";
        $stmt = $db->prepare($sql);
        $resultado = $stmt->execute([$id]);
        
        if ($resultado) {
            header('Location: listar.php?success=1');
        } else {
            header('Location: listar.php?error=Error al eliminar');
        }
        
    } catch (PDOException $e) {
        header('Location: listar.php?error=' . urlencode('Error: ' . $e->getMessage()));
    }
} else {
    header('Location: listar.php?error=ID inválido');
}
exit;