/**
 * @fileoverview Widget de Acordeón para Gestión de Capítulos Técnicos
 * 
 * Este módulo implementa un widget personalizado para Odoo que permite la gestión
 * visual e interactiva de capítulos técnicos en pedidos de venta. Proporciona una
 * interfaz de acordeón con funcionalidades avanzadas de edición, búsqueda y
 * organización de productos por secciones.
 * 
 * @module CapitulosAccordionWidget
 * @author Sergio Vadillo
 * @version 18.0.1.1.0
 * @since 2024
 * @requires @odoo/owl
 * @requires @web/core/registry
 * @requires @web/views/fields/standard_field_props
 * @requires @web/core/utils/hooks
 * @requires @web/core/l10n/translation
 * @requires @web/core/dialog/dialog
 * 
 * @description
 * Características principales:
 * - Visualización en acordeón de capítulos y secciones
 * - Edición inline de productos con validación
 * - Búsqueda y selección de productos por categorías
 * - Gestión de condiciones particulares por sección
 * - Interfaz responsive y accesible
 * - Integración completa con el ORM de Odoo
 * - Notificaciones y confirmaciones de usuario
 * - Debugging y logging avanzado
 */

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

/**
 * Widget principal para la gestión de capítulos técnicos en pedidos de venta.
 * 
 * Este componente implementa una interfaz de acordeón que permite visualizar y gestionar
 * capítulos técnicos organizados por secciones, con funcionalidades completas de CRUD
 * para productos, edición inline, y gestión de condiciones particulares.
 * 
 * @class CapitulosAccordionWidget
 * @extends {Component}
 * 
 * @property {Object} state - Estado reactivo del componente
 * @property {Object} state.collapsedChapters - Capítulos colapsados/expandidos
 * @property {string|null} state.editingLine - ID de la línea en edición
 * @property {Object} state.editValues - Valores temporales durante la edición
 * @property {boolean} state.showProductDialog - Estado del diálogo de productos
 * @property {Object|null} state.currentSection - Sección actual seleccionada
 * @property {Object|null} state.currentChapter - Capítulo actual seleccionado
 * @property {Object} state.condicionesParticulares - Condiciones por sección
 * 
 * @example
 * // Uso en vista XML:
 * <field name="capitulos_agrupados" widget="capitulos_accordion"/>
 * 
 * @since 18.0.1.1.0
 */
export class CapitulosAccordionWidget extends Component {
    /** @static {string} Template QWeb asociado al componente */
    static template = "capitulos.CapitulosAccordionWidget";
    
    /** @static {Object} Propiedades del componente heredadas de standardFieldProps */
    static props = {
        ...standardFieldProps,
    };
    
    /** @static {string[]} Tipos de campo soportados por el widget */
    static supportedTypes = ["text"];

    /**
     * Configuración inicial del componente.
     * 
     * Inicializa el estado reactivo, servicios necesarios y configuraciones
     * del widget. Se ejecuta una vez durante el ciclo de vida del componente.
     * 
     * @method setup
     * @memberof CapitulosAccordionWidget
     * @returns {void}
     * 
     * @description
     * Servicios inicializados:
     * - orm: Para operaciones con la base de datos
     * - notification: Para mostrar notificaciones al usuario
     * - dialog: Para mostrar diálogos modales
     * 
     * Estado inicial:
     * - collapsedChapters: Objeto para controlar capítulos colapsados
     * - editingLine: Línea actualmente en edición (null por defecto)
     * - editValues: Valores temporales durante la edición
     * - showProductDialog: Control del diálogo de selección de productos
     * - currentSection/currentChapter: Referencias a elementos seleccionados
     * - condicionesParticulares: Almacén de condiciones por sección
     */
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
        
