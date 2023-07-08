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
};

const CITY_COLORS = {
  active: "#00FF00",
  defunct: "#FF0000",
};

layerControl = L.control.layers([], [], { collapsed: false }).addTo(map);

fetch("./data/cities.json")
  .then((response) => response.json())
  .then((cities) => {
    var geojson = { type: "FeatureCollection", features: [] };
    cities.forEach((city) => {
      geojson.features.push({
        type: "Feature",
        properties: city,
        geometry: {
          type: "Point",
          coordinates: [city.coordinates.longitude, city.coordinates.latitude],
        },
        style: {
          color: CITY_COLORS[city.status],
        },
      });
    });
    console.log(geojson);

    var geojsonLayer = new L.GeoJSON(geojson, {
      pointToLayer: function (feature, latlng) {
        // Using circles because markers are harder to re-color
        return L.circleMarker(latlng, {
          radius: 5,
          fillColor: feature.style.color,
          fillOpacity: 0.5,
          color: "#000",
          weight: 1,
        });
      },
      onEachFeature: function (feature, layer) {
        const properties = feature.properties;
        let popup = `<h3><a href="${properties.url}">${properties.name}</a></h3>`;
        layer.bindPopup(popup);
      },
    });
    geojsonLayer.addTo(map);
    layerControl.addOverlay(geojsonLayer, "Cities");
  });

Object.keys(eventIds).forEach((key) => {
  eventId = eventIds[key];

  fetch(`./data/locations_${eventId}.geojson`)
    .then((response) => response.json())
    .then((locations) => {
      var geojsonLayer = new L.GeoJSON(locations, {
        onEachFeature: function (feature, layer) {
          const properties = feature.properties;
          let popup = `<h3>${properties.name}</h3>`;
          if (properties.start_time) {
            regex = /0([1-9]:[0-9][0-9]) ?([ap]m)/;
            start_match = properties.start_time.match(regex);
            stop_match = properties.stop_time.match(regex);
            start = properties.start_time;
            stop = properties.stop_time;
            if (start_match && start_match.length == 3) {
              start = start_match[1] + start_match[2];
            }
            if (stop_match && stop_match.length == 3) {
              stop = stop_match[1] + stop_match[2];
            }
            popup +=
              '<p><i class="fa fa-clock-o"></i> <span>' +
              start +
              " – " +
              stop +
              "</span></p>";
          }

          var barText;
          if (properties.bar_url) {
            barText = `<a href=${properties.bar_url}>${properties.bar}</a>`;
          } else {
            barText = properties.bar;
          }
          popup += `<span><i class="fa fa-map-marker"></i> ${barText}</span><br />`;
          popup += `<span>${
            properties.address
          } (<a href=https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
            properties.address
          )} target="_blank">Google Maps</a>)</span>`;
          popup += `<p>${properties.notes}</p>`;
          layer.bindPopup(popup);
        },
      });
      // geojsonLayer.addTo(map);
      layerControl.addOverlay(geojsonLayer, key);
    });
});
