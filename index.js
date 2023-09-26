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

var remoteIcon = L.icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const events = [
  {
    id: 186,
    name: "March 2023",
  },
  {
    id: 187,
    name: "April 2023",
  },
  {
    id: 188,
    name: "May 2023",
  },
  {
    id: 189,
    name: "June 2023",
  },
  {
    id: 190,
    name: "July 2023",
  },
  {
    id: 191,
    name: "August 2023",
  },
  {
    id: 192,
    name: "September 2023",
  },
  {
    id: 193,
    name: "October 2023",
  },

];

const CITY_COLORS = {
  active: "#00FF00",
  defunct: "#FF0000",
  hiatus: "yellow",
};

layerControl = L.control.layers([], [], { collapsed: false }).addTo(map);

function event_ids_to_names(event_ids) {
  return event_ids
    .map((id) => events.find((event) => event.id == id).name)
    .join(", ");
}

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
        popup += `<p>status: ${
          properties.status
        }</p><p>past events: ${event_ids_to_names(
          properties.event_ids
        )}</p><p>past remote/inactive events: ${event_ids_to_names(
          properties.remote_event_ids
        )}`;
        layer.bindPopup(popup);
      },
    });
    geojsonLayer.addTo(map);
    layerControl.addOverlay(geojsonLayer, "Cities");
  });

processedEvents = 0;
events.forEach((event) => {
  fetch(`./data/locations_${event.id}.geojson`)
    .then((response) => response.json())
    .then((locations) => {
      var geojsonLayer = new L.GeoJSON(locations, {
        pointToLayer: function (feature, latlng) {
          if (feature.properties.address) {
            return L.marker(latlng);
          } else {
            return L.marker(latlng, { icon: remoteIcon });
          }
        },
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
              ` (${event.name})</span></p>`;
          }

          if (properties.address) {
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
          }
          popup += `<p>${properties.notes}</p>`;
          layer.bindPopup(popup);
        },
      });
      event["geojsonLayer"] = geojsonLayer;
      processedEvents++;
      // All geojsons are loaded, so display the overlay toggles in order
      if (processedEvents == events.length) {
        events.forEach((event) => {
          layerControl.addOverlay(event.geojsonLayer, event.name);
        });

        // Display the most recent event's layer
        events[events.length - 1].geojsonLayer.addTo(map);
      }
    });
});
