jQuery(document).ready(function(){     

    var status = "maybe",
        lats = [],
        longs = [],
        type, ip, geo, status, deviceIcon, marker, stats, zoom, popUpText, //keep vars global

        btsIcon = L.icon({
            iconUrl: 'img/bts.png',
            iconSize: [45, 45], // size of the icon
            iconAnchor: [20, -20], // point of the icon which will correspond to marker's location
            popupAnchor: [-5, 20] // point from which the popup should open relative to the iconAnchor
        }),
        bscIcon = L.icon({
            iconUrl: 'img/bsc.png',
            iconSize: [45, 45], // size of the icon
            iconAnchor: [20, -20], // point of the icon which will correspond to marker's location
            popupAnchor: [30, 5] // point from which the popup should open relative to the iconAnchor
        }),
        linkIcon = L.icon({
            iconUrl: 'img/link.png',
            iconSize: [45, 45], // size of the icon
            iconAnchor: [0, 10], // point of the icon which will correspond to marker's location
            popupAnchor: [5, -5] // point from which the popup should open relative to the iconAnchor
        }),
    // place the legend properly if big window
    contentHeight = $("#container").height(),
    legendHeight =$("table#legend").height(),
    legendOffset = contentHeight-legendHeight-15,
    windowHeight = $(window).height();

    $(window).on("load resize",function(){
        if (windowHeight > contentHeight) {
                 $("#legend").css("top",legendOffset);
        }
    });

    // set up the initial map
    var map = L.map('map').setView([ 17.066409, -96.729473], 2);

    // get json data
    var network = $.getJSON("js/localnet.json", function(data) {}).fail(function() {
        console.log("Can't find any devices???");
    });

    // when done getting json make a map
    network.done(function(net) {

        // get the tiles from mapBox
        L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
            attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
            maxZoom: 18,
            id: 'multilectical.n3mbdga4',
            accessToken: 'pk.eyJ1IjoibXVsdGlsZWN0aWNhbCIsImEiOiJiZmQ3NzViNGI3NTBhNzdiMzk0NGI3ZmUyMTVhZjgzMSJ9.K0fI8HFCQvmHqk0S9RY4Sw'
        }).addTo(map);


        // loop through devices
        for (var key in net) {
            if (net.hasOwnProperty(key)) {

                // make vars of all the things
                type = net[key].type,
                ip = net[key].ip,
                geo = net[key].geo;

                // use the opportunity to make arrays of boundaries for map resizing
                lats.push(net[key].geo[0]);
                longs.push(net[key].geo[1]);

                // throw the ip to php
                status = pingStatus(ip, type, geo);

            }

        }

        // resize map

        var zoom = .006,
            enlarge = largestLat = Math.max.apply(Math, lats) + zoom,
            smallestLat = Math.min.apply(Math, lats) - zoom,
            largestLon = Math.max.apply(Math, longs) + zoom,
            smallestLon = Math.min.apply(Math, longs) - zoom;

        var southWest = L.latLng(smallestLat, smallestLon),
            northEast = L.latLng(largestLat, largestLon),
            bounds = L.latLngBounds(southWest, northEast);
        map.fitBounds(bounds);

    });

    function pingStatus(ip, type, geo) {

        $.ajax({
            method: "POST",
            url: "ping.php",
            data: {
                ip
            }
        })
            .done(function(status) {

                //make an iconout of the type var
                deviceIcon = eval(type.concat("Icon"));

                // traducir cosas
                switch(status){
                    case 'up': popUpText = 'En línea :)';
                    break;
                    case 'down': popUpText = 'desconectado :(';
                    break;
                }

                marker = L.marker(geo, {
                    icon: deviceIcon
                }, {
                    title: ip
                }).addTo(map).bindPopup(type + " <br>" + ip + "<br> Estatus: " + popUpText);

                $(marker._icon).addClass(status);

                console.log(ip + ": " + status);

            })
            .fail(function() {
                console.log("failaed to ajjjaaxx");
                $("#outsideWorld").prepend("<h1 class=\"error\">error: gran fracasado en encontrar la red</h1>");
            });
    }

});