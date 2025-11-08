/**
 * Aplicación principal de Kairos
 * Lógica de flujo y UI
 */

class KairosApp {
    constructor() {
        this.estado = 'espera';
        this.datosUsuario = null;
        this.mensajes = [];

        console.log('🚀 Kairos App inicializada');
        console.log('🔧 Debug mode:', KairosConfig.DEBUG);
        
        this.inicializar();
    }

    /**
     * Inicializar aplicación
     */
    async inicializar() {
        console.log('🚀 Kairos App inicializada');
        
        // Verificar conexión API
        const conectado = await api.healthCheck();
        if (!conectado) {
            this.mostrarError('No se pudo conectar con el servidor');
            return;
        }

        // Cargar estadísticas
        this.actualizarEstadisticas();
        
        // Auto-refresh estadísticas cada 30 seg
        setInterval(() => this.actualizarEstadisticas(), 30000);

        // Detectar inactividad
        this.resetearInactividad();
    }

    /**
     * Actualizar estadísticas
     */
    async actualizarEstadisticas() {
        try {
            const result = await api.obtenerEstadisticas();
            if (result.success) {
                document.getElementById('contador-hoy').textContent = 
                    result.estadisticas.total_consultas || 0;
            }
        } catch (error) {
            console.error('Error obteniendo estadísticas:', error);
        }
    }

    /**
     * Cambiar pantalla
     */
    cambiarPantalla(pantalla) {
        // Ocultar todas
        document.querySelectorAll('.pantalla').forEach(p => {
            p.classList.remove('activa');
        });

        // Mostrar nueva
        const elemento = document.getElementById(`pantalla-${pantalla}`);
        if (elemento) {
            elemento.classList.add('activa');
            this.estado = pantalla;
        }

        console.log(`📺 Pantalla: ${pantalla}`);
    }

    /**
     * Iniciar consulta
     */
    async iniciarConsulta() {
        try {
            const result = await api.nuevaSesion();
            
            if (result.success) {
                console.log('✅ Sesión creada:', result.sesion_id);
                this.cambiarPantalla('datos');
            } else {
                this.mostrarError('No se pudo iniciar sesión');
            }
        } catch (error) {
            this.mostrarError('Error al iniciar sesión');
        }
    }

    /**
     * Capturar datos del paciente
     */
    async capturarDatos() {
        const nombre = document.getElementById('nombre').value.trim();
        const dni = document.getElementById('dni').value.trim();
        const edadInput = document.getElementById('edad').value;
        const edad = edadInput ? parseInt(edadInput) : null;

        // Validar
        const validacion = this.validarDatos(nombre, dni, edad);
        if (!validacion.valido) {
            this.mostrarValidacion(validacion.errores);
            return;
        }

        try {
            const result = await api.capturarDatos(nombre, dni, edad);
            
            if (result.success) {
                this.datosUsuario = {
                    nombre: nombre,
                    dni: dni,
                    edad: edad,
                    ...result.info
                };
                
                // Actualizar UI
                document.getElementById('nombre-paciente').textContent = nombre;
                document.getElementById('dni-paciente').textContent = `DNI: ${dni}`;
                
                // Ir a chat
                this.cambiarPantalla('chat');
                
                // Mensaje inicial con nombre correcto
                const primerNombre = nombre.split(' ')[0];
                const mensajeBienvenida = `Hola ${primerNombre}! ¿En qué puedo ayudarte hoy?`;
                
                this.agregarMensajeKairos(mensajeBienvenida);
                
                console.log('✅ Datos capturados:', this.datosUsuario);
                
            } else {
                this.mostrarValidacion([result.info?.errores?.[0] || 'Error capturando datos']);
            }
        } catch (error) {
            console.error('Error:', error);
            this.mostrarValidacion(['Error de conexión con el servidor']);
        }
    }

    /**
     * Validar datos
     */
    validarDatos(nombre, dni, edad) {
        const errores = [];
        
        if (!nombre || nombre.length < 6) {
            errores.push('Ingresa nombre completo (mínimo 6 caracteres)');
        }
        
        if (!/^\d{8}$/.test(dni)) {
            errores.push('DNI debe tener 8 dígitos');
        }
        
        if (edad && (edad < 0 || edad > 120)) {
            errores.push('Edad inválida');
        }
        
        return {
            valido: errores.length === 0,
            errores
        };
    }

    /**
     * Mostrar validación
     */
    mostrarValidacion(errores) {
        const div = document.getElementById('validacion');
        
        if (errores.length === 0) {
            div.innerHTML = '';
            div.className = 'validacion';
        } else {
            div.innerHTML = errores.map(e => `❌ ${e}`).join('<br>');
            div.className = 'validacion error';
        }
    }

