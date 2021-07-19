import json
import pyproj
from typing import List, Tuple


def get_polygon(geojson_path: str) -> List:
    try:
        geojson = json.loads(open(geojson_path, 'r').read())
    except:
        return (
            f"No such file or directory: {geojson_path}\nIf your "
            + "using the default path, please check you are running "
            + "the script from ecoTeka-deepforest-demo folder."
        )
    return geojson['features'][0]['geometry']['coordinates'][0]


def get_tile_coord_from_polygon(polygon):
    xmin = polygon[0][0]
    xmax = polygon[0][0]
    ymin = polygon[0][1]
    ymax = polygon[0][1]
    for point in polygon:
        xmin = point[0] if point[0] < xmin else xmin
        xmax = point[0] if point[0] > xmax else xmax
        ymin = point[1] if point[1] < ymin else ymin
        ymax = point[1] if point[1] > ymax else ymax
    return xmin, ymin, xmax, ymax


def convert_coord(x: float, y: float,
                  input_epsg: int,
                  output_epsg: int) -> Tuple[float]:

    input_crs = pyproj.CRS.from_epsg(input_epsg)
    output_crs = pyproj.CRS.from_epsg(output_epsg)

    proj = pyproj.Transformer.from_crs(input_crs, output_crs)

    if input_crs.is_geographic and not output_crs.is_geographic:
        coord = proj.transform(y, x)
    else:
        coord = proj.transform(x, y)

    if output_crs.is_geographic and not input_crs.is_geographic:
        return coord[1], coord[0]
    else:
        return coord[0], coord[1]
