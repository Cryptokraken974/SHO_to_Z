# JavaScript Modules Documentation - SHO to Z Application

## Overview
This document provides detailed descriptions of all JavaScript modules in the SHO to Z web application. The application follows a modular architecture with each module handling specific responsibilities.

## Module Architecture

```
app_new.js (Main Entry Point)
├── utils.js (Core Utilities)
├── map.js (Map Management)
├── fileManager.js (File Operations)
├── overlays.js (Map Overlay Management)
├── processing.js (LAZ File Processing)
├── websocket.js (Real-time Communication)
└── ui.js (User Interface Management)
```

---

## 1. app_new.js - Main Application Controller

**Purpose**: Application entry point and module coordination
**Global Object**: `SHOtoZ`

### Key Functions:
- `initializeApplication()` - Main initialization sequence
- `waitForDOM()` - DOM ready checker
- `checkRequiredElements()` - Validates HTML elements exist
- `validateModules()` - Ensures all modules loaded correctly

### Initialization Flow:
1. Wait for DOM ready
2. Check required HTML elements exist
3. Initialize all modules in order:
   - Utils → Map → FileManager → OverlayManager → ProcessingManager → WebSocketManager → UIManager
4. Set up global error handlers
5. Load saved user preferences

### Key Data:
- `SHOtoZ.version` - Application version
- `SHOtoZ.initialized` - Initialization status
- `SHOtoZ.modules` - Module references

---

## 2. utils.js - Core Utility Functions

**Purpose**: Shared utility functions across all modules
**Global Object**: `Utils`

### Key Functions:

#### Notifications
- `showNotification(message, type, duration)` - Display toast notifications
  - Types: 'info', 'success', 'error', 'warning'
  - Auto-dismisses after duration (default 3000ms)

#### Utilities
- `debounce(func, wait)` - Rate-limit function calls
- `throttle(func, limit)` - Throttle function execution
- `formatFileSize(bytes)` - Human-readable file sizes
- `formatDuration(ms)` - Format time durations
- `generateId()` - Generate unique IDs
- `isValidCoordinate(lat, lng)` - Validate geographic coordinates
- `parseCoordinates(input)` - Parse coordinate strings
- `downloadBlob(blob, filename)` - Download file blobs

#### Logging
- `log(level, message, data)` - Centralized logging
  - Levels: 'info', 'warn', 'error', 'debug'
  - Integrates with browser console and optional backend logging

### Key Data Structures:
- Notification queue management
- Log level configuration
- Performance timing utilities

---

## 3. map.js - Map Management

**Purpose**: Leaflet map initialization and core mapping functionality
**Global Object**: `MapManager`

### Key Properties:
- `map` - Leaflet map instance
- `drawnItems` - Layer group for user drawings
- `drawControl` - Leaflet.draw controls
- `sentinel2TestMarker` - Marker for Sentinel-2 test coordinates

### Key Functions:

#### Map Operations
- `init()` - Initialize Leaflet map centered on Brazil
- `getMap()` - Get map instance
- `setView(lat, lng, zoom)` - Set map view
- `fitBounds(bounds)` - Fit map to bounds
- `addMarker(lat, lng, options)` - Add map markers

#### Drawing Controls
- `initDrawingControls()` - Set up area selection tools
- `enableDrawing()` - Enable drawing mode
- `disableDrawing()` - Disable drawing mode
- `clearDrawings()` - Remove all drawings

#### Event Handling
- `setupEventHandlers()` - Map click/drawing events
- `onMapClick(e)` - Handle map clicks for coordinate capture
- `onDrawCreated(e)` - Handle area drawings
- `updateCoordinateInputs(lat, lng)` - Update coordinate input fields

#### Markers
- `addSentinel2TestMarker(lat, lng)` - Add marker for Sentinel-2 testing
- `clearMarkers()` - Remove all markers

### Key Data Flow:
1. User clicks map → coordinates captured → input fields updated
2. User draws area → bounds calculated → processing area defined
3. Coordinate inputs changed → map view updated → marker added

### HTML Element IDs:
- `#map` - Map container
- `#lat-input`, `#lng-input` - Coordinate input fields

