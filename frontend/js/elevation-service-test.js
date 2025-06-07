/**
 * Simple integration test for ElevationService
 * Tests that the service is properly integrated and accessible
 */

function testElevationServiceIntegration() {
    console.log('=== ElevationService Integration Test ===');
    
    // Check if ElevationService is available
    if (typeof ElevationService === 'undefined') {
        console.error('❌ ElevationService is not available');
        return false;
    }
    
    console.log('✅ ElevationService is available');
    
    // Try to instantiate the service
    let elevationService;
    try {
        elevationService = new ElevationService();
        console.log('✅ ElevationService can be instantiated');
    } catch (error) {
        console.error('❌ Failed to instantiate ElevationService:', error);
        return false;
    }
    
    // Check if required methods exist on the instance
    const requiredMethods = [
        'downloadElevationData',
        'getBrazilianElevationData', 
        'getElevationStatus',
        'checkElevationAvailability',
        'downloadWithProgress',
        'getRecommendedSettings'
    ];
    
    let methodsOk = true;
    requiredMethods.forEach(method => {
        if (typeof elevationService[method] === 'function') {
            console.log(`✅ Method ${method} exists`);
        } else {
            console.error(`❌ Method ${method} is missing or not a function`);
            methodsOk = false;
        }
    });
    
    if (!methodsOk) {
        return false;
    }
    
    // Test coordinate validation
    try {
        const testRequest = {
            lat: -15.7801,
            lng: -47.9292,
            buffer_km: 1.0
        };
        
        // This should not throw an error for valid coordinates
        const result = elevationService.downloadElevationData(testRequest);
        if (result instanceof Promise) {
            console.log('✅ downloadElevationData returns a Promise as expected');
        } else {
            console.error('❌ downloadElevationData should return a Promise');
            return false;
        }
        
    } catch (error) {
        console.error('❌ Error testing downloadElevationData:', error);
        return false;
    }
    
    console.log('✅ ElevationService integration test passed');
    return true;
}

// Run test if in browser environment
if (typeof window !== 'undefined') {
    // Wait for DOM and services to be loaded
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            testElevationServiceIntegration();
        }, 1000);
    });
}

// Export for Node.js testing if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { testElevationServiceIntegration };
}
