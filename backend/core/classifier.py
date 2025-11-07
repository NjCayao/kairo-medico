"""
Clasificador de Intenciones con Machine Learning
Versión simplificada para Kairos 
"""

import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from typing import Tuple, List, Dict, Optional
import os
import re
from unidecode import unidecode

class IntentClassifier:
    """
    Clasificador de intenciones usando SVM
    """
    
    def __init__(self, model_path: str = None):
        """
        Inicializar clasificador
        
        Args:
            model_path: Ruta al modelo guardado
        """
        # Determinar ruta del modelo
        if model_path:
            self.model_path = model_path
        else:
            # Ruta por defecto
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.model_path = os.path.join(base_dir, 'backend', 'data', 'models', 'classifier.pkl')
        
        # Componentes del modelo
        self.vectorizer = TfidfVectorizer(
            max_features=500,           # Reducido para feria (más rápido)
            lowercase=True,
            analyzer='word',
            ngram_range=(1, 2),         # Palabras y bigramas
            max_df=0.85,
            min_df=1
        )
        
        self.classifier = SVC(
            kernel='linear',
            probability=True,
            C=1.0,
            random_state=42
        )
        
        self.label_encoder = LabelEncoder()
        
        # Lista de intenciones
        self.intenciones = []
        
        # Estado
        self.esta_entrenado = False
        
        # Intentar cargar modelo existente
        self.cargar_modelo()
    
    def preprocesar_texto(self, texto: str) -> str:
        """
        Limpiar y normalizar texto
        
        Args:
            texto: Texto original
            
        Returns:
            str: Texto limpio
        """
        # Convertir a minúsculas
        texto = texto.lower().strip()
        
        # Normalizar acentos (á → a)
        texto = unidecode(texto)
        
        # Eliminar caracteres especiales excepto letras, números y espacios
        texto = re.sub(r'[^\w\s]', ' ', texto)
        
        # Eliminar espacios múltiples
        texto = ' '.join(texto.split())
        
        return texto
    
    def entrenar(self, textos: List[str], intenciones: List[str]) -> Dict[str, float]:
        """
        Entrenar el modelo
        
        Args:
            textos: Lista de textos de ejemplo
            intenciones: Lista de intenciones correspondientes
            
        Returns:
            Dict con métricas de entrenamiento
        """
        print("🎓 Iniciando entrenamiento del clasificador...")
        
        # Validar datos
        if len(textos) != len(intenciones):
            raise ValueError("Textos e intenciones deben tener la misma longitud")
        
        if len(textos) < 10:
            print("⚠️ ADVERTENCIA: Pocos ejemplos de entrenamiento (< 10)")
        
        # Preprocesar textos
        print("   📝 Preprocesando textos...")
        textos_limpios = [self.preprocesar_texto(texto) for texto in textos]
        
        # Codificar intenciones
        print("   🏷️ Codificando intenciones...")
        intenciones_numericas = self.label_encoder.fit_transform(intenciones)
        self.intenciones = list(self.label_encoder.classes_)
        
        print(f"   ✅ Intenciones detectadas: {len(self.intenciones)}")
        for i, intencion in enumerate(self.intenciones):
            count = list(intenciones).count(intencion)
            print(f"      {i+1}. {intencion}: {count} ejemplos")
        
        # Vectorizar textos (TF-IDF)
        print("   🔢 Vectorizando textos...")
        X = self.vectorizer.fit_transform(textos_limpios)
        
        print(f"   ✅ Vocabulario: {len(self.vectorizer.vocabulary_)} palabras")
        
        # Entrenar clasificador SVM
        print("   🧠 Entrenando modelo SVM...")
        self.classifier.fit(X, intenciones_numericas)
        
        # Calcular precisión en datos de entrenamiento
        predicciones = self.classifier.predict(X)
        precision = np.mean(predicciones == intenciones_numericas)
        
        print(f"\n   ✅ Modelo entrenado exitosamente!")
        print(f"   📊 Precisión en entrenamiento: {precision:.2%}")
        
        self.esta_entrenado = True
        
        # Guardar modelo automáticamente
        self.guardar_modelo()
        
        return {
            'precision': float(precision),
            'num_ejemplos': len(textos),
            'num_intenciones': len(self.intenciones),
            'vocabulario': len(self.vectorizer.vocabulary_)
        }
    
    def predecir(self, texto: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Predecir intención de un texto
        
        Args:
            texto: Texto a clasificar
            
        Returns:
            Tupla (intencion, confianza, probabilidades_todas)
        """
        if not self.esta_entrenado:
            raise ValueError("El modelo no está entrenado")
        
        # Preprocesar
        texto_limpio = self.preprocesar_texto(texto)
        
        # Vectorizar
        X = self.vectorizer.transform([texto_limpio])
        
        # Predecir
        prediccion_numerica = self.classifier.predict(X)[0]
        intencion = self.label_encoder.inverse_transform([prediccion_numerica])[0]
        
        # Obtener probabilidades
        probabilidades_array = self.classifier.predict_proba(X)[0]
        
        # Crear diccionario de probabilidades
        probabilidades = {}
        for i, prob in enumerate(probabilidades_array):
            intent_name = self.label_encoder.inverse_transform([i])[0]
            probabilidades[intent_name] = float(prob)
        
        # Confianza es la probabilidad máxima
        confianza = float(max(probabilidades_array))
        
        return intencion, confianza, probabilidades
    
    def predecir_con_umbral(self, texto: str, umbral: float = 0.6) -> Tuple[str, float]:
        """
        Predecir con umbral de confianza mínimo
        
        Args:
            texto: Texto a clasificar
            umbral: Confianza mínima requerida (0-1)
            
        Returns:
            Tupla (intencion, confianza)
            Si confianza < umbral, retorna ('desconocida', confianza)
        """
        intencion, confianza, _ = self.predecir(texto)
        
        if confianza < umbral:
            return 'desconocida', confianza
        
        return intencion, confianza
    
    def explicar_prediccion(self, texto: str) -> Dict:
        """
        Explicar por qué se clasificó de cierta forma
        
        Args:
            texto: Texto clasificado
            
        Returns:
            Dict con explicación detallada
        """
        if not self.esta_entrenado:
            return {"error": "Modelo no entrenado"}
        
        # Predecir
        intencion, confianza, probabilidades = self.predecir(texto)
        
        # Preprocesar
        texto_limpio = self.preprocesar_texto(texto)
        palabras = texto_limpio.split()
        
        # Obtener palabras que están en el vocabulario
        vocabulario = self.vectorizer.get_feature_names_out()
        palabras_reconocidas = [p for p in palabras if p in vocabulario]
        
        # Generar explicación
        if confianza > 0.8:
            nivel = "muy seguro"
        elif confianza > 0.6:
            nivel = "bastante seguro"
        elif confianza > 0.4:
            nivel = "poco seguro"
        else:
            nivel = "muy poco seguro"
        
        # Top 3 intenciones más probables
        top_intenciones = sorted(
            probabilidades.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        explicacion = {
            'texto_original': texto,
            'texto_procesado': texto_limpio,
            'palabras_reconocidas': palabras_reconocidas,
            'intencion_detectada': intencion,
            'confianza': confianza,
            'nivel_confianza': nivel,
            'top_3_intenciones': [
                {
                    'intencion': intent,
                    'probabilidad': prob,
                    'porcentaje': f"{prob:.1%}"
                }
                for intent, prob in top_intenciones
            ]
        }
        
        return explicacion
    
    def guardar_modelo(self) -> bool:
        """
        Guardar modelo entrenado
        
        Returns:
            bool: True si guardó correctamente
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Empaquetar todo
            modelo_completo = {
                'vectorizer': self.vectorizer,
                'classifier': self.classifier,
                'label_encoder': self.label_encoder,
                'intenciones': self.intenciones,
                'version': '2.0-feria'
            }
            
            # Guardar con pickle
            with open(self.model_path, 'wb') as f:
                pickle.dump(modelo_completo, f)
            
            print(f"💾 Modelo guardado en: {self.model_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar modelo: {e}")
            return False
    
    def cargar_modelo(self) -> bool:
        """
        Cargar modelo guardado
        
        Returns:
            bool: True si cargó correctamente
        """
        if not os.path.exists(self.model_path):
            print(f"ℹ️ No hay modelo guardado en: {self.model_path}")
            print("   Necesitas entrenar primero con train.py")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                modelo_completo = pickle.load(f)
            
            # Restaurar componentes
            self.vectorizer = modelo_completo['vectorizer']
            self.classifier = modelo_completo['classifier']
            self.label_encoder = modelo_completo['label_encoder']
            self.intenciones = modelo_completo['intenciones']
            
            self.esta_entrenado = True
            
            print(f"✅ Modelo cargado desde: {self.model_path}")
            print(f"   Intenciones: {', '.join(self.intenciones)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar modelo: {e}")
            return False
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtener estadísticas del modelo
        
        Returns:
            Dict con estadísticas
        """
        if not self.esta_entrenado:
            return {"error": "Modelo no entrenado"}
        
        stats = {
            'esta_entrenado': self.esta_entrenado,
            'intenciones': self.intenciones,
            'num_intenciones': len(self.intenciones),
            'vocabulario_size': len(self.vectorizer.vocabulary_),
            'modelo_tipo': 'SVM con kernel lineal',
            'version': '2.0-feria'
        }
        
        return stats

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRUEBAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("="*60)
    print("PROBANDO CLASIFICADOR")
    print("="*60)
    
    # Crear clasificador
    clf = IntentClassifier()
    
    # Datos de ejemplo para entrenar
    textos_ejemplo = [
        # Consulta médica
        "Me duele la cabeza", "Tengo dolor de cabeza", "Me duele mucho la cabeza",
        "Siento dolor en la cabeza", "Tengo cefalea", "Me duele la frente",
        
        # Pregunta producto
        "Qué es la moringa", "Para qué sirve el ganoderma", "Qué contiene la moringa",
        "Cuéntame sobre la moringa", "Información del ganoderma", "De qué está hecho",
        
        # Pregunta uso
        "Cómo lo tomo", "Cómo se usa", "Cuántas cápsulas tomo", 
        "A qué hora lo tomo", "Cómo se prepara", "Modo de uso",
        
        # Pregunta precio
        "Cuánto cuesta", "Qué precio tiene", "Cuál es el precio",
        "Cuánto vale", "Cuánto sale", "Precio",
        
        # Saludo
        "Hola", "Buenos días", "Buenas tardes", "Hey", "Hola Kairos",
        
        # Despedida
        "Gracias", "Adiós", "Hasta luego", "Chao", "Gracias por todo"
    ]
    
    intenciones_ejemplo = [
        # Consulta médica
        "consulta_medica", "consulta_medica", "consulta_medica",
        "consulta_medica", "consulta_medica", "consulta_medica",
        
        # Pregunta producto
        "pregunta_producto", "pregunta_producto", "pregunta_producto",
        "pregunta_producto", "pregunta_producto", "pregunta_producto",
        
        # Pregunta uso
        "pregunta_uso", "pregunta_uso", "pregunta_uso",
        "pregunta_uso", "pregunta_uso", "pregunta_uso",
        
        # Pregunta precio
        "pregunta_precio", "pregunta_precio", "pregunta_precio",
        "pregunta_precio", "pregunta_precio", "pregunta_precio",
        
        # Saludo
        "saludo", "saludo", "saludo", "saludo", "saludo",
        
        # Despedida
        "despedida", "despedida", "despedida", "despedida", "despedida"
    ]
    
    # Entrenar
    print("\n🎓 Entrenando con ejemplos básicos...\n")
    metricas = clf.entrenar(textos_ejemplo, intenciones_ejemplo)
    
    print(f"\n📊 Métricas finales:")
    for key, value in metricas.items():
        print(f"   {key}: {value}")
    
    # Probar predicciones
    print("\n" + "="*60)
    print("PROBANDO PREDICCIONES")
    print("="*60)
    
    pruebas = [
        "Hola, me duele mucho la cabeza",
        "Qué es la moringa y para qué sirve",
        "Cuánto cuesta el ganoderma",
        "Cómo tomo las cápsulas",
        "Muchas gracias por tu ayuda",
        "Tengo quistes en los ovarios"
    ]
    
    for texto in pruebas:
        print(f"\n📝 Texto: '{texto}'")
        
        intencion, confianza, _ = clf.predecir(texto)
        print(f"   ➜ Intención: {intencion}")
        print(f"   ➜ Confianza: {confianza:.1%}")
        
        # Mostrar explicación
        explicacion = clf.explicar_prediccion(texto)
        print(f"   ➜ Nivel: {explicacion['nivel_confianza']}")
        print(f"   ➜ Top 3:")
        for item in explicacion['top_3_intenciones']:
            print(f"      - {item['intencion']}: {item['porcentaje']}")
    
    # Estadísticas
    print("\n" + "="*60)
    print("ESTADÍSTICAS DEL MODELO")
    print("="*60)
    
    stats = clf.obtener_estadisticas()
    for key, value in stats.items():
        if key != 'intenciones':
            print(f"   {key}: {value}")
    
    print("\n" + "="*60)