/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

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
            editValues: {}
        });
        
        this.orm = useService("orm");
        this.notification = useService("notification");
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
            const productId = await this.openProductSelector();
            
            if (!productId) {
                return;
            }
            
            const orderId = this.props.record.resId;
            
            // Usar el método del modelo Python para añadir el producto
            const result = await this.orm.call(
                'sale.order',
                'add_product_to_section',
                [orderId, chapterName, sectionName, productId, 1.0]
            );
            
            if (result.success) {
                this.notification.add(result.message, {
                    type: 'success'
                });
                
                // Recargar los datos del registro
                await this.props.record.load();
            } else {
                this.notification.add(result.message || 'Error al añadir el producto', {
                    type: 'danger'
                });
            }
            
        } catch (error) {
            console.error('Error adding product:', error);
            this.notification.add('Error al añadir el producto: ' + (error.message || error), {
                type: 'danger'
            });
        }
    }

    async openProductSelector() {
        try {
            const searchTerm = prompt('Ingrese el nombre del producto a buscar:');
            
            if (!searchTerm) {
                return null;
            }
            
            const products = await this.orm.searchRead(
                'product.product',
                [['name', 'ilike', searchTerm]],
                ['id', 'name', 'list_price'],
                { limit: 10 }
            );
            
            if (products.length === 0) {
                alert('No se encontraron productos');
                return null;
            }
            
            let productList = 'Seleccione un producto:\n\n';
            products.forEach((product, index) => {
                productList += `${index + 1}. ${product.name} - $${product.list_price}\n`;
            });
            
            const selection = prompt(productList + '\nIngrese el número:');
            
            if (!selection) {
                return null;
            }
            
            const selectedIndex = parseInt(selection) - 1;
            
            if (selectedIndex >= 0 && selectedIndex < products.length) {
                return products[selectedIndex].id;
            } else {
                alert('Selección inválida');
                return null;
            }
            
        } catch (error) {
            console.error('Error selecting product:', error);
            alert('Error al buscar productos');
            return null;
        }
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
            const updateValues = {
                product_uom_qty: parseFloat(this.state.editValues.product_uom_qty) || 0,
                price_unit: parseFloat(this.state.editValues.price_unit) || 0,
                name: this.state.editValues.name || ''
            };
            
            await this.orm.write('sale.order.line', [parseInt(lineId)], updateValues);
            
            this.notification.add('Línea actualizada', { type: 'success' });
            
            this.state.editingLine = null;
            this.state.editValues = {};
            
            await this.props.record.load();
            
        } catch (error) {
            console.error('Error saving edit:', error);
            this.notification.add('Error al guardar', { type: 'danger' });
        }
    }

    async deleteLine(lineId) {
        if (!confirm('¿Eliminar esta línea?')) {
            return;
        }
        
        try {
            await this.orm.unlink('sale.order.line', [parseInt(lineId)]);
            
            this.notification.add('Línea eliminada', { type: 'success' });
            
            await this.props.record.load();
            
        } catch (error) {
            console.error('Error deleting line:', error);
            this.notification.add('Error al eliminar', { type: 'danger' });
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
}

// Hacer el widget accesible globalmente para depuración
window.CapitulosAccordionWidget = CapitulosAccordionWidget;

registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});