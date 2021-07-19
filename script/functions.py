import json
from typing import List


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
