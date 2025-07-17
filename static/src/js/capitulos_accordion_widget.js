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
    static supportedTypes = ["text"];

    setup() {
        this.state = useState({ 
            collapsedChapters: {},
            editingLine: null,
            editValues: {},
            categories: []
        });
        
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Cargar categorías al inicializar
        this.loadCategories();
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

    async loadCategories() {
        try {
            const categories = await this.orm.searchRead(
                'product.category',
                [],
                ['id', 'name'],
                { order: 'name asc' }
            );
            this.state.categories = categories;
        } catch (error) {
            console.error('Error al cargar categorías:', error);
        }
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
            lines: chapter.sections[sectionName].lines || [],
            category_id: chapter.sections[sectionName].category_id || null
        }));
    }

    async onCategoryChange(chapterName, sectionName, categoryId) {
        try {
            const orderId = this.props.record.resId;
            
            const result = await this.orm.call(
                'sale.order',
                'update_section_category',
                [orderId, chapterName, sectionName, categoryId ? parseInt(categoryId) : false]
            );
            
            if (result && result.success) {
                this.notification.add(
                    result.message || _t('Categoría actualizada correctamente'),
                    { type: 'success' }
                );
                
                await this.props.record.load();
            } else {
                this.notification.add(
                    result?.error || _t('Error al actualizar la categoría'),
                    { type: 'danger' }
                );
            }
        } catch (error) {
            console.error('Error al cambiar categoría:', error);
            this.notification.add(
                _t('Error al actualizar la categoría: ') + (error.message || error),
                { type: 'danger' }
            );
        }
    }

    // Método para formatear moneda
    formatCurrency(amount) {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount || 0);
    }

    async addProductToSection(chapterName, sectionName) {
        try {
            // Obtener la categoría de la sección
            const data = this.parsedData;
            let sectionCategoryId = null;
            if (data && data[chapterName] && data[chapterName].sections && data[chapterName].sections[sectionName]) {
                sectionCategoryId = data[chapterName].sections[sectionName].category_id;
            }
            
            // Por ahora, usar un prompt simple para seleccionar producto
            const productName = prompt(_t('Ingrese el nombre del producto a buscar:'));
            if (!productName) return;
            
            // Buscar productos
            let domain = [['sale_ok', '=', true], ['name', 'ilike', productName]];
            if (sectionCategoryId) {
                domain.push(['categ_id', '=', sectionCategoryId]);
            }
            
            const products = await this.orm.searchRead(
                'product.product',
                domain,
                ['id', 'name', 'list_price'],
                { limit: 10 }
            );
            
            if (products.length === 0) {
                this.notification.add(_t('No se encontraron productos'), { type: 'warning' });
                return;
            }
            
            // Usar el primer producto encontrado (simplificado)
            const productId = products[0].id;
            const orderId = this.props.record.resId;
            
            const result = await this.orm.call(
                'sale.order',
                'add_product_to_section',
                [orderId, chapterName, sectionName, productId, 1.0]
            );
            
            if (result && result.success) {
                this.notification.add(
                    result.message || _t('Producto añadido correctamente'),
                    { type: 'success' }
                );
                
                await this.props.record.load();
            } else {
                this.notification.add(
                    result?.error || _t('Error al añadir producto'),
                    { type: 'danger' }
                );
            }
        } catch (error) {
            console.error('Error al añadir producto:', error);
            this.notification.add(
                _t('Error al añadir producto: ') + (error.message || error),
                { type: 'danger' }
            );
        }
    }

    async editLine(chapterName, sectionName, lineIndex) {
        const data = this.parsedData;
        const line = data[chapterName]?.sections?.[sectionName]?.lines?.[lineIndex];
        
        if (!line) return;
        
        this.state.editingLine = `${chapterName}-${sectionName}-${lineIndex}`;
        this.state.editValues = {
            quantity: line.quantity || 1,
            price_unit: line.price_unit || 0
        };
    }

    async saveLine(chapterName, sectionName, lineIndex) {
        try {
            const orderId = this.props.record.resId;
            const { quantity, price_unit } = this.state.editValues;
            
            const result = await this.orm.call(
                'sale.order',
                'update_line_in_section',
                [orderId, chapterName, sectionName, lineIndex, {
                    quantity: parseFloat(quantity) || 1,
                    price_unit: parseFloat(price_unit) || 0
                }]
            );
            
            if (result && result.success) {
                this.notification.add(
                    result.message || _t('Línea actualizada correctamente'),
                    { type: 'success' }
                );
                
                this.state.editingLine = null;
                this.state.editValues = {};
                await this.props.record.load();
            } else {
                this.notification.add(
                    result?.error || _t('Error al actualizar línea'),
                    { type: 'danger' }
                );
            }
        } catch (error) {
            console.error('Error al guardar línea:', error);
            this.notification.add(
                _t('Error al guardar línea: ') + (error.message || error),
                { type: 'danger' }
            );
        }
    }

    cancelEdit() {
        this.state.editingLine = null;
        this.state.editValues = {};
    }

    async deleteLine(chapterName, sectionName, lineIndex) {
        if (!confirm(_t('¿Está seguro de que desea eliminar esta línea?'))) {
            return;
        }
        
        try {
            const orderId = this.props.record.resId;
            
            const result = await this.orm.call(
                'sale.order',
                'delete_line_from_section',
                [orderId, chapterName, sectionName, lineIndex]
            );
            
            if (result && result.success) {
                this.notification.add(
                    result.message || _t('Línea eliminada correctamente'),
                    { type: 'success' }
                );
                
                await this.props.record.load();
            } else {
                this.notification.add(
                    result?.error || _t('Error al eliminar línea'),
                    { type: 'danger' }
                );
            }
        } catch (error) {
            console.error('Error al eliminar línea:', error);
            this.notification.add(
                _t('Error al eliminar línea: ') + (error.message || error),
                { type: 'danger' }
            );
        }
    }

    // Método para verificar si una línea está en edición
    isEditing(chapterName, sectionName, lineIndex) {
        return this.state.editingLine === `${chapterName}-${sectionName}-${lineIndex}`;
    }

    // Método para calcular el subtotal de una línea
    getSubtotal(line) {
        return (line.quantity || 0) * (line.price_unit || 0);
    }

    // Método para manejar cambios en cantidad
    onQuantityChange(ev) {
        this.state.editValues.quantity = parseFloat(ev.target.value) || 0;
    }

    // Método para manejar cambios en precio
    onPriceChange(ev) {
        this.state.editValues.price_unit = parseFloat(ev.target.value) || 0;
    }

    async updateCondicionesParticulares(chapterName, sectionName, value) {
        try {
            const orderId = this.props.record.resId;
            
            const result = await this.orm.call(
                'sale.order',
                'update_section_conditions',
                [orderId, chapterName, sectionName, value]
            );
            
            if (result && result.success) {
                this.notification.add(
                    result.message || _t('Condiciones actualizadas correctamente'),
                    { type: 'success' }
                );
            } else {
                this.notification.add(
                    result?.error || _t('Error al actualizar condiciones'),
                    { type: 'danger' }
                );
            }
        } catch (error) {
            console.error('Error al actualizar condiciones:', error);
            this.notification.add(
                _t('Error al actualizar condiciones: ') + (error.message || error),
                { type: 'danger' }
            );
        }
    }
}

// Registrar el widget en el registro de campos
registry.category("fields").add("capitulos_accordion", CapitulosAccordionWidget);