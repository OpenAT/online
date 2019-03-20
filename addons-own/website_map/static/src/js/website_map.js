/// <reference path='/austria_data/bundeslaender_und_gemeinden.js'/>

var state_data_glo = [];
var community_data_glo = [];

$(document).ready(function () {
'use strict'

    $('#wrap').after('<div id="gardenMap"/>');
    $('#gardenMap').after('<div id="myModal"/>');

    var jsonDomain = 'https://demo.datadialog.net';
    var dirBase = 'http://demo.local.com/gl2k_gardenvis/static/src/alextest';
    var iconCamera = '/img/camera_small.png';

    var statesKml = '/data/austria_states.kml';         // will be cached for some minutes by google on first calling
    var communityKml = '/data/austria_communities.kml';    // will be cached for some minutes by google on first calling
    /* CONFIG END */

    var gardenMap;
    var state_data = null, community_data = null;
    var dataSuccess = false, imageSuccess = false;

    /* ToDo: Image URL */
    /* ToDo: Check State Centers */


//    $.loadScript = function (url, callback) {
//        $.ajax({
//            url: url,
//            dataType: 'script',
//            success: callback,
//            async: true
//        });
//    };

    try {

        var jsonParams = {"params": {}};

        $.ajax({
            url: jsonDomain + "/gl2k/garden/data",
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            data: JSON.stringify(jsonParams),
            error: function (data) {
                console.log('ERROR');
                console.log(data);

                return;
            },
            success: function (data) {
                state_data = data.result.state_data;
                community_data = data.result.community_data;
                state_data_glo = data.result.state_data[0];
                community_data_glo = data.result.community_data[0];
                dataSuccess = true;
                console.log('SUCCESS');
                console.log(data);
                initMap();
            }
        });
    } catch (error) {
        console.log('Error', error);
        return;
    }

//-----------------------------------------------------------------------------------
// Map initialization

    function initMap() {

        var cornerTop = L.latLng(49.009, 9.245),
            cornerBottom = L.latLng(46.294, 17.155),
            boundary = L.latLngBounds(cornerTop, cornerBottom);

        gardenMap = L.map('gardenMap', {
            center: [47.564, 13.364],
            zoom: 7,
            maxBounds: boundary,
        });

        L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png", {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
            maxZoom: 20,
            minZoom: 7,
            bounds: boundary,
        }).addTo(gardenMap);

        addGeoJsonState();
        addGeoJsonCommunity();
//        addGeoJsonBorder();
        addMarkerState();

        gardenMap.on('zoomend', function () {
            var zoomLevel = gardenMap.getZoom();
            if (zoomLevel < 8) {
                gardenMap.removeLayer(geoAustriaCommunities);
                removeMarkerCommunity();
                addMarkerState();
                gardenMap.addLayer(geoAustriaState);
            } else if ((zoomLevel >= 8) && (zoomLevel < 11)) {
                gardenMap.removeLayer(geoAustriaState);
                removeMarkerState();
                gardenMap.addLayer(geoAustriaCommunities);
            } else if (zoomLevel >= 11) {
                addMarkerCommunity();
            }
        });
    }


    // // control that shows state info on hover
    // var info = L.control();
    // info.onAdd = function(mymap) {
    //   this._div = L.DomUtil.create("div", "info");
    //   this.update();
    //   return this._div;
    // };
    // info.update = function(props) {
    //   this._div.innerHTML =
    //     "<h4>US Population Density</h4>" +
    //     (props
    //       ? "<b>" +
    //       props.name +
    //       "</b><br />" +
    //       props.density +
    //       " people / mi<sup>2</sup>"
    //       : "Hover over a state");
    // };
    // info.addTo(mymap);


