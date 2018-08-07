openerp.oepetstore = function(instance, local) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    console.log(instance);
    console.log(local);

    local.HomePage = instance.Widget.extend({
        className: 'petstore_homepage',
//        template: 'HomepageTemplate',
//
//        init: function(parent) {
//            this._super(parent);
//            this.name = "Mordecai";
//        },

        start: function() {
            console.log("pet store home page loaded");

            this.$el.append("<div>Welcome to the petstore!</div>");
//            this.$el.append(QWeb.render("HomepageTemplate"));
//            QWeb.render("HomepageTemplate", {name: "Klaus"});

            var products = new local.ProductWidget(this, ["test", "asd", " sadghgre"], "'green");
            products.appendTo(this.$el);

            var widget = new local.ConfirmWidget(this);
            widget.on("user_chose", this, this.user_chose);
            widget.appendTo(this.$el);

            this.colorInput = new local.ColorInputWidget(this);
            this.colorInput.on("change:color", this, this.color_changed);
            this.colorInput.appendTo(this.$el);

            var self = this;
            var model = new instance.web.Model("oepetstore.message_of_the_day");
            model.call("my_method", {context: new instance.web.CompoundContext()}).then(function(res) {
                        self.$el.append("<div>Hi "+ res["hello"] + "</div>")});

            new local.MessageOfTheDay(this).appendTo(this.$el);

            $.when(
                new local.PetToysList(this).appendTo(this.$('.oe_petstore_homepage_left')),
                new local.MessageOfTheDay(this).appendTo(this.$('.oe_petstore_homepage_right'))
            );
            new local.WidgetCoordinates()

//            var greeting = new local.GreetingsWidget(this);
//
//            var greeting2 = new local.GreetingsWidget(this);
//            greeting2.appendTo(this.$el);
//            console.log(this.getChildren()[0].el);
//
//            greeting2.destroy();
//
//            return greeting.appendTo(this.$el);
        },
        user_chose: function(input) {
            if (input)
            {
                console.log("ok");
            }
            else
            {
                console.log("not ok");
            }
        },
        color_changed: function() {
            this.$(".oe_color_div").css("background-color", this.colorInput.get("color"));
        },
    });

    local.GreetingsWidget = instance.Widget.extend({
        className: 'petstore_greetings',

//        init: function(parent, name) {
//            this._super(parent);
//            this.name = name;
//        }

        start: function() {
            this.$el.append("<div>Greeting Widget!</div>");
            console.log(this.getParent().el)
        },
    });

    local.ProductWidget = instance.Widget.extend({
        template: "ProductTmp",
        init: function(parent, products, color) {
            this._super(parent);
            this.products = products;
            this.color = color;
        },
    });

    local.ConfirmWidget = instance.Widget.extend({
        events: {
            "click button.ok_button": function() {
                this.trigger('user_chose', true);
            },
           "click button.cancel_button": function() {
                this.trigger('user_chose', false);
            }
        },
        start: function() {
            this.$el.append("<div>Perform Action:</div>" + "<button class='ok_button'>OK</button>"
                            + "<button class='cancel_button'>Cancel</button>");
        },
    });

    local.ColorInputWidget = instance.Widget.extend({
        template: "ColorInputWidget",
        events: {
            'change input': 'input_changed'
        },
        start: function() {
            this.input_changed();
            return this._super();
        },
        input_changed: function() {
            var color = [
                "#",
                this.$(".oe_color_red").val(),
                this.$(".oe_color_green").val(),
                this.$(".oe_color_blue").val()
            ].join('');
            this.set("color", color);
        },
    });

    local.MessageOfTheDay = instance.Widget.extend({
        template: "MessageOfTheDay",
        start: function() {
            var self = this;
            return new instance.web.Model("oepetstore.message_of_the_day")
                .query(["message"])
                .order_by('-create_date', '-id')
                .first()
                .then(function(result) {
                    self.$(".oe_mywidget_message_of_the_day").text(result.message);
                });
        },
    });

    local.PetToysList = instance.Widget.extend({
        template: 'PetToysList',

        events: {
        'click .oe_petstore_pettoy': 'selected_item',
        },

        start: function () {
            var self = this;
            return new instance.web.Model('product.product')
                .query(['name', 'image'])
                .filter([['categ_id.name', '=', "Pet Toys"]])
                .limit(5)
                .all()
                .then(function (results) {
                    _(results).each(function (item) {
                        self.$el.append(QWeb.render('PetToy', {item: item}));
                    });
                });
        },

        selected_item: function (event) {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'product.product',
                res_id: $(event.currentTarget).data('id'),
                views: [[false, 'form']],
            });
    }   ,
    });

    local.FieldChar2 = instance.web.form.AbstractField.extend({
        init: function() {
            this._super.apply(this, arguments);
            this.set("value", "");
        },
        start: function() {
            console.log("fieldchar2");
            this.on("change:effective_readonly", this, function() {
                this.display_field();
                this.render_value();
            });
            this.display_field();
            return this._super();
        },
        display_field: function() {
            var self = this;
            this.$el.html(QWeb.render("FieldChar2", {widget: this}));
            if (! this.get("effective_readonly")) {
                this.$("input").change(function() {
                    self.internal_set_value(self.$("input").val());
                });
            }
        },
        render_value: function() {
            if (this.get("effective_readonly")) {
                this.$el.text(this.get("value"));
            } else {
                this.$("input").val(this.get("value"));
            }
        },
    });

    local.FieldColor = instance.web.form.AbstractField.extend({
        events: {
            'change input': function (e) {
                if (!this.get('effective_readonly')) {
                    this.internal_set_value($(e.currentTarget).val());
                }
            }
        },
        init: function() {
            console.log("fieldcolor");
            this._super.apply(this, arguments);
            this.set("value", "");
        },
        start: function() {
            this.on("change:effective_readonly", this, function() {
                this.display_field();
                this.render_value();
            });
            this.display_field();
            return this._super();
        },
        display_field: function() {
            this.$el.html(QWeb.render("FieldColor", {widget: this}));
        },
        render_value: function() {
            if (this.get("effective_readonly")) {
                this.$(".oe_field_color_content").css("background-color", this.get("value") || "#FFFFFF");
            } else {
                this.$("input").val(this.get("value") || "#FFFFFF");
            }
        },
    });

    local.WidgetCoordinates = instance.web.form.FormWidget.extend({
        events: {
            'click button': function () {
                navigator.geolocation.getCurrentPosition(
                    this.proxy('received_position'));
            }
        },
        start: function() {
            console.log("coord");
            var sup = this._super();
            this.field_manager.on("field_changed:provider_latitude", this, this.display_map);
            this.field_manager.on("field_changed:provider_longitude", this, this.display_map);
            this.on("change:effective_readonly", this, this.display_map);
            this.display_map();
            return sup;
        },
        display_map: function() {
            this.$el.html(QWeb.render("WidgetCoordinates", {
                "latitude": this.field_manager.get_field_value("provider_latitude") || 0,
                "longitude": this.field_manager.get_field_value("provider_longitude") || 0,
            }));
            this.$("button").toggle(! this.get("effective_readonly"));
        },
        received_position: function(obj) {
            this.field_manager.set_values({
                "provider_latitude": obj.coords.latitude,
                "provider_longitude": obj.coords.longitude,
            });
        },
    });

