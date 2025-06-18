# Step 3: Explain Composite Raster Techniques

## 1. Introduction to Composite Rasters

While individual DTM derivatives like hillshade, slope, or Sky-View Factor (SVF) are powerful tools for enhancing topographic features, combining multiple raster datasets into a single composite image can further improve interpretability and the likelihood of detecting subtle archaeological anomalies.

*   **Why combine rasters?**
    *   **Leveraging Strengths:** Different derivatives highlight different aspects of the terrain. For instance, hillshade provides an intuitive 3D perspective, while SVF excels at revealing subtle depressions. A composite can synergize these strengths.
    *   **Enhancing Interpretability:** A well-designed composite can present complex spatial information in a more digestible and visually compelling manner than viewing multiple separate images.
    *   **Contextual Information:** Combining a derivative (e.g., hillshade) with the original DTM (colored by elevation) allows the viewer to perceive relief in the context of absolute elevation values.
*   **General Principle:** The fundamental idea is to display multiple layers of geospatial raster data simultaneously in a single map view or image. This is achieved by assigning different rasters (or their properties) to different visual channels (e.g., transparency, color channels).

## 2. Common and Effective Composite Techniques

Several techniques can be used to create effective composite rasters for archaeological prospection.

*   **DTM (Colorized) + Hillshade Blending (Transparent Overlay):**
    *   **Most common and intuitive method.** This is a foundational technique in topographic visualization.
    *   **Layers:**
        *   **Base Layer:** The Digital Terrain Model (DTM) is displayed with a color ramp applied to its elevation values (a hypsometric tint). Common color schemes might range from blues/greens for low elevations to yellows/reds/browns for higher elevations.
        *   **Overlay Layer:** A grayscale hillshade raster (preferably multi-directional, or the user should experiment with different azimuths).
    *   **Parameters:** The key parameter is the **transparency** (or its inverse, opacity) of the hillshade layer. Typically, the hillshade is made partially transparent (e.g., 30-60% transparent, meaning 40-70% opaque).
    *   **How it works:** The semi-transparent hillshade is draped over the colored DTM. This allows the 3D relief perception offered by the hillshade's shadows and highlights to be combined with the quantitative elevation information conveyed by the DTM's color. The result is an intuitive and information-rich visualization.
    *   **Variations:**
        *   Using a **multi-directional hillshade** as the overlay layer can provide more consistent feature illumination.
        *   Layering additional semi-transparent derivatives, like slope, can also be done, but can make the image overly complex if not managed carefully.

*   **Overtinting / Color Shading:**
    *   **Principle:** This is conceptually similar to the DTM + Hillshade blend but can imply more direct modulation of one raster's color values by another, or specific blending modes in GIS software. Instead of just making a grayscale hillshade transparent over a colored DTM, one raster's values directly influence the color characteristics of another.
    *   **Example:**
        *   Tinting a grayscale hillshade directly with colors derived from the DTM's elevation values. For example, the shadowed and illuminated areas of the hillshade would take on hues corresponding to their actual elevation (e.g., low-lying shadowed areas might be dark blue, high-altitude illuminated areas might be light red).
        *   Tinting a hillshade with SVF values, where areas of high enclosure (low SVF) might be shaded with a specific color (e.g., cool blues) and open areas (high SVF) with another (e.g., warm yellows), all while retaining the hillshade's relief effect.
    *   **Software Specific:** GIS and image processing software offer various **blending modes** (e.g., "Multiply," "Overlay," "Screen," "Hard Light," "Soft Light") that can be used to achieve different overtinting effects. For example, a "Multiply" blend mode often darkens the base layer with the overlay, which can be effective for combining a hillshade with a colorized DTM or another derivative. Experimentation with these modes is key.

