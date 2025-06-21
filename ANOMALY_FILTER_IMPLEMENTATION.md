# Anomaly Filter Implementation

## Overview
This document describes the implementation of a dynamic anomaly filtering system for the Results tab in the SHO_to_Z application. The system allows users to filter displayed anomalies by type based on the visual lexicon definitions.

## Architecture

### Backend Components

#### 1. Visual Lexicon API Endpoint (`app/endpoints/visual_lexicon.py`)
- **Base URL**: `/api/visual_lexicon`
- **Endpoints**:
  - `GET /anomaly_types` - Returns all available anomaly types from JSON files
  - `GET /anomaly_details/{anomaly_name}` - Returns detailed info for specific anomaly
  - `GET /all_anomaly_data` - Returns complete data for all anomaly types

#### 2. Visual Lexicon Data Source
- **Location**: `llm/prompts/prompt_modules/visual_lexicon/`
- **Files**: 
  - `causeway.json` - Defines "Causeway" anomaly type
  - `geoglyph.json` - Defines "Geoglyph" anomaly type  
  - `hillside_settlement.json` - Defines "Hillside Settlement" anomaly type
  - `settlement_platform.json` - Defines "Settlement Platform" anomaly type

### Frontend Components

#### 1. API Client (`frontend/js/api-client.js`)
- Added `VisualLexiconAPIClient` class
- Methods:
  - `getAnomalyTypes()` - Fetch available anomaly types
  - `getAnomalyDetails(anomalyName)` - Get details for specific anomaly
  - `getAllAnomalyData()` - Get all anomaly data
- Added to `APIClientFactory` with getter `visualLexicon()`

#### 2. Results Manager (`frontend/js/components/results.js`)
- **New Properties**:
  - `availableAnomalyTypes` - Array of available anomaly types
  - `activeAnomalyFilters` - Set of currently active filters
- **New Methods**:
  - `loadAnomalyTypes()` - Load anomaly types from API
  - `renderAnomalyFilter()` - Create filter UI with checkboxes
  - `selectAllAnomalyFilters()` - Select all filters
  - `clearAllAnomalyFilters()` - Clear all filters
  - `applyAnomalyFilters()` - Apply current filters to dashboard

#### 3. Anomalies Dashboard (`frontend/js/components/anomalies-dashboard.js`)
- **New Properties**:
  - `originalAnomaliesData` - Store unfiltered data
  - `activeFilters` - Set of active anomaly type filters
- **New Methods**:
  - `applyFilters()` - Filter anomalies by active types
  - `setFilters(filterSet)` - Set active filters and refresh
  - `addFilter(anomalyType)` - Add single filter
  - `removeFilter(anomalyType)` - Remove single filter
  - `clearAllFilters()` - Clear all filters

#### 4. UI Components (`frontend/modules/results-tab-content.html`)
- Added anomaly filter section to left panel:
  - Filter container with checkboxes for each anomaly type
  - "Select All" and "Clear All" buttons
  - Scrollable container for multiple types

#### 5. Styling (`frontend/css/results.css`)
- Added comprehensive CSS for filter interface:
  - Filter section background and borders
  - Checkbox styling with accent colors
  - Hover effects and transitions
  - Scrollbar styling
  - Error state styling

## Usage Flow

1. **Initialization**: 
   - Results tab loads and calls `loadAnomalyTypes()`
   - API fetches anomaly types from visual lexicon JSON files
   - Filter UI is rendered with checkboxes (all checked by default)

2. **User Interaction**:
   - User can check/uncheck specific anomaly types
   - "Select All" button checks all types
   - "Clear All" button unchecks all types
   - Changes trigger `applyAnomalyFilters()`

3. **Filtering**:
   - Active filters are passed to `AnomaliesDashboard.setFilters()`
   - Dashboard filters `originalAnomaliesData` based on classification.type
   - Display updates to show only matching anomalies
   - Summary count updates to reflect filtered results

## Data Flow

```
Visual Lexicon JSON Files
    ↓
Visual Lexicon API (/api/visual_lexicon/anomaly_types)
    ↓
Results Manager (loadAnomalyTypes)
    ↓
Filter UI Rendering (renderAnomalyFilter)
    ↓
User Filter Selection
    ↓
Anomalies Dashboard Filtering (setFilters)
    ↓
Updated Display
```

## Anomaly Type Matching

The filtering system matches anomalies by comparing the `classification.type` field in the anomaly data with the `anomaly_name` field from the visual lexicon JSON files.

**Example**:
- Visual lexicon file: `settlement_platform.json` → `"anomaly_name": "Settlement Platform"`
- Anomaly data: `{"classification": {"type": "Settlement Platform"}}`
- Match: ✅ This anomaly will be shown when "Settlement Platform" filter is active

## Configuration

### Adding New Anomaly Types
1. Create new JSON file in `llm/prompts/prompt_modules/visual_lexicon/`
2. Include `"anomaly_name"` field with the type name
3. System automatically detects and includes in filter options

### Filter Behavior
- **Default State**: All filters active (all anomalies shown)
- **Empty Selection**: No anomalies shown (intentional UX)
- **Auto-refresh**: Filters apply immediately when changed
- **Persistence**: Filters persist when switching between result logs

## Testing

### Available Test Data
The system includes test data with these anomaly types:
- Settlement Platform (2 instances)
- Causeway (1 instance)

### Manual Testing
1. Open Results tab
2. Select a result log to load dashboard
3. Use filter checkboxes to show/hide different anomaly types
4. Verify count updates and display changes

### API Testing
```bash
curl -X GET "http://localhost:8000/api/visual_lexicon/anomaly_types"
```

Expected response:
```json
{
  "success": true,
  "anomaly_types": ["Causeway", "Geoglyph", "Hillside Settlement", "Settlement Platform"],
  "total_count": 4
}
```

## Future Enhancements

1. **Advanced Filtering**: Add confidence score thresholds, bounding box size filters
2. **Visual Indicators**: Show filter status in anomaly cards
3. **Preset Filters**: Save/load common filter combinations
4. **Export Filtered Results**: Export filtered data as JSON/CSV
5. **Filter Analytics**: Track which filters are most commonly used