---

## 4. fileManager.js - File Operations

**Purpose**: LAZ file management and server communication
**Global Object**: `FileManager`

### Key Properties:
- `selectedLazFile` - Currently selected LAZ file path
- `lazFileMarkers` - Array of map markers for LAZ files
- `currentLocationPin` - Current location marker

### Key Functions:

#### File Loading
- `loadFiles()` - Fetch LAZ files from `/api/list-laz-files`
- `displayFiles(files)` - Render file list in modal
- `createLazFileMarkers(files)` - Add markers to map for file locations

#### File Selection
- `selectFile(filePath, fileName, coords)` - Select a LAZ file
- `getSelectedFile()` - Get currently selected file path
- `clearSelection()` - Clear file selection

#### UI Updates
- `updateFileDisplay(fileName)` - Update selected file display
- `updateLocationPin(coords)` - Update map location marker
- `showFileDetails(fileInfo)` - Show file information

### Key Data Flow:
1. User clicks "Browse Files" → `loadFiles()` called
2. Server returns file list → files displayed in modal
3. User selects file → coordinates extracted → map updated
4. Selected file becomes available for processing

### API Endpoints:
- `GET /api/list-laz-files` - Fetch available LAZ files

### HTML Element IDs:
- `#file-modal` - File selection modal
- `#file-list` - File list container
- `#selected-file-name` - Display selected file

---

## 5. processing.js - LAZ File Processing

**Purpose**: Handle all LAZ file processing operations
**Global Object**: `ProcessingManager`

### Key Properties:
- `activeProcesses` - Set of currently running processes

### Key Functions:

#### Core Processing
- `sendProcess(processingType, options)` - Send processing request to server
- `cancelProcessing(processingType)` - Cancel active processing (UI only)

#### Processing Types
- `processDTM()` - Digital Terrain Model
- `processHillshade()` - Hillshade visualization
- `processDSM()` - Digital Surface Model
- `processCHM()` - Canopy Height Model
- `processSlope()` - Slope analysis
- `processAspect()` - Aspect analysis
- `processRoughness()` - Terrain roughness
- `processTRI()` - Terrain Ruggedness Index
- `processTPI()` - Topographic Position Index
- `processColorRelief()` - Color relief maps

#### UI Management
- `updateProcessingUI(processingType, status)` - Update button states
- `handleProcessingSuccess(processingType, data)` - Handle successful processing
- `handleProcessingError(processingType, error)` - Handle processing errors
- `resetProcessingState(processingType)` - Reset UI state

### Key Data Flow:
1. User clicks processing button → `sendProcess()` called
2. Request sent to `/api/{processingType}` endpoint
3. WebSocket provides real-time progress updates
4. On completion → overlay becomes available for map display

### API Endpoints:
- `POST /api/dtm` - Digital Terrain Model processing
- `POST /api/hillshade` - Hillshade processing
- `POST /api/dsm` - Digital Surface Model processing
- `POST /api/chm` - Canopy Height Model processing
- `POST /api/slope` - Slope analysis
- `POST /api/aspect` - Aspect analysis
- `POST /api/roughness` - Roughness analysis
- `POST /api/tri` - TRI processing
- `POST /api/tpi` - TPI processing
- `POST /api/color-relief` - Color relief processing

### Processing Status States:
- `idle` - No processing active
- `processing` - Currently processing
- `completed` - Processing finished successfully
- `error` - Processing failed
- `cancelled` - Processing cancelled by user

---

## 6. overlays.js - Map Overlay Management

**Purpose**: Manage image overlays on the Leaflet map
**Global Object**: `OverlayManager`

### Key Properties:
- `mapOverlays` - Object storing active overlay references

### Key Functions:

#### Overlay Management
- `addImageOverlay(processingType, imagePath, bounds, options)` - Add image overlay
- `removeOverlay(processingType)` - Remove specific overlay
- `clearAllOverlays()` - Remove all overlays
- `toggleOverlay(processingType)` - Toggle overlay visibility

#### Specialized Overlays
- `addTestOverlay(imageData, bounds)` - Add test overlay (black rectangle with red border)
- `addSatelliteImageOverlay(imageFile, bandType)` - Add Sentinel-2 satellite images

