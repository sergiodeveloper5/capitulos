/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { useRef } from "@odoo/owl";

export class CapitulosAccordionWidget extends Component {
    static template = "capitulos.CapitulosAccordionWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({ 
            collapsedChapters: {},
            editingLine: null,
            editValues: {}
        });
        
        // Servicios con manejo de errores
        try {
            this.orm = useService("orm");
            this.notification = useService("notification");
            this.action = useService("action");
            this.dialog = useService("dialog");
            this.rpc = useService("rpc");
        } catch (error) {
            console.error('CapitulosAccordionWidget - Error initializing services:', error);
            // Fallback para servicios no disponibles
            this.orm = null;
            this.notification = null;
            this.action = null;
            this.dialog = null;
            this.rpc = null;
        }
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    get parsedData() {
        try {
            const data = this.value ? JSON.parse(this.value) : {};
            console.log('CapitulosAccordionWidget - parsedData:', data);
            return data;
        } catch (e) {
            console.error('CapitulosAccordionWidget - Error parsing data:', e, 'Raw value:', this.value);
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
            id: `chapter_${Date.now()}_${index}`
        }));
    }

    toggleChapter(chapterName) {
        console.log('CapitulosAccordionWidget - toggleChapter called for:', chapterName);
        this.state.collapsedChapters = {
            ...this.state.collapsedChapters,
            [chapterName]: !this.state.collapsedChapters[chapterName]
        };
        console.log('CapitulosAccordionWidget - new state:', this.state.collapsedChapters);
    }

    isChapterCollapsed(chapterName) {
        return this.state.collapsedChapters[chapterName] || false;
    }

    getSections(chapter) {
        return Object.keys(chapter.sections || {}).map((sectionName, index) => ({
            name: sectionName,
            id: `section_${Date.now()}_${index}`,
            lines: (chapter.sections[sectionName].lines || []).map((line, lineIndex) => ({
                ...line,
                id: `line_${Date.now()}_${index}_${lineIndex}`
            }))
        }));
    }

    formatCurrency(value) {
        return (value || 0).toFixed(2);
    }

    async addProductToSection(chapterName, sectionName) {
        console.log('CapitulosAccordionWidget - addProductToSection called:', chapterName, sectionName);
        
        // Verificar que los servicios estén disponibles
        if (!this.rpc || !this.notification) {
            console.error('CapitulosAccordionWidget - Services not available');
            this.notification?.add('Error: Servicios no disponibles. Por favor, recargue la página.', {
                type: 'danger',
                title: 'Error'
            }) || alert('Error: Servicios no disponibles');
            return;
        }
        
        try {
            // Abrir selector de productos usando el action service
            const productId = await this.openProductSelector();
            
            if (!productId) {
                return; // Usuario canceló
            }
            
            // Obtener el ID del pedido actual
            const orderId = this.props.record.resId;
            
            if (!orderId) {
                this.notification.add('Error: No se pudo obtener el ID del pedido', {
                    type: 'danger',
                    title: 'Error'
                });
                return;
            }
            
            // Llamar al controlador HTTP para añadir el producto
            const result = await this.rpc('/capitulos/add_product_to_section', {
                order_id: orderId,
                capitulo_name: chapterName,
                seccion_name: sectionName,
                product_id: productId,
                quantity: 1.0
            });
            
            if (result && result.success) {
                this.notification.add(result.message || 'Producto añadido correctamente', {
                    type: 'success',
                    title: 'Producto añadido'
                });
                
                // Actualizar el record para reflejar los cambios
                await this.props.record.load();
                this.render();
            } else {
                this.notification.add(result?.error || 'Error desconocido al añadir producto', {
                    type: 'danger',
                    title: 'Error al añadir producto'
                });
            }
            
        } catch (error) {
            console.error('CapitulosAccordionWidget - Error adding product:', error);
            const errorMessage = error.message || error.data?.message || 'Error al añadir el producto';
            
            this.notification.add(errorMessage, {
                type: 'danger',
                title: 'Error'
            });
        }
    }

    async openProductSelector() {
        return new Promise((resolve) => {
            if (!this.action) {
                // Fallback al método anterior si no hay action service
                this.showProductSelectionDialog().then(resolve);
                return;
            }
            
            // Usar el selector de productos nativo de Odoo
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Seleccionar Producto',
                res_model: 'product.product',
                view_mode: 'list',
                views: [[false, 'list']],
                target: 'new',
                domain: [['sale_ok', '=', true]],
                context: {
                    search_default_filter_to_sell: 1,
                    default_detailed_type: 'product'
                }
            }, {
                onClose: (result) => {
                    if (result && result.resIds && result.resIds.length > 0) {
                        resolve(result.resIds[0]);
                    } else {
                        resolve(null);
                    }
                }
            });
        });
    }

    async showProductSelectionDialog() {
        return new Promise((resolve) => {
            // Verificar que el servicio ORM esté disponible
            if (!this.orm) {
                console.error('CapitulosAccordionWidget - ORM service not available');
                alert('Error: Servicio ORM no disponible');
                resolve(null);
                return;
            }
            
            // Crear un diálogo simple con prompt
            const productName = prompt('Ingrese el nombre del producto a buscar:');
            
            if (!productName || productName.trim() === '') {
                resolve(null);
                return;
            }
            
            // Buscar productos
            this.orm.searchRead(
                'product.product',
                [['sale_ok', '=', true], ['name', 'ilike', productName.trim()]],
                ['id', 'name', 'default_code', 'list_price', 'uom_id'],
                { limit: 10 }
            ).then((products) => {
                if (products && products.length > 0) {
                    // Mostrar lista de productos encontrados
                    let message = 'Productos encontrados:\n\n';
                    products.forEach((product, index) => {
                        const price = product.list_price || 0;
                        const code = product.default_code ? `[${product.default_code}] ` : '';
                        message += `${index + 1}. ${code}${product.name} - ${price.toFixed(2)}€\n`;
                    });
                    message += '\nIngrese el número del producto a seleccionar (o 0 para cancelar):';
                    
                    const selection = prompt(message);
                    
                    if (!selection || selection.trim() === '' || selection === '0') {
                        resolve(null);
                        return;
                    }
                    
                    const selectedIndex = parseInt(selection) - 1;
                    
                    if (selectedIndex >= 0 && selectedIndex < products.length) {
                        resolve(products[selectedIndex].id);
                    } else {
                        this.notification?.add('Selección inválida', {
                            type: 'warning',
                            title: 'Advertencia'
                        }) || alert('Selección inválida');
                        resolve(null);
                    }
                } else {
                    this.notification?.add('No se encontraron productos', {
                        type: 'warning',
                        title: 'Sin resultados'
                    }) || alert('No se encontraron productos');
                    resolve(null);
                }
            }).catch((error) => {
                console.error('Error searching products:', error);
                const errorMessage = error.message || error.data?.message || 'Error al buscar productos';
                
                this.notification?.add(errorMessage, {
                    type: 'danger',
                    title: 'Error'
                }) || alert('Error: ' + errorMessage);
                resolve(null);
            });
        });
    }

    // Métodos para edición inline
    startEditLine(lineId) {
        this.state.editingLine = lineId;
        // Obtener los valores actuales de la línea para edición
        const line = this.findLineById(lineId);
        if (line) {
            this.state.editValues = {
                product_uom_qty: line.product_uom_qty,
                price_unit: line.price_unit,
                name: line.name,
                product_name: line.product_name
            };
        }
    }

    cancelEdit() {
        this.state.editingLine = null;
        this.state.editValues = {};
    }

    async saveEdit(lineId) {
        if (!this.orm) {
            this.notification?.add('Error: Servicio ORM no disponible', {
                type: 'danger',
                title: 'Error'
            });
            return;
        }

        try {
            // Preparar los valores para actualizar
            const updateValues = {
                product_uom_qty: this.state.editValues.product_uom_qty,
                price_unit: this.state.editValues.price_unit,
                name: this.state.editValues.name
            };
            
            // Si hay un product_name, también actualizarlo
            if (this.state.editValues.product_name !== undefined) {
                updateValues.product_name = this.state.editValues.product_name;
            }
            
            await this.orm.write('sale.order.line', [lineId], updateValues);
            
            this.notification?.add('Línea actualizada correctamente (incluyendo condiciones particulares)', {
                type: 'success',
                title: 'Actualizado'
            });
            
            this.state.editingLine = null;
            this.state.editValues = {};
            
            // Actualizar el record
            await this.props.record.load();
            this.render();
        } catch (error) {
            console.error('Error updating line:', error);
            this.notification?.add('Error al actualizar la línea: ' + (error.message || 'Error desconocido'), {
                type: 'danger',
                title: 'Error'
            });
        }
    }

    async deleteLine(lineId) {
        if (!this.orm) {
            this.notification?.add('Error: Servicio ORM no disponible', {
                type: 'danger',
                title: 'Error'
            });
            return;
        }

        if (!confirm('¿Está seguro de que desea eliminar esta línea?')) {
            return;
        }

        try {
            await this.orm.unlink('sale.order.line', [lineId]);
            
            this.notification?.add('Línea eliminada correctamente', {
                type: 'success',
                title: 'Eliminado'
            });
            
            // Actualizar el record
            await this.props.record.load();
            this.render();
        } catch (error) {
            console.error('Error deleting line:', error);
            this.notification?.add('Error al eliminar la línea', {
                type: 'danger',
                title: 'Error'
            });
        }
    }

    findLineById(lineId) {
        // Buscar la línea en los datos parseados
        const data = this.parsedData;
        for (const chapterName in data) {
            const chapter = data[chapterName];
            for (const sectionName in chapter.sections) {
                const section = chapter.sections[sectionName];
                const line = section.lines.find(l => l.id === lineId);
                if (line) return line;
            }
        }
        return null;
    }

    updateEditValue(field, value) {
        this.state.editValues[field] = value;
    }
}

registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});