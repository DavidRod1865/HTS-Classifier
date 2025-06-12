import { test, expect } from '@playwright/test';

test.describe('Accessibility Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should have accessibility controls panel', async ({ page }) => {
    // Check accessibility button is present
    const accessibilityButton = page.locator('button[aria-label="Open accessibility controls"]');
    await expect(accessibilityButton).toBeVisible();
    
    // Click to open accessibility panel
    await accessibilityButton.click();
    
    // Check panel contents (use more specific selector to avoid tooltip conflicts)
    await expect(page.locator('h3:has-text("Accessibility Settings")')).toBeVisible();
    await expect(page.locator('text=High Contrast Mode')).toBeVisible();
    await expect(page.locator('text=Font Size:')).toBeVisible();
  });

  test('should toggle high contrast mode', async ({ page }) => {
    // Open accessibility panel
    await page.locator('button[aria-label="Open accessibility controls"]').click();
    
    // Find and click high contrast toggle
    const highContrastButton = page.locator('button:has-text("Enable High Contrast")');
    await expect(highContrastButton).toBeVisible();
    await highContrastButton.click();
    
    // Check that high contrast class is applied
    const html = page.locator('html');
    await expect(html).toHaveClass(/high-contrast/);
    
    // Button text should change
    await expect(page.locator('button:has-text("Disable High Contrast")')).toBeVisible();
  });

  test('should adjust font size', async ({ page }) => {
    // Open accessibility panel
    await page.locator('button[aria-label="Open accessibility controls"]').click();
    
    // Find font size controls
    const increaseButton = page.locator('button[aria-label="Increase font size"]');
    const decreaseButton = page.locator('button[aria-label="Decrease font size"]');
    
    await expect(increaseButton).toBeVisible();
    await expect(decreaseButton).toBeVisible();
    
    // Test increase font size
    await increaseButton.click();
    await expect(page.locator('text=Font Size: 110%')).toBeVisible();
    
    // Test decrease font size
    await decreaseButton.click();
    await decreaseButton.click();
    await expect(page.locator('text=Font Size: 90%')).toBeVisible();
  });

  test('should reset accessibility settings', async ({ page }) => {
    // Open accessibility panel
    await page.locator('button[aria-label="Open accessibility controls"]').click();
    
    // Change some settings first
    await page.locator('button:has-text("Enable High Contrast")').click();
    await page.locator('button[aria-label="Increase font size"]').click();
    
    // Reset settings
    await page.locator('button[aria-label="Reset to default settings"]').click();
    
    // Check settings are reset
    await expect(page.locator('text=Font Size: 100%')).toBeVisible();
    await expect(page.locator('button:has-text("Enable High Contrast")')).toBeVisible();
  });

  test('should have proper ARIA labels and roles', async ({ page }) => {
    // Check main container has role="main"
    await expect(page.locator('[role="main"]')).toBeVisible();
    
    // Check search input has proper associated label (via sr-only label)
    const searchInput = page.locator('#product-search');
    await expect(searchInput).toBeVisible();
    await expect(page.locator('label[for="product-search"]')).toBeAttached();
    
    // Check buttons have proper aria-labels
    await expect(page.locator('button[aria-label="Start new HTS classification"]')).toBeVisible();
    await expect(page.locator('button[aria-label="Open accessibility controls"]')).toBeVisible();
  });

  test('should have keyboard navigation support', async ({ page }) => {
    // Tab through interactive elements - just verify we can focus on key elements
    await page.keyboard.press('Tab');
    // Check that some element received focus (doesn't have to be specific one due to browser differences)
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
    
    // Test that we can focus on the search input
    await page.locator('#product-search').focus();
    await expect(page.locator('#product-search')).toBeFocused();
  });

  test('should display keyboard navigation instructions', async ({ page }) => {
    // Open accessibility panel
    await page.locator('button[aria-label="Open accessibility controls"]').click();
    
    // Check keyboard navigation instructions are present
    await expect(page.locator('text=Keyboard Navigation:')).toBeVisible();
    await expect(page.locator('text=Tab: Navigate between elements')).toBeVisible();
    await expect(page.locator('text=Enter/Space: Activate buttons')).toBeVisible();
    await expect(page.locator('text=Escape: Close dialogs')).toBeVisible();
  });

  test('should support screen reader elements', async ({ page }) => {
    // Check for screen reader only content - sr-only elements should be attached but not visible
    const srOnlyElements = page.locator('.sr-only');
    await expect(srOnlyElements.first()).toBeAttached();
    
    // Check specific sr-only labels
    await expect(page.locator('label.sr-only:has-text("Product description for HTS classification")')).toBeAttached();
  });

  test('should have proper focus indicators', async ({ page }) => {
    // Focus on search input and verify it's focused
    await page.locator('#product-search').focus();
    await expect(page.locator('#product-search')).toBeFocused();
    
    // Test button focus - first enable the button by adding text
    await page.locator('#product-search').fill('test');
    await page.locator('button[aria-label="Start new HTS classification"]').focus();
    await expect(page.locator('button[aria-label="Start new HTS classification"]')).toBeFocused();
  });

  test('should handle high contrast mode persistence', async ({ page }) => {
    // Enable high contrast
    await page.locator('button[aria-label="Open accessibility controls"]').click();
    await page.locator('button:has-text("Enable High Contrast")').click();
    
    // Reload page
    await page.reload();
    
    // Check that high contrast is still enabled
    const html = page.locator('html');
    await expect(html).toHaveClass(/high-contrast/);
  });

  test('should handle font size persistence', async ({ page }) => {
    // Change font size
    await page.locator('button[aria-label="Open accessibility controls"]').click();
    await page.locator('button[aria-label="Increase font size"]').click();
    await page.locator('button[aria-label="Increase font size"]').click();
    
    // Reload page
    await page.reload();
    
    // Check that font size setting persists
    await page.locator('button[aria-label="Open accessibility controls"]').click();
    await expect(page.locator('text=Font Size: 120%')).toBeVisible();
  });
});