from flask import Flask, request, Response, jsonify, send_file


from shapely.geometry import box

from pathlib import Path
from typing import Optional, Iterable
from pystac import Catalog, Collection, Item

from pystac_client import Client, Modifiable

def filter_stac_catalog(catalog: Catalog,
                        bbox: Optional[tuple[float, float, float, float]] = None,
                        ) -> tuple[list[Collection], Iterable[Item]]:
    filtered_collections = filter_collections(catalog, bbox)
    filtered_items = filter_items(filtered_collections, bbox)
    return filtered_collections, filtered_items

def filter_collections(catalog: Catalog,
                       bbox: Optional[tuple[float, float, float, float]] = None
                       ) -> list[Collection]:
    if bbox is None:
        return [collection for collection in catalog.get_children()
                if isinstance(collection, Collection)]
    else:
        return [collection for collection in catalog.get_children() if
                isinstance(collection, Collection) and
                collection.extent.spatial.bboxes is not None and
                any(_bbox_intersection(list(bbox), b) is not None
                    for b in collection.extent.spatial.bboxes)]


def _bbox_intersection(bbox1: list[float, float, float, float],
                       bbox2: list[float, float, float, float]
                       ) -> Optional[list[float, float, float, float]]:
    box1 = box(*bbox1)
    box2 = box(*bbox2)
    intersection = box1.intersection(box2)
    if intersection.is_empty:
        return None
    else:
        return list(intersection.bounds)


def filter_items(collections: list[Collection],
                bbox: Optional[tuple[float, float, float, float]] = None
                 ) -> list[Item]:
    items = []
    for collection in collections:
        for item in collection.get_items():
            if _bbox_intersection(list(bbox), item.bbox) is not None:
                items.append(item)
    return items


app = Flask(__name__)

@app.route('/free-samples', methods=['GET'])
def getItems():
    bboxParam = request.args.get('bbox')  # Get value of 'param1' parameter

    bBox = [float(num) for num in bboxParam.split(',')]
    catalog = Client.open('http://localhost:8089/catalog.json')

    result = filter_stac_catalog(catalog=catalog, bbox=bBox)
    items = result[1]
    items_dict = [item.to_dict() for item in items]
    return jsonify(items_dict)

@app.route('/free-samples/<path:item_id>', methods=['GET'])
def getByItemId(item_id):

    catalog = Client.open('http://localhost:8089/catalog.json')
    collections = [collection for collection in catalog.get_children()
                if isinstance(collection, Collection)]
    for collection in collections:
        for item in collection.get_items():
            if item.id == item_id :
                return item.to_dict()

    return 


if __name__ == '__main__':
    app.run(host='localhost', port=8082, debug=False)