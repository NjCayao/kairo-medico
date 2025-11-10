<!-- Main Sidebar Container -->
<aside class="main-sidebar sidebar-dark-primary elevation-4">
    <!-- Brand Logo -->
    <a href="<?= BASE_URL ?>dashboard.php" class="brand-link text-center">
        <span class="brand-text font-weight-light">🤖 <strong>KAIROS</strong></span>
    </a>

    <!-- Sidebar -->
    <div class="sidebar">
        <!-- Sidebar Menu -->
        <nav class="mt-2">
            <ul class="nav nav-pills nav-sidebar flex-column" data-widget="treeview" role="menu">

                <!-- Dashboard -->
                <li class="nav-item">
                    <a href="<?= BASE_URL ?>dashboard.php" class="nav-link <?= ($current_page == 'dashboard') ? 'active' : '' ?>">
                        <i class="nav-icon fas fa-tachometer-alt"></i>
                        <p>Dashboard</p>
                    </a>
                </li>

                <!-- Productos -->
                <li class="nav-item <?= ($current_section == 'productos') ? 'menu-open' : '' ?>">
                    <a href="#" class="nav-link <?= ($current_section == 'productos') ? 'active' : '' ?>">
                        <i class="nav-icon fas fa-pills"></i>
                        <p>
                            Productos
                            <i class="right fas fa-angle-left"></i>
                        </p>
                    </a>
                    <ul class="nav nav-treeview">
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>productos/listar.php" class="nav-link <?= ($current_page == 'productos_listar') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>Listar Productos</p>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>productos/crear.php" class="nav-link <?= ($current_page == 'productos_crear') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>Nuevo Producto</p>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>productos/importar.php" class="nav-link <?= ($current_page == 'productos_importar') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>Importar Excel</p>
                            </a>
                        </li>
                    </ul>
                </li>

                <!-- Consultas -->
                <li class="nav-item <?= ($current_section == 'consultas') ? 'menu-open' : '' ?>">
                    <a href="#" class="nav-link <?= ($current_section == 'consultas') ? 'active' : '' ?>">
                        <i class="nav-icon fas fa-notes-medical"></i>
                        <p>
                            Consultas
                            <i class="right fas fa-angle-left"></i>
                        </p>
                    </a>
                    <ul class="nav nav-treeview">
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>consultas/historial.php" class="nav-link <?= ($current_page == 'consultas_historial') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>Historial</p>
                            </a>
                        </li>
                    </ul>
                </li>

                <!-- Aprendizaje -->
                <li class="nav-item <?= ($current_section == 'aprendizaje') ? 'menu-open' : '' ?>">
                    <a href="#" class="nav-link <?= ($current_section == 'aprendizaje') ? 'active' : '' ?>">
                        <i class="nav-icon fas fa-brain"></i>
                        <p>
                            Aprendizaje
                            <i class="right fas fa-angle-left"></i>
                        </p>
                    </a>
                    <ul class="nav nav-treeview">
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>aprendizaje/patrones.php" class="nav-link <?= ($current_page == 'patrones') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>Patrones ML</p>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>aprendizaje/conocimientos.php" class="nav-link <?= ($current_page == 'conocimientos') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>Conocimientos GPT</p>
                            </a>
                        </li>
                    </ul>
                </li>

                <!-- Configuración -->
                <li class="nav-item <?= ($current_section == 'configuracion') ? 'menu-open' : '' ?>">
                    <a href="#" class="nav-link <?= ($current_section == 'configuracion') ? 'active' : '' ?>">
                        <i class="nav-icon fas fa-cog"></i>
                        <p>
                            Configuración
                            <i class="right fas fa-angle-left"></i>
                        </p>
                    </a>
                    <ul class="nav nav-treeview">
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>configuracion/general.php" class="nav-link <?= ($current_page == 'config_general') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>General</p>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>configuracion/ia.php" class="nav-link <?= ($current_page == 'config_ia') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>Inteligencia Artificial</p>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="<?= BASE_URL ?>configuracion/uso_ia.php"
                                class="nav-link <?= ($current_page == 'uso_ia') ? 'active' : '' ?>">
                                <i class="far fa-circle nav-icon"></i>
                                <p>Costos AI</p>
                            </a>
                        </li>
                    </ul>
                </li>

            </ul>
        </nav>
        <!-- /.sidebar-menu -->
    </div>
    <!-- /.sidebar -->
</aside>

<!-- Content Wrapper. Contains page content -->
<div class="content-wrapper">