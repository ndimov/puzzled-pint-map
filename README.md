# puzzled-pint-map
Map of Puzzled Pint locations

[Puzzled Pint](https://puzzledpint.com/) is a casual puzzle-solving event hosted in many cities across the world on the second Tuesday of each month. Whenever I find myself in a new city or country, I wonder where I can find a Puzzled Pint event near me. The current site has no easy way to search for this. The list of locations on the homepage helps, but it includes many defunct sites that have been inactive for a while.

Currently, the script fetches the location data from the Puzzled Pint API. It then geocodes the addresses (with caching into a pickle file) and saves a geojson with all these point features. You can map these out with a website like https://geojson.io/.

Verbose comments (and much of the code) are thanks to Copilot.