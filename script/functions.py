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

