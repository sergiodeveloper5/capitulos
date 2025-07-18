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
            
            // Obtener la categoría de la sección
            const data = this.parsedData;
            let categoryId = null;
            
            if (data && data[chapterName] && data[chapterName].sections && data[chapterName].sections[sectionName]) {
                categoryId = data[chapterName].sections[sectionName].category_id;
                console.log('DEBUG: Categoría de la sección:', categoryId);
            }
            
            // Debug: Mostrar todos los capítulos y secciones disponibles
            console.log('DEBUG: Capítulos disponibles en parsedData:');
            for (const [capName, capData] of Object.entries(data || {})) {
                console.log(`DEBUG: - Capítulo: '${capName}'`);
                for (const [secName, secData] of Object.entries(capData.sections || {})) {
                    console.log(`DEBUG:   - Sección: '${secName}' (categoría: ${secData.category_id || 'ninguna'})`);
                }
            }
            
            // Abrir el diálogo de selección de productos con filtro de categoría
            const productId = await this.openProductSelector(categoryId);
            
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

    async openProductSelector(categoryId = null) {
        return new Promise((resolve) => {
            this.dialog.add(ProductSelectorDialog, {
                title: _t("Seleccionar Producto"),
                onConfirm: (product) => {
                    resolve(product.id);
                },
                onCancel: () => {
                    resolve(null);
                },
                close: () => {}
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
    static template = "capitulos.ProductSelectorDialog";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        onConfirm: Function,
        onCancel: Function,
        close: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            step: "category", // Siempre empezar por categoría
            
            // Para categorías
            categorySearchTerm: "",
            categories: [],
            selectedCategory: null,
            loadingCategories: false,
            showCategoryDropdown: false,
            categoryError: null,
            
            // Para productos
            productSearchTerm: "",
            products: [],
            selectedProduct: null,
            loadingProducts: false,
        });
        
        // NO cargar categorías automáticamente - solo cuando el usuario interactúe
        
        // Bind para manejar clicks fuera del dropdown
        this.handleClickOutside = this.handleClickOutside.bind(this);
    }

    mounted() {
        document.addEventListener('click', this.handleClickOutside);
    }

    willUnmount() {
        document.removeEventListener('click', this.handleClickOutside);
        if (this.categorySearchTimeout) {
            clearTimeout(this.categorySearchTimeout);
        }
        if (this.productSearchTimeout) {
            clearTimeout(this.productSearchTimeout);
        }
    }

    handleClickOutside(event) {
        // Verificar si el clic fue dentro del componente del selector de categorías
        const categorySelector = event.target.closest('#category-selector, .dropdown-menu');
        const chevronIcon = event.target.closest('.fa-chevron-down, .fa-chevron-up');
        
        // Si el clic no fue en el selector de categorías ni en el icono de chevron, cerrar el dropdown
        if (!categorySelector && !chevronIcon && this.state.showCategoryDropdown) {
            this.state.showCategoryDropdown = false;
        }
    }

    async loadCategories() {
        this.state.loadingCategories = true;
        try {
            const categories = await this.orm.call(
                'product.category',
                'search_read',
                [[], ['name', 'parent_id', 'product_count']],
                { limit: 100 }
            );
            
            // Filtrar categorías base de Odoo
            this.state.categories = this.filterOdooBaseCategories(categories);
        } catch (error) {
            console.error('Error al cargar categorías:', error);
            this.notification.add('Error al cargar las categorías', { type: 'danger' });
        } finally {
            this.state.loadingCategories = false;
        }
    }

    // Método para filtrar categorías base de Odoo
    filterOdooBaseCategories(categories) {
        return categories.filter(category => {
            // Excluir categorías que sean exactamente "All"
            if (category.name === 'All') {
                return false;
            }
            
            // Excluir categorías que empiecen con "All /"
            if (category.name.startsWith('All /')) {
                return false;
            }
            
            // Excluir categorías que tengan como padre "All" o cualquier subcategoría de "All"
            if (category.parent_id) {
                const parentName = category.parent_id[1];
                if (parentName === 'All' || parentName.startsWith('All /')) {
                    return false;
                }
            }
            
            // Lista específica de categorías base a excluir
            const baseCategoriesToExclude = [
                'All',
                'Deliveries', 
                'Sales',
                'Purchase',
                'Expenses',
                'Saleable',
                'Consumable',
                'Service',
                'Storable Product',
                'All / Deliveries',
                'All / Sales',
                'All / Purchase',
                'All / Expenses',
                'All / Saleable',
                'All / Consumable',
                'All / Service',
                'All / Storable Product'
            ];
            
            if (baseCategoriesToExclude.includes(category.name)) {
                return false;
            }
            
            return true;
        });
    }

    showCategoryDropdown() {
        this.state.showCategoryDropdown = true;
        this.state.categoryError = null;
        
        // Focus en el campo de búsqueda después de un pequeño delay
        setTimeout(() => {
            const searchInput = this.el?.querySelector('#category-selector');
            if (searchInput) {
                searchInput.focus();
            }
        }, 100);
    }

    showCategoryDropdownWithLoad() {
        this.state.showCategoryDropdown = true;
        this.state.categoryError = null;
        
        // Si no hay categorías cargadas, cargarlas automáticamente
        if (this.state.categories.length === 0 && !this.state.loadingCategories) {
            this.loadCategories();
        }
        
        // Focus en el campo de búsqueda después de un pequeño delay
        setTimeout(() => {
            const searchInput = this.el?.querySelector('#category-selector');
            if (searchInput) {
                searchInput.focus();
            }
        }, 100);
    }

    hideCategoryDropdown() {
        this.state.showCategoryDropdown = false;
    }

    toggleCategoryDropdown() {
        if (this.state.showCategoryDropdown) {
            this.hideCategoryDropdown();
        } else {
            this.showCategoryDropdownWithLoad();
        }
    }

    async onCategorySearchInput(event) {
        const searchTerm = event.target.value;
        this.state.categorySearchTerm = searchTerm;
        
        // Si hay una categoría seleccionada y el usuario está escribiendo algo diferente, deseleccionarla
        if (this.state.selectedCategory && searchTerm !== this.state.selectedCategory.name) {
            this.state.selectedCategory = null;
        }
        
        // Mostrar el dropdown si no está visible
        if (!this.state.showCategoryDropdown) {
            this.state.showCategoryDropdown = true;
        }
        
        // Debounce la búsqueda
        clearTimeout(this.categorySearchTimeout);
        this.categorySearchTimeout = setTimeout(() => {
            if (searchTerm.length === 0) {
                // Si no hay término de búsqueda, cargar todas las categorías
                this.loadCategories();
            } else {
                // Buscar categorías que coincidan con el término
                this.searchCategories(searchTerm);
            }
        }, 300);
    }

    async searchCategories(searchTerm) {
        this.state.loadingCategories = true;
        try {
            const domain = [['name', 'ilike', searchTerm]];
            const categories = await this.orm.call(
                'product.category',
                'search_read',
                [domain, ['name', 'parent_id', 'product_count']],
                { limit: 50 }
            );
            
            // Filtrar categorías base de Odoo
            this.state.categories = this.filterOdooBaseCategories(categories);
        } catch (error) {
            console.error('Error al buscar categorías:', error);
            this.notification.add('Error al buscar categorías', { type: 'danger' });
        } finally {
            this.state.loadingCategories = false;
        }
    }

    selectCategory(category) {
        this.state.selectedCategory = category;
    }

    async selectCategoryFromDropdown(category) {
        this.state.selectedCategory = category;
        this.state.categorySearchTerm = category.name;
        this.state.showCategoryDropdown = false;
        this.state.categoryError = null;
        
        // Limpiar estado de productos y cargar automáticamente los productos de la categoría seleccionada
        this.state.productSearchTerm = "";
        this.state.products = [];
        this.state.selectedProduct = null;
        
        // Cargar productos de la categoría seleccionada
        await this.loadProductsByCategory();
    }

    async proceedToProducts() {
        if (!this.state.selectedCategory) {
            this.state.categoryError = 'Debe seleccionar una categoría';
            this.notification.add('Debe seleccionar una categoría', { type: 'warning' });
            return;
        }
        
        this.state.step = "product";
        this.state.productSearchTerm = "";
        this.state.products = [];
        this.state.selectedProduct = null;
        
        // Cargar productos de la categoría seleccionada
        await this.loadProductsByCategory();
    }

    async loadProductsByCategory(searchTerm = '') {
        this.state.loadingProducts = true;
        try {
            const domain = [
                ['categ_id', '=', this.state.selectedCategory.id],
                ['sale_ok', '=', true]
            ];
            
            // Si hay término de búsqueda, añadirlo al dominio
            if (searchTerm.trim()) {
                domain.push(['name', 'ilike', searchTerm.trim()]);
            }
            
            const products = await this.orm.call(
                'product.product',
                'search_read',
                [domain, ['name', 'default_code', 'categ_id', 'list_price', 'uom_id']],
                { limit: 100 }
            );
            this.state.products = products;
            
        } catch (error) {
            console.error('Error al cargar productos:', error);
            this.notification.add('Error al cargar los productos', { type: 'danger' });
        } finally {
            this.state.loadingProducts = false;
        }
    }

    async onProductSearchInput(event) {
        const searchTerm = event.target.value;
        this.state.productSearchTerm = searchTerm;
        
        // Debounce la búsqueda
        clearTimeout(this.productSearchTimeout);
        this.productSearchTimeout = setTimeout(() => {
            if (searchTerm.trim()) {
                this.loadProductsByCategory(searchTerm);
            } else {
                // Si no hay término de búsqueda, cargar todos los productos de la categoría
                this.loadProductsByCategory();
            }
        }, 300);
    }

    async searchProductsInCategory(searchTerm) {
        // Usar el método unificado loadProductsByCategory
        await this.loadProductsByCategory(searchTerm);
    }

    selectProduct(product) {
        this.state.selectedProduct = product;
    }

    goBackToCategories() {
        this.state.step = "category";
        this.state.productSearchTerm = "";
        this.state.products = [];
        this.state.selectedProduct = null;
    }

    onConfirm() {
        if (this.state.selectedProduct) {
            this.props.onConfirm(this.state.selectedProduct);
            this.props.close();
        }
    }

    onCancel() {
        this.props.onCancel();
        this.props.close();
    }
}

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