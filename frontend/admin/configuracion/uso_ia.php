<?php
$page_title = 'Uso de IA';
$current_page = 'uso_ia';
$current_section = 'configuracion';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

// Obtener configuración
$config_ia = $db_instance->query(
    "SELECT * FROM configuracion_ia ORDER BY id DESC LIMIT 1"
)[0] ?? null;

// Estadísticas del día
$stats_hoy = $db_instance->query(
    "SELECT 
        COUNT(*) as total_consultas,
        COALESCE(SUM(tokens_usados), 0) as total_tokens,
        COALESCE(SUM(costo_estimado), 0) as costo_total,
        COALESCE(AVG(tiempo_respuesta_ms), 0) as tiempo_promedio
    FROM log_consultas_ia
    WHERE DATE(fecha_consulta) = CURDATE()"
)[0] ?? ['total_consultas' => 0, 'total_tokens' => 0, 'costo_total' => 0, 'tiempo_promedio' => 0];

// Estadísticas del mes
$stats_mes = $db_instance->query(
    "SELECT 
        COUNT(*) as total_consultas,
        COALESCE(SUM(tokens_usados), 0) as total_tokens,
        COALESCE(SUM(costo_estimado), 0) as costo_total
    FROM log_consultas_ia
    WHERE MONTH(fecha_consulta) = MONTH(CURDATE())
    AND YEAR(fecha_consulta) = YEAR(CURDATE())"
)[0] ?? ['total_consultas' => 0, 'total_tokens' => 0, 'costo_total' => 0];

// Desglose por modelo
$por_modelo = $db_instance->query(
    "SELECT 
        modelo,
        COUNT(*) as consultas,
        COALESCE(SUM(tokens_usados), 0) as tokens,
        COALESCE(SUM(costo_estimado), 0) as costo
    FROM log_consultas_ia
    WHERE MONTH(fecha_consulta) = MONTH(CURDATE())
    GROUP BY modelo
    ORDER BY consultas DESC"
) ?? [];

// Últimas consultas
$ultimas = $db_instance->query(
    "SELECT 
        fecha_consulta,
        sintoma,
        modelo,
        COALESCE(tokens_usados, 0) as tokens_usados,
        COALESCE(costo_estimado, 0) as costo_estimado,
        COALESCE(tiempo_respuesta_ms, 0) as tiempo_respuesta_ms,
        exitosa
    FROM log_consultas_ia
    ORDER BY fecha_consulta DESC
    LIMIT 20"
) ?? [];

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">💰 Uso de Inteligencia Artificial</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item active">Uso IA</li>
                </ol>
            </div>
        </div>
    </div>
</div>

