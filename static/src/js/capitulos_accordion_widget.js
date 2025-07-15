/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class CapitulosAccordionWidget extends Component {
    static template = "capitulos.CapitulosAccordionWidget";
    static props = { ...standardFieldProps };
    static supportedTypes = ["text"];
    static extractProps = ({ attrs }) => {
        return {
            ...standardFieldProps,
        };
    };

    setup() {
        this.state = useState({
            collapsedChapters: {}
        });
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.action = useService("action");
    }

    get parsedData() {
        try {
            const data = this.props.value ? JSON.parse(this.props.value) : {};
            console.log('CapitulosAccordionWidget - parsedData:', data);
            return data;
        } catch (e) {
            console.error('CapitulosAccordionWidget - Error parsing data:', e, 'Raw value:', this.props.value);
            return {};
        }
    }

    getChapters() {
        const data = this.parsedData;
        if (!data || Object.keys(data).length === 0) {
            return [];
        }
        return Object.keys(data).map((chapterName, index) => {
            return {
                name: chapterName,
                data: data[chapterName],
                id: 'chapter_' + Date.now() + '_' + index,
                collapsed: this.state.collapsedChapters[chapterName] || false
            };
        });
    }

    toggleChapter(chapterName) {
        console.log('CapitulosAccordionWidget - toggleChapter called for:', chapterName);
        this.state.collapsedChapters[chapterName] = !this.state.collapsedChapters[chapterName];
    }

    getSections(chapter) {
        return Object.keys(chapter.sections || {}).map((sectionName, index) => {
            return {
                name: sectionName,
                id: 'section_' + Date.now() + '_' + index,
                lines: (chapter.sections[sectionName].lines || []).map((line, lineIndex) => {
                    return Object.assign({}, line, {
                        id: 'line_' + Date.now() + '_' + index + '_' + lineIndex
                    });
                })
            };
        });
    }

    formatCurrency(value) {
        return (value || 0).toFixed(2);
    }

    async addProductToSection(chapterName, sectionName) {
        console.log('Adding product to chapter:', chapterName, 'section:', sectionName);
        
        const orderId = this.props.record.resId;
        
        try {
            const result = await this.rpc('/capitulos/add_product_to_section', {
                order_id: orderId,
                chapter_name: chapterName,
                section_name: sectionName
            });
            
            if (result.error) {
                console.error('Error adding product:', result.error);
                this.notification.add(result.error, {
                    type: 'danger',
                    title: _t('Error')
                });
            } else {
                console.log('Product added successfully');
                this.notification.add(_t('Producto añadido correctamente'), {
                    type: 'success'
                });
                // Trigger reload
                await this.action.doAction({
                    type: 'ir.actions.client',
                    tag: 'reload'
                });
            }
        } catch (error) {
            console.error('Error in addProductToSection:', error);
            this.notification.add(_t('Error al añadir el producto'), {
                type: 'danger',
                title: _t('Error')
            });
        }
    }
}

export const capitulosAccordionWidget = {
    component: CapitulosAccordionWidget,
};

registry.category("fields").add("capitulos_accordion", capitulosAccordionWidget);