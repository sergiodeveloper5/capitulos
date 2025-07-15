/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
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
        // Usar importación directa de rpc y servicios disponibles
        this.rpc = rpc;
        try {
            this.notification = useService("notification");
            this.action = useService("action");
        } catch (error) {
            console.warn('Some services not available in current context:', error);
            // Fallback para cuando los servicios no están disponibles
            this.notification = null;
            this.action = null;
        }
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
                id: 'chapter_' + chapterName.replace(/\s+/g, '_'),
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
                id: 'section_' + sectionName.replace(/\s+/g, '_'),
                lines: (chapter.sections[sectionName].lines || []).map((line, lineIndex) => {
                    return Object.assign({}, line, {
                        id: 'line_' + (line.id || lineIndex)
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
                if (this.notification) {
                    this.notification.add(result.error, {
                        type: 'danger',
                        title: _t('Error')
                    });
                } else {
                    alert('Error: ' + result.error);
                }
            } else {
                console.log('Product added successfully');
                if (this.notification) {
                    this.notification.add(_t('Producto añadido correctamente'), {
                        type: 'success'
                    });
                } else {
                    alert('Producto añadido correctamente');
                }
                // Trigger reload
                if (this.action) {
                    await this.action.doAction({
                        type: 'ir.actions.client',
                        tag: 'reload'
                    });
                } else {
                    // Fallback: reload the page
                    window.location.reload();
                }
            }
        } catch (error) {
            console.error('Error in addProductToSection:', error);
            if (this.notification) {
                this.notification.add(_t('Error al añadir el producto'), {
                    type: 'danger',
                    title: _t('Error')
                });
            } else {
                alert('Error al añadir el producto: ' + error.message);
            }
        }
    }
}

export const capitulosAccordionWidget = {
    component: CapitulosAccordionWidget,
};

registry.category("fields").add("capitulos_accordion", capitulosAccordionWidget);