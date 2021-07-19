import argparse

from functions import get_polygon


parser = argparse.ArgumentParser()
default_geojson = "data/export.geojson" 
parser.add_argument(
    "--geojson",
    help=f"use to change the path of the geojson file with the polygon coordinates from overpass-turbo.eu (default: {default_geojson})",
    type=str,
    default=default_geojson
)
args = parser.parse_args()

polygon = get_polygon(args.geojson)