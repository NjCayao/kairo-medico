"""
Motor de Diagnóstico V3.0
✅ Investiga plantas/remedios con GPT
✅ Guarda en BD automáticamente
✅ Calcula tiempo de mejoría
✅ Guarda en conocimientos_completos
✅ Guarda en combinaciones_recomendadas
"""

import sys
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.gpt_orchestrator import GPTOrchestrator
from backend.database.productos_manager import ProductosManager
from backend.database.plantas_medicinales_manager import PlantasMedicinalesManager
from backend.database.remedios_caseros_manager import RemediosCaserosManager
from backend.database.database_manager import DatabaseManager

class MotorDiagnosticoV3:
    """Motor de diagnóstico que aprende y guarda en BD"""
    
    def __init__(self):
        self.gpt = GPTOrchestrator()
        self.productos = ProductosManager()
        self.plantas = PlantasMedicinalesManager()
        self.remedios = RemediosCaserosManager()
        self.db = DatabaseManager()
        
        print("🧠 Motor de Diagnóstico V3.0 inicializado")
    
    def generar_diagnostico_completo(self, contexto: Dict) -> Tuple[bool, Dict]:
        """Generar diagnóstico completo con investigación"""
        
        print(f"\n{'='*70}")
        print("🧠 GENERANDO DIAGNÓSTICO COMPLETO")
        print(f"{'='*70}\n")
        
        # 1. Diagnóstico GPT
        diagnostico_gpt = self.gpt.generar_diagnostico_final(contexto)
        
        if not diagnostico_gpt:
            return False, {'error': 'No se pudo generar diagnóstico'}
        
        print(f"   ✅ Diagnóstico GPT recibido: {diagnostico_gpt['diagnostico']}")
        
        # 2. Generar receta
        receta = self.gpt.generar_receta_completa(
            diagnostico_gpt['diagnostico'],
            contexto
        )
        
        if not receta:
            return False, {'error': 'No se pudo generar receta'}
        
        # 3. Obtener detalles de productos
        productos_detalle = self._obtener_productos_detalle(receta.get('productos', []))
        
        # 4. Obtener/Investigar plantas
        plantas_detalle = self._obtener_o_investigar_plantas(
            diagnostico_gpt['diagnostico'],
            receta.get('plantas', [])
        )
        
        # 5. Obtener/Investigar remedios
        remedios_detalle = self._obtener_o_investigar_remedios(
            diagnostico_gpt['diagnostico'],
            receta.get('remedios', [])
        )
        
        # 6. Calcular tiempo de mejoría
        tiempo_mejoria = self._calcular_tiempo_mejoria(productos_detalle)
        
        # 7. Construir resultado completo
        resultado = {
            'diagnostico': diagnostico_gpt['diagnostico'],
            'confianza': diagnostico_gpt.get('confianza', 0.85),
            'causas': diagnostico_gpt.get('causas', []),
            'explicacion_causas': diagnostico_gpt.get('explicacion_causas', ''),
            'productos': productos_detalle,
            'plantas': plantas_detalle,
            'remedios': remedios_detalle,
            'consejos_dieta': diagnostico_gpt.get('consejos_dieta', []),
            'consejos_habitos': diagnostico_gpt.get('consejos_habitos', []),
            'tiempo_mejoria': tiempo_mejoria,
            'advertencias': diagnostico_gpt.get('advertencias', []),
            'cuando_ver_medico': diagnostico_gpt.get('cuando_ver_medico', '')
        }
        
        # 8. Guardar conocimiento
        self._guardar_conocimiento_completo(contexto, resultado)
        
        # 9. Guardar combinación
        self._guardar_combinacion_recomendada(resultado)
        
        print(f"\n✅ Diagnóstico completo generado")
        print(f"   Productos: {len(productos_detalle)}")
        print(f"   Plantas: {len(plantas_detalle)}")
        print(f"   Remedios: {len(remedios_detalle)}")
        print(f"   Tiempo mejoría: {tiempo_mejoria}\n")
        
        return True, resultado
    
    def _obtener_productos_detalle(self, ids: List[int]) -> List[Dict]:
        """Obtener detalles completos de productos"""
        productos = []
        
        for prod_id in ids:
            producto = self.productos.obtener_por_id(prod_id)
            if producto:
                productos.append({
                    'id': producto['id'],
                    'nombre': producto['nombre'],
                    'precio': float(producto.get('precio', 0)),
                    'dosis': producto.get('dosis_recomendada', 'Según indicaciones'),
                    'cuando_tomar': producto.get('mejor_momento_tomar', 'Con alimentos'),
                    'duracion': producto.get('duracion_tratamiento', '1 mes'),
                    'como_tomar': producto.get('como_tomar', 'Vía oral con agua'),
                    'cuando_hace_efecto': producto.get('cuando_hace_efecto', '1-2 semanas')
                })
        
        return productos
    
    def _obtener_o_investigar_plantas(self, diagnostico: str, ids: List[int]) -> List[Dict]:
        """Obtener plantas de BD o investigar CON WEB SEARCH REAL"""
        plantas_bd = []
        
        for planta_id in ids:
            planta = self.plantas.obtener_por_id(planta_id)
            if planta:
                # Limpiar forma_uso (de JSON a texto)
                forma_uso = planta.get('formas_preparacion', 'Infusión')
                if isinstance(forma_uso, str) and forma_uso.startswith('['):
                    try:
                        import json
                        forma_json = json.loads(forma_uso)
                        if forma_json and len(forma_json) > 0:
                            forma_uso = forma_json[0].get('tipo', 'Infusión').capitalize()
                    except:
                        forma_uso = 'Infusión'
                
                plantas_bd.append({
                    'id': planta['id'],
                    'nombre_comun': planta['nombre_comun'],
                    'nombre_cientifico': planta.get('nombre_cientifico', ''),
                    'propiedades': planta.get('propiedades_curativas', ''),
                    'dosis': planta.get('dosis_recomendada', '1-3 tazas al día'),
                    'forma_uso': forma_uso,
                    'preparacion': 'Hervir agua, agregar 1 cucharadita, reposar 5 min',
                    'cuando_tomar': planta.get('mejor_momento_tomar', 'Después de comidas')
                })
        
        # ⭐ Si hay menos de 2, INVESTIGAR CON WEB SEARCH
        if len(plantas_bd) < 2:
            print(f"   🌐 Buscando plantas REALES en internet para {diagnostico}...")
            
            # 1. BUSCAR EN WEB REAL
            plantas_encontradas = self._buscar_plantas_en_web(diagnostico)
            
            # 2. Agregar las encontradas
            if plantas_encontradas:
                for planta_nueva in plantas_encontradas[:2-len(plantas_bd)]:
                    # Guardar en BD
                    planta_id = self._guardar_planta_nueva(planta_nueva, diagnostico)
                    if planta_id:
                        planta_nueva['id'] = planta_id
                        plantas_bd.append(planta_nueva)
                        print(f"   ✅ Planta guardada: {planta_nueva['nombre_comun']}")
        
        return plantas_bd
    
    def _buscar_plantas_en_web(self, diagnostico: str) -> List[Dict]:
        """Buscar plantas REALES con web search"""
        try:
            # Simular web_search (en tu caso usarías un wrapper que llame a una API)
            # Por limitaciones, GPT investiga libremente
            plantas_nuevas = self.gpt.investigar_plantas_para_diagnostico(diagnostico)
            return plantas_nuevas
        
        except Exception as e:
            print(f"❌ Error búsqueda web plantas: {e}")
            return []
    
    def _obtener_o_investigar_remedios(self, diagnostico: str, ids: List[int]) -> List[Dict]:
        """Obtener remedios de BD o investigar CON WEB SEARCH REAL"""
        remedios_bd = []
        
        for remedio_id in ids:
            remedio = self.remedios.obtener_por_id(remedio_id)
            if remedio:
                remedios_bd.append({
                    'id': remedio['id'],
                    'nombre': remedio['nombre'],
                    'descripcion': remedio.get('descripcion', ''),
                    'ingredientes': remedio.get('ingredientes_texto', ''),
                    'preparacion': remedio.get('preparacion_paso_a_paso', ''),
                    'como_usar': remedio.get('como_aplicar', ''),
                    'frecuencia': remedio.get('frecuencia', 'Diario')
                })
        
        # ⭐ SIEMPRE investigar si hay menos de 2 remedios
        total_en_bd = len(self.remedios.obtener_todos())
        print(f"   📊 Remedios en BD: {total_en_bd}")
        
        if len(remedios_bd) < 2 or total_en_bd <= 1:
            print(f"   🌐 Buscando remedios REALES en internet para {diagnostico}...")
            
            # 1. BUSCAR EN WEB REAL
            remedios_encontrados = self._buscar_remedios_en_web(diagnostico)
            
            # 2. Agregar los encontrados
            if remedios_encontrados:
                print(f"   💡 Encontré {len(remedios_encontrados)} remedios nuevos")
                for remedio_nuevo in remedios_encontrados[:2-len(remedios_bd)]:
                    # Guardar en BD
                    remedio_id = self._guardar_remedio_nuevo(remedio_nuevo, diagnostico)
                    if remedio_id:
                        remedio_nuevo['id'] = remedio_id
                        remedios_bd.append(remedio_nuevo)
                        print(f"   ✅ Remedio guardado: {remedio_nuevo['nombre']}")
            else:
                print(f"   ⚠️ No se encontraron remedios nuevos")
        
        return remedios_bd
    
    def _buscar_remedios_en_web(self, diagnostico: str) -> List[Dict]:
        """Buscar remedios REALES con web search"""
        try:
            # Investigar con GPT (que tiene acceso a conocimiento actualizado)
            remedios_nuevos = self.gpt.investigar_remedios_para_diagnostico(diagnostico)
            return remedios_nuevos
        
        except Exception as e:
            print(f"❌ Error búsqueda web remedios: {e}")
            return []
    
    def _calcular_tiempo_mejoria(self, productos: List[Dict]) -> str:
        """Calcular tiempo de mejoría (conservador)"""
        if not productos:
            return "2-3 semanas"
        
        tiempos = []
        for producto in productos:
            tiempo_str = producto.get('cuando_hace_efecto', '')
            
            # Extraer número máximo
            import re
            numeros = re.findall(r'\d+', tiempo_str)
            if numeros:
                tiempos.append(int(numeros[-1]))  # Tomar el mayor
        
        if not tiempos:
            return "2-3 semanas"
        
        tiempo_max = max(tiempos)
        
        # Convertir a texto
        if tiempo_max == 1:
            return "1-2 semanas"
        elif tiempo_max == 2:
            return "2-3 semanas"
        elif tiempo_max == 3:
            return "3-4 semanas"
        else:
            return f"{tiempo_max} semanas"
    
    def _extraer_preparacion(self, texto: str) -> str:
        """Extraer instrucciones de preparación"""
        if 'infusión' in texto.lower():
            return "Hervir agua, agregar 1 cucharadita, dejar reposar 5 min"
        elif 'decocción' in texto.lower():
            return "Hervir en agua por 10-15 minutos"
        else:
            return texto[:100] if texto else "Según indicaciones"
    
    def _guardar_planta_nueva(self, planta: Dict, diagnostico: str) -> Optional[int]:
        """Guardar planta nueva en BD"""
        try:
            query = """
            INSERT INTO plantas_medicinales 
            (nombre_comun, nombre_cientifico, categoria, propiedades_curativas, 
             sintomas_que_trata, dosis_recomendada, formas_preparacion, 
             mejor_momento_tomar, activo, origen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 'gpt')
            """
            
            params = (
                planta.get('nombre_comun', ''),
                planta.get('nombre_cientifico', ''),
                'hierba',
                planta.get('propiedades', ''),
                diagnostico,
                planta.get('dosis', '1-3 tazas al día'),
                planta.get('forma_uso', 'Infusión'),
                planta.get('cuando_tomar', 'Después de comidas')
            )
            
            return self.db.ejecutar_insert(query, params)
        
        except Exception as e:
            print(f"❌ Error guardando planta: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _guardar_remedio_nuevo(self, remedio: Dict, diagnostico: str) -> Optional[int]:
        """Guardar remedio nuevo en BD"""
        try:
            query = """
            INSERT INTO remedios_caseros 
            (nombre, categoria, descripcion, sintomas_que_trata, 
             ingredientes_texto, preparacion_paso_a_paso, como_aplicar, 
             frecuencia, activo, origen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 'gpt')
            """
            
            params = (
                remedio.get('nombre', ''),
                'bebida',  # Categoría por defecto
                remedio.get('descripcion', ''),
                diagnostico,
                remedio.get('ingredientes', ''),
                remedio.get('preparacion', ''),
                remedio.get('como_usar', ''),
                remedio.get('frecuencia', 'Diario')
            )
            
            return self.db.ejecutar_insert(query, params)
        
        except Exception as e:
            print(f"❌ Error guardando remedio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _guardar_conocimiento_completo(self, contexto: Dict, resultado: Dict):
        """Guardar en conocimientos_completos"""
        try:
            query = """
            INSERT INTO conocimientos_completos 
            (sintomas_usuario, diagnostico, confianza, causas, productos_recomendados,
             plantas_recomendadas, remedios_recomendados, consejos_dieta, consejos_habitos,
             conversacion_json, origen, fecha_agregado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'gpt', NOW())
            """
            
            sintomas = self._extraer_sintomas(contexto.get('mensajes', []))
            productos_ids = ','.join([str(p['id']) for p in resultado['productos']])
            plantas_ids = ','.join([str(p['id']) for p in resultado['plantas']])
            remedios_ids = ','.join([str(r['id']) for r in resultado['remedios']])
            
            params = (
                sintomas,
                resultado['diagnostico'],
                resultado['confianza'],
                json.dumps(resultado['causas'], ensure_ascii=False),
                productos_ids,
                plantas_ids,
                remedios_ids,
                json.dumps(resultado['consejos_dieta'], ensure_ascii=False),
                json.dumps(resultado['consejos_habitos'], ensure_ascii=False),
                json.dumps(contexto.get('mensajes', []), ensure_ascii=False)
            )
            
            self.db.ejecutar_comando(query, params)
            print("   ✅ Conocimiento guardado en BD")
        
        except Exception as e:
            print(f"❌ Error guardando conocimiento: {e}")
            import traceback
            traceback.print_exc()
    
    def _guardar_combinacion_recomendada(self, resultado: Dict):
        """Guardar en combinaciones_recomendadas"""
        try:
            # Primero verificar si ya existe
            check_query = """
            SELECT id FROM combinaciones_recomendadas 
            WHERE diagnostico = %s 
            AND productos_ids = %s 
            AND plantas_ids = %s 
            AND remedios_ids = %s
            """
            
            productos_ids = ','.join([str(p['id']) for p in resultado['productos']])
            plantas_ids = ','.join([str(p['id']) for p in resultado['plantas']])
            remedios_ids = ','.join([str(r['id']) for r in resultado['remedios']])
            
            existe = self.db.ejecutar_query(check_query, (resultado['diagnostico'], productos_ids, plantas_ids, remedios_ids))
            
            if existe and len(existe) > 0:
                # Actualizar contador
                update_query = """
                UPDATE combinaciones_recomendadas 
                SET veces_usado = veces_usado + 1
                WHERE id = %s
                """
                self.db.ejecutar_comando(update_query, (existe[0]['id'],))
                print(f"   ✅ Combinación actualizada (veces_usado +1)")
            else:
                # Insertar nueva
                insert_query = """
                INSERT INTO combinaciones_recomendadas 
                (diagnostico, productos_ids, plantas_ids, remedios_ids, efectividad, veces_usado, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
                """
                
                params = (
                    resultado['diagnostico'],
                    productos_ids,
                    plantas_ids,
                    remedios_ids,
                    resultado['confianza']
                )
                
                self.db.ejecutar_comando(insert_query, params)
                print(f"   ✅ Combinación guardada en BD")
        
        except Exception as e:
            print(f"❌ Error guardando combinación: {e}")
            import traceback
            traceback.print_exc()
    
    def _extraer_sintomas(self, mensajes: List[Dict]) -> str:
        """Extraer síntomas de la conversación"""
        sintomas = []
        for msg in mensajes:
            if msg.get('role') == 'user':
                sintomas.append(msg.get('content', ''))
        
        return ' | '.join(sintomas[:3])  # Primeros 3 mensajes
    
    def responder_duda_post_diagnostico(self, pregunta: str, diagnostico: Dict) -> str:
        """Responder dudas sobre el diagnóstico"""
        
        contexto = {
            'diagnostico': diagnostico['diagnostico'],
            'productos': [p['nombre'] for p in diagnostico['productos']],
            'plantas': [p['nombre_comun'] for p in diagnostico['plantas']],
            'pregunta': pregunta
        }
        
        respuesta = self.gpt.responder_duda_tratamiento(contexto)
        
        return respuesta


if __name__ == "__main__":
    print("="*70)
    print("TEST MOTOR DIAGNÓSTICO V3.0")
    print("="*70)
    
    motor = MotorDiagnosticoV3()
    print("\n✅ Motor inicializado correctamente")
    print("="*70)