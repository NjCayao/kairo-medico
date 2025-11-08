<?php
$page_title = 'Dashboard';
$current_page = 'dashboard';

define('BASE_PATH', dirname(__DIR__));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

// Estadísticas principales
try {
    $stats = [
        'total_consultas' => $db->query("SELECT COUNT(*) as total FROM consultas_medicas")->fetch()['total'] ?? 0,
        'consultas_hoy' => $db->query("SELECT COUNT(*) as total FROM consultas_medicas WHERE DATE(fecha_consulta) = CURDATE()")->fetch()['total'] ?? 0,
        'total_patrones' => $db->query("SELECT COUNT(*) as total FROM patrones_aprendidos")->fetch()['total'] ?? 0,
        'total_productos' => $db->query("SELECT COUNT(*) as total FROM productos_naturales WHERE activo = 1")->fetch()['total'] ?? 0
    ];
} catch (Exception $e) {
    $stats = ['total_consultas' => 0, 'consultas_hoy' => 0, 'total_patrones' => 0, 'total_productos' => 0];
}

// Últimas consultas
try {
    $stmt = $db->query("
        SELECT 
            cm.id,
            cm.fecha_consulta,
            cm.sintoma_principal,
            cm.diagnostico_kairos,
            u.nombre as paciente,
            u.dni
        FROM consultas_medicas cm 
        LEFT JOIN usuarios u ON cm.usuario_id = u.id 
        ORDER BY cm.fecha_consulta DESC 
        LIMIT 5
    ");
    $consultas = $stmt->fetchAll();
} catch (Exception $e) {
    $consultas = [];
}

// Consultas por día (últimos 7 días)
try {
    $stmt = $db->query("
        SELECT DATE(fecha_consulta) as dia, COUNT(*) as total 
        FROM consultas_medicas 
        WHERE fecha_consulta >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(fecha_consulta)
        ORDER BY dia ASC
    ");
    $consultas_semana = $stmt->fetchAll();
} catch (Exception $e) {
    $consultas_semana = [];
}

// Preparar datos para el gráfico
$dias_labels = [];
$dias_valores = [];

for ($i = 6; $i >= 0; $i--) {
    $fecha = date('Y-m-d', strtotime("-$i days"));
    $dias_labels[] = date('d/m', strtotime($fecha));
    
    $encontrado = false;
    foreach ($consultas_semana as $cs) {
        if ($cs['dia'] == $fecha) {
            $dias_valores[] = $cs['total'];
            $encontrado = true;
            break;
        }
    }
    if (!$encontrado) {
        $dias_valores[] = 0;
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
                <h1 class="m-0">Dashboard</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item active">Dashboard</li>
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
            <div class="col-lg-3 col-6">
                <div class="small-box bg-info">
                    <div class="inner">
                        <h3><?= $stats['total_consultas'] ?></h3>
                        <p>Total Consultas</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-notes-medical"></i>
                    </div>
                    <a href="<?= BASE_URL ?>admin/consultas/historial.php" class="small-box-footer">
                        Ver más <i class="fas fa-arrow-circle-right"></i>
                    </a>
                </div>
            </div>
            
            <div class="col-lg-3 col-6">
                <div class="small-box bg-success">
                    <div class="inner">
                        <h3><?= $stats['consultas_hoy'] ?></h3>
                        <p>Consultas Hoy</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-calendar-day"></i>
                    </div>
                    <a href="<?= BASE_URL ?>admin/consultas/historial.php" class="small-box-footer">
                        Ver más <i class="fas fa-arrow-circle-right"></i>
                    </a>
                </div>
            </div>
            
            <div class="col-lg-3 col-6">
                <div class="small-box bg-warning">
                    <div class="inner">
                        <h3><?= $stats['total_patrones'] ?></h3>
                        <p>Patrones ML</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <a href="<?= BASE_URL ?>admin/aprendizaje/patrones.php" class="small-box-footer">
                        Ver más <i class="fas fa-arrow-circle-right"></i>
                    </a>
                </div>
            </div>
            
            <div class="col-lg-3 col-6">
                <div class="small-box bg-danger">
                    <div class="inner">
                        <h3><?= $stats['total_productos'] ?></h3>
                        <p>Productos Activos</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-pills"></i>
                    </div>
                    <a href="<?= BASE_URL ?>admin/productos/listar.php" class="small-box-footer">
                        Ver más <i class="fas fa-arrow-circle-right"></i>
                    </a>
                </div>
            </div>
        </div>
        
        <!-- Gráficos y Tablas -->
        <div class="row">
            <!-- Gráfico de consultas -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-chart-line"></i> Consultas de la Semana
                        </h3>
                    </div>
                    <div class="card-body">
                        <canvas id="chartConsultas" height="80"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Accesos rápidos -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-rocket"></i> Accesos Rápidos
                        </h3>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="<?= BASE_URL ?>admin/productos/crear.php" class="btn btn-primary btn-block mb-2">
                                <i class="fas fa-plus"></i> Nuevo Producto
                            </a>
                            <a href="<?= BASE_URL ?>admin/consultas/historial.php" class="btn btn-info btn-block mb-2">
                                <i class="fas fa-history"></i> Ver Consultas
                            </a>
                            <a href="<?= BASE_URL ?>admin/aprendizaje/patrones.php" class="btn btn-warning btn-block mb-2">
                                <i class="fas fa-brain"></i> Patrones ML
                            </a>
                            <a href="<?= BASE_URL ?>admin/configuracion/general.php" class="btn btn-secondary btn-block">
                                <i class="fas fa-cog"></i> Configuración
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Últimas Consultas -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-clock"></i> Últimas Consultas
                        </h3>
                        <div class="card-tools">
                            <a href="<?= BASE_URL ?>admin/consultas/historial.php" class="btn btn-sm btn-primary">
                                Ver todas
                            </a>
                        </div>
                    </div>
                    <div class="card-body table-responsive p-0">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Fecha</th>
                                    <th>Paciente</th>
                                    <th>DNI</th>
                                    <th>Síntoma</th>
                                    <th>Diagnóstico</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php if (empty($consultas)): ?>
                                    <tr>
                                        <td colspan="6" class="text-center text-muted py-4">
                                            <i class="fas fa-inbox fa-3x mb-3 d-block"></i>
                                            <p>No hay consultas registradas todavía</p>
                                            <small class="text-muted">Las consultas aparecerán aquí cuando se realicen</small>
                                        </td>
                                    </tr>
                                <?php else: ?>
                                    <?php foreach ($consultas as $consulta): ?>
                                        <tr>
                                            <td>
                                                <small><?= date('d/m/Y H:i', strtotime($consulta['fecha_consulta'])) ?></small>
                                            </td>
                                            <td><?= htmlspecialchars($consulta['paciente'] ?? 'Anónimo') ?></td>
                                            <td><?= htmlspecialchars($consulta['dni'] ?? '-') ?></td>
                                            <td>
                                                <span class="text-primary">
                                                    <?= htmlspecialchars(mb_substr($consulta['sintoma_principal'], 0, 40)) ?>...
                                                </span>
                                            </td>
                                            <td>
                                                <?php if (!empty($consulta['diagnostico_kairos'])): ?>
                                                    <?= htmlspecialchars(mb_substr($consulta['diagnostico_kairos'], 0, 30)) ?>...
                                                <?php else: ?>
                                                    <span class="text-muted">-</span>
                                                <?php endif; ?>
                                            </td>
                                            <td>
                                                <a href="<?= BASE_URL ?>admin/consultas/detalle.php?id=<?= $consulta['id'] ?>" 
                                                   class="btn btn-sm btn-info" 
                                                   title="Ver detalle">
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
        </div>
        
    </div>
</section>

<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script>
const ctx = document.getElementById('chartConsultas').getContext('2d');
new Chart(ctx, {
    type: 'line',
    data: {
        labels: <?= json_encode($dias_labels) ?>,
        datasets: [{
            label: 'Consultas',
            data: <?= json_encode($dias_valores) ?>,
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    stepSize: 1
                }
            }
        }
    }
});
</script>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>