/** @odoo-module **/

/**
 * WIDGET ACORDEÓN DE CAPÍTULOS TÉCNICOS
 * =====================================
 * 
 * Widget personalizado para Odoo que proporciona una interfaz de acordeón
 * interactiva para la gestión de capítulos técnicos en presupuestos de venta.
 * 
 * FUNCIONALIDADES PRINCIPALES:
 * - Visualización jerárquica de capítulos, secciones y líneas
 * - Colapso/expansión de capítulos individuales
 * - Edición inline de líneas de productos
 * - Búsqueda y adición de productos por categoría
 * - Integración completa con el ORM de Odoo
 * - Interfaz responsive y moderna
 * 
 * ESTRUCTURA DE DATOS:
 * El widget espera recibir datos en formato JSON con la siguiente estructura:
 * {
 *   "Capítulo 1": {
 *     "sections": {
 *       "Sección A": {
 *         "lines": [
 *           {
 *             "id": 123,
 *             "product_name": "Producto X",
 *             "quantity": 2.0,
 *             "price_unit": 100.0,
 *             "price_subtotal": 200.0
 *           }
 *         ]
 *       }
 *     }
 *   }
 * }
 * 
 * COMPONENTES INTEGRADOS:
 * - Modal de búsqueda de productos
 * - Selector de categorías con autocompletado
 * - Editor inline de líneas
 * - Sistema de notificaciones
 * - Validaciones de datos
 * 
 * EVENTOS MANEJADOS:
 * - Colapso/expansión de capítulos
 * - Edición de líneas de productos
 * - Búsqueda de productos y categorías
 * - Adición de productos a secciones
 * - Guardado automático de cambios
 * 
 * DEPENDENCIAS:
 * - @web/core/utils/hooks (useState, useService)
 * - @web/views/fields/field (standardFieldProps)
 * - @web/core/l10n/translation (_t)
 * - @web/core/registry (registry)
 * 
 * @author: Sergio Vadillo
 * @version: 18.0.1.1.0
 * @since: 2024
 * @license: LGPL-3
 */

