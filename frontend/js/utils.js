/**
 * Utility functions and helpers
 */

window.Utils = {
  /**
   * Show notification message
   * @param {string} message - Message to show
   * @param {string} type - Type of notification (info, success, error, warning)
   * @param {number} duration - Duration in milliseconds (optional)
   */
  showNotification(message, type = 'info', duration = 3000) {
    const notification = $(`
      <div class="notification notification-${type}">
        <span class="notification-message">${message}</span>
        <button class="notification-close">&times;</button>
      </div>
    `);
    
    $('body').append(notification);
    
    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        notification.fadeOut(() => notification.remove());
      }, duration);
    }
    
    // Remove on close button click
    notification.find('.notification-close').on('click', function() {
      notification.fadeOut(() => notification.remove());
    });
  },

  /**
   * Debounce function to limit the rate of function calls
   * @param {Function} func - Function to debounce
   * @param {number} wait - Wait time in milliseconds
   * @returns {Function} Debounced function
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Format file size in human readable format
   * @param {number} bytes - Size in bytes
   * @returns {string} Formatted size string
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  /**
   * Extract coordinates from filename
   * @param {string} filename - LAZ filename
   * @returns {Object|null} Object with lat/lng or null if not found
   */
  extractCoordinatesFromFilename(filename) {
    // Pattern for files like "lidar_22.95S_43.21W_lidar.laz"
    const pattern = /lidar_(\d+\.?\d*)([NS])_(\d+\.?\d*)([EW])/i;
    const match = filename.match(pattern);
    
    if (match) {
      let lat = parseFloat(match[1]);
      let lng = parseFloat(match[3]);
      
      // Apply negative values for South and West
      if (match[2].toUpperCase() === 'S') lat = -lat;
      if (match[4].toUpperCase() === 'W') lng = -lng;
      
      return { lat, lng };
    }
    
    return null;
  },

  /**
   * Validate coordinate values
   * @param {number} lat - Latitude
   * @param {number} lng - Longitude
   * @returns {boolean} True if valid coordinates
   */
  isValidCoordinate(lat, lng) {
    return (
      typeof lat === 'number' && 
      typeof lng === 'number' &&
      lat >= -90 && lat <= 90 &&
      lng >= -180 && lng <= 180
    );
  },

  /**
   * Deep clone an object
   * @param {Object} obj - Object to clone
   * @returns {Object} Cloned object
   */
  deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
  },

  /**
   * Generate unique ID
   * @returns {string} Unique identifier
   */
  generateId() {
    return Math.random().toString(36).substr(2, 9);
  },

  /**
   * Log with timestamp
   * @param {string} level - Log level (info, warn, error)
   * @param {string} message - Log message
   * @param {any} data - Additional data to log
   */
  log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${level.toUpperCase()}: ${message}`;
    
    console[level](logMessage, data || '');
  },

  /**
   * Generate region name from coordinates
   * @param {number} lat - Latitude value
   * @param {number} lng - Longitude value
   * @returns {string} Region name in format like "22.95S_43.21W"
   */
  generateRegionName(lat, lng) {
    if (!this.isValidCoordinate(lat, lng)) {
      return '';
    }

    // Convert to absolute values and determine directions
    const absLat = Math.abs(lat);
    const absLng = Math.abs(lng);
    const latDir = lat >= 0 ? 'N' : 'S';
    const lngDir = lng >= 0 ? 'E' : 'W';

    // Format with 2 decimal places
    const formattedLat = absLat.toFixed(2);
    const formattedLng = absLng.toFixed(2);

    return `${formattedLat}${latDir}_${formattedLng}${lngDir}`;
  },
};
