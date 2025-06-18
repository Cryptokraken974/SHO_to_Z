# Step 6: Considerations for AI Ingestion

## 1. Introduction

The Digital Terrain Models (DTMs), their derivatives (hillshade, slope, Sky-View Factor, Local Relief Model, etc.), and composite rasters generated in the previous steps are highly valuable inputs for Artificial Intelligence (AI) and Machine Learning (ML) models aimed at archaeological feature detection and landscape analysis. The primary goal of this step is to outline key considerations for preparing these raster datasets in a way that is optimal for ingestion into AI/ML pipelines, ensuring that the models can learn effectively from the data and produce meaningful results.

## 2. Data Selection for AI Input

Careful selection of which raster products to use as input for an AI model is crucial.

*   **Which Rasters?**
    *   **Single Best Derivative:** For simpler models or initial tests, using what is considered the single most informative derivative for the target features might be sufficient. For example, a Local Relief Model (LRM) often excels at highlighting subtle earthworks, or a specific multi-directional hillshade might be chosen.
    *   **Key Composites:** A visually effective composite (e.g., DTM color-shaded with a transparent hillshade overlay, saved as an RGB image) could be used, treating it as a standard image input.
    *   **Stacking Multiple Rasters as Input Channels:** This is often the most powerful approach. Similar to how a color photograph has Red, Green, and Blue channels, multiple co-registered rasters can be stacked to form a multi-channel input for the AI.
        *   **Example:** A 3-channel input could consist of [DTM, Slope, SVF]. Another could be [LRM, Hillshade_Azimuth1, Hillshade_Azimuth2].
        *   **Benefit:** This provides the AI model with richer, more diverse information about the terrain characteristics at each location, potentially leading to better discrimination of features. The AI can learn complex relationships between these different layers.
*   **Resolution Consistency:**
    *   It is critical that all raster layers being stacked or used as input for a specific AI model run share the **exact same spatial resolution (pixel size) and grid alignment**. If resolutions differ, rasters must be resampled (e.g., using bilinear or cubic convolution for continuous data) to a common resolution before stacking or tiling.

## 3. Data Normalization and Scaling

AI models, especially neural networks, typically perform best when input data is scaled to a specific, consistent range.

*   **Importance:**
    *   Prevents features with larger numerical values from dominating the learning process.
    *   Helps optimization algorithms (like gradient descent) converge faster and more reliably.
    *   Many activation functions in neural networks (e.g., sigmoid, tanh) operate within specific ranges (like 0 to 1 or -1 to 1).
*   **Common Methods:**
    *   **Min-Max Scaling (Normalization):** Scales the data to a fixed range, typically 0 to 1.
        *   `X_scaled = (X - X_min) / (X_max - X_min)`
        *   `X_min` and `X_max` can be global (across the entire dataset) or tile-specific. Global scaling is usually preferred for consistency if the overall data distribution is somewhat uniform.
    *   **Standardization (Z-score Normalization):** Transforms data to have a mean of 0 and a standard deviation of 1.
        *   `X_scaled = (X - mean) / std_dev`
        *   This is common and can be effective if the data contains outliers.
*   **Considerations:**
    *   The choice of normalization method can impact model performance and should be considered part of the model tuning process.
    *   The *same* normalization parameters (e.g., min/max values or mean/std_dev calculated from the **training set**) must be applied consistently to the training, validation, and testing datasets to avoid data leakage and ensure comparable distributions.

## 4. Tiling / Patching Strategy

Full-sized DTMs or derivative rasters are often too large to be fed directly into AI models (especially Convolutional Neural Networks - CNNs) due to memory limitations and the need for fixed-size inputs.

*   **Why Tile?**
    *   AI models, particularly CNNs, are designed to process images in smaller, fixed-size patches (tiles or windows).
    *   Tiling allows for batch processing, which is more memory-efficient.
*   **Tile Size:**
    *   Common tile sizes include 64x64, 128x128, 256x256, or 512x512 pixels.
    *   The optimal tile size depends on:
        *   The AI model architecture (some models have specific input size requirements).
        *   The average size of the archaeological features of interest (features should ideally be fully or mostly contained within a tile, or be recognizable from a patch of that size).
        *   Available GPU memory.
*   **Overlap:**
    *   It is highly recommended to introduce overlap between adjacent tiles (e.g., 10% to 25% of the tile width/height).
    *   **Reason:** This helps to avoid "edge effects" where an archaeological feature located at the border of a tile might be cut in half and thus be misclassified or missed by the model. Overlapping ensures that every feature is likely to appear fully within at least one tile during prediction.
