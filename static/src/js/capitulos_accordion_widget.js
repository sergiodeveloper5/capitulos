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

    setup() {
        this.state = useState({ collapsedChapters: {} });
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.action = useService("action");
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
        
        try {
            // Mostrar diálogo de selección de producto
            const productId = await this.showProductSelectionDialog();
            
            if (!productId) {
                return; // Usuario canceló
            }
            
            // Obtener el ID del pedido actual
            const orderId = this.props.record.resId;
            
            // Llamar al endpoint para añadir el producto
            const result = await this.rpc('/capitulos/add_product_to_section', {
                order_id: orderId,
                capitulo_name: chapterName,
                seccion_name: sectionName,
                product_id: productId,
                quantity: 1.0
            });
            
            if (result.success) {
                this.notification.add(result.message, {
                    type: 'success',
                    title: 'Producto añadido'
                });
                
                // Recargar la página para mostrar los cambios
                window.location.reload();
            } else {
                this.notification.add(result.error || 'Error desconocido', {
                    type: 'danger',
                    title: 'Error al añadir producto'
                });
            }
            
        } catch (error) {
            console.error('CapitulosAccordionWidget - Error adding product:', error);
            this.notification.add('Error al añadir el producto', {
                type: 'danger',
                title: 'Error'
            });
        }
    }

    async showProductSelectionDialog() {
        return new Promise((resolve) => {
            // Crear un diálogo simple con prompt
            const productName = prompt('Ingrese el nombre del producto a buscar:');
            
            if (!productName) {
                resolve(null);
                return;
            }
            
            // Buscar productos
            this.rpc('/capitulos/search_products', {
                query: productName,
                limit: 10
            }).then((result) => {
                if (result.success && result.products.length > 0) {
                    // Mostrar lista de productos encontrados
                    let message = 'Productos encontrados:\n\n';
                    result.products.forEach((product, index) => {
                        message += `${index + 1}. ${product.name} - ${product.list_price}€\n`;
                    });
                    message += '\nIngrese el número del producto a seleccionar:';
                    
                    const selection = prompt(message);
                    const selectedIndex = parseInt(selection) - 1;
                    
                    if (selectedIndex >= 0 && selectedIndex < result.products.length) {
                        resolve(result.products[selectedIndex].id);
                    } else {
                        this.notification.add('Selección inválida', {
                            type: 'warning',
                            title: 'Advertencia'
                        });
                        resolve(null);
                    }
                } else {
                    this.notification.add('No se encontraron productos', {
                        type: 'warning',
                        title: 'Sin resultados'
                    });
                    resolve(null);
                }
            }).catch((error) => {
                console.error('Error searching products:', error);
                this.notification.add('Error al buscar productos', {
                    type: 'danger',
                    title: 'Error'
                });
                resolve(null);
            });
        });
    }
}

registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});