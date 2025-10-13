const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });
  
  try {
    console.log('Loading workspace...');
    await page.goto('http://localhost:3000/workspace', { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    
    // Wait for any dynamic content
    await page.waitForTimeout(3000);
    
    // Take screenshot
    await page.screenshot({ path: 'workspace-ui.png', fullPage: true });
    console.log('Screenshot saved as workspace-ui.png');
    
    // Get page content for debugging
    const title = await page.title();
    console.log('Page title:', title);
    
    const hasValueVerse = await page.locator('text=ValueVerse').count();
    console.log('ValueVerse elements found:', hasValueVerse);
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  await browser.close();
})();
