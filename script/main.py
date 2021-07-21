import argparse

from functions import (
    get_polygon,
    get_tile_coord_from_polygon,
    convert_coord,
    get_ign_request,
    render_image,
    get_image,
    convert_polygon,
    predictions,
    save_image_predictions
)


parser = argparse.ArgumentParser()
default_geojson = "data/export.geojson"
parser.add_argument(
    "--high-resolution",
    help="can be used if 10 centimeters per pixel resolution "
    + "is available.",
    action="store_true"
)
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
        + "from the IGN "
        + f"(default: {default_tiff})"),
    type=str,
    default=default_tiff
)
default_png = "data/prediction.png"
default_tiff = "data/image.tiff"
parser.add_argument(
    "--png",
    help=(
        "use to change the path of the generated png file "
        + "with the detected trees and the polygon "
        + f"(default: {default_png})"),
    type=str,
    default=default_png
)
args = parser.parse_args()

osm_polygon = get_polygon(args.geojson)

osm_coords = get_tile_coord_from_polygon(osm_polygon)

xmin, ymin = convert_coord(osm_coords[0], osm_coords[1], 4326, 3857)
xmax, ymax = convert_coord(osm_coords[2], osm_coords[3], 4326, 3857)

url_request = get_ign_request()

render_image(
    url_request,
    xmin,
    ymin,
    xmax,
    ymax,
    args.tiff,
    args.high_resolution)

image = get_image(args.tiff)

image_polygon = convert_polygon(
    osm_polygon,
    image,
    xmin,
    ymin,
    xmax,
    ymax
)

image_predictions = predictions(image, args.high_resolution)

save_image_predictions(
    args.png,
    image,
    image_predictions,
    image_polygon)