    /**
     * Enviar mensaje
     */
    async enviarMensaje() {
        const input = document.getElementById('mensaje-input');
        const mensaje = input.value.trim();
        
        if (!mensaje) return;
        
        // Agregar mensaje del usuario
        this.agregarMensajeUsuario(mensaje);
        input.value = '';
        
        // Mostrar indicador "escribiendo"
        document.getElementById('escribiendo').style.display = 'block';
        
        try {
            const result = await api.enviarMensaje(mensaje);
            
            // Ocultar indicador
            document.getElementById('escribiendo').style.display = 'none';
            
            if (result.success) {
                // Agregar respuesta de Kairos
                this.agregarMensajeKairos(result.resultado.respuesta);
                
                // Hablar respuesta
                voz.hablar(result.resultado.respuesta);
                
                // Verificar si está listo para diagnóstico
                if (result.resultado.diagnostico_listo) {
                    setTimeout(() => this.finalizarConsulta(), 2000);
                }
            }
        } catch (error) {
            document.getElementById('escribiendo').style.display = 'none';
            this.mostrarError('Error enviando mensaje');
        }
    }

    /**
     * Agregar mensaje al chat
     */
    agregarMensajeUsuario(texto) {
        const container = document.getElementById('chat-mensajes');
        
        const div = document.createElement('div');
        div.className = 'mensaje usuario';
        div.innerHTML = `<div class="mensaje-bubble">${texto}</div>`;
        
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    agregarMensajeKairos(texto) {
        const container = document.getElementById('chat-mensajes');
        
        const div = document.createElement('div');
        div.className = 'mensaje kairos';
        div.innerHTML = `<div class="mensaje-bubble">${texto}</div>`;
        
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    /**
     * Finalizar consulta
     */
    async finalizarConsulta() {
        // Cambiar a pantalla de generando
        this.cambiarPantalla('generando');
        
        // Simular progreso
        setTimeout(() => {
            document.getElementById('paso-productos').classList.add('activo');
        }, 1000);
        
        setTimeout(() => {
            document.getElementById('paso-receta').classList.add('activo');
        }, 2000);
        
        setTimeout(() => {
            document.getElementById('paso-impresion').classList.add('activo');
        }, 3000);
        
        try {
            const result = await api.finalizarSesion();
            
            if (result.success) {
                // Ir a imprimir
                this.cambiarPantalla('imprimiendo');
                this.simularImpresion();
            } else {
                this.mostrarError('Error finalizando consulta');
            }
        } catch (error) {
            this.mostrarError('Error de conexión');
        }
    }

    /**
     * Simular impresión
     */
    simularImpresion() {
        const barra = document.getElementById('barra-impresion');
        let progreso = 0;
        
        const intervalo = setInterval(() => {
            progreso += 10;
            barra.style.width = `${progreso}%`;
            
            if (progreso >= 100) {
                clearInterval(intervalo);
                setTimeout(() => this.mostrarDespedida(), 1000);
            }
        }, 300);
    }

    /**
     * Mostrar despedida
     */
    mostrarDespedida() {
    // Ir a despedida
        this.cambiarPantalla('despedida');
        
        // Nombre correcto del usuario
        if (this.datosUsuario && this.datosUsuario.nombre) {
            const primerNombre = this.datosUsuario.nombre.split(' ')[0];
            document.getElementById('nombre-despedida').textContent = primerNombre;
        } else {
            document.getElementById('nombre-despedida').textContent = 'Paciente';
        }
        
        // Contador regresivo
        let segundos = 5;
        const contador = document.getElementById('contador');
        
        const intervalo = setInterval(() => {
            segundos--;
            contador.textContent = segundos;
            
            if (segundos <= 0) {
                clearInterval(intervalo);
                this.resetear();
            }
        }, 1000);
    }

    /**
     * Resetear aplicación
     */
    resetear() {
        // Limpiar datos
        this.datosUsuario = null;
        this.mensajes = [];
        
        // Limpiar formularios
        document.getElementById('nombre').value = '';
        document.getElementById('dni').value = '';
        document.getElementById('edad').value = '';
        document.getElementById('mensaje-input').value = '';
        document.getElementById('chat-mensajes').innerHTML = '';
        
        // Volver a inicio
        this.cambiarPantalla('espera');
        
        // Actualizar estadísticas
        this.actualizarEstadisticas();
        
        console.log('🔄 Sistema reseteado');
    }

    /**
     * Mostrar error
     */
    mostrarError(mensaje) {
        document.getElementById('mensaje-error').textContent = mensaje;
        this.cambiarPantalla('error');
    }

    /**
     * Resetear timer de inactividad
     */
    resetearInactividad() {
        // Implementar si es necesario
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// FUNCIONES GLOBALES (llamadas desde HTML)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let app;

// Inicializar al cargar
window.addEventListener('DOMContentLoaded', () => {
    app = new KairosApp();
});

function iniciarConsulta() {
    app.iniciarConsulta();
}

function capturarDatos() {
    app.capturarDatos();
}

function enviarMensaje() {
    app.enviarMensaje();
}

function volverInicio() {
    app.resetear();
}

function confirmarTerminar() {
    if (confirm('¿Seguro que quieres terminar la consulta?')) {
        app.resetear();
    }
}

// Voz
async function dictarNombre() {
    try {
        const texto = await voz.escuchar();
        document.getElementById('nombre').value = texto;
    } catch (error) {
        console.error('Error dictado:', error);
    }
}

function toggleVoz() {
    const activa = voz.toggle();
    // Cambiar icono si quieres
}