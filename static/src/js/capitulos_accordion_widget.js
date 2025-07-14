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
            return this.value ? JSON.parse(this.value) : {};
        } catch (e) {
            return {};
        }
    }

    get chapters() {
        const data = this.parsedData;
        return Object.keys(data).map((chapterName, index) => ({
            name: chapterName,
            data: data[chapterName],
            id: `chapter_${index}`,
            isCollapsed: this.state.collapsedChapters[chapterName] || false
        }));
    }

    toggleChapter(chapterName) {
        this.state.collapsedChapters[chapterName] = !this.state.collapsedChapters[chapterName];
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