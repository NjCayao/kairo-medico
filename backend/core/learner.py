"""
Sistema de Aprendizaje Continuo de Kairos
Aprende automáticamente de cada consulta y mejora con el tiempo
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import pandas as pd
from collections import Counter
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.database_manager import DatabaseManager
from backend.core.classifier import IntentClassifier

class TipoAprendizaje:
    """Tipos de aprendizaje del sistema"""
    PATRON_NUEVO = 'patron_nuevo'
    MEJORA_CONFIANZA = 'mejora_confianza'
    REDUCCION_CONFIANZA = 'reduccion_confianza'
    NUEVA_INTENCION = 'nueva_intencion'
    OPTIMIZACION_PROMPT = 'optimizacion_prompt'
    CORRECION_ERROR = 'correccion_error'

class KairosLearner:
    """
    Sistema completo de aprendizaje automático
    
    Funcionalidades:
    1. Detecta patrones repetitivos
    2. Identifica nuevas intenciones
    3. Re-entrena clasificador ML
    4. Ajusta confianzas
    5. Optimiza prompts de GPT
    6. Aprende de errores
    """
    
    def __init__(self, auto_entrenamiento: bool = True):
        """
        Inicializar sistema de aprendizaje
        
        Args:
            auto_entrenamiento: Si debe re-entrenar automáticamente
        """
        self.db = DatabaseManager()
        self.classifier = IntentClassifier()
        self.auto_entrenamiento = auto_entrenamiento
        
        # Umbrales de aprendizaje
        self.umbral_patron_repetitivo = 5  # Veces que se repite para aprender
        self.umbral_confianza_baja = 0.6   # Confianza baja para revisar
        self.umbral_nueva_intencion = 10    # Casos desconocidos para nueva intención
        self.dias_analisis = 7              # Días de datos para analizar
        
        # Estadísticas
        self.aprendizajes_realizados = 0
        self.reentrenamientos = 0
        self.patrones_nuevos = 0
        
        print("="*70)
        print("🧠 KAIROS LEARNER - SISTEMA DE APRENDIZAJE CONTINUO")
        print("="*70)
        print(f"   Auto-entrenamiento: {'✅ ACTIVO' if auto_entrenamiento else '❌ MANUAL'}")
        print(f"   Umbral patrones: {self.umbral_patron_repetitivo} repeticiones")
        print(f"   Umbral confianza: {self.umbral_confianza_baja}")
        print(f"   Días análisis: {self.dias_analisis}")
        print("="*70 + "\n")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ANÁLISIS DE CONVERSACIONES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def analizar_conversaciones_recientes(self, dias: int = None) -> Dict:
        """
        Analizar conversaciones recientes para identificar patrones
        
        Args:
            dias: Días hacia atrás (default: self.dias_analisis)
            
        Returns:
            Dict con análisis completo
        """
        dias = dias or self.dias_analisis
        
        print(f"\n{'='*70}")
        print(f"📊 ANALIZANDO CONVERSACIONES DE ÚLTIMOS {dias} DÍAS")
        print(f"{'='*70}\n")
        
        # Obtener conversaciones recientes
        fecha_inicio = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        
        query = """
        SELECT * FROM conversaciones 
        WHERE fecha >= %s
        ORDER BY fecha DESC
        """
        
        conversaciones = self.db.ejecutar_query(query, (fecha_inicio,))
        
        if not conversaciones:
            print("⚠️ No hay conversaciones para analizar\n")
            # RETORNAR ESTRUCTURA COMPLETA VACÍA
            return {
                'total_conversaciones': 0,
                'periodo': f"{dias} días",
                'patrones_detectados': [],
                'intenciones_bajas': [],
                'mensajes_desconocidos': [],
                'intenciones_frecuentes': {
                    'total_intenciones': 0,
                    'distribucion': {},
                    'mas_comun': None,
                    'menos_comun': None
                },
                'errores_clasificacion': []
            }
        
        print(f"✅ {len(conversaciones)} conversaciones encontradas\n")
        
        # Análisis
        analisis = {
            'total_conversaciones': len(conversaciones),
            'periodo': f"{dias} días",
            'patrones_detectados': self._detectar_patrones(conversaciones),
            'intenciones_bajas': self._detectar_confianza_baja(conversaciones),
            'mensajes_desconocidos': self._detectar_mensajes_desconocidos(conversaciones),
            'intenciones_frecuentes': self._analizar_frecuencia_intenciones(conversaciones),
            'errores_clasificacion': self._detectar_errores_clasificacion(conversaciones)
        }
        
        # Mostrar resumen
        self._mostrar_resumen_analisis(analisis)
        
        return analisis
    
    def _detectar_patrones(self, conversaciones: List[Dict]) -> List[Dict]:
        """
        Detectar patrones repetitivos en mensajes
        
        Returns:
            Lista de patrones encontrados
        """
        print("🔍 Detectando patrones repetitivos...")
        
        # Agrupar mensajes similares
        mensajes_normalizados = {}
        
        for conv in conversaciones:
            mensaje = conv['mensaje_usuario'].lower().strip()
            mensaje_normalizado = self._normalizar_mensaje(mensaje)
            
            if mensaje_normalizado not in mensajes_normalizados:
                mensajes_normalizados[mensaje_normalizado] = {
                    'ejemplos': [],
                    'intenciones': [],
                    'confianzas': []
                }
            
            mensajes_normalizados[mensaje_normalizado]['ejemplos'].append(mensaje)
            mensajes_normalizados[mensaje_normalizado]['intenciones'].append(
                conv['intencion_detectada']
            )
            mensajes_normalizados[mensaje_normalizado]['confianzas'].append(
                float(conv['confianza_intencion'])
            )
        
        # Filtrar patrones repetitivos
        patrones = []
        
        for msg_norm, datos in mensajes_normalizados.items():
            frecuencia = len(datos['ejemplos'])
            
            if frecuencia >= self.umbral_patron_repetitivo:
                # Patrón repetitivo encontrado
                intencion_comun = Counter(datos['intenciones']).most_common(1)[0][0]
                confianza_promedio = sum(datos['confianzas']) / len(datos['confianzas'])
                
                patron = {
                    'patron': msg_norm,
                    'frecuencia': frecuencia,
                    'ejemplos': datos['ejemplos'][:3],  # Primeros 3
                    'intencion_comun': intencion_comun,
                    'confianza_promedio': confianza_promedio,
                    'variaciones': len(set(datos['ejemplos']))
                }
                
                patrones.append(patron)
        
        print(f"   ✅ {len(patrones)} patrones repetitivos encontrados\n")
        
        return sorted(patrones, key=lambda x: x['frecuencia'], reverse=True)
    
    def _detectar_confianza_baja(self, conversaciones: List[Dict]) -> List[Dict]:
        """
        Detectar mensajes con confianza baja
        
        Returns:
            Lista de mensajes problemáticos
        """
        print("🔍 Detectando mensajes con baja confianza...")
        
        bajas = []
        
        for conv in conversaciones:
            confianza = float(conv['confianza_intencion'])
            
            if confianza < self.umbral_confianza_baja:
                bajas.append({
                    'mensaje': conv['mensaje_usuario'],
                    'intencion': conv['intencion_detectada'],
                    'confianza': confianza,
                    'fecha': conv['fecha']
                })
        
        print(f"   ⚠️ {len(bajas)} mensajes con confianza < {self.umbral_confianza_baja}\n")
        
        return sorted(bajas, key=lambda x: x['confianza'])
    
    def _detectar_mensajes_desconocidos(self, conversaciones: List[Dict]) -> List[Dict]:
        """
        Detectar mensajes clasificados como 'desconocida'
        
        Returns:
            Lista de mensajes desconocidos
        """
        print("🔍 Detectando mensajes desconocidos...")
        
        desconocidos = []
        
        for conv in conversaciones:
            if conv['intencion_detectada'] == 'desconocida':
                desconocidos.append({
                    'mensaje': conv['mensaje_usuario'],
                    'confianza': float(conv['confianza_intencion']),
                    'fecha': conv['fecha']
                })
        
        print(f"   ❓ {len(desconocidos)} mensajes desconocidos\n")
        
        return desconocidos
    
    def _analizar_frecuencia_intenciones(self, conversaciones: List[Dict]) -> Dict:
        """
        Analizar frecuencia de cada intención
        
        Returns:
            Dict con estadísticas de intenciones
        """
        print("📊 Analizando frecuencia de intenciones...")
        
        intenciones = [conv['intencion_detectada'] for conv in conversaciones]
        frecuencias = Counter(intenciones)
        
        stats = {
            'total_intenciones': len(frecuencias),
            'distribucion': dict(frecuencias.most_common()),
            'mas_comun': frecuencias.most_common(1)[0] if frecuencias else None,
            'menos_comun': frecuencias.most_common()[-1] if frecuencias else None
        }
        
        print(f"   ✅ {len(frecuencias)} intenciones diferentes detectadas\n")
        
        return stats
    
    def _detectar_errores_clasificacion(self, conversaciones: List[Dict]) -> List[Dict]:
        """
        Detectar posibles errores de clasificación
        Basado en respuestas inconsistentes
        
        Returns:
            Lista de posibles errores
        """
        print("🔍 Detectando posibles errores de clasificación...")
        
        # Por ahora, consideramos errores los casos con confianza muy baja
        # En el futuro, podríamos usar feedback del usuario
        
        errores = []
        
        for conv in conversaciones:
            confianza = float(conv['confianza_intencion'])
            
            # Muy baja confianza = posible error
            if confianza < 0.4:
                errores.append({
                    'mensaje': conv['mensaje_usuario'],
                    'intencion': conv['intencion_detectada'],
                    'confianza': confianza,
                    'fecha': conv['fecha']
                })
        
        print(f"   ⚠️ {len(errores)} posibles errores detectados\n")
        
        return errores
    
    def _normalizar_mensaje(self, mensaje: str) -> str:
        """
        Normalizar mensaje para detectar similitudes
        
        Args:
            mensaje: Mensaje original
            
        Returns:
            Mensaje normalizado
        """
        # Convertir a minúsculas
        msg = mensaje.lower()
        
        # Eliminar puntuación
        msg = re.sub(r'[^\w\s]', '', msg)
        
        # Eliminar espacios múltiples
        msg = ' '.join(msg.split())
        
        # Eliminar palabras muy comunes (stopwords básicos)
        stopwords = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'una', 'por', 'para']
        palabras = [p for p in msg.split() if p not in stopwords]
        
        return ' '.join(palabras)
    
    def _mostrar_resumen_analisis(self, analisis: Dict):
        """Mostrar resumen del análisis"""
        print(f"\n{'='*70}")
        print("📋 RESUMEN DEL ANÁLISIS")
        print(f"{'='*70}\n")
        
        print(f"Total conversaciones: {analisis['total_conversaciones']}")
        print(f"Periodo: {analisis['periodo']}\n")
        
        print(f"🔄 Patrones repetitivos: {len(analisis['patrones_detectados'])}")
        if analisis['patrones_detectados']:
            top3 = analisis['patrones_detectados'][:3]
            for i, patron in enumerate(top3, 1):
                print(f"   {i}. '{patron['patron'][:40]}...' ({patron['frecuencia']} veces)")
        
        print(f"\n⚠️ Mensajes baja confianza: {len(analisis['intenciones_bajas'])}")
        print(f"❓ Mensajes desconocidos: {len(analisis['mensajes_desconocidos'])}")
        print(f"❌ Posibles errores: {len(analisis['errores_clasificacion'])}")
        
        if analisis['intenciones_frecuentes']['mas_comun']:
            intencion, count = analisis['intenciones_frecuentes']['mas_comun']
            print(f"\n🏆 Intención más común: {intencion} ({count} veces)")
        
        print(f"\n{'='*70}\n")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # APRENDIZAJE AUTOMÁTICO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def aprender_de_patrones(self, patrones: List[Dict]) -> Dict:
        """
        Aprender de patrones detectados
        Guarda en BD para futuro re-entrenamiento
        
        Args:
            patrones: Lista de patrones detectados
            
        Returns:
            Dict con resultado del aprendizaje
        """
        print(f"\n{'='*70}")
        print("🎓 APRENDIENDO DE PATRONES DETECTADOS")
        print(f"{'='*70}\n")
        
        aprendidos = 0
        
        for patron in patrones:
            # Verificar si ya existe
            query = """
            SELECT id FROM patrones_aprendidos 
            WHERE patron = %s AND intencion_detectada = %s
            """
            
            existe = self.db.ejecutar_query(
                query, 
                (patron['patron'], patron['intencion_comun'])
            )
            
            if existe:
                # Actualizar frecuencia
                query = """
                UPDATE patrones_aprendidos 
                SET veces_visto = veces_visto + %s,
                    confianza_promedio = %s,
                    ultima_vez_visto = NOW()
                WHERE id = %s
                """
                
                self.db.ejecutar_comando(
                    query,
                    (patron['frecuencia'], patron['confianza_promedio'], existe[0]['id'])
                )
                
                print(f"   🔄 Actualizado: '{patron['patron'][:40]}...'")
                
            else:
                # Guardar nuevo patrón
                query = """
                INSERT INTO patrones_aprendidos (
                    patron, ejemplo_original, intencion_detectada,
                    confianza_promedio, veces_visto, variaciones,
                    aprendido_automaticamente, origen_aprendizaje
                ) VALUES (%s, %s, %s, %s, %s, %s, TRUE, 'analisis_conversaciones')
                """
                
                self.db.ejecutar_comando(
                    query,
                    (
                        patron['patron'],
                        patron['ejemplos'][0] if patron['ejemplos'] else '',
                        patron['intencion_comun'],
                        patron['confianza_promedio'],
                        patron['frecuencia'],
                        patron['variaciones']
                    )
                )
                
                aprendidos += 1
                self.patrones_nuevos += 1
                
                print(f"   ✅ Nuevo patrón: '{patron['patron'][:40]}...'")
        
        print(f"\n✅ {aprendidos} patrones nuevos aprendidos")
        print(f"   Total acumulado: {self.patrones_nuevos}\n")
        
        self.aprendizajes_realizados += aprendidos
        
        # Si hay suficientes patrones nuevos, sugerir re-entrenamiento
        if aprendidos >= 10 and self.auto_entrenamiento:
            print("💡 Suficientes patrones nuevos. Iniciando re-entrenamiento...\n")
            return self.reentrenar_clasificador()
        
        return {
            'aprendidos': aprendidos,
            'total_patrones': self.patrones_nuevos,
            'reentrenamiento_sugerido': aprendidos >= 10
        }
    
    def reentrenar_clasificador(self) -> Dict:
        """
        Re-entrenar clasificador ML con datos actualizados
        
        Returns:
            Dict con resultado del re-entrenamiento
        """
        print(f"\n{'='*70}")
        print("🔄 RE-ENTRENANDO CLASIFICADOR ML")
        print(f"{'='*70}\n")
        
        try:
            # Obtener todos los patrones aprendidos
            query = """
            SELECT patron, intencion_detectada, veces_visto
            FROM patrones_aprendidos
            WHERE activo = TRUE
            ORDER BY veces_visto DESC
            """
            
            patrones = self.db.ejecutar_query(query)
            
            if not patrones or len(patrones) < 20:
                print("⚠️ Muy pocos datos para re-entrenar (mínimo 20)\n")
                return {'exito': False, 'razon': 'datos_insuficientes'}
            
            print(f"📊 {len(patrones)} patrones para entrenamiento\n")
            
            # Preparar datos
            textos = []
            intenciones = []
            
            for patron in patrones:
                # Repetir según frecuencia (ponderación)
                repeticiones = min(patron['veces_visto'], 5)  # Max 5 veces
                
                for _ in range(repeticiones):
                    textos.append(patron['patron'])
                    intenciones.append(patron['intencion_detectada'])
            
            print(f"📝 Total ejemplos (ponderados): {len(textos)}\n")
            
            # Re-entrenar
            print("🧠 Entrenando modelo...\n")
            metricas = self.classifier.entrenar(textos, intenciones)
            
            self.reentrenamientos += 1
            
            # Guardar evento de re-entrenamiento
            self._registrar_reentrenamiento(metricas, len(patrones))
            
            print(f"\n{'='*70}")
            print("✅ RE-ENTRENAMIENTO COMPLETADO")
            print(f"{'='*70}")
            print(f"   Precisión: {metricas['precision']:.1%}")
            print(f"   Ejemplos: {metricas['num_ejemplos']}")
            print(f"   Intenciones: {metricas['num_intenciones']}")
            print(f"   Vocabulario: {metricas['vocabulario']} palabras")
            print(f"{'='*70}\n")
            
            return {
                'exito': True,
                'metricas': metricas,
                'reentrenamientos_totales': self.reentrenamientos
            }
            
        except Exception as e:
            print(f"❌ Error en re-entrenamiento: {e}\n")
            return {'exito': False, 'error': str(e)}
    
    def _registrar_reentrenamiento(self, metricas: Dict, patrones_usados: int):
        """Registrar evento de re-entrenamiento"""
        query = """
        INSERT INTO log_reentrenamientos (
            fecha_reentrenamiento, patrones_usados, 
            precision_obtenida, num_intenciones,
            num_ejemplos, vocabulario_size
        ) VALUES (NOW(), %s, %s, %s, %s, %s)
        """
        
        self.db.ejecutar_comando(
            query,
            (
                patrones_usados,
                metricas['precision'],
                metricas['num_intenciones'],
                metricas['num_ejemplos'],
                metricas['vocabulario']
            )
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # APRENDIZAJE DE CONOCIMIENTO MÉDICO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def analizar_conocimientos_gpt(self, dias: int = 7) -> Dict:
        """
        Analizar qué ha enseñado GPT recientemente
        
        Args:
            dias: Días hacia atrás
            
        Returns:
            Dict con análisis de conocimientos
        """
        print(f"\n{'='*70}")
        print(f"🤖 ANALIZANDO CONOCIMIENTOS DE GPT ({dias} días)")
        print(f"{'='*70}\n")
        
        fecha_inicio = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        
        # Conocimientos guardados
        query = """
        SELECT * FROM conocimientos_completos
        WHERE fecha_aprendido >= %s
        ORDER BY veces_usado DESC
        """
        
        conocimientos = self.db.ejecutar_query(query, (fecha_inicio,))
        
        if not conocimientos:
            print("⚠️ No hay conocimientos nuevos de GPT\n")
            return {'total': 0}
        
        print(f"✅ {len(conocimientos)} conocimientos encontrados\n")
        
        # Análisis
        analisis = {
            'total_conocimientos': len(conocimientos),
            'por_origen': self._contar_por_origen(conocimientos),
            'mas_usados': self._obtener_mas_usados(conocimientos, 5),
            'confianza_promedio': self._calcular_confianza_promedio(conocimientos),
            'condiciones_nuevas': self._identificar_condiciones_nuevas(conocimientos)
        }
        
        # Mostrar resumen
        print("📊 RESUMEN:")
        print(f"   Total: {analisis['total_conocimientos']}")
        print(f"   De GPT: {analisis['por_origen'].get('gpt', 0)}")
        print(f"   Confianza promedio: {analisis['confianza_promedio']:.1%}")
        
        if analisis['mas_usados']:
            print(f"\n🏆 Top 5 más usados:")
            for i, conocimiento in enumerate(analisis['mas_usados'], 1):
                print(f"   {i}. {conocimiento['condicion']} ({conocimiento['veces_usado']} veces)")
        
        print()
        
        return analisis
    
    def _contar_por_origen(self, conocimientos: List[Dict]) -> Dict:
        """Contar conocimientos por origen"""
        origenes = [k['origen'] for k in conocimientos]
        return dict(Counter(origenes))
    
    def _obtener_mas_usados(self, conocimientos: List[Dict], limite: int) -> List[Dict]:
        """Obtener conocimientos más usados"""
        return sorted(
            conocimientos, 
            key=lambda x: x['veces_usado'], 
            reverse=True
        )[:limite]
    
    def _calcular_confianza_promedio(self, conocimientos: List[Dict]) -> float:
        """Calcular confianza promedio"""
        if not conocimientos:
            return 0.0
        
        confianzas = [float(k['confianza']) for k in conocimientos]
        return sum(confianzas) / len(confianzas)
    
    def _identificar_condiciones_nuevas(self, conocimientos: List[Dict]) -> List[str]:
        """Identificar condiciones nuevas aprendidas"""
        return [k['condicion'] for k in conocimientos if k['veces_usado'] == 1]
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # OPTIMIZACIÓN DE PROMPTS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def sugerir_mejoras_prompts(self) -> Dict:
        """
        Analizar consultas a GPT y sugerir mejoras en prompts
        
        Returns:
            Dict con sugerencias
        """
        print(f"\n{'='*70}")
        print("💡 ANALIZANDO PROMPTS A GPT")
        print(f"{'='*70}\n")
        
        # Obtener consultas recientes a IA
        query = """
        SELECT * FROM log_consultas_ia
        WHERE fecha_consulta >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY fecha_consulta DESC
        """
        
        consultas = self.db.ejecutar_query(query)
        
        if not consultas:
            print("⚠️ No hay consultas a IA para analizar\n")
            return {'total': 0}
        
        print(f"✅ {len(consultas)} consultas analizadas\n")
        
        # Análisis
        sugerencias = {
            'total_consultas': len(consultas),
            'exitosas': sum(1 for c in consultas if c['exitosa']),
            'fallidas': sum(1 for c in consultas if not c['exitosa']),
            'tiempo_promedio': self._calcular_tiempo_promedio(consultas),
            'tokens_promedio': self._calcular_tokens_promedio(consultas),
            'costo_total': self._calcular_costo_total(consultas),
            'mejoras_sugeridas': []
        }
        
        # Sugerencias específicas
        if sugerencias['tiempo_promedio'] > 5000:  # >5 segundos
            sugerencias['mejoras_sugeridas'].append({
                'tipo': 'rendimiento',
                'descripcion': 'Tiempo de respuesta alto. Considerar reducir max_tokens.',
                'prioridad': 'alta'
            })
        
        if sugerencias['tokens_promedio'] > 800:
            sugerencias['mejoras_sugeridas'].append({
                'tipo': 'costo',
                'descripcion': 'Alto uso de tokens. Optimizar prompt para ser más conciso.',
                'prioridad': 'media'
            })
        
        if sugerencias['fallidas'] > sugerencias['total_consultas'] * 0.1:  # >10% fallos
            sugerencias['mejoras_sugeridas'].append({
                'tipo': 'confiabilidad',
                'descripcion': 'Tasa de error alta. Revisar manejo de errores.',
                'prioridad': 'alta'
            })
        
        # Mostrar
        print("📊 ESTADÍSTICAS:")
        print(f"   Exitosas: {sugerencias['exitosas']}/{sugerencias['total_consultas']}")
        print(f"   Tiempo promedio: {sugerencias['tiempo_promedio']:.0f}ms")
        print(f"   Tokens promedio: {sugerencias['tokens_promedio']:.0f}")
        print(f"   Costo total: S/. {sugerencias['costo_total']:.4f}")
        
        if sugerencias['mejoras_sugeridas']:
            print(f"\n💡 SUGERENCIAS DE MEJORA:")
            for i, mejora in enumerate(sugerencias['mejoras_sugeridas'], 1):
                print(f"   {i}. [{mejora['prioridad'].upper()}] {mejora['descripcion']}")
        
        print()
        
        return sugerencias
    
    def _calcular_tiempo_promedio(self, consultas: List[Dict]) -> float:
        """Calcular tiempo promedio de respuesta"""
        if not consultas:
            return 0.0
        
        tiempos = [c['tiempo_respuesta_ms'] for c in consultas if c['tiempo_respuesta_ms']]
        return sum(tiempos) / len(tiempos) if tiempos else 0.0
    
    def _calcular_tokens_promedio(self, consultas: List[Dict]) -> float:
        """Calcular tokens promedio"""
        if not consultas:
            return 0.0
        
        tokens = [c['tokens_usados'] for c in consultas if c['tokens_usados']]
        return sum(tokens) / len(tokens) if tokens else 0.0
    
    def _calcular_costo_total(self, consultas: List[Dict]) -> float:
        """Calcular costo total"""
        return sum(c['costo_estimado'] for c in consultas if c['costo_estimado'])
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PROCESO COMPLETO DE APRENDIZAJE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def ejecutar_ciclo_aprendizaje(self, dias: int = 7) -> Dict:
        """
        Ejecutar ciclo completo de aprendizaje
        
        Args:
            dias: Días de datos para analizar
            
        Returns:
            Dict con resultado completo
        """
        print("\n" + "="*70)
        print("🎓 INICIANDO CICLO COMPLETO DE APRENDIZAJE")
        print("="*70)
        
        inicio = datetime.now()
        
        # 1. Analizar conversaciones
        analisis_conv = self.analizar_conversaciones_recientes(dias)
        
        # 2. Aprender de patrones (VERIFICAR QUE EXISTAN)
        resultado_patrones = {'aprendidos': 0, 'reentrenamiento_realizado': False}
        
        if analisis_conv.get('patrones_detectados') and len(analisis_conv['patrones_detectados']) > 0:
            resultado_patrones = self.aprender_de_patrones(
                analisis_conv['patrones_detectados']
            )
        else:
            print("ℹ️ No hay patrones detectados para aprender\n")
        
        # 3. Analizar conocimientos de GPT
        analisis_gpt = self.analizar_conocimientos_gpt(dias)
        
        # 4. Sugerir mejoras de prompts (SOLO SI HAY CONSULTAS)
        sugerencias = {'mejoras_sugeridas': []}
        try:
            sugerencias = self.sugerir_mejoras_prompts()
        except Exception as e:
            print(f"⚠️ No se pudieron analizar prompts: {e}\n")
        
        # Tiempo total
        duracion = (datetime.now() - inicio).total_seconds()
        
        resultado = {
            'duracion_segundos': duracion,
            'conversaciones_analizadas': analisis_conv.get('total_conversaciones', 0),
            'patrones_aprendidos': resultado_patrones.get('aprendidos', 0),
            'conocimientos_gpt': analisis_gpt.get('total_conocimientos', 0),
            'sugerencias_prompts': len(sugerencias.get('mejoras_sugeridas', [])),
            'reentrenamiento_realizado': resultado_patrones.get('reentrenamiento_realizado', False),
            'estadisticas': {
                'aprendizajes_totales': self.aprendizajes_realizados,
                'reentrenamientos_totales': self.reentrenamientos,
                'patrones_nuevos': self.patrones_nuevos
            }
        }
        
        print(f"\n{'='*70}")
        print("✅ CICLO DE APRENDIZAJE COMPLETADO")
        print(f"{'='*70}")
        print(f"   Duración: {duracion:.1f}s")
        print(f"   Conversaciones: {resultado['conversaciones_analizadas']}")
        print(f"   Patrones aprendidos: {resultado['patrones_aprendidos']}")
        print(f"   Conocimientos GPT: {resultado['conocimientos_gpt']}")
        print(f"   Sugerencias: {resultado['sugerencias_prompts']}")
        print(f"{'='*70}\n")
        
        return resultado
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ESTADÍSTICAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def obtener_estadisticas_aprendizaje(self) -> Dict:
        """Obtener estadísticas globales de aprendizaje"""
        
        stats = {
            'aprendizajes_realizados': self.aprendizajes_realizados,
            'reentrenamientos': self.reentrenamientos,
            'patrones_nuevos': self.patrones_nuevos,
            'clasificador': self.classifier.obtener_estadisticas()
        }
        
        # Estadísticas de BD
        query = "SELECT COUNT(*) as total FROM patrones_aprendidos WHERE activo = TRUE"
        resultado = self.db.ejecutar_query(query)
        stats['patrones_bd'] = resultado[0]['total'] if resultado else 0
        
        query = "SELECT COUNT(*) as total FROM conocimientos_completos"
        resultado = self.db.ejecutar_query(query)
        stats['conocimientos_bd'] = resultado[0]['total'] if resultado else 0
        
        return stats


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*20 + "🧪 TEST LEARNER")
    print("="*70 + "\n")
    
    # Crear learner
    learner = KairosLearner(auto_entrenamiento=True)
    
    # Ejecutar ciclo completo
    resultado = learner.ejecutar_ciclo_aprendizaje(dias=7)
    
    # Mostrar estadísticas
    print("\n" + "="*70)
    print("ESTADÍSTICAS FINALES")
    print("="*70)
    
    stats = learner.obtener_estadisticas_aprendizaje()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                print(f"   {k}: {v}")
        else:
            print(f"{key}: {value}")
    
    print("\n" + "="*70)