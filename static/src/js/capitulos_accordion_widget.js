/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

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
            currentChapter: null
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
            // Abrir el diálogo de selección de productos
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
            
            if (result && result.success) {
                this.notification.add(
                    _t('Producto añadido correctamente'),
                    { type: 'success' }
                );
                
                // Recargar los datos del widget
                await this.props.record.load();
            } else {
                this.notification.add(
                    result?.error || _t('Error al añadir el producto'),
                    { type: 'danger' }
                );
            }
            
        } catch (error) {
            console.error('Error al añadir producto:', error);
            this.notification.add(
                _t('Error al añadir producto a la sección'),
                { type: 'danger' }
            );
        }
    }

    async openProductSelector() {
        return new Promise((resolve) => {
            this.dialog.add(ProductSelectorDialog, {
                title: _t("Seleccionar Producto"),
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

    async deleteLine(lineId) {
        try {
            // Usar el servicio de diálogo para confirmación
            const confirmed = await new Promise((resolve) => {
                this.dialog.add(Dialog, {
                    title: _t("Confirmar eliminación"),
                    body: _t("¿Está seguro de que desea eliminar esta línea?"),
                    confirm: () => resolve(true),
                    cancel: () => resolve(false),
                });
            });
            
            if (!confirmed) {
                return;
            }
            
            await this.orm.unlink('sale.order.line', [parseInt(lineId)]);
            
            this.notification.add(_t('Línea eliminada correctamente'), { type: 'success' });
            
            await this.props.record.load();
            
        } catch (error) {
            console.error('Error deleting line:', error);
            this.notification.add(_t('Error al eliminar la línea'), { type: 'danger' });
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

// Componente de diálogo para selección de productos
class ProductSelectorDialog extends Component {
    static template = "capitulos.ProductSelectorDialog";
    static components = { Dialog };
    static props = {
        title: String,
        onConfirm: Function,
        onCancel: Function,
        close: Function,
    };

    setup() {
        this.state = useState({
            selectedProduct: null,
            searchTerm: '',
            products: [],
            isLoading: false
        });
        
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Cargar productos iniciales
        this.searchProducts();
    }

    async searchProducts() {
        this.state.isLoading = true;
        try {
            const domain = [['sale_ok', '=', true]];
            if (this.state.searchTerm) {
                domain.push(['name', 'ilike', this.state.searchTerm]);
            }
            
            const products = await this.orm.searchRead(
                'product.product',
                domain,
                ['id', 'name', 'list_price', 'default_code', 'uom_id'],
                { limit: 20 }
            );
            
            this.state.products = products;
        } catch (error) {
            console.error('Error al buscar productos:', error);
            this.notification.add(
                _t('Error al buscar productos'),
                { type: 'danger' }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    onSearchInput(ev) {
        this.state.searchTerm = ev.target.value;
        // Debounce la búsqueda
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.searchProducts();
        }, 300);
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

registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});