import os
from pathlib import Path
from typing import Optional
import numpy as np
from osgeo import gdal
import rvt.vis

from .dtm import dtm


def sky_view_factor(input_file: str, region_name: Optional[str] = None,
                    svf_n_dir: int = 16, svf_r_max: int = 10, svf_noise: int = 0) -> str:
    """Generate Sky View Factor raster from a LAZ file.

    The LAZ file is first converted to a DTM using the existing ``dtm``
    processing function. The sky view factor is then computed using the
    ``rvt.vis`` module and written to ``GTiff`` format.

    Parameters
    ----------
    input_file: str
        Path to the LAZ file.
    region_name: Optional[str]
        Optional region name for output folder naming. If ``None`` the
        region name is inferred from ``input_file``.
    svf_n_dir: int
        Number of directions used for the SVF calculation.
    svf_r_max: int
        Maximum search radius in pixels.
    svf_noise: int
        Noise removal level (0 = none).

    Returns
    -------
    str
        Path to the generated sky view factor GeoTIFF file.
    """
    # Generate a DTM first
    dtm_path = dtm(input_file, region_name)

    ds = gdal.Open(dtm_path)
    if ds is None:
        raise RuntimeError(f"Failed to open DTM file: {dtm_path}")

    dem = ds.GetRasterBand(1).ReadAsArray()
    res_x = ds.GetGeoTransform()[1]
    no_data = ds.GetRasterBand(1).GetNoDataValue()

    # Compute SVF using rvt
    svf = rvt.vis.sky_view_factor(
        dem=dem,
        resolution=res_x,
        compute_svf=True,
        compute_asvf=False,
        compute_opns=False,
        svf_n_dir=svf_n_dir,
        svf_r_max=svf_r_max,
        svf_noise=svf_noise,
        no_data=no_data,
    )["svf"]

    # Prepare output path
    input_path = Path(input_file)
    region = region_name if region_name else (
        input_path.parts[input_path.parts.index("input") + 1]
        if "lidar" in input_path.parts else input_path.stem
    )

    output_dir = Path("output") / region / "lidar" / "SkyViewFactor"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{region}_Sky_View_Factor.tif"

    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(
        str(output_path), ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Float32
    )
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    out_ds.SetProjection(ds.GetProjection())
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(svf.astype(np.float32))
    out_band.SetNoDataValue(no_data if no_data is not None else -9999)
    out_band.FlushCache()
    out_ds.FlushCache()

    return str(output_path)
