"""
Script de Validación Integral de Kairos
Prueba todos los componentes trabajando juntos
"""

import sys
import os
from datetime import datetime
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend.core.session_manager import SessionManager
from backend.core.learner import KairosLearner
from backend.database.sqlite_manager import SQLiteManager
from backend.core.medical_assistant import MedicalAssistant
from backend.core.diagnostico import DiagnosticoEngine
from backend.database.database_manager import DatabaseManager

class ColoresTerminal:
    """Colores para terminal"""
    VERDE = '\033[92m'
    AMARILLO = '\033[93m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    NEGRITA = '\033[1m'

class ValidadorSistema:
    """
    Validador completo del sistema Kairos
    """
    
    def __init__(self):
        self.resultados = {
            'total_tests': 0,
            'exitosos': 0,
            'fallidos': 0,
            'advertencias': 0,
            'tests': []
        }
        
        self.inicio = None
        
    def print_header(self, texto: str, color=ColoresTerminal.CYAN):
        """Imprimir encabezado"""
        print(f"\n{color}{'='*70}")
        print(f"{texto:^70}")
        print(f"{'='*70}{ColoresTerminal.RESET}\n")
    
    def print_test(self, nombre: str):
        """Imprimir nombre de test"""
        print(f"{ColoresTerminal.AZUL}▶ TEST: {nombre}{ColoresTerminal.RESET}")
    
    def print_exito(self, mensaje: str):
        """Imprimir éxito"""
        print(f"   {ColoresTerminal.VERDE}✅ {mensaje}{ColoresTerminal.RESET}")
    
    def print_fallo(self, mensaje: str):
        """Imprimir fallo"""
        print(f"   {ColoresTerminal.ROJO}❌ {mensaje}{ColoresTerminal.RESET}")
    
    def print_advertencia(self, mensaje: str):
        """Imprimir advertencia"""
        print(f"   {ColoresTerminal.AMARILLO}⚠️ {mensaje}{ColoresTerminal.RESET}")
    
    def print_info(self, mensaje: str):
        """Imprimir información"""
        print(f"   {ColoresTerminal.CYAN}ℹ️ {mensaje}{ColoresTerminal.RESET}")
    
    def registrar_test(self, nombre: str, exito: bool, mensaje: str = ""):
        """Registrar resultado de test"""
        self.resultados['total_tests'] += 1
        
        if exito:
            self.resultados['exitosos'] += 1
            self.print_exito(mensaje or "OK")
        else:
            self.resultados['fallidos'] += 1
            self.print_fallo(mensaje or "FALLÓ")
        
        self.resultados['tests'].append({
            'nombre': nombre,
            'exito': exito,
            'mensaje': mensaje
        })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TESTS DE COMPONENTES INDIVIDUALES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def test_database_mysql(self):
        """Test 1: Conexión MySQL"""
        self.print_test("Conexión a MySQL")
        
        try:
            db = DatabaseManager()
            if db.conexion and db.conexion.is_connected():
                self.registrar_test("MySQL", True, "Conectado correctamente")
                
                # Test query
                resultado = db.ejecutar_query("SELECT 1 as test")
                if resultado and resultado[0]['test'] == 1:
                    self.print_info("Query de prueba OK")
                
                db.desconectar()
                return True
            else:
                self.registrar_test("MySQL", False, "No se pudo conectar")
                return False
                
        except Exception as e:
            self.registrar_test("MySQL", False, f"Error: {e}")
            return False
    
    def test_sqlite_offline(self):
        """Test 2: Base de datos SQLite"""
        self.print_test("Base de datos SQLite (Modo Offline)")
        
        try:
            sqlite = SQLiteManager()
            
            # Test crear usuario
            usuario = sqlite.buscar_usuario_offline("99999997")
            
            if not usuario:
                usuario_id = sqlite.crear_usuario_offline(
                    "Test Validación",
                    "99999997",
                    28
                )
                self.print_info(f"Usuario test creado: ID {usuario_id}")
            else:
                self.print_info(f"Usuario test existe: {usuario['nombre']}")
            
            # Test estadísticas
            stats = sqlite.obtener_estadisticas()
            self.print_info(f"Registros en SQLite: {stats['usuarios']} usuarios, {stats['productos_naturales']} productos")
            
            self.registrar_test("SQLite", True, "Funcionando correctamente")
            return True
            
        except Exception as e:
            self.registrar_test("SQLite", False, f"Error: {e}")
            return False
    
    def test_classifier_ml(self):
        """Test 3: Clasificador ML"""
        self.print_test("Clasificador de Intenciones (ML)")
        
        try:
            from backend.core.classifier import IntentClassifier
            
            clf = IntentClassifier()
            
            if not clf.esta_entrenado:
                self.registrar_test("Classifier", False, "Modelo no entrenado")
                return False
            
            # Test predicción
            texto_prueba = "Me duele la cabeza"
            intencion, confianza, _ = clf.predecir(texto_prueba)
            
            self.print_info(f"'{texto_prueba}' → {intencion} ({confianza:.0%})")
            
            if confianza >= 0.7:
                self.registrar_test("Classifier", True, f"Precisión: {confianza:.0%}")
                return True
            else:
                self.registrar_test("Classifier", False, f"Confianza baja: {confianza:.0%}")
                return False
                
        except Exception as e:
            self.registrar_test("Classifier", False, f"Error: {e}")
            return False
    
    def test_productos_manager(self):
        """Test 4: Gestor de Productos"""
        self.print_test("Gestor de Productos")
        
        try:
            from backend.database.productos_manager import ProductosManager
            
            pm = ProductosManager()
            
            if pm.catalogo is None:
                self.registrar_test("Productos", False, "No se cargó el catálogo")
                return False
            
            productos = pm.obtener_todos()
            self.print_info(f"{len(productos)} productos en catálogo")
            
            # Test búsqueda
            resultado = pm.buscar_por_sintoma("dolor cabeza")
            self.print_info(f"Búsqueda 'dolor cabeza': {len(resultado)} productos")
            
            self.registrar_test("Productos", True, f"{len(productos)} productos disponibles")
            return True
            
        except Exception as e:
            self.registrar_test("Productos", False, f"Error: {e}")
            return False
    
    def test_medical_assistant(self):
        """Test 5: Medical Assistant"""
        self.print_test("Medical Assistant")
        
        try:
            asistente = MedicalAssistant(modo_preguntas='estatico')
            
            # Test saludo
            resultado = asistente.procesar_mensaje("Hola", {'nombre': 'Test Usuario'})
            
            if resultado['intencion'] == 'saludo':
                self.print_info(f"Intención detectada: {resultado['intencion']}")
                self.registrar_test("Medical Assistant", True, "Funcionando correctamente")
                return True
            else:
                self.registrar_test("Medical Assistant", False, f"Intención incorrecta: {resultado['intencion']}")
                return False
                
        except Exception as e:
            self.registrar_test("Medical Assistant", False, f"Error: {e}")
            return False
    
    def test_diagnostico_engine(self):
        """Test 6: Motor de Diagnóstico"""
        self.print_test("Motor de Diagnóstico")
        
        try:
            motor = DiagnosticoEngine()
            
            # Test con contexto mínimo
            contexto = {
                'sintoma_principal': 'dolor de cabeza',
                'respuestas_usuario': [
                    'En la frente',
                    'Una semana',
                    '7 de 10',
                    'Por las mañanas',
                    'Mejora con descanso'
                ]
            }
            
            # No hacer consulta real a GPT en test
            self.print_info("Motor inicializado correctamente")
            self.print_advertencia("Test de diagnóstico real omitido (requiere GPT)")
            
            self.registrar_test("Diagnóstico Engine", True, "Componente inicializado")
            return True
            
        except Exception as e:
            self.registrar_test("Diagnóstico Engine", False, f"Error: {e}")
            return False
    
    def test_learner(self):
        """Test 7: Sistema de Aprendizaje"""
        self.print_test("Sistema de Aprendizaje (Learner)")
        
        try:
            learner = KairosLearner(auto_entrenamiento=False)
            
            # Test análisis (sin datos reales no hará mucho)
            stats = learner.obtener_estadisticas_aprendizaje()
            
            self.print_info(f"Clasificador: {stats['clasificador']['num_intenciones']} intenciones")
            self.print_info(f"Patrones en BD: {stats['patrones_bd']}")
            
            self.registrar_test("Learner", True, "Sistema de aprendizaje activo")
            return True
            
        except Exception as e:
            self.registrar_test("Learner", False, f"Error: {e}")
            return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TEST DE INTEGRACIÓN COMPLETA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def test_flujo_completo(self):
        """Test 8: Flujo Completo de Consulta"""
        self.print_test("Flujo Completo de Consulta (Integración)")
        
        try:
            # Crear session manager
            manager = SessionManager(
                evento="Test Validación Sistema",
                ubicacion="Test Lab",
                dispositivo="Test-Device",
                modo_offline=False
            )
            
            # 1. Nueva sesión
            self.print_info("1/6 Creando nueva sesión...")
            exito, sesion_id, info = manager.nueva_sesion()
            
            if not exito:
                self.registrar_test("Flujo Completo", False, "No se creó la sesión")
                return False
            
            self.print_info(f"   Sesión: {sesion_id}")
            
            # 2. Capturar datos
            self.print_info("2/6 Capturando datos paciente...")
            exito, info_usuario = manager.capturar_datos_paciente(
                "Test Paciente Validación",
                "99999996",
                30
            )
            
            if not exito:
                self.registrar_test("Flujo Completo", False, "Error capturando datos")
                return False
            
            self.print_info(f"   Usuario: {info_usuario['nombre']}")
            
            # 3. Conversación simulada
            self.print_info("3/6 Simulando conversación...")
            mensajes = [
                "Hola",
                "Me duele la cabeza",
                "En la frente",
                "Dos días",
                "Un 6 de 10",
                "Por las mañanas",
                "Mejora con descanso",
                "Empeora con el trabajo"
            ]
            
            for msg in mensajes:
                resultado = manager.procesar_mensaje(msg)
                if resultado.get('diagnostico_listo'):
                    self.print_info(f"   Conversación completa ({len(mensajes)} mensajes)")
                    break
            
            # 4. Generar diagnóstico (sin GPT real)
            self.print_info("4/6 Generando diagnóstico...")
            self.print_advertencia("   Diagnóstico GPT omitido en test")
            
            # Simular diagnóstico básico
            manager.diagnostico_resultado = {
                'condicion': 'Cefalea tensional',
                'confianza': 0.85,
                'causas': ['Estrés', 'Tensión muscular'],
                'productos': [],
                'origen': 'test'
            }
            
            manager.receta_generada = {
                'fecha': datetime.now().strftime('%d/%m/%Y'),
                'paciente': 'Test Paciente',
                'diagnostico': 'Cefalea tensional',
                'texto_ticket': 'Receta de prueba'
            }
            
            self.print_info("   Diagnóstico simulado generado")
            
            # 5. Simular impresión
            self.print_info("5/6 Simulando impresión...")
            self.print_advertencia("   Impresión real omitida en test")
            
            # 6. Finalizar sesión
            self.print_info("6/6 Finalizando sesión...")
            resumen = manager.finalizar_sesion()
            
            self.print_info(f"   Duración: {resumen['duracion_minutos']} min")
            
            self.registrar_test("Flujo Completo", True, "Flujo end-to-end exitoso")
            return True
            
        except Exception as e:
            self.registrar_test("Flujo Completo", False, f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_sincronizacion(self):
        """Test 9: Sincronización MySQL ↔ SQLite"""
        self.print_test("Sincronización MySQL ↔ SQLite")
        
        try:
            sqlite = SQLiteManager()
            
            # Test sincronización desde MySQL
            self.print_info("Sincronizando DESDE MySQL...")
            resultado = sqlite.sincronizar_desde_mysql()
            
            productos_sync = resultado.get('productos', 0)
            conocimientos_sync = resultado.get('conocimientos', 0)
            
            self.print_info(f"   Productos: {productos_sync}")
            self.print_info(f"   Conocimientos: {conocimientos_sync}")
            
            if productos_sync > 0:
                self.registrar_test("Sincronización", True, f"{productos_sync} productos sincronizados")
                return True
            else:
                self.registrar_test("Sincronización", False, "No se sincronizaron productos")
                return False
                
        except Exception as e:
            self.registrar_test("Sincronización", False, f"Error: {e}")
            return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EJECUCIÓN DE TODOS LOS TESTS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def ejecutar_todos(self):
        """Ejecutar todos los tests"""
        
        self.inicio = datetime.now()
        
        self.print_header("VALIDACIÓN INTEGRAL DEL SISTEMA KAIROS", ColoresTerminal.MAGENTA)
        
        print(f"{ColoresTerminal.CYAN}Fecha: {self.inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Modo: Validación Completa{ColoresTerminal.RESET}\n")
        
        # Ejecutar tests en orden
        tests = [
            ("Componentes Base", [
                self.test_database_mysql,
                self.test_sqlite_offline,
                self.test_classifier_ml,
                self.test_productos_manager
            ]),
            ("Componentes de IA", [
                self.test_medical_assistant,
                self.test_diagnostico_engine,
                self.test_learner
            ]),
            ("Integración", [
                self.test_flujo_completo,
                self.test_sincronizacion
            ])
        ]
        
        for categoria, tests_categoria in tests:
            self.print_header(categoria)
            
            for test_func in tests_categoria:
                test_func()
                print()
                time.sleep(0.5)  # Pausa para legibilidad
        
        # Generar reporte final
        self.generar_reporte_final()
    
    def generar_reporte_final(self):
        """Generar reporte final de validación"""
        
        duracion = (datetime.now() - self.inicio).total_seconds()
        
        self.print_header("REPORTE FINAL", ColoresTerminal.MAGENTA)
        
        total = self.resultados['total_tests']
        exitosos = self.resultados['exitosos']
        fallidos = self.resultados['fallidos']
        porcentaje = (exitosos / total * 100) if total > 0 else 0
        
        print(f"{ColoresTerminal.NEGRITA}Estadísticas:{ColoresTerminal.RESET}")
        print(f"   Total de tests: {total}")
        print(f"   {ColoresTerminal.VERDE}✅ Exitosos: {exitosos}{ColoresTerminal.RESET}")
        print(f"   {ColoresTerminal.ROJO}❌ Fallidos: {fallidos}{ColoresTerminal.RESET}")
        print(f"   {ColoresTerminal.CYAN}Porcentaje: {porcentaje:.1f}%{ColoresTerminal.RESET}")
        print(f"   Duración: {duracion:.1f}s")
        
        print(f"\n{ColoresTerminal.NEGRITA}Detalle de Tests:{ColoresTerminal.RESET}")
        for test in self.resultados['tests']:
            icono = "✅" if test['exito'] else "❌"
            color = ColoresTerminal.VERDE if test['exito'] else ColoresTerminal.ROJO
            print(f"   {color}{icono} {test['nombre']}{ColoresTerminal.RESET}")
        
        # Resultado final
        print(f"\n{'='*70}")
        
        if fallidos == 0:
            print(f"{ColoresTerminal.VERDE}{ColoresTerminal.NEGRITA}")
            print("✅ SISTEMA COMPLETAMENTE FUNCIONAL")
            print("Todos los componentes pasaron las pruebas")
            print(f"{ColoresTerminal.RESET}")
        elif fallidos <= 2:
            print(f"{ColoresTerminal.AMARILLO}{ColoresTerminal.NEGRITA}")
            print("⚠️ SISTEMA FUNCIONAL CON ADVERTENCIAS")
            print(f"Algunos componentes necesitan atención")
            print(f"{ColoresTerminal.RESET}")
        else:
            print(f"{ColoresTerminal.ROJO}{ColoresTerminal.NEGRITA}")
            print("❌ SISTEMA CON PROBLEMAS")
            print(f"Revisa los componentes fallidos antes de usar en producción")
            print(f"{ColoresTerminal.RESET}")
        
        print("="*70 + "\n")
        
        # Recomendaciones
        if fallidos > 0:
            self.print_header("RECOMENDACIONES")
            
            if any('MySQL' in t['nombre'] for t in self.resultados['tests'] if not t['exito']):
                print("• Verifica la configuración de MySQL en .env")
                print("• Asegúrate de que el servidor MySQL esté corriendo")
            
            if any('GPT' in t['mensaje'] or 'IA' in t['mensaje'] for t in self.resultados['tests']):
                print("• Configura tu API key de OpenAI si quieres usar GPT")
                print("• El sistema puede funcionar sin GPT en modo básico")
            
            if any('Classifier' in t['nombre'] for t in self.resultados['tests'] if not t['exito']):
                print("• Ejecuta: python train.py para entrenar el clasificador")
            
            print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EJECUCIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    validador = ValidadorSistema()
    validador.ejecutar_todos()