//  --------------------------------------------------------------------------------------------------------------------
    var MyClass = instance.web.Class.extend({
        say_hello: function() {
            console.log("hello", this.name);
        },
    })

    var my_object = new MyClass();
    my_object.name = "bob";
    my_object.say_hello();

    var My2Class = instance.web.Class.extend({
        init: function(name) {
            this.name = name;
        },
        say_hi: function() {
            console.log("hi", this.name);
        }
    });

    var my_2_object = new My2Class("tim");
    my_2_object.say_hi();

    var subClass = MyClass.extend({
        say_hello: function() {
            console.log("hello from subclass to", this.name);
        }
    });

    var sc_obj = new subClass();
    sc_obj.name = "bobo";
    sc_obj.say_hello();

    var sub2Class = My2Class.extend({
        say_hi: function() {
            this._super();
//            console.log(this._super());
            console.log("sub2Class says hello to ", this.name);
        }
    });

    var sc2obj = new sub2Class("timi");
    sc2obj.say_hi();


    var extension = instance.web.Class.extend({
        testMethod: function() {
            return "extend";
        },
    });

    extension.include({
        testMethod: function() {
            return this._super() + " me";
        },
    });

    console.log(new extension().testMethod());

//  --------------------------------------------------------------------------------------------------------------------

    instance.web.client_actions.add('petstore.homepage', 'instance.oepetstore.HomePage');
    instance.web.form.widgets.add('char2', 'instance.oepetstore.FieldChar2');
    instance.web.form.widgets.add('color', 'instance.oepetstore.FieldColor');
    instance.web.form.custom_widgets.add('coordinates', 'instance.oepetstore.WidgetCoordinates');


}
