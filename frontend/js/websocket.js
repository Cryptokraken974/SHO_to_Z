/**
 * WebSocket communication for real-time progress updates
 */

window.WebSocketManager = {
  socket: null,
  reconnectAttempts: 0,
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,
  currentDownload: null, // Track Sentinel-2 download progress

  /**
   * Initialize WebSocket connection
   */
  init() {
    this.connect();
  },

  /**
   * Connect to WebSocket server
   */
  connect() {
    try {
      // Determine WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/progress`;
      
      Utils.log('info', `Connecting to WebSocket: ${wsUrl}`);
      
      this.socket = new WebSocket(wsUrl);
      this.setupEventHandlers();
      
    } catch (error) {
      Utils.log('error', 'Failed to create WebSocket connection', error);
      this.handleConnectionError();
    }
  },

  /**
   * Setup WebSocket event handlers
   */
  setupEventHandlers() {
    this.socket.onopen = () => {
      Utils.log('info', 'WebSocket connected successfully');
      this.reconnectAttempts = 0;
      this.onConnectionEstablished();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        Utils.log('error', 'Failed to parse WebSocket message', error);
      }
    };

    this.socket.onclose = (event) => {
      Utils.log('info', `WebSocket connection closed: ${event.code} - ${event.reason}`);
      this.handleConnectionClose();
    };

    this.socket.onerror = (error) => {
      Utils.log('error', 'WebSocket error', error);
      this.handleConnectionError();
    };
  },

  /**
   * Handle incoming WebSocket messages
   * @param {Object} data - Message data
   */
  handleMessage(data) {
    const { type, message, progress, processingType, status } = data;
    
    switch (type) {
      case 'progress':
        this.handleProgressUpdate(processingType, progress, message);
        break;
        
      case 'status':
        this.handleStatusUpdate(processingType, status, message);
        break;
        
      case 'error':
        this.handleErrorMessage(processingType, message);
        break;
        
      case 'complete':
        this.handleCompletionMessage(processingType, message);
        break;
        
      case 'log':
        this.handleLogMessage(message, data.level || 'info');
        break;

      case 'download_start':
        this.handleDownloadStart(data);
        break;
        
      case 'download_info':
        this.handleDownloadInfo(data);
        break;
        
      case 'download_complete':
        this.handleDownloadComplete(data);
        break;
        
      default:
        Utils.log('warn', `Unknown WebSocket message type: ${type}`, data);
    }
  },

  /**
   * Handle progress updates
   * @param {string} processingType - Type of processing
   * @param {number} progress - Progress percentage (0-100)
   * @param {string} message - Progress message
   */
  handleProgressUpdate(processingType, progress, message) {
    // Update progress bar if exists
    const progressBar = $(`#progress-bar-${processingType}`);
    if (progressBar.length) {
      progressBar.css('width', `${progress}%`)
                .attr('aria-valuenow', progress)
                .text(`${Math.round(progress)}%`);
    }
    
    // Update progress text
    const progressText = $(`#progress-text-${processingType}`);
    if (progressText.length) {
      progressText.text(message || `Processing... ${Math.round(progress)}%`);
    }
    
    // Update global progress indicator
    this.updateGlobalProgress(processingType, progress, message);
    
    Utils.log('info', `Progress update for ${processingType}: ${progress}% - ${message}`);
  },

  /**
   * Handle status updates
   * @param {string} processingType - Type of processing
   * @param {string} status - Processing status
   * @param {string} message - Status message
   */
  handleStatusUpdate(processingType, status, message) {
    // Update processing UI based on status
    if (ProcessingManager.updateProcessingUI) {
      ProcessingManager.updateProcessingUI(processingType, status);
    }
    
    // Show status notification
    let notificationType = 'info';
    if (status === 'error' || status === 'failed') {
      notificationType = 'error';
    } else if (status === 'completed' || status === 'success') {
      notificationType = 'success';
    }
    
    Utils.showNotification(message, notificationType, 3000);
    
    Utils.log('info', `Status update for ${processingType}: ${status} - ${message}`);
  },

  /**
   * Handle error messages
   * @param {string} processingType - Type of processing
   * @param {string} message - Error message
   */
  handleErrorMessage(processingType, message) {
    if (ProcessingManager.handleProcessingError) {
      ProcessingManager.handleProcessingError(processingType, message);
    }
    
    Utils.showNotification(`Error in ${processingType}: ${message}`, 'error');
    Utils.log('error', `Processing error for ${processingType}: ${message}`);
  },

  /**
   * Handle completion messages
   * @param {string} processingType - Type of processing
   * @param {string} message - Completion message
   */
  handleCompletionMessage(processingType, message) {
    if (ProcessingManager.handleProcessingSuccess) {
      ProcessingManager.handleProcessingSuccess(processingType, { message });
    }
    
    Utils.showNotification(`${processingType} completed: ${message}`, 'success');
    Utils.log('info', `Processing completed for ${processingType}: ${message}`);
  },

  /**
   * Handle log messages
   * @param {string} message - Log message
   * @param {string} level - Log level
   */
  handleLogMessage(message, level) {
    // Add to console log
    Utils.log(level, `[WebSocket] ${message}`);
    
    // Optionally add to a debug console in the UI
    const debugConsole = $('#debug-console');
    if (debugConsole.length && debugConsole.is(':visible')) {
      const timestamp = new Date().toLocaleTimeString();
      const logEntry = $(`<div class="log-entry log-${level}">[${timestamp}] ${message}</div>`);
      debugConsole.append(logEntry);
      
      // Auto-scroll to bottom
      debugConsole.scrollTop(debugConsole[0].scrollHeight);
      
      // Limit number of log entries
      const entries = debugConsole.find('.log-entry');
      if (entries.length > 100) {
        entries.first().remove();
      }
    }
  },

  /**
   * Handle Sentinel-2 download start
   * @param {Object} data - Download start data
   */
  handleDownloadStart(data) {
    const { message, total_files, download_id } = data;
    
    // Update progress modal
    if (window.UIManager && window.UIManager.updateProgress) {
      window.UIManager.updateProgress(0, message || 'Starting Sentinel-2 download...');
    }
    
    // Store download info for progress tracking
    this.currentDownload = {
      id: download_id,
      totalFiles: total_files || 1,
      downloadedFiles: 0
    };
    
    Utils.log('info', `Sentinel-2 download started: ${message}`, data);
  },

  /**
   * Handle Sentinel-2 download progress info
   * @param {Object} data - Download progress data
   */
  handleDownloadInfo(data) {
    const { message, file_name, current_file, total_files, download_id } = data;
    
    if (this.currentDownload && download_id === this.currentDownload.id) {
      // Update downloaded files count
      if (current_file) {
        this.currentDownload.downloadedFiles = current_file;
      }
      
      // Calculate progress percentage
      const progress = total_files ? 
        Math.round((this.currentDownload.downloadedFiles / total_files) * 100) : 0;
      
      // Create detailed message
      const progressMessage = file_name ? 
        `Downloading: ${file_name} (${this.currentDownload.downloadedFiles}/${total_files})` :
        message || `Downloading files... (${this.currentDownload.downloadedFiles}/${total_files})`;
      
      // Update progress modal
      if (window.UIManager && window.UIManager.updateProgress) {
        window.UIManager.updateProgress(progress, progressMessage);
      }
      
      Utils.log('info', `Sentinel-2 download progress: ${progress}% - ${progressMessage}`);
    }
  },

  /**
   * Handle Sentinel-2 download completion
   * @param {Object} data - Download completion data
   */
  handleDownloadComplete(data) {
    const { message, download_path, total_files, download_id } = data;
    
    if (this.currentDownload && download_id === this.currentDownload.id) {
      // Update progress to 100%
      if (window.UIManager && window.UIManager.updateProgress) {
        window.UIManager.updateProgress(100, message || 'Sentinel-2 download completed!');
      }
      
      // Show completion notification
      Utils.showNotification(
        `Sentinel-2 download completed: ${total_files} files downloaded`, 
        'success', 
        5000
      );
      
      // Clear download tracking
      this.currentDownload = null;
      
      Utils.log('info', `Sentinel-2 download completed: ${message}`, data);
      
      // If UIManager has a callback for download completion, call it
      if (window.UIManager && window.UIManager.onSentinel2DownloadComplete) {
        window.UIManager.onSentinel2DownloadComplete(data);
      }
    }
  },

  /**
   * Update global progress indicator
   * @param {string} processingType - Type of processing
   * @param {number} progress - Progress percentage
   * @param {string} message - Progress message
   */
  updateGlobalProgress(processingType, progress, message) {
    const globalIndicator = $('#global-progress');
    if (globalIndicator.length) {
      globalIndicator.show()
                    .find('.progress-bar')
                    .css('width', `${progress}%`);
      
      globalIndicator.find('.progress-text')
                    .text(`${processingType}: ${message || `${Math.round(progress)}%`}`);
      
      // Hide when complete
      if (progress >= 100) {
        setTimeout(() => {
          globalIndicator.fadeOut();
        }, 2000);
      }
    }
  },

  /**
   * Handle connection established
   */
  onConnectionEstablished() {
    // Update connection status in UI
    $('#connection-status').removeClass('disconnected').addClass('connected');
    
    // Send initial handshake if needed
    this.sendMessage({
      type: 'handshake',
      clientId: Utils.generateId(),
      timestamp: Date.now()
    });
  },

  /**
   * Handle connection close
   */
  handleConnectionClose() {
    // Update connection status in UI
    $('#connection-status').removeClass('connected').addClass('disconnected');
    
    // Attempt to reconnect
    this.attemptReconnect();
  },

  /**
   * Handle connection error
   */
  handleConnectionError() {
    // Update connection status in UI
    $('#connection-status').removeClass('connected').addClass('error');
    
    // Attempt to reconnect
    this.attemptReconnect();
  },

  /**
   * Attempt to reconnect to WebSocket
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      Utils.log('error', 'Max reconnection attempts reached');
      Utils.showNotification('Lost connection to server. Please refresh the page.', 'error', 0);
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    Utils.log('info', `Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  },

  /**
   * Send message to WebSocket server
   * @param {Object} data - Message data to send
   */
  sendMessage(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      try {
        this.socket.send(JSON.stringify(data));
        Utils.log('info', 'Sent WebSocket message', data);
      } catch (error) {
        Utils.log('error', 'Failed to send WebSocket message', error);
      }
    } else {
      Utils.log('warn', 'WebSocket not connected, cannot send message', data);
    }
  },

  /**
   * Close WebSocket connection
   */
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  },

  /**
   * Get connection status
   * @returns {string} Connection status
   */
  getConnectionStatus() {
    if (!this.socket) return 'disconnected';
    
    switch (this.socket.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'unknown';
    }
  }
};
