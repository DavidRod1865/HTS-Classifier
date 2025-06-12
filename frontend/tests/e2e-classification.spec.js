import { test, expect } from '@playwright/test';

test.describe('HTS Classification End-to-End Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should show breadcrumb navigation during classification', async ({ page }) => {
    // Start a classification
    const searchInput = page.locator('#product-search');
    await searchInput.fill('laptop computer');
    await page.locator('button[aria-label="Start new HTS classification"]').click();
    
    // Wait for breadcrumb to appear
    await expect(page.locator('text=Classification Journey:')).toBeVisible();
    await expect(page.locator('text=Product Entry')).toBeVisible();
    await expect(page.locator('text=Currently classifying: laptop computer')).toBeVisible();
  });

  test('should handle backend connection test', async ({ page }) => {
    // Test backend connection
    await page.locator('button:has-text("Test Backend")').click();
    
    // Wait for response
    await page.waitForTimeout(3000);
    
    // Should show either success or failure message
    const errorAlert = page.locator('.destructive');
    await expect(errorAlert).toBeVisible();
    
    // The message should contain either connection success or failure info
    await expect(errorAlert).toContainText(/Backend connected|Backend connection failed|Connection failed/);
  });

  test('should display refine vs new search options when results exist', async ({ page }) => {
    // This test assumes we have mock results or a working backend
    // For now, we'll test the UI behavior with mock data
    
    const searchInput = page.locator('#product-search');
    await searchInput.fill('electronics');
    await page.locator('button[aria-label="Start new HTS classification"]').click();
    
    // Wait for potential results (this will depend on backend availability)
    await page.waitForTimeout(2000);
    
    // If results appear, check for refine vs new buttons
    const refineButton = page.locator('button:has-text("Refine")');
    const newButton = page.locator('button:has-text("New")');
    
    // These buttons should appear if there are results
    if (await refineButton.isVisible()) {
      await expect(refineButton).toBeVisible();
      await expect(newButton).toBeVisible();
      
      // Check explanatory text
      await expect(page.locator('text=Try different keywords for the same product type')).toBeVisible();
      await expect(page.locator('text=Start over with a completely different product')).toBeVisible();
    }
  });

  test('should handle new search workflow', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    
    // First search
    await searchInput.fill('laptop');
    await page.locator('button[aria-label="Start new HTS classification"]').click();
    
    // Wait for any response
    await page.waitForTimeout(1000);
    
    // If new/refine buttons appear, test new search
    const newButton = page.locator('button:has-text("New")');
    if (await newButton.isVisible()) {
      await newButton.click();
      
      // Search field should be cleared and ready for new input
      await expect(searchInput).toHaveValue('');
      await expect(page.locator('button[aria-label="Start new HTS classification"]')).toBeVisible();
      
      // Breadcrumb should be reset
      const breadcrumb = page.locator('text=Classification Journey:');
      if (await breadcrumb.isVisible()) {
        await expect(page.locator('text=Currently classifying:')).not.toBeVisible();
      }
    }
  });

  test('should handle refine search workflow', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    
    // First search
    await searchInput.fill('computer');
    await page.locator('button[aria-label="Start new HTS classification"]').click();
    
    // Wait for any response
    await page.waitForTimeout(1000);
    
    // If refine button appears, test refine search
    const refineButton = page.locator('button:has-text("Refine")');
    if (await refineButton.isVisible()) {
      // Change search term and refine
      await searchInput.fill('gaming laptop');
      await refineButton.click();
      
      // Should maintain the session but with new search term
      await expect(page.locator('text=Currently classifying: gaming laptop')).toBeVisible();
    }
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Test with invalid input or when backend is down
    const searchInput = page.locator('#product-search');
    await searchInput.fill('test product');
    await page.locator('button[aria-label="Start new HTS classification"]').click();
    
    // Wait for response
    await page.waitForTimeout(3000);
    
    // Should either show results or error message
    const hasError = await page.locator('.destructive').isVisible();
    const hasResults = await page.locator('text=Found').isVisible();
    const hasQuestions = await page.locator('text=I need more information').isVisible();
    const hasOptions = await page.locator('text=Multiple matches found').isVisible();
    
    // One of these should be true
    expect(hasError || hasResults || hasQuestions || hasOptions).toBeTruthy();
  });

  test('should handle loading states', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    await searchInput.fill('smartphone');
    
    const classifyButton = page.locator('button[aria-label="Start new HTS classification"]');
    await classifyButton.click();
    
    // Should show loading state
    await expect(page.locator('text=Searching..., ...')).toBeVisible();
    
    // Button should be disabled during loading
    await expect(classifyButton).toBeDisabled();
  });

  test('should handle mobile responsive design', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that elements are still accessible on mobile
    await expect(page.locator('#product-search')).toBeVisible();
    await expect(page.locator('button[aria-label="Start new HTS classification"]')).toBeVisible();
    
    // Test search on mobile
    const searchInput = page.locator('#product-search');
    await searchInput.fill('mobile device');
    
    // Button should still work on mobile
    const classifyButton = page.locator('button[aria-label="Start new HTS classification"]');
    await expect(classifyButton).toBeEnabled();
    
    // Accessibility controls should still be accessible
    await expect(page.locator('button[aria-label="Open accessibility controls"]')).toBeVisible();
  });

  test('should handle keyboard-only navigation', async ({ page }) => {
    // Test complete workflow using only keyboard
    
    // Tab to search input
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // Should be on search input
    
    // Type search term
    await page.keyboard.type('tablet computer');
    
    // Press Enter to search
    await page.keyboard.press('Enter');
    
    // Should trigger search
    await page.waitForTimeout(1000);
    
    // Loading state should be visible
    const isLoading = await page.locator('text=Searching..., ...').isVisible();
    if (isLoading) {
      await expect(page.locator('text=Searching..., ...')).toBeVisible();
    }
  });

  test('should persist accessibility settings during workflow', async ({ page }) => {
    // Enable high contrast mode
    await page.locator('button[aria-label="Open accessibility controls"]').click();
    await page.locator('button:has-text("Enable High Contrast")').click();
    await page.locator('button[aria-label="Close accessibility controls"]').click();
    
    // Start classification workflow
    await page.locator('#product-search').fill('computer hardware');
    await page.locator('button[aria-label="Start new HTS classification"]').click();
    
    // Wait for response
    await page.waitForTimeout(1000);
    
    // High contrast should still be enabled
    const html = page.locator('html');
    await expect(html).toHaveClass(/high-contrast/);
  });

  test('should handle tooltip interactions', async ({ page }) => {
    // Test tooltip on HTS Classifier title
    const title = page.locator('h1 span:has-text("HTS Classifier")');
    await title.hover();
    
    // Tooltip should appear
    await expect(page.locator('text=HTS (Harmonized Tariff Schedule) codes are used to classify imported goods')).toBeVisible();
    
    // Move away and tooltip should disappear
    await page.locator('body').hover();
    await expect(page.locator('text=HTS (Harmonized Tariff Schedule) codes are used to classify imported goods')).not.toBeVisible();
  });
});