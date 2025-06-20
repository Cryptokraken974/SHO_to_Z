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
    
    // Map invalid levels to valid console methods
    const validLevels = {
      'info': 'info',
      'warn': 'warn', 
      'warning': 'warn', // Map 'warning' to 'warn'
      'error': 'error',
      'debug': 'debug',
      'log': 'log'
    };
    
    const consoleMethod = validLevels[level] || 'log';
    console[consoleMethod](logMessage, data || '');
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

  /**
   * Parse coordinates from various string formats
   * @param {string} coordString - Coordinate string in various formats
   * @returns {Object|null} Object with lat/lng as decimal degrees or null if invalid
   */
  parseCoordinateString(coordString) {
    if (!coordString || typeof coordString !== 'string') {
      return null;
    }

    // Clean the input string
    const cleaned = coordString.trim().replace(/\s+/g, ' ');

    try {
      // Pattern 1: Degrees, Minutes, Seconds format "10°42′05″S, 67°52′36″W"
      const dmsPattern = /(\d+)\s*°\s*(\d+)\s*[′']\s*(\d+(?:\.\d+)?)\s*[″"]\s*([NSEW])\s*,?\s*(\d+)\s*°\s*(\d+)\s*[′']\s*(\d+(?:\.\d+)?)\s*[″"]\s*([NSEW])/i;
      const dmsMatch = cleaned.match(dmsPattern);
      
      if (dmsMatch) {
        const [, deg1, min1, sec1, dir1, deg2, min2, sec2, dir2] = dmsMatch;
        
        // Convert DMS to decimal degrees
        const decimal1 = parseFloat(deg1) + parseFloat(min1) / 60 + parseFloat(sec1) / 3600;
        const decimal2 = parseFloat(deg2) + parseFloat(min2) / 60 + parseFloat(sec2) / 3600;
        
        // Determine which values are lat/lng based on direction indicators
        let lat, lng;
        if (['N', 'S'].includes(dir1.toUpperCase()) && ['E', 'W'].includes(dir2.toUpperCase())) {
          lat = decimal1;
          lng = decimal2;
          
          // Apply sign based on direction
          if (dir1.toUpperCase() === 'S') lat = -lat;
          if (dir2.toUpperCase() === 'W') lng = -lng;
        } else if (['E', 'W'].includes(dir1.toUpperCase()) && ['N', 'S'].includes(dir2.toUpperCase())) {
          // Swapped order: lng first, lat second
          lng = decimal1;
          lat = decimal2;
          
          // Apply sign based on direction
          if (dir1.toUpperCase() === 'W') lng = -lng;
          if (dir2.toUpperCase() === 'S') lat = -lat;
        } else {
          return null;
        }
        
        return this.isValidCoordinate(lat, lng) ? { lat, lng } : null;
      }

      // Pattern 2: "8.845°S, 67.255°W" format (decimal degrees with direction)
      const degreePattern = /(\d+(?:\.\d+)?)\s*°?\s*([NSEW])\s*,?\s*(\d+(?:\.\d+)?)\s*°?\s*([NSEW])/i;
      const degreeMatch = cleaned.match(degreePattern);
      
      if (degreeMatch) {
        const [, lat1, dir1, lng1, dir2] = degreeMatch;
        
        // Determine which values are lat/lng based on direction indicators
        let lat, lng;
        if (['N', 'S'].includes(dir1.toUpperCase()) && ['E', 'W'].includes(dir2.toUpperCase())) {
          lat = parseFloat(lat1);
          lng = parseFloat(lng1);
          
          // Apply sign based on direction
          if (dir1.toUpperCase() === 'S') lat = -lat;
          if (dir2.toUpperCase() === 'W') lng = -lng;
        } else if (['E', 'W'].includes(dir1.toUpperCase()) && ['N', 'S'].includes(dir2.toUpperCase())) {
          // Swapped order: lng first, lat second
          lng = parseFloat(lat1);
          lat = parseFloat(lng1);
          
          // Apply sign based on direction
          if (dir1.toUpperCase() === 'W') lng = -lng;
          if (dir2.toUpperCase() === 'S') lat = -lat;
        } else {
          return null;
        }
        
        return this.isValidCoordinate(lat, lng) ? { lat, lng } : null;
      }

      // Pattern 3: "-8.845, -67.255" or "8.845, -67.255" format (decimal degrees)
      const decimalPattern = /^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/;
      const decimalMatch = cleaned.match(decimalPattern);
      
      if (decimalMatch) {
        const lat = parseFloat(decimalMatch[1]);
        const lng = parseFloat(decimalMatch[2]);
        
        return this.isValidCoordinate(lat, lng) ? { lat, lng } : null;
      }

      // Pattern 4: Single coordinate with direction (try to parse what we can)
      const singlePattern = /(\d+(?:\.\d+)?)\s*°?\s*([NSEW])/i;
      const singleMatch = cleaned.match(singlePattern);
      
      if (singleMatch) {
        // This is incomplete, but we can at least validate the format
        return null; // Don't process incomplete coordinates
      }

    } catch (error) {
      console.error('Error parsing coordinate string:', error);
      return null;
    }

    return null;
  },
};
