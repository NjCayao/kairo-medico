<?php
$page_title = 'Editar Producto';
$current_page = 'productos_listar';
$current_section = 'productos';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

$id = $_GET['id'] ?? 0;
$errores = [];

// Obtener producto
$producto = $db_instance->query(
    "SELECT * FROM productos_naturales WHERE id = ?",
    [$id]
);

if (empty($producto)) {
    header('Location: listar.php?error=Producto no encontrado');
    exit;
}

$producto = $producto[0];

// Procesar formulario
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    
    $datos = [
        'nombre' => trim($_POST['nombre'] ?? ''),
        'categoria' => trim($_POST['categoria'] ?? ''),
        'codigo_producto' => trim($_POST['codigo_producto'] ?? ''),
        'descripcion_corta' => trim($_POST['descripcion_corta'] ?? ''),
        'presentacion' => trim($_POST['presentacion'] ?? ''),
        'para_que_sirve' => trim($_POST['para_que_sirve'] ?? ''),
        'beneficios' => trim($_POST['beneficios'] ?? ''),
        'dosis' => trim($_POST['dosis'] ?? ''),
        'precio' => trim($_POST['precio'] ?? ''),
        'sintomas_que_trata' => trim($_POST['sintomas_que_trata'] ?? ''),
        'activo' => isset($_POST['activo']) ? 1 : 0
    ];
    
    // Validar
    if (empty($datos['nombre'])) {
        $errores[] = 'El nombre es obligatorio';
    }
    
    if (empty($datos['precio']) || !is_numeric($datos['precio'])) {
        $errores[] = 'El precio es obligatorio y debe ser numérico';
    }
    
    // Si no hay errores, actualizar
    if (empty($errores)) {
        $sql = "UPDATE productos_naturales SET
            nombre = ?,
            categoria = ?,
            codigo_producto = ?,
            descripcion_corta = ?,
            presentacion = ?,
            para_que_sirve = ?,
            beneficios_principales = ?,
            dosis_recomendada = ?,
            precio = ?,
            sintomas_que_trata = ?,
            activo = ?
        WHERE id = ?";
        
        $resultado = $db_instance->execute($sql, [
            $datos['nombre'],
            $datos['categoria'],
            $datos['codigo_producto'],
            $datos['descripcion_corta'],
            $datos['presentacion'],
            $datos['para_que_sirve'],
            $datos['beneficios'],
            $datos['dosis'],
            $datos['precio'],
            $datos['sintomas_que_trata'],
            $datos['activo'],
            $id
        ]);
        
        if ($resultado) {
            header('Location: listar.php?success=1');
            exit;
        } else {
            $errores[] = 'Error al actualizar el producto';
        }
    }
    
    // Actualizar producto con nuevos datos
    $producto = array_merge($producto, $datos);
}

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">Editar Producto</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="../dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item"><a href="listar.php">Productos</a></li>
                    <li class="breadcrumb-item active">Editar</li>
                </ol>
            </div>
        </div>
    </div>
</div>

<!-- Main content -->
<section class="content">
    <div class="container-fluid">
        
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <i class="fas fa-edit"></i> Editar: <?= e($producto['nombre']) ?>
                </h3>
            </div>
            
            <form method="post">
                <div class="card-body">
                    
                    <?php if (!empty($errores)): ?>
                        <div class="alert alert-danger">
                            <ul class="mb-0">
                                <?php foreach ($errores as $error): ?>
                                    <li><?= e($error) ?></li>
                                <?php endforeach; ?>
                            </ul>
                        </div>
                    <?php endif; ?>
                    
                    <div class="row">
                        <!-- Nombre -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Nombre del Producto <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" name="nombre" 
                                       value="<?= e($producto['nombre']) ?>" required>
                            </div>
                        </div>
                        
                        <!-- Categoría -->
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Categoría</label>
                                <select class="form-control" name="categoria">
                                    <option value="">Seleccionar</option>
                                    <option value="moringa_capsulas" <?= $producto['categoria'] == 'moringa_capsulas' ? 'selected' : '' ?>>Moringa Cápsulas</option>
                                    <option value="moringa_aceite" <?= $producto['categoria'] == 'moringa_aceite' ? 'selected' : '' ?>>Moringa Aceite</option>
                                    <option value="ganoderma_te" <?= $producto['categoria'] == 'ganoderma_te' ? 'selected' : '' ?>>Ganoderma Té</option>
                                    <option value="ganoderma_capsulas" <?= $producto['categoria'] == 'ganoderma_capsulas' ? 'selected' : '' ?>>Ganoderma Cápsulas</option>
                                    <option value="otros" <?= $producto['categoria'] == 'otros' ? 'selected' : '' ?>>Otros</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Código -->
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Código</label>
                                <input type="text" class="form-control" name="codigo_producto" 
                                       value="<?= e($producto['codigo_producto']) ?>">
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <!-- Descripción corta -->
                        <div class="col-md-12">
                            <div class="form-group">
                                <label>Descripción Corta</label>
                                <textarea class="form-control" name="descripcion_corta" rows="2"><?= e($producto['descripcion_corta']) ?></textarea>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <!-- Presentación -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Presentación</label>
                                <input type="text" class="form-control" name="presentacion" 
                                       value="<?= e($producto['presentacion']) ?>">
                            </div>
                        </div>
                        
                        <!-- Precio -->
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Precio (S/.) <span class="text-danger">*</span></label>
                                <input type="number" step="0.01" class="form-control" name="precio" 
                                       value="<?= e($producto['precio']) ?>" required>
                            </div>
                        </div>
                        
                        <!-- Estado -->
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Estado</label>
                                <div class="custom-control custom-switch" style="padding-top: 8px;">
                                    <input type="checkbox" class="custom-control-input" 
                                           id="activo" name="activo" 
                                           <?= $producto['activo'] ? 'checked' : '' ?>>
                                    <label class="custom-control-label" for="activo">Activo</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <!-- Para qué sirve -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>¿Para qué sirve?</label>
                                <textarea class="form-control" name="para_que_sirve" rows="3"><?= e($producto['para_que_sirve']) ?></textarea>
                            </div>
                        </div>
                        
                        <!-- Beneficios -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Beneficios Principales</label>
                                <textarea class="form-control" name="beneficios" rows="3"><?= e($producto['beneficios_principales']) ?></textarea>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <!-- Dosis -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Dosis Recomendada</label>
                                <textarea class="form-control" name="dosis" rows="2"><?= e($producto['dosis_recomendada']) ?></textarea>
                            </div>
                        </div>
                        
                        <!-- Síntomas -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Síntomas que Trata</label>
                                <textarea class="form-control" name="sintomas_que_trata" rows="2"><?= e($producto['sintomas_que_trata']) ?></textarea>
                                <small class="text-muted">Separar por comas</small>
                            </div>
                        </div>
                    </div>
                    
                </div>
                
                <div class="card-footer">
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-save"></i> Guardar Cambios
                    </button>
                    <a href="listar.php" class="btn btn-secondary">
                        <i class="fas fa-times"></i> Cancelar
                    </a>
                </div>
            </form>
        </div>
        
    </div>
</section>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>