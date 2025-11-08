<?php
$page_title = 'Patrones de Aprendizaje';
$current_page = 'patrones';
$current_section = 'aprendizaje';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

// Paginación
$page = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;
$per_page = 20;
$offset = ($page - 1) * $per_page;

// Filtro de intención
$filtro_intencion = $_GET['intencion'] ?? '';

// Contar total de patrones
$sql_count = "SELECT COUNT(*) as total FROM patrones_aprendidos";
if (!empty($filtro_intencion)) {
    $sql_count .= " WHERE intencion_detectada = ?";
    $total_result = $db_instance->query($sql_count, [$filtro_intencion]);
} else {
    $total_result = $db_instance->query($sql_count);
}

$total_patrones = $total_result[0]['total'] ?? 0;
$total_pages = ceil($total_patrones / $per_page);

// Obtener patrones con paginación - FORMA SIMPLE
$sql = "SELECT * FROM patrones_aprendidos";
if (!empty($filtro_intencion)) {
    $sql .= " WHERE intencion_detectada = '$filtro_intencion'";
}
$sql .= " ORDER BY veces_visto DESC, created_at DESC LIMIT $per_page OFFSET $offset";

$patrones = $db_instance->query($sql) ?: [];

// Estadísticas
$stats = $db_instance->query(
    "SELECT 
        COUNT(*) as total_patrones,
        SUM(veces_visto) as total_veces,
        AVG(confianza) as confianza_promedio
    FROM patrones_aprendidos"
)[0] ?? ['total_patrones' => 0, 'total_veces' => 0, 'confianza_promedio' => 0];

// Obtener intenciones únicas para filtro
$intenciones = $db_instance->query(
    "SELECT DISTINCT intencion_detectada FROM patrones_aprendidos ORDER BY intencion_detectada"
) ?: [];

