/// <reference path='/austria_data/bundeslaender_und_gemeinden.js'/>

var state_data_glo = [];
var community_data_glo = [];

$(document).ready(function () {
'use strict'

    $('#wrap').after('<div id="gardenMapInfoBox"/>');
    $('#gardenMapInfoBox').after('<div id="gardenMap">');
    $('#gardenMap').after('<div id="gardenMapGallery"/>');

    var jsonDomain = 'https://demo.datadialog.net';

    /* CONFIG END */

    var gardenMap;
    var state_data = null, community_data = null;
    var galleryData;

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
        showInfoBox();

        gardenMap.on('zoomend', function () {
            var zoomLevel = gardenMap.getZoom();
            if (zoomLevel < 10) {
                gardenMap.removeLayer(geoAustriaCommunities);
                removeMarkerCommunity();
                addMarkerState();
                gardenMap.addLayer(geoAustriaState);
            } else if ((zoomLevel >= 10) && (zoomLevel < 11)) {
                gardenMap.removeLayer(geoAustriaState);
                removeMarkerState();
                gardenMap.addLayer(geoAustriaCommunities);
            } else if (zoomLevel >= 11) {
                addMarkerCommunity();
            }
        });
    }


//-----------------------------------------------------------------------------------
// GeoJson

//    function getColor(d) {
//        return d > 1000
//            ? "#006d2c"
//            : d > 500
//                ? "#31a354"
//                : d > 200
//                    ? "#74c476"
//                    : d > 100
//                        ? "#bae4b3"
//                        : d > 50
//                            ? "#edf8e9"
//                            : d > 20 ? "#FEB24C" : d > 10 ? "#FED976" : "#FFEDA0";
//    }

    function fillMap(size) {
        if (size > 0) {
            return '#006d2c';
        } else {
            return 'transparent';
        }
    }

    function styleCommunity(feature) {
        return {
            weight: 1,
            opacity: 1,
            color: "grey",
            dashArray: "1",
            fillOpacity: feature.properties.opacityValue,
            fillColor: fillMap(feature.properties.opacityValue),
        };
    }

    function style(feature) {
        return {
            weight: 2,
            opacity: 1,
            color: "black",
            dashArray: "3",
            fillOpacity: feature.properties.opacityValue,
            fillColor: fillMap(feature.properties.opacityValue),
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
                    gardenSize = state_data[0][i].garden_size_peg;
//                    gardenSize = state_data[0][i].garden_size;
                }
            }
        } else if (feature.properties.rtype === 'gemeinde') {
            for (var i = 0; i < community_data[0].length; i++) {
                nameData = filterName(community_data[0][i].cmp_community);
                nameGeo = filterName(feature.properties.name);
                if (nameGeo === nameData) {
                    gardenSize = community_data[0][i].garden_size_peg;
//                    gardenSize = community_data[0][i].garden_size;
                }
            }
        }
        feature.properties.opacityValue = gardenSize;
//        feature.properties.aream2 = gardenSize;
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
        });
        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
            layer.bringToFront();
        }
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
            style: styleCommunity,
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

        console.log(state_data)
        var cnt = 0;
        for (var j = 0; j < state_data[0].length; j++) {
            if(state_data[0][j].thumbnail_record_ids) {
                for (var i = 0; i < stateCenter.length; i++) {
                    if (stateCenter[i][0] === filterName(state_data[0][j].cmp_state)) {
                        var marker = L.marker([stateCenter[i][1], stateCenter[i][2]], {
                            icon: L.divIcon({
    //                            html: '<i id="' + state_data[0][j].cmp_state_id + '" class="fa fa-picture-o iconState" onclick="showGallery()"></i>',
                                html: '<img id="' + state_data[0][j].cmp_state_id + " bundesland" + '" class="gardenMapIcon" src="/website_map/static/src/img/camera.png" onclick="showGallery(this)">',
                            })
    //                        icon: L.icon({
    //                            iconUrl: '/website_map/static/src/img/camera.png',
    //                            iconSize: [40, 40],
    //                        })
                        });
                        stateMarker.push(marker);
                        gardenMap.addLayer(stateMarker[cnt]);
                        cnt++;
                    }
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

        var cnt = 0;
        for (var i = 0; i < community_data[0].length; i++) {
            if(community_data[0][i].thumbnail_record_ids) {
                communityCenter = [parseFloat(community_data[0][i].latitude), parseFloat(community_data[0][i].longitude)];
                var marker = L.marker(communityCenter, {
                    icon: L.divIcon({
    //                    html: '<i id="' + community_data[0][i].cmp_community_code + '" class="fa fa-picture-o iconState" onclick="showGallery()"></i>',
                        html: '<p class="gardenMapCommunityM2">' + community_data[0][i].garden_size + '</p><img id="' + community_data[0][i].cmp_community_code + " gemeinde" + '" class="gardenMapIcon" src="/website_map/static/src/img/camera.png" onclick="showGallery(this)">',
                    })
                });
                communityMarker.push(marker);
                gardenMap.addLayer(communityMarker[cnt]);
                cnt++;
            }
        }

    }

    function removeMarkerCommunity() {
        for(var i = 0; i < communityMarker.length; i++) {
            gardenMap.removeLayer(communityMarker[i]);
        }
    }

//-----------------------------------------------------------------------------------
// GardenMap Infobox
    function showInfoBox() {
        var maxGardenSize = 0;
        for (var i = 0; i < state_data[0].length; i++) {
            maxGardenSize = maxGardenSize + state_data[0][i].garden_size;
        }
        $("#gardenMapInfoBox").wrapInner("<p>" + maxGardenSize + " m²</p>" +
                                  "<p>Nationalpark in</p>" +
                                  "<p>Österreichs Gärten</p>");
    }
});

