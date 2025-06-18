# Step 4: Recommend Raster Output Parameters and PNG Color Scales

Creating effective visualizations is as crucial as processing the data correctly. This step details recommended output parameters for raster files, with a special focus on PNGs and their color scales for anomaly visualization.

## 1. General Raster Output Parameters

These parameters apply to DTMs, their derivatives, and composite rasters when saving them for analysis, archiving, or visualization.

*   **File Format:**
    *   **GeoTIFF (.tif, .tiff):**
        *   **Advantages:** The industry standard for storing and exchanging georeferenced raster data.
            *   **Georeferencing:** Stores coordinate system, projection, and extent information directly within the file.
            *   **Multi-band Support:** Can store multiple layers (e.g., RGB composites, or DTM with its derivatives).
            *   **Various Bit Depths:** Supports 8-bit, 16-bit, 32-bit integer, and 32-bit/64-bit floating-point data, allowing for full precision or optimized file sizes.
            *   **Lossless Compression:** Options like LZW or DEFLATE can significantly reduce file size without data loss. Tiled GeoTIFFs with compression are often efficient.
        *   **Use For:** Primary data storage, analytical processing, input for most GIS operations.
    *   **PNG (.png):** Portable Network Graphics.
        *   **Advantages:**
            *   **Lossless Compression:** Uses DEFLATE compression, ensuring no data is lost, which is good for preserving sharp details in features.
            *   **Good for Sharp Features:** Renders crisp lines and edges, suitable for visualizing earthworks.
            *   **Alpha Channel:** Supports transparency, useful for overlays in reports or web maps.
            *   Widely supported by web browsers and image viewing software.
        *   **Disadvantages:**
            *   **Bit Depth:** Typically 8-bit per channel (e.g., grayscale, or R,G,B each 8-bit). While 16-bit PNGs exist, support is less universal. This means data often needs to be scaled.
            *   **Metadata:** Limited support for extensive geospatial metadata compared to GeoTIFF. A "world file" (.pgw) can accompany a PNG to provide basic georeferencing, but projection details might be lost.
        *   **Use For:** Final visualization products for reports, presentations, web display, quick visual checks, sharing non-analytical imagery.

*   **Bit Depth:**
    *   **32-bit Float:**
        *   **Ideal for:** Original DTMs and analytical derivatives (slope, SVF, LRM, etc.) during processing and intermediate stages.
        *   **Reason:** Preserves the full precision of calculations and the original range of elevation values (which can be negative or require decimal places).
    *   **16-bit Integer (Signed or Unsigned):**
        *   **Ideal for:** Intermediate storage if disk space is a concern, or for some analytical tasks if data is appropriately scaled (e.g., elevation in cm). Can significantly reduce file size compared to 32-bit float (halves it).
        *   **Reason:** Offers a good balance between data precision and file size. Elevation values might be multiplied by a factor (e.g., 100 to store cm) to retain some decimal precision before converting to integer.
    *   **8-bit Integer (Unsigned):**
        *   **Ideal for:** Final visualization products, especially PNGs or GeoTIFFs intended purely for display.
        *   **Reason:** Represents values from 0 to 255. Requires careful scaling/stretching of the original higher bit-depth data to fit this limited range. This is standard for most image formats.

*   **Compression:**
    *   **For GeoTIFF:**
        *   **LZW (Lempel-Ziv-Welch):** A good general-purpose lossless compression algorithm. Widely supported.
        *   **DEFLATE (Zip):** Often provides better compression ratios than LZW, also lossless.
        *   **Predictor:** Using a predictor (e.g., horizontal differencing) with LZW or DEFLATE can further improve compression for DTM data.
    *   **For PNG:**
        *   Uses **DEFLATE** compression inherently and losslessly. The compression level can sometimes be adjusted in software, but it's always lossless.

*   **Resolution:**
    *   The output resolution (pixel size) should generally be consistent with the source DTM and the scale of the derivatives.
    *   It should be chosen to adequately resolve the smallest archaeological features of interest, as discussed in DTM generation best practices (e.g., 0.25m to 1m for Amazonian archaeology).
    *   Avoid unnecessary upsampling (which creates larger files without adding real detail) or excessive downsampling (which can obscure features).

