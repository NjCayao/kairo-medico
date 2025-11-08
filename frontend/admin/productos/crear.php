<?php
$page_title = 'Nuevo Producto';
$current_page = 'productos_crear';
$current_section = 'productos';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

$errores = [];
$datos = [];

// Procesar formulario
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    
    // Recoger datos
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
    
    // ==========================================
    // VALIDACIONES
    // ==========================================
    
    if (empty($datos['nombre'])) {
        $errores[] = 'El nombre es obligatorio';
    }
    
    if (empty($datos['categoria'])) {
        $errores[] = 'La categoría es obligatoria';
    }
    
    if (empty($datos['precio']) || !is_numeric($datos['precio'])) {
        $errores[] = 'El precio es obligatorio y debe ser numérico';
    }
    
    // Validar código único (si se proporciona)
    if (!empty($datos['codigo_producto'])) {
        try {
            $stmt = $db->prepare("SELECT id FROM productos_naturales WHERE codigo_producto = ?");
            $stmt->execute([$datos['codigo_producto']]);
            $existe = $stmt->fetch();
            
            if ($existe) {
                $errores[] = 'El código "' . htmlspecialchars($datos['codigo_producto']) . '" ya existe. Usa otro código o déjalo vacío para generar uno automático.';
            }
        } catch (PDOException $e) {
            $errores[] = 'Error al validar el código';
        }
    }
    
    // ==========================================
    // INSERTAR SOLO SI NO HAY ERRORES
    // ==========================================
    
    if (empty($errores)) {
        try {
            // Si no hay código, generar uno automático
            if (empty($datos['codigo_producto'])) {
                $prefijo = strtoupper(substr($datos['categoria'], 0, 3));
                $datos['codigo_producto'] = $prefijo . '-' . date('ymd') . '-' . rand(100, 999);
            }
            
            $sql = "INSERT INTO productos_naturales (
                nombre, categoria, codigo_producto, descripcion_corta, 
                presentacion, para_que_sirve, beneficios_principales, 
                dosis_recomendada, precio, sintomas_que_trata, activo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
            
            $stmt = $db->prepare($sql);
            $stmt->execute([
                $datos['nombre'],
                $datos['categoria'],
                $datos['codigo_producto'],
                !empty($datos['descripcion_corta']) ? $datos['descripcion_corta'] : null,
                !empty($datos['presentacion']) ? $datos['presentacion'] : null,
                !empty($datos['para_que_sirve']) ? $datos['para_que_sirve'] : null,
                !empty($datos['beneficios']) ? $datos['beneficios'] : null,
                !empty($datos['dosis']) ? $datos['dosis'] : null,
                $datos['precio'],
                !empty($datos['sintomas_que_trata']) ? $datos['sintomas_que_trata'] : null,
                $datos['activo']
            ]);
            
            header('Location: listar.php?success=1');
            exit;
            
        } catch (PDOException $e) {
            // Capturar error de duplicado
            if (strpos($e->getMessage(), 'Duplicate entry') !== false) {
                $errores[] = 'El código de producto ya existe en la base de datos.';
            } else {
                $errores[] = 'Error de base de datos: ' . $e->getMessage();
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
                <h1 class="m-0">Nuevo Producto</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="<?= BASE_URL ?>dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item"><a href="listar.php">Productos</a></li>
                    <li class="breadcrumb-item active">Nuevo</li>
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
                    <i class="fas fa-plus"></i> Crear Producto
                </h3>
            </div>
            
            <form method="post">
                <div class="card-body">
                    
                    <?php if (!empty($errores)): ?>
                        <div class="alert alert-danger alert-dismissible">
                            <button type="button" class="close" data-dismiss="alert">&times;</button>
                            <h5><i class="icon fas fa-ban"></i> Errores encontrados:</h5>
                            <ul class="mb-0">
                                <?php foreach ($errores as $error): ?>
                                    <li><?= $error ?></li>
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
                                       value="<?= e($datos['nombre'] ?? '') ?>" required>
                            </div>
                        </div>
                        
                        <!-- Categoría -->
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Categoría <span class="text-danger">*</span></label>
                                <select class="form-control" name="categoria" required>
                                    <option value="">Seleccionar</option>
                                    <option value="moringa_capsulas" <?= ($datos['categoria'] ?? '') == 'moringa_capsulas' ? 'selected' : '' ?>>Moringa Cápsulas</option>
                                    <option value="moringa_aceite" <?= ($datos['categoria'] ?? '') == 'moringa_aceite' ? 'selected' : '' ?>>Moringa Aceite</option>
                                    <option value="moringa_polvo" <?= ($datos['categoria'] ?? '') == 'moringa_polvo' ? 'selected' : '' ?>>Moringa Polvo</option>
                                    <option value="ganoderma_te" <?= ($datos['categoria'] ?? '') == 'ganoderma_te' ? 'selected' : '' ?>>Ganoderma Té</option>
                                    <option value="ganoderma_capsulas" <?= ($datos['categoria'] ?? '') == 'ganoderma_capsulas' ? 'selected' : '' ?>>Ganoderma Cápsulas</option>
                                    <option value="combos" <?= ($datos['categoria'] ?? '') == 'combos' ? 'selected' : '' ?>>Combos</option>
                                    <option value="otros" <?= ($datos['categoria'] ?? '') == 'otros' ? 'selected' : '' ?>>Otros</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Código -->
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Código del Producto</label>
                                <input type="text" class="form-control" name="codigo_producto" 
                                       value="<?= e($datos['codigo_producto'] ?? '') ?>"
                                       placeholder="Opcional">
                                <small class="text-muted">Dejar vacío para auto-generar</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <!-- Descripción corta -->
                        <div class="col-md-12">
                            <div class="form-group">
                                <label>Descripción Corta</label>
                                <textarea class="form-control" name="descripcion_corta" rows="2"><?= e($datos['descripcion_corta'] ?? '') ?></textarea>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <!-- Presentación -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Presentación</label>
                                <input type="text" class="form-control" name="presentacion" 
                                       value="<?= e($datos['presentacion'] ?? '') ?>"
                                       placeholder="Ej: Frasco x 60 cápsulas">
                            </div>
                        </div>
                        
                        <!-- Precio -->
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Precio (S/.) <span class="text-danger">*</span></label>
                                <input type="number" step="0.01" class="form-control" name="precio" 
                                       value="<?= e($datos['precio'] ?? '') ?>" required>
                            </div>
                        </div>
                        
                        <!-- Estado -->
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Estado</label>
                                <div class="custom-control custom-switch" style="padding-top: 8px;">
                                    <input type="checkbox" class="custom-control-input" 
                                           id="activo" name="activo" 
                                           <?= ($datos['activo'] ?? 1) ? 'checked' : '' ?>>
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
                                <textarea class="form-control" name="para_que_sirve" rows="3"><?= e($datos['para_que_sirve'] ?? '') ?></textarea>
                            </div>
                        </div>
                        
                        <!-- Beneficios -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Beneficios Principales</label>
                                <textarea class="form-control" name="beneficios" rows="3"><?= e($datos['beneficios'] ?? '') ?></textarea>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <!-- Dosis -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Dosis Recomendada</label>
                                <textarea class="form-control" name="dosis" rows="2"><?= e($datos['dosis'] ?? '') ?></textarea>
                            </div>
                        </div>
                        
                        <!-- Síntomas -->
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Síntomas que Trata</label>
                                <textarea class="form-control" name="sintomas_que_trata" rows="2"><?= e($datos['sintomas_que_trata'] ?? '') ?></textarea>
                                <small class="text-muted">Separar por comas</small>
                            </div>
                        </div>
                    </div>
                    
                </div>
                
                <div class="card-footer">
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-save"></i> Guardar Producto
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