//-----------------------------------------------------------------------------------
// GardenMap Gallery
function showGallery(e) {
    var callerID = parseInt(e.id.replace(/[a-z]/g, "").replace(/\ /g, ''));
    var callerIDName = e.id.replace(/[0-9]/g, "").replace(/\ /g, '');

    if (callerIDName === 'bundesland') {
        for (var i = 0; i < state_data_glo.length; i++) {
            if (callerID === state_data_glo[i].cmp_state_id) {
                galleryData = state_data_glo[i];
            }
        }
    } else if (callerIDName === 'gemeinde') {
        for (var i = 0; i < community_data_glo.length; i++) {
            if (String(callerID) === community_data_glo[i].cmp_community_code) {
                galleryData = community_data_glo[i];
            }
        }
    }

    var gallery = $('#gardenMapGallery');

    gallery.wrapInner('<div id="gardenMapModal" class="gardenModal">' +
                      '<img class="closeBtnGardenMap" src="/website_map/static/src/img/close.png" onclick="closeGallery()"/>' +
                      '<img class="moveBtnGardenMapPrev" src="/website_map/static/src/img/arrow-left.png" onclick="moveImg(-1)"/>' +
                      '<img class="moveBtnGardenMapNext" src="/website_map/static/src/img/arrow-right.png" onclick="moveImg(1)"/>' +
                      '<div class="gardenMapModalContent">' +
                      '<div class="gardenMapFrontImageContainer">' +
                      '<img id="gardenMapFrontImage" src="/website/image/gl2k.garden/' + galleryData.record_ids[0] + '/cmp_image_file">' +
                      '</div>' +
                      '</div>');

    insertThumbnail(galleryData);

    document.getElementById('gardenMapGallery').style.display = "block";
}

function closeGallery() {
    document.getElementById('gardenMapGallery').style.display = "none";
}

function insertThumbnail(galleryData) {
    var galleryModal = $('#gardenMapModal');

    for (var i = 0; i < galleryData.thumbnail_record_ids.length; i++) {
        galleryModal.append('<div class="gardenMapColumn">' +
                            '<img class="gardenMapThumbnail" src="/website/image/gl2k.garden/' + String(galleryData.thumbnail_record_ids[i]) + '/cmp_thumbnail_file " onclick="selectImg(' + galleryData.thumbnail_record_ids[i] + ')"/>' +
                            '</div>');
    }
}

//function querryImage(id, thumb) {
//        var jsonDomain = 'https://demo.datadialog.net';
//
//        try {
//
//            var jsonParams = {"params": {
//                                  "thumbnail_record_ids": thumb,
//                                  "image_record_id": id
//                              }};
//
//            $.ajax({
//                url: jsonDomain + "/gl2k/garden/image",
//                type: 'POST',
//                contentType: 'application/json; charset=utf-8',
//                dataType: 'json',
//                data: JSON.stringify(jsonParams),
//                error: function (data) {
//                    console.log('ERROR');
//                    console.log(data);
//
//                    return;
//                },
//                success: function (data) {
//                    console.log('SUCCESS');
//                    console.log(data);
//                }
//            });
//        } catch (error) {
//            console.log('Error', error);
//            return;
//        }
//}

var slideIndex = 1;

function moveImg(n) {
    (slideIndex += n);
    if ((slideIndex < galleryData.thumbnail_record_ids.length) && (slideIndex > 0)) {

    } else if (slideIndex < 0) {
        slideIndex = galleryData.thumbnail_record_ids.length - 1;
    } else {
        slideIndex = 0
    }
    selectImg(galleryData.record_ids[slideIndex]);
}

function selectImg(id) {
    var frontImage = document.getElementById('gardenMapFrontImage');
    frontImage.src = '/website/image/gl2k.garden/' + id + '/cmp_image_file';
    frontImage.parentElement.style.display = 'block';
}
