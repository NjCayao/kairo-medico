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

// Obtener ID
$id = $_GET['id'] ?? 0;

if (!$id) {
    header('Location: historial.php?error=ID no especificado');
    exit;
}

// ✅ Obtener consulta completa con columnas REALES de BD
$sql = "SELECT 
    cm.*,
    u.nombre as paciente,
    u.dni,
    u.edad,
    u.celular,
    u.email,
    u.genero,
    u.alergias,
    u.condiciones_cronicas
FROM consultas_medicas cm
LEFT JOIN usuarios u ON cm.usuario_id = u.id
WHERE cm.id = ?";

$consultas = $db_instance->query($sql, [$id]);

$consulta = null;
if ($consultas && is_array($consultas) && count($consultas) > 0) {
    $consulta = $consultas[0];
}

if (!$consulta) {
    echo "<h3>❌ No se encontró la consulta</h3>";
    echo "<p>ID buscado: " . $id . "</p>";
    echo '<p><a href="historial.php">Volver al historial</a></p>';
    exit;
}

// Decodificar JSONs
$productos_ids = json_decode($consulta['productos_recomendados_json'] ?? '[]', true);
$mensajes = json_decode($consulta['mensajes_conversacion'] ?? '[]', true);

// Obtener productos si hay IDs
$productos = [];
if (!empty($productos_ids) && is_array($productos_ids)) {
    $placeholders = str_repeat('?,', count($productos_ids) - 1) . '?';
    $productos = $db_instance->query(
        "SELECT id, nombre, precio, descripcion_corta 
         FROM productos_naturales 
         WHERE id IN ($placeholders) AND activo = 1",
        $productos_ids
    ) ?? [];
}

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">
                    <i class="fas fa-file-medical"></i> Consulta #<?= $id ?>
                </h1>
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
        
        <!-- Botones superiores -->
        <div class="row mb-3">
            <div class="col-12">
                <a href="historial.php" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Volver
                </a>
                <button onclick="window.print()" class="btn btn-primary">
                    <i class="fas fa-print"></i> Imprimir Receta
                </button>
                <button onclick="exportarPDF()" class="btn btn-danger">
                    <i class="fas fa-file-pdf"></i> Exportar PDF
                </button>
            </div>
        </div>
        
        <div class="row">
            <!-- COLUMNA IZQUIERDA: Info del Paciente -->
            <div class="col-md-4">
                <!-- Datos del Paciente -->
                <div class="card card-primary card-outline">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-user"></i> Datos del Paciente
                        </h3>
                    </div>
                    <div class="card-body box-profile">
                        <div class="text-center">
                            <i class="fas fa-user-circle fa-5x text-primary"></i>
                        </div>
                        
                        <h3 class="profile-username text-center">
                            <?= htmlspecialchars($consulta['paciente'] ?? 'N/A') ?>
                        </h3>
                        
                        <ul class="list-group list-group-unbordered mb-3">
                            <li class="list-group-item">
                                <b><i class="fas fa-id-card mr-2"></i>DNI</b>
                                <span class="float-right"><?= htmlspecialchars($consulta['dni'] ?? 'N/A') ?></span>
                            </li>
                            <li class="list-group-item">
                                <b><i class="fas fa-birthday-cake mr-2"></i>Edad</b>
                                <span class="float-right"><?= $consulta['edad'] ?? 'N/A' ?> años</span>
                            </li>
                            <?php if (!empty($consulta['celular'])): ?>
                            <li class="list-group-item">
                                <b><i class="fas fa-mobile-alt mr-2"></i>Celular</b>
                                <span class="float-right"><?= htmlspecialchars($consulta['celular']) ?></span>
                            </li>
                            <?php endif; ?>
                            <?php if (!empty($consulta['email'])): ?>
                            <li class="list-group-item">
                                <b><i class="fas fa-envelope mr-2"></i>Email</b>
                                <span class="float-right text-sm"><?= htmlspecialchars($consulta['email']) ?></span>
                            </li>
                            <?php endif; ?>
                            <?php if (!empty($consulta['genero'])): ?>
                            <li class="list-group-item">
                                <b><i class="fas fa-venus-mars mr-2"></i>Género</b>
                                <span class="float-right"><?= ucfirst(htmlspecialchars($consulta['genero'])) ?></span>
                            </li>
                            <?php endif; ?>
                        </ul>
                    </div>
                </div>
                
                <!-- Info de la Sesión -->
                <div class="card card-info card-outline">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-info-circle"></i> Información de Consulta
                        </h3>
                    </div>
                    <div class="card-body">
                        <strong><i class="fas fa-calendar mr-1"></i> Fecha</strong>
                        <p class="text-muted">
                            <?= date('d/m/Y H:i:s', strtotime($consulta['fecha_consulta'])) ?>
                        </p>
                        
                        <strong><i class="fas fa-hashtag mr-1"></i> Sesión ID</strong>
                        <p class="text-muted text-sm">
                            <?= htmlspecialchars($consulta['sesion_id'] ?? 'N/A') ?>
                        </p>
                        
                        <strong><i class="fas fa-wifi mr-1"></i> Canal</strong>
                        <p class="text-muted">
                            <span class="badge badge-info">
                                <?= strtoupper(htmlspecialchars($consulta['canal'] ?? 'feria')) ?>
                            </span>
                        </p>
                        
                        <strong><i class="fas fa-cog mr-1"></i> Modo</strong>
                        <p class="text-muted">
                            <span class="badge badge-secondary">
                                <?= strtoupper(htmlspecialchars($consulta['modo_operacion'] ?? 'feria')) ?>
                            </span>
                        </p>
                        
                        <strong><i class="fas fa-clock mr-1"></i> Duración</strong>
                        <p class="text-muted">
                            <?= number_format($consulta['duracion_minutos'] ?? 0, 1) ?> minutos
                        </p>
                        
                        <strong><i class="fas fa-file-alt mr-1"></i> Estado</strong>
                        <p class="text-muted">
                            <span class="badge badge-success">
                                <?= strtoupper(htmlspecialchars($consulta['estado'] ?? 'completada')) ?>
                            </span>
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- COLUMNA DERECHA: Receta Médica -->
            <div class="col-md-8">
                <!-- Diagnóstico Principal -->
                <div class="card card-warning card-outline">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-stethoscope"></i> Diagnóstico
                        </h3>
                        <div class="card-tools">
                            <?php if ($consulta['confianza_diagnostico']): ?>
                                <?php 
                                $confianza = $consulta['confianza_diagnostico'] * 100;
                                $color = $confianza >= 80 ? 'success' : ($confianza >= 60 ? 'warning' : 'danger');
                                ?>
                                <span class="badge badge-<?= $color ?> badge-lg">
                                    <i class="fas fa-chart-line"></i> 
                                    Confianza: <?= number_format($confianza, 0) ?>%
                                </span>
                            <?php endif; ?>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-12">
                                <h5><i class="fas fa-exclamation-circle text-danger"></i> Síntoma Principal:</h5>
                                <p class="lead text-primary">
                                    <?= htmlspecialchars($consulta['diagnostico_kairos'] ?? 'N/A') ?>
                                </p>
                            </div>
                        </div>
                        
                        <?php if ($consulta['sintomas_adicionales']): ?>
                        <div class="row mt-2">
                            <div class="col-12">
                                <h5><i class="fas fa-list-ul"></i> Síntomas Adicionales:</h5>
                                <p><?= nl2br(htmlspecialchars($consulta['sintomas_adicionales'])) ?></p>
                            </div>
                        </div>
                        <?php endif; ?>
                        
                        <?php if ($consulta['diagnostico_kairos']): ?>
                        <div class="alert alert-success mt-3">
                            <h5><i class="fas fa-diagnoses"></i> Diagnóstico de Kairos:</h5>
                            <h4 class="text-success">
                                <strong><?= htmlspecialchars($consulta['diagnostico_kairos']) ?></strong>
                            </h4>
                        </div>
                        <?php endif; ?>
                        
                        <?php if ($consulta['causas_probables']): ?>
                        <div class="row mt-2">
                            <div class="col-12">
                                <h5><i class="fas fa-question-circle"></i> Causas Probables:</h5>
                                <p><?= nl2br(htmlspecialchars($consulta['causas_probables'])) ?></p>
                            </div>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
                
                <!-- Receta Médica Completa -->
                <div class="card card-success card-outline">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-prescription"></i> Receta Médica Completa
                        </h3>
                    </div>
                    <div class="card-body">
                        <?php if ($consulta['receta_completa']): ?>
                            <div class="receta-contenido" style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f8f9fa; padding: 20px; border-radius: 5px; border-left: 4px solid #28a745;">
                                <?= htmlspecialchars($consulta['receta_completa']) ?>
                            </div>
                        <?php else: ?>
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle"></i>
                                No hay receta médica generada para esta consulta.
                            </div>
                        <?php endif; ?>
                    </div>
                </div>
                
                <!-- Productos Recomendados -->
                <?php if (!empty($productos)): ?>
                <div class="card card-primary card-outline">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-pills"></i> Productos Naturales Recomendados
                        </h3>
                        <div class="card-tools">
                            <span class="badge badge-primary"><?= count($productos) ?> productos</span>
                        </div>
                    </div>
                    <div class="card-body table-responsive p-0">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Producto</th>
                                    <th>Descripción</th>
                                    <th class="text-right">Precio</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($productos as $producto): ?>
                                <tr>
                                    <td><?= $producto['id'] ?></td>
                                    <td><strong><?= htmlspecialchars($producto['nombre']) ?></strong></td>
                                    <td><small><?= htmlspecialchars($producto['descripcion_corta'] ?? '-') ?></small></td>
                                    <td class="text-right">
                                        <span class="badge badge-success">
                                            S/. <?= number_format($producto['precio'], 2) ?>
                                        </span>
                                    </td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                </div>
                <?php endif; ?>
                
                <!-- Consejos y Recomendaciones -->
                <?php if ($consulta['consejos_dieta'] || $consulta['consejos_habitos']): ?>
                <div class="card card-info card-outline">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-lightbulb"></i> Recomendaciones y Consejos
                        </h3>
                    </div>
                    <div class="card-body">
                        <?php if ($consulta['consejos_dieta']): ?>
                        <h5><i class="fas fa-utensils text-success"></i> Alimentación Recomendada:</h5>
                        <div class="pl-3">
                            <?= nl2br(htmlspecialchars($consulta['consejos_dieta'])) ?>
                        </div>
                        <hr>
                        <?php endif; ?>
                        
                        <?php if ($consulta['consejos_habitos']): ?>
                        <h5><i class="fas fa-heart text-danger"></i> Hábitos Saludables:</h5>
                        <div class="pl-3">
                            <?= nl2br(htmlspecialchars($consulta['consejos_habitos'])) ?>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
                <?php endif; ?>
                
                <!-- Conversación Completa -->
                <?php if (!empty($mensajes) && is_array($mensajes)): ?>
                <div class="card collapsed-card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-comments"></i> Conversación con el Paciente
                        </h3>
                        <div class="card-tools">
                            <span class="badge badge-info"><?= count($mensajes) ?> mensajes</span>
                            <button type="button" class="btn btn-tool" data-card-widget="collapse">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                    <div class="card-body" style="display: none; max-height: 500px; overflow-y: auto;">
                        <div class="direct-chat-messages">
                            <?php foreach ($mensajes as $msg): ?>
                                <?php if ($msg['role'] == 'user'): ?>
                                    <!-- Mensaje del usuario -->
                                    <div class="direct-chat-msg">
                                        <div class="direct-chat-infos clearfix">
                                            <span class="direct-chat-name float-left">
                                                <i class="fas fa-user text-primary"></i> Paciente
                                            </span>
                                            <?php if (isset($msg['timestamp'])): ?>
                                            <span class="direct-chat-timestamp float-right">
                                                <?= date('H:i:s', strtotime($msg['timestamp'])) ?>
                                            </span>
                                            <?php endif; ?>
                                        </div>
                                        <div class="direct-chat-text bg-light">
                                            <?= nl2br(htmlspecialchars($msg['content'])) ?>
                                        </div>
                                    </div>
                                <?php else: ?>
                                    <!-- Mensaje de Kairos -->
                                    <div class="direct-chat-msg right">
                                        <div class="direct-chat-infos clearfix">
                                            <span class="direct-chat-name float-right">
                                                <i class="fas fa-robot text-success"></i> Kairos
                                            </span>
                                            <?php if (isset($msg['timestamp'])): ?>
                                            <span class="direct-chat-timestamp float-left">
                                                <?= date('H:i:s', strtotime($msg['timestamp'])) ?>
                                            </span>
                                            <?php endif; ?>
                                        </div>
                                        <div class="direct-chat-text bg-success">
                                            <?= nl2br(htmlspecialchars($msg['content'])) ?>
                                        </div>
                                    </div>
                                <?php endif; ?>
                            <?php endforeach; ?>
                        </div>
                    </div>
                </div>
                <?php endif; ?>
            </div>
        </div>
        
    </div>
</section>

<style>
/* Estilos para impresión */
@media print {
    .content-header,
    .btn,
    .breadcrumb,
    .card-tools,
    .sidebar,
    .main-header,
    .main-footer,
    .direct-chat-messages {
        display: none !important;
    }
    
    .card {
        border: 1px solid #ddd !important;
        box-shadow: none !important;
        page-break-inside: avoid;
    }
    
    .receta-contenido {
        border: 2px solid #28a745 !important;
    }
}

/* Estilos para mensajes de chat */
.direct-chat-messages {
    padding: 10px;
}

.direct-chat-msg {
    margin-bottom: 15px;
}

.direct-chat-text {
    padding: 10px;
    border-radius: 5px;
    position: relative;
}

.direct-chat-msg.right .direct-chat-text {
    margin-left: 50px;
}

.direct-chat-msg:not(.right) .direct-chat-text {
    margin-right: 50px;
}
</style>

<script>
function exportarPDF() {
    alert('Función de exportar PDF en desarrollo');
    // Aquí puedes implementar jsPDF o similar
}
</script>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>