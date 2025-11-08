<?php
$page_title = 'Detalle de Consulta';
$current_page = 'consultas_historial';
$current_section = 'consultas';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

$id = $_GET['id'] ?? 0;

// Obtener consulta completa
$consulta = $db_instance->query(
    "SELECT 
        cm.*,
        u.nombre as paciente,
        u.dni,
        u.edad,
        u.telefono,
        d.condicion_detectada,
        d.confianza,
        d.causas_probables,
        d.recomendaciones_generales,
        d.alimentacion_recomendada,
        d.habitos_sugeridos,
        d.created_at as fecha_diagnostico,
        sa.evento,
        sa.ubicacion,
        sa.dispositivo,
        sa.duracion_minutos
    FROM consultas_medicas cm
    LEFT JOIN usuarios u ON cm.usuario_id = u.id
    LEFT JOIN diagnosticos d ON cm.diagnostico_id = d.id
    LEFT JOIN sesiones_autonomas sa ON cm.sesion_autonoma_id = sa.id
    WHERE cm.id = ?",
    [$id]
)[0] ?? null;

if (!$consulta) {
    header('Location: historial.php?error=Consulta no encontrada');
    exit;
}

// Obtener productos recomendados
$productos = $db_instance->query(
    "SELECT 
        p.nombre,
        p.precio,
        dp.dosis_personalizada,
        dp.duracion_tratamiento
    FROM diagnosticos_productos dp
    INNER JOIN productos_naturales p ON dp.producto_id = p.id
    WHERE dp.diagnostico_id = ?",
    [$consulta['diagnostico_id']]
);

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">Detalle de Consulta #<?= $id ?></h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item"><a href="historial.php">Consultas</a></li>
                    <li class="breadcrumb-item active">Detalle</li>
                </ol>
            </div>
        </div>
    </div>
</div>

<!-- Main content -->
<section class="content">
    <div class="container-fluid">
        
        <div class="row">
            <!-- Datos del Paciente -->
            <div class="col-md-4">
                <div class="card card-primary">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-user"></i> Datos del Paciente
                        </h3>
                    </div>
                    <div class="card-body">
                        <dl>
                            <dt>Nombre:</dt>
                            <dd><?= e($consulta['paciente']) ?></dd>
                            
                            <dt>DNI:</dt>
                            <dd><?= e($consulta['dni']) ?></dd>
                            
                            <dt>Edad:</dt>
                            <dd><?= $consulta['edad'] ?> años</dd>
                            
                            <?php if ($consulta['telefono']): ?>
                                <dt>Teléfono:</dt>
                                <dd><?= e($consulta['telefono']) ?></dd>
                            <?php endif; ?>
                        </dl>
                    </div>
                </div>
                
                <div class="card card-info">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-info-circle"></i> Info de Sesión
                        </h3>
                    </div>
                    <div class="card-body">
                        <dl>
                            <dt>Fecha:</dt>
                            <dd><?= formatFecha($consulta['fecha'], 'd/m/Y H:i:s') ?></dd>
                            
                            <dt>Evento:</dt>
                            <dd><?= e($consulta['evento'] ?? 'N/A') ?></dd>
                            
                            <dt>Ubicación:</dt>
                            <dd><?= e($consulta['ubicacion'] ?? 'N/A') ?></dd>
                            
                            <dt>Duración:</dt>
                            <dd><?= $consulta['duracion_minutos'] ?? 0 ?> minutos</dd>
                        </dl>
                    </div>
                </div>
            </div>
            
            <!-- Consulta y Diagnóstico -->
            <div class="col-md-8">
                <div class="card card-warning">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-stethoscope"></i> Consulta Médica
                        </h3>
                    </div>
                    <div class="card-body">
                        <h5>Síntoma Principal:</h5>
                        <p class="lead"><?= e($consulta['sintoma_principal']) ?></p>
                        
                        <?php if ($consulta['sintomas_adicionales']): ?>
                            <h5>Síntomas Adicionales:</h5>
                            <p><?= e($consulta['sintomas_adicionales']) ?></p>
                        <?php endif; ?>
                        
                        <?php if ($consulta['notas']): ?>
                            <h5>Notas:</h5>
                            <p><?= nl2br(e($consulta['notas'])) ?></p>
                        <?php endif; ?>
                    </div>
                </div>
                
                <?php if ($consulta['condicion_detectada']): ?>
                    <div class="card card-success">
                        <div class="card-header">
                            <h3 class="card-title">
                                <i class="fas fa-diagnoses"></i> Diagnóstico
                            </h3>
                            <div class="card-tools">
                                <span class="badge badge-light">
                                    Confianza: <?= number_format($consulta['confianza'] * 100, 0) ?>%
                                </span>
                            </div>
                        </div>
                        <div class="card-body">
                            <h5>Condición Detectada:</h5>
                            <p class="lead"><?= e($consulta['condicion_detectada']) ?></p>
                            
                            <?php if ($consulta['causas_probables']): ?>
                                <h5>Causas Probables:</h5>
                                <p><?= nl2br(e($consulta['causas_probables'])) ?></p>
                            <?php endif; ?>
                            
                            <?php if ($consulta['recomendaciones_generales']): ?>
                                <h5>Recomendaciones:</h5>
                                <p><?= nl2br(e($consulta['recomendaciones_generales'])) ?></p>
                            <?php endif; ?>
                            
                            <?php if ($consulta['alimentacion_recomendada']): ?>
                                <h5>Alimentación:</h5>
                                <p><?= nl2br(e($consulta['alimentacion_recomendada'])) ?></p>
                            <?php endif; ?>
                        </div>
                    </div>
                <?php endif; ?>
                
                <?php if (!empty($productos)): ?>
                    <div class="card card-primary">
                        <div class="card-header">
                            <h3 class="card-title">
                                <i class="fas fa-pills"></i> Productos Recomendados
                            </h3>
                        </div>
                        <div class="card-body">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>Producto</th>
                                        <th>Precio</th>
                                        <th>Dosis</th>
                                        <th>Duración</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php foreach ($productos as $producto): ?>
                                        <tr>
                                            <td><?= e($producto['nombre']) ?></td>
                                            <td><?= formatPrecio($producto['precio']) ?></td>
                                            <td><?= e($producto['dosis_personalizada'] ?? '-') ?></td>
                                            <td><?= e($producto['duracion_tratamiento'] ?? '-') ?></td>
                                        </tr>
                                    <?php endforeach; ?>
                                </tbody>
                            </table>
                        </div>
                    </div>
                <?php endif; ?>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <a href="historial.php" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Volver al Historial
                </a>
            </div>
        </div>
        
    </div>
</section>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>