<?php
$page_title = 'Importar Productos';
$current_page = 'productos_importar';
$current_section = 'productos';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

$errores = [];
$exitos = [];
$advertencias = [];

// Verificar si PhpSpreadsheet está disponible
$phpspreadsheet_disponible = file_exists(dirname(dirname(dirname(__DIR__))) . '/vendor/autoload.php');

if ($phpspreadsheet_disponible) {
    require dirname(dirname(dirname(__DIR__))) . '/vendor/autoload.php';
}

// Procesar formulario
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['archivo'])) {

    if (!$phpspreadsheet_disponible) {
        $errores[] = 'PhpSpreadsheet no está instalado. Ejecuta: composer require phpoffice/phpspreadsheet';
    } else {

        $archivo = $_FILES['archivo'];

        // Validar archivo
        if ($archivo['error'] !== UPLOAD_ERR_OK) {
            $errores[] = 'Error al subir el archivo';
        } elseif (!in_array($archivo['type'], [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ])) {
            $errores[] = 'El archivo debe ser Excel (.xlsx o .xls)';
        } else {

            try {
                // Leer archivo Excel
                $reader = \PhpOffice\PhpSpreadsheet\IOFactory::createReader('Xlsx');
                $spreadsheet = $reader->load($archivo['tmp_name']);
                $sheet = $spreadsheet->getActiveSheet();
                $rows = $sheet->toArray();

                // Validar encabezados (primera fila)
                $headers = $rows[0];
                $expected_headers = [
                    'ID',
                    'Nombre',
                    'Categoría',
                    'Código',
                    'Descripción Corta',
                    'Presentación',
                    'Para qué sirve',
                    'Beneficios',
                    'Dosis',
                    'Precio',
                    'Síntomas',
                    'Activo'
                ];

                // Saltar primera fila (encabezados) y procesar datos
                $importados = 0;
                $actualizados = 0;
                $saltados = 0;

                for ($i = 1; $i < count($rows); $i++) {
                    $row = $rows[$i];

                    // Validar que tenga datos
                    if (empty($row[1])) { // Nombre vacío
                        $saltados++;
                        continue;
                    }

                    $id = $row[0] ?? null;
                    $nombre = $row[1] ?? '';
                    $categoria = $row[2] ?? 'otros';
                    $codigo = $row[3] ?? null;
                    $descripcion = $row[4] ?? null;
                    $presentacion = $row[5] ?? null;
                    $para_que_sirve = $row[6] ?? null;
                    $beneficios = $row[7] ?? null;
                    $dosis = $row[8] ?? null;
                    $precio = $row[9] ?? 0;
                    $sintomas = $row[10] ?? null;
                    $activo = ($row[11] ?? 'Sí') === 'Sí' ? 1 : 0;

                    // Si tiene ID, intentar actualizar
                    if (!empty($id) && is_numeric($id)) {
                        $existe = $db_instance->query("SELECT id FROM productos_naturales WHERE id = ?", [$id]);

                        if (!empty($existe)) {
                            // Actualizar
                            $sql = "UPDATE productos_naturales SET
                                nombre = ?, categoria = ?, codigo_producto = ?,
                                descripcion_corta = ?, presentacion = ?, para_que_sirve = ?,
                                beneficios_principales = ?, dosis_recomendada = ?,
                                precio = ?, sintomas_que_trata = ?, activo = ?
                                WHERE id = ?";

                            $stmt = $db->prepare($sql);
                            $stmt->execute([
                                $nombre,
                                $categoria,
                                $codigo,
                                $descripcion,
                                $presentacion,
                                $para_que_sirve,
                                $beneficios,
                                $dosis,
                                $precio,
                                $sintomas,
                                $activo,
                                $id
                            ]);

                            $actualizados++;
                            continue;
                        }
                    }

                    // Insertar nuevo
                    try {
                        // Generar código si está vacío
                        if (empty($codigo)) {
                            $prefijo = strtoupper(substr($categoria, 0, 3));
                            $codigo = $prefijo . '-' . date('ymd') . '-' . rand(100, 999);
                        }

                        $sql = "INSERT INTO productos_naturales (
                            nombre, categoria, codigo_producto, descripcion_corta,
                            presentacion, para_que_sirve, beneficios_principales,
                            dosis_recomendada, precio, sintomas_que_trata, activo
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

                        $stmt = $db->prepare($sql);
                        $stmt->execute([
                            $nombre,
                            $categoria,
                            $codigo,
                            $descripcion,
                            $presentacion,
                            $para_que_sirve,
                            $beneficios,
                            $dosis,
                            $precio,
                            $sintomas,
                            $activo
                        ]);

                        $importados++;
                    } catch (PDOException $e) {
                        if (strpos($e->getMessage(), 'Duplicate entry') !== false) {
                            $advertencias[] = "Producto '{$nombre}' ya existe (código duplicado)";
                            $saltados++;
                        } else {
                            $advertencias[] = "Error en producto '{$nombre}': " . $e->getMessage();
                            $saltados++;
                        }
                    }
                }

                // Resumen
                if ($importados > 0) {
                    $exitos[] = "✅ {$importados} productos importados correctamente";
                }
                if ($actualizados > 0) {
                    $exitos[] = "✅ {$actualizados} productos actualizados";
                }
                if ($saltados > 0) {
                    $advertencias[] = "⚠️ {$saltados} productos saltados";
                }
            } catch (Exception $e) {
                $errores[] = 'Error al procesar el archivo: ' . $e->getMessage();
            }
        }
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
                <h1 class="m-0">Importar Productos</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item"><a href="listar.php">Productos</a></li>
                    <li class="breadcrumb-item active">Importar</li>
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
                            <i class="fas fa-file-excel"></i> Importar desde Excel
                        </h3>
                    </div>

                    <form method="post" enctype="multipart/form-data">
                        <div class="card-body">

                            <?php if (!empty($errores)): ?>
                                <div class="alert alert-danger alert-dismissible">
                                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                                    <h5><i class="icon fas fa-ban"></i> Errores:</h5>
                                    <ul class="mb-0">
                                        <?php foreach ($errores as $error): ?>
                                            <li><?= $error ?></li>
                                        <?php endforeach; ?>
                                    </ul>
                                </div>
                            <?php endif; ?>

                            <?php if (!empty($exitos)): ?>
                                <div class="alert alert-success alert-dismissible">
                                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                                    <h5><i class="icon fas fa-check"></i> Éxito:</h5>
                                    <ul class="mb-0">
                                        <?php foreach ($exitos as $exito): ?>
                                            <li><?= $exito ?></li>
                                        <?php endforeach; ?>
                                    </ul>
                                </div>
                            <?php endif; ?>

                            <?php if (!empty($advertencias)): ?>
                                <div class="alert alert-warning alert-dismissible">
                                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                                    <h5><i class="icon fas fa-exclamation-triangle"></i> Advertencias:</h5>
                                    <ul class="mb-0">
                                        <?php foreach ($advertencias as $advertencia): ?>
                                            <li><?= $advertencia ?></li>
                                        <?php endforeach; ?>
                                    </ul>
                                </div>
                            <?php endif; ?>

                            <?php if (!$phpspreadsheet_disponible): ?>
                                <div class="alert alert-warning">
                                    <h5><i class="icon fas fa-exclamation-triangle"></i> PhpSpreadsheet no instalado</h5>
                                    <p>Para usar esta funcionalidad, ejecuta:</p>
                                    <code>composer require phpoffice/phpspreadsheet</code>
                                </div>
                            <?php endif; ?>

                            <div class="form-group">
                                <label for="archivo">Seleccionar archivo Excel</label>
                                <input type="file" class="form-control-file" id="archivo"
                                    name="archivo" accept=".xlsx,.xls" required>
                                <small class="form-text text-muted">
                                    Formatos permitidos: .xlsx, .xls (máximo 10MB)
                                </small>
                            </div>

                            <div class="alert alert-info">
                                <h5><i class="icon fas fa-info-circle"></i> Instrucciones:</h5>
                                <ol>
                                    <li>Descarga la plantilla usando el botón de la derecha</li>
                                    <li>Llena los datos en el Excel</li>
                                    <li>Sube el archivo aquí</li>
                                    <li>Si el producto tiene ID, se actualizará. Si no, se creará uno nuevo</li>
                                </ol>
                            </div>

                        </div>

                        <div class="card-footer">
                            <button type="submit" class="btn btn-primary" <?= !$phpspreadsheet_disponible ? 'disabled' : '' ?>>
                                <i class="fas fa-upload"></i> Importar Productos
                            </button>
                            <a href="listar.php" class="btn btn-secondary">
                                <i class="fas fa-times"></i> Cancelar
                            </a>
                        </div>
                    </form>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card card-primary">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-download"></i> Descargar Plantilla
                        </h3>
                    </div>
                    <div class="card-body">
                        <p>Descarga la plantilla con los productos actuales para editarla.</p>
                        <a href="exportar.php" class="btn btn-success btn-block">
                            <i class="fas fa-file-excel"></i> Descargar Excel
                        </a>
                    </div>
                </div>

                <div class="card card-info">
                    <div class="card-header">
                        <h3 class="card-title">
                            <i class="fas fa-question-circle"></i> Ayuda
                        </h3>
                    </div>
                    <div class="card-body">
                        <p><strong>Formato del Excel:</strong></p>
                        <ul>
                            <li>Primera fila: Encabezados</li>
                            <li>Categorías válidas: moringa_capsulas, moringa_aceite, moringa_polvo, ganoderma_te, ganoderma_capsulas, combos, otros</li>
                            <li>Activo: "Sí" o "No"</li>
                            <li>Precio: Números decimales</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

    </div>
</section>

<script>
    $(document).ready(function() {
        // Actualizar label del input file cuando se selecciona
        $('#archivo').on('change', function() {
            var fileName = $(this).val().split('\\').pop();
            if (fileName) {
                $(this).next('.custom-file-label').addClass('selected').html(fileName);
            } else {
                $(this).next('.custom-file-label').removeClass('selected').html('Seleccionar archivo...');
            }
        });

        // También funciona con BS file input nativo
        $('.custom-file-input').on('change', function() {
            var fileName = $(this).val().split('\\').pop();
            if (fileName) {
                $(this).siblings('.custom-file-label').addClass('selected').html(fileName);
            }
        });
    });
</script>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>