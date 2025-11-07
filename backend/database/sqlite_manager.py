"""
Gestor de base de datos SQLite (backup offline)
"""

import sqlite3
import json
from datetime import datetime

class SQLiteManager:
    """
    Base de datos local SQLite para modo offline
    """
    
    def __init__(self, db_path='data/kairos_offline.db'):
        self.db_path = db_path
        self.crear_tablas()
    
    def conectar(self):
        """Crea conexión"""
        return sqlite3.connect(self.db_path)
    
    def crear_tablas(self):
        """Crea tablas si no existen"""
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Leer schema
        with open('database/04_sqlite_schema.sql', 'r') as f:
            schema = f.read()
            cursor.executescript(schema)
        
        conn.commit()
        conn.close()
    
    def guardar_consulta_pendiente(self, usuario_id, sesion_id, datos):
        """Guarda consulta para sincronizar después"""
        conn = self.conectar()
        cursor = conn.cursor()
        
        datos_json = json.dumps(datos)
        
        cursor.execute("""
            INSERT INTO consultas_pendientes (usuario_id, sesion_id, datos_json)
            VALUES (?, ?, ?)
        """, (usuario_id, sesion_id, datos_json))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Consulta guardada offline: {sesion_id}")
    
    def obtener_pendientes(self):
        """Obtiene consultas no sincronizadas"""
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM consultas_pendientes
            WHERE sincronizado = 0
        """)
        
        pendientes = cursor.fetchall()
        conn.close()
        
        return pendientes

if __name__ == "__main__":
    # Probar
    sqlite = SQLiteManager()
    print("✅ SQLite configurado correctamente")