/**
 * Script de depuración para el problema de secciones incorrectas
 * Ejecutar en la consola del navegador cuando esté en la vista del pedido
 */

// Función para encontrar el widget de capítulos
function findCapitulosWidget() {
    // Buscar en el DOM el widget
    const widgetElement = document.querySelector('[data-field-name="capitulos_agrupados"]');
    if (!widgetElement) {
        console.log('❌ No se encontró el elemento del widget');
        return null;
    }
    
    // Buscar el componente OWL asociado
    const component = widgetElement.__owl__?.component;
    if (!component) {
        console.log('❌ No se encontró el componente OWL');
        return null;
    }
    
    console.log('✅ Widget encontrado:', component);
    return component;
}

// Función para depurar la estructura de datos
function debugDataStructure() {
    console.log('\n' + '='.repeat(60));
    console.log('DEPURACIÓN DE ESTRUCTURA DE DATOS');
    console.log('='.repeat(60));
    
    const widget = findCapitulosWidget();
    if (!widget) return;
    
    console.log('📊 Datos parseados:', widget.parsedData);
    console.log('📁 Capítulos:', widget.chapters);
    
    // Mostrar estructura detallada
    const data = widget.parsedData;
    for (const [chapterName, chapterData] of Object.entries(data || {})) {
        console.log(`\n📁 Capítulo: "${chapterName}"`);
        console.log(`   💰 Total: ${chapterData.total || 0}`);
        
        const sections = chapterData.sections || {};
        for (const [sectionName, sectionData] of Object.entries(sections)) {
            const linesCount = (sectionData.lines || []).length;
            console.log(`   📂 Sección: "${sectionName}" (${linesCount} productos)`);
            
            // Mostrar productos
            (sectionData.lines || []).forEach((line, index) => {
                console.log(`      ${index + 1}. ${line.name || 'Sin nombre'} (ID: ${line.id})`);
            });
        }
    }
}

// Función para simular la adición de un producto
function simulateAddProduct(chapterName, sectionName) {
    console.log('\n' + '='.repeat(60));
    console.log('SIMULACIÓN DE ADICIÓN DE PRODUCTO');
    console.log('='.repeat(60));
    
    const widget = findCapitulosWidget();
    if (!widget) return;
    
    console.log(`🎯 Intentando añadir producto a:`);
    console.log(`   📁 Capítulo: "${chapterName}"`);
    console.log(`   📂 Sección: "${sectionName}"`);
    
    // Verificar si el capítulo y sección existen
    const data = widget.parsedData;
    const chapter = data[chapterName];
    
    if (!chapter) {
        console.log(`❌ ERROR: Capítulo "${chapterName}" no encontrado`);
        console.log('📁 Capítulos disponibles:');
        Object.keys(data).forEach(name => console.log(`   - "${name}"`));
        return;
    }
    
    const section = chapter.sections?.[sectionName];
    if (!section) {
        console.log(`❌ ERROR: Sección "${sectionName}" no encontrada en capítulo "${chapterName}"`);
        console.log('📂 Secciones disponibles:');
        Object.keys(chapter.sections || {}).forEach(name => console.log(`   - "${name}"`));
        return;
    }
    
    console.log('✅ Capítulo y sección encontrados');
    console.log('🚀 Llamando a addProductToSection...');
    
    // Llamar al método del widget
    if (typeof widget.addProductToSection === 'function') {
        widget.addProductToSection(chapterName, sectionName);
    } else {
        console.log('❌ Método addProductToSection no encontrado');
    }
}

// Función para verificar la correspondencia entre frontend y backend
function checkFrontendBackendSync() {
    console.log('\n' + '='.repeat(60));
    console.log('VERIFICACIÓN FRONTEND-BACKEND');
    console.log('='.repeat(60));
    
    const widget = findCapitulosWidget();
    if (!widget) return;
    
    // Obtener datos del frontend
    const frontendData = widget.parsedData;
    console.log('🖥️  Datos del frontend:', frontendData);
    
    // Obtener el ID del pedido
    const orderId = widget.props.record.resId;
    console.log(`📋 ID del pedido: ${orderId}`);
    
    // Aquí podrías hacer una llamada al backend para comparar
    console.log('💡 Para verificar el backend, ejecute en la consola de Odoo:');
    console.log(`   debug_capitulos_structure(${orderId})`);
}

// Función para monitorear cambios en tiempo real
function monitorChanges() {
    console.log('\n' + '='.repeat(60));
    console.log('MONITOR DE CAMBIOS EN TIEMPO REAL');
    console.log('='.repeat(60));
    
    const widget = findCapitulosWidget();
    if (!widget) return;
    
    let lastData = JSON.stringify(widget.parsedData);
    
    const monitor = setInterval(() => {
        const currentData = JSON.stringify(widget.parsedData);
        if (currentData !== lastData) {
            console.log('🔄 CAMBIO DETECTADO en los datos del widget');
            console.log('📊 Nuevos datos:', widget.parsedData);
            lastData = currentData;
        }
    }, 1000);
    
    console.log('👁️  Monitor iniciado. Para detener, ejecute: clearInterval(' + monitor + ')');
    return monitor;
}

// Función principal de depuración
function debugSectionIssue() {
    console.log('🔧 INICIANDO DEPURACIÓN DEL PROBLEMA DE SECCIONES');
    
    // Verificar que estamos en la página correcta
    if (!window.location.href.includes('sale.order')) {
        console.log('⚠️  Advertencia: No parece que esté en una vista de pedido de venta');
    }
    
    // Ejecutar depuraciones
    debugDataStructure();
    checkFrontendBackendSync();
    
    console.log('\n📝 FUNCIONES DISPONIBLES:');
    console.log('   - debugDataStructure() - Muestra la estructura de datos');
    console.log('   - simulateAddProduct("Capítulo", "Sección") - Simula añadir producto');
    console.log('   - checkFrontendBackendSync() - Verifica sincronización');
    console.log('   - monitorChanges() - Monitorea cambios en tiempo real');
    console.log('   - findCapitulosWidget() - Encuentra el widget');
}

// Exponer funciones globalmente
window.debugSectionIssue = {
    main: debugSectionIssue,
    debugData: debugDataStructure,
    simulate: simulateAddProduct,
    checkSync: checkFrontendBackendSync,
    monitor: monitorChanges,
    findWidget: findCapitulosWidget
};

// Ejecutar automáticamente si se carga el script
if (typeof window !== 'undefined') {
    console.log('🔧 Script de depuración de secciones cargado');
    console.log('📝 Ejecute debugSectionIssue.main() para iniciar la depuración');
    console.log('📝 O use las funciones individuales desde debugSectionIssue.*');
}