## 2. PNG Specifics for Anomaly Visualization

PNGs are excellent for sharing visual results. However, converting floating-point or 16-bit data to the typical 8-bit PNG format requires careful data scaling.

*   **When to use PNG:**
    *   Creating images for reports, publications, or presentations.
    *   Sharing visualizations with colleagues who may not have GIS software.
    *   Quick visual checks of processing results.
    *   Web mapping applications where GeoTIFF might be too slow or unsupported directly by browsers.

*   **Scaling Data to 8-bit (0-255 range):**
    This process, often called "contrast stretching" or "dynamic range adjustment," maps the original data values to the 0-255 range available in an 8-bit PNG.
    *   **Linear Stretch (Min-Max):** The minimum value in the original data is mapped to 0, and the maximum value to 255. All other values are scaled linearly in between. This is simple and preserves relative differences but can be heavily influenced by extreme outliers.
    *   **Standard Deviation Stretch:** Data is stretched based on a chosen number of standard deviations from the mean. For example, values within +/- 2 standard deviations of the mean are stretched to 0-255. This can enhance contrast in the most frequent data values, pushing outliers to 0 or 255.
    *   **Histogram Equalize Stretch:** This method redistributes pixel values so that the output image has a nearly flat histogram. It's effective at enhancing contrast in areas with subtle variations and revealing texture but can significantly alter the visual relationship between values and may not be suitable if absolute magnitudes are important to convey.
    *   **Percentage Clip (Min/Max Cut):** Similar to a linear stretch, but a certain percentage of the lowest and highest values in the original data are saturated to 0 and 255, respectively, before the linear stretch is applied to the remaining values. This is useful for handling outliers and improving contrast in the bulk of the data. A common clip is 2% (1% at each tail).
    *   **Importance of Context:** The "best" stretching method depends heavily on the specific characteristics of the raster data (its histogram) and the features one wishes to highlight. Experimentation is often necessary. For subtle anomaly detection, methods that maximize local contrast without losing too much overall context are preferred.

## 3. Color Scale (Colormap/LUT) Strategies for PNGs

The choice of color scale (also known as a colormap or Look-Up Table - LUT) dramatically impacts how features are perceived in a PNG image.

*   **General Principles:**
    *   **Contrast:** The colormap should provide sufficient contrast to make subtle features stand out from their background.
    *   **Perceptual Uniformity:** Ideally, use colormaps where a given step in data value corresponds to a proportional step in perceived brightness and/or color. This prevents the colormap itself from creating artificial visual boundaries or obscuring real ones. Examples include Viridis, Cividis, Plasma, Magma, and Inferno from Matplotlib or ColorBrewer sequential/diverging schemes.
    *   **Accessibility:** Be mindful of colorblind viewers. Many perceptually uniform colormaps (like Viridis, Cividis) are also designed to be colorblind-friendly. Avoid red-green combinations where possible if not specifically designed for accessibility.

