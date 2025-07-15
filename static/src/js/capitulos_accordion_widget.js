/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class CapitulosAccordionWidget extends Component {
    static template = "capitulos.CapitulosAccordionWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({ collapsedChapters: {} });
        
        // Servicios con manejo de errores
        try {
            this.orm = useService("orm");
            this.notification = useService("notification");
            this.action = useService("action");
        } catch (error) {
            console.error('CapitulosAccordionWidget - Error initializing services:', error);
            // Fallback para servicios no disponibles
            this.orm = null;
            this.notification = null;
            this.action = null;
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
        if (!this.orm || !this.notification) {
            console.error('CapitulosAccordionWidget - Services not available');
            alert('Error: Servicios no disponibles. Por favor, recargue la página.');
            return;
        }
        
        try {
            // Mostrar diálogo de selección de producto
            const productId = await this.showProductSelectionDialog();
            
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
            
            // Llamar al método del modelo para añadir el producto
            const result = await this.orm.call(
                'sale.order',
                'add_product_to_section',
                [orderId],
                {
                    capitulo_name: chapterName,
                    seccion_name: sectionName,
                    product_id: productId,
                    quantity: 1.0
                }
            );
            
            if (result && result.success) {
                this.notification.add(result.message || 'Producto añadido correctamente', {
                    type: 'success',
                    title: 'Producto añadido'
                });
                
                // Recargar la página para mostrar los cambios
                window.location.reload();
            } else {
                this.notification.add(result?.error || 'Error desconocido al añadir producto', {
                    type: 'danger',
                    title: 'Error al añadir producto'
                });
            }
            
        } catch (error) {
            console.error('CapitulosAccordionWidget - Error adding product:', error);
            const errorMessage = error.message || error.data?.message || 'Error al añadir el producto';
            
            if (this.notification) {
                this.notification.add(errorMessage, {
                    type: 'danger',
                    title: 'Error'
                });
            } else {
                alert('Error: ' + errorMessage);
            }
        }
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
                        if (this.notification) {
                            this.notification.add('Selección inválida', {
                                type: 'warning',
                                title: 'Advertencia'
                            });
                        } else {
                            alert('Selección inválida');
                        }
                        resolve(null);
                    }
                } else {
                    if (this.notification) {
                        this.notification.add('No se encontraron productos', {
                            type: 'warning',
                            title: 'Sin resultados'
                        });
                    } else {
                        alert('No se encontraron productos');
                    }
                    resolve(null);
                }
            }).catch((error) => {
                console.error('Error searching products:', error);
                const errorMessage = error.message || error.data?.message || 'Error al buscar productos';
                
                if (this.notification) {
                    this.notification.add(errorMessage, {
                        type: 'danger',
                        title: 'Error'
                    });
                } else {
                    alert('Error: ' + errorMessage);
                }
                resolve(null);
            });
        });
    }
}

registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});