#### Data Fetching
- `fetchOverlayData(processingType)` - Get overlay data from server
- `handleAddToMapClick(processingType)` - Handle "Add to Map" button clicks

#### UI Updates
- `updateAddToMapButtonState(processingType, isAdded)` - Update button states
- `showOverlayNotification(message, type)` - Show overlay-related notifications

### Key Data Flow:
1. User clicks "Add to Map" → `handleAddToMapClick()` called
2. Overlay data fetched from `/api/overlay/{processingType}/{filename}`
3. Image bounds and data processed
4. Overlay added to map with appropriate opacity and styling

### API Endpoints:
- `GET /api/overlay/{processingType}/{filename}` - Fetch overlay data
- `GET /api/test-overlay/{filename}` - Fetch test overlay data

### Overlay Data Structure:
```javascript
{
  success: boolean,
  image_data: "base64_encoded_image",
  bounds: {
    north: number,
    south: number,
    east: number,
    west: number
  },
  processing_type: string,
  filename: string
}
```

---

## 7. websocket.js - Real-time Communication

**Purpose**: WebSocket communication for real-time progress updates
**Global Object**: `WebSocketManager`

### Key Properties:
- `socket` - WebSocket connection instance
- `reconnectAttempts` - Current reconnection attempt count
- `maxReconnectAttempts` - Maximum reconnection attempts (5)
- `reconnectDelay` - Base reconnection delay (1000ms)
- `currentDownload` - Track Sentinel-2 download progress

### Key Functions:

#### Connection Management
- `init()` - Initialize WebSocket connection
- `connect()` - Establish WebSocket connection
- `disconnect()` - Close WebSocket connection
- `getConnectionStatus()` - Get current connection status

#### Event Handling
- `setupEventHandlers()` - Set up WebSocket event listeners
- `handleMessage(data)` - Process incoming messages
- `sendMessage(data)` - Send message to server

#### Message Handlers
- `handleProgressUpdate(processingType, progress, message)` - Processing progress
- `handleStatusUpdate(processingType, status, message)` - Status changes
- `handleErrorMessage(processingType, message)` - Error notifications
- `handleCompletionMessage(processingType, message)` - Completion notifications
- `handleLogMessage(message, level)` - Log messages

#### Sentinel-2 Specific Handlers
- `handleDownloadStart(data)` - Sentinel-2 download started
- `handleDownloadInfo(data)` - Sentinel-2 download progress
- `handleDownloadComplete(data)` - Sentinel-2 download completed

#### Connection Recovery
- `attemptReconnect()` - Attempt to reconnect with exponential backoff
- `onConnectionEstablished()` - Handle successful connection
- `handleConnectionClose()` - Handle connection loss
- `handleConnectionError()` - Handle connection errors

### Message Types:
- `progress` - Processing progress updates
- `status` - Status change notifications
- `error` - Error messages
- `complete` - Completion notifications
- `log` - Log messages
- `download_start` - Sentinel-2 download started
- `download_info` - Sentinel-2 download progress
- `download_complete` - Sentinel-2 download completed

### WebSocket URL:
- `ws://localhost:8000/ws/progress` (development)
- `wss://domain.com/ws/progress` (production)

### Key Data Flow:
1. WebSocket connects on application start
2. Server sends real-time updates during processing
3. Progress bars and UI updated in real-time
4. Connection automatically recovers from failures

---

## 8. ui.js - User Interface Management

**Purpose**: UI interactions, modals, and interface state management
**Global Object**: `UIManager`

### Key Functions:

#### Initialization
- `init()` - Initialize UI components
- `initializeAccordions()` - Set up collapsible sections
- `initializeEventHandlers()` - Set up all event listeners
- `initializeTooltips()` - Set up help tooltips
- `initializeModals()` - Set up modal dialogs

#### Accordion Management
- `toggleAccordion(accordionType)` - Toggle section visibility
- Sections: 'laz' (LAZ Files), 'test' (Testing), 'processing' (Processing)

