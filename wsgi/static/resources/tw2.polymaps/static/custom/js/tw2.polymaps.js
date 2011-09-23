
var po = org.polymaps;

function setupPolymap(args, api_key, tileset_id,
        center_latlon, center_range,
        zoom, zoom_range)
{
        var map = po.map();
        map.container(
                document.getElementById(args.id+":target")
                .appendChild(po.svg("svg"))
        );

        // http://cloudmade.com/register
        map.add(po.image()
        .url(po.url("http://{S}tile.cloudmade.com/" + api_key
                + "/" + tileset_id + "/256/{Z}/{X}/{Y}.png")
                .hosts(["a.", "b.", "c.", ""])));

        if ( center_latlon ) { map.center(center_latlon); }
        if ( center_range ) { map.centerRange(center_range); }
        if ( zoom ) { map.zoom(zoom); }
        if ( zoom_range ) { map.zoomRange(zoom_range); }

        // Singleton:
        if ( window._polymapwidgets === undefined ) {
                window._polymapwidgets = {};
        }
        window._polymapwidgets[args.id] = map;

        return map;
}

function setupPolymapControls(
        map, arrow, compass, dblclick, drag,
        grid, hash, interact, wheel)
{
        if ( arrow ) { map.add(po.arrow()); }
        if ( compass ) { map.add(po.compass()); }
        if ( dblclick ) { map.add(po.dblclick()); }
        if ( drag ) { map.add(po.drag()); }
        if ( grid ) { map.add(po.grid()); }
        if ( hash ) { map.add(po.hash()); }
        if ( interact ) { map.add(po.interact()); }
        if ( wheel ) { map.add(po.wheel()); }
        return map;
}

function setupPolymapData(map, data_url, timeout, properties_callback)
{
        if ( data_url ) {
                var layer = po.geoJson().url(data_url);
                if ( properties_callback ) {
                        layer = properties_callback(layer);
                }
                map.add(layer);
                if ( timeout != 0 ) {
                        setTimeout(function(){
                                map.remove(layer);
                                delete layer;
                        }, timeout);
                }
        }
}

function setupPolymapPollingData(map, data_url, interval, timeout)
{
        if ( data_url ) {
                var layer = po.geoJson().url(data_url)
                map.add(layer);

                setTimeout( function () {
                        setupPolymapPollingData(map, data_url, interval, timeout);
                }, interval );

                if ( timeout != 0 ) {
                        setTimeout(function(){
                                map.remove(layer);
                                delete layer;
                        }, timeout);
                }
        }
}

function addGeoJsonToPolymap(id, json, timeout) {
        var map = window._polymapwidgets[id];
        var layer = po.geoJson().features(json['features']);
        map.add(layer);
        if ( timeout != 0 ) {
                setTimeout(function(){
                        map.remove(layer);
                        delete layer;
                }, timeout);
        }
}