        // Inicialización de servicios Odoo
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
    }

    /**
     * Obtiene el valor actual del campo desde el registro.
     * 
     * @getter value
     * @memberof CapitulosAccordionWidget
     * @returns {string} Valor JSON del campo capitulos_agrupados
     */
    get value() {
        return this.props.record.data[this.props.name];
    }

    /**
     * Parsea y valida los datos JSON del campo.
     * 
     * @getter parsedData
     * @memberof CapitulosAccordionWidget
     * @returns {Object} Datos parseados o objeto vacío si hay error
     * 
     * @description
     * Convierte el string JSON almacenado en el campo a un objeto JavaScript.
     * En caso de error de parsing, retorna un objeto vacío y registra el error.
     */
    get parsedData() {
        try {
            return this.value ? JSON.parse(this.value) : {};
        } catch (e) {
            console.error('Error parsing capitulos data:', e);
            return {};
        }
    }

    /**
     * Transforma los datos parseados en una estructura de capítulos.
     * 
     * @getter chapters
     * @memberof CapitulosAccordionWidget
     * @returns {Array<Object>} Array de objetos capítulo con estructura normalizada
     * 
     * @description
     * Cada objeto capítulo contiene:
     * - name: Nombre del capítulo
     * - data: Datos completos del capítulo (secciones, totales, etc.)
     * - id: Identificador único para el template
     * 
     * @example
     * // Estructura de retorno:
     * [
     *   {
     *     name: "Capítulo 1",
     *     data: { sections: {...}, total: 1500.00 },
     *     id: "chapter_0"
     *   }
     * ]
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

    /**
     * Alterna el estado de colapso de un capítulo.
     * 
     * @method toggleChapter
     * @memberof CapitulosAccordionWidget
     * @param {string} chapterName - Nombre del capítulo a alternar
     * @returns {void}
     * 
     * @description
     * Cambia el estado de expansión/colapso del capítulo especificado.
     * El estado se mantiene en el objeto reactivo collapsedChapters.
     */
    toggleChapter(chapterName) {
        this.state.collapsedChapters = {
            ...this.state.collapsedChapters,
            [chapterName]: !this.state.collapsedChapters[chapterName]
        };
    }

    /**
     * Verifica si un capítulo está colapsado.
     * 
     * @method isChapterCollapsed
     * @memberof CapitulosAccordionWidget
     * @param {string} chapterName - Nombre del capítulo a verificar
     * @returns {boolean} true si está colapsado, false si está expandido
     */
    isChapterCollapsed(chapterName) {
        return this.state.collapsedChapters[chapterName] || false;
    }

    /**
     * Obtiene las secciones de un capítulo en formato normalizado.
     * 
     * @method getSections
     * @memberof CapitulosAccordionWidget
     * @param {Object} chapter - Objeto capítulo con datos
     * @returns {Array<Object>} Array de secciones con nombre y líneas
     * 
     * @description
     * Transforma las secciones del capítulo en un array con estructura:
     * - name: Nombre de la sección
     * - lines: Array de líneas de productos de la sección
     */
    getSections(chapter) {
        return Object.keys(chapter.sections || {}).map((sectionName) => ({
            name: sectionName,
            lines: chapter.sections[sectionName].lines || []
        }));
    }

    /**
     * Formatea un valor numérico como moneda.
     * 
     * @method formatCurrency
     * @memberof CapitulosAccordionWidget
     * @param {number} value - Valor a formatear
     * @returns {string} Valor formateado con 2 decimales
     */
    formatCurrency(value) {
        return (value || 0).toFixed(2);
    }

    /**
     * Añade un producto a una sección específica de un capítulo.
     * 
     * @async
     * @method addProductToSection
     * @memberof CapitulosAccordionWidget
     * @param {string} chapterName - Nombre del capítulo destino
     * @param {string} sectionName - Nombre de la sección destino
     * @returns {Promise<void>}
     * 
     * @description
     * Proceso completo de adición de productos:
     * 1. Obtiene la categoría de la sección para filtrar productos
     * 2. Abre el diálogo de selección de productos
     * 3. Llama al método del backend para añadir el producto
     * 4. Actualiza la interfaz con los nuevos datos
     * 5. Muestra notificaciones de éxito o error
     * 
     * @throws {Error} Si hay problemas de comunicación con el servidor
     * 
     * @example
     * // Llamada desde template:
     * t-on-click="() => this.addProductToSection('Capítulo 1', 'Materiales')"
     * 
     * @see {@link openProductSelector} Para el diálogo de selección
     * @see {@link ProductSelectorDialog} Para el componente de diálogo
     */
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

    /**
     * Abre el diálogo de selección de productos con filtro opcional por categoría.
     * 
     * @async
     * @method openProductSelector
     * @memberof CapitulosAccordionWidget
     * @param {number|null} [categoryId=null] - ID de categoría para filtrar productos
     * @returns {Promise<number|null>} ID del producto seleccionado o null si se cancela
     * 
     * @description
     * Muestra un diálogo modal de dos pasos:
     * 1. Selección de categoría (si no se proporciona categoryId)
     * 2. Selección de producto dentro de la categoría
     * 
     * @example
     * const productId = await this.openProductSelector(5);
     * if (productId) {
     *   // Procesar producto seleccionado
     * }
     */
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

    // ==========================================
    // MÉTODOS DE EDICIÓN INLINE
    // ==========================================

    /**
     * Inicia el modo de edición para una línea específica.
     * 
     * @method startEditLine
     * @memberof CapitulosAccordionWidget
     * @param {string|number} lineId - ID de la línea a editar
     * @returns {void}
     * 
     * @description
     * Cambia el estado del widget para mostrar campos de edición inline
     * para la línea especificada. Carga los valores actuales en editValues.
     */
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

    /**
     * Cancela el modo de edición actual sin guardar cambios.
     * 
     * @method cancelEdit
     * @memberof CapitulosAccordionWidget
     * @returns {void}
     * 
     * @description
     * Restaura el estado del widget al modo de visualización,
     * descartando cualquier cambio no guardado.
     */
    cancelEdit() {
        this.state.editingLine = null;
        this.state.editValues = {};
    }

    /**
     * Guarda los cambios de la línea en edición.
     * 
     * @async
     * @method saveEdit
     * @memberof CapitulosAccordionWidget
     * @returns {Promise<void>}
     * 
     * @description
     * Proceso de guardado:
     * 1. Valida los valores ingresados (cantidad y precio >= 0)
     * 2. Llama al ORM para actualizar la línea en la base de datos
     * 3. Muestra notificación de éxito o error
     * 4. Recarga los datos del widget
     * 5. Sale del modo de edición
     * 
     * @throws {Error} Si hay problemas de validación o comunicación
     */
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

    /**
     * Elimina una línea de producto con confirmación del usuario.
     * 
     * @async
     * @method deleteLine
     * @memberof CapitulosAccordionWidget
     * @param {string|number} lineId - ID de la línea a eliminar
     * @returns {Promise<void>}
     * 
     * @description
     * Proceso de eliminación:
     * 1. Muestra diálogo de confirmación
     * 2. Si se confirma, llama al ORM para eliminar la línea
     * 3. Muestra notificación de éxito o error
     * 4. Recarga los datos del widget
     * 
     * @example
     * await this.deleteLine(123);
     */
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

    /**
     * Busca una línea por su ID en todos los capítulos y secciones.
     * 
     * @method findLineById
     * @memberof CapitulosAccordionWidget
     * @param {string|number} lineId - ID de la línea a buscar
     * @returns {Object|null} Objeto de línea encontrado o null si no existe
     * 
     * @description
     * Realiza una búsqueda recursiva en la estructura de datos
     * para encontrar la línea con el ID especificado.
     * 
     * @example
     * const line = this.findLineById(123);
     * if (line) {
     *   console.log(line.product_name);
     * }
     */
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

    // ==========================================
    // MÉTODOS DE CONDICIONES PARTICULARES
    // ==========================================

    /**
     * Actualiza las condiciones particulares para una sección específica.
     * 
     * @method updateCondicionesParticulares
     * @memberof CapitulosAccordionWidget
     * @param {string} chapterName - Nombre del capítulo
     * @param {string} sectionName - Nombre de la sección
     * @param {string} value - Valor de las condiciones particulares
     * @returns {void}
     * 
     * @description
     * Actualiza el estado local con las condiciones particulares de una sección
     * específica y las guarda automáticamente en el servidor.
     */
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

    /**
     * Guarda las condiciones particulares en la base de datos.
     * 
     * @async
     * @method saveCondicionesParticulares
     * @memberof CapitulosAccordionWidget
     * @param {string} chapterName - Nombre del capítulo
     * @param {string} sectionName - Nombre de la sección
     * @param {string} value - Valor de las condiciones particulares
     * @returns {Promise<void>}
     * 
     * @description
     * Proceso de guardado:
     * 1. Llama al método del backend para actualizar las condiciones
     * 2. Muestra notificación de éxito o error
     * 
     * @throws {Error} Si hay problemas de comunicación con el servidor
     */
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

    /**
     * Obtiene las condiciones particulares de una sección específica.
     * 
     * @method getCondicionesParticulares
     * @memberof CapitulosAccordionWidget
     * @param {string} chapterName - Nombre del capítulo
     * @param {string} sectionName - Nombre de la sección
     * @returns {string} Condiciones particulares de la sección
     * 
     * @description
     * Busca las condiciones particulares primero en el estado local
     * (cambios no guardados) y luego en los datos del servidor.
     */
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
    
    // ==========================================
    // MÉTODOS DE DEBUGGING Y UTILIDADES
    // ==========================================

    /**
     * Fuerza la actualización completa del widget desde el servidor.
     * 
     * @async
     * @method forceRefresh
     * @memberof CapitulosAccordionWidget
     * @returns {Promise<void>}
     * 
     * @description
     * Método de debugging que realiza una actualización completa:
     * 1. Ejecuta el método computed en el servidor
     * 2. Recarga el registro completo
     * 3. Verifica los datos actualizados
     * 4. Fuerza el re-renderizado del componente
     * 
     * Útil para debugging y resolución de problemas de sincronización.
     * 
     * @example
     * await this.forceRefresh();
     */
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
    
    /**
     * Muestra información detallada del estado actual del widget.
     * 
     * @method debugState
     * @memberof CapitulosAccordionWidget
     * @returns {void}
     * 
     * @description
     * Método de debugging que imprime en consola:
     * - ID del registro actual
     * - Datos raw y parseados
     * - Estado del componente
     * - Estructura completa de capítulos y secciones
     * - Productos en cada sección
     * 
     * Útil para diagnosticar problemas de datos y estado.
     * 
     * @example
     * this.debugState(); // Imprime estado en consola
     */
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

