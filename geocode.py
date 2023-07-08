import os
from geopy.geocoders import GoogleV3
from dotenv import load_dotenv

load_dotenv()

# locator = Nominatim(user_agent="puzzled-pint-map")
locator = GoogleV3(api_key=os.environ["GOOGLE_API_KEY"])

def geocode_address(address):
    print(f"Geocoding address via API: {address}")
    location = locator.geocode(address)
    return location