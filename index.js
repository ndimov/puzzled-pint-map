var attr_osm =
  'Map data &copy; <a href="http://openstreetmap.org/">OpenStreetMap</a> contributors';

var osm = new L.TileLayer(
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {
    opacity: 0.7,
    attribution: attr_osm,
  }
);

var map = new L.Map("map").addLayer(osm).setView([39.82, -98.58], 3);

const eventIds = {
  "June 2023": 189,
  "July 2023": 190,
}

layerControl = L.control.layers().addTo(map);

Object.keys(eventIds).forEach((key) => {
  eventId = eventIds[key];

  fetch(`./data/locations_${eventId}.geojson`)
    .then((response) => response.json())
    .then((locations) => {
      var geojsonLayer = new L.GeoJSON(locations, {
        onEachFeature: function (feature, layer) {
          const properties = feature.properties;
          layer.bindPopup(
            `<h3>${properties.name}</h3><a href=${properties.bar_url}>${properties.bar}</a><p>${properties.address}</p><p>${properties.notes}</p>`
          );
        },
      })
      layerControl.addOverlay(geojsonLayer, key);
    });
})