/**
 * Metadata Manager for Region Selection
 * Creates simple coordinate-only metadata files when regions are selected
 */

window.MetadataManager = {
  
  /**
   * Create simple coordinate metadata file for a selected region
   * @param {string} regionName - Name of the region
   * @param {Object} coords - Coordinates object with lat/lng
   * @param {string} processingRegion - Processing region name 
   * @returns {Promise<boolean>} Success status
   */
  async createRegionMetadata(regionName, coords, processingRegion = null) {
    try {
      if (!coords || !coords.lat || !coords.lng) {
        Utils.log('warn', 'No coordinates provided for metadata creation');
        return false;
      }

      const effectiveRegionName = processingRegion || regionName;
      
      // Create simple metadata with just coordinates
      const metadata = {
        region_name: effectiveRegionName,
        display_name: regionName,
        center_latitude: coords.lat,
        center_longitude: coords.lng,
        creation_time: new Date().toISOString(),
        source: 'region_selection'
      };

      Utils.log('info', `Creating simple metadata for region: ${regionName}`, metadata);

      // Call backend API to create the metadata file
      const result = await this.saveMetadataToFile(effectiveRegionName, metadata);
      
      if (result.success) {
        Utils.log('info', `Metadata file created successfully for region: ${regionName}`);
        Utils.showNotification(`Created metadata for ${regionName}`, 'info', 2000);
        return true;
      } else {
        Utils.log('error', `Failed to create metadata file: ${result.error}`);
        return false;
      }

    } catch (error) {
      Utils.log('error', 'Error creating region metadata:', error);
      return false;
    }
  },

  /**
   * Save metadata to file via backend API
   * @param {string} regionName - Region name for file path
   * @param {Object} metadata - Metadata object to save
   * @returns {Promise<Object>} API response
   */
  async saveMetadataToFile(regionName, metadata) {
    try {
      const response = await fetch('/api/save-region-metadata', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          region_name: regionName,
          metadata: metadata
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      Utils.log('error', 'API call failed for metadata creation:', error);
      return { success: false, error: error.message };
    }
  }
};
