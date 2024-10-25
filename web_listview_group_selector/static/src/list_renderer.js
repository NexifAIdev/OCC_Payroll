/** @odoo-module */

import {ListRenderer} from '@web/views/list/list_renderer';
import {patch} from '@web/core/utils/patch';

patch(ListRenderer.prototype, {

    getGroupNameCellColSpan(group) {
        let colspan = super.getGroupNameCellColSpan(group);
        if (this.hasSelectors) {
            colspan--;
        }
        return colspan
    },

    toggleGroupSelection(group) {
        if (!this.canSelectRecord) {
            return;
        }
        group.list.toggleSelection();
    },

    isGroupSelected(group) {
        return !group.isFolded && group.list.selection.length === group.list.records.length;
    }

})
