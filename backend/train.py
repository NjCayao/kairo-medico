"""
Script de entrenamiento de Kairos
Lee datos desde Excel y entrena el modelo
"""

import pandas as pd
import sys
import os
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURAR PATHS CORRECTAMENTE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Obtener ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agregar al path
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

# Ahora sí importar
from backend.core.classifier import IntentClassifier

# Rutas de archivos
EXCEL_ENTRENAMIENTO = os.path.join(BASE_DIR, 'backend', 'data', 'kairos_entrenamiento.xlsx')
MODELO_PATH = os.path.join(BASE_DIR, 'backend', 'data', 'models', 'classifier.pkl')

class TrainerKairos:
    """
    Entrenador del modelo de Kairos
    """
    
    def __init__(self, excel_path: str = None):
        """
        Inicializar entrenador
        
        Args:
            excel_path: Ruta al Excel de entrenamiento
        """
        self.excel_path = excel_path or EXCEL_ENTRENAMIENTO
        self.classifier = IntentClassifier(model_path=MODELO_PATH)
        self.datos = None
        self.metricas = {}
    
    def cargar_datos(self) -> bool:
        """
        Cargar datos desde Excel
        
        Returns:
            bool: True si cargó correctamente
        """
        try:
            print("="*60)
            print("CARGANDO DATOS DE ENTRENAMIENTO")
            print("="*60)
            print(f"📂 Archivo: {self.excel_path}\n")
            
            # Verificar que existe
            if not os.path.exists(self.excel_path):
                print(f"❌ No se encuentra el archivo: {self.excel_path}")
                print(f"\n💡 Asegúrate de tener el archivo en:")
                print(f"   {self.excel_path}")
                return False
            
            # Leer Excel
            self.datos = pd.read_excel(self.excel_path)
            
            # Normalizar nombres de columnas
            self.datos.columns = [col.lower().strip() for col in self.datos.columns]
            
            # Verificar columnas requeridas
            columnas_requeridas = ['entrada', 'intencion']
            for col in columnas_requeridas:
                if col not in self.datos.columns:
                    print(f"❌ Falta columna '{col}' en el Excel")
                    print(f"   Columnas encontradas: {list(self.datos.columns)}")
                    return False
            
            # Limpiar datos vacíos
            self.datos = self.datos.dropna(subset=['entrada', 'intencion'])
            
            # Mostrar estadísticas
            print(f"✅ Datos cargados exitosamente\n")
            print(f"📊 ESTADÍSTICAS:")
            print(f"   Total de ejemplos: {len(self.datos)}")
            print(f"   Intenciones únicas: {self.datos['intencion'].nunique()}")
            print(f"\n📋 Distribución por intención:")
            
            distribucion = self.datos['intencion'].value_counts()
            for intencion, count in distribucion.items():
                porcentaje = (count / len(self.datos)) * 100
                barra = '█' * int(porcentaje / 2)
                print(f"   {intencion:20} {count:3} ejemplos {barra} {porcentaje:.1f}%")
            
            # Validar cantidad mínima
            print(f"\n🔍 VALIDACIONES:")
            
            min_ejemplos = 5
            intenciones_pocas = [
                intencion for intencion, count in distribucion.items() 
                if count < min_ejemplos
            ]
            
            if intenciones_pocas:
                print(f"   ⚠️ Intenciones con pocos ejemplos (< {min_ejemplos}):")
                for intencion in intenciones_pocas:
                    print(f"      - {intencion}: {distribucion[intencion]} ejemplos")
                print(f"   💡 Recomendación: Agregar más ejemplos para mejor precisión")
            else:
                print(f"   ✅ Todas las intenciones tienen suficientes ejemplos")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar datos: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def entrenar(self):
        """
        Entrenar el modelo con los datos cargados
        """
        if self.datos is None:
            print("❌ Primero debes cargar los datos")
            return False
        
        print("\n" + "="*60)
        print("ENTRENANDO MODELO")
        print("="*60 + "\n")
        
        # Obtener textos e intenciones
        X = self.datos['entrada'].values
        y = self.datos['intencion'].values
        
        # Entrenar
        self.metricas = self.classifier.entrenar(X, y)
        
        print("\n" + "="*60)
        print("ENTRENAMIENTO COMPLETADO")
        print("="*60)
        
        return True
    
    def probar_predicciones(self):
        """
        Probar el modelo con ejemplos de cada intención
        """
        if not self.classifier.esta_entrenado:
            print("❌ El modelo no está entrenado")
            return
        
        print("\n" + "="*60)
        print("PROBANDO PREDICCIONES")
        print("="*60 + "\n")
        
        # Tomar 1 ejemplo de cada intención
        ejemplos_prueba = []
        for intencion in self.datos['intencion'].unique():
            ejemplo = self.datos[self.datos['intencion'] == intencion].iloc[0]
            ejemplos_prueba.append((ejemplo['entrada'], ejemplo['intencion']))
        
        # Probar cada uno
        aciertos = 0
        for texto, intencion_real in ejemplos_prueba:
            intencion_pred, confianza, _ = self.classifier.predecir(texto)
            
            resultado = "✅" if intencion_pred == intencion_real else "❌"
            
            print(f"{resultado} '{texto}'")
            print(f"   Real: {intencion_real}")
            print(f"   Predicción: {intencion_pred} ({confianza:.1%})")
            print()
            
            if intencion_pred == intencion_real:
                aciertos += 1
        
        precision = (aciertos / len(ejemplos_prueba)) * 100
        print(f"📊 Precisión en ejemplos de prueba: {precision:.1f}%")
        print(f"   ({aciertos}/{len(ejemplos_prueba)} correctos)\n")
    
    def generar_reporte(self):
        """
        Generar reporte de entrenamiento
        """
        print("\n" + "="*60)
        print("REPORTE FINAL")
        print("="*60 + "\n")
        
        print("📅 Fecha entrenamiento:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print(f"📂 Archivo origen: {os.path.basename(self.excel_path)}")
        print(f"\n📊 Métricas:")
        for key, value in self.metricas.items():
            print(f"   {key}: {value}")
        
        stats = self.classifier.obtener_estadisticas()
        print(f"\n🎯 Intenciones entrenadas:")
        for i, intencion in enumerate(stats['intenciones'], 1):
            print(f"   {i}. {intencion}")
        
        print(f"\n💾 Modelo guardado en:")
        print(f"   {self.classifier.model_path}")
        
        print("\n" + "="*60)
        print("✅ ¡LISTO PARA USAR!")
        print("="*60)

def main():
    """
    Función principal de entrenamiento
    """
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "KAIROS - ENTRENADOR" + " "*23 + "║")
    print("╚" + "="*58 + "╝")
    print()
    
    # Crear entrenador
    trainer = TrainerKairos()
    
    # Cargar datos
    if not trainer.cargar_datos():
        print("\n❌ No se pudieron cargar los datos")
        print("\n💡 PASOS PARA SOLUCIONAR:")
        print("   1. Verifica que el archivo Excel existe")
        print("   2. Debe estar en: backend/data/kairos_entrenamiento.xlsx")
        print("   3. Debe tener 2 columnas: 'entrada' e 'intencion'")
        return
    
    # Entrenar
    if not trainer.entrenar():
        print("\n❌ Error durante el entrenamiento")
        return
    
    # Probar predicciones
    trainer.probar_predicciones()
    
    # Generar reporte
    trainer.generar_reporte()
    
    print("\n💡 Para usar el modelo entrenado:")
    print("   1. En tu código: from backend.core.classifier import IntentClassifier")
    print("   2. clf = IntentClassifier()")
    print("   3. intencion, confianza, _ = clf.predecir('tu texto aquí')")
    print()

if __name__ == "__main__":
    main()