#### Test Functions
- `testCoordinateAcquisition()` - Test coordinate input functionality
- `testOverlay()` - Test overlay functionality with selected LAZ file
- `testSentinel2()` - Test Sentinel-2 satellite image download and display

#### Sentinel-2 Workflow
- `convertAndDisplaySentinel2(regionName)` - Convert TIF to PNG and display
- `displaySentinel2Images(files)` - Add images to satellite gallery
- `onSentinel2DownloadComplete(data)` - WebSocket callback for download completion

#### Progress Management
- `showProgress(message)` - Show progress modal
- `updateProgress(percentage, status, details)` - Update progress bar
- `hideProgress()` - Hide progress modal

#### UI State Management
- `updateProcessingButtons(hasSelectedFile)` - Enable/disable processing buttons
- `showFileInfo(fileInfo)` - Display selected file information
- `updateConnectionStatus(status)` - Update WebSocket connection indicator

#### Preferences
- `loadPreferences()` - Load saved UI preferences from localStorage
- `savePreferences()` - Save UI preferences to localStorage
- `updateTheme(theme)` - Switch between light/dark themes

#### Modals and Dialogs
- `showSettingsModal()` - Show application settings
- `showHelpModal()` - Show help documentation
- `showConfirmation(message, onConfirm, onCancel)` - Confirmation dialogs

### Key Event Handlers:
- File modal open/close/selection
- Processing button clicks
- Test button clicks
- Map coordinate updates
- Progress modal close/cancel

### HTML Element IDs:
- `#laz-accordion`, `#test-accordion`, `#processing-accordion` - Accordion headers
- `#laz-content`, `#test-content`, `#processing-content` - Accordion content
- `#file-modal` - File selection modal
- `#progress-modal` - Progress indicator modal
- `#satellite-gallery` - Satellite image gallery
- `#lat-input`, `#lng-input` - Coordinate input fields

### Key Data Flow:
1. User interactions trigger event handlers
2. UI state updated based on application state
3. Progress updates received via WebSocket
4. Preferences saved/loaded from localStorage

---

## Inter-Module Communication

### Data Flow Patterns:

1. **File Selection Flow**:
   ```
   UI → FileManager → Map (update marker) → Processing (enable buttons)
   ```

2. **Processing Flow**:
   ```
   UI → Processing → WebSocket (progress) → UI (progress bar) → Overlay (add to map)
   ```

3. **Sentinel-2 Flow**:
   ```
   UI → API (download) → WebSocket (progress) → UI (convert) → API (convert) → UI (display)
   ```

### Global Objects:
- `SHOtoZ` - Main application state
- `Utils` - Utility functions
- `MapManager` - Map operations
- `FileManager` - File operations
- `ProcessingManager` - Processing operations
- `OverlayManager` - Overlay management
- `WebSocketManager` - Real-time communication
- `UIManager` - UI management

### Error Handling:
- Each module has try-catch blocks for async operations
- Errors displayed via `Utils.showNotification()`
- WebSocket automatically reconnects on connection loss
- Processing failures gracefully reset UI state

### Configuration:
- API endpoints configurable via URL detection
- WebSocket URL automatically determined (ws/wss)
- Default coordinates for testing (Portland, Oregon)
- Progress update intervals and timeouts

---

## Development Notes

### Adding New Processing Types:
1. Add button and UI elements in HTML
2. Add processing function in `processing.js`
3. Add API endpoint handling in backend
4. Add overlay support in `overlays.js`
5. Update WebSocket message handling if needed

### Adding New Test Functions:
1. Add test button in HTML
2. Add test function in `ui.js`
3. Set up event handler in `initializeEventHandlers()`
4. Add any required API endpoints

### WebSocket Message Protocol:
- All messages are JSON with `type` field
- Progress messages include `progress` (0-100) and `message`
- Error messages include `error` field
- Completion messages include `success` and result data

### File Naming Conventions:
- Processing outputs: `{filename}_{processingType}.png`
- Overlay APIs: `/api/overlay/{processingType}/{filename}`
- Satellite images: `{region}_{timestamp}_{band}.png`

This documentation should help with understanding the codebase structure and making future modifications to the SHO to Z application.
