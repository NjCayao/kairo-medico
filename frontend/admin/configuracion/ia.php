<?php
$page_title = 'Configuración IA';
$current_page = 'config_ia';
$current_section = 'configuracion';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

$mensaje = '';
$tipo_mensaje = 'success';

// Obtener configuración IA
$config_ia = $db_instance->query(
    "SELECT * FROM configuracion_ia ORDER BY id DESC LIMIT 1"
)[0] ?? null;

// Verificar si viene de guardado exitoso
if (isset($_GET['success'])) {
    $mensaje = 'Configuración de IA guardada correctamente';
    $tipo_mensaje = 'success';
}

// Procesar formulario
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $datos = [
            'api_key' => trim($_POST['api_key'] ?? ''),
            'modelo_gpt' => trim($_POST['modelo'] ?? 'gpt-4o-mini'),  
            'temperatura' => floatval($_POST['temperatura'] ?? 0.7),
            'max_tokens' => intval($_POST['max_tokens'] ?? 1000),
            'activo' => isset($_POST['activo']) ? 1 : 0,
            'limite_diario_consultas' => intval($_POST['consultas_por_dia'] ?? 100),  
            'presupuesto_mensual' => floatval($_POST['costo_maximo_dia'] ?? 10.0)  
        ];

        if ($config_ia) {
            // Actualizar
            $stmt = $db->prepare("UPDATE configuracion_ia SET 
                api_key = ?, 
                modelo_gpt = ?,
                temperatura = ?, 
                max_tokens = ?,
                activo = ?, 
                limite_diario_consultas = ?, 
                presupuesto_mensual = ?
                WHERE id = ?");
            
            $stmt->execute([
                $datos['api_key'],
                $datos['modelo_gpt'],
                $datos['temperatura'],
                $datos['max_tokens'],
                $datos['activo'],
                $datos['limite_diario_consultas'],
                $datos['presupuesto_mensual'],
                $config_ia['id']
            ]);
        } else {
            // Insertar
            $stmt = $db->prepare("INSERT INTO configuracion_ia 
                (proveedor, api_key, modelo_gpt, temperatura, max_tokens, activo, limite_diario_consultas, presupuesto_mensual)
                VALUES ('openai', ?, ?, ?, ?, ?, ?, ?)");
            
            $stmt->execute([
                $datos['api_key'],
                $datos['modelo_gpt'],
                $datos['temperatura'],
                $datos['max_tokens'],
                $datos['activo'],
                $datos['limite_diario_consultas'],
                $datos['presupuesto_mensual']
            ]);
        }

        // Redirigir con mensaje de éxito
        header('Location: ia.php?success=1');
        exit;
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
                <h1 class="m-0">Configuración de Inteligencia Artificial</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item active">Config IA</li>
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
                            <i class="fas fa-robot"></i> Configuración de GPT
                        </h3>
                    </div>

                    <form method="post">
                        <div class="card-body">

                            <?php if ($mensaje): ?>
                                <div class="alert alert-<?= $tipo_mensaje ?> alert-dismissible">
                                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                                    <i class="fas fa-check-circle"></i> <?= $mensaje ?>
                                </div>
                            <?php endif; ?>

                            <!-- API Key -->
                            <div class="form-group">
                                <label>API Key de OpenAI</label>
                                <input type="password" class="form-control" name="api_key"
                                    value="<?= e($config_ia['api_key'] ?? '') ?>"
                                    placeholder="sk-...">
                                <small class="text-muted">
                                    Obtén tu API key en: <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a>
                                </small>
                            </div>

                            <!-- Modelo -->
                            <div class="form-group">
                                <label>Modelo</label>
                                <select class="form-control" name="modelo">
                                    <option value="gpt-4o-mini" <?= ($config_ia['modelo_gpt'] ?? 'gpt-4o-mini') == 'gpt-4o-mini' ? 'selected' : '' ?>>
                                        GPT-4o Mini (Recomendado - Económico y rápido) ⭐
                                    </option>
                                    <option value="gpt-4o" <?= ($config_ia['modelo_gpt'] ?? '') == 'gpt-4o' ? 'selected' : '' ?>>
                                        GPT-4o (Más completo)
                                    </option>
                                    <option value="gpt-4-turbo" <?= ($config_ia['modelo_gpt'] ?? '') == 'gpt-4-turbo' ? 'selected' : '' ?>>
                                        GPT-4 Turbo
                                    </option>
                                    <option value="gpt-4" <?= ($config_ia['modelo_gpt'] ?? '') == 'gpt-4' ? 'selected' : '' ?>>
                                        GPT-4 (Más preciso pero caro)
                                    </option>
                                    <option value="gpt-3.5-turbo" <?= ($config_ia['modelo_gpt'] ?? '') == 'gpt-3.5-turbo' ? 'selected' : '' ?>>
                                        GPT-3.5 Turbo (Antiguo)
                                    </option>
                                </select>
                                <small class="text-muted">
                                    <strong>Recomendado:</strong> GPT-4o Mini ($0.15 por millón tokens) vs GPT-4 ($30 por millón)
                                </small>
                            </div>

                            <div class="row">
                                <!-- Temperatura -->
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label>Temperatura (0-1)</label>
                                        <input type="number" step="0.1" min="0" max="1" class="form-control"
                                            name="temperatura" value="<?= $config_ia['temperatura'] ?? 0.7 ?>">
                                        <small class="text-muted">0 = Preciso, 1 = Creativo</small>
                                    </div>
                                </div>

                                <!-- Max Tokens -->
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label>Max Tokens</label>
                                        <input type="number" class="form-control" name="max_tokens"
                                            value="<?= $config_ia['max_tokens'] ?? 1000 ?>">
                                        <small class="text-muted">Longitud máxima de respuesta</small>
                                    </div>
                                </div>
                            </div>

                            <!-- Estado -->
                            <div class="form-group">
                                <div class="custom-control custom-switch">
                                    <input type="checkbox" class="custom-control-input"
                                        id="activo" name="activo" value="1"
                                        <?= ($config_ia['activo'] ?? 1) ? 'checked' : '' ?>>
                                    <label class="custom-control-label" for="activo">
                                        Activar GPT (si está desactivado, usa solo clasificador local)
                                    </label>
                                </div>
                            </div>

                            <hr>

                            <h5>Límites de Uso</h5>

                            <div class="row">
                                <!-- Consultas por día -->
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label>Consultas Máximas por Día</label>
                                        <input type="number" class="form-control" name="consultas_por_dia"
                                            value="<?= $config_ia['limite_diario_consultas'] ?? 100 ?>">
                                    </div>
                                </div>

                                <!-- Presupuesto mensual -->
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label>Presupuesto Mensual (S/.)</label>
                                        <input type="number" step="0.01" class="form-control"
                                            name="costo_maximo_dia" value="<?= $config_ia['presupuesto_mensual'] ?? 50.0 ?>">
                                        <small class="text-muted">En soles peruanos</small>
                                    </div>
                                </div>
                            </div>

                        </div>

                        <div class="card-footer">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Guardar Configuración
                            </button>
                            
                            <a href="<?= BASE_URL ?>dashboard.php" class="btn btn-secondary">
                                <i class="fas fa-arrow-left"></i> Volver
                            </a>
                        </div>
                    </form>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card card-success">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-lightbulb"></i> Estado Actual
                        </h3>
                    </div>
                    <div class="card-body">
                        <?php if ($config_ia): ?>
                            <p><strong>Modelo:</strong> <?= $config_ia['modelo_gpt'] ?? 'No configurado' ?></p>
                            <p><strong>Estado:</strong> 
                                <span class="badge badge-<?= $config_ia['activo'] ? 'success' : 'danger' ?>">
                                    <?= $config_ia['activo'] ? 'Activo' : 'Inactivo' ?>
                                </span>
                            </p>
                            <p><strong>Temperatura:</strong> <?= $config_ia['temperatura'] ?? 0.7 ?></p>
                            <p><strong>Consultas hoy:</strong> <?= $config_ia['consultas_realizadas_hoy'] ?? 0 ?> / <?= $config_ia['limite_diario_consultas'] ?? 100 ?></p>
                            <p><strong>Gasto mes:</strong> S/. <?= number_format($config_ia['gasto_mes_actual'] ?? 0, 2) ?> / S/. <?= number_format($config_ia['presupuesto_mensual'] ?? 50, 2) ?></p>
                        <?php else: ?>
                            <p class="text-warning">No hay configuración guardada</p>
                        <?php endif; ?>
                    </div>
                </div>

                <div class="card card-warning">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-exclamation-triangle"></i> Importante
                        </h3>
                    </div>
                    <div class="card-body">
                        <p><strong>Seguridad:</strong></p>
                        <ul>
                            <li>Nunca compartas tu API key</li>
                            <li>Revisa tus límites de uso</li>
                            <li>Monitorea los costos regularmente</li>
                        </ul>

                        <p><strong>Costos aproximados por consulta:</strong></p>
                        <ul>
                            <li><strong>GPT-4o Mini:</strong> ~$0.001 (MÁS ECONÓMICO) ⭐</li>
                            <li>GPT-4o: ~$0.005</li>
                            <li>GPT-4 Turbo: ~$0.01</li>
                            <li>GPT-4: ~$0.03 (30x más caro)</li>
                            <li>GPT-3.5: ~$0.002</li>
                        </ul>
                        <p class="text-muted">
                            <small>
                                <strong>Nota:</strong> GPT-4o Mini es 30 veces más barato que GPT-4 y suficientemente bueno para diagnósticos médicos.
                            </small>
                        </p>
                    </div>
                </div>

                <div class="card card-info">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-chart-bar"></i> Uso Actual
                        </h3>
                    </div>
                    <div class="card-body">
                        <?php
                        $uso_hoy = $db_instance->query(
                            "SELECT 
                                COUNT(*) as consultas,
                                SUM(costo_estimado) as costo_total
                            FROM log_consultas_ia
                            WHERE DATE(fecha_consulta) = CURDATE()"
                        )[0] ?? ['consultas' => 0, 'costo_total' => 0];
                        ?>
                        <p><strong>Hoy:</strong></p>
                        <p>Consultas: <?= $uso_hoy['consultas'] ?? 0 ?></p>
                        <p>Costo: $<?= number_format($uso_hoy['costo_total'] ?? 0, 4) ?></p>
                        
                        <?php
                        $uso_mes = $db_instance->query(
                            "SELECT 
                                COUNT(*) as consultas,
                                SUM(costo_estimado) as costo_total
                            FROM log_consultas_ia
                            WHERE MONTH(fecha_consulta) = MONTH(CURDATE())
                            AND YEAR(fecha_consulta) = YEAR(CURDATE())"
                        )[0] ?? ['consultas' => 0, 'costo_total' => 0];
                        ?>
                        <hr>
                        <p><strong>Este mes:</strong></p>
                        <p>Consultas: <?= $uso_mes['consultas'] ?? 0 ?></p>
                        <p>Costo: $<?= number_format($uso_mes['costo_total'] ?? 0, 2) ?></p>
                    </div>
                </div>
            </div>
        </div>

    </div>
</section>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>