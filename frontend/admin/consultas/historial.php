<?php
$page_title = 'Historial de Consultas';
$current_page = 'consultas_historial';
$current_section = 'consultas';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

// Filtros
$fecha_desde = $_GET['fecha_desde'] ?? date('Y-m-d', strtotime('-30 days'));
$fecha_hasta = $_GET['fecha_hasta'] ?? date('Y-m-d');
$buscar = $_GET['buscar'] ?? '';

// ✅ Query CORREGIDO con columnas reales
$sql = "SELECT 
    cm.id,
    cm.fecha_consulta as fecha,
    cm.sintoma_principal,
    cm.diagnostico_kairos as condicion_detectada,
    cm.confianza_diagnostico as confianza,
    cm.duracion_minutos,
    cm.canal,
    cm.modo_operacion,
    cm.sesion_id,
    u.nombre as paciente,
    u.dni,
    u.edad
FROM consultas_medicas cm
LEFT JOIN usuarios u ON cm.usuario_id = u.id
WHERE DATE(cm.fecha_consulta) BETWEEN ? AND ?";

$params = [$fecha_desde, $fecha_hasta];

if (!empty($buscar)) {
    $sql .= " AND (u.nombre LIKE ? OR u.dni LIKE ? OR cm.sintoma_principal LIKE ?)";
    $params[] = "%$buscar%";
    $params[] = "%$buscar%";
    $params[] = "%$buscar%";
}

$sql .= " ORDER BY cm.fecha_consulta DESC LIMIT 100";

$consultas = $db_instance->query($sql, $params);
if ($consultas === false) {
    $consultas = [];
}

// ✅ Estadísticas CORREGIDAS
$stats = $db_instance->query(
    "SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT usuario_id) as pacientes_unicos,
        AVG(confianza_diagnostico) as confianza_promedio
    FROM consultas_medicas
    WHERE DATE(fecha_consulta) BETWEEN ? AND ?",
    [$fecha_desde, $fecha_hasta]
)[0] ?? ['total' => 0, 'pacientes_unicos' => 0, 'confianza_promedio' => 0];

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">Historial de Consultas</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item active">Consultas</li>
                </ol>
            </div>
        </div>
    </div>
</div>

<!-- Main content -->
<section class="content">
    <div class="container-fluid">
        
        <!-- Estadísticas -->
        <div class="row">
            <div class="col-lg-4 col-6">
                <div class="small-box bg-info">
                    <div class="inner">
                        <h3><?= $stats['total'] ?></h3>
                        <p>Total Consultas</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-notes-medical"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 col-6">
                <div class="small-box bg-success">
                    <div class="inner">
                        <h3><?= $stats['pacientes_unicos'] ?></h3>
                        <p>Pacientes Únicos</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-users"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 col-6">
                <div class="small-box bg-warning">
                    <div class="inner">
                        <h3><?= number_format(($stats['confianza_promedio'] ?? 0) * 100, 1) ?>%</h3>
                        <p>Confianza Promedio</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Filtros -->
        <div class="card collapsed-card">
            <div class="card-header">
                <h3 class="card-title">
                    <i class="fas fa-filter"></i> Filtros
                </h3>
                <div class="card-tools">
                    <button type="button" class="btn btn-tool" data-card-widget="collapse">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
            <div class="card-body" style="display: none;">
                <form method="get" class="form-inline">
                    <div class="form-group mr-3">
                        <label class="mr-2">Desde:</label>
                        <input type="date" class="form-control" name="fecha_desde" 
                               value="<?= htmlspecialchars($fecha_desde) ?>">
                    </div>
                    
                    <div class="form-group mr-3">
                        <label class="mr-2">Hasta:</label>
                        <input type="date" class="form-control" name="fecha_hasta" 
                               value="<?= htmlspecialchars($fecha_hasta) ?>">
                    </div>
                    
                    <div class="form-group mr-3">
                        <label class="mr-2">Buscar:</label>
                        <input type="text" class="form-control" name="buscar" 
                               value="<?= htmlspecialchars($buscar) ?>" placeholder="Nombre, DNI o síntoma">
                    </div>
                    
                    <button type="submit" class="btn btn-primary mr-2">
                        <i class="fas fa-search"></i> Filtrar
                    </button>
                    
                    <a href="historial.php" class="btn btn-secondary">
                        <i class="fas fa-redo"></i> Limpiar
                    </a>
                </form>
            </div>
        </div>
        
        <!-- Tabla de consultas -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <i class="fas fa-list"></i> Consultas Registradas
                </h3>
                <div class="card-tools">
                    <span class="badge badge-primary"><?= is_array($consultas) ? count($consultas) : 0 ?> registros</span>
                </div>
            </div>
            
            <div class="card-body table-responsive p-0">
                <table class="table table-hover table-striped">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Paciente</th>
                            <th>DNI</th>
                            <th>Edad</th>                            
                            <th>Diagnóstico</th>
                            <th>Confianza</th>
                            <th>Duración</th>
                            <th>Canal</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (empty($consultas)): ?>
                            <tr>
                                <td colspan="10" class="text-center text-muted">
                                    <i class="fas fa-inbox"></i> No hay consultas registradas en este período
                                </td>
                            </tr>
                        <?php else: ?>
                            <?php foreach ($consultas as $consulta): ?>
                                <tr>
                                    <td>
                                        <small><?= date('d/m/Y H:i', strtotime($consulta['fecha'])) ?></small>
                                    </td>
                                    <td><?= htmlspecialchars($consulta['paciente'] ?? '-') ?></td>
                                    <td><?= htmlspecialchars($consulta['dni'] ?? '-') ?></td>
                                    <td><?= ($consulta['edad'] ?? '-') ?> años</td>                                    
                                    <td>
                                        <?php if ($consulta['condicion_detectada']): ?>
                                            <?= htmlspecialchars(substr($consulta['condicion_detectada'], 0, 30)) ?>
                                        <?php else: ?>
                                            <span class="text-muted">-</span>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <?php if ($consulta['confianza']): ?>
                                            <?php 
                                            $confianza = $consulta['confianza'] * 100;
                                            $color = $confianza >= 80 ? 'success' : ($confianza >= 60 ? 'warning' : 'danger');
                                            ?>
                                            <span class="badge badge-<?= $color ?>">
                                                <?= number_format($confianza, 0) ?>%
                                            </span>
                                        <?php else: ?>
                                            <span class="text-muted">-</span>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <small><?= $consulta['duracion_minutos'] ?? '-' ?> min</small>
                                    </td>
                                    <td>
                                        <span class="badge badge-info">
                                            <?= htmlspecialchars($consulta['canal'] ?? 'feria') ?>
                                        </span>
                                    </td>
                                    <td>
                                        <a href="detalle.php?id=<?= $consulta['id'] ?>" 
                                           class="btn btn-sm btn-info" 
                                           target="_blank"
                                           title="Ver detalle"
                                           onclick="console.log('Click en ID: <?= $consulta['id'] ?>')">
                                            <i class="fas fa-eye"></i>
                                        </a>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
        </div>
        
    </div>
</section>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>