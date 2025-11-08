<?php
define('BASE_PATH', dirname(dirname(__DIR__)));
require_once BASE_PATH . '/includes/config.php';
require_once BASE_PATH . '/includes/db.php';
require_once BASE_PATH . '/includes/auth.php';

Auth::require_login();

// Verificar si PhpSpreadsheet está disponible
if (!file_exists(dirname(dirname(dirname(__DIR__))) . '/vendor/autoload.php')) {
    die('PhpSpreadsheet no está instalado. Ejecuta: composer require phpoffice/phpspreadsheet');
}

require dirname(dirname(dirname(__DIR__))) . '/vendor/autoload.php';

use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Writer\Xlsx;
use PhpOffice\PhpSpreadsheet\Style\Fill;
use PhpOffice\PhpSpreadsheet\Style\Alignment;

$db_instance = new Database();
$db = $db_instance->connect();

// Obtener productos
$productos = $db_instance->query("SELECT * FROM productos_naturales ORDER BY id ASC");

// Crear spreadsheet
$spreadsheet = new Spreadsheet();
$sheet = $spreadsheet->getActiveSheet();
$sheet->setTitle('Productos');

// Encabezados
$headers = [
    'A1' => 'ID',
    'B1' => 'Nombre',
    'C1' => 'Categoría',
    'D1' => 'Código',
    'E1' => 'Descripción Corta',
    'F1' => 'Presentación',
    'G1' => 'Para qué sirve',
    'H1' => 'Beneficios',
    'I1' => 'Dosis',
    'J1' => 'Precio',
    'K1' => 'Síntomas',
    'L1' => 'Activo'
];

foreach ($headers as $cell => $value) {
    $sheet->setCellValue($cell, $value);
}

// Estilo de encabezados
$headerStyle = [
    'font' => ['bold' => true, 'color' => ['rgb' => 'FFFFFF']],
    'fill' => [
        'fillType' => Fill::FILL_SOLID,
        'startColor' => ['rgb' => '4CAF50']
    ],
    'alignment' => ['horizontal' => Alignment::HORIZONTAL_CENTER]
];

$sheet->getStyle('A1:L1')->applyFromArray($headerStyle);

// Datos
$row = 2;
foreach ($productos as $producto) {
    $sheet->setCellValue('A' . $row, $producto['id']);
    $sheet->setCellValue('B' . $row, $producto['nombre']);
    $sheet->setCellValue('C' . $row, $producto['categoria']);
    $sheet->setCellValue('D' . $row, $producto['codigo_producto']);
    $sheet->setCellValue('E' . $row, $producto['descripcion_corta']);
    $sheet->setCellValue('F' . $row, $producto['presentacion']);
    $sheet->setCellValue('G' . $row, $producto['para_que_sirve']);
    $sheet->setCellValue('H' . $row, $producto['beneficios_principales']);
    $sheet->setCellValue('I' . $row, $producto['dosis_recomendada']);
    $sheet->setCellValue('J' . $row, $producto['precio']);
    $sheet->setCellValue('K' . $row, $producto['sintomas_que_trata']);
    $sheet->setCellValue('L' . $row, $producto['activo'] ? 'Sí' : 'No');
    $row++;
}

// Auto-ajustar columnas
foreach (range('A', 'L') as $col) {
    $sheet->getColumnDimension($col)->setAutoSize(true);
}

// Generar archivo
$filename = 'productos_' . date('Y-m-d_His') . '.xlsx';

header('Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
header('Content-Disposition: attachment;filename="' . $filename . '"');
header('Cache-Control: max-age=0');

$writer = new Xlsx($spreadsheet);
$writer->save('php://output');
exit;