import { Component } from "@odoo/owl";
import { useState, useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/field";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

/**
 * CLASE PRINCIPAL DEL WIDGET ACORDEÓN
 * ==================================
 * 
 * Componente principal que maneja toda la lógica del acordeón de capítulos,
 * incluyendo la visualización, interacción y comunicación con el backend.
 */
class CapitulosAccordionWidget extends Component {
    static template = "capitulos.CapitulosAccordionWidget";
    static props = {
        ...standardFieldProps,
    };

    /**
     * CONSTRUCTOR Y CONFIGURACIÓN INICIAL
     * ==================================
     * 
     * Inicializa el estado del componente y configura los servicios necesarios
     * para la comunicación con Odoo (ORM, notificaciones, etc.)
     */
    setup() {
        // ===================================
        // SERVICIOS DE ODOO
        // ===================================
        
        this.orm = useService("orm");           // Servicio ORM para consultas a BD
        this.notification = useService("notification"); // Servicio de notificaciones
        
        // ===================================
        // ESTADO DEL COMPONENTE
        // ===================================
        
        this.state = useState({
            // --- Estado de capítulos ---
            collapsedChapters: {},              // Capítulos colapsados {nombre: boolean}
            
            // --- Estado de edición ---
            editingLine: null,                  // ID de línea en edición
            editingData: {},                    // Datos temporales de edición
            
            // --- Estado del modal de productos ---
            showProductModal: false,            // Visibilidad del modal
            currentChapter: null,               // Capítulo actual para añadir producto
            currentSection: null,               // Sección actual para añadir producto
            step: "category",                   // Paso actual: "category" o "product"
            
            // --- Estado de categorías ---
            categories: [],                     // Lista de categorías cargadas
            loadingCategories: false,           // Flag de carga de categorías
            selectedCategory: null,             // Categoría seleccionada
            showCategoryDropdown: false,        // Visibilidad del dropdown
            categorySearchTerm: "",             // Término de búsqueda de categorías
            categoryError: null,                // Error en carga de categorías
            
            // --- Estado de productos ---
            products: [],                       // Lista de productos cargados
            loadingProducts: false,             // Flag de carga de productos
            productSearchTerm: "",              // Término de búsqueda de productos
            productError: null,                 // Error en carga de productos
        });
        
        // ===================================
        // TIMEOUTS PARA DEBOUNCING
        // ===================================
        
        this.categorySearchTimeout = null;     // Timeout para búsqueda de categorías
        this.productSearchTimeout = null;      // Timeout para búsqueda de productos
    }

    // ===================================
    // PROPIEDADES COMPUTADAS
    // ===================================

    /**
     * DATOS PARSEADOS DEL CAMPO
     * ========================
     * 
     * Convierte el valor del campo (string JSON) en un objeto JavaScript
     * para su manipulación en el componente.
     * 
     * @returns {Object|null} Datos parseados o null si hay error
     */
    get parsedData() {
        try {
            const value = this.props.record.data[this.props.name];
            return value ? JSON.parse(value) : {};
        } catch (error) {
            console.error("Error parsing capitulos data:", error);
            return {};
        }
    }

    /**
     * LISTA DE CAPÍTULOS FORMATEADA
     * ============================
     * 
     * Convierte los datos parseados en una lista de capítulos con
     * estructura uniforme para el template.
     * 
     * @returns {Array} Lista de capítulos con formato:
     *   [{name: string, data: Object, id: string}]
     */
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

    // ===================================
    // MÉTODOS DE UTILIDAD
    // ===================================

    /**
     * OBTENER SECCIONES DE UN CAPÍTULO
     * ===============================
     * 
     * Extrae y formatea las secciones de un capítulo específico.
     * 
     * @param {Object} chapter - Datos del capítulo
     * @returns {Array} Lista de secciones formateadas
     */
    getSections(chapter) {
        return Object.keys(chapter.sections || {}).map((sectionName) => ({
            name: sectionName,
            lines: chapter.sections[sectionName].lines || []
        }));
    }

    /**
     * VERIFICAR SI CAPÍTULO ESTÁ COLAPSADO
     * ===================================
     * 
     * @param {string} chapterName - Nombre del capítulo
     * @returns {boolean} True si está colapsado
     */
    isChapterCollapsed(chapterName) {
        return this.state.collapsedChapters[chapterName] || false;
    }

    // ===================================
    // GESTIÓN DE CAPÍTULOS
    // ===================================

    /**
     * ALTERNAR ESTADO DE CAPÍTULO
     * ==========================
     * 
     * Cambia el estado de colapso/expansión de un capítulo específico.
     * 
     * @param {string} chapterName - Nombre del capítulo a alternar
     */
    toggleChapter(chapterName) {
        this.state.collapsedChapters[chapterName] = !this.state.collapsedChapters[chapterName];
    }

    // ===================================
    // GESTIÓN DE EDICIÓN DE LÍNEAS
    // ===================================

    /**
     * INICIAR EDICIÓN DE LÍNEA
     * =======================
     * 
     * Activa el modo de edición para una línea específica,
     * guardando los datos actuales como backup.
     * 
     * @param {number} lineId - ID de la línea a editar
     */
    startEdit(lineId) {
        const line = this.findLineById(lineId);
        if (line) {
            this.state.editingLine = lineId;
            this.state.editingData = {
                quantity: line.quantity || 0,
                price_unit: line.price_unit || 0
            };
        }
    }

    /**
     * CANCELAR EDICIÓN
     * ===============
     * 
     * Cancela la edición actual y restaura el estado original.
     */
    cancelEdit() {
        this.state.editingLine = null;
        this.state.editingData = {};
    }

    /**
     * ACTUALIZAR DATOS DE EDICIÓN
     * ==========================
     * 
     * Actualiza los datos temporales durante la edición.
     * 
     * @param {string} field - Campo a actualizar ('quantity' o 'price_unit')
     * @param {number} value - Nuevo valor
     */
    updateEditData(field, value) {
        this.state.editingData[field] = parseFloat(value) || 0;
    }

    /**
     * GUARDAR EDICIÓN
     * ==============
     * 
     * Guarda los cambios realizados en la línea editada,
     * actualizando tanto el frontend como el backend.
     */
    async saveEdit() {
        if (!this.state.editingLine) {
            return;
        }
        
        try {
            const lineId = this.state.editingLine;
            const editData = this.state.editingData;
            
            // ===================================
            // ACTUALIZACIÓN EN BACKEND
            // ===================================
            
            await this.orm.call(
                'sale.order.line',
                'write',
                [[lineId], {
                    product_uom_qty: editData.quantity,
                    price_unit: editData.price_unit
                }]
            );
            
            // ===================================
            // ACTUALIZACIÓN EN FRONTEND
            // ===================================
            
            const line = this.findLineById(lineId);
            if (line) {
                line.quantity = editData.quantity;
                line.price_unit = editData.price_unit;
                line.price_subtotal = editData.quantity * editData.price_unit;
            }
            
            // ===================================
            // RECÁLCULO DEL PEDIDO
            // ===================================
            
            await this.orm.call(
                'sale.order',
                'write',
                [[this.props.record.resId], {}]
            );
            
            // ===================================
            // FINALIZACIÓN
            // ===================================
            
            this.cancelEdit();
            this.notification.add(_t("Línea actualizada correctamente"), { type: 'success' });
            
            // Recargar datos del registro
            await this.props.record.load();
            
        } catch (error) {
            console.error('Error al guardar edición:', error);
            this.notification.add(_t("Error al actualizar la línea"), { type: 'danger' });
        }
    }

    /**
     * ELIMINAR LÍNEA
     * =============
     * 
     * Elimina una línea específica del pedido.
     * 
     * @param {number} lineId - ID de la línea a eliminar
     */
    async deleteLine(lineId) {
        try {
            await this.orm.call(
                'sale.order.line',
                'unlink',
                [[lineId]]
            );
            
            this.notification.add(_t("Línea eliminada correctamente"), { type: 'success' });
            await this.props.record.load();
            
        } catch (error) {
            console.error('Error al eliminar línea:', error);
            this.notification.add(_t("Error al eliminar la línea"), { type: 'danger' });
        }
    }

    // ===================================
    // UTILIDADES DE BÚSQUEDA
    // ===================================

    /**
     * BUSCAR LÍNEA POR ID
     * ==================
     * 
     * Busca una línea específica en toda la estructura de datos.
     * 
     * @param {number} lineId - ID de la línea a buscar
     * @returns {Object|null} Línea encontrada o null
     */
    findLineById(lineId) {
        const data = this.parsedData;
        if (!data) {
            return null;
        }
        
        // Recorrer todos los capítulos y secciones
        for (const chapterName of Object.keys(data)) {
            const chapter = data[chapterName];
            if (chapter.sections) {
                for (const sectionName of Object.keys(chapter.sections)) {
                    const section = chapter.sections[sectionName];
                    if (section.lines) {
                        for (const line of section.lines) {
                            const currentLineId = line.id || line.line_id;
                            if (currentLineId == lineId) {
                                return line;
                            }
                        }
                    }
                }
            }
        }
        return null;
    }

    // ===================================
    // GESTIÓN DEL MODAL DE PRODUCTOS
    // ===================================

    /**
     * ABRIR MODAL DE PRODUCTOS
     * =======================
     * 
     * Abre el modal para añadir productos a una sección específica.
     * 
     * @param {string} chapterName - Nombre del capítulo
     * @param {string} sectionName - Nombre de la sección
     */
    openProductModal(chapterName, sectionName) {
        this.state.showProductModal = true;
        this.state.currentChapter = chapterName;
        this.state.currentSection = sectionName;
        this.state.step = "category";
        this.state.selectedCategory = null;
        this.state.products = [];
        this.state.productSearchTerm = "";
        this.state.categorySearchTerm = "";
        
        // Cargar categorías automáticamente
        this.loadCategories();
    }

    /**
     * CERRAR MODAL DE PRODUCTOS
     * ========================
     * 
     * Cierra el modal y resetea el estado relacionado.
     */
    closeProductModal() {
        this.state.showProductModal = false;
        this.state.currentChapter = null;
        this.state.currentSection = null;
        this.state.step = "category";
        this.state.selectedCategory = null;
        this.state.products = [];
        this.state.categories = [];
        this.state.productSearchTerm = "";
        this.state.categorySearchTerm = "";
        this.hideCategoryDropdown();
    }

    // ===================================
    // GESTIÓN DE CATEGORÍAS
    // ===================================

    /**
     * CARGAR CATEGORÍAS
     * ================
     * 
     * Carga la lista de categorías de productos desde el backend.
     * 
     * @param {string} searchTerm - Término de búsqueda opcional
     */
    async loadCategories(searchTerm = '') {
        this.state.loadingCategories = true;
        this.state.categoryError = null;
        
        try {
            let domain = [];
            if (searchTerm) {
                domain = [['name', 'ilike', searchTerm]];
            }
            
            const categories = await this.orm.call(
                'product.category',
                'search_read',
                [domain, ['name', 'parent_id', 'product_count']],
                { limit: 50 }
            );
            
            // Filtrar categorías base de Odoo que no son útiles
            this.state.categories = this.filterOdooBaseCategories(categories);
            
        } catch (error) {
            console.error('Error al cargar categorías:', error);
            this.state.categoryError = 'Error al cargar categorías';
            this.notification.add(_t("Error al cargar categorías"), { type: 'danger' });
        } finally {
            this.state.loadingCategories = false;
        }
    }

    /**
     * FILTRAR CATEGORÍAS BASE DE ODOO
     * ==============================
     * 
     * Filtra las categorías predeterminadas de Odoo que no son relevantes.
     * 
     * @param {Array} categories - Lista de categorías
     * @returns {Array} Categorías filtradas
     */
    filterOdooBaseCategories(categories) {
        const excludeNames = [
            'All',
            'Saleable',
            'Services',
            'Storable Product',
            'Consumable'
        ];
        
        return categories.filter(cat => 
            !excludeNames.includes(cat.name) && 
            cat.name !== 'All' &&
            !cat.name.startsWith('[')
        );
    }

    /**
     * MOSTRAR DROPDOWN DE CATEGORÍAS
     * =============================
     * 
     * Muestra el dropdown de categorías y enfoca el campo de búsqueda.
     */
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

    /**
     * MOSTRAR DROPDOWN CON CARGA AUTOMÁTICA
     * ====================================
     * 
     * Muestra el dropdown y carga categorías si no están cargadas.
     */
    showCategoryDropdownWithLoad() {
        this.state.showCategoryDropdown = true;
        this.state.categoryError = null;
        
        // Si no hay categorías cargadas, cargarlas automáticamente
        if (this.state.categories.length === 0 && !this.state.loadingCategories) {
            this.loadCategories();
        }
        
        // Focus en el campo de búsqueda
        setTimeout(() => {
            const searchInput = this.el?.querySelector('#category-selector');
            if (searchInput) {
                searchInput.focus();
            }
        }, 100);
    }

    /**
     * OCULTAR DROPDOWN DE CATEGORÍAS
     * =============================
     */
    hideCategoryDropdown() {
        this.state.showCategoryDropdown = false;
    }

    /**
     * MANEJAR ENTRADA DE BÚSQUEDA DE CATEGORÍAS
     * ========================================
     * 
     * Maneja la entrada de texto en el campo de búsqueda de categorías
     * con debouncing para optimizar las consultas.
     * 
     * @param {Event} event - Evento de entrada de texto
     */
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
                // Buscar categorías que coincidan
                this.searchCategories(searchTerm);
            }
        }, 300);
    }

    /**
     * BUSCAR CATEGORÍAS
     * ================
     * 
     * Realiza búsqueda específica de categorías por término.
     * 
     * @param {string} searchTerm - Término de búsqueda
     */
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

    /**
     * SELECCIONAR CATEGORÍA
     * ====================
     * 
     * Selecciona una categoría y procede al paso de selección de productos.
     * 
     * @param {Object} category - Categoría seleccionada
     */
    selectCategory(category) {
        this.state.selectedCategory = category;
    }

    // ===================================
    // GESTIÓN DE PRODUCTOS
    // ===================================

    /**
     * PROCEDER A SELECCIÓN DE PRODUCTOS
     * ================================
     * 
     * Avanza al paso de selección de productos y carga los productos
     * de la categoría seleccionada.
     */
    async proceedToProducts() {
        if (!this.state.selectedCategory) {
            this.notification.add(_t("Por favor seleccione una categoría"), { type: 'warning' });
            return;
        }
        
        this.state.step = "product";
        this.hideCategoryDropdown();
        await this.loadProductsByCategory();
    }

    /**
     * CARGAR PRODUCTOS POR CATEGORÍA
     * =============================
     * 
     * Carga los productos de la categoría seleccionada.
     * 
     * @param {string} searchTerm - Término de búsqueda opcional
     */
    async loadProductsByCategory(searchTerm = '') {
        if (!this.state.selectedCategory) {
            return;
        }
        
        this.state.loadingProducts = true;
        this.state.productError = null;
        
        try {
            let domain = [
                ['categ_id', '=', this.state.selectedCategory.id],
                ['sale_ok', '=', true]
            ];
            
            if (searchTerm) {
                domain.push(['name', 'ilike', searchTerm]);
            }
            
            const products = await this.orm.call(
                'product.product',
                'search_read',
                [domain, ['name', 'default_code', 'list_price', 'uom_id']],
                { limit: 50 }
            );
            
            this.state.products = products;
            
        } catch (error) {
            console.error('Error al cargar productos:', error);
            this.state.productError = 'Error al cargar productos';
            this.notification.add(_t("Error al cargar productos"), { type: 'danger' });
        } finally {
            this.state.loadingProducts = false;
        }
    }

    /**
     * MANEJAR ENTRADA DE BÚSQUEDA DE PRODUCTOS
     * =======================================
     * 
     * Maneja la búsqueda de productos con debouncing.
     * 
     * @param {Event} event - Evento de entrada de texto
     */
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

    /**
     * BUSCAR PRODUCTOS EN CATEGORÍA
     * =============================
     * 
     * Método auxiliar para búsqueda de productos.
     * 
     * @param {string} searchTerm - Término de búsqueda
     */
    async searchProductsInCategory(searchTerm) {
        // Usar el método unificado loadProductsByCategory
        await this.loadProductsByCategory(searchTerm);
    }

    /**
     * AÑADIR PRODUCTO A SECCIÓN
     * ========================
     * 
     * Añade un producto seleccionado a la sección actual.
     * 
     * @param {Object} product - Producto a añadir
     */
    async addProductToSection(product) {
        try {
            const result = await this.orm.call(
                'sale.order',
                'add_product_to_section',
                [this.props.record.resId],
                {
                    capitulo_name: this.state.currentChapter,
                    seccion_name: this.state.currentSection,
                    product_id: product.id,
                    quantity: 1.0
                }
            );
            
            if (result.success) {
                this.notification.add(_t("Producto añadido correctamente"), { type: 'success' });
                this.closeProductModal();
                await this.props.record.load();
            } else {
                this.notification.add(result.error || _t("Error al añadir producto"), { type: 'danger' });
            }
            
        } catch (error) {
            console.error('Error al añadir producto:', error);
            this.notification.add(_t("Error al añadir producto"), { type: 'danger' });
        }
    }

    /**
     * VOLVER A CATEGORÍAS
     * ==================
     * 
     * Regresa al paso de selección de categorías.
     */
    goBackToCategories() {
        this.state.step = "category";
        this.state.productSearchTerm = "";
        this.state.products = [];
    }
}

// ===================================
// REGISTRO DEL WIDGET
// ===================================

/**
 * REGISTRO EN EL SISTEMA DE WIDGETS DE ODOO
 * =========================================
 * 
 * Registra el widget en el registro de campos de Odoo para que
 * pueda ser utilizado en las vistas XML.
 */
registry.category("fields").add("capitulos_accordion", CapitulosAccordionWidget);