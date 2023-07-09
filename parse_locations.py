"""
Parses the locations from a Puzzled Pint URL and saves them to a geojson
"""

import json
import logging
import os
import pickle
import re
import shutil
import sys

import requests
from geopy.geocoders import GoogleV3, Nominatim

from geocode import geocode_address

KNOWN_ADDRESSES_FILE = "known_addresses.pkl"
PRESENT_ID = 190


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
        location = geocode_address(full_address)
        if not location:
            logging.warning(f"Could not geocode {full_address}")
            logging.warning(f"Geocoding the city instead.")
            location = geocode_address(address["city"])
            logging.debug(location)
        logging.info(f"Found location: {location}")
        known_addresses[full_address] = location
    # Check if the address contains any digits
    # If it does, we assume it's a full address
    # If it doesn't, we assume it's just a city
    successful_geocode = re.search(r"\d", location.address) is not None
    return (full_address, location, successful_geocode)


def parse_city_info_to_geojson(
    city_info, known_addresses, geojson, event_id, city_group=None
):
    city = city_info["city"].strip()  # Philadelphia has a trailing whitespace
    logging.info(f"Parsing city {city}")
    locations = city_info.get("locations")
    address = city_info.get("address")
    if locations:
        # We're actually in a city group, so parse the nested locations
        for location in locations:
            parse_city_info_to_geojson(
                location, known_addresses, geojson, event_id, city_group=city
            )
        if address:
            logging.warning(
                f"Location {city} has nested locations, but also an address. Skipping address."
            )
        return
    if address:
        address_str, location, success = get_location(address, known_addresses)
        if not location:
            logging.warning(f"Could not find location for {city}.")
            return
        update_city_json(city, True, city_group, event_id)
        latitude, longitude = location.latitude, location.longitude
    else:
        logging.warning(f"Could not find address for {city}. City group: {city_group} City info: {city_info}")
        if city_group in ["Seattle", "Bay Area"]:
            # These places list two events on the same page, so we could update it manually
            # FIXME currently we just put a pin at the city because manual parsing is expensive
            manual_locations = True
        matched_city = update_city_json(city, False, city_group, event_id)
        if not matched_city:
            logging.warning(f"Not placing icon because city coordinates are not known")
            return
        coordinates = matched_city["coordinates"]
        latitude, longitude = coordinates["latitude"], coordinates["longitude"]
        address_str = None
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
            # "successful_geocode": success,
            "start_time": city_info.get("start_time"),
            "stop_time": city_info.get("stop_time"),
            "notes": re.sub("&nbsp;", " ", city_info.get("notes")),
        },
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
    }
    # Add the feature to the geojson
    geojson["features"].append(feature)


def update_city_json(city, found_address, city_group, event_id):
    """
    Updates the status of the city based on its presence in the event.
    Returns the updated city json.
    """

    search_name = city
    if city_group and city_group != "Bay Area":
        search_name = f"{city_group} ({city})"

    for shortcut_substring in ["Arlington", "Jersey City"]:
        if shortcut_substring in search_name:
            search_name = shortcut_substring

    # Backup the json before we overwrite it
    shutil.copyfile("data/cities.json", "data/cities_backup.json")
    cities_json = json.load(open("data/cities.json", "r"))
    matched_city = None
    for i, c in enumerate(cities_json):
        if search_name in c["name"]:
            matched_city = c
            matched_city_index = i
            break
    if not matched_city:
        logging.warning(f"Could not find city {search_name} in cities.json")
        return

    logging.info(f"Updating city {matched_city['name']} with event {event_id}")

    if event_id in matched_city["event_ids"]:
        return matched_city

    if found_address or (city_group, city) in [("Bay Area", "San Francisco"), ("Seattle", "City")]:
        matched_city["event_ids"].append(int(event_id))
        matched_city["event_ids"] = sorted(list(set(matched_city["event_ids"])), reverse=True)
        if PRESENT_ID - event_id <= 3:
            matched_city["status"] = "active"
    else:
        if PRESENT_ID - event_id <= 3:
            matched_city["status"] = "hiatus"
    # TODO: set active/hiatus events to defunct if they haven't appeared recently
    cities_json[matched_city_index] = matched_city
    json.dump(cities_json, open("data/cities.json", "w+"))
    return matched_city


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
        parse_city_info_to_geojson(city_info, known_addresses, geojson, event_id)

    pickle.dump(known_addresses, open(KNOWN_ADDRESSES_FILE, "wb"))
    # Save the geojson
    with open(f"data/locations_{event_id}.geojson", "w+") as outfile:
        json.dump(geojson, outfile)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_locations.py <first_event_id> [second_event_id]")
        sys.exit()
    first_event_id = sys.argv[1]
    if len(sys.argv) == 3:
        second_event_id = sys.argv[2]
    else:
        second_event_id = first_event_id

    for event_id in range(int(first_event_id), int(second_event_id) + 1):
        get_locations(event_id)
