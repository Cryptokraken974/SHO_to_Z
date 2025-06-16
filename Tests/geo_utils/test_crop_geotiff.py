import os
import pytest
gdal = pytest.importorskip('osgeo.gdal')
osr = pytest.importorskip('osgeo.osr')
from app.geo_utils import get_image_bounds_from_geotiff, crop_geotiff_to_bbox, intersect_bounding_boxes
from app.data_acquisition.utils.coordinates import BoundingBox


def create_test_tiff(path):
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(path, 10, 10, 1, gdal.GDT_Byte)
    geotransform = (0, 1, 0, 10, 0, -1)
    ds.SetGeoTransform(geotransform)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    ds.SetProjection(srs.ExportToWkt())
    data = bytes(range(100))
    ds.GetRasterBand(1).WriteRaster(0, 0, 10, 10, data, buf_xsize=10, buf_ysize=10, buf_type=gdal.GDT_Byte)
    ds = None


def test_crop_geotiff(tmp_path):
    src = tmp_path / "src.tif"
    create_test_tiff(str(src))

    bbox_full = BoundingBox(north=10, south=0, east=10, west=0)
    bbox_crop = BoundingBox(north=8, south=2, east=8, west=2)
    dst = tmp_path / "crop.tif"
    assert crop_geotiff_to_bbox(str(src), str(dst), bbox_crop)

    info = get_image_bounds_from_geotiff(str(dst))
    assert info
    cropped = BoundingBox(north=info['north'], south=info['south'], east=info['east'], west=info['west'])
    inter = intersect_bounding_boxes(bbox_full, bbox_crop)
    assert inter == cropped
    ds = gdal.Open(str(dst))
    assert ds.RasterXSize == 6 and ds.RasterYSize == 6
    ds = None
