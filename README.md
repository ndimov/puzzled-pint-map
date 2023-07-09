# About
This tool generates a map of current and historical Puzzled Pint locations. [View it online](https://ndimov.com/puzzled-pint-map/)!

# Background

[Puzzled Pint](https://puzzledpint.com/) is a casual puzzle-solving event hosted in many cities across the world on the second Tuesday of each month. Whenever I find myself in a new city or country, I wonder where I can find a Puzzled Pint event near me. The current site has no easy way to search for this. The list of locations on the homepage helps, but it includes many defunct sites that have been inactive for a while.

# Implementation

The `parse_locations.py` script fetches the location data from the Puzzled Pint API for the specified event IDs. It then geocodes the addresses (with caching into a pickle file for known addresses) and saves a geojson with each location as a point feature. Currently, this script must be run manually to update the website with any changes.

The `parse_cities.py` script is intended to be run rarely, and parses the list of locations (cities) on the Puzzled Pint homepage. These are saved to `data/cities.json`. This file should be manually adjusted, for example to fix the coordinates for region names that are incorrectly geocoded.

The frontend loads these json data files and serves them on a map using Leaflet.

More notes and todos can be found at [DEVELOPMENT.md](DEVELOPMENT.md).