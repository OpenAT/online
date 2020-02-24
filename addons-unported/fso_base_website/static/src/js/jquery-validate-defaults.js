//$(document).ready(function () {

    // https://jsfiddle.net/dark_diesel/gzmwtvh3
    // http://stackoverflow.com/questions/18754020/bootstrap-3-with-jquery-validation-plugin
    jQuery.validator.setDefaults({
        ignore: '.data-rule-ignore, :hidden',
        errorPlacement: function(error, element) {
            // removes error labels
          },
        highlight: function (element, errorClass, validClass) {
            if (element.type === "radio") {
                this.findByName(element.name).addClass(errorClass).removeClass(validClass);
            }
            $(element).closest('.form-group').removeClass('has-success has-feedback').addClass('has-error has-feedback');
            $(element).closest('.form-group').find('span.form-control-feedback').remove();
            $(element).closest('.form-group').append('<span class="glyphicon glyphicon-remove form-control-feedback"></span>');
        },
        unhighlight: function (element, errorClass, validClass) {
            if (element.type === "radio") {
                this.findByName(element.name).removeClass(errorClass).addClass(validClass);
            }
            $(element).closest('.form-group').removeClass('has-error has-feedback').addClass('has-success has-feedback');
            $(element).closest('.form-group').find('span.form-control-feedback').remove();
            $(element).closest('.form-group').append('<span class="glyphicon glyphicon-ok form-control-feedback"></span>');
        },
    });



//});
