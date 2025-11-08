"""
Conversation Orchestrator - Orquestador Principal
Coordina TODA la conversación: detecta, decide, responde, aprende
"""

import sys
import os
from typing import Dict, Optional
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from backend.core.intent_detector import IntentDetector
from backend.core.context_manager import ContextManager
from backend.core.response_generator import ResponseGenerator
from backend.core.personality_config import (
    obtener_frase,
    obtener_presentacion,
    obtener_info_creador,
    obtener_system_prompt,
    IDENTIDAD
)

class ConversationOrchestrator:
    """
    Orquestador Principal de Conversación
    
    Responsabilidades:
    1. Coordinar todos los componentes
    2. Gestionar el flujo de conversación
    3. Decidir qué tipo de respuesta dar
    4. Mantener coherencia
    5. Aprender de cada interacción
    """
    
    def __init__(self):
        """Inicializar orquestador"""
        
        # Componentes
        self.intent_detector = IntentDetector()
        self.context_manager = ContextManager()
        self.response_generator = ResponseGenerator()
        
        # Estado de la conversación
        self.estado = {
            'ya_saludo': False,
            'ya_se_presento': False,
            'consulta_activa': False,
            'esperando_diagnostico': False,
            'total_mensajes': 0
        }
        
        print("🎭 Conversation Orchestrator inicializado")
        print(f"   Kairos v1.0 - Creado por {IDENTIDAD['creador']}")
    
    def procesar_mensaje(self, mensaje: str, usuario_info: Dict = None) -> Dict:
        """Procesar mensaje completo"""
        
        print(f"\n{'='*70}")
        print(f"📨 Mensaje #{self.estado['total_mensajes'] + 1}")
        print(f"{'='*70}")
        
        # Actualizar info del paciente
        if usuario_info:
            self.context_manager.actualizar_paciente(
                nombre=usuario_info.get('nombre'),
                dni=usuario_info.get('dni')
            )
        
        self.estado['total_mensajes'] += 1
        
        # Detectar intención
        deteccion = self.intent_detector.detectar(mensaje)
        
        # Decidir tipo de respuesta
        tipo_respuesta = self._decidir_tipo_respuesta(deteccion)
        
        # Generar respuesta
        respuesta = self._generar_respuesta(mensaje, deteccion, tipo_respuesta, usuario_info)
        
        # Actualizar contexto
        if deteccion['es_consulta_medica']:
            self._actualizar_contexto_medico(mensaje, deteccion)
        
        self.context_manager.agregar_pregunta_respuesta(mensaje, respuesta)
        
        listo_diagnostico = self.context_manager.tiene_info_suficiente()
        
        return {
            'respuesta': respuesta,
            'intencion': deteccion['intencion'],
            'tipo_respuesta': tipo_respuesta,
            'diagnostico_listo': listo_diagnostico,
            'timestamp': datetime.now().isoformat()
        }
    
    def _decidir_tipo_respuesta(self, deteccion: Dict) -> str:
        """Decidir qué tipo de respuesta dar"""
        
        intencion = deteccion['intencion']
        
        if intencion in ['quien_eres', 'quien_te_creo', 'que_puedes_hacer']:
            return 'regla_fija'
        
        if intencion == 'saludo' and not self.estado['ya_saludo']:
            return 'regla_fija'
        
        if deteccion['es_consulta_medica'] or self.estado['consulta_activa']:
            return 'contexto_medico'
        
        return 'gpt_conversacional'
    
    def _generar_respuesta(self, mensaje: str, deteccion: Dict, 
                          tipo_respuesta: str, usuario_info: Dict) -> str:
        """Generar respuesta según el tipo"""
        
        nombre = self._obtener_primer_nombre()
        
        if tipo_respuesta == 'regla_fija':
            return self._respuesta_regla_fija(deteccion['intencion'], nombre)
        
        elif tipo_respuesta == 'contexto_medico':
            return self._respuesta_contexto_medico(mensaje, deteccion, nombre)
        
        else:
            return self._respuesta_gpt(mensaje, deteccion, nombre)
    
    def _respuesta_regla_fija(self, intencion: str, nombre: str) -> str:
        """Respuestas predefinidas"""
        
        if intencion == 'saludo':
            self.estado['ya_saludo'] = True
            return f"¡Hola {nombre}! Soy Kairos, tu médico de cabecera virtual en el que puedes confiar. ¿En qué puedo ayudarte hoy?"
        
        elif intencion == 'quien_eres':
            return obtener_presentacion()
        
        elif intencion == 'quien_te_creo':
            return obtener_info_creador()
        
        return "¿En qué puedo ayudarte?"
    
    def _respuesta_contexto_medico(self, mensaje: str, deteccion: Dict, nombre: str) -> str:
        """Respuesta en consulta médica"""
        
        if not self.estado['consulta_activa']:
            self.estado['consulta_activa'] = True
            
            sintoma = deteccion['sintomas'][0] if deteccion['sintomas'] else mensaje
            self.context_manager.agregar_sintoma_principal(sintoma)
            
            siguiente = self.context_manager.sugerir_siguiente_pregunta()
            return f"Entiendo {nombre}, {sintoma}. {siguiente}"
        
        else:
            if self.context_manager.tiene_info_suficiente():
                return f"Perfecto {nombre}, ya tengo toda la información. Analizando tu caso... 🔍"
            
            siguiente = self.context_manager.sugerir_siguiente_pregunta()
            return siguiente if siguiente else f"¿Algo más {nombre}?"
    
    def _respuesta_gpt(self, mensaje: str, deteccion: Dict, nombre: str) -> str:
        """Respuesta usando GPT"""
        
        contexto = self.context_manager.obtener_contexto_para_gpt()
        
        resultado = self.response_generator.generar_respuesta(
            mensaje=mensaje,
            intencion=deteccion['intencion'],
            contexto=contexto,
            system_prompt=obtener_system_prompt(),
            usar_aprendizaje=True
        )
        
        return resultado['respuesta']
    
    def _actualizar_contexto_medico(self, mensaje: str, deteccion: Dict):
        """Actualizar contexto médico"""
        
        if deteccion['entidades']:
            self.context_manager.actualizar_desde_entidades(deteccion['entidades'])
        
        for sintoma in deteccion['sintomas']:
            if not self.context_manager.contexto['medico']['sintoma_principal']:
                self.context_manager.agregar_sintoma_principal(sintoma)
            else:
                self.context_manager.agregar_sintoma_adicional(sintoma)
    
    def _obtener_primer_nombre(self) -> str:
        """Obtener primer nombre"""
        nombre = self.context_manager.contexto['paciente']['nombre']
        return nombre.split()[0] if nombre else ""
    
    def reiniciar_conversacion(self):
        """Reiniciar"""
        self.context_manager.reiniciar()
        self.estado = {
            'ya_saludo': False,
            'ya_se_presento': False,
            'consulta_activa': False,
            'esperando_diagnostico': False,
            'total_mensajes': 0
        }


if __name__ == "__main__":
    print("🧪 TEST")
    orchestrator = ConversationOrchestrator()
    
    resultado = orchestrator.procesar_mensaje("hola", {'nombre': 'Juan'})
    print(f"Respuesta: {resultado['respuesta']}")