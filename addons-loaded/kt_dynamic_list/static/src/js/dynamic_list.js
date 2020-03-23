odoo.define('kt_dynamic_list.shcolumns', function (require) {
"use strict";

var core = require('web.core');
var BaseImport = require('base_import.import');
var ListController= require('web.ListController');
var QWeb = core.qweb;

ListController.include({
   renderButtons: function($node) {
            var self = this;
            this._super.apply(this, arguments);
            if (!this.noLeaf && this.hasButtons) {
                this.$buttons.on('click', '.oe_select_columns', this.my_setup_columns.bind(this));
                this.$buttons.on('click', '.oe_dropdown_btn', this.hide_show_columns.bind(this));
                this.$buttons.on('click', '.oe_dropdown_menu', this.stop_event.bind(this));
            }
            if (this.$buttons){
                this.contents = this.$buttons.find('ul#showcb');
                var columns = []
                _.each(this.renderer.arch.children, function(node){
                    var name = node.attrs.name
                    var description = node.attrs.string || self.renderer.state.fields[name].string;
                    columns.push({
                        'field_name': node.attrs.name,
                        'label': description,
                        'invisible': node.attrs.modifiers.column_invisible || false
                    })
                })
                this.contents.append($(QWeb.render('ColumnSelectionDropDown',{widget:this,columns:columns})));
            }
        },

    my_setup_columns: function () {
            $("#showcb").toggle();
        },
        stop_event : function(e)
        {
            e.stopPropagation();
        },

        hide_show_columns : function(){
           $("#showcb").hide();
           this.setup_columns()
           var state = this.model.get(this.handle);
           this.renderer.updateState(state, {reload: true})
        },

        setup_columns: function () {
            var self = this;
            _.each(this.contents.find('li.item_column'), function(item){
                var checkbox_item = $(item).find('input');
                var field = _.find(self.renderer.arch.children, function(field){
                    return field.attrs.name === checkbox_item.data('name')
                });
                if(checkbox_item.prop('checked')){
                    field.attrs.modifiers.column_invisible = false;
                }
                else {
                    field.attrs.modifiers.column_invisible = true;
                }
            })
        },
    });

    $(document).click(function(){
      $("#showcb").hide();
    });

});
