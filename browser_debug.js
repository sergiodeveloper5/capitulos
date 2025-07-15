// Script de debugging para ejecutar en la consola del navegador
// Copiar y pegar este código en la consola del navegador cuando esté en la página del pedido

// Función para encontrar el widget de capítulos
function findCapitulosWidget() {
    // Buscar el widget en el DOM
    const widgetElement = document.querySelector('.capitulos-accordion-widget');
    if (!widgetElement) {
        console.log('❌ Widget de capítulos no encontrado en el DOM');
        return null;
    }
    
    // Buscar el componente Owl asociado
    const component = widgetElement.__owl__;
    if (!component) {
        console.log('❌ Componente Owl no encontrado');
        return null;
    }
    
    console.log('✅ Widget de capítulos encontrado');
    return component;
}

// Función para debuggear el estado del widget
function debugWidget() {
    console.log('🔍 === INICIANDO DEBUG DEL WIDGET ===');
    
    const widget = findCapitulosWidget();
    if (!widget) {
        return;
    }
    
    // Llamar al método de debug del widget
    if (typeof widget.debugState === 'function') {
        widget.debugState();
    } else {
        console.log('❌ Método debugState no encontrado en el widget');
        
        // Debug manual
        console.log('🔍 Record ID:', widget.props?.record?.resId);
        console.log('🔍 Raw data:', widget.props?.record?.data?.capitulos_agrupados);
        console.log('🔍 Parsed data:', widget.parsedData);
        console.log('🔍 State:', widget.state);
    }
}

// Función para forzar actualización del widget
function forceRefreshWidget() {
    console.log('🔄 === FORZANDO ACTUALIZACIÓN DEL WIDGET ===');
    
    const widget = findCapitulosWidget();
    if (!widget) {
        return;
    }
    
    // Llamar al método de refresh del widget
    if (typeof widget.forceRefresh === 'function') {
        widget.forceRefresh();
    } else {
        console.log('❌ Método forceRefresh no encontrado en el widget');
        
        // Refresh manual
        if (widget.props?.record?.load) {
            console.log('🔄 Recargando registro...');
            widget.props.record.load().then(() => {
                console.log('✅ Registro recargado');
                if (widget.render) {
                    widget.render(true);
                    console.log('✅ Widget re-renderizado');
                }
            }).catch(error => {
                console.error('❌ Error al recargar:', error);
            });
        }
    }
}

// Función para simular adición de producto
function simulateAddProduct(chapterName, sectionName, productId = 1) {
    console.log('➕ === SIMULANDO ADICIÓN DE PRODUCTO ===');
    
    const widget = findCapitulosWidget();
    if (!widget) {
        return;
    }
    
    if (typeof widget.addProductToSection === 'function') {
        console.log(`➕ Añadiendo producto ${productId} a capítulo '${chapterName}', sección '${sectionName}'`);
        widget.addProductToSection(chapterName, sectionName);
    } else {
        console.log('❌ Método addProductToSection no encontrado en el widget');
    }
}

// Función para verificar datos del servidor
async function checkServerData() {
    console.log('🌐 === VERIFICANDO DATOS DEL SERVIDOR ===');
    
    const widget = findCapitulosWidget();
    if (!widget) {
        return;
    }
    
    const orderId = widget.props?.record?.resId;
    if (!orderId) {
        console.log('❌ No se pudo obtener el ID del pedido');
        return;
    }
    
    try {
        // Obtener datos directamente del servidor
        const response = await fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'sale.order',
                    method: 'read',
                    args: [[orderId], ['capitulos_agrupados', 'tiene_multiples_capitulos', 'order_line']],
                    kwargs: {}
                },
                id: Math.random()
            })
        });
        
        const data = await response.json();
        console.log('🌐 Datos del servidor:', data.result);
        
        if (data.result && data.result.length > 0) {
            const orderData = data.result[0];
            console.log('🌐 Capítulos agrupados (raw):', orderData.capitulos_agrupados);
            console.log('🌐 Tiene múltiples capítulos:', orderData.tiene_multiples_capitulos);
            console.log('🌐 Líneas del pedido:', orderData.order_line?.length || 0);
            
            try {
                const parsed = JSON.parse(orderData.capitulos_agrupados || '{}');
                console.log('🌐 Capítulos agrupados (parsed):', parsed);
                console.log('🌐 Número de capítulos:', Object.keys(parsed).length);
            } catch (e) {
                console.error('❌ Error al parsear JSON:', e);
            }
        }
        
    } catch (error) {
        console.error('❌ Error al obtener datos del servidor:', error);
    }
}

// Función principal para ejecutar todas las verificaciones
function fullDebug() {
    console.log('🚀 === DEBUGGING COMPLETO ===');
    debugWidget();
    setTimeout(() => checkServerData(), 1000);
}

// Exponer funciones globalmente para fácil acceso
window.debugCapitulos = {
    debug: debugWidget,
    refresh: forceRefreshWidget,
    simulate: simulateAddProduct,
    server: checkServerData,
    full: fullDebug,
    widget: findCapitulosWidget
};

console.log('🎯 === HERRAMIENTAS DE DEBUG CARGADAS ===');
console.log('Usa las siguientes funciones en la consola:');
console.log('- debugCapitulos.debug() - Debuggear estado del widget');
console.log('- debugCapitulos.refresh() - Forzar actualización');
console.log('- debugCapitulos.server() - Verificar datos del servidor');
console.log('- debugCapitulos.full() - Debug completo');
console.log('- debugCapitulos.widget() - Obtener referencia al widget');
console.log('===============================================');