import argparse

from functions import (
    get_polygons,
    save_polygon,
    get_tile_coord_from_polygon,
    convert_coord,
    get_ign_request,
    render_image,
    get_image,
    convert_polygon,
    predictions,
    save_image_predictions,
    start_qgis,
    end_qgis
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
default_tiff = "data/image"
parser.add_argument(
    "--tiff",
    help=(
        "use to change the path of the generated tiff file "
        + "from the IGN without .tiff"
        + f"(default: {default_tiff})"),
    type=str,
    default=default_tiff
)
default_png = "data/prediction"
parser.add_argument(
    "--png",
    help=(
        "use to change the path of the generated png file "
        + "with the detected trees and the polygon without .png "
        + f"(default: {default_png})"),
    type=str,
    default=default_png
)
args = parser.parse_args()

osm_polygons = get_polygons(args.geojson)

url_request = get_ign_request()

QGS = start_qgis()

length = len(osm_polygons)

for index in range(length):

    if length == 1:
        tiff_path = args.tiff
        png_path = args.png
    else:
        tiff_path = args.tiff + str(index)
        png_path = args.png + str(index)

    osm_polygon = osm_polygons[index]

    if len(osm_polygon) < 3:
        continue

    osm_coords = get_tile_coord_from_polygon(osm_polygon)

    xmin, ymin = convert_coord(
        osm_coords[0],
        osm_coords[1],
        4326,
        3857
    )
    xmax, ymax = convert_coord(
        osm_coords[2],
        osm_coords[3],
        4326,
        3857
    )

    render_image(
        url_request,
        xmin,
        ymin,
        xmax,
        ymax,
        tiff_path,
        args.high_resolution)

    image = get_image(tiff_path)

    image_polygon = convert_polygon(
        osm_polygon,
        image,
        xmin,
        ymin,
        xmax,
        ymax
    )

    save_polygon(image_polygon, tiff_path)

    print(f'Zone ' + str(index + 1) + ' sur ' + str(length) + ' :')

    image_predictions = predictions(image, args.high_resolution)

    save_image_predictions(
        png_path,
        image,
        image_predictions,
        image_polygon)

end_qgis(QGS)
