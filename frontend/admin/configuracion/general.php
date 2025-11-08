<?php
$page_title = 'Configuración General';
$current_page = 'config_general';
$current_section = 'configuracion';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

$mensaje = '';
$tipo_mensaje = 'success';

// Obtener configuración actual
$config = [
    'evento_nombre' => $db_instance->query("SELECT valor FROM configuracion WHERE clave = 'evento_nombre'")[0]['valor'] ?? '',
    'ubicacion' => $db_instance->query("SELECT valor FROM configuracion WHERE clave = 'ubicacion'")[0]['valor'] ?? '',
    'voz_activa' => $db_instance->query("SELECT valor FROM configuracion WHERE clave = 'voz_activa'")[0]['valor'] ?? '1',
    'modo_offline' => $db_instance->query("SELECT valor FROM configuracion WHERE clave = 'modo_offline'")[0]['valor'] ?? '0',
];

// Verificar si viene de guardado exitoso
if (isset($_GET['success'])) {
    $mensaje = 'Configuración guardada correctamente';
    $tipo_mensaje = 'success';
}

// Procesar formulario
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $campos = ['evento_nombre', 'ubicacion', 'voz_activa', 'modo_offline'];

        foreach ($campos as $campo) {
            $valor = $_POST[$campo] ?? '';

            // Verificar si existe
            $existe = $db_instance->query(
                "SELECT id FROM configuracion WHERE clave = ?",
                [$campo]
            );

            if (empty($existe)) {
                // Insertar
                $stmt = $db->prepare("INSERT INTO configuracion (clave, valor) VALUES (?, ?)");
                $stmt->execute([$campo, $valor]);
            } else {
                // Actualizar
                $stmt = $db->prepare("UPDATE configuracion SET valor = ? WHERE clave = ?");
                $stmt->execute([$valor, $campo]);
            }
        }

        // Redirigir con mensaje de éxito
        header('Location: general.php?success=1');
        exit;

        // Recargar config
        $config = [
            'evento_nombre' => $_POST['evento_nombre'] ?? '',
            'ubicacion' => $_POST['ubicacion'] ?? '',
            'voz_activa' => $_POST['voz_activa'] ?? '1',
            'modo_offline' => $_POST['modo_offline'] ?? '0',
        ];
    } catch (Exception $e) {
        $mensaje = 'Error al guardar: ' . $e->getMessage();
        $tipo_mensaje = 'danger';
    }
}

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">Configuración General</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item active">Configuración</li>
                </ol>
            </div>
        </div>
    </div>
</div>

<!-- Main content -->
<section class="content">
    <div class="container-fluid">

        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-cog"></i> Configuración del Sistema
                        </h3>
                    </div>

                    <form method="post">
                        <div class="card-body">

                            <?php if ($mensaje): ?>
                                <div class="alert alert-<?= $tipo_mensaje ?> alert-dismissible">
                                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                                    <?= $mensaje ?>
                                </div>
                            <?php endif; ?>

                            <!-- Nombre del Evento -->
                            <div class="form-group">
                                <label>Nombre del Evento/Feria</label>
                                <input type="text" class="form-control" name="evento_nombre"
                                    value="<?= e($config['evento_nombre']) ?>"
                                    placeholder="Ej: Feria de Salud Natural 2024">
                                <small class="text-muted">
                                    Aparecerá en los tickets y reportes
                                </small>
                            </div>

                            <!-- Ubicación -->
                            <div class="form-group">
                                <label>Ubicación</label>
                                <input type="text" class="form-control" name="ubicacion"
                                    value="<?= e($config['ubicacion']) ?>"
                                    placeholder="Ej: Plaza Mayor - Stand 12">
                                <small class="text-muted">
                                    Ubicación física del stand o botica
                                </small>
                            </div>

                            <!-- Voz Activa -->
                            <div class="form-group">
                                <label>Sistema de Voz</label>
                                <div class="custom-control custom-switch">
                                    <input type="checkbox" class="custom-control-input"
                                        id="voz_activa" name="voz_activa" value="1"
                                        <?= $config['voz_activa'] == '1' ? 'checked' : '' ?>>
                                    <label class="custom-control-label" for="voz_activa">
                                        Activar reconocimiento y síntesis de voz
                                    </label>
                                </div>
                                <small class="text-muted">
                                    Permite al sistema hablar y escuchar al paciente
                                </small>
                            </div>

                            <!-- Modo Offline -->
                            <div class="form-group">
                                <label>Modo de Operación</label>
                                <div class="custom-control custom-switch">
                                    <input type="checkbox" class="custom-control-input"
                                        id="modo_offline" name="modo_offline" value="1"
                                        <?= $config['modo_offline'] == '1' ? 'checked' : '' ?>>
                                    <label class="custom-control-label" for="modo_offline">
                                        Modo Offline (sin internet)
                                    </label>
                                </div>
                                <small class="text-muted">
                                    En modo offline se usa solo SQLite y clasificador local
                                </small>
                            </div>

                        </div>

                        <div class="card-footer">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Guardar Cambios
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card card-info">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-info-circle"></i> Información
                        </h3>
                    </div>
                    <div class="card-body">
                        <p><strong>Versión:</strong> 1.0.0</p>
                        <p><strong>Sistema:</strong> Kairos Médico</p>
                        <p><strong>Base de datos:</strong> MySQL</p>
                        <p><strong>Python:</strong> 3.9+</p>
                        <p><strong>PHP:</strong> <?= phpversion() ?></p>
                    </div>
                </div>
            </div>
        </div>

    </div>
</section>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>