/**
 * Script para probar la adición de productos desde la consola del navegador
 * Ejecutar en la consola del navegador (F12 -> Console) cuando esté en la página del pedido
 */

window.testAddProduct = {
    
    /**
     * Función principal para probar la adición de productos
     */
    async main() {
        console.log('=== INICIANDO PRUEBA DE ADICIÓN DE PRODUCTO ===');
        
        try {
            // Verificar que estamos en la página correcta
            if (!this.isOnSaleOrderPage()) {
                console.error('❌ No estamos en una página de pedido de venta');
                return false;
            }
            
            console.log('✅ Estamos en una página de pedido de venta');
            
            // Buscar el widget de capítulos
            const widget = this.findCapitulosWidget();
            if (!widget) {
                console.error('❌ No se encontró el widget de capítulos');
                return false;
            }
            
            console.log('✅ Widget de capítulos encontrado');
            
            // Obtener datos del widget
            const data = this.getWidgetData(widget);
            if (!data) {
                console.error('❌ No se pudieron obtener los datos del widget');
                return false;
            }
            
            console.log('✅ Datos del widget obtenidos:', data);
            
            // Buscar capítulos y secciones
            const chapters = Object.keys(data);
            if (chapters.length === 0) {
                console.error('❌ No hay capítulos disponibles');
                return false;
            }
            
            console.log(`✅ Capítulos encontrados (${chapters.length}):`, chapters);
            
            // Buscar secciones en el primer capítulo
            const firstChapter = chapters[0];
            const sections = Object.keys(data[firstChapter].sections || {});
            
            if (sections.length === 0) {
                console.error('❌ No hay secciones disponibles en el primer capítulo');
                return false;
            }
            
            console.log(`✅ Secciones encontradas en '${firstChapter}' (${sections.length}):`, sections);
            
            // Buscar una sección que no sea "CONDICIONES PARTICULARES"
            const targetSection = sections.find(s => s !== 'CONDICIONES PARTICULARES');
            
            if (!targetSection) {
                console.error('❌ No hay secciones válidas para añadir productos');
                return false;
            }
            
            console.log(`✅ Sección objetivo: '${targetSection}'`);
            
            // Simular la adición de un producto
            return await this.simulateAddProduct(widget, firstChapter, targetSection);
            
        } catch (error) {
            console.error('❌ Error en main:', error);
            return false;
        }
    },
    
    /**
     * Verifica si estamos en una página de pedido de venta
     */
    isOnSaleOrderPage() {
        return window.location.href.includes('sale.order') || 
               document.querySelector('[data-model="sale.order"]') !== null ||
               document.querySelector('.o_form_view') !== null;
    },
    
    /**
     * Busca el widget de capítulos en la página
     */
    findCapitulosWidget() {
        // Buscar por diferentes selectores posibles
        const selectors = [
            '.capitulos-accordion-widget',
            '[data-widget="capitulos_accordion"]',
            '.o_field_widget[data-field-name="capitulos_agrupados"]'
        ];
        
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                return element;
            }
        }
        
        // Buscar en el DOM por texto característico
        const elements = document.querySelectorAll('*');
        for (const el of elements) {
            if (el.textContent && el.textContent.includes('Añadir Producto')) {
                return el.closest('.o_field_widget') || el;
            }
        }
        
        return null;
    },
    
    /**
     * Obtiene los datos del widget
     */
    getWidgetData(widget) {
        try {
            // Intentar obtener datos del widget de Odoo
            if (widget.__owl__ && widget.__owl__.component) {
                const component = widget.__owl__.component;
                if (component.parsedData) {
                    return component.parsedData;
                }
            }
            
            // Buscar datos en atributos
            const dataAttr = widget.getAttribute('data-capitulos');
            if (dataAttr) {
                return JSON.parse(dataAttr);
            }
            
            // Buscar en elementos script cercanos
            const scripts = widget.querySelectorAll('script');
            for (const script of scripts) {
                if (script.textContent.includes('parsedData')) {
                    const match = script.textContent.match(/parsedData\s*=\s*({.*?});/);
                    if (match) {
                        return JSON.parse(match[1]);
                    }
                }
            }
            
            return null;
            
        } catch (error) {
            console.error('Error obteniendo datos del widget:', error);
            return null;
        }
    },
    
    /**
     * Simula la adición de un producto
     */
    async simulateAddProduct(widget, chapterName, sectionName) {
        console.log(`\n=== SIMULANDO ADICIÓN DE PRODUCTO ===`);
        console.log(`Capítulo: '${chapterName}'`);
        console.log(`Sección: '${sectionName}'`);
        
        try {
            // Buscar el botón "Añadir Producto" para esta sección
            const addButton = this.findAddProductButton(widget, chapterName, sectionName);
            
            if (!addButton) {
                console.error('❌ No se encontró el botón "Añadir Producto"');
                return false;
            }
            
            console.log('✅ Botón "Añadir Producto" encontrado');
            
            // Simular click en el botón
            console.log('🔄 Simulando click en "Añadir Producto"...');
            addButton.click();
            
            // Esperar a que aparezca el diálogo de selección
            await this.waitForProductDialog();
            
            return true;
            
        } catch (error) {
            console.error('❌ Error simulando adición:', error);
            return false;
        }
    },
    
    /**
     * Busca el botón "Añadir Producto" para una sección específica
     */
    findAddProductButton(widget, chapterName, sectionName) {
        const buttons = widget.querySelectorAll('button');
        
        for (const button of buttons) {
            if (button.textContent.includes('Añadir Producto')) {
                // Verificar si está en la sección correcta
                const section = button.closest('[data-section]');
                if (section) {
                    const sectionAttr = section.getAttribute('data-section');
                    if (sectionAttr === sectionName) {
                        return button;
                    }
                }
                
                // Buscar por proximidad de texto
                const parent = button.closest('.section, .capitulo-section, [class*="section"]');
                if (parent && parent.textContent.includes(sectionName)) {
                    return button;
                }
            }
        }
        
        return null;
    },
    
    /**
     * Espera a que aparezca el diálogo de selección de productos
     */
    async waitForProductDialog(timeout = 5000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const dialog = document.querySelector('.modal, .o_dialog, [role="dialog"]');
            if (dialog && dialog.textContent.includes('Seleccionar Producto')) {
                console.log('✅ Diálogo de selección de productos apareció');
                return dialog;
            }
            
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        console.error('❌ El diálogo de selección no apareció en el tiempo esperado');
        return null;
    },
    
    /**
     * Función de utilidad para inspeccionar el DOM
     */
    inspectDOM() {
        console.log('=== INSPECCIÓN DEL DOM ===');
        
        // Buscar elementos relacionados con capítulos
        const capitulosElements = document.querySelectorAll('*[class*="capitulo"], *[data*="capitulo"]');
        console.log(`Elementos con 'capitulo': ${capitulosElements.length}`);
        capitulosElements.forEach((el, i) => {
            console.log(`  ${i + 1}. ${el.tagName} - ${el.className} - ${el.textContent.substring(0, 50)}...`);
        });
        
        // Buscar botones
        const buttons = document.querySelectorAll('button');
        const addButtons = Array.from(buttons).filter(b => b.textContent.includes('Añadir'));
        console.log(`\nBotones con 'Añadir': ${addButtons.length}`);
        addButtons.forEach((btn, i) => {
            console.log(`  ${i + 1}. ${btn.textContent.trim()}`);
        });
        
        // Buscar widgets de Odoo
        const widgets = document.querySelectorAll('.o_field_widget');
        console.log(`\nWidgets de Odoo: ${widgets.length}`);
        widgets.forEach((widget, i) => {
            const fieldName = widget.getAttribute('data-field-name');
            if (fieldName) {
                console.log(`  ${i + 1}. Campo: ${fieldName}`);
            }
        });
    }
};

// Mensaje de ayuda
console.log(`
🔧 HERRAMIENTAS DE PRUEBA DISPONIBLES:

1. testAddProduct.main() - Ejecuta la prueba completa
2. testAddProduct.inspectDOM() - Inspecciona el DOM
3. testAddProduct.findCapitulosWidget() - Busca el widget

Ejemplo de uso:
  testAddProduct.main()
`);