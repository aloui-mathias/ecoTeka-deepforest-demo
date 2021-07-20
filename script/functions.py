import json
import pyproj
import numpy
from urllib.parse import unquote, urlencode
from owslib.wmts import WebMapTileService
from PIL import Image
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsRectangle,
    QgsRasterLayer,
    QgsMapSettings,
    QgsMapRendererParallelJob
)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize, QEventLoop
from typing import List, Tuple


def get_polygon(geojson_path: str) -> List:
    try:
        file = open(geojson_path, 'r')
        file.seek(0)
        geojson = json.loads(file.read())
    except:
        print(
            "Using the default path, please check you are running "
            + "the script from ecoTeka-deepforest-demo folder."
        )
        raise
    finally:
        file.close()
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


def get_ign_request() -> str:

    WMTS_URL_GETCAP = "https://wxs.ign.fr/pratique/geoportail/wmts?"\
        "SERVICE%3DWMTS%26REQUEST%3DGetCapabilities"
    WMTS = WebMapTileService(WMTS_URL_GETCAP)
    LAYER_NAME = "ORTHOIMAGERY.ORTHOPHOTOS"
    WMTS_LAYER = WMTS[LAYER_NAME]
    LAYER_TITLE = WMTS_LAYER.title
    WMTS_URL_PARAMS = {
        "SERVICE": "WMTS",
        "VERSION": "1.0.0",
        "REQUEST": "GetCapabilities",
        "layers": LAYER_NAME,
        "crs": "EPSG:3857",
        "format": "image/jpeg",
        "styles": "normal",
        "tileMatrixSet": "PM",
        "tileMatrix": "21",
        "url": WMTS_URL_GETCAP
    }
    WMTS_URL_FINAL = unquote(urlencode(WMTS_URL_PARAMS))

    return WMTS_URL_FINAL


def render_image(
        request: str,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        path: str) -> None:

    QGS = QgsApplication([], False)
    QGS.initQgis()
    WMTS_LAYER = QgsRasterLayer(
        request, "raster-layer", "wms")
    if WMTS_LAYER.isValid():
        QgsProject.instance().addMapLayer(WMTS_LAYER)
    else:
        return WMTS_LAYER.error().message()
    extent = QgsRectangle(xmin, ymin, xmax, ymax)
    WMTS_LAYER.setExtent(extent)
    settings = QgsMapSettings()
    settings.setLayers([WMTS_LAYER])
    settings.setBackgroundColor(QColor(255, 255, 255))
    settings.setOutputSize(QSize(
        int(extent.width() / 0.25),
        int(extent.height() / 0.25)
    ))
    settings.setExtent(WMTS_LAYER.extent())

    render = QgsMapRendererParallelJob(settings)

    def finished():
        img = render.renderedImage()
        img.save(path, "png")

    render.finished.connect(finished)

    render.start()

    loop = QEventLoop()
    render.finished.connect(loop.quit)
    loop.exec_()

    QGS.exitQgis()

def get_image(path: str) -> numpy.ndarray:
    image = Image.open(path, 'r')
    numpy_rgba = numpy.array(image).astype('float32')
    return numpy_rgba[:, :, :3]
