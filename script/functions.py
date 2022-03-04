import json
import pyproj
import numpy
import pandas
import cv2
from urllib.parse import unquote, urlencode
from owslib.wmts import WebMapTileService
from PIL import Image
from matplotlib import pyplot
from shapely import geometry
from deepforest import main
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
from typing import Dict, List, Optional, Tuple
import tifffile


def get_polygons(input: str) -> Tuple[List[List[List[float]]], int]:
    try:
        file = open(input, 'r', encoding="utf-8")
        file.seek(0)
        geojson = json.loads(file.read())
    except:
        print(".geojson not found.")
        print()
        print(
            "Using the default path, please check you are running "
            + "the script from ecoTeka-deepforest-demo folder."
        )
        raise
    file.close()

    polygons = []
    for feature in geojson['features']:
        if feature['geometry']['type'] == "Polygon":
            polygons.append(feature['geometry']['coordinates'][0])

    epsg = None
    crs = geojson.get("crs", None)
    if crs:
        prop = crs.get("properties", None)
        if prop:
            epsg_data = prop.get("name", None)
            if epsg_data:
                epsg = epsg_data.split(":")[-1]

    return [polygons, epsg]


def get_ign_request() -> str:

    WMTS_URL_GETCAP = "https://wxs.ign.fr/decouverte/geoportail/wmts?"\
        "SERVICE%3DWMTS%26REQUEST%3DGetCapabilities"
    WMTS = WebMapTileService(WMTS_URL_GETCAP, timeout=10)
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


def start_qgis():
    QGS = QgsApplication([], False)
    QGS.initQgis()
    return QGS


def save_geojson(
        osm_polygon: List[List[float]],
        output_path: str,
        index: Optional[int] = None) -> None:
    output = {
        "type": "FeatureCollection",
        "name": f"polygon{index+1}",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::3857"
            }
        },
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": index+1
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": []
                }
            }
        ]
    }

    for point in osm_polygon:
        output["features"][0]["geometry"]["coordinates"].append(
            point
        )

    filepath = output_path + f"polygon{index or ''}.geojson"
    with open(filepath, "w") as file:
        json.dump(output, file, indent=4)


def get_tile_coord_from_polygon(polygon: List) -> Tuple[float]:
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


def convert_coord(
        x: float,
        y: float,
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


def render_image(
        request: str,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        output_path: str,
        high_resolution: bool,
        index: Optional[int] = None) -> None:

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
    if high_resolution:
        res = 0.2
    else:
        res = 0.25
    settings.setOutputSize(QSize(
        int(extent.width() / res),
        int(extent.height() / res)
    ))
    settings.setExtent(WMTS_LAYER.extent())

    render = QgsMapRendererParallelJob(settings)

    def finished():
        img = render.renderedImage()
        img.save(output_path + f"image{index or ''}.tiff", "png")

    render.finished.connect(finished)

    render.start()

    loop = QEventLoop()
    render.finished.connect(loop.quit)
    loop.exec_()

    del render

    return


def get_image(
        output_path: str,
        index: Optional[int] = None) -> numpy.ndarray:
    image_path = output_path + f"image{index or ''}.tiff"
    image = Image.open(image_path, 'r')
    numpy_rgba = numpy.array(image).astype('float32')
    numpy_rgb = numpy_rgba[:, :, :3]
    return numpy_rgb


def convert_polygon(
        polygon: List[List[float]],
        image: numpy.ndarray,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        epsg: int) -> List:

    polygon_image = []
    width_ign = image.shape[1]
    height_ign = image.shape[0]

    for index in range(len(polygon)):
        coord = polygon[index]
        coord_ign = convert_coord(coord[0], coord[1], epsg, 3857)
        point = ((coord_ign[0] - xmin)*(width_ign/(xmax-xmin)),
                 (ymax - coord_ign[1])*(height_ign/(ymax-ymin)))
        polygon_image.append(point)

    return numpy.array(polygon_image).astype('int32')


def save_polygon(
        polygon: numpy.array,
        output_path: str,
        index: Optional[int] = None) -> None:
    output = {}
    points = []
    for coords in polygon:
        point = {}
        point["x"] = str(coords[0])
        point["y"] = str(coords[1])
        points.append(point)
    output["points"] = points
    filepath = output_path + f"polygon{index or ''}.json"
    with open(filepath, "w") as file:
        json.dump(output, file, indent=4)


def make_predictions(
        image: numpy.ndarray,
        high_resolution: bool) -> pandas.DataFrame:

    model = main.deepforest()
    model.use_release()

    if high_resolution:
        patch_size = 800
    else:
        patch_size = 500

    return model.predict_tile(
        raster_path=None,
        image=image,
        patch_size=patch_size,
        patch_overlap=0.15,
        iou_threshold=0.15,
        return_plot=False,
        use_soft_nms=False,
        sigma=0.5,
        thresh=0.001)


def save_predictions(
        predictions: pandas.DataFrame,
        output_path: str,
        index: Optional[int] = None) -> None:
    predictions.to_csv(
        output_path + f"predictions{index or ''}.csv",
        index=False
    )


def draw_box(
        image: numpy.ndarray,
        box: List,
        color: List,
        thickness: float = 2) -> None:

    b = numpy.array(box).astype(int)
    cv2.rectangle(
        img=image,
        pt1=(b[0], b[1]),
        pt2=(b[2], b[3]),
        color=color,
        thickness=thickness,
        lineType=cv2.LINE_AA
    )

    return


def draw_all_boxes(
        image: numpy.ndarray,
        boxes: pandas.DataFrame,
        color: List = [0, 0, 255]) -> None:

    for box in boxes[["xmin", "ymin", "xmax", "ymax"]].values:
        draw_box(image, box, color)

    return


def save_image_predictions(
        output_path: str,
        image: numpy.ndarray,
        predictions: pandas.DataFrame,
        polygon: Optional[List[List[float]]] = None,
        index: Optional[int] = None) -> None:

    image_copy = image.copy().astype('uint8')

    if polygon is None:
        boxes = predictions
    else:
        zone = geometry.Polygon(polygon)
        boxes = []
        if predictions is not None:
            for predicted_box in predictions.values:
                coord = predicted_box[:4]
                box_points = [
                    [coord[0], coord[1]],
                    [coord[0], coord[3]],
                    [coord[2], coord[3]],
                    [coord[2], coord[1]]
                ]
                box = geometry.Polygon(box_points)
                intersection_area = box.intersection(zone).area
                box_area = box.area
                ioa = intersection_area / box_area
                if ioa > 0.4:
                    boxes.append(predicted_box)

            boxes = pandas.DataFrame(
                boxes,
                columns=predictions.columns
            )

        cv2.polylines(
            image_copy,
            [polygon],
            True,
            [255, 0, 0],
            thickness=10
        )

    if boxes is not None:
        draw_all_boxes(image_copy, boxes)
    print(str(len(boxes)) + " predictions inside")

    tifffile.imwrite(
        output_path + f"image-predictions{index or ''}.tiff",
        image_copy
    )
    pyplot.imsave(
        output_path + f"image-predictions{index or ''}.png",
        image_copy
    )

    return


def end_qgis(QGS):
    QGS.exitQgis()