//-----------------------------------------------------------------------------------
// GeoJson

    function getColor(d) {
        return d > 1000
            ? "#006d2c"
            : d > 500
                ? "#31a354"
                : d > 200
                    ? "#74c476"
                    : d > 100
                        ? "#bae4b3"
                        : d > 50
                            ? "#edf8e9"
                            : d > 20 ? "#FEB24C" : d > 10 ? "#FED976" : "#FFEDA0";
    }

    function style(feature) {
        return {
            weight: 2,
            opacity: 1,
            color: "black",
            dashArray: "3",
            fillOpacity: 0.7,
            fillColor: getColor(feature.properties.aream2)
        };
    }

    function replaceUmlaute(str) {
        var umlautMap = {
            '\u00dc': 'UE',
            '\u00c4': 'AE',
            '\u00d6': 'OE',
            '\u00fc': 'ue',
            '\u00e4': 'ae',
            '\u00f6': 'oe',
            '\u00df': 'ss',
        };
        return str
            .replace(/[\u00dc|\u00c4|\u00d6][a-z]/g, (a) => {
                var big = umlautMap[a.slice(0, 1)];
                return big.charAt(0) + big.charAt(1).toLowerCase() + a.slice(1);
            })
            .replace(new RegExp('['+Object.keys(umlautMap).join('|')+']',"g"),
                (a) => umlautMap[a]
            );
    }
    function filterName(str) {
        var filtered = replaceUmlaute(str);
        return filtered.replace(/\./g, '').replace(/\-/g, '').replace(/\ /g, '').toLowerCase();
    }

    function setArea(feature) {
        var gardenSize, nameGeo, nameData;
        if (feature.properties.rtype === 'bundesland') {
            for (var i = 0; i < state_data[0].length; i++) {
                nameData = filterName(state_data[0][i].cmp_state);
                nameGeo = filterName(feature.properties.name);
                if (nameGeo == nameData) {
                    gardenSize = state_data[0][i].garden_size;
                }
            }
        } else if (feature.properties.rtype === 'gemeinde') {
            for (var i = 0; i < community_data[0].length; i++) {
                nameData = filterName(community_data[0][i].cmp_community);
                nameGeo = filterName(feature.properties.name);
                if (nameGeo === nameData) {
                    gardenSize = community_data[0][i].garden_size;
                }
            }
        }
        feature.properties.aream2 = gardenSize;
    }

    function resetArea(feature) {
        feature.properties.aream2 = 0.0;
    }

    function highlightFeature(e) {
        var layer = e.target;
        layer.setStyle({
            weight: 5,
            color: "#666",
            dashArray: "",
            fillOpacity: 0.7
        });
        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
            layer.bringToFront();
        }
        // info.update(layer.feature.properties);
    }

    var geoAustriaState, geoAustriaBorder, geoAustriaCommunities;

    function resetHighlight(e) {
        geoAustriaState.resetStyle(e.target);
    }

    function resetHighlightCommunity(e) {
        geoAustriaCommunities.resetStyle(e.target);
    }

    function zoomToFeature(e) {
        gardenMap.fitBounds(e.target.getBounds());
        gardenMap.removeLayer(geoAustriaState);
        removeMarkerState();
        gardenMap.addLayer(geoAustriaCommunities);
    }

    function zoomToFeatureCommunity(e) {
        gardenMap.fitBounds(e.target.getBounds());
    }

    function onEachFeatureState(feature, layer) {
        layer.on({
            mouseover: highlightFeature,
            mouseout: resetHighlight,
            click: zoomToFeature,
        });
    }

    function onEachFeatureCommunity(feature, layer) {
        layer.on({
            mouseover: highlightFeature,
            mouseout: resetHighlightCommunity,
            click: zoomToFeatureCommunity,
        });
    }

    function communityFilter(feature) {
        if (feature.properties.rtype === 'gemeinde') {
            setArea(feature);
            return true;
        }
    }

    function stateFilter(feature) {
        if (feature.properties.rtype === 'bundesland') {
            setArea(feature);
            return true;
        }
    }

    function addGeoJsonCommunity() {
        geoAustriaCommunities = L.geoJson(austriaBG, {
            filter: communityFilter,
            style: style,
            onEachFeature: onEachFeatureCommunity
        });
    }

    function addGeoJsonState() {
        geoAustriaState = L.geoJson(austriaBG, {
            filter: stateFilter,
            style: style,
            onEachFeature: onEachFeatureState
        }).addTo(gardenMap);
    }