// Últimos entrenamientos
$entrenamientos = $db_instance->query(
    "SELECT * FROM entrenamientos_modelo ORDER BY fecha DESC LIMIT 10"
) ?: [];

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">Patrones de Aprendizaje</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item active">Patrones ML</li>
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
                        <h3><?= $stats['total_patrones'] ?></h3>
                        <p>Patrones Aprendidos</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-brain"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 col-6">
                <div class="small-box bg-success">
                    <div class="inner">
                        <h3><?= $stats['total_veces'] ?></h3>
                        <p>Total Observaciones</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-eye"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 col-6">
                <div class="small-box bg-warning">
                    <div class="inner">
                        <h3><?= number_format($stats['confianza_promedio'] * 100, 0) ?>%</h3>
                        <p>Confianza Promedio</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Acciones -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-cogs"></i> Acciones
                        </h3>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-primary" onclick="ejecutarAprendizaje()">
                            <i class="fas fa-sync"></i> Ejecutar Aprendizaje Ahora
                        </button>
                        <span class="text-muted ml-3">
                            <i class="fas fa-info-circle"></i> 
                            Analiza consultas recientes y actualiza el modelo
                        </span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Patrones -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <i class="fas fa-list"></i> Patrones Detectados
                </h3>
                <div class="card-tools">
                    <!-- Filtro por intención -->
                    <?php if (!empty($intenciones)): ?>
                        <form method="get" class="form-inline">
                            <div class="form-group">
                                <label class="mr-2">Filtrar:</label>
                                <select name="intencion" class="form-control form-control-sm mr-2" onchange="this.form.submit()">
                                    <option value="">Todas las intenciones</option>
                                    <?php foreach ($intenciones as $int): ?>
                                        <option value="<?= e($int['intencion_detectada']) ?>" 
                                                <?= $filtro_intencion == $int['intencion_detectada'] ? 'selected' : '' ?>>
                                            <?= e($int['intencion_detectada']) ?>
                                        </option>
                                    <?php endforeach; ?>
                                </select>
                                <?php if ($filtro_intencion): ?>
                                    <a href="patrones.php" class="btn btn-sm btn-secondary">
                                        <i class="fas fa-times"></i> Limpiar
                                    </a>
                                <?php endif; ?>
                            </div>
                        </form>
                    <?php endif; ?>
                </div>
            </div>
            
            <div class="card-body table-responsive p-0">
                <table class="table table-hover table-striped">
                    <thead>
                        <tr>
                            <th>Intención</th>
                            <th>Texto de Ejemplo</th>
                            <th>Veces Visto</th>
                            <th>Confianza</th>
                            <th>Última Vez</th>
                            <th>Origen</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (empty($patrones)): ?>
                            <tr>
                                <td colspan="6" class="text-center text-muted">
                                    <i class="fas fa-inbox"></i> No hay patrones que mostrar
                                </td>
                            </tr>
                        <?php else: ?>
                            <?php foreach ($patrones as $patron): ?>
                                <tr>
                                    <td>
                                        <span class="badge badge-primary">
                                            <?= e($patron['intencion_detectada']) ?>
                                        </span>
                                    </td>
                                    <td><?= e(truncate($patron['texto_ejemplo'], 60)) ?></td>
                                    <td>
                                        <span class="badge badge-info">
                                            <?= $patron['veces_visto'] ?>
                                        </span>
                                    </td>
                                    <td>
                                        <?php 
                                        $confianza = $patron['confianza'] * 100;
                                        $color = $confianza >= 80 ? 'success' : ($confianza >= 60 ? 'warning' : 'danger');
                                        ?>
                                        <span class="badge badge-<?= $color ?>">
                                            <?= number_format($confianza, 0) ?>%
                                        </span>
                                    </td>
                                    <td>
                                        <small><?= formatFecha($patron['ultima_vez_visto'], 'd/m/Y H:i') ?></small>
                                    </td>
                                    <td>
                                        <span class="badge badge-secondary">
                                            <?= e($patron['origen']) ?>
                                        </span>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
            
            <!-- Paginación -->
            <?php if ($total_pages > 1): ?>
                <div class="card-footer clearfix">
                    <ul class="pagination pagination-sm m-0 float-right">
                        <!-- Anterior -->
                        <?php if ($page > 1): ?>
                            <li class="page-item">
                                <a class="page-link" href="?page=<?= $page - 1 ?><?= $filtro_intencion ? '&intencion=' . urlencode($filtro_intencion) : '' ?>">
                                    «
                                </a>
                            </li>
                        <?php endif; ?>
                        
                        <!-- Números de página -->
                        <?php
                        $start = max(1, $page - 2);
                        $end = min($total_pages, $page + 2);
                        
                        if ($start > 1): ?>
                            <li class="page-item">
                                <a class="page-link" href="?page=1<?= $filtro_intencion ? '&intencion=' . urlencode($filtro_intencion) : '' ?>">1</a>
                            </li>
                            <?php if ($start > 2): ?>
                                <li class="page-item disabled"><span class="page-link">...</span></li>
                            <?php endif; ?>
                        <?php endif; ?>
                        
                        <?php for ($i = $start; $i <= $end; $i++): ?>
                            <li class="page-item <?= $i == $page ? 'active' : '' ?>">
                                <a class="page-link" href="?page=<?= $i ?><?= $filtro_intencion ? '&intencion=' . urlencode($filtro_intencion) : '' ?>">
                                    <?= $i ?>
                                </a>
                            </li>
                        <?php endfor; ?>
                        
                        <?php if ($end < $total_pages): ?>
                            <?php if ($end < $total_pages - 1): ?>
                                <li class="page-item disabled"><span class="page-link">...</span></li>
                            <?php endif; ?>
                            <li class="page-item">
                                <a class="page-link" href="?page=<?= $total_pages ?><?= $filtro_intencion ? '&intencion=' . urlencode($filtro_intencion) : '' ?>">
                                    <?= $total_pages ?>
                                </a>
                            </li>
                        <?php endif; ?>
                        
                        <!-- Siguiente -->
                        <?php if ($page < $total_pages): ?>
                            <li class="page-item">
                                <a class="page-link" href="?page=<?= $page + 1 ?><?= $filtro_intencion ? '&intencion=' . urlencode($filtro_intencion) : '' ?>">
                                    »
                                </a>
                            </li>
                        <?php endif; ?>
                    </ul>
                    
                    <div class="float-left">
                        Mostrando <?= $offset + 1 ?> - <?= min($offset + $per_page, $total_patrones) ?> de <?= $total_patrones ?> patrones
                    </div>
                </div>
            <?php endif; ?>
        </div>
        
        <!-- Historial de Entrenamientos -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <i class="fas fa-history"></i> Historial de Entrenamientos
                </h3>
            </div>
            
            <div class="card-body table-responsive p-0">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Tipo</th>
                            <th>Muestras</th>
                            <th>Precisión</th>
                            <th>Duración</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (empty($entrenamientos)): ?>
                            <tr>
                                <td colspan="5" class="text-center text-muted">
                                    <i class="fas fa-inbox"></i> No hay entrenamientos registrados
                                </td>
                            </tr>
                        <?php else: ?>
                            <?php foreach ($entrenamientos as $ent): ?>
                                <tr>
                                    <td><?= formatFecha($ent['fecha'], 'd/m/Y H:i') ?></td>
                                    <td>
                                        <span class="badge badge-info">
                                            <?= e($ent['tipo_entrenamiento']) ?>
                                        </span>
                                    </td>
                                    <td><?= $ent['num_muestras'] ?></td>
                                    <td>
                                        <span class="badge badge-success">
                                            <?= number_format($ent['precision_alcanzada'] * 100, 1) ?>%
                                        </span>
                                    </td>
                                    <td><?= $ent['duracion_segundos'] ?>s</td>
                                </tr>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
        </div>
        
    </div>
</section>

<script>
function ejecutarAprendizaje() {
    if (!confirm('¿Ejecutar ciclo de aprendizaje?\n\nEsto analizará las consultas recientes y puede tomar unos minutos.')) {
        return;
    }
    
    const btn = event.target;
    const btnOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
    
    fetch('http://localhost:5000/api/aprender', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            dias: 7
        })
    })
    .then(response => {
        console.log('Respuesta HTTP:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Datos recibidos:', data);
        
        if (data.success) {
            let mensaje = '✅ Aprendizaje completado exitosamente\n\n';
            
            if (data.resultado) {
                if (data.resultado.patrones_nuevos !== undefined) {
                    mensaje += `📊 Patrones nuevos: ${data.resultado.patrones_nuevos}\n`;
                }
                if (data.resultado.clasificador) {
                    mensaje += `🎯 Precisión: ${(data.resultado.clasificador.precision * 100).toFixed(1)}%\n`;
                    mensaje += `📚 Muestras: ${data.resultado.clasificador.muestras}\n`;
                }
                if (data.resultado.modelo_reentrenado) {
                    mensaje += `\n✅ Modelo re-entrenado correctamente`;
                }
            }
            
            alert(mensaje);
            location.reload();
        } else {
            alert('❌ Error: ' + (data.error || 'Error desconocido'));
            btn.disabled = false;
            btn.innerHTML = btnOriginal;
        }
    })
    .catch(error => {
        console.error('Error completo:', error);
        alert('❌ Error de conexión con la API Python\n\n' + 
              'Verifica que esté corriendo:\n' +
              'python backend/api/app.py\n\n' +
              'Error técnico: ' + error.message);
        btn.disabled = false;
        btn.innerHTML = btnOriginal;
    });
}
</script>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>