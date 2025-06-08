// Debug script to check region state during LAZ processing
console.log('=== DEBUG REGION STATE ===');

if (window.FileManager) {
  console.log('📊 FileManager.getSelectedRegion():', FileManager.getSelectedRegion());
  console.log('📊 FileManager.getProcessingRegion():', FileManager.getProcessingRegion());
  console.log('📊 FileManager.hasSelectedRegion():', FileManager.hasSelectedRegion());
  console.log('📊 FileManager.selectedRegion:', FileManager.selectedRegion);
  console.log('📊 FileManager.processingRegion:', FileManager.processingRegion);
} else {
  console.log('❌ FileManager not available');
}

// Test sendProcess call
if (window.ProcessingManager) {
  console.log('\n=== TESTING SENDPROCESS ===');
  const testSendProcess = async () => {
    try {
      console.log('🧪 Calling sendProcess("dtm") for testing...');
      const result = await ProcessingManager.sendProcess('dtm');
      console.log('✅ sendProcess result:', result);
    } catch (error) {
      console.error('❌ sendProcess error:', error);
    }
  };
  
  // Uncomment to test:
  // testSendProcess();
} else {
  console.log('❌ ProcessingManager not available');
}
