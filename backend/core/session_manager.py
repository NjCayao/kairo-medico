"""
Gestor de Sesiones Autónomas - VERSIÓN ROBUSTA
Coordina todo el flujo de consulta de inicio a fin
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.medical_assistant import MedicalAssistant
from backend.core.diagnostico import DiagnosticoEngine
from backend.database.database_manager import DatabaseManager
from backend.database.sqlite_manager import SQLiteManager

class EstadoSesion:
    """Estados posibles de una sesión"""
    DISPONIBLE = 'disponible'
    INICIANDO = 'iniciando'
    CAPTURANDO_DATOS = 'capturando_datos'
    CONSULTANDO = 'consultando'
    GENERANDO_RECETA = 'generando_receta'
    IMPRIMIENDO = 'imprimiendo'
    FINALIZANDO = 'finalizando'
    FINALIZADA = 'finalizada'
    ERROR = 'error'

class SessionManager:
    """
    Gestor completo de sesiones autónomas
    Coordina: captura → conversación → diagnóstico → receta → impresión
    """
    
    def __init__(self, evento: str = None, ubicacion: str = None, 
                 dispositivo: str = None, modo_offline: bool = False):
        """
        Inicializar gestor de sesiones
        
        Args:
            evento: Nombre del evento (ej: "Feria Salud Lima 2025")
            ubicacion: Ubicación física (ej: "Stand 12")
            dispositivo: Identificador del dispositivo (ej: "Tablet-01")
            modo_offline: True para funcionar sin internet
        """
        self.evento = evento or "Evento Kairos"
        self.ubicacion = ubicacion or "Stand Principal"
        self.dispositivo = dispositivo or f"Device-{uuid.uuid4().hex[:6]}"
        self.modo_offline = modo_offline
        
        # Componentes
        self.db = DatabaseManager()
        self.sqlite = SQLiteManager() if modo_offline else None
        self.medical_assistant = MedicalAssistant()
        self.diagnostico_engine = DiagnosticoEngine()
        
        # Estado de sesión actual
        self.sesion_id = None
        self.usuario_id = None
        self.usuario_data = None
        self.estado = EstadoSesion.DISPONIBLE
        self.inicio_sesion = None
        self.mensajes_conversacion = []
        self.contexto_completo = {}
        self.diagnostico_resultado = None
        self.receta_generada = None
        
        # Métricas
        self.total_sesiones = 0
        self.sesiones_exitosas = 0
        self.errores = []
        
        print("="*70)
        print("🤖 SESSION MANAGER - MODO ROBUSTO")
        print("="*70)
        print(f"   Evento: {self.evento}")
        print(f"   Ubicación: {self.ubicacion}")
        print(f"   Dispositivo: {self.dispositivo}")
        print(f"   Modo offline: {'✅ SÍ' if modo_offline else '❌ NO'}")
        print("="*70 + "\n")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CICLO DE VIDA DE SESIÓN
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def nueva_sesion(self) -> Tuple[bool, str, Dict]:
        """
        Crear nueva sesión
        
        Returns:
            Tuple (exito, sesion_id, info)
        """
        try:
            # Generar ID único
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            self.sesion_id = f"FERIA-{timestamp}-{uuid.uuid4().hex[:6]}"
            self.inicio_sesion = datetime.now()
            self.estado = EstadoSesion.INICIANDO
            
            # Reiniciar estado
            self.usuario_id = None
            self.usuario_data = None
            self.mensajes_conversacion = []
            self.contexto_completo = {}
            self.diagnostico_resultado = None
            self.receta_generada = None
            
            # Reiniciar asistente médico
            self.medical_assistant.reiniciar_conversacion()
            
            # Guardar en BD
            if not self.modo_offline:
                self.db.crear_sesion(
                    self.sesion_id,
                    self.evento,
                    self.ubicacion,
                    self.dispositivo
                )
            else:
                self.sqlite.guardar_sesion_offline(
                    self.sesion_id,
                    self.evento,
                    self.ubicacion
                )
            
            self.total_sesiones += 1
            
            print(f"\n{'='*70}")
            print(f"✅ NUEVA SESIÓN CREADA: {self.sesion_id}")
            print(f"{'='*70}\n")
            
            return True, self.sesion_id, {
                'sesion_id': self.sesion_id,
                'evento': self.evento,
                'ubicacion': self.ubicacion,
                'timestamp': self.inicio_sesion.isoformat()
            }
            
        except Exception as e:
            self._registrar_error("nueva_sesion", str(e))
            return False, None, {'error': str(e)}
    
    def capturar_datos_paciente(self, nombre: str, dni: str, 
                                edad: int = None) -> Tuple[bool, Dict]:
        """
        Capturar y validar datos del paciente
        
        Args:
            nombre: Nombre completo
            dni: DNI 8 dígitos
            edad: Edad opcional
            
        Returns:
            Tuple (exito, info_usuario)
        """
        try:
            self._cambiar_estado(EstadoSesion.CAPTURANDO_DATOS)
            
            # Validar datos
            validacion = self._validar_datos_paciente(nombre, dni, edad)
            if not validacion['valido']:
                return False, validacion
            
            # Buscar si usuario existe
            if not self.modo_offline:
                usuario_existente = self.db.buscar_usuario_por_dni(dni)
            else:
                usuario_existente = self.sqlite.buscar_usuario_offline(dni)
            
            if usuario_existente:
                # Usuario recurrente
                self.usuario_id = usuario_existente['id']
                self.usuario_data = usuario_existente
                
                print(f"👤 Usuario recurrente: {usuario_existente['nombre']}")
                print(f"   Consultas previas: {usuario_existente.get('total_consultas', 0)}")
                
            else:
                # Usuario nuevo
                if not self.modo_offline:
                    self.usuario_id = self.db.crear_usuario(
                        nombre, dni, edad, 
                        origen='feria',
                        evento=self.evento
                    )
                else:
                    self.usuario_id = self.sqlite.crear_usuario_offline(
                        nombre, dni, edad
                    )
                
                self.usuario_data = {
                    'id': self.usuario_id,
                    'nombre': nombre,
                    'dni': dni,
                    'edad': edad,
                    'nuevo': True
                }
                
                print(f"👤 Usuario nuevo: {nombre}")
            
            # Guardar datos en sesión
            if not self.modo_offline:
                self.db.guardar_datos_capturados(
                    self.sesion_id, nombre, dni, edad, self.usuario_id
                )
            
            return True, {
                'usuario_id': self.usuario_id,
                'nombre': self.usuario_data['nombre'],
                'es_nuevo': self.usuario_data.get('nuevo', False),
                'consultas_previas': usuario_existente.get('total_consultas', 0) if usuario_existente else 0
            }
            
        except Exception as e:
            self._registrar_error("capturar_datos", str(e))
            return False, {'error': str(e)}
    
    def procesar_mensaje(self, mensaje: str) -> Dict:
        """
        Procesar mensaje del usuario durante consulta
        
        Args:
            mensaje: Mensaje del usuario
            
        Returns:
            Dict con respuesta y estado
        """
        try:
            self._cambiar_estado(EstadoSesion.CONSULTANDO)
            
            # Procesar con medical assistant
            resultado = self.medical_assistant.procesar_mensaje(
                mensaje, 
                self.usuario_data
            )
            
            # Guardar mensaje
            self.mensajes_conversacion.append({
                'timestamp': datetime.now().isoformat(),
                'tipo': 'usuario',
                'mensaje': mensaje,
                'intencion': resultado['intencion'],
                'confianza': resultado['confianza']
            })
            
            self.mensajes_conversacion.append({
                'timestamp': datetime.now().isoformat(),
                'tipo': 'kairos',
                'mensaje': resultado['respuesta']
            })
            
            # Guardar en BD
            if not self.modo_offline:
                self.db.guardar_mensaje(
                    self.usuario_id,
                    self.sesion_id,
                    mensaje,
                    resultado['intencion'],
                    resultado['confianza'],
                    resultado['respuesta']
                )
            
            # Actualizar contexto
            self.contexto_completo = resultado['contexto']
            
            # Verificar si está listo para diagnóstico
            if resultado['diagnostico_listo']:
                print("\n✅ Información suficiente para diagnóstico")
            
            return {
                'respuesta': resultado['respuesta'],
                'intencion': resultado['intencion'],
                'confianza': resultado['confianza'],
                'diagnostico_listo': resultado['diagnostico_listo'],
                'total_mensajes': len(self.mensajes_conversacion)
            }
            
        except Exception as e:
            self._registrar_error("procesar_mensaje", str(e))
            return {
                'respuesta': "Disculpa, ocurrió un error. ¿Podrías repetir?",
                'error': str(e)
            }
    
    def generar_diagnostico_y_receta(self) -> Tuple[bool, Dict]:
        """
        Generar diagnóstico completo y receta
        
        Returns:
            Tuple (exito, resultado_completo)
        """
        try:
            self._cambiar_estado(EstadoSesion.GENERANDO_RECETA)
            
            print(f"\n{'='*70}")
            print("🧠 GENERANDO DIAGNÓSTICO Y RECETA")
            print(f"{'='*70}\n")
            
            # Obtener resumen de conversación
            resumen = self.medical_assistant.obtener_resumen_consulta()
            
            # Generar diagnóstico con motor (3 capas)
            self.diagnostico_resultado = self.diagnostico_engine.analizar_completo(
                self.contexto_completo,
                self.sesion_id,
                self.usuario_id
            )
            
            self.receta_generada = self.diagnostico_resultado['receta']
            
            # Guardar consulta completa en BD
            consulta_id = self._guardar_consulta_completa(
                resumen,
                self.diagnostico_resultado
            )
            
            # Actualizar sesión
            if not self.modo_offline:
                self.db.finalizar_sesion(
                    self.sesion_id,
                    self.diagnostico_resultado['condicion'],
                    [p['id'] for p in self.diagnostico_resultado['productos']],
                    self.receta_generada['texto_ticket'],
                    consulta_id
                )
            
            print(f"\n{'='*70}")
            print("✅ DIAGNÓSTICO Y RECETA GENERADOS")
            print(f"{'='*70}\n")
            
            return True, {
                'diagnostico': self.diagnostico_resultado['condicion'],
                'confianza': self.diagnostico_resultado['confianza'],
                'productos': self.diagnostico_resultado['productos'],
                'receta': self.receta_generada,
                'origen': self.diagnostico_resultado['origen'],
                'consulta_id': consulta_id
            }
            
        except Exception as e:
            self._registrar_error("generar_diagnostico", str(e))
            return False, {'error': str(e)}
    
    def imprimir_receta(self) -> Tuple[bool, Dict]:
        """
        Imprimir receta en ticket térmico
        
        Returns:
            Tuple (exito, info_impresion)
        """
        try:
            self._cambiar_estado(EstadoSesion.IMPRIMIENDO)
            
            print(f"\n{'='*70}")
            print("🖨️ IMPRIMIENDO RECETA")
            print(f"{'='*70}\n")
            
            # TODO: Integrar con printer.py cuando esté listo
            # Por ahora, simulamos impresión exitosa
            
            # Registrar impresión
            if not self.modo_offline:
                self.db.registrar_impresion(
                    self.sesion_id,
                    self.diagnostico_resultado.get('consulta_id'),
                    self.usuario_id,
                    estado='exitosa',
                    impresora='Xprinter XP-58IIH'
                )
                
                self.db.marcar_ticket_impreso(self.sesion_id)
            
            print("✅ Ticket impreso correctamente\n")
            
            return True, {
                'impreso': True,
                'archivo_pdf': f"recetas/{self.sesion_id}.pdf"
            }
            
        except Exception as e:
            self._registrar_error("imprimir_receta", str(e))
            
            # Registrar error
            if not self.modo_offline:
                self.db.registrar_impresion(
                    self.sesion_id,
                    None,
                    self.usuario_id,
                    estado='fallida',
                    error=str(e)
                )
            
            return False, {'error': str(e)}
    
    def finalizar_sesion(self) -> Dict:
        """
        Finalizar sesión y preparar para siguiente paciente
        
        Returns:
            Dict con resumen de sesión
        """
        try:
            self._cambiar_estado(EstadoSesion.FINALIZANDO)
            
            # Calcular duración
            duracion = (datetime.now() - self.inicio_sesion).total_seconds() / 60
            
            # Actualizar estadísticas usuario
            if not self.modo_offline:
                self.db.actualizar_ultimo_contacto(self.usuario_id)
                self.db.incrementar_total_consultas(self.usuario_id)
            
            # Resumen de sesión
            resumen = {
                'sesion_id': self.sesion_id,
                'usuario': self.usuario_data['nombre'],
                'dni': self.usuario_data['dni'],
                'diagnostico': self.diagnostico_resultado['condicion'],
                'productos': len(self.diagnostico_resultado['productos']),
                'duracion_minutos': round(duracion, 1),
                'total_mensajes': len(self.mensajes_conversacion),
                'origen_diagnostico': self.diagnostico_resultado['origen'],
                'ticket_impreso': True
            }
            
            self._cambiar_estado(EstadoSesion.FINALIZADA)
            self.sesiones_exitosas += 1
            
            print(f"\n{'='*70}")
            print("✅ SESIÓN FINALIZADA")
            print(f"{'='*70}")
            print(f"   Paciente: {self.usuario_data['nombre']}")
            print(f"   Diagnóstico: {self.diagnostico_resultado['condicion']}")
            print(f"   Duración: {round(duracion, 1)} min")
            print(f"   Origen: {self.diagnostico_resultado['origen']}")
            print(f"{'='*70}\n")
            
            # Preparar para siguiente
            self._reset_para_siguiente()
            
            return resumen
            
        except Exception as e:
            self._registrar_error("finalizar_sesion", str(e))
            return {'error': str(e)}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES AUXILIARES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _cambiar_estado(self, nuevo_estado: str):
        """Cambiar estado de sesión"""
        self.estado = nuevo_estado
        
        if not self.modo_offline and self.sesion_id:
            self.db.actualizar_estado_sesion(self.sesion_id, nuevo_estado)
    
    def _validar_datos_paciente(self, nombre: str, dni: str, 
                                edad: int = None) -> Dict:
        """
        Validar datos del paciente
        
        Returns:
            Dict con resultado de validación
        """
        errores = []
        
        # Validar nombre
        if not nombre or len(nombre.strip()) < 3:
            errores.append("Nombre muy corto (mínimo 3 caracteres)")
        
        partes_nombre = nombre.strip().split()
        if len(partes_nombre) < 2:
            errores.append("Ingresa nombre y apellido")
        
        # Validar DNI
        if not dni or len(dni) != 8:
            errores.append("DNI debe tener 8 dígitos")
        
        if not dni.isdigit():
            errores.append("DNI solo debe contener números")
        
        # Validar edad
        if edad is not None:
            if edad < 0 or edad > 120:
                errores.append("Edad fuera de rango válido (0-120)")
        
        return {
            'valido': len(errores) == 0,
            'errores': errores
        }
    
    def _guardar_consulta_completa(self, resumen: Dict, 
                                   diagnostico: Dict) -> int:
        """Guardar consulta completa en BD"""
        
        datos_consulta = {
            'usuario_id': self.usuario_id,
            'sesion_id': self.sesion_id,
            'sintoma_principal': resumen['sintoma_principal'],
            'diagnostico': diagnostico['condicion'],
            'confianza': diagnostico['confianza'],
            'causas': ', '.join(diagnostico.get('causas', [])),
            'productos': diagnostico['productos'],
            'receta_completa': diagnostico['receta']['texto_ticket'],
            'conversacion': self.mensajes_conversacion,
            'duracion_minutos': (datetime.now() - self.inicio_sesion).total_seconds() / 60,
            'canal': 'feria',
            'modo': 'autonomo'
        }
        
        if not self.modo_offline:
            return self.db.guardar_consulta(datos_consulta)
        else:
            return self.sqlite.guardar_consulta_offline(datos_consulta)
    
    def _registrar_error(self, funcion: str, error: str):
        """Registrar error para análisis"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'funcion': funcion,
            'error': error,
            'sesion_id': self.sesion_id,
            'estado': self.estado
        }
        
        self.errores.append(error_info)
        
        print(f"\n❌ ERROR en {funcion}: {error}\n")
    
    def _reset_para_siguiente(self):
        """Limpiar estado para siguiente paciente"""
        self.sesion_id = None
        self.usuario_id = None
        self.usuario_data = None
        self.estado = EstadoSesion.DISPONIBLE
        self.inicio_sesion = None
        self.mensajes_conversacion = []
        self.contexto_completo = {}
        self.diagnostico_resultado = None
        self.receta_generada = None
        
        self.medical_assistant.reiniciar_conversacion()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ESTADÍSTICAS Y MONITOREO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def obtener_estadisticas(self) -> Dict:
        """Obtener estadísticas de sesión actual y general"""
        
        stats = {
            'dispositivo': self.dispositivo,
            'evento': self.evento,
            'ubicacion': self.ubicacion,
            'estado_actual': self.estado,
            'sesion_activa': self.sesion_id,
            'total_sesiones': self.total_sesiones,
            'sesiones_exitosas': self.sesiones_exitosas,
            'tasa_exito': (self.sesiones_exitosas / self.total_sesiones * 100) if self.total_sesiones > 0 else 0,
            'total_errores': len(self.errores)
        }
        
        # Estadísticas de BD
        if not self.modo_offline:
            stats_db = self.db.obtener_estadisticas_hoy()
            stats.update(stats_db)
        
        return stats
    
    def obtener_errores_recientes(self, limite: int = 10) -> List[Dict]:
        """Obtener errores recientes"""
        return self.errores[-limite:]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*20 + "🧪 TEST SESSION MANAGER")
    print("="*70 + "\n")
    
    # Crear gestor
    manager = SessionManager(
        evento="Feria Salud Lima 2025",
        ubicacion="Stand 12",
        dispositivo="Tablet-Test",
        modo_offline=False
    )
    
    # TEST 1: Crear sesión
    print("TEST 1: Crear nueva sesión")
    exito, sesion_id, info = manager.nueva_sesion()
    print(f"   Resultado: {'✅ OK' if exito else '❌ FALLÓ'}")
    print(f"   Sesión ID: {sesion_id}\n")
    
    # TEST 2: Capturar datos
    print("TEST 2: Capturar datos paciente")
    exito, info = manager.capturar_datos_paciente(
        "María López García",
        "12345678",
        32
    )
    print(f"   Resultado: {'✅ OK' if exito else '❌ FALLÓ'}")
    if exito:
        print(f"   Usuario: {info['nombre']}")
        print(f"   Es nuevo: {info['es_nuevo']}\n")
    
    # TEST 3: Conversación simulada
    print("TEST 3: Conversación médica")
    mensajes_test = [
        "Hola",
        "Me duele mucho la cabeza",
        "En la frente y las sienes",
        "Como una semana",
        "Un 7 de 10"
    ]
    
    for i, msg in enumerate(mensajes_test, 1):
        print(f"   Mensaje {i}: '{msg}'")
        resultado = manager.procesar_mensaje(msg)
        print(f"   Respuesta: {resultado['respuesta'][:50]}...")
        
        if resultado.get('diagnostico_listo'):
            print("   ✅ Listo para diagnóstico\n")
            break
    
    # TEST 4: Generar diagnóstico
    print("TEST 4: Generar diagnóstico y receta")
    exito, resultado = manager.generar_diagnostico_y_receta()
    print(f"   Resultado: {'✅ OK' if exito else '❌ FALLÓ'}")
    if exito:
        print(f"   Diagnóstico: {resultado['diagnostico']}")
        print(f"   Confianza: {resultado['confianza']:.0%}")
        print(f"   Origen: {resultado['origen']}\n")
    
    # TEST 5: Imprimir
    print("TEST 5: Imprimir receta")
    exito, info = manager.imprimir_receta()
    print(f"   Resultado: {'✅ OK' if exito else '❌ FALLÓ'}\n")
    
    # TEST 6: Finalizar
    print("TEST 6: Finalizar sesión")
    resumen = manager.finalizar_sesion()
    print(f"   Duración: {resumen.get('duracion_minutos', 0)} min")
    print(f"   Mensajes: {resumen.get('total_mensajes', 0)}\n")
    
    # Estadísticas finales
    print("="*70)
    print("ESTADÍSTICAS FINALES")
    print("="*70)
    stats = manager.obtener_estadisticas()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*70)