// Test script to check frontend state
// Run this in the browser console at http://localhost:3000

console.log('🔍 Frontend State Debug');
console.log('========================');

// Check FileManager state
console.log('📊 FileManager.getSelectedRegion():', window.FileManager ? FileManager.getSelectedRegion() : 'FileManager not loaded');
console.log('📊 FileManager.getProcessingRegion():', window.FileManager ? FileManager.getProcessingRegion() : 'FileManager not loaded');

// Check UI state
console.log('📊 Selected region display:', $('#selected-region-name').text());
console.log('📊 Global region selector:', $('#global-region-selector').val());

// Check if processing buttons are enabled
console.log('📊 DTM process button:', $('#process-dtm').length ? 'exists' : 'missing');

// Try to trigger DTM processing and see what happens
if (window.ProcessingManager) {
    console.log('📊 ProcessingManager available');
    
    // Check what would happen if we try to process DTM
    console.log('🧪 Testing DTM processing trigger...');
    
    const selectedRegion = FileManager.getSelectedRegion();
    const processingRegion = FileManager.getProcessingRegion();
    
    console.log('📊 Would use selectedRegion:', selectedRegion);
    console.log('📊 Would use processingRegion:', processingRegion);
    
    if (!selectedRegion) {
        console.log('❌ No region selected - this would cause the 400 error');
    } else {
        console.log('✅ Region is selected - should work');
    }
} else {
    console.log('❌ ProcessingManager not loaded');
}

// List available regions from current UI
console.log('📊 Available regions in file list:');
$('.file-item').each(function() {
    const regionName = $(this).data('region-name');
    const isSelected = $(this).hasClass('selected');
    console.log(`   - ${regionName} ${isSelected ? '(SELECTED)' : ''}`);
});
