# Parses the cities from the homepage into cities.json
# Note that this will geocode every city and overwrite the file

import json

from bs4 import BeautifulSoup
from geopy.geocoders import GoogleV3

from geocode import geocode_address


def parse_cities(html):
    soup = BeautifulSoup(html, 'html.parser')
    cities_html = soup.find_all('a')
    cities = []

    for city_html in cities_html:
        name = city_html.text
        city = {
            'name': name,
            'url': city_html['href'],
            'status': 'defunct',  # Assume a city is defunct until proven otherwise
            'event_ids': [],
            'remote_event_ids': [],
        }
        location = geocode_address(name)
        if location:
            city['coordinates'] = {
                'latitude': location.latitude,
                'longitude': location.longitude,
            }
        else:
            print(f"Could not find location for {name}.")
            text = input("Enter coordinates: ")
            if text:
                latitude, longitude = [float(x) for x in text.split(',')]
                city['coordinates'] = {
                    'latitude': latitude,
                    'longitude': longitude,
                }
            else:
                print("No text entered. Not adding coordinates.")
        cities.append(city)

    return cities


if __name__ == '__main__':
    with open('city-list.html') as f:
        html = f.read()
    cities = parse_cities(html)
    json.dump(cities, open('data/cities.json', 'w+'))