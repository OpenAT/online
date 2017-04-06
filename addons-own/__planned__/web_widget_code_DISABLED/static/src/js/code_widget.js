odoo.define('web.widgets.code_widget', function (require) {
"use strict";

var core = require('web.core');
var common = require('web.form_common');
var dom_utils = require('web.dom_utils');
var qweb = core.qweb;


qweb.add_template('/web_widget_code/static/src/xml/templates.xml');


var FieldCode = common.AbstractField.extend(common.ReinitializeFieldMixin, {
    template: 'FieldCode',

    init: function(field_manager, node) {
        var self = this;
        this._super(field_manager, node);
        
        if (this.node.attrs['ace-mode']) {
            this.$ace_mode = this.node.attrs['ace-mode'];
        } else {
            this.$ace_mode = 'python';
        }

        if (this.node.attrs['ace-theme']) {
            this.$ace_theme = this.node.attrs['ace-theme'];
        } else {
            this.$ace_theme = 'tomorrow';
        }

        if (this.node.attrs.height) {
            this.default_height = this.node.attrs.height;
        } else {
            this.default_height = '240px';
        }
    },
    initialize_content: function() {
        this.$editor_el = this.$el.find('.oe_form_code_editor');
        this.auto_sized = false;

        // create editor
        this.$editor = ace.edit(this.$editor_el[0]);
        this.$editor.$blockScrolling = Infinity;
        this.$editor.setTheme("ace/theme/" + this.$ace_theme);
        this.$editor.getSession().setMode("ace/mode/" + this.$ace_mode);

        if (this.get("effective_readonly")) {
            this.$editor.setReadOnly(true);
        } else {
            this.$editor.setReadOnly(false);
        }
    },
    render_value: function() {
        var val = this.get("value") || '';
        this.$editor.setValue(val);
        dom_utils.autoresize(this.$editor_el, {
            parent: this,
            min_height: parseInt(this.default_height)
        });
        this.$editor.resize();
        this.$editor.clearSelection();
    },

    store_dom_value: function () {
        var val = this.$editor.getValue();
        this.internal_set_value(val);
    },

    set_dimensions: function (height, width) {
        this._super(height, width);
        if (!this.get("effective_readonly")) {
            this.$el.find('oe_form_code_editor').css({
                width: width,
                minHeight: height
            });
            this.$editor.resize();
        }
    },
    commit_value: function () {
        if (! this.get("effective_readonly")) {
            this.store_dom_value();
        }
        return this._super();
    },
    is_false: function() {
        return this.get('value') === '' || this._super();
    },
});

core.form_widget_registry
    .add('code', FieldCode);

});

