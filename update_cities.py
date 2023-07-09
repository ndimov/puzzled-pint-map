# This file is intended to be run to update cities.json for schema changes without overwriting manual changes

import json

cities = json.load(open('data/cities.json'))
for city in cities:
    city["event_ids"] = []
    city["remote_event_ids"] = []

json.dump(cities, open('data/cities.json', 'w+'))