<section class="content">
    <div class="container-fluid">

        <!-- Resumen de hoy -->
        <div class="row">
            <div class="col-lg-3 col-6">
                <div class="small-box bg-info">
                    <div class="inner">
                        <h3><?= intval($stats_hoy['total_consultas']) ?></h3>
                        <p>Consultas Hoy</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-comments"></i>
                    </div>
                </div>
            </div>

            <div class="col-lg-3 col-6">
                <div class="small-box bg-success">
                    <div class="inner">
                        <h3>$<?= number_format(floatval($stats_hoy['costo_total']), 4) ?></h3>
                        <p>Costo Hoy (USD)</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-dollar-sign"></i>
                    </div>
                </div>
            </div>

            <div class="col-lg-3 col-6">
                <div class="small-box bg-warning">
                    <div class="inner">
                        <h3><?= number_format(floatval($stats_hoy['total_tokens'])) ?></h3>
                        <p>Tokens Usados Hoy</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-microchip"></i>
                    </div>
                </div>
            </div>

            <div class="col-lg-3 col-6">
                <div class="small-box bg-danger">
                    <div class="inner">
                        <h3><?= $config_ia ? intval($config_ia['consultas_realizadas_hoy']) : 0 ?> / <?= $config_ia ? intval($config_ia['limite_diario_consultas']) : 0 ?></h3>
                        <p>Límite Diario</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Estadísticas del mes -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-calendar-alt"></i> Estadísticas del Mes
                        </h3>
                    </div>
                    <div class="card-body">
                        <table class="table table-sm">
                            <tr>
                                <th>Total Consultas:</th>
                                <td><strong><?= intval($stats_mes['total_consultas']) ?></strong></td>
                            </tr>
                            <tr>
                                <th>Total Tokens:</th>
                                <td><?= number_format(floatval($stats_mes['total_tokens'])) ?></td>
                            </tr>
                            <tr>
                                <th>Costo Total:</th>
                                <td>$<?= number_format(floatval($stats_mes['costo_total']), 2) ?> USD</td>
                            </tr>
                            <tr>
                                <th>Equivalente PEN:</th>
                                <td>S/. <?= number_format(floatval($stats_mes['costo_total']) * 3.8, 2) ?></td>
                            </tr>
                            <?php if ($config_ia): ?>
                            <tr>
                                <th>Presupuesto Mensual:</th>
                                <td>S/. <?= number_format(floatval($config_ia['presupuesto_mensual']), 2) ?></td>
                            </tr>
                            <tr>
                                <th>Porcentaje Usado:</th>
                                <td>
                                    <?php 
                                    $gasto_actual = floatval($config_ia['gasto_mes_actual']);
                                    $presupuesto = floatval($config_ia['presupuesto_mensual']);
                                    $porcentaje = $presupuesto > 0 ? ($gasto_actual / $presupuesto * 100) : 0;
                                    ?>
                                    <div class="progress">
                                        <div class="progress-bar <?= $porcentaje > 80 ? 'bg-danger' : ($porcentaje > 50 ? 'bg-warning' : 'bg-success') ?>" 
                                             style="width: <?= min($porcentaje, 100) ?>%">
                                            <?= number_format($porcentaje, 1) ?>%
                                        </div>
                                    </div>
                                    <small class="text-muted">
                                        S/. <?= number_format($gasto_actual, 2) ?> / S/. <?= number_format($presupuesto, 2) ?>
                                    </small>
                                </td>
                            </tr>
                            <?php else: ?>
                            <tr>
                                <td colspan="2" class="text-warning">
                                    <i class="fas fa-exclamation-triangle"></i> 
                                    No hay configuración de IA. 
                                    <a href="<?= BASE_URL ?>configuracion/ia.php">Configurar ahora</a>
                                </td>
                            </tr>
                            <?php endif; ?>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Uso por modelo -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-robot"></i> Uso por Modelo (Este Mes)
                        </h3>
                    </div>
                    <div class="card-body">
                        <?php if (empty($por_modelo)): ?>
                            <p class="text-muted text-center py-3">
                                <i class="fas fa-inbox"></i><br>
                                No hay consultas este mes
                            </p>
                        <?php else: ?>
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Modelo</th>
                                        <th class="text-center">Consultas</th>
                                        <th class="text-center">Tokens</th>
                                        <th class="text-right">Costo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php foreach ($por_modelo as $modelo): ?>
                                    <tr>
                                        <td>
                                            <span class="badge badge-primary">
                                                <?= e($modelo['modelo']) ?>
                                            </span>
                                        </td>
                                        <td class="text-center"><?= intval($modelo['consultas']) ?></td>
                                        <td class="text-center"><?= number_format(floatval($modelo['tokens'])) ?></td>
                                        <td class="text-right">$<?= number_format(floatval($modelo['costo']), 4) ?></td>
                                    </tr>
                                    <?php endforeach; ?>
                                </tbody>
                            </table>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>

        <!-- Últimas consultas -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-history"></i> Últimas 20 Consultas
                        </h3>
                    </div>
                    <div class="card-body table-responsive p-0" style="max-height: 500px;">
                        <?php if (empty($ultimas)): ?>
                            <div class="text-center py-5">
                                <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                                <p class="text-muted">No hay consultas registradas aún</p>
                            </div>
                        <?php else: ?>
                            <table class="table table-striped table-sm table-head-fixed">
                                <thead>
                                    <tr>
                                        <th>Fecha</th>
                                        <th>Síntoma</th>
                                        <th>Modelo</th>
                                        <th class="text-center">Tokens</th>
                                        <th class="text-right">Costo</th>
                                        <th class="text-center">Tiempo</th>
                                        <th class="text-center">Estado</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php foreach ($ultimas as $consulta): ?>
                                    <tr>
                                        <td>
                                            <small><?= date('d/m/y H:i', strtotime($consulta['fecha_consulta'])) ?></small>
                                        </td>
                                        <td>
                                            <small><?= e(substr($consulta['sintoma'], 0, 50)) ?><?= strlen($consulta['sintoma']) > 50 ? '...' : '' ?></small>
                                        </td>
                                        <td>
                                            <span class="badge badge-info badge-sm">
                                                <?= e($consulta['modelo']) ?>
                                            </span>
                                        </td>
                                        <td class="text-center">
                                            <?= number_format(floatval($consulta['tokens_usados'])) ?>
                                        </td>
                                        <td class="text-right">
                                            $<?= number_format(floatval($consulta['costo_estimado']), 4) ?>
                                        </td>
                                        <td class="text-center">
                                            <small><?= number_format(floatval($consulta['tiempo_respuesta_ms'])) ?>ms</small>
                                        </td>
                                        <td class="text-center">
                                            <?php if ($consulta['exitosa']): ?>
                                                <span class="badge badge-success">✓</span>
                                            <?php else: ?>
                                                <span class="badge badge-danger">✗</span>
                                            <?php endif; ?>
                                        </td>
                                    </tr>
                                    <?php endforeach; ?>
                                </tbody>
                            </table>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>

        <!-- Botón para consultar uso real -->
        <div class="row">
            <div class="col-12">
                <div class="card card-primary">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-external-link-alt"></i> Consultar Saldo Real en OpenAI
                        </h3>
                    </div>
                    <div class="card-body">
                        <p>Para ver tu uso y crédito REAL directamente desde OpenAI:</p>
                        <a href="https://platform.openai.com/account/billing/overview" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt"></i> Abrir Dashboard de OpenAI
                        </a>
                        
                        <hr>
                        
                        <div class="alert alert-info">
                            <h5><i class="icon fas fa-info"></i> Nota importante:</h5>
                            <ul class="mb-0">
                                <li>Los costos mostrados aquí son <strong>estimados</strong> basados en tokens usados.</li>
                                <li>Para ver el <strong>costo exacto</strong> y crédito disponible, consulta el dashboard de OpenAI.</li>
                                <li>Los precios pueden variar según el modelo y la región.</li>
                            </ul>
                        </div>
                        
                        <h5>📊 Precios de Referencia (USD por millón de tokens):</h5>
                        <table class="table table-sm table-bordered">
                            <thead>
                                <tr>
                                    <th>Modelo</th>
                                    <th class="text-center">Input</th>
                                    <th class="text-center">Output</th>
                                    <th class="text-right">Costo Promedio/Consulta</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="table-success">
                                    <td><strong>GPT-4o Mini ⭐</strong></td>
                                    <td class="text-center">$0.15</td>
                                    <td class="text-center">$0.60</td>
                                    <td class="text-right">~$0.001</td>
                                </tr>
                                <tr>
                                    <td>GPT-4o</td>
                                    <td class="text-center">$2.50</td>
                                    <td class="text-center">$10.00</td>
                                    <td class="text-right">~$0.005</td>
                                </tr>
                                <tr>
                                    <td>GPT-4 Turbo</td>
                                    <td class="text-center">$10.00</td>
                                    <td class="text-center">$30.00</td>
                                    <td class="text-right">~$0.01</td>
                                </tr>
                                <tr class="table-danger">
                                    <td>GPT-4</td>
                                    <td class="text-center">$30.00</td>
                                    <td class="text-center">$60.00</td>
                                    <td class="text-right">~$0.03</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

    </div>
</section>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>