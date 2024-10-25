/** @odoo-module **/

import {_t} from '@web/core/l10n/translation';
import {registry} from '@web/core/registry';
import {UrlField, urlField} from '@web/views/fields/url/url_field';

export class VideoUrlField extends UrlField {

    static template = 'web_widget_video_url.VideoURLField';

    get value() {
        return this.props.record.data[this.props.name]
    }

    get isUrlYoutube() {
        return !!this.value && this.value.includes('youtu');
    }
    get isUrlVimeo() {
        return !!this.value && this.value.includes('vimeo');
    }

}

export const videoUrlField = {
    ...urlField,
    component: VideoUrlField,
    displayName: _t('Video URL'),
    supportedTypes: ['char'],
}

registry.category('fields').add('video_url', videoUrlField);
