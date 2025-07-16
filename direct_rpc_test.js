/**
 * Script para probar directamente la llamada RPC que está fallando
 * Ejecutar en la consola del navegador (F12 -> Console)
 */

window.directRPCTest = {
    
    /**
     * Prueba directa de la llamada RPC
     */
    async testRPCCall() {
        console.log('=== PRUEBA DIRECTA DE LLAMADA RPC ===');
        
        try {
            // Obtener el ID del pedido actual
            const orderId = this.getCurrentOrderId();
            if (!orderId) {
                console.error('❌ No se pudo obtener el ID del pedido');
                return false;
            }
            
            console.log(`✅ ID del pedido: ${orderId}`);
            
            // Parámetros de prueba
            const testParams = {
                order_id: orderId,
                capitulo_name: 'AAAAAA',  // Según los logs
                seccion_name: 'ALQUILER (SECCIÓN FIJA)',  // Según los logs
                product_id: 14,  // Según los logs
                quantity: 1.0
            };
            
            console.log('📤 Parámetros de la llamada:', testParams);
            
            // Realizar la llamada RPC
            console.log('🔄 Realizando llamada RPC...');
            
            const result = await this.makeRPCCall(
                'sale.order',
                'add_product_to_section',
                [testParams.order_id, testParams.capitulo_name, testParams.seccion_name, testParams.product_id, testParams.quantity]
            );
            
            console.log('✅ ÉXITO - Resultado:', result);
            return true;
            
        } catch (error) {
            console.error('❌ ERROR en llamada RPC:', error);
            
            // Mostrar detalles del error
            if (error.data) {
                console.error('Datos del error:', error.data);
            }
            if (error.message) {
                console.error('Mensaje:', error.message);
            }
            if (error.traceback) {
                console.error('Traceback:', error.traceback);
            }
            
            return false;
        }
    },
    
    /**
     * Obtiene el ID del pedido actual
     */
    getCurrentOrderId() {
        try {
            // Método 1: Desde la URL
            const urlMatch = window.location.href.match(/id=(\d+)/);
            if (urlMatch) {
                return parseInt(urlMatch[1]);
            }
            
            // Método 2: Desde el contexto de Odoo
            if (window.odoo && window.odoo.define) {
                // Intentar acceder al contexto actual
                const webClient = document.querySelector('.o_web_client');
                if (webClient && webClient.__owl__) {
                    const component = webClient.__owl__.component;
                    if (component && component.env && component.env.services) {
                        const actionService = component.env.services.action;
                        if (actionService && actionService.currentController) {
                            const controller = actionService.currentController;
                            if (controller.props && controller.props.resId) {
                                return controller.props.resId;
                            }
                        }
                    }
                }
            }
            
            // Método 3: Desde elementos del DOM
            const formElement = document.querySelector('[data-model="sale.order"]');
            if (formElement) {
                const resId = formElement.getAttribute('data-res-id');
                if (resId) {
                    return parseInt(resId);
                }
            }
            
            // Método 4: Buscar en inputs hidden
            const hiddenInputs = document.querySelectorAll('input[type="hidden"]');
            for (const input of hiddenInputs) {
                if (input.name === 'id' || input.name === 'res_id') {
                    const value = parseInt(input.value);
                    if (value > 0) {
                        return value;
                    }
                }
            }
            
            // Método 5: Preguntar al usuario
            const userInput = prompt('No se pudo detectar automáticamente el ID del pedido. Por favor, ingrese el ID:');
            if (userInput) {
                const id = parseInt(userInput);
                if (id > 0) {
                    return id;
                }
            }
            
            return null;
            
        } catch (error) {
            console.error('Error obteniendo ID del pedido:', error);
            return null;
        }
    },
    
    /**
     * Realiza una llamada RPC a Odoo
     */
    async makeRPCCall(model, method, args = [], kwargs = {}) {
        try {
            // Método 1: Usar el servicio RPC de Odoo si está disponible
            if (window.odoo && window.odoo.define) {
                return new Promise((resolve, reject) => {
                    window.odoo.define('rpc_test', ['web.rpc'], function(rpc) {
                        rpc.query({
                            model: model,
                            method: method,
                            args: args,
                            kwargs: kwargs
                        }).then(resolve).catch(reject);
                    });
                });
            }
            
            // Método 2: Llamada fetch directa
            const response = await fetch('/web/dataset/call_kw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        model: model,
                        method: method,
                        args: args,
                        kwargs: kwargs
                    },
                    id: Math.floor(Math.random() * 1000000)
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw data.error;
            }
            
            return data.result;
            
        } catch (error) {
            console.error('Error en makeRPCCall:', error);
            throw error;
        }
    },
    
    /**
     * Prueba con diferentes productos
     */
    async testWithDifferentProducts() {
        console.log('=== PRUEBA CON DIFERENTES PRODUCTOS ===');
        
        const orderId = this.getCurrentOrderId();
        if (!orderId) {
            console.error('❌ No se pudo obtener el ID del pedido');
            return;
        }
        
        // Lista de productos para probar
        const productIds = [1, 2, 3, 4, 5, 14];
        
        for (const productId of productIds) {
            console.log(`\n🔄 Probando con producto ID: ${productId}`);
            
            try {
                const result = await this.makeRPCCall(
                    'sale.order',
                    'add_product_to_section',
                    [orderId, 'AAAAAA', 'ALQUILER (SECCIÓN FIJA)', productId, 1.0]
                );
                
                console.log(`✅ ÉXITO con producto ${productId}:`, result);
                break; // Si uno funciona, parar
                
            } catch (error) {
                console.error(`❌ Error con producto ${productId}:`, error.message || error);
            }
        }
    },
    
    /**
     * Obtiene información del pedido actual
     */
    async getOrderInfo() {
        console.log('=== INFORMACIÓN DEL PEDIDO ===');
        
        const orderId = this.getCurrentOrderId();
        if (!orderId) {
            console.error('❌ No se pudo obtener el ID del pedido');
            return;
        }
        
        try {
            const orderInfo = await this.makeRPCCall(
                'sale.order',
                'read',
                [[orderId], ['name', 'state', 'order_line']]
            );
            
            console.log('📋 Información del pedido:', orderInfo);
            
            // Obtener información de las líneas
            if (orderInfo[0] && orderInfo[0].order_line) {
                const lineIds = orderInfo[0].order_line;
                const linesInfo = await this.makeRPCCall(
                    'sale.order.line',
                    'read',
                    [lineIds, ['name', 'sequence', 'es_encabezado_capitulo', 'es_encabezado_seccion', 'product_id']]
                );
                
                console.log('📝 Líneas del pedido:');
                linesInfo.forEach(line => {
                    const tipo = line.es_encabezado_capitulo ? 'CAPÍTULO' : 
                               line.es_encabezado_seccion ? 'SECCIÓN' : 'PRODUCTO';
                    console.log(`  ${line.sequence}: [${tipo}] ${line.name}`);
                });
            }
            
        } catch (error) {
            console.error('❌ Error obteniendo información:', error);
        }
    }
};

// Mensaje de ayuda
console.log(`
🔧 HERRAMIENTAS DE PRUEBA RPC DISPONIBLES:

1. directRPCTest.testRPCCall() - Prueba la llamada RPC específica
2. directRPCTest.testWithDifferentProducts() - Prueba con diferentes productos
3. directRPCTest.getOrderInfo() - Obtiene información del pedido
4. directRPCTest.getCurrentOrderId() - Obtiene el ID del pedido actual

Ejemplo de uso:
  directRPCTest.testRPCCall()
`);