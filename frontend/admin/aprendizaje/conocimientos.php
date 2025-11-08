<?php
$page_title = 'Conocimientos GPT';
$current_page = 'conocimientos';
$current_section = 'aprendizaje';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

// Obtener conocimientos en caché
$conocimientos = $db_instance->query(
    "SELECT * FROM conocimientos_cache ORDER BY created_at DESC LIMIT 100"
);

// Estadísticas
$stats = $db_instance->query(
    "SELECT 
        COUNT(*) as total,
        SUM(veces_usado) as total_usos,
        AVG(costo_tokens) as costo_promedio
    FROM conocimientos_cache"
)[0] ?? ['total' => 0, 'total_usos' => 0, 'costo_promedio' => 0];

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">Conocimientos GPT en Caché</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item active">Conocimientos</li>
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
                        <p>Conocimientos en Caché</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-database"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 col-6">
                <div class="small-box bg-success">
                    <div class="inner">
                        <h3><?= $stats['total_usos'] ?></h3>
                        <p>Total de Usos</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-recycle"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 col-6">
                <div class="small-box bg-warning">
                    <div class="inner">
                        <h3>$<?= number_format($stats['costo_promedio'], 4) ?></h3>
                        <p>Costo Promedio por Query</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-dollar-sign"></i>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Información -->
        <div class="alert alert-info">
            <h5><i class="fas fa-info-circle"></i> ¿Qué es esto?</h5>
            <p>
                Kairos guarda en caché las respuestas de GPT para evitar consultas repetidas y ahorrar costos.
                Cuando un síntoma similar se consulta, se usa la respuesta guardada en lugar de llamar a GPT nuevamente.
            </p>
        </div>
        
        <!-- Tabla de conocimientos -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <i class="fas fa-list"></i> Conocimientos Almacenados
                </h3>
            </div>
            
            <div class="card-body table-responsive p-0">
                <table class="table table-hover table-striped">
                    <thead>
                        <tr>
                            <th>Síntoma/Consulta</th>
                            <th>Respuesta</th>
                            <th>Veces Usado</th>
                            <th>Costo Tokens</th>
                            <th>Fecha</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (empty($conocimientos)): ?>
                            <tr>
                                <td colspan="5" class="text-center text-muted">
                                    <i class="fas fa-inbox"></i> No hay conocimientos en caché todavía
                                </td>
                            </tr>
                        <?php else: ?>
                            <?php foreach ($conocimientos as $conocimiento): ?>
                                <tr>
                                    <td>
                                        <strong><?= e(truncate($conocimiento['sintoma_consulta'], 50)) ?></strong>
                                    </td>
                                    <td>
                                        <button class="btn btn-sm btn-info" 
                                                onclick="verRespuesta(<?= $conocimiento['id'] ?>)">
                                            <i class="fas fa-eye"></i> Ver
                                        </button>
                                    </td>
                                    <td>
                                        <span class="badge badge-success">
                                            <?= $conocimiento['veces_usado'] ?>
                                        </span>
                                    </td>
                                    <td>
                                        <small>$<?= number_format($conocimiento['costo_tokens'], 4) ?></small>
                                    </td>
                                    <td>
                                        <small><?= formatFecha($conocimiento['created_at'], 'd/m/Y H:i') ?></small>
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

<!-- Modal para ver respuesta -->
<div class="modal fade" id="modalRespuesta">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h4 class="modal-title">Respuesta de GPT</h4>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body" id="contenidoRespuesta">
                <p class="text-muted">Cargando...</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cerrar</button>
            </div>
        </div>
    </div>
</div>

<script>
function verRespuesta(id) {
    $('#modalRespuesta').modal('show');
    $('#contenidoRespuesta').html('<p class="text-muted">Cargando...</p>');
    
    // Buscar el conocimiento en PHP (temporal, idealmente hacer AJAX)
    <?php foreach ($conocimientos as $c): ?>
        if (id === <?= $c['id'] ?>) {
            $('#contenidoRespuesta').html(`
                <h5>Consulta:</h5>
                <p><?= e($c['sintoma_consulta']) ?></p>
                <hr>
                <h5>Respuesta:</h5>
                <div class="alert alert-info">
                    <?= nl2br(e($c['respuesta_gpt'])) ?>
                </div>
            `);
        }
    <?php endforeach; ?>
}
</script>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>