/*!
 * jQuery Validation Plugin v1.15.0
 *
 * http://jqueryvalidation.org/
 *
 * Copyright (c) 2016 Jörn Zaefferer
 * Released under the MIT license
 */
// Add a new Valdiator for German Dates
$.validator.addMethod("dateDEBirthdate", function (value, element, params) {
    // Use moment.js to validate the date input
    // HINT: If nothing is passed to moment#isBefore, it will default to the current time.
    var test = moment(value, 'DD.MM.YYYY', 'de', true).isBetween('1900-01-01', moment().add(1, 'd'), 'year');
    // Debug
    // console.log(value);
    // console.log(test);
    // HINT: .optional() is there to return true as long as the input is empty
    return this.optional(element) || test;
}, $.validator.messages.date);

$.validator.addMethod("dateDE", function (value, element, params) {
    // Use moment.js to validate the date input
    // HINT: If nothing is passed to moment#isBefore, it will default to the current time.
    var test = moment(value, 'DD.MM.YYYY', 'de', true).isBetween('1900-01-01', moment().add(1, 'y'), 'year');
    // Debug
    // console.log(value);
    // console.log(test);
    // HINT: .optional() is there to return true as long as the input is empty
    return this.optional(element) || test;
}, $.validator.messages.date);

$.validator.addMethod("floatDE", function (value, element) {
    // HINT: .optional() is there to return true as long as the input is empty
    return this.optional( element ) || /^[0-9]+[,]*[0-9]*$/.test( value );
}, $.validator.messages.number);

$.validator.addMethod("floatDEmin", function (value, element, params) {
    // console.log('floatDEmin');
    // HINT: .optional() is there to return true as long as the input is empty
    if (!(this.optional( element ) || /^[0-9]+[,]*[0-9]*$/.test( value ))) {
        // console.log('WRONG FORMAT');
        return false
    }

    var value_float = parseFloat(value.replace(/,/g, "."));
    var compare_float = parseFloat(params);
    // console.log(value_float);
    // console.log(compare_float);
    return this.optional( element ) || value_float >= compare_float;

}, $.validator.messages.number);
