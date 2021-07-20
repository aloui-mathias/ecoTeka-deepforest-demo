import argparse

from functions import (
    get_polygon,
    get_tile_coord_from_polygon,
    convert_coord,
    get_ign_request,
    render_image,
    get_image
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
default_tiff = "data/image.tiff"
parser.add_argument(
    "--tiff",
    help=(
        "use to change the path of the generated tiff file "
        + ""
        + f"(default: {default_tiff})"),
    type=str,
    default=default_tiff
)
args = parser.parse_args()

polygon = get_polygon(args.geojson)

osm_coords = get_tile_coord_from_polygon(polygon)

xmin, ymin = convert_coord(osm_coords[0], osm_coords[1], 4326, 3857)
xmax, ymax = convert_coord(osm_coords[2], osm_coords[3], 4326, 3857)

url_request = get_ign_request()

render_image(
    url_request,
    xmin,
    ymin,
    xmax,
    ymax,
    args.tiff)

image = get_image(args.tiff)