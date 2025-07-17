/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

export class CapitulosAccordionWidget extends Component {
    static template = "capitulos.CapitulosAccordionWidget";
    static props = {
        ...standardFieldProps,
    };
    static supportedTypes = ["text"];

    setup() {
        this.state = useState({ 
            collapsedChapters: {},
            editingLine: null,
            editValues: {},
            showProductDialog: false,
            currentSection: null,
            currentChapter: null,
            condicionesParticulares: {} // Objeto para almacenar condiciones por sección
        });
        
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    get parsedData() {
        try {
            return this.value ? JSON.parse(this.value) : {};
        } catch (e) {
            console.error('Error parsing capitulos data:', e);
            return {};
        }
    }

    get chapters() {
        const data = this.parsedData;
        if (!data || Object.keys(data).length === 0) {
            return [];
        }
        return Object.keys(data).map((chapterName, index) => ({
            name: chapterName,
            data: data[chapterName],
            id: `chapter_${index}`
        }));
    }

    toggleChapter(chapterName) {
        this.state.collapsedChapters = {
            ...this.state.collapsedChapters,
            [chapterName]: !this.state.collapsedChapters[chapterName]
        };
    }

    isChapterCollapsed(chapterName) {
        return this.state.collapsedChapters[chapterName] || false;
    }

    getSections(chapter) {
        return Object.keys(chapter.sections || {}).map((sectionName) => ({
            name: sectionName,
            lines: chapter.sections[sectionName].lines || []
        }));
    }

    formatCurrency(value) {
        return (value || 0).toFixed(2);
    }

    async addProductToSection(chapterName, sectionName) {
        try {
            console.log('DEBUG: addProductToSection llamado con:', {
                chapterName: chapterName,
                sectionName: sectionName,
                orderId: this.props.record.resId
            });
            
            // Debug: Mostrar todos los capítulos y secciones disponibles
            console.log('DEBUG: Capítulos disponibles en parsedData:');
            const data = this.parsedData;
            for (const [capName, capData] of Object.entries(data || {})) {
                console.log(`DEBUG: - Capítulo: '${capName}'`);
                for (const [secName, secData] of Object.entries(capData.sections || {})) {
                    console.log(`DEBUG:   - Sección: '${secName}'`);
                }
            }
            
            // Abrir el diálogo de selección de productos
            const productId = await this.openProductSelector();
            
            if (!productId) {
                console.log('DEBUG: No se seleccionó producto, cancelando');
                return;
            }
            
            console.log('DEBUG: Producto seleccionado:', productId);
            const orderId = this.props.record.resId;
            
            // Usar el método del modelo Python para añadir el producto
            console.log('DEBUG: Llamando al método add_product_to_section...');
            const result = await this.orm.call(
                'sale.order',
                'add_product_to_section',
                [orderId, chapterName, sectionName, productId, 1.0]
            );
            
            console.log('DEBUG: Resultado del método:', result);
            
            if (result && result.success) {
                console.log('DEBUG: Producto añadido exitosamente, recargando datos...');
                this.notification.add(
                    result.message || _t('Producto añadido correctamente'),
                    { type: 'success' }
                );
                
                // ESTRATEGIA DE RECARGA MEJORADA
                console.log('DEBUG: Iniciando recarga de datos...');
                
                // 1. Recargar el registro completo
                await this.props.record.load();
                console.log('DEBUG: Registro recargado');
                
                // 2. Forzar recálculo del modelo raíz si existe
                if (this.props.record.model && this.props.record.model.root) {
                    await this.props.record.model.root.load();
                    console.log('DEBUG: Modelo raíz recargado');
                }
                
                // 3. Forzar actualización del estado reactivo
                this.state.collapsedChapters = { ...this.state.collapsedChapters };
                
                // 4. Esperar un tick para que se procesen los cambios
                await new Promise(resolve => setTimeout(resolve, 100));
                
                // 5. Forzar re-renderizado del componente
                this.render();
                
                console.log('DEBUG: Datos después de recarga:', this.parsedData);
                console.log('DEBUG: Capítulos encontrados:', this.chapters.length);
                
                // Verificar si los datos se actualizaron correctamente
                const updatedData = this.parsedData;
                if (updatedData && Object.keys(updatedData).length > 0) {
                    console.log('DEBUG: ✅ Datos actualizados correctamente');
                    for (const [chapterName, chapterData] of Object.entries(updatedData)) {
                        console.log(`DEBUG: Capítulo '${chapterName}' tiene ${Object.keys(chapterData.sections || {}).length} secciones`);
                        for (const [sectionName, sectionData] of Object.entries(chapterData.sections || {})) {
                            console.log(`DEBUG: Sección '${sectionName}' tiene ${(sectionData.lines || []).length} productos`);
                        }
                    }
                } else {
                    console.log('DEBUG: ❌ Los datos siguen vacíos después de la recarga');
                }
                
            } else {
                console.log('DEBUG: Error en el resultado:', result);
                this.notification.add(
                    result?.error || result?.message || _t('Error al añadir el producto'),
                    { type: 'danger' }
                );
            }
            
        } catch (error) {
            console.error('DEBUG: Error al añadir producto:', error);
            this.notification.add(
                _t('Error al añadir producto a la sección: ') + (error.message || error),
                { type: 'danger' }
            );
        }
    }

    async openProductSelector() {
        return new Promise((resolve) => {
            this.dialog.add(ProductSelectorDialog, {
                title: _t("Seleccionar Producto"),
                orm: this.orm,
                onConfirm: (productId) => {
                    resolve(productId);
                },
                onCancel: () => {
                    resolve(null);
                }
            });
        });
    }

    // Métodos para edición inline
    startEditLine(lineId) {
        const line = this.findLineById(lineId);
        if (!line) {
            this.notification.add('Línea no encontrada', { type: 'danger' });
            return;
        }
        
        this.state.editingLine = lineId;
        this.state.editValues = {
            product_uom_qty: line.product_uom_qty || 0,
            price_unit: line.price_unit || 0,
            name: line.name || ''
        };
    }

    cancelEdit() {
        this.state.editingLine = null;
        this.state.editValues = {};
    }

    async saveEdit() {
        if (!this.state.editingLine) {
            return;
        }
        
        try {
            const lineId = this.state.editingLine;
            
            // Validar valores antes de guardar
            const quantity = parseFloat(this.state.editValues.product_uom_qty);
            const price = parseFloat(this.state.editValues.price_unit);
            
            if (isNaN(quantity) || quantity < 0) {
                this.notification.add(
                    _t('La cantidad debe ser un número válido mayor o igual a 0'),
                    { type: 'warning' }
                );
                return;
            }
            
            if (isNaN(price) || price < 0) {
                this.notification.add(
                    _t('El precio debe ser un número válido mayor o igual a 0'),
                    { type: 'warning' }
                );
                return;
            }
            
            const updateValues = {
                product_uom_qty: quantity,
                price_unit: price,
                name: this.state.editValues.name || ''
            };
            
            await this.orm.write('sale.order.line', [parseInt(lineId)], updateValues);
            
            this.notification.add(
                _t('Línea actualizada correctamente'),
                { type: 'success' }
            );
            
            this.state.editingLine = null;
            this.state.editValues = {};
            
            // Recargar los datos del widget
            await this.props.record.load();
            
        } catch (error) {
            console.error('Error al guardar:', error);
            this.notification.add(
                _t('Error al guardar los cambios'),
                { type: 'danger' }
            );
        }
    }

    updateEditValue(field, value) {
        this.state.editValues = {
            ...this.state.editValues,
            [field]: value
        };
    }

    async updateCondicionesParticulares(chapterName, sectionName, value) {
        try {
            const sectionKey = `${chapterName}::${sectionName}`;
            
            // Actualizar el estado local inmediatamente para respuesta rápida
            this.state.condicionesParticulares[sectionKey] = value;
            
            // Llamar al método del servidor para guardar
            const orderId = this.props.record.resId;
            await this.orm.call(
                'sale.order',
                'update_condiciones_particulares',
                [orderId, chapterName, sectionName, value]
            );
            
        } catch (error) {
            console.error('Error al actualizar condiciones particulares:', error);
            this.notification.add(
                _t('Error al guardar las condiciones particulares'),
                { type: 'danger' }
            );
        }
    }

    async deleteLine(lineId) {
        try {
            console.log('DEBUG: deleteLine llamado con lineId:', lineId);
            
            // Verificar que el lineId es válido
            if (!lineId || isNaN(parseInt(lineId))) {
                console.error('DEBUG: lineId inválido:', lineId);
                this.notification.add(_t('ID de línea inválido'), { type: 'danger' });
                return;
            }
            
            // Buscar información del producto para mostrar en la confirmación
            const line = this.findLineById(lineId);
            const productName = line ? line.name : 'Producto';
            
            // Confirmación con diálogo más elegante
              const confirmed = await new Promise((resolve) => {
                  this.dialog.add(DeleteConfirmDialog, {
                      title: _t("Confirmar eliminación"),
                      productName: productName,
                      onConfirm: () => resolve(true),
                      onCancel: () => resolve(false),
                  });
              });
            
            if (!confirmed) {
                console.log('DEBUG: Eliminación cancelada por el usuario');
                return;
            }
            
            console.log('DEBUG: Iniciando eliminación de línea ID:', parseInt(lineId));
            
            // Llamada directa sin contexto adicional
            await this.orm.call(
                'sale.order.line',
                'unlink',
                [[parseInt(lineId)]]
            );
            
            console.log('DEBUG: Eliminación exitosa');
            this.notification.add(_t('Línea eliminada correctamente'), { type: 'success' });
            
            // Recargar los datos
            await this.props.record.load();
            
        } catch (error) {
            console.error('DEBUG: Error al eliminar línea:', error);
            let errorMessage = 'Error desconocido';
            
            if (error.data && error.data.message) {
                errorMessage = error.data.message;
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            this.notification.add(_t('Error al eliminar la línea: ') + errorMessage, { type: 'danger' });
        }
    }

    findLineById(lineId) {
        const data = this.parsedData;
        if (!data) {
            return null;
        }
        
        for (const chapterName of Object.keys(data)) {
            const chapter = data[chapterName];
            if (chapter.sections) {
                for (const sectionName of Object.keys(chapter.sections)) {
                    const section = chapter.sections[sectionName];
                    if (section.lines) {
                        for (const line of section.lines) {
                            const currentLineId = line.id || line.line_id;
                            if (currentLineId && (currentLineId == lineId || currentLineId === lineId)) {
                                return line;
                            }
                        }
                    }
                }
            }
        }
        
        return null;
    }

    updateEditValue(field, value) {
        this.state.editValues = {
            ...this.state.editValues,
            [field]: value
        };
    }

    // Métodos para manejar las condiciones particulares
    updateCondicionesParticulares(chapterName, sectionName, value) {
        // Crear clave única para esta sección específica
        const sectionKey = `${chapterName}::${sectionName}`;
        
        // Guardar el valor en el estado local para esta sección específica
        this.state.condicionesParticulares[sectionKey] = value;
        
        // Log para depuración
        console.log(`Condiciones particulares actualizadas para ${sectionKey}:`, value);
        console.log('Estado completo de condiciones:', this.state.condicionesParticulares);
        
        // Guardar automáticamente en el servidor
        this.saveCondicionesParticulares(chapterName, sectionName, value);
    }

    async saveCondicionesParticulares(chapterName, sectionName, value) {
        try {
            const orderId = this.props.record.resId;
            console.log(`Guardando condiciones particulares para ${chapterName}::${sectionName}:`, value);
            
            await this.orm.call('sale.order', 'save_condiciones_particulares', [
                orderId, chapterName, sectionName, value
            ]);
            
            console.log('✅ Condiciones particulares guardadas correctamente');
        } catch (error) {
            console.error('❌ Error al guardar condiciones particulares:', error);
            this.notification.add(
                _t('Error al guardar las condiciones particulares'),
                { type: 'danger' }
            );
        }
    }

    getCondicionesParticulares(chapterName, sectionName) {
        // Crear clave única para esta sección específica
        const sectionKey = `${chapterName}::${sectionName}`;
        
        // Primero intentar obtener desde el estado local (cambios no guardados)
        if (this.state.condicionesParticulares[sectionKey] !== undefined) {
            return this.state.condicionesParticulares[sectionKey];
        }
        
        // Si no está en el estado local, obtener desde los datos del servidor
        const data = this.parsedData;
        if (data && data[chapterName] && data[chapterName].sections && data[chapterName].sections[sectionName]) {
            const serverValue = data[chapterName].sections[sectionName].condiciones_particulares || '';
            // Guardar en el estado local para futuras referencias
            this.state.condicionesParticulares[sectionKey] = serverValue;
            return serverValue;
        }
        
        // Retornar string vacío si no se encuentra en ningún lado
        return '';
    }
    
    // MÉTODO DE DEBUGGING - FORZAR ACTUALIZACIÓN MANUAL
    async forceRefresh() {
        console.log('🔄 FORCE REFRESH: Iniciando actualización forzada...');
        
        try {
            // Obtener datos frescos directamente del servidor
            const orderId = this.props.record.resId;
            console.log('🔄 FORCE REFRESH: Order ID:', orderId);
            
            // Llamar directamente al método computed
            await this.orm.call('sale.order', '_compute_capitulos_agrupados', [[orderId]]);
            console.log('🔄 FORCE REFRESH: Método computed ejecutado');
            
            // Recargar el registro
            await this.props.record.load();
            console.log('🔄 FORCE REFRESH: Registro recargado');
            
            // Verificar datos
            const newData = this.parsedData;
            console.log('🔄 FORCE REFRESH: Nuevos datos:', newData);
            console.log('🔄 FORCE REFRESH: Capítulos:', Object.keys(newData).length);
            
            // Forzar re-render
            this.render();
            
            console.log('🔄 FORCE REFRESH: ✅ Actualización completada');
            
        } catch (error) {
            console.error('🔄 FORCE REFRESH: ❌ Error:', error);
        }
    }
    
    // MÉTODO DE DEBUGGING - VERIFICAR ESTADO
    debugState() {
        console.log('🐛 DEBUG STATE: === ESTADO ACTUAL DEL WIDGET ===');
        console.log('🐛 DEBUG STATE: Record ID:', this.props.record.resId);
        console.log('🐛 DEBUG STATE: Raw data:', this.props.record.data.capitulos_agrupados);
        console.log('🐛 DEBUG STATE: Parsed data:', this.parsedData);
        console.log('🐛 DEBUG STATE: Chapters count:', this.chapters.length);
        console.log('🐛 DEBUG STATE: State:', this.state);
        
        // Verificar cada capítulo y sección
        const data = this.parsedData;
        if (data && Object.keys(data).length > 0) {
            for (const [chapterName, chapterData] of Object.entries(data)) {
                console.log(`🐛 DEBUG STATE: Capítulo '${chapterName}':`);
                console.log(`🐛 DEBUG STATE:   - Secciones: ${Object.keys(chapterData.sections || {}).length}`);
                
                for (const [sectionName, sectionData] of Object.entries(chapterData.sections || {})) {
                    const linesCount = (sectionData.lines || []).length;
                    console.log(`🐛 DEBUG STATE:   - Sección '${sectionName}': ${linesCount} productos`);
                    
                    if (linesCount > 0) {
                        sectionData.lines.forEach((line, idx) => {
                            console.log(`🐛 DEBUG STATE:     ${idx + 1}. ${line.name} (ID: ${line.id})`);
                        });
                    }
                }
            }
        } else {
            console.log('🐛 DEBUG STATE: ❌ No hay datos de capítulos');
        }
        
        console.log('🐛 DEBUG STATE: === FIN DEL ESTADO ===');
    }
}

// Diálogo para seleccionar productos
class ProductSelectorDialog extends Component {
    static props = {
        title: { type: String },
        orm: { type: Object },
        onConfirm: { type: Function },
        onCancel: { type: Function },
        close: { type: Function }
    };
    
    setup() {
        this.orm = this.props.orm;
        this.notification = useService("notification");
        this.state = useState({
            searchTerm: "",
            products: [],
            categories: [],
            selectedCategory: null,
            selectedProduct: null,
            loading: false,
            loadingCategories: false
        });
        
        // Cargar categorías al inicializar
        this.loadCategories();
    }

    async loadCategories() {
        this.state.loadingCategories = true;
        try {
            const categories = await this.orm.searchRead(
                'product.category',
                [],
                ['id', 'name', 'parent_id'],
                { order: 'name' }
            );
            this.state.categories = categories;
        } catch (error) {
            console.error('Error al cargar categorías:', error);
            this.notification.add(
                _t('Error al cargar categorías'),
                { type: 'danger' }
            );
        } finally {
            this.state.loadingCategories = false;
        }
    }

    async onCategoryChange(event) {
        const categoryId = parseInt(event.target.value);
        this.state.selectedCategory = categoryId || null;
        this.state.selectedProduct = null;
        this.state.products = [];
        this.state.searchTerm = "";
        
        // Si se selecciona una categoría, cargar productos automáticamente
        if (categoryId) {
            await this.searchProducts();
        }
    }

    async searchProducts() {
        if (!this.state.selectedCategory) {
            this.notification.add(
                _t('Por favor seleccione primero una categoría'),
                { type: 'warning' }
            );
            return;
        }

        this.state.loading = true;
        try {
            // Construir dominio de búsqueda
            let domain = [
                ['sale_ok', '=', true],
                ['categ_id', 'child_of', this.state.selectedCategory]
            ];
            
            // Añadir filtro de búsqueda por texto si existe
            if (this.state.searchTerm.trim()) {
                domain.push(['name', 'ilike', this.state.searchTerm.trim()]);
            }

            const products = await this.orm.searchRead(
                'product.product',
                domain,
                ['id', 'name', 'list_price', 'default_code'],
                { limit: 50, order: 'name' }
            );
            this.state.products = products;
        } catch (error) {
            console.error('Error al buscar productos:', error);
            this.notification.add(
                _t('Error al buscar productos'),
                { type: 'danger' }
            );
        } finally {
            this.state.loading = false;
        }
    }

    onSearchInput(event) {
        this.state.searchTerm = event.target.value;
        // Solo buscar si hay una categoría seleccionada
        if (this.state.selectedCategory) {
            this.searchProducts();
        }
    }

    selectProduct(product) {
        this.state.selectedProduct = product;
    }

    onConfirm() {
        if (this.state.selectedProduct) {
            this.props.onConfirm(this.state.selectedProduct.id);
            this.props.close();
        } else {
            this.notification.add(
                _t('Por favor seleccione un producto'),
                { type: 'warning' }
            );
        }
    }

    onCancel() {
        this.props.onCancel();
        this.props.close();
    }
}

ProductSelectorDialog.template = "capitulos.ProductSelectorDialog";
ProductSelectorDialog.components = { Dialog };

// Diálogo de confirmación para eliminar productos
class DeleteConfirmDialog extends Component {
    static props = {
        title: { type: String },
        productName: { type: String },
        onConfirm: { type: Function },
        onCancel: { type: Function },
        close: { type: Function }
    };
    
    onConfirm() {
        this.props.onConfirm();
        this.props.close();
    }

    onCancel() {
        this.props.onCancel();
        this.props.close();
    }
}

DeleteConfirmDialog.template = "capitulos.DeleteConfirmDialog";
DeleteConfirmDialog.components = { Dialog };

// Hacer el widget accesible globalmente para depuración
window.CapitulosAccordionWidget = CapitulosAccordionWidget;

registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});