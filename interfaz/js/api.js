/**
 * Cliente API de Kairos - ACTUALIZADO
 * Maneja todas las peticiones al backend
 */

class KairosAPI {
    constructor() {
        this.baseURL = KairosConfig.API_BASE_URL;
        this.sesionId = null;
    }

    /**
     * Realizar petición HTTP
     */
    async request(endpoint, method = 'GET', data = null) {
        const url = `${this.baseURL}${endpoint}`;
        
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            if (KairosConfig.DEBUG) {
                console.log(`📡 ${method} ${endpoint}`, data);
            }

            const response = await fetch(url, options);
            const result = await response.json();

            if (KairosConfig.DEBUG) {
                console.log(`✅ Respuesta:`, result);
            }

            return result;

        } catch (error) {
            console.error('❌ Error API:', error);
            throw error;
        }
    }

    /**
     * Crear nueva sesión
     */
    async nuevaSesion(dispositivo = 'web') {
        const data = { dispositivo };
        const result = await this.request(KairosConfig.API.NUEVA_SESION, 'POST', data);
        
        if (result.success) {
            this.sesionId = result.sesion_id;
        }
        
        return result;
    }

    /**
     * Capturar datos del paciente
     */
    async capturarDatos(nombre, dni, edad = null) {
        const data = {
            sesion_id: this.sesionId,
            nombre,
            dni,
            edad
        };
        
        return await this.request(KairosConfig.API.CAPTURAR_DATOS, 'POST', data);
    }

    /**
     * Enviar mensaje
     */
    async enviarMensaje(mensaje) {
        const data = {
            sesion_id: this.sesionId,
            mensaje
        };
        
        return await this.request(KairosConfig.API.MENSAJE, 'POST', data);
    }

    /**
     * ⭐ NUEVO: Generar diagnóstico
     */
    async generarDiagnostico() {
        const data = {
            sesion_id: this.sesionId
        };
        
        return await this.request('/api/sesion/diagnostico', 'POST', data);
    }

    /**
     * ⭐ NUEVO: Imprimir receta
     */
    async imprimirReceta() {
        const data = {
            sesion_id: this.sesionId
        };
        
        return await this.request('/api/sesion/imprimir', 'POST', data);
    }

    /**
     * Finalizar sesión
     */
    async finalizarSesion() {
        const data = {
            sesion_id: this.sesionId
        };
        
        return await this.request(KairosConfig.API.FINALIZAR, 'POST', data);
    }

    /**
     * Obtener estadísticas
     */
    async obtenerEstadisticas() {
        return await this.request(KairosConfig.API.ESTADISTICAS, 'GET');
    }

    /**
     * Obtener configuración
     */
    async obtenerConfig() {
        return await this.request(KairosConfig.API.CONFIG, 'GET');
    }

    /**
     * Health check
     */
    async healthCheck() {
        try {
            const result = await this.request(KairosConfig.API.HEALTH, 'GET');
            return result.success;
        } catch {
            return false;
        }
    }
}

// Instancia global
const api = new KairosAPI();