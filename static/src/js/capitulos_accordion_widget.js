/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";

export class CapitulosAccordionWidget extends Component {
    static template = "capitulos.CapitulosAccordionWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({ collapsedChapters: {} });
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
        console.log('Adding product to chapter:', chapterName, 'section:', sectionName);
        
        try {
            const orderId = this.props.record.resId;
            const result = await jsonrpc('/capitulos/add_product_to_section', {
                order_id: orderId,
                chapter_name: chapterName,
                section_name: sectionName
            });
            
            if (result.error) {
                console.error('Error adding product:', result.error);
                // Show error notification
                this.env.services.notification.add(result.error, {
                    type: 'danger',
                    title: 'Error'
                });
            } else {
                console.log('Product added successfully');
                // Reload the view to show the new product
                await this.props.record.model.root.load();
                this.env.services.notification.add('Producto añadido correctamente', {
                    type: 'success'
                });
            }
        } catch (error) {
            console.error('Error in addProductToSection:', error);
            this.env.services.notification.add('Error al añadir el producto', {
                type: 'danger',
                title: 'Error'
            });
        }
    }
}

registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});