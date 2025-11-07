"""
Medical Assistant - Cerebro principal de Kairos
Maneja la conversación médica y coordina diagnóstico
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Agregar paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from backend.core.classifier import IntentClassifier
from backend.database.productos_manager import ProductosManager

class MedicalAssistant:
    """
    Asistente médico virtual de Kairos
    """
    
    def __init__(self):
        """Inicializar asistente médico"""
        
        # Componentes
        self.classifier = IntentClassifier()
        self.productos = ProductosManager()
        
        # Estado de la conversación
        self.contexto = {
            'sintoma_principal': None,
            'sintomas_adicionales': [],
            'intensidad': None,
            'duracion': None,
            'frecuencia': None,
            'momento_dia': None,
            'factores_mejoran': [],
            'factores_empeoran': [],
            'medicamentos_actuales': [],
            'alergias': [],
            'preguntas_realizadas': [],
            'respuestas_usuario': []
        }
        
        # Contador de preguntas (modo express: máximo 8)
        self.preguntas_realizadas = 0
        self.max_preguntas = 8
        
        # Estado
        self.consulta_iniciada = False
        self.diagnostico_completo = False
        
        print("🤖 Kairos Medical Assistant inicializado")
    
    def procesar_mensaje(self, mensaje: str, usuario_info: Dict = None) -> Dict:
        """
        Procesar mensaje del usuario y generar respuesta
        
        Args:
            mensaje: Mensaje del usuario
            usuario_info: Información del usuario (opcional)
            
        Returns:
            Dict con respuesta y datos
        """
        
        # Clasificar intención
        intencion, confianza, probabilidades = self.classifier.predecir(mensaje)
        
        print(f"💭 Intención detectada: {intencion} ({confianza:.0%})")
        
        # Guardar en contexto
        self.contexto['preguntas_realizadas'].append(mensaje)
        
        # Determinar tipo de respuesta según intención
        if intencion == 'saludo':
            respuesta = self._respuesta_saludo(usuario_info)
            tipo_respuesta = 'saludo'
            
        elif intencion == 'consulta_medica':
            respuesta = self._respuesta_consulta_medica(mensaje)
            tipo_respuesta = 'consulta'
            
        elif intencion == 'pregunta_producto':
            respuesta = self._respuesta_pregunta_producto(mensaje)
            tipo_respuesta = 'info_producto'
            
        elif intencion == 'pregunta_uso':
            respuesta = self._respuesta_pregunta_uso(mensaje)
            tipo_respuesta = 'info_uso'
            
        elif intencion == 'pregunta_precio':
            respuesta = self._respuesta_pregunta_precio(mensaje)
            tipo_respuesta = 'info_precio'
            
        elif intencion == 'despedida':
            respuesta = self._respuesta_despedida()
            tipo_respuesta = 'despedida'
            
        else:
            respuesta = self._respuesta_desconocida(mensaje)
            tipo_respuesta = 'desconocida'
        
        return {
            'respuesta': respuesta,
            'intencion': intencion,
            'confianza': confianza,
            'tipo_respuesta': tipo_respuesta,
            'contexto': self.contexto.copy(),
            'diagnostico_listo': self.diagnostico_completo
        }
    
    def _respuesta_saludo(self, usuario_info: Dict = None) -> str:
        """Respuesta a saludos"""
        
        nombre = usuario_info.get('nombre', '') if usuario_info else ''
        nombre_primero = nombre.split()[0] if nombre else ''
        
        if nombre_primero:
            return f"¡Hola {nombre_primero}! 👋 Soy Kairos, tu asistente de salud natural. ¿En qué puedo ayudarte hoy?"
        else:
            return "¡Hola! 👋 Soy Kairos, tu asistente de salud natural. ¿Qué molestia tienes?"
    
    def _respuesta_consulta_medica(self, mensaje: str) -> str:
        """Respuesta a consulta médica"""
        
        # Extraer síntoma del mensaje
        sintoma = self._extraer_sintoma(mensaje)
        
        if not self.consulta_iniciada:
            # Primera vez que menciona síntoma
            self.consulta_iniciada = True
            self.contexto['sintoma_principal'] = sintoma
            
            # Hacer primera pregunta de diagnóstico
            return self._siguiente_pregunta_diagnostico()
        else:
            # Ya estamos en consulta, guardar respuesta
            self.contexto['respuestas_usuario'].append(mensaje)
            self.preguntas_realizadas += 1
            
            # Verificar si ya tenemos suficiente información
            if self.preguntas_realizadas >= self.max_preguntas or self._tiene_info_suficiente():
                self.diagnostico_completo = True
                return "Perfecto, ya tengo toda la información necesaria. Dame un momento para analizar tu caso... 🔍"
            else:
                # Continuar con preguntas
                return self._siguiente_pregunta_diagnostico()
    
    def _respuesta_pregunta_producto(self, mensaje: str) -> str:
        """Respuesta sobre productos"""
        
        # Detectar si pregunta por moringa o ganoderma
        mensaje_lower = mensaje.lower()
        
        if 'moringa' in mensaje_lower:
            producto = self.productos.obtener_por_id(1)  # Moringa
            if producto:
                return f"""