// ==========================================
// CLASES DE DIÁLOGO
// ==========================================

/**
 * Diálogo modal para la selección de productos por categoría.
 * 
 * @class ProductSelectorDialog
 * @extends Component
 * 
 * @description
 * Componente de diálogo de dos pasos que permite:
 * 1. Selección de categoría de productos con búsqueda
 * 2. Selección de producto específico dentro de la categoría
 * 
 * Características principales:
 * - Búsqueda en tiempo real de categorías y productos
 * - Navegación fluida entre pasos
 * - Integración completa con ORM de Odoo
 * - Estados de carga y manejo de errores
 * - Interfaz responsive y accesible
 * 
 * @property {Object} state - Estado reactivo del diálogo
 * @property {string} state.step - Paso actual ('category' | 'product')
 * @property {string} state.categorySearchTerm - Término de búsqueda de categorías
 * @property {Array} state.categories - Lista de categorías disponibles
 * @property {Object|null} state.selectedCategory - Categoría seleccionada
 * @property {boolean} state.loadingCategories - Estado de carga de categorías
 * @property {string} state.productSearchTerm - Término de búsqueda de productos
 * @property {Array} state.products - Lista de productos disponibles
 * @property {Object|null} state.selectedProduct - Producto seleccionado
 * @property {boolean} state.loadingProducts - Estado de carga de productos
 * 
 * @author Sergio Vadillo
 * @version 18.0.1.1.0
 * @since 2024
 * 
 * @example
 * this.dialog.add(ProductSelectorDialog, {
 *   title: "Seleccionar Producto",
 *   onConfirm: (product) => {
 *     console.log('Producto seleccionado:', product);
 *   },
 *   onCancel: () => {
 *     console.log('Selección cancelada');
 *   }
 * });
 */