*   **RGB Composites (False Color Composites):**
    *   **Principle:** This technique involves assigning three different raster datasets (or derivatives) to the Red, Green, and Blue display channels of a digital image. The combination creates a "false-color" image where colors are not natural but represent variations in the input datasets.
    *   **Potential Combinations for Archaeology:** The goal is to choose three layers that each highlight different aspects of the terrain or features of interest.
        *   **R: Slope, G: SVF (or Openness Positive), B: Hillshade:**
            *   *Red channel:* Emphasizes areas of steep slope (edges of earthworks, terraces).
            *   *Green channel:* Highlights concavities (SVF) or convexities (Openness Positive).
            *   *Blue channel:* Provides general topographic context and relief.
            *   *Interpretation:* Areas appearing bright red would be steep; bright green, very enclosed or very open; bright blue, well-illuminated by the hillshade. Combinations of these (yellow, magenta, cyan) would indicate co-occurrence of these properties.
        *   **R: DTM (normalized), G: Local Relief Model (LRM), B: Hillshade:**
            *   *Red channel:* Shows absolute elevation.
            *   *Green channel:* Emphasizes very local, subtle relief.
            *   *Blue channel:* General topographic shading.
        *   **R: Hillshade (Azimuth 1, e.g., 315°), G: Hillshade (Azimuth 2, e.g., 45°), B: DTM or SVF:**
            *   This uses hillshades from different (often opposing) sun angles in the red and green channels. This can make features visible regardless of their orientation relative to a single light source.
            *   The blue channel can provide elevation context (DTM) or highlight depressions/enclosure (SVF).
    *   **Considerations:**
        *   **Correlation:** Ideally, the chosen layers should be relatively uncorrelated to maximize the amount of unique information displayed. If two layers are highly correlated, their combination in an RGB composite might not be as informative.
        *   **Normalization:** It is critical that the input raster layers are individually stretched to a common value range (typically 0-255 for an 8-bit display channel, or 0-1 for floating-point processing) before being combined. Without proper normalization, one layer might dominate the composite, washing out the information from the others.
        *   **Interpretation:** RGB composites can be less intuitive to interpret initially than a simple hillshade overlay. It often requires practice and understanding what each channel represents to effectively decipher the resulting colors and patterns. However, they can reveal complex spatial relationships and feature signatures not visible in single layers.

*   **Brovey Transform / Pansharpening (Conceptual Application):**
    *   **Principle (from satellite remote sensing):** Pansharpening techniques (like the Brovey Transform, Gram-Schmidt, etc.) are used to merge a high-resolution panchromatic (grayscale) image with lower-resolution multispectral (color) bands. The result is a high-resolution color image that attempts to preserve both the spatial detail of the panchromatic band and the spectral information of the multispectral bands. The Brovey transform, for example, multiplies each multispectral band by the panchromatic band and divides by the sum of the multispectral bands (with adjustments for value ranges).
    *   **Conceptual Adaptation for DTM Derivatives:** While not a standard application in DTM visualization in the same way it's used in satellite imagery, the concept could be adapted experimentally.
        *   One might consider using a very high-resolution, detailed derivative (e.g., a texture analysis raster derived from the DTM, or a very fine-grained hillshade focusing on micro-relief) as the "panchromatic" layer to "sharpen" other, perhaps smoother or broader-scale derivatives (e.g., a colorized DTM, SVF, or LRM).
        *   For instance, one could try to modulate the intensity of a colorized DTM using a high-frequency texture layer.
    *   **Acknowledgement:** This is a more experimental approach for DTM derivative visualization compared to the well-established techniques above. Its effectiveness would require careful implementation and testing.

## 3. Tips for Effective Composites

*   **Data Normalization / Stretching:** Before combining rasters, especially for RGB composites or techniques involving mathematical operations between layers (like some overtinting methods), ensure their pixel values are scaled to a consistent and appropriate range (e.g., 0-255 for 8-bit display, or 0.0-1.0 for floating-point operations). This prevents any single layer with a large value range from dominating the visual output. Most GIS software has tools for histogram stretching (e.g., min-max, standard deviation).
*   **Layer Order:** When using transparent overlays (like DTM + Hillshade), the order in which layers are stacked in the GIS software is crucial. The hillshade (or other relief-enhancing layer) is typically placed on top of the colorized DTM.
*   **Experimentation:** There is no single "best" composite for all situations. The optimal combination of layers, parameters (like transparency), and blending modes often depends on the specific characteristics of the LiDAR data, the nature of the terrain, the types of archaeological anomalies being sought, and even user preference. Iterative testing and visual assessment are key.
*   **Purpose-Driven Composites:** Create composites with a clear goal in mind. For example:
    *   If trying to enhance subtle linear features, a combination of multi-azimuth hillshades or a hillshade with a slope layer might be effective.
    *   If searching for small pits or mounds, combining SVF/Openness with a Local Relief Model or a detailed hillshade might be more appropriate.
*   **Keep it Simple (Initially):** While complex composites can be powerful, start with simpler combinations (like DTM + Hillshade) and gradually add complexity if needed. Overly complex composites with too many layers can become visually cluttered and difficult to interpret.

By thoughtfully applying these composite techniques, archaeologists can create powerful visualizations that significantly enhance their ability to detect and interpret subtle archaeological features from DTM data.
