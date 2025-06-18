# Step 2: Describe Key DTM Derivatives for Anomaly Detection

## 1. Introduction

While a high-quality Digital Terrain Model (DTM) provides the fundamental bare-earth elevation data, its direct visualization can often be insufficient for detecting subtle archaeological anomalies, especially in complex or eroded landscapes like those found in Amazonia. DTM derivatives are secondary raster products calculated from the DTM that enhance specific aspects of the topography. By exaggerating or isolating certain terrain characteristics, these derivatives make subtle features more visually apparent and aid in their identification and interpretation as potential archaeological anomalies.

## 2. Hillshade

*   **Principle:** Hillshade (or shaded relief) simulates the illumination of the DTM surface by a light source from a specific direction (azimuth) and angle above the horizon (altitude). It calculates the brightness of each pixel based on its orientation relative to the light source, creating an intuitive representation of topography with highlights and shadows that mimic how we perceive 3D surfaces.
*   **Key Parameters:**
    *   **Azimuth:** The direction of the simulated sun, measured in degrees clockwise from North (0° to 360°). A common default is 315° (NW lighting).
        *   **Importance of Multiple Azimuths:** Features (especially linear ones) oriented parallel to the light source may be poorly illuminated and thus difficult to see. Generating and comparing hillshades from multiple azimuths (e.g., 315°, 270°, 225°, 45°, or even more) is crucial. A "multi-directional hillshade" combines several hillshades into a single, often more informative image.
    *   **Altitude:** The angle of the sun above the horizon, measured in degrees (0° to 90°).
        *   Common values range from 30° to 45°. Lower angles (e.g., 20-30°) produce longer shadows and can accentuate subtle relief but may also obscure features in areas of high relief or create excessively large shadowed areas. Higher angles (e.g., >45°) provide more even illumination but may flatten the appearance of subtle features.
    *   **Z-factor (Vertical Exaggeration):** A scaling factor applied to the elevation values before calculating the hillshade.
        *   This is crucial for enhancing very subtle, low-relief features that might otherwise be invisible. By exaggerating the vertical dimension relative to the horizontal, small variations become more pronounced.
        *   Common Z-factor values for archaeological prospection range from 2x to 5x, but can sometimes be higher for extremely subtle features. The optimal value depends on the feature height and the overall landscape relief.
*   **Utility for Anomalies:** Hillshade is one of the most widely used derivatives. It is excellent for visualizing:
    *   **Linear features:** Banks, ditches, causeways, ancient roads, field boundaries.
    *   **Mounds:** Burial mounds, house platforms, agricultural mounds.
    *   **Depressions:** Pits, sunken features, moats.
    *   The overall form and layout of larger earthwork complexes.

## 3. Slope

*   **Principle:** The slope derivative calculates the rate of change of elevation at each pixel in the DTM, representing the steepness of the terrain.
*   **Units:** Typically expressed in degrees (0° for flat terrain, 90° for a vertical cliff) or as a percentage (rise over run, multiplied by 100).
*   **Key Parameters:** Generally, the primary input is the DTM itself. Some software tools might offer different algorithms for slope calculation (e.g., average neighborhood slope vs. maximum slope), but these usually have minor effects on archaeological interpretation. The Z-factor of the input DTM can influence the slope values.
*   **Utility for Anomalies:** Slope maps are very effective at:
    *   Highlighting the edges of earthworks where there's an abrupt change in slope (e.g., the scarp of a ditch, the side of a mound or platform).
    *   Identifying terracing, ramparts, or fortification lines.
    *   Differentiating between natural geomorphological slopes and artificially constructed slopes, which may have more regular or distinct slope values.
    *   Mapping breaks in slope that might indicate former agricultural terraces or other land modifications.

## 4. Aspect

*   **Principle:** The aspect derivative determines the compass direction that each slope faces. It assigns a value to each pixel indicating the orientation of the slope at that location (e.g., 0-360°, with North typically being 0° or 360°, East 90°, South 180°, West 270°). Flat areas are often assigned a specific value (e.g., -1).
*   **Utility for Anomalies:**
    *   Aspect is less directly used for primary anomaly detection compared to hillshade or slope.
    *   However, it can be valuable for understanding the layout and orientation of identified features in relation to the surrounding landscape (e.g., are features preferentially built on south-facing slopes?).
    *   It can sometimes help highlight features that have a consistent, specific alignment, especially if they are subtle and their primary characteristic is their directional trend rather than a sharp relief. For example, ancient field systems or drainage patterns might exhibit consistent aspect values.

## 5. Sky-View Factor (SVF) / Openness