class ProductSelectorDialog extends Component {
    static template = "capitulos.ProductSelectorDialog";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        onConfirm: Function,
        onCancel: Function,
        close: Function,
    };

    /**
     * Inicializa el componente y carga las categorías iniciales.
     * 
     * @method setup
     * @memberof ProductSelectorDialog
     * @returns {void}
     * 
     * @description
     * Configura el estado inicial del diálogo y carga la lista
     * de categorías disponibles desde el servidor.
     */
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            step: "category", // 'category' o 'product'
            
            // Para categorías
            categorySearchTerm: "",
            categories: [],
            selectedCategory: null,
            loadingCategories: false,
            
            // Para productos
            productSearchTerm: "",
            products: [],
            selectedProduct: null,
            loadingProducts: false,
        });
        
        // Cargar categorías al inicializar
        this.loadCategories();
    }

    /**
     * Carga todas las categorías de productos disponibles.
     * 
     * @async
     * @method loadCategories
     * @memberof ProductSelectorDialog
     * @returns {Promise<void>}
     * 
     * @description
     * Obtiene la lista completa de categorías de productos
     * desde el modelo product.category y actualiza el estado.
     */
    async loadCategories() {
        this.state.loadingCategories = true;
        try {
            const categories = await this.orm.call(
                'product.category',
                'search_read',
                [[], ['name', 'parent_id', 'product_count']],
                { limit: 100 }
            );
            this.state.categories = categories;
        } catch (error) {
            console.error('Error al cargar categorías:', error);
            this.notification.add('Error al cargar las categorías', { type: 'danger' });
        } finally {
            this.state.loadingCategories = false;
        }
    }

    /**
     * Maneja la entrada de texto en el campo de búsqueda de categorías.
     * 
     * @method onCategorySearchInput
     * @memberof ProductSelectorDialog
     * @param {Event} event - Evento de input del campo de búsqueda
     * @returns {void}
     * 
     * @description
     * Actualiza el término de búsqueda y ejecuta la búsqueda
     * de categorías en tiempo real.
     */
    async onCategorySearchInput(event) {
        const searchTerm = event.target.value;
        this.state.categorySearchTerm = searchTerm;
        
        if (searchTerm.length >= 2) {
            await this.searchCategories(searchTerm);
        } else if (searchTerm.length === 0) {
            await this.loadCategories();
        }
    }

    /**
     * Busca categorías que coincidan con el término de búsqueda.
     * 
     * @async
     * @method searchCategories
     * @memberof ProductSelectorDialog
     * @param {string} searchTerm - Término de búsqueda
     * @returns {Promise<void>}
     * 
     * @description
     * Filtra las categorías basándose en el término de búsqueda
     * actual, buscando coincidencias en el nombre de la categoría.
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
            this.state.categories = categories;
        } catch (error) {
            console.error('Error al buscar categorías:', error);
            this.notification.add('Error al buscar categorías', { type: 'danger' });
        } finally {
            this.state.loadingCategories = false;
        }
    }

    /**
     * Selecciona una categoría y actualiza el estado.
     * 
     * @method selectCategory
     * @memberof ProductSelectorDialog
     * @param {Object} category - Objeto de categoría seleccionada
     * @returns {void}
     * 
     * @description
     * Marca la categoría como seleccionada y actualiza
     * la interfaz para mostrar la selección.
     */
    selectCategory(category) {
        this.state.selectedCategory = category;
    }

    /**
     * Procede al paso de selección de productos.
     * 
     * @async
     * @method proceedToProducts
     * @memberof ProductSelectorDialog
     * @returns {Promise<void>}
     * 
     * @description
     * Cambia al paso de selección de productos y carga
     * los productos de la categoría seleccionada.
     */
    async proceedToProducts() {
        if (!this.state.selectedCategory) {
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

    /**
     * Carga los productos de una categoría específica.
     * 
     * @async
     * @method loadProductsByCategory
     * @memberof ProductSelectorDialog
     * @returns {Promise<void>}
     * 
     * @description
     * Obtiene todos los productos que pertenecen a la categoría
     * especificada y actualiza el estado con la lista de productos.
     */
    async loadProductsByCategory() {
        this.state.loadingProducts = true;
        try {
            const domain = [
                ['categ_id', '=', this.state.selectedCategory.id],
                ['sale_ok', '=', true]
            ];
            
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
        
        if (searchTerm.length >= 2) {
            await this.searchProductsInCategory(searchTerm);
        } else if (searchTerm.length === 0) {
            await this.loadProductsByCategory();
        }
    }

    async searchProductsInCategory(searchTerm) {
        this.state.loadingProducts = true;
        try {
            const domain = [
                ['categ_id', '=', this.state.selectedCategory.id],
                ['name', 'ilike', searchTerm],
                ['sale_ok', '=', true]
            ];
            
            const products = await this.orm.call(
                'product.product',
                'search_read',
                [domain, ['name', 'default_code', 'categ_id', 'list_price', 'uom_id']],
                { limit: 50 }
            );
            this.state.products = products;
        } catch (error) {
            console.error('Error al buscar productos:', error);
            this.notification.add('Error al buscar productos', { type: 'danger' });
        } finally {
            this.state.loadingProducts = false;
        }
    }

    /**
     * Selecciona un producto específico.
     * 
     * @method selectProduct
     * @memberof ProductSelectorDialog
     * @param {Object} product - Objeto de producto seleccionado
     * @returns {void}
     * 
     * @description
     * Marca el producto como seleccionado y actualiza
     * la interfaz para mostrar la selección.
     */
    selectProduct(product) {
        this.state.selectedProduct = product;
    }

    /**
     * Regresa al paso de selección de categorías.
     * 
     * @method goBackToCategories
     * @memberof ProductSelectorDialog
     * @returns {void}
     * 
     * @description
     * Cambia al paso anterior (selección de categorías)
     * y limpia la selección de productos.
     */
    goBackToCategories() {
        this.state.step = "category";
        this.state.productSearchTerm = "";
        this.state.products = [];
        this.state.selectedProduct = null;
    }

    /**
     * Confirma la selección del producto.
     * 
     * @method onConfirm
     * @memberof ProductSelectorDialog
     * @returns {void}
     * 
     * @description
     * Ejecuta el callback de confirmación con el producto
     * seleccionado y cierra el diálogo.
     */
    onConfirm() {
        if (this.state.selectedProduct) {
            this.props.onConfirm(this.state.selectedProduct);
            this.props.close();
        }
    }

    /**
     * Cancela la selección y cierra el diálogo.
     * 
     * @method onCancel
     * @memberof ProductSelectorDialog
     * @returns {void}
     * 
     * @description
     * Ejecuta el callback de cancelación y cierra el diálogo
     * sin seleccionar ningún producto.
     */
    onCancel() {
        this.props.onCancel();
        this.props.close();
    }
}

/**
 * Diálogo de confirmación para eliminación de productos.
 * 
 * @class DeleteConfirmDialog
 * @extends Component
 * 
 * @description
 * Componente de diálogo modal que solicita confirmación del usuario
 * antes de eliminar una línea de producto. Muestra información
 * del producto a eliminar y botones de confirmación/cancelación.
 * 
 * @property {Object} props - Propiedades del componente
 * @property {string} props.title - Título del diálogo
 * @property {string} props.productName - Nombre del producto a eliminar
 * @property {Function} props.onConfirm - Callback de confirmación
 * @property {Function} props.onCancel - Callback de cancelación
 * @property {Function} props.close - Función para cerrar el diálogo
 * 
 * @author Sergio Vadillo
 * @version 18.0.1.1.0
 * @since 2024
 * 
 * @example
 * this.dialog.add(DeleteConfirmDialog, {
 *   title: "Confirmar eliminación",
 *   productName: "Producto XYZ",
 *   onConfirm: () => {
 *     // Lógica de eliminación
 *   },
 *   onCancel: () => {
 *     // Lógica de cancelación
 *   }
 * });
 */
class DeleteConfirmDialog extends Component {
    static props = {
        title: { type: String },
        productName: { type: String },
        onConfirm: { type: Function },
        onCancel: { type: Function },
        close: { type: Function }
    };
    
    /**
     * Confirma la eliminación del producto.
     * 
     * @method onConfirm
     * @memberof DeleteConfirmDialog
     * @returns {void}
     * 
     * @description
     * Ejecuta el callback de confirmación para proceder
     * con la eliminación y cierra el diálogo.
     */
    onConfirm() {
        this.props.onConfirm();
        this.props.close();
    }

    /**
     * Cancela la eliminación del producto.
     * 
     * @method onCancel
     * @memberof DeleteConfirmDialog
     * @returns {void}
     * 
     * @description
     * Ejecuta el callback de cancelación y cierra el diálogo
     * sin eliminar el producto.
     */
    onCancel() {
        this.props.onCancel();
        this.props.close();
    }
}

DeleteConfirmDialog.template = "capitulos.DeleteConfirmDialog";
DeleteConfirmDialog.components = { Dialog };

// ==========================================
// REGISTRO DEL WIDGET EN ODOO
// ==========================================

// Hacer el widget accesible globalmente para depuración
window.CapitulosAccordionWidget = CapitulosAccordionWidget;

/**
 * Registro del widget CapitulosAccordionWidget en el sistema de campos de Odoo.
 * 
 * @description
 * Registra el widget personalizado para que esté disponible en las vistas
 * de formulario de Odoo. El widget se puede usar en campos de tipo 'text'
 * o 'char' especificando widget="capitulos_accordion" en la vista XML.
 * 
 * @example
 * // En vista XML:
 * <field name="capitulos_data" widget="capitulos_accordion"/>
 */
registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});