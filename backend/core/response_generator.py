"""
Response Generator - Generador Inteligente de Respuestas
Sistema de 3 capas: BD → GPT → Fallback
Aprende automáticamente
"""

import sys
import os
from typing import Dict, Optional
import requests
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from backend.core.ia_config_manager import IAConfigManager
from backend.database.db_manager import DatabaseManager

class ResponseGenerator:
    """
    Generador Inteligente de Respuestas
    
    Proceso:
    1. Buscar respuesta aprendida en BD
    2. Si no existe, consultar GPT
    3. Guardar nueva respuesta (aprender)
    4. Si GPT falla, usar fallback
    """
    
    def __init__(self):
        """Inicializar generador"""
        
        self.ia_config = IAConfigManager()
        self.db = DatabaseManager()
        
        # Crear tabla de respuestas aprendidas si no existe
        self._crear_tabla_respuestas()
        
        print("💬 Response Generator inicializado")
    
    def _crear_tabla_respuestas(self):
        """Crear tabla para almacenar respuestas aprendidas"""
        
        query = """
        CREATE TABLE IF NOT EXISTS respuestas_aprendidas (
            id INT PRIMARY KEY AUTO_INCREMENT,
            patron_mensaje VARCHAR(500),
            intencion VARCHAR(50),
            contexto_previo TEXT,
            respuesta_generada TEXT,
            origen ENUM('gpt', 'manual', 'editado') DEFAULT 'gpt',
            veces_usado INT DEFAULT 0,
            calificacion_promedio DECIMAL(3,2) DEFAULT 0,
            fecha_aprendido DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultima_vez_usado DATETIME,
            activo BOOLEAN DEFAULT TRUE,
            INDEX idx_patron (patron_mensaje),
            INDEX idx_intencion (intencion),
            INDEX idx_activo (activo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.db.ejecutar_query(query)
            print("   ✅ Tabla respuestas_aprendidas verificada")
        except Exception as e:
            print(f"   ⚠️ Error creando tabla: {e}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GENERACIÓN PRINCIPAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def generar_respuesta(self, 
                         mensaje: str,
                         intencion: str,
                         contexto: str,
                         system_prompt: str,
                         usar_aprendizaje: bool = True) -> Dict:
        """
        Generar respuesta inteligente
        
        Args:
            mensaje: Mensaje del usuario
            intencion: Intención detectada
            contexto: Contexto de la conversación
            system_prompt: Prompt del sistema para GPT
            usar_aprendizaje: Si debe buscar/guardar en BD
            
        Returns:
            Dict con respuesta, origen, confianza
        """
        
        # CAPA 1: Buscar respuesta aprendida
        if usar_aprendizaje:
            respuesta_aprendida = self._buscar_respuesta_aprendida(
                mensaje, 
                intencion, 
                contexto
            )
            
            if respuesta_aprendida:
                self._marcar_uso(respuesta_aprendida['id'])
                
                return {
                    'respuesta': respuesta_aprendida['respuesta'],
                    'origen': 'bd_aprendida',
                    'confianza': 0.9,
                    'id_respuesta': respuesta_aprendida['id'],
                    'veces_usado': respuesta_aprendida['veces_usado'] + 1
                }
        
        # CAPA 2: Consultar GPT
        if self.ia_config.esta_activo():
            respuesta_gpt = self._generar_con_gpt(
                mensaje,
                contexto,
                system_prompt
            )
            
            if respuesta_gpt:
                # Guardar respuesta para aprender
                if usar_aprendizaje:
                    self._guardar_respuesta_aprendida(
                        mensaje,
                        intencion,
                        contexto,
                        respuesta_gpt
                    )
                
                return {
                    'respuesta': respuesta_gpt,
                    'origen': 'gpt',
                    'confianza': 0.85,
                    'guardado': usar_aprendizaje
                }
        
        # CAPA 3: Fallback genérico
        respuesta_fallback = self._generar_fallback(mensaje, intencion)
        
        return {
            'respuesta': respuesta_fallback,
            'origen': 'fallback',
            'confianza': 0.5
        }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BÚSQUEDA EN BD
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _buscar_respuesta_aprendida(self, 
                                    mensaje: str, 
                                    intencion: str,
                                    contexto: str) -> Optional[Dict]:
        """
        Buscar respuesta similar en BD
        Usa similitud de texto
        """
        
        # Normalizar mensaje para búsqueda
        patron = self._normalizar_patron(mensaje)
        
        query = """
        SELECT id, respuesta_generada, veces_usado, calificacion_promedio
        FROM respuestas_aprendidas
        WHERE activo = TRUE
          AND intencion = %s
          AND (
              patron_mensaje LIKE %s
              OR patron_mensaje = %s
          )
        ORDER BY veces_usado DESC, calificacion_promedio DESC
        LIMIT 1
        """
        
        resultado = self.db.ejecutar_query(
            query,
            (intencion, f"%{patron}%", patron)
        )
        
        if resultado:
            print(f"   ✅ Respuesta aprendida encontrada (usada {resultado[0]['veces_usado']} veces)")
            return {
                'id': resultado[0]['id'],
                'respuesta': resultado[0]['respuesta_generada'],
                'veces_usado': resultado[0]['veces_usado']
            }
        
        return None
    
    def _normalizar_patron(self, mensaje: str) -> str:
        """Normalizar mensaje para búsqueda"""
        
        from unidecode import unidecode
        
        # Minúsculas
        patron = mensaje.lower().strip()
        
        # Quitar acentos
        patron = unidecode(patron)
        
        # Quitar palabras comunes
        palabras_comunes = ['el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'a']
        palabras = patron.split()
        palabras = [p for p in palabras if p not in palabras_comunes]
        
        return ' '.join(palabras)
    
    def _marcar_uso(self, id_respuesta: int):
        """Marcar que una respuesta aprendida fue usada"""
        
        query = """
        UPDATE respuestas_aprendidas
        SET veces_usado = veces_usado + 1,
            ultima_vez_usado = NOW()
        WHERE id = %s
        """
        
        self.db.ejecutar_query(query, (id_respuesta,))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GENERACIÓN CON GPT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _generar_con_gpt(self,
                        mensaje: str,
                        contexto: str,
                        system_prompt: str) -> Optional[str]:
        """Generar respuesta usando GPT"""
        
        try:
            config = self.ia_config.obtener_config()
            
            # Construir prompt completo
            prompt_usuario = f"""CONTEXTO DE LA CONVERSACIÓN:
{contexto}

