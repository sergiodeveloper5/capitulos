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
            id: `chapter_${index}`,
            isCollapsed: this.state.collapsedChapters[chapterName] || false
        }));
    }

    toggleChapter(chapterName) {
        console.log('CapitulosAccordionWidget - toggleChapter called for:', chapterName);
        this.state.collapsedChapters[chapterName] = !this.state.collapsedChapters[chapterName];
        console.log('CapitulosAccordionWidget - new state:', this.state.collapsedChapters);
    }

    isChapterCollapsed(chapterName) {
        return this.state.collapsedChapters[chapterName] || false;
    }

    getSections(chapter) {
        return Object.keys(chapter.sections || {}).map(sectionName => ({
            name: sectionName,
            lines: chapter.sections[sectionName].lines || []
        }));
    }

    formatCurrency(value) {
        return (value || 0).toFixed(2);
    }
}

registry.category("fields").add("capitulos_accordion", {
    component: CapitulosAccordionWidget,
});