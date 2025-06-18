# Modular System Guide for LAZ Terrain Processor

## Overview

The LAZ Terrain Processor frontend has been refactored into a modular architecture. The main application shell is `frontend/index-modular.html`. This file contains placeholder `div` elements where different UI components (modules) are dynamically loaded at runtime. This approach helps in organizing the codebase, improving maintainability, and allowing for more dynamic content management.

## Module Storage

HTML modules are stored in the following directories:

-   **General UI Components**: `frontend/modules/`
    -   This includes modules for the header, tab content sections (Map, GeoTiff Tools, Analysis, OpenAI Analysis, Results), and other non-modal UI parts.
-   **Modal Dialogs**: `frontend/modules/modals/`
    -   This directory houses the HTML for all modal dialogs used in the application (e.g., File Selection, Progress, LAZ File Browser).

## Module Loading Mechanism

### Core Function: `loadModule`

The primary mechanism for loading HTML modules is the `loadModule(modulePath, targetElementId)` function, located in `frontend/js/app_new.js`.
This asynchronous function:
1.  Fetches the HTML content from the specified `modulePath`. (Note: Paths are typically prefixed with `/static/` by the function, e.g., `/static/modules/header.html`).
2.  Injects the fetched HTML into the DOM element identified by `targetElementId`.
3.  After successfully injecting the HTML, it calls the global `window.initializeDynamicContent(targetElement, modulePath)` function to ensure any JavaScript needed for the new content is executed.

### JavaScript Initialization for Dynamic Content: `initializeDynamicContent`

A crucial part of the modular system is the `initializeDynamicContent(contextElement, contextName)` function, located in `frontend/js/ui.js` (and exposed globally as `window.initializeDynamicContent`).
-   **`contextElement`**: The DOM element into which the new HTML content was loaded.
-   **`contextName`**: A string (usually the module path) identifying the loaded module.

This function acts as a dispatcher. Based on the `contextName` (or by inspecting `contextElement`), it calls specific JavaScript initialization routines required to make the newly loaded module interactive. This includes:
-   Setting up event listeners for buttons, forms, etc., within the module.
-   Initializing UI components like maps, accordions, resizable panels, or galleries.
-   Calling `init()` methods of specific JavaScript classes or objects associated with the module.

## Loading Strategies

### 1. Loading Static Modules (on Initial Page Load)

Core UI components that are part of the main application layout are loaded when the DOM is ready.
-   **File**: `frontend/js/app_new.js` (typically within the `DOMContentLoaded` event listener or an equivalent initialization sequence).
-   **Placeholders in `index-modular.html`**:
    -   `header-placeholder`
    -   `global-region-selector-placeholder`
    -   `tab-nav-placeholder`
    -   `modals-placeholder` (though modals are usually loaded on demand)
-   **Example Calls**:
    ```javascript
    // In app_new.js or similar init phase
    await loadModule('modules/header.html', 'header-placeholder');
    await loadModule('modules/global-region-selector.html', 'global-region-selector-placeholder');
    await loadModule('modules/tab-navigation.html', 'tab-nav-placeholder');
    ```

### 2. Loading Tab Content Dynamically

-   **Handler**: The `UIManager.loadTabContent(tabName)` function in `frontend/js/ui.js`.
-   **Trigger**: Called when a tab button is clicked.
-   **Target Placeholder**: `main-content-placeholder` in `index-modular.html`.
-   **Module Path Construction**: Paths are typically like `modules/{tabName}-tab-content.html`. For example, clicking the "Map" tab loads `modules/map-tab-content.html`.
-   **Post-load**: `loadModule` calls `initializeDynamicContent`, which then runs specific initializations for the loaded tab content (e.g., initializing the map for the 'map' tab).

### 3. Loading Modals Dynamically

-   **Trigger**: Various user interactions (e.g., clicking "Select Region", "Load LAZ file", or an action that shows progress).
-   **Target Placeholder**: `modals-placeholder` in `index-modular.html`. This div is intended to temporarily hold the HTML for the currently active modal.
-   **Mechanism**:
    1.  The JavaScript event handler that triggers a modal (e.g., in `ui.js`, `geotiff-left-panel.js`, `openai-analysis.js`) first calls `await loadModule('modules/modals/{modal-name}.html', 'modals-placeholder');`.
    2.  Once the modal HTML is loaded into `modals-placeholder`, `initializeDynamicContent` is called. This function will then call specific setup/initialization logic for that modal (e.g., `geoTiffLeftPanelInstance.setupLazModalEvents()` for the LAZ file modal).
    3.  The modal is then made visible (e.g., using `$(modalId).fadeIn()`).
