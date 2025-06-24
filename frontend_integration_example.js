
// Frontend Integration Example - Leaflet Map
// This demonstrates how to add overlays with correct scaling

const overlayData = await overlays().getRasterOverlayData(regionName, processingType);

if (overlayData.success) {
    // Create properly scaled image overlay
    const overlay = L.imageOverlay(
        `data:image/png;base64,${overlayData.image_data}`,
        [
            [overlayData.bounds.south, overlayData.bounds.west],  // SW corner
            [overlayData.bounds.north, overlayData.bounds.east]   // NE corner  
        ],
        {
            opacity: 0.7,
            interactive: false
        }
    ).addTo(map);
    
    // Overlay will display at correct 650m × 290m scale
    console.log(`Added ${processingType} overlay:`, 
                `${(overlayData.bounds.north - overlayData.bounds.south) * 111:.1f}km × `,
                `${(overlayData.bounds.east - overlayData.bounds.west) * 111:.1f}km`);
}