//    function addGeoJsonBorder() {
//        geoAustriaBorder = L.geoJson(austriaBG, {
//            filter: stateFilter,
//            style: {
//                weight: 2,
//                opacity: 1,
//                color: "red",
//                dashArray: "3",
//                fillColor: "transparent",
//            },
//        }).addTo(gardenMap);
//    }

//-----------------------------------------------------------------------------------
// Marker
    var stateMarker = new Array();
    var communityMarker = new Array();

    function addMarkerState() {

        var stateCenter = [['oberoesterreich',48.2500000, 14.0000000],  //ooe
                           ['niederoesterreich',48.2817813, 15.7632457],  //noe
                           ['wien',48.2083537, 16.3725042],  //vie
                           ['burgenland',47.5000001, 16.4166666],  //bgl
                           ['steiermark',47.2500001, 15.1666665],  //stmk
                           ['kaernten',46.7500001, 13.8333333],  //car
                           ['salzburg',47.4166667, 13.2500000],  //sal
                           ['tirol',47.2231930, 11.5261028],  //tir
                           ['vorarlberg',47.2500000, 9.9166667]];  //vor
        console.log(state_data);
        console.log(stateCenter[0][1]);

//                nameData = filterName(state_data[0][i].cmp_state);
//                nameGeo = filterName(feature.properties.name);
//                if (nameGeo == nameData) {
//                    gardenSize = state_data[0][i].garden_size;
//                }
//            }
        for (var i = 0; i < stateCenter.length; i++) {
            for (var j = 0; j < state_data[0].length; j++) {
                if (stateCenter[j][0] === filterName(state_data[0][j].cmp_state)) {
                    var marker = L.marker([stateCenter[i][1],stateCenter[i][2]], {
//                        icon: L.divIcon({
//                            html: '<i id="' + state_data[0][j].cmp_state_id + '" class="fa fa-picture-o iconState" onclick="showGallery()"></i>',
//                        })
                        icon: L.divIcon({
                            iconUrl: './img/camera.png',
                        })
                    });
                    stateMarker.push(marker);
                    gardenMap.addLayer(stateMarker[i]);
                }
            }
        }
    }

    function removeMarkerState() {
        for(var i = 0; i < stateMarker.length; i++) {
            gardenMap.removeLayer(stateMarker[i]);
        }
    }

    function addMarkerCommunity() {
        var communityCenter = [];

        for (var i = 0; i < community_data[0].length; i++) {
            communityCenter = [parseFloat(community_data[0][i].latitude), parseFloat(community_data[0][i].longitude)];
            var marker = L.marker(communityCenter, {
                icon: L.divIcon({
                    html: '<i class="fa fa-picture-o" onclick="showGallery()"></i>',
                })
            });
            communityMarker.push(marker);
            gardenMap.addLayer(communityMarker[i]);
        }
    }

    function removeMarkerCommunity() {
        for(var i = 0; i < communityMarker.length; i++) {
            gardenMap.removeLayer(communityMarker[i]);
        }
    }
});

function showGallery() {
    console.log(this);
    console.log(state_data_glo);
    console.log(community_data_glo);
//    this.$('#myModal').replaceWith(
//                openerp.qweb.render(
//                    'wm_gallery', {image: rows}));
//    document.getElementById('myModal').style.display = "block";
}
function closeGallery() {
    document.getElementById('myModal').style.display = "none";
}

window.addEventListener('load', function () {
    this.thumbmail = document.getElementsByClassName("slideshow");
    console.log(thumbmail);
    console.log(thumbmail[0]);
    console.log(thumbmail.length);
    selectImg(thumbmail[0]);
});
var slideIndex = 1;

function moveImg(n) {
    (slideIndex += n);
    console.log(slideIndex);
    if ((slideIndex < thumbmail.length) && (slideIndex > 0)) {

    } else if (slideIndex < 0) {
        slideIndex = thumbmail.length - 1;
    } else {
        slideIndex = 0
    }
    console.log(slideIndex);
    selectImg(thumbmail[slideIndex]);
}

function selectImg(img) {
    console.log(img)
    var frontImage = document.getElementById('front_Image');
    frontImage.src = img.src;
    frontImage.parentElement.style.display = 'block';
}