MENSAJE DEL PACIENTE:
"{mensaje}"

INSTRUCCIONES:
- Responde de forma natural y conversacional
- Máximo 3 líneas
- Usa el nombre del paciente si está disponible
- Sé empático y profesional
- NO uses markdown ni formato especial

RESPUESTA:"""
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['modelo'],
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt_usuario}
                    ],
                    'temperature': 0.8,
                    'max_tokens': 200
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                respuesta = data['choices'][0]['message']['content'].strip()
                
                # Limpiar formato
                respuesta = respuesta.replace('**', '').replace('*', '')
                respuesta = respuesta.replace('#', '').replace('```', '')
                
                # Incrementar contador
                self.ia_config.incrementar_consulta(0.003)
                
                print(f"   ✅ Respuesta GPT generada")
                
                return respuesta
            else:
                print(f"   ❌ Error GPT: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error consultando GPT: {e}")
            return None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GUARDAR RESPUESTA (APRENDIZAJE)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _guardar_respuesta_aprendida(self,
                                     mensaje: str,
                                     intencion: str,
                                     contexto: str,
                                     respuesta: str):
        """Guardar respuesta en BD para aprendizaje futuro"""
        
        patron = self._normalizar_patron(mensaje)
        
        query = """
        INSERT INTO respuestas_aprendidas 
        (patron_mensaje, intencion, contexto_previo, respuesta_generada, origen)
        VALUES (%s, %s, %s, %s, 'gpt')
        """
        
        try:
            self.db.ejecutar_query(
                query,
                (patron, intencion, contexto[:500], respuesta)
            )
            print(f"   💾 Respuesta guardada para aprendizaje")
        except Exception as e:
            print(f"   ⚠️ Error guardando respuesta: {e}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FALLBACK
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _generar_fallback(self, mensaje: str, intencion: str) -> str:
        """Generar respuesta fallback cuando todo falla"""
        
        fallbacks = {
            'saludo': "¡Hola! Soy Kairos. ¿En qué puedo ayudarte?",
            'sintoma': "Entiendo. Cuéntame más sobre eso.",
            'despedida': "¡Cuídate mucho! Hasta pronto.",
            'quien_eres': "Soy Kairos, tu médico de cabecera virtual en el que puedes confiar.",
            'quien_te_creo': "Me creó Nilson Cayao, un joven apasionado por la tecnología.",
            'producto': "Tenemos productos naturales como Moringa y Ganoderma. ¿Sobre cuál quieres saber?",
            'precio': "Los precios varían según el producto. ¿Cuál te interesa?",
        }
        
        return fallbacks.get(intencion, "¿Puedes explicarme un poco más?")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GESTIÓN DE APRENDIZAJE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def calificar_respuesta(self, id_respuesta: int, calificacion: float):
        """
        Calificar una respuesta (1-5 estrellas)
        Actualiza el promedio
        """
        
        query = """
        UPDATE respuestas_aprendidas
        SET calificacion_promedio = (
            (calificacion_promedio * veces_usado + %s) / (veces_usado + 1)
        )
        WHERE id = %s
        """
        
        self.db.ejecutar_query(query, (calificacion, id_respuesta))
        print(f"   ⭐ Respuesta calificada: {calificacion}/5")
    
    def desactivar_respuesta(self, id_respuesta: int):
        """Desactivar una respuesta que no funcionó bien"""
        
        query = "UPDATE respuestas_aprendidas SET activo = FALSE WHERE id = %s"
        self.db.ejecutar_query(query, (id_respuesta,))
        print(f"   🚫 Respuesta {id_respuesta} desactivada")
    
    def obtener_estadisticas(self) -> Dict:
        """Obtener estadísticas del sistema de aprendizaje"""
        
        query = """
        SELECT 
            COUNT(*) as total_respuestas,
            SUM(veces_usado) as total_usos,
            AVG(calificacion_promedio) as calificacion_promedio,
            COUNT(DISTINCT intencion) as intenciones_aprendidas
        FROM respuestas_aprendidas
        WHERE activo = TRUE
        """
        
        resultado = self.db.ejecutar_query(query)
        
        if resultado:
            return {
                'respuestas_aprendidas': resultado[0]['total_respuestas'] or 0,
                'total_usos': resultado[0]['total_usos'] or 0,
                'calificacion_promedio': float(resultado[0]['calificacion_promedio'] or 0),
                'intenciones': resultado[0]['intenciones_aprendidas'] or 0
            }
        
        return {
            'respuestas_aprendidas': 0,
            'total_usos': 0,
            'calificacion_promedio': 0,
            'intenciones': 0
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*70)
    print("🧪 TEST RESPONSE GENERATOR")
    print("="*70)
    
    generator = ResponseGenerator()
    
    # Test generación
    print("\n📝 TEST GENERACIÓN:\n")
    
    resultado = generator.generar_respuesta(
        mensaje="me duele la cabeza",
        intencion="sintoma",
        contexto="Paciente: Juan\nSíntoma principal: dolor de cabeza",
        system_prompt="Eres un médico empático",
        usar_aprendizaje=True
    )
    
    print(f"Respuesta: {resultado['respuesta']}")
    print(f"Origen: {resultado['origen']}")
    print(f"Confianza: {resultado['confianza']:.0%}")
    
    # Estadísticas
    print("\n📊 ESTADÍSTICAS:")
    stats = generator.obtener_estadisticas()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*70)