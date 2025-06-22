// Final NDVI Satellite Gallery Test
// Run this in browser console on the main page

console.log('🚀 FINAL NDVI SATELLITE GALLERY TEST');
console.log('====================================');

// Step 1: Check current state
console.log('1. Checking current state...');
console.log('   Satellite gallery available:', !!window.satelliteOverlayGallery);
console.log('   UIManager available:', !!window.UIManager);
console.log('   satellite() API available:', !!window.satellite);

// Step 2: Initialize satellite gallery if needed
if (!window.satelliteOverlayGallery) {
    console.log('2. Initializing satellite gallery...');
    try {
        window.satelliteOverlayGallery = new window.SatelliteOverlayGallery('satellite-gallery', {
            onAddToMap: (regionBand, bandType) => {
                console.log('Add to map called:', regionBand, bandType);
            }
        });
        console.log('✅ Satellite gallery initialized');
    } catch (error) {
        console.error('❌ Failed to initialize:', error);
    }
} else {
    console.log('2. Satellite gallery already initialized');
}

// Step 3: Test direct API call
console.log('3. Testing direct API call...');
fetch('/api/overlay/sentinel2/PRE_A05-01_NDVI')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('❌ API Error:', data.error);
        } else {
            console.log('✅ API Success');
            console.log('   Bounds available:', !!data.bounds);
            console.log('   Image data available:', !!data.image_data);
            console.log('   Image data size:', data.image_data ? data.image_data.length : 'none');
        }
    })
    .catch(error => console.error('❌ API Error:', error));

// Step 4: Test satellite gallery loading
console.log('4. Testing satellite gallery loading...');
if (window.satelliteOverlayGallery) {
    window.satelliteOverlayGallery.loadImages('PRE_A05-01')
        .then(() => {
            console.log('✅ Gallery loading completed');
            console.log('   Items loaded:', window.satelliteOverlayGallery.items.length);
            console.log('   Items:', window.satelliteOverlayGallery.items);
            
            if (window.satelliteOverlayGallery.items.length > 0) {
                console.log('🎉 SUCCESS: NDVI images are loading in satellite gallery!');
            } else {
                console.log('❌ PROBLEM: No items loaded');
            }
        })
        .catch(error => {
            console.error('❌ Gallery loading failed:', error);
        });
}

// Step 5: Test refresh via UIManager
console.log('5. Testing UIManager refresh...');
setTimeout(() => {
    if (window.UIManager && window.UIManager.displaySentinel2ImagesForRegion) {
        console.log('Calling UIManager.displaySentinel2ImagesForRegion...');
        window.UIManager.displaySentinel2ImagesForRegion('PRE_A05-01');
    } else {
        console.error('❌ UIManager method not available');
    }
}, 3000);

console.log('Test started - watch for results above...');
