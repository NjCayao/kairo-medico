<?php
$page_title = 'Productos';
$current_page = 'productos_listar';
$current_section = 'productos';

define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/functions.php';

$db_instance = new Database();
$db = $db_instance->connect();

// Obtener productos
$productos = $db_instance->query(
    "SELECT * FROM productos_naturales ORDER BY nombre ASC"
);

require_once BASE_PATH . '/includes/header.php';
require_once BASE_PATH . '/includes/sidebar.php';
?>

<!-- Content Header -->
<div class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-6">
                <h1 class="m-0">Productos</h1>
            </div>
            <div class="col-sm-6">
                <ol class="breadcrumb float-sm-right">
                    <li class="breadcrumb-item"><a href="../dashboard.php">Dashboard</a></li>
                    <li class="breadcrumb-item active">Productos</li>
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
                    <i class="fas fa-pills"></i> Lista de Productos
                </h3>
                <div class="card-tools">
                    <a href="crear.php" class="btn btn-success btn-sm">
                        <i class="fas fa-plus"></i> Nuevo Producto
                    </a>
                    <a href="importar.php" class="btn btn-primary btn-sm">
                        <i class="fas fa-file-excel"></i> Importar Excel
                    </a>
                    <a href="exportar.php" class="btn btn-info btn-sm">
                        <i class="fas fa-download"></i> Exportar
                    </a>
                </div>
            </div>
            
            <div class="card-body">
                <?php if (isset($_GET['success'])): ?>
                    <?= alerta('Operación realizada con éxito', 'success') ?>
                <?php endif; ?>
                
                <?php if (isset($_GET['error'])): ?>
                    <?= alerta($_GET['error'], 'danger') ?>
                <?php endif; ?>
                
                <table id="productosTable" class="table table-bordered table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Categoría</th>
                            <th>Código</th>
                            <th>Precio</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($productos as $producto): ?>
                            <tr>
                                <td><?= $producto['id'] ?></td>
                                <td>
                                    <strong><?= e($producto['nombre']) ?></strong><br>
                                    <small class="text-muted">
                                        <?= e(truncate($producto['descripcion_corta'], 60)) ?>
                                    </small>
                                </td>
                                <td><?= e($producto['categoria']) ?></td>
                                <td><?= e($producto['codigo_producto']) ?></td>
                                <td><?= formatPrecio($producto['precio']) ?></td>
                                <td>
                                    <?php if ($producto['activo']): ?>
                                        <span class="badge badge-success">Activo</span>
                                    <?php else: ?>
                                        <span class="badge badge-secondary">Inactivo</span>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <a href="editar.php?id=<?= $producto['id'] ?>" 
                                       class="btn btn-sm btn-info" 
                                       title="Editar">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    <a href="eliminar.php?id=<?= $producto['id'] ?>" 
                                       class="btn btn-sm btn-danger" 
                                       title="Eliminar"
                                       onclick="return confirm('¿Estás seguro de eliminar este producto?')">
                                        <i class="fas fa-trash"></i>
                                    </a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
        
    </div>
</section>

<!-- DataTables -->
<link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/dataTables.bootstrap4.min.css">
<script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.11.5/js/dataTables.bootstrap4.min.js"></script>

<script>
$(document).ready(function() {
    $('#productosTable').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.11.5/i18n/es-ES.json"
        },
        "order": [[1, "asc"]],
        "pageLength": 25
    });
});
</script>

<?php require_once BASE_PATH . '/includes/footer.php'; ?>