-   **Note**: Event handlers for buttons *inside* the modal (Confirm, Cancel, Close) are typically re-attached by the modal's specific setup function called from `initializeDynamicContent` or through delegated event listeners.

## Adding New Modules

### Adding a New Static UI Component (e.g., Footer)

1.  **Create HTML**: Create your module file (e.g., `frontend/modules/footer.html`).
2.  **Add Placeholder**: Add a corresponding `div` with an ID in `frontend/index-modular.html` (e.g., `<div id="footer-placeholder"></div>`).
3.  **Load Module**: In `frontend/js/app_new.js`, within the main application initialization sequence (e.g., after other static modules are loaded), add:
    ```javascript
    await loadModule('modules/footer.html', 'footer-placeholder');
    ```
4.  **Initialize JS (if needed)**: If the footer has interactive elements, add a section to `initializeDynamicContent` in `frontend/js/ui.js` to handle its specific JavaScript setup when `contextName` includes `footer.html`.

### Adding a New Tab

1.  **Button**: Add a new tab button to `frontend/modules/tab-navigation.html`. Ensure it has the correct `data-tab="{newTabName}"` attribute.
    ```html
    <button class="tab-btn px-6 py-3 text-[#ababab] ..." data-tab="my-new-tab">My New Tab</button>
    ```
2.  **Content HTML**: Create the content file `frontend/modules/my-new-tab-tab-content.html`.
3.  **JS Initialization**: In `frontend/js/ui.js`, update `initializeDynamicContent`. Add an `else if` condition for your new tab:
    ```javascript
    // In initializeDynamicContent
    // ...
    else if (contextName.includes('my-new-tab-tab-content.html')) {
        // Call functions to initialize your new tab's content, e.g.:
        // if (window.MyNewTabManager && typeof MyNewTabManager.init === 'function') {
        //     MyNewTabManager.init(contextElement);
        // }
        // this.initializeMyNewTabEventHandlers(contextElement); // If you have specific handlers
    }
    ```
    The `loadTabContent` function should automatically handle loading this new tab's HTML due to its generic path construction, as long as the `data-tab` attribute matches the file name convention.

### Adding a New Modal

1.  **HTML**: Create the modal's HTML file in `frontend/modules/modals/my-new-modal.html`. Ensure it has a unique ID (e.g., `id="my-new-modal"`).
2.  **Triggering JS**:
    *   Locate the JavaScript code that should open this modal.
    *   Modify it to first load the modal HTML:
        ```javascript
        // Example trigger
        async function showMyNewModal() {
            await loadModule('modules/modals/my-new-modal.html', 'modals-placeholder');
            // The initializeDynamicContent function will be called by loadModule.
            // It should handle making the modal visible and setting up its internal events.
            // If not, you might need to explicitly show it here after load:
            // $('#my-new-modal').fadeIn(); // Or equivalent
        }
        // Attach showMyNewModal to a button click or other event.
        ```
3.  **JS Initialization**: In `frontend/js/ui.js`, update `initializeDynamicContent`:
    ```javascript
    // In initializeDynamicContent, within the modal handling section:
    // ...
    if (contextName.includes('-modal.html')) {
        const modalId = contextElement.firstElementChild ? `#${contextElement.firstElementChild.id}` : null;
        if (modalId) {
            this.reinitializeModalEventHandlers(modalId, contextElement); // Generic close/bg click

            if (modalId === '#my-new-modal') {
                // Call specific setup for your new modal, e.g.:
                // if (typeof setupMyNewModal === 'function') setupMyNewModal(contextElement.firstElementChild);
            }
            $(modalId).filter(':hidden').fadeIn(); // Ensure it's visible
        }
    }
    ```
    Ensure any internal event listeners (confirm, cancel buttons within the modal) are correctly set up by its specific initialization function or use delegated event listeners.

## CSS Management

Currently, all CSS files from the `frontend/css/` directory are linked globally in the `<head>` of `frontend/index-modular.html`. This means all styles are loaded upfront.

**Potential for Future Improvement (Module-Specific CSS):**
While not implemented, a future enhancement could involve loading CSS files dynamically along with their respective HTML modules. This would be beneficial if certain CSS files are large and only used by specific, less frequently accessed modules. For example:
-   `chat.css` might only be needed when the "Analysis" or "OpenAI Analysis" tab (if they include chat features) is active.
-   `geotiff-tools.css` might only be necessary when the "GeoTiff Files Tools" tab is loaded.

This would require modifying the `loadModule` function to also handle `<link>` tag injection for CSS and ensuring that `initializeDynamicContent` or the module itself manages its styles. For now, the global loading approach is simpler and ensures all styles are available when needed.

This guide should help developers understand and work with the modular frontend architecture.
