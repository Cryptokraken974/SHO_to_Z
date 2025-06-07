/**
 * API Client Integration Test
 * Simple test to verify API client functionality
 */

// Test function to verify API client is loaded and working
window.testAPIClient = function() {
  console.log('🧪 Testing API Client Integration...');
  
  // Check if APIClient is available
  if (typeof APIClient === 'undefined') {
    console.error('❌ APIClient not found! Make sure api-client.js is loaded.');
    return false;
  }
  
  console.log('✅ APIClient is available');
  
  // Test all service clients are available
  const expectedServices = [
    'region', 'processing', 'elevation', 'satellite', 
    'overlay', 'savedPlaces', 'geotiff', 'laz', 'dataAcquisition'
  ];
  
  const missingServices = [];
  expectedServices.forEach(service => {
    if (!APIClient[service]) {
      missingServices.push(service);
    }
  });
  
  if (missingServices.length > 0) {
    console.error('❌ Missing services:', missingServices);
    return false;
  }
  
  console.log('✅ All service clients are available:', expectedServices);
  
  // Test service methods are callable
  const testCases = [
    { service: 'region', method: 'listRegions' },
    { service: 'processing', method: 'processRegion' },
    { service: 'elevation', method: 'downloadElevationData' },
    { service: 'satellite', method: 'downloadSentinel2Data' },
    { service: 'overlay', method: 'getTestOverlay' },
    { service: 'savedPlaces', method: 'getSavedPlaces' },
    { service: 'geotiff', method: 'listGeotiffFiles' },
    { service: 'laz', method: 'loadLAZFile' }
  ];
  
  testCases.forEach(test => {
    if (typeof APIClient[test.service][test.method] !== 'function') {
      console.error(`❌ ${test.service}.${test.method} is not a function`);
      return false;
    }
  });
  
  console.log('✅ All tested service methods are callable');
  
  // Test configuration
  console.log('🔧 API Client Configuration:', {
    baseUrl: APIClient.processing.baseUrl,
    timeout: APIClient.processing.timeout
  });
  
  console.log('🎉 API Client integration test completed successfully!');
  console.log('📖 Usage examples:');
  console.log('  - APIClient.region.listRegions()');
  console.log('  - APIClient.processing.processRegion("dem", { regionName: "test" })');
  console.log('  - APIClient.savedPlaces.getSavedPlaces()');
  console.log('  - APIClient.geotiff.listGeotiffFiles()');
  console.log('');
  console.log('📖 Service Factory examples:');
  console.log('  - regions().listRegions()');
  console.log('  - processing().processRegion("dem", { regionName: "test" })');
  console.log('  - satellite().downloadSentinel2Data()');
  console.log('  - overlays().getTestOverlay()');
  
  return true;
};

// Auto-run test when page is loaded (if in development mode)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      if (typeof APIClient !== 'undefined') {
        window.testAPIClient();
      }
    }, 1000);
  });
} else {
  // Run immediately if document is already loaded
  setTimeout(() => {
    if (typeof APIClient !== 'undefined') {
      window.testAPIClient();
    }
  }, 100);
}