🌿 **{producto['nombre']}**

**¿Qué es?**
{producto['descripcion_corta']}

**Para qué sirve:**
{producto['para_que_sirve']}

**Beneficios principales:**
{producto['beneficios']}

**Precio:** S/. {producto['precio']:.2f}

¿Tienes alguna otra pregunta sobre la moringa?
"""
        
        elif 'ganoderma' in mensaje_lower or 'reishi' in mensaje_lower:
            producto = self.productos.obtener_por_id(2)  # Ganoderma
            if producto:
                return f"""
🍄 **{producto['nombre']}**

**¿Qué es?**
{producto['descripcion_corta']}

**Para qué sirve:**
{producto['para_que_sirve']}

**Beneficios principales:**
{producto['beneficios']}

**Precio:** S/. {producto['precio']:.2f}

¿Tienes alguna otra pregunta sobre el ganoderma?
"""
        
        # Respuesta genérica
        productos = self.productos.obtener_todos()
        lista = "\n".join([f"• {p['nombre']} - S/. {p['precio']:.2f}" for p in productos])
        
        return f"""
💊 **Nuestros Productos Naturales:**

{lista}

¿Sobre cuál te gustaría saber más?
"""
    
    def _respuesta_pregunta_uso(self, mensaje: str) -> str:
        """Respuesta sobre modo de uso"""
        
        return """
📋 **Modo de Uso General:**

Para darte la información exacta de cómo tomar el producto, primero necesito saber:

1. ¿Qué producto específico te interesa? (Moringa, Ganoderma, Aceite)
2. ¿Para qué molestia lo necesitas?

Así puedo darte las instrucciones precisas y personalizadas. 😊
"""
    
    def _respuesta_pregunta_precio(self, mensaje: str) -> str:
        """Respuesta sobre precios"""
        
        productos = self.productos.obtener_todos()
        
        respuesta = "💰 **Nuestros Precios:**\n\n"
        
        for producto in productos:
            respuesta += f"• {producto['nombre']}\n"
            respuesta += f"  **S/. {producto['precio']:.2f}**\n"
            respuesta += f"  ({producto['presentacion']})\n\n"
        
        respuesta += "\n📦 **Nota:** El precio incluye el tratamiento completo recomendado.\n"
        respuesta += "¿Te gustaría saber qué producto se ajusta mejor a tu caso?"
        
        return respuesta
    
    def _respuesta_despedida(self) -> str:
        """Respuesta a despedida"""
        
        return """
¡De nada! 😊 Fue un gusto ayudarte.

Recuerda:
✅ Sigue las indicaciones de la receta
✅ Mantén hábitos saludables
✅ Si tienes dudas, vuelve cuando quieras

¡Que te mejores pronto! 💚

*Puedes encontrar los productos en nuestra botica.*
"""
    
    def _respuesta_desconocida(self, mensaje: str) -> str:
        """Respuesta cuando no se entiende"""
        
        return """
Disculpa, no entendí bien tu pregunta. 🤔

Puedo ayudarte con:
- 🏥 Consultas médicas sobre tus síntomas
- 💊 Información sobre productos naturales
- 💰 Precios de productos
- 📋 Cómo usar los productos

