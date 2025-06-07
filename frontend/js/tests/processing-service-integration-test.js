/**
 * Test file for Processing Service Integration
 * 
 * Tests the integration between frontend ProcessingManager and backend ProcessingService
 * This file can be loaded in the browser console for testing.
 */

window.ProcessingServiceIntegrationTest = {
  
  /**
   * Test basic service method mapping
   */
  async testServiceMethodMapping() {
    console.log('🧪 Testing Processing Service Method Mapping...');
    
    // Check if all required methods exist
    const requiredMethods = [
      'listLazFiles',
      'loadLazFile', 
      'getLazInfo',
      'generateDTM',
      'generateDSM',
      'generateCHM',
      'generateHillshade',
      'generateSlope',
      'generateAspect',
      'generateColorRelief',
      'generateTPI',
      'generateRoughness',
      'generateAllRasters',
      'getProcessingStatus',
      'cancelProcessing',
      'getProcessingHistory',
      'deleteProcessedFiles',
      'getProcessingOverlay'
    ];
    
    console.log('✅ Required service methods:');
    const missingMethods = [];
    
    requiredMethods.forEach(method => {
      if (typeof APIClient.processing[method] === 'function') {
        console.log(`  ✓ ${method}`);
      } else {
        console.log(`  ❌ ${method} - MISSING`);
        missingMethods.push(method);
      }
    });
    
    if (missingMethods.length === 0) {
      console.log('🎉 All service methods are available!');
      return true;
    } else {
      console.log(`❌ Missing ${missingMethods.length} methods:`, missingMethods);
      return false;
    }
  },

  /**
   * Test ProcessingManager service integration
   */
  async testProcessingManagerIntegration() {
    console.log('🧪 Testing ProcessingManager Service Integration...');
    
    // Check if ProcessingManager has the new service methods
    const managerMethods = [
      'listLazFiles',
      'loadLazFile',
      'getLazInfo',
      'generateAllRastersForRegion',
      'getProcessingStatusForRegion',
      'getProcessingHistory',
      'deleteProcessedFiles'
    ];
    
    console.log('✅ ProcessingManager service methods:');
    const missingManagerMethods = [];
    
    managerMethods.forEach(method => {
      if (typeof ProcessingManager[method] === 'function') {
        console.log(`  ✓ ${method}`);
      } else {
        console.log(`  ❌ ${method} - MISSING`);
        missingManagerMethods.push(method);
      }
    });
    
    if (missingManagerMethods.length === 0) {
      console.log('🎉 All ProcessingManager service methods are available!');
      return true;
    } else {
      console.log(`❌ Missing ${missingManagerMethods.length} manager methods:`, missingManagerMethods);
      return false;
    }
  },

  /**
   * Test service factory integration
   */
  async testServiceFactoryIntegration() {
    console.log('🧪 Testing Service Factory Integration...');
    
    // Test service factory
    if (typeof window.processing === 'function') {
      const processingService = window.processing();
      console.log('✅ Service factory processing() method available');
      
      if (processingService && typeof processingService.generateDTM === 'function') {
        console.log('✅ Service factory returns valid processing service');
        return true;
      } else {
        console.log('❌ Service factory returns invalid processing service');
        return false;
      }
    } else {
      console.log('❌ Service factory processing() method not available');
      return false;
    }
  },

  /**
   * Test the sendProcess method service routing
   */
  async testSendProcessServiceRouting() {
    console.log('🧪 Testing sendProcess Service Routing...');
    
    // Mock the region selection for testing
    const originalGetSelectedRegion = FileManager.getSelectedRegion;
    const originalGetProcessingRegion = FileManager.getProcessingRegion;
    
    FileManager.getSelectedRegion = () => 'test-region';
    FileManager.getProcessingRegion = () => 'test-region';
    
    try {
      // Mock the API client to capture calls
      const originalGenerateDTM = APIClient.processing.generateDTM;
      let capturedCall = null;
      
      APIClient.processing.generateDTM = async (options) => {
        capturedCall = { method: 'generateDTM', options };
        return { success: true };
      };
      
      // Test DTM processing
      await ProcessingManager.sendProcess('dtm', { test: 'value' });
      
      if (capturedCall && capturedCall.method === 'generateDTM') {
        console.log('✅ sendProcess correctly routes to generateDTM service method');
        console.log('✅ Options passed correctly:', capturedCall.options);
        
        // Restore original method
        APIClient.processing.generateDTM = originalGenerateDTM;
        return true;
      } else {
        console.log('❌ sendProcess did not route to generateDTM service method');
        APIClient.processing.generateDTM = originalGenerateDTM;
        return false;
      }
      
    } catch (error) {
      console.log('❌ Error testing sendProcess routing:', error);
      return false;
    } finally {
      // Restore original methods
      FileManager.getSelectedRegion = originalGetSelectedRegion;
      FileManager.getProcessingRegion = originalGetProcessingRegion;
    }
  },

  /**
   * Run all tests
   */
  async runAllTests() {
    console.log('🚀 Starting Processing Service Integration Tests...');
    console.log('================================================');
    
    const results = {
      serviceMethodMapping: await this.testServiceMethodMapping(),
      processingManagerIntegration: await this.testProcessingManagerIntegration(),
      serviceFactoryIntegration: await this.testServiceFactoryIntegration(),
      sendProcessServiceRouting: await this.testSendProcessServiceRouting()
    };
    
    console.log('================================================');
    console.log('📊 Test Results Summary:');
    
    let passedTests = 0;
    let totalTests = 0;
    
    Object.keys(results).forEach(testName => {
      totalTests++;
      if (results[testName]) {
        passedTests++;
        console.log(`✅ ${testName}: PASSED`);
      } else {
        console.log(`❌ ${testName}: FAILED`);
      }
    });
    
    console.log(`\n🎯 Overall: ${passedTests}/${totalTests} tests passed`);
    
    if (passedTests === totalTests) {
      console.log('🎉 All tests passed! Service integration is working correctly.');
    } else {
      console.log('⚠️ Some tests failed. Please check the integration.');
    }
    
    return results;
  }
};

// Auto-run tests if this file is loaded directly
if (typeof window !== 'undefined' && window.location && window.location.search.includes('run-processing-tests')) {
  window.addEventListener('load', () => {
    setTimeout(() => {
      window.ProcessingServiceIntegrationTest.runAllTests();
    }, 1000);
  });
}

console.log('📋 Processing Service Integration Test loaded. Run window.ProcessingServiceIntegrationTest.runAllTests() to test the integration.');
