/*!
 * jQuery Validation Plugin v1.15.0
 *
 * http://jqueryvalidation.org/
 *
 * Copyright (c) 2016 Jörn Zaefferer
 * Released under the MIT license
 */
// Add a new Valdiator for German Dates
$.validator.addMethod("dateDEBirthdate", function (value, element) {
    // Use moment.js to validate the date input
    // HINT: If nothing is passed to moment#isBefore, it will default to the current time.
    var test = moment(value, 'DD.MM.YYYY', 'de', true).isBetween('1900-01-01', moment().add(1, 'd'), 'year');
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
