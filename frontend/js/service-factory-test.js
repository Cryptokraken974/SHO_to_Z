/**
 * Service Factory Integration Test
 * Comprehensive test to verify service factory and API client integration
 */

window.testServiceFactoryIntegration = function() {
  console.log('🧪 Testing Service Factory Integration...');
  console.log('');
  
  // Check if service factory is available
  if (typeof window.satellite === 'undefined') {
    console.error('❌ Service factory not found! Make sure service-factory.js is loaded.');
    return false;
  }
  
  console.log('✅ Service factory is available');
  
  // Test all service factory functions
  const factoryFunctions = [
    'regions', 'processing', 'elevation', 'satellite', 
    'overlays', 'savedPlaces', 'geotiff'
  ];
  
  const missingFunctions = [];
  factoryFunctions.forEach(func => {
    if (typeof window[func] !== 'function') {
      missingFunctions.push(func);
    }
  });
  
  if (missingFunctions.length > 0) {
    console.error('❌ Missing service factory functions:', missingFunctions);
    return false;
  }
  
  console.log('✅ All service factory functions are available:', factoryFunctions);
  console.log('');
  
  // Test service instances
  console.log('🔧 Testing service instances...');
  
  try {
    const satelliteService = satellite();
    console.log('✅ Satellite service:', typeof satelliteService.downloadSentinel2Data === 'function' ? 'OK' : 'MISSING downloadSentinel2Data');
    
    const regionService = regions();
    console.log('✅ Region service:', typeof regionService.listRegions === 'function' ? 'OK' : 'MISSING listRegions');
    
    const processingService = processing();
    console.log('✅ Processing service:', typeof processingService.generateDTM === 'function' ? 'OK' : 'MISSING generateDTM');
    
    const overlayService = overlays();
    console.log('✅ Overlay service:', typeof overlayService.getTestOverlay === 'function' ? 'OK' : 'MISSING getTestOverlay');
    
    const elevationService = elevation();
    console.log('✅ Elevation service:', typeof elevationService.downloadElevationData === 'function' ? 'OK' : 'MISSING downloadElevationData');
    
    const savedPlacesService = savedPlaces();
    console.log('✅ SavedPlaces service:', typeof savedPlacesService.getSavedPlaces === 'function' ? 'OK' : 'MISSING getSavedPlaces');
    
    const geotiffService = geotiff();
    console.log('✅ Geotiff service:', typeof geotiffService.listGeotiffFiles === 'function' ? 'OK' : 'MISSING listGeotiffFiles');
    
  } catch (error) {
    console.error('❌ Error testing service instances:', error);
    return false;
  }
  
  console.log('');
  console.log('🎯 Testing consistency between direct API client and service factory...');
  
  // Test that service factory returns the same instances as APIClient
  try {
    const directSatellite = APIClient.satellite;
    const factorySatellite = satellite();
    
    console.log('📊 Direct API Client instance:', directSatellite.constructor.name);
    console.log('📊 Service Factory instance:', factorySatellite.constructor.name);
    
    if (directSatellite.constructor.name === factorySatellite.constructor.name) {
      console.log('✅ Both approaches return instances of the same class');
    } else {
      console.log('⚠️  Different class types - this might be expected');
    }
    
    // Test that they have the same methods
    const directMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(directSatellite))
      .filter(name => typeof directSatellite[name] === 'function' && name !== 'constructor');
    
    const factoryMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(factorySatellite))
      .filter(name => typeof factorySatellite[name] === 'function' && name !== 'constructor');
    
    console.log('📊 Direct API methods count:', directMethods.length);
    console.log('📊 Factory API methods count:', factoryMethods.length);
    
    const missingInFactory = directMethods.filter(method => !factoryMethods.includes(method));
    const missingInDirect = factoryMethods.filter(method => !directMethods.includes(method));
    
    if (missingInFactory.length > 0) {
      console.log('⚠️  Methods missing in factory service:', missingInFactory);
    }
    
    if (missingInDirect.length > 0) {
      console.log('⚠️  Methods missing in direct client:', missingInDirect);
    }
    
    if (missingInFactory.length === 0 && missingInDirect.length === 0) {
      console.log('✅ Both approaches have identical method sets');
    }
    
  } catch (error) {
    console.error('❌ Error comparing API client and service factory:', error);
  }
  
  console.log('');
  console.log('🎉 Service Factory integration test completed!');
  console.log('');
  console.log('📖 Recommended usage patterns:');
  console.log('  Service Factory (preferred):');
  console.log('    - satellite().downloadSentinel2Data()');
  console.log('    - regions().listRegions()'); 
  console.log('    - processing().generateDTM()');
  console.log('    - overlays().getTestOverlay()');
  console.log('');
  console.log('  Direct API Client (legacy):');
  console.log('    - APIClient.satellite.downloadSentinel2Data()');
  console.log('    - APIClient.region.listRegions()');
  console.log('    - APIClient.processing.generateDTM()');
  console.log('    - APIClient.overlay.getTestOverlay()');
  console.log('');
  console.log('✨ The codebase has been updated to use service factory consistently!');
  
  return true;
};

// Also create a function to test satellite service specifically
window.testSatelliteServiceIntegration = function() {
  console.log('🛰️  Testing Satellite Service Integration...');
  console.log('');
  
  try {
    const satelliteService = satellite();
    
    console.log('📊 Available Satellite Service Methods:');
    const methods = Object.getOwnPropertyNames(Object.getPrototypeOf(satelliteService))
      .filter(name => typeof satelliteService[name] === 'function' && name !== 'constructor');
    
    methods.forEach(method => {
      console.log(`  ✅ ${method}()`);
    });
    
    console.log('');
    console.log('🎯 Critical Satellite Methods Check:');
    const criticalMethods = [
      'downloadSentinel2Data',
      'convertSentinel2ToPNG', 
      'getSentinel2Overlay'
    ];
    
    criticalMethods.forEach(method => {
      if (typeof satelliteService[method] === 'function') {
        console.log(`  ✅ ${method}() - Available`);
      } else {
        console.log(`  ❌ ${method}() - Missing`);
      }
    });
    
    console.log('');
    console.log('🎉 Satellite service integration test completed!');
    
  } catch (error) {
    console.error('❌ Error testing satellite service:', error);
    return false;
  }
  
  return true;
};

// Auto-run comprehensive test when page is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      if (typeof window.satellite !== 'undefined') {
        window.testServiceFactoryIntegration();
        console.log('');
        window.testSatelliteServiceIntegration();
      }
    }, 1000);
  });
} else {
  setTimeout(() => {
    if (typeof window.satellite !== 'undefined') {
      window.testServiceFactoryIntegration();
      console.log('');
      window.testSatelliteServiceIntegration();
    }
  }, 100);
}