*   **For Single-Band Rasters (DTM, Slope, SVF, LRM, etc., saved as Grayscale or Colorized PNGs):**
    *   **DTM (Elevation):**
        *   **Standard Hypsometric Tints:** Traditional color schemes (e.g., blues for water/lowlands, progressing through greens, yellows, browns, to whites for high peaks). Useful for general topographic context.
        *   **Custom Hypsometric Tints:** More effective for archaeology. Tailor the color breaks and hues to the specific elevation range of the study area. Use distinct, contrasting colors to highlight very subtle elevation changes that might correspond to earthworks.
        *   **Grayscale:** A simple grayscale ramp (black to white or vice-versa) can be very effective, especially for experienced interpreters who are used to associating brightness with elevation.
        *   **Perceptually Uniform Sequential Colormaps:** (e.g., `viridis`, `cividis`, `plasma`, `magma`, `inferno`). These are often excellent choices as they are designed to represent data magnitude faithfully. `Cividis` is specifically designed to be perceivable by people with all forms of color vision deficiency.
    *   **Hillshade:** Almost universally displayed using a **grayscale** ramp (black for shadows, white for illuminated areas).
    *   **Slope, SVF, LRM, other derivatives:**
        *   **Sequential Colormaps:**
            *   **Grayscale:** Very common and effective for showing magnitude (e.g., low slope to high slope, low SVF to high SVF).
            *   **Perceptually Uniform Single-Hue or Multi-Hue Sequential:** (e.g., `viridis`, `magma`, ColorBrewer `Blues`, `Reds`, `Greens`). These are excellent for representing the intensity or magnitude of the derivative.
        *   **Diverging Colormaps:**
            *   (e.g., ColorBrewer `RdBu` (Red-White-Blue), `BrBG` (Brown-White-Teal/Green)).
            *   Useful if the data has a meaningful midpoint or zero value. For example, Topographic Position Index (TPI) values are negative for valleys, positive for ridges, and near zero for flat/slope areas. SVF can also be centered if looking at deviations from an average.
        *   **"Archaeological" or Custom Palettes:** Some remote sensing specialists and archaeological geophysicists develop or prefer specific high-contrast, sometimes non-standard, color palettes they find particularly effective for highlighting subtle earthworks or soil marks. These often involve specific shades of browns, oranges, yellows, and grays. Examples include the "LIDAR Palette for R" or custom palettes shared within the QGIS community. Experimentation is key to finding what works best for a specific dataset and feature type.

*   **For Composite Rasters (e.g., DTM + Hillshade Blend shown as PNG):**
    *   The primary color information typically comes from the base DTM layer (or another colorized derivative). Therefore, the color scale choices described for DTMs (hypsometric tints, perceptual colormaps) apply to this base layer. The hillshade (usually grayscale) is then blended transparently on top, providing texture and relief without altering the underlying colors significantly (though it will darken them in shadowed areas).

*   **For RGB Composites (saved as PNG):**
    *   The "color scale" is implicitly defined by how the three input raster bands (each typically normalized to 0-255) are combined into the Red, Green, and Blue channels of the PNG.
    *   The key here is not choosing a single colormap post-composition, but rather the careful selection, normalization, and stretching of *each individual input band* before it is assigned to an R, G, or B channel. The perceived colors in the final PNG are a direct result of the intensity mix of these three channels.

## 4. Tools for Applying Color Scales and Exporting PNGs

*   **GIS Software (QGIS, ArcGIS Pro, SAGA GIS, GRASS GIS):**
    *   Offer extensive graphical user interfaces for raster symbolization, including numerous pre-defined color ramps, tools to create custom ramps, control over color breaks (classification), and methods for contrast stretching.
    *   They provide direct export options to PNG, often with control over resolution and georeferencing (via world files).
*   **Command-line tools (GDAL - Geospatial Data Abstraction Library):**
    *   `gdaldem color-relief`: A powerful utility to apply a color configuration file (mapping values to R,G,B triplets) to a DEM or other single-band raster to produce a colorized GeoTIFF or other formats. This can then be converted to PNG using `gdal_translate`.
    *   `gdal_translate`: Can be used to convert between raster formats, scale data (e.g., with `-scale` option), and change bit depth.
*   **Programming Libraries:**
    *   **Python:**
        *   **Matplotlib (with `pyplot`):** Offers a vast array of colormaps (including perceptually uniform ones like Viridis), extensive control over plot appearance, and can save figures directly to PNG.
        *   **Rasterio (or GDAL Python bindings):** For reading raster data. Data can then be manipulated with NumPy and visualized with Matplotlib or other plotting libraries.
        *   **EarthPy:** Has utilities for plotting rasters and histograms, often simplifying Matplotlib usage for earth science data.
    *   **R:** Packages like `raster`, `terra`, `ggplot2`, and `tmap` provide rich functionalities for raster manipulation, visualization, and applying color scales, with options to export to PNG.

By considering these output parameters and color scale strategies, archaeologists can produce clear, informative, and impactful visualizations that effectively communicate the presence of potential archaeological anomalies.
