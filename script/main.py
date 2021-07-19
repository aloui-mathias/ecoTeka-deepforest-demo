import argparse

from functions import (
    get_polygon,
    get_tile_coord_from_polygon,
    convert_coord
)


parser = argparse.ArgumentParser()
default_geojson = "data/export.geojson"
parser.add_argument(
    "--geojson",
    help=(
        "use to change the path of the geojson file with the "
        + "polygon coordinates from overpass-turbo.eu "
        + f"(default: {default_geojson})"),
    type=str,
    default=default_geojson
)
args = parser.parse_args()

polygon = get_polygon(args.geojson)

osm_coords = get_tile_coord_from_polygon(polygon)

xmin, ymin = convert_coord(osm_coords[0], osm_coords[1], 4326, 3857)
xmax, ymax = convert_coord(osm_coords[2], osm_coords[3], 4326, 3857)
