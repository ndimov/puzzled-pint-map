"""
Parses the locations from a Puzzled Pint URL and saves them to a geojson
"""

import json
import logging
import os
import pickle
import re

import requests
from geopy.geocoders import GoogleV3, Nominatim
from dotenv import load_dotenv

load_dotenv()

KNOWN_ADDRESSES_FILE = "known_addresses.pkl"


def get_location(address, known_addresses):
    """Given an address dictionary, return a tuple (full_address, location, whether the full address was successfully geocoded)"""
    # Get the latitude and longitude from this dictionary by geocoding the address
    # Format example {"street_1":"5600 Roswell Rd","street_2":"F210","city":"Atlanta","state":"GA","postal_code":"30342","country":"US"}
    # Note we are ignoring street address line 2 for now, it shouldn't be needed
    state = address.get("state")
    state_str = f"{state} " if state else ""
    full_address = (
        f"{address['street_1']}, {address['city']}, {state_str}{address['postal_code']}"
    )
    logging.debug("Geocoding address: ", full_address)
    if full_address in known_addresses:
        logging.debug("Using cached address")
        location = known_addresses[full_address]
    else:
        # locator = Nominatim(user_agent="puzzled-pint-map")
        locator = GoogleV3(api_key=os.environ["GOOGLE_API_KEY"])
        location = locator.geocode(full_address)
        if not location:
            logging.warning(f"Could not geocode {full_address}")
            logging.warning(f"Geocoding the city instead.")
            location = locator.geocode(address["city"])
            logging.debug(location)
        logging.info(f"Found location: {location}")
        known_addresses[full_address] = location
    # Check if the address contains any digits
    # If it does, we assume it's a full address
    # If it doesn't, we assume it's just a city
    successful_geocode = re.search(r"\d", location.address) is not None
    return (full_address, location, successful_geocode)


def parse_city_info_to_geojson(city_info, known_addresses, geojson, city_group=None):
    city = city_info["city"]
    logging.info(f"Parsing city {city}")
    locations = city_info.get("locations")
    address = city_info.get("address")
    if locations:
        # We're actually in a city group, so parse the nested locations
        for location in locations:
            parse_city_info_to_geojson(
                location, known_addresses, geojson, city_group=city
            )
        if address:
            logging.warning(
                f"Location {city} has nested locations, but also an address. Skipping address."
            )
        return
    if not address:
        logging.warning(f"Could not find address for {city}. City info: {city_info}")
        return
    address_str, location, success = get_location(address, known_addresses)
    if not location:
        logging.warning(f"Could not find location for {city}.")
        return
    name = city
    if city_group:
        name = f"{city_group} - {city}"
    feature = {
        "type": "Feature",
        "properties": {
            "name": name,
            "bar": city_info.get("bar"),
            "bar_url": city_info.get("bar_url"),
            "address": address_str,
            "successful_geocode": success,
            "start_time": city_info.get("start_time"),
            "stop_time": city_info.get("stop_time"),
            "notes": city_info.get("notes"),
        },
        "geometry": {
            "type": "Point",
            "coordinates": [location.longitude, location.latitude],
        },
    }
    # Add the feature to the geojson
    geojson["features"].append(feature)


def get_locations(event_id):
    url = f"https://puzzledpint.com/legacy-pp-locations.php?id={event_id}"

    # Create a geojson
    geojson = {"type": "FeatureCollection", "features": []}

    # Get the JSON locations from the above url
    response = requests.get(url)
    response_json = response.json()
    try:
        known_addresses = pickle.load(open(KNOWN_ADDRESSES_FILE, "rb"))
    except FileNotFoundError:
        known_addresses = {}
    for city_info in response_json["locations"]:
        parse_city_info_to_geojson(city_info, known_addresses, geojson)

    pickle.dump(known_addresses, open(KNOWN_ADDRESSES_FILE, "wb"))
    # Save the geojson
    with open(f"data/locations_{event_id}.geojson", "w+") as outfile:
        json.dump(geojson, outfile)


if __name__ == "__main__":
    get_locations(190)