¿Sobre qué te gustaría que hablemos?
"""
    
    def _siguiente_pregunta_diagnostico(self) -> str:
        """
        Generar siguiente pregunta para diagnóstico
        Modo express: máximo 8 preguntas clave
        """
        
        preguntas_realizadas = len(self.contexto['respuestas_usuario'])
        
        # Preguntas clave en orden de prioridad
        if preguntas_realizadas == 0:
            return f"Entiendo que tienes {self.contexto['sintoma_principal']}. ¿Dónde exactamente sientes esta molestia?"
        
        elif preguntas_realizadas == 1:
            return "¿Desde hace cuánto tiempo tienes este problema? (días, semanas, meses)"
        
        elif preguntas_realizadas == 2:
            return "En una escala del 1 al 10, ¿qué tan fuerte es la molestia? (1=leve, 10=insoportable)"
        
        elif preguntas_realizadas == 3:
            return "¿En qué momento del día es peor? (mañana, tarde, noche, todo el día)"
        
        elif preguntas_realizadas == 4:
            return "¿Algo hace que mejore? (descanso, comida, medicamento)"
        
        elif preguntas_realizadas == 5:
            return "¿Algo hace que empeore? (estrés, ciertos alimentos, actividades)"
        
        elif preguntas_realizadas == 6:
            return "¿Tomas algún medicamento actualmente?"
        
        else:
            return "¿Tienes alguna alergia a alimentos o medicamentos?"
    
    def _extraer_sintoma(self, mensaje: str) -> str:
        """
        Extraer síntoma principal del mensaje
        """
        mensaje_lower = mensaje.lower()
        
        # Diccionario de síntomas comunes
        sintomas_conocidos = {
            'cabeza': 'dolor de cabeza',
            'cefalea': 'dolor de cabeza',
            'migraña': 'migraña',
            'estómago': 'dolor de estómago',
            'barriga': 'dolor de estómago',
            'gastritis': 'gastritis',
            'cansancio': 'fatiga crónica',
            'fatiga': 'fatiga crónica',
            'agotado': 'fatiga crónica',
            'estrés': 'estrés',
            'ansiedad': 'ansiedad',
            'insomnio': 'insomnio',
            'dormir': 'problemas de sueño',
            'quiste': 'quistes ováricos',
            'menstruación': 'irregularidad menstrual',
            'regla': 'irregularidad menstrual'
        }
        
        # Buscar síntoma conocido
        for palabra_clave, sintoma in sintomas_conocidos.items():
            if palabra_clave in mensaje_lower:
                return sintoma
        
        # Si no encuentra, usar el mensaje completo
        return mensaje.strip()
    
    def _tiene_info_suficiente(self) -> bool:
        """
        Verificar si tenemos suficiente información para diagnóstico
        """
        # Criterios mínimos
        tiene_sintoma = self.contexto['sintoma_principal'] is not None
        tiene_respuestas = len(self.contexto['respuestas_usuario']) >= 5
        
        return tiene_sintoma and tiene_respuestas
    
    def obtener_resumen_consulta(self) -> Dict:
        """
        Obtener resumen de la consulta
        """
        return {
            'sintoma_principal': self.contexto['sintoma_principal'],
            'sintomas_adicionales': self.contexto['sintomas_adicionales'],
            'respuestas': self.contexto['respuestas_usuario'],
            'preguntas': self.contexto['preguntas_realizadas'],
            'total_interacciones': self.preguntas_realizadas,
            'diagnostico_completo': self.diagnostico_completo
        }
    
    def reiniciar_conversacion(self):
        """Reiniciar para nueva consulta"""
        self.contexto = {
            'sintoma_principal': None,
            'sintomas_adicionales': [],
            'intensidad': None,
            'duracion': None,
            'frecuencia': None,
            'momento_dia': None,
            'factores_mejoran': [],
            'factores_empeoran': [],
            'medicamentos_actuales': [],
            'alergias': [],
            'preguntas_realizadas': [],
            'respuestas_usuario': []
        }
        
        self.preguntas_realizadas = 0
        self.consulta_iniciada = False
        self.diagnostico_completo = False
        
        print("🔄 Conversación reiniciada")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*70)
    print(" "*20 + "🧪 TEST MEDICAL ASSISTANT")
    print("="*70)
    print()
    
    # Crear asistente
    asistente = MedicalAssistant()
    
    # Simular conversación
    mensajes_prueba = [
        ("Hola", "saludo"),
        ("Me duele mucho la cabeza", "consulta"),
        ("En la frente y las sienes", "respuesta"),
        ("Como una semana", "respuesta"),
        ("Un 7 de 10", "respuesta"),
        ("Por las mañanas es peor", "respuesta"),
        ("Mejora cuando descanso", "respuesta"),
        ("Empeora con el estrés", "respuesta"),
        ("No tomo medicamentos", "respuesta"),
        ("No tengo alergias", "respuesta")
    ]
    
    usuario_info = {
        'nombre': 'María López',
        'edad': 32
    }
    
    print("👤 Usuario: María López\n")
    print("━"*70)
    print("CONVERSACIÓN SIMULADA")
    print("━"*70)
    print()
    
    for i, (mensaje, tipo) in enumerate(mensajes_prueba, 1):
        print(f"👤 Usuario: {mensaje}")
        
        resultado = asistente.procesar_mensaje(mensaje, usuario_info)
        
        print(f"🤖 Kairos: {resultado['respuesta']}\n")
        
        if resultado['diagnostico_listo']:
            print("✅ Diagnóstico listo para generar\n")
            break
    
    # Resumen
    print("━"*70)
    print("RESUMEN DE CONSULTA")
    print("━"*70)
    resumen = asistente.obtener_resumen_consulta()
    print(f"Síntoma principal: {resumen['sintoma_principal']}")
    print(f"Total preguntas: {len(resumen['preguntas'])}")
    print(f"Total respuestas: {len(resumen['respuestas'])}")
    print(f"Diagnóstico completo: {resumen['diagnostico_completo']}")
    
    print("\n" + "="*70)