*   **Handling No-Data Values:**
    *   LiDAR datasets often have "no-data" areas (e.g., outside the survey boundary, or water bodies if masked).
    *   These need to be handled consistently:
        *   **Filling:** After normalization, no-data values might be filled with a specific, consistent value (e.g., 0 if data is scaled to 0-1, or a value outside the typical scaled range).
        *   **Masking:** Some AI architectures can explicitly handle masked inputs, ignoring these pixels during computation.
    *   The chosen strategy should prevent no-data values from being misinterpreted as real terrain data.

## 5. Data Augmentation (from a GIS perspective)

Data augmentation involves artificially expanding the training dataset by creating modified versions of existing training samples. This helps to improve model generalization and reduce overfitting.

*   **GIS-Relevant Augmentations for Raster Tiles:**
    *   **Rotation:** Rotate tiles by 90, 180, 270 degrees. This can be useful if the orientation of archaeological features is variable or not a defining characteristic, or to teach the model orientation invariance.
    *   **Flipping:** Horizontal and/or vertical flips of the tiles.
    *   **Slight Variations in Derivatives (if generated on-the-fly or pre-generated):** For example, if using hillshades, generate training tiles using hillshades with slightly different azimuths or altitudes for the same ground truth feature. This can make the model more robust to variations in illumination.
    *   **Adding Noise:** Introduce small amounts of random Gaussian noise to the raster values. This can improve model robustness but should be used cautiously to avoid obscuring subtle features.
    *   **Contrast/Brightness Adjustments:** Slightly alter the contrast or brightness of the input tiles.
    *   **Elastic Deformations (use with extreme caution):** Minor, realistic warping of tiles. This is common in medical imaging but might be less appropriate for precise geospatial data unless deformations are very subtle and mimic natural variations.
*   **Note:** Augmentation techniques should aim to create realistic variations that the model might encounter in new, unseen data. The corresponding labels (ground truth) for augmented data must also be transformed consistently (e.g., if a tile is rotated, the label polygons within that tile must also be rotated).

## 6. Labeling / Ground Truth Data

For supervised learning tasks (where the AI learns to detect or classify specific types of anomalies), high-quality labeled data is essential.

*   **Crucial for Supervised Learning:** The AI model learns by comparing its predictions to these "ground truth" labels.
*   **Format:**
    *   **Polygons:** Vector polygons delineating the precise extent of known archaeological features (e.g., mounds, ditches, enclosures).
    *   **Bounding Boxes:** Simpler rectangular boxes around features.
    *   **Pixel Masks (Segmentation Masks):** Rasters where each pixel is labeled as belonging to a feature class or background. This is common for semantic segmentation models.
    *   Labels must be co-registered with the input raster tiles.
*   **Source:**
    *   Manual interpretation and digitization by experienced archaeologists based on the DTMs and derivatives.
    *   Existing archaeological databases or survey maps.
*   **Consistency and Accuracy:** The quality of the AI model is heavily dependent on the quality of the labels. Labeling must be consistent (e.g., what constitutes a "mound" should be uniformly applied) and spatially accurate. Inter-annotator agreement checks can be valuable.
*   **Balanced Datasets:** Strive for a balanced representation of different feature classes and background areas. If certain anomaly types are rare, techniques like oversampling rare classes or undersampling common ones might be needed.

## 7. Output Format for AI Ingestion and Prediction

*   **Input Tiles:** Often prepared as individual image files (e.g., PNG, TIFF) per tile, per channel if using stacked inputs. Some frameworks prefer specialized binary formats (e.g., TFRecords for TensorFlow, HDF5 files) for efficient data loading.
*   **Maintaining Georeferencing:**
    *   While the AI model itself might only see pixel arrays, it's crucial to keep track of the georeferencing information (e.g., coordinates of tile corners) for each tile.
    *   This allows predictions made by the AI (which will initially be in tile/pixel coordinates) to be accurately mapped back to their real-world geographic locations to create output maps of detected features. Tile filenames or accompanying metadata files can store this.

## 8. Experimentation and Iteration

Preparing data for AI is rarely a one-shot process.
*   The optimal combination of input rasters (which derivatives to stack), normalization techniques, tiling strategies, and augmentation methods will likely require significant experimentation.
*   Performance of the AI model on a validation dataset should guide these choices. Iteratively refine the data preparation pipeline based on model feedback.
*   Start simple and gradually add complexity.

By carefully considering these aspects of data preparation, archaeologists can significantly improve the chances of successfully applying AI models to LiDAR-derived DTMs for feature detection and landscape analysis.
