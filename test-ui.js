const { chromium } = require('playwright');

(async () => {
  console.log('Starting Playwright test...');
  
  // Launch browser
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Set viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    console.log('Navigating to http://localhost:3000...');
    
    // Try to navigate with longer timeout
    const response = await page.goto('http://localhost:3000', { 
      waitUntil: 'networkidle',
      timeout: 60000 
    });
    
    console.log('Response status:', response.status());
    
    // Wait a bit for any redirects or dynamic content
    await page.waitForTimeout(5000);
    
    // Get the current URL (in case of redirect)
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);
    
    // Try to get page title
    const title = await page.title();
    console.log('Page title:', title);
    
    // Check for error messages
    const errorText = await page.textContent('body');
    if (errorText.includes('Module not found') || errorText.includes('Error')) {
      console.log('ERROR DETECTED:', errorText.substring(0, 500));
    }
    
    // Take screenshot
    await page.screenshot({ path: 'ui-screenshot.png', fullPage: true });
    console.log('Screenshot saved as ui-screenshot.png');
    
    // Try to find specific elements
    const hasWorkspace = await page.locator('text=ValueVerse').count() > 0;
    console.log('Has ValueVerse text:', hasWorkspace);
    
    const hasDualBrain = await page.locator('text=AI Assistant').count() > 0;
    console.log('Has AI Assistant:', hasDualBrain);
    
    const hasCanvas = await page.locator('text=Value Canvas').count() > 0;
    console.log('Has Value Canvas:', hasCanvas);
    
  } catch (error) {
    console.error('Error during test:', error);
  } finally {
    await browser.close();
    console.log('Browser closed');
  }
})();
