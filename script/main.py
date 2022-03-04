import argparse
from operator import length_hint
import PIL

from functions import (
    get_polygons,
    get_ign_request,
    start_qgis,
    save_geojson,
    get_tile_coord_from_polygon,
    convert_coord,
    render_image,
    get_image,
    convert_polygon,
    save_polygon,
    make_predictions,
    save_predictions,
    save_image_predictions,
    end_qgis
)

# To allow big tiff image to be opened by PIL
# Warning : can overflow the memory
PIL.Image.MAX_IMAGE_PIXELS = None

parser = argparse.ArgumentParser()

parser.add_argument(
    "--example",
    help=("can be used to make example in docs"),
    action="store_true"
)

parser.add_argument(
    "--high-resolution",
    help=("can be used if 10 centimeters per pixel resolution "
          + "is available."),
    action="store_true"
)

default_input = "data/export.geojson"
parser.add_argument(
    "--input",
    help=(
        "use to change the path of the geojson file with the "
        + "polygons coordinates from overpass-turbo.eu "
        + f"(default: {default_input})"),
    type=str,
    default=default_input
)

default_output_path = "data/"
parser.add_argument(
    "--output-path",
    help=(
        "use to change the path of the folder with the "
        + "output files "
        + f"(default: {default_output_path})"),
    type=str,
    default=default_output_path
)

default_epsg = 4326
parser.add_argument(
    "--epsg",
    help=("use to change the coordinates system of the "
          + "geojson file to EPSG:3857 "
          + f"(default: {default_epsg})"),
    type=int,
    default=default_epsg
)

args = parser.parse_args()

# Set the variables for the docs example
if args.example:
    args.input = "docs/export.geojson"
    args.output_path = "docs/"
    args.epsg = 4326

osm_polygons, epsg = get_polygons(args.input)

if epsg:
    args.epsg = epsg

url_request = get_ign_request()

QGS = start_qgis()

length = len(osm_polygons)

for index in range(length):

    osm_polygon = osm_polygons[index]

    # Increase index to have nicer outpout
    if length == 1:
        index = None
    else:
        index += 1

    # Check if the polygon is valid
    if len(osm_polygon) < 3:
        print("One polygon is not valid : have less than 3 points")
        print("===> Ignored")
        continue

    # If there is multiple polygons, save them separately
    if length > 1:
        save_geojson(osm_polygon, args.output_path, index)

    tile_coords = get_tile_coord_from_polygon(osm_polygon)

    xmin, ymin = convert_coord(
        tile_coords[0],
        tile_coords[1],
        args.epsg,
        3857
    )
    xmax, ymax = convert_coord(
        tile_coords[2],
        tile_coords[3],
        args.epsg,
        3857
    )

    render_image(
        url_request,
        xmin,
        ymin,
        xmax,
        ymax,
        args.output_path,
        args.high_resolution,
        index)

    image = get_image(args.output_path, index)

    image_polygon = convert_polygon(
        osm_polygon,
        image,
        xmin,
        ymin,
        xmax,
        ymax,
        args.epsg
    )

    save_polygon(image_polygon, args.output_path, index)

    if length > 1:
        print(f'Zone ' + str(index) + ' sur ' + str(length) + ' :')

    predictions = make_predictions(image, args.high_resolution)

    save_predictions(predictions, args.output_path, index)

    save_image_predictions(
        args.output_path,
        image,
        predictions,
        image_polygon,
        index)

end_qgis(QGS)
