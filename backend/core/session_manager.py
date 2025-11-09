"""
Session Manager V3.0
✅ Muestra receta COMPLETA (causas, dieta, hábitos, tiempo)
✅ Detalles de productos (dosis, momento, duración)
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.gpt_orchestrator import GPTOrchestrator
from backend.core.motor_diagnostico import MotorDiagnosticoV3
from backend.database.database_manager import DatabaseManager

class SessionManager:
    """Session Manager V3.0"""
    
    def __init__(self, evento: str, ubicacion: str, dispositivo: str):
        self.evento = evento
        self.ubicacion = ubicacion
        self.dispositivo = dispositivo
        
        self.db = DatabaseManager()
        self.orchestrator = GPTOrchestrator()
        self.motor = MotorDiagnosticoV3()
        
        self.sesion_id = None
        self.estado = 'iniciando'
        self.usuario_data = None
        self.mensajes_conversacion = []
        self.diagnostico_actual = None
        self.fecha_inicio = None
        
        print(f"\n{'='*70}")
        print("🤖 SESSION MANAGER V3.0")
        print(f"{'='*70}\n")
    
    def nueva_sesion(self) -> Tuple[bool, str, Dict]:
        """Crear nueva sesión"""
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        random_id = hex(hash(timestamp) & 0xffffff)[2:]
        self.sesion_id = f"KAIROS-{timestamp}-{random_id}"
        
        self.fecha_inicio = datetime.now()
        self.estado = 'capturando_datos'
        
        self.db.crear_sesion(self.sesion_id, self.evento, self.ubicacion, self.dispositivo)
        
        return True, self.sesion_id, {'sesion_id': self.sesion_id, 'estado': self.estado}
    
    def capturar_datos_paciente(self, nombre: str, dni: str, edad: int = None) -> Tuple[bool, Dict]:
        """Capturar datos del paciente"""
        
        if not dni or len(dni) != 8 or not dni.isdigit():
            return False, {'error': 'DNI inválido'}
        
        usuario = self.db.buscar_usuario_por_dni(dni)
        
        if usuario:
            usuario_id = usuario['id']
            es_nuevo = False
            self.db.actualizar_ultimo_contacto(usuario_id)
            self.db.incrementar_total_consultas(usuario_id)
        else:
            usuario_id = self.db.crear_usuario(nombre, dni, edad, origen='feria', evento=self.evento)
            es_nuevo = True
        
        self.usuario_data = {'id': usuario_id, 'nombre': nombre, 'dni': dni, 'edad': edad, 'es_nuevo': es_nuevo}
        
        self.db.guardar_datos_capturados(self.sesion_id, nombre, dni, edad, usuario_id)
        
        self.estado = 'consultando'
        self.db.actualizar_estado_sesion(self.sesion_id, 'consultando')
        
        return True, {'usuario_id': usuario_id, 'es_nuevo': es_nuevo, 'nombre': nombre}
    
    def procesar_mensaje(self, mensaje_usuario: str) -> Dict:
        """Procesar mensaje del usuario"""
        
        self.mensajes_conversacion.append({
            'role': 'user',
            'content': mensaje_usuario,
            'timestamp': datetime.now().isoformat()
        })
        
        if self.diagnostico_actual:
            return self._procesar_duda_post_diagnostico(mensaje_usuario)
        
        contexto = {'mensajes': self.mensajes_conversacion, 'usuario': self.usuario_data}
        
        decision = self.orchestrator.decidir_accion(contexto)
        respuesta = self.orchestrator.generar_respuesta(decision, contexto)
        
        self.mensajes_conversacion.append({
            'role': 'assistant',
            'content': respuesta,
            'timestamp': datetime.now().isoformat()
        })
        
        # ⭐ Guardar en tabla conversaciones (mensaje por mensaje)
        self._guardar_mensaje_conversacion(mensaje_usuario, respuesta, decision.get('accion', ''))
        
        return {
            'respuesta': respuesta,
            'tipo': decision['accion'],
            'listo_diagnostico': decision['accion'] == 'diagnosticar',
            'preguntas_realizadas': self.orchestrator.preguntas_realizadas
        }
    
    def _guardar_mensaje_conversacion(self, mensaje_usuario: str, respuesta: str, intencion: str):
        """Guardar en tabla conversaciones (turno por turno)"""
        try:
            query = """
            INSERT INTO conversaciones 
            (usuario_id, sesion_id, mensaje_usuario, intencion_detectada, 
             respuesta_kairos, fecha, canal)
            VALUES (%s, %s, %s, %s, %s, NOW(), 'feria')
            """
            
            params = (
                self.usuario_data['id'],
                self.sesion_id,
                mensaje_usuario,
                intencion,
                respuesta
            )
            
            self.db.ejecutar_comando(query, params)
        
        except Exception as e:
            print(f"❌ Error guardando conversación: {e}")
    
    def _procesar_duda_post_diagnostico(self, pregunta: str) -> Dict:
        """Procesar dudas después del diagnóstico"""
        
        palabras_continuar = ['imprimir', 'listo', 'continuar', 'siguiente', 'ok']
        if any(palabra in pregunta.lower() for palabra in palabras_continuar):
            return {
                'respuesta': 'Perfecto, tu receta está lista.',
                'tipo': 'continuar',
                'listo_imprimir': True
            }
        
        respuesta = self.motor.responder_duda_post_diagnostico(pregunta, self.diagnostico_actual)
        
        self.mensajes_conversacion.append({'role': 'user', 'content': pregunta, 'timestamp': datetime.now().isoformat()})
        self.mensajes_conversacion.append({'role': 'assistant', 'content': respuesta, 'timestamp': datetime.now().isoformat()})
        
        return {'respuesta': respuesta, 'tipo': 'respuesta_duda', 'listo_diagnostico': True, 'listo_imprimir': False}
    
    def generar_diagnostico_y_receta(self) -> Tuple[bool, Dict]:
        """Generar diagnóstico y receta"""
        
        self.estado = 'generando_receta'
        self.db.actualizar_estado_sesion(self.sesion_id, 'generando_receta')
        
        contexto = {'mensajes': self.mensajes_conversacion, 'usuario': self.usuario_data, 'sesion_id': self.sesion_id}
        
        exito, resultado = self.motor.generar_diagnostico_completo(contexto)
        
        if not exito:
            return False, resultado
        
        self.diagnostico_actual = resultado
        
        self._guardar_diagnostico_bd(resultado)
        
        return True, resultado
    
    def _guardar_diagnostico_bd(self, diagnostico: Dict):
        """Guardar diagnóstico en BD"""
        
        duracion = (datetime.now() - self.fecha_inicio).total_seconds() / 60
        
        # ⭐ Preparar mensajes_conversacion como JSON string
        import json
        mensajes_json = json.dumps(self.mensajes_conversacion, ensure_ascii=False)
        
        datos = {
            'usuario_id': self.usuario_data['id'],
            'sesion_id': self.sesion_id,
            'sintoma_principal': self._extraer_sintoma_principal(),
            'diagnostico': diagnostico['diagnostico'],
            'confianza': diagnostico.get('confianza', 0.85),
            'causas': ', '.join(diagnostico.get('causas', [])),
            'productos': [p['id'] for p in diagnostico['productos']],
            'mensajes_conversacion': mensajes_json,  # ⭐ JSON completo aquí
            'receta_completa': self._generar_texto_receta(diagnostico),
            'conversacion': self.mensajes_conversacion,
            'duracion_minutos': round(duracion, 1),
            'canal': 'feria',
            'modo': 'gpt'
        }
        
        consulta_id = self.db.guardar_consulta(datos)
        
        return consulta_id
    
    def _extraer_sintoma_principal(self) -> str:
        """Extraer síntoma principal"""
        if self.mensajes_conversacion and len(self.mensajes_conversacion) > 0:
            primer_mensaje = self.mensajes_conversacion[0]['content']
            return primer_mensaje[:100]
        return 'Consulta general'
    
    def _generar_texto_receta(self, diagnostico: Dict) -> str:
        """Generar texto de receta completo"""
        
        texto = f"DIAGNÓSTICO: {diagnostico['diagnostico']}\n"
        texto += f"CONFIANZA: {int(diagnostico.get('confianza', 0.85) * 100)}%\n\n"
        
        if diagnostico.get('causas'):
            texto += "CAUSAS PROBABLES:\n"
            for causa in diagnostico['causas']:
                texto += f"• {causa}\n"
            texto += "\n"
        
        if diagnostico.get('explicacion_causas'):
            texto += f"POR QUÉ SURGE:\n{diagnostico['explicacion_causas']}\n\n"
        
        if diagnostico['productos']:
            texto += "PRODUCTOS NATURALES:\n"
            for p in diagnostico['productos']:
                texto += f"• {p['nombre']} - S/.{p['precio']:.2f}\n"
                texto += f"  Dosis: {p.get('dosis', 'Ver etiqueta')}\n"
                texto += f"  Cuándo: {p.get('cuando_tomar', 'Con alimentos')}\n"
                texto += f"  Duración: {p.get('duracion', '1 mes')}\n\n"
        
        if diagnostico['plantas']:
            texto += "PLANTAS MEDICINALES:\n"
            for p in diagnostico['plantas']:
                texto += f"• {p['nombre_comun']}\n"
                texto += f"  Forma: {p.get('forma_uso', 'Infusión')}\n"
                texto += f"  Dosis: {p.get('dosis', '1-3 tazas')}\n\n"
        
        if diagnostico['remedios']:
            texto += "REMEDIOS CASEROS:\n"
            for r in diagnostico['remedios']:
                texto += f"• {r['nombre']}\n"
                if r.get('como_usar'):
                    texto += f"  {r['como_usar']}\n"
                texto += "\n"
        
        if diagnostico.get('consejos_dieta'):
            texto += "DIETA RECOMENDADA:\n"
            for consejo in diagnostico['consejos_dieta']:
                texto += f"• {consejo}\n"
            texto += "\n"
        
        if diagnostico.get('consejos_habitos'):
            texto += "HÁBITOS SALUDABLES:\n"
            for consejo in diagnostico['consejos_habitos']:
                texto += f"• {consejo}\n"
            texto += "\n"
        
        if diagnostico.get('tiempo_mejoria'):
            texto += f"TIEMPO ESTIMADO DE MEJORÍA:\n{diagnostico['tiempo_mejoria']}\n\n"
        
        return texto
    
    def imprimir_receta(self) -> Tuple[bool, Dict]:
        """Marcar receta como lista"""
        
        if not self.diagnostico_actual:
            return False, {'error': 'No hay diagnóstico'}
        
        self.db.marcar_ticket_impreso(self.sesion_id)
        self.db.registrar_impresion(self.sesion_id, None, self.usuario_data['id'], 'lista')
        
        return True, {'mensaje': 'Receta guardada en BD'}
    
    def finalizar_sesion(self) -> Dict:
        """Finalizar sesión"""
        
        self.estado = 'finalizada'
        duracion = (datetime.now() - self.fecha_inicio).total_seconds() / 60
        
        if self.diagnostico_actual:
            productos_ids = [p['id'] for p in self.diagnostico_actual['productos']]
            self.db.finalizar_sesion(self.sesion_id, self.diagnostico_actual['diagnostico'], productos_ids, self._generar_texto_receta(self.diagnostico_actual), None)
        
        resumen = {
            'sesion_id': self.sesion_id,
            'paciente': self.usuario_data['nombre'] if self.usuario_data else None,
            'diagnostico': self.diagnostico_actual['diagnostico'] if self.diagnostico_actual else None,
            'duracion_minutos': round(duracion, 1),
            'productos': len(self.diagnostico_actual['productos']) if self.diagnostico_actual else 0,
            'plantas': len(self.diagnostico_actual['plantas']) if self.diagnostico_actual else 0,
            'remedios': len(self.diagnostico_actual['remedios']) if self.diagnostico_actual else 0
        }
        
        return resumen