*   **Principle:**
    *   **Sky-View Factor (SVF)**, also known as **Topographic Enclosure** or **Negative Openness**, measures the proportion of the sky visible from a specific point on the DTM surface when looking upwards in all directions within a defined radius. Lower SVF values indicate locations that are more enclosed by surrounding higher terrain (concavities).
    *   **Positive Openness** is the inverse, measuring the degree to which a point is exposed or sits above the surrounding terrain within a defined radius. Higher Positive Openness values highlight convexities.
*   **Key Parameters:**
    *   **Search Radius:** This is a critical parameter. It defines the distance from each cell within which the algorithm considers occluding (for SVF) or lower (for Positive Openness) terrain.
        *   A small radius will emphasize very local micro-topography.
        *   A large radius will capture broader topographic context.
        *   The radius should be adapted to the expected scale of the features of interest. For example, a small radius (e.g., 5-10 meters) might be good for small pits, while a larger radius (e.g., 50-100 meters) might be better for broader, shallow depressions or larger mounds. Multiple radii are often tested.
*   **Utility for Anomalies:**
    *   **SVF/Negative Openness:** Extremely effective for detecting subtle concavities such as:
        *   House pits, storage pits, borrow pits.
        *   Sunken roads, trails, or canals.
        *   Eroded ditches or moats.
    *   **Positive Openness:** Useful for highlighting subtle convexities like:
        *   Low, eroded mounds or platforms.
        *   Remnant field boundaries or causeways.
    *   Both are particularly powerful in relatively flat terrain where hillshade might not clearly reveal such features. They are less affected by illumination direction biases than hillshade.

## 6. Local Relief Model (LRM) / Multi-scale Topographic Position Index (TPI)

*   **Principle:**
    *   **Local Relief Model (LRM):** This is created by subtracting a heavily smoothed version of the DTM from the original DTM (DTM_original - DTM_smoothed = LRM). The smoothing process (e.g., using a mean or Gaussian filter with a large kernel) removes the broad-scale, regional topography, leaving behind the local, higher-frequency variations.
    *   **Topographic Position Index (TPI):** TPI calculates the difference between the elevation of a central pixel and the mean elevation of its neighboring pixels within a defined radius. Positive TPI values indicate locations that are higher than their surroundings (crests, mounds), negative values indicate locations lower than their surroundings (valleys, depressions), and values near zero indicate flat areas or constant slopes.
        *   **Multi-scale TPI:** Involves calculating TPI at multiple neighborhood radii (e.g., small, medium, large) and combining them. This helps to classify features based on their characteristics at different scales.
*   **Key Parameters:**
    *   **LRM:** The size and type of the smoothing kernel (e.g., window size for a mean filter, standard deviation for a Gaussian filter). A larger kernel removes more of the regional trend, emphasizing smaller local features.
    *   **TPI:** The radius (or radii for multi-scale) of the neighborhood used for comparison. The choice of radius dictates the scale of features that will be highlighted.
*   **Utility for Anomalies:**
    *   Both LRM and TPI are excellent for enhancing very subtle, low-relief archaeological features that might be "drowned out" or masked by the larger, natural variations in the landscape.
    *   They can make faint earthworks, eroded mounds, subtle depressions, agricultural ridges, or ancient causeways stand out clearly from the background topography.
    *   Particularly useful in areas with undulating terrain where global relief changes can obscure local anthropogenic modifications.

## 7. Other Potential Derivatives (Briefly Mention)

While the above are often the primary workhorses, other derivatives can be useful in specific contexts:

*   **Curvature:** Measures the rate of change of slope.
    *   **Profile Curvature:** Curvature in the direction of maximum slope. Can highlight breaks in slope.
    *   **Planform Curvature:** Curvature perpendicular to the direction of maximum slope. Can highlight ridges or valleys.
    *   **Tangential Curvature:** More complex, but can be sensitive to subtle changes in surface shape.
    *   Curvature can help identify the edges of features or subtle changes in their form.
*   **Drainage Networks / Flow Accumulation:**
    *   Derived by simulating water flow over the DTM. Flow accumulation highlights channels where water would concentrate.
    *   Can sometimes reveal anthropogenic alterations to natural hydrology (e.g., canals, diversions) or features that are aligned with or interact with water flow patterns (e.g., fish traps, agricultural systems).
    *   Can also help identify natural features (gullies, streams) that need to be distinguished from anthropogenic ones.

By combining and comparing these various DTM derivatives, archaeologists can significantly improve their ability to detect, delineate, and interpret potential archaeological anomalies hidden within the landscape. Each derivative offers a different perspective on the terrain, and their synergistic use often leads to more robust and reliable feature identification.
