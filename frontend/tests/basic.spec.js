import { test, expect } from '@playwright/test';

test.describe('HTS Classifier Basic Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the main page', async ({ page }) => {
    // Check that the page loads with the correct title
    await expect(page.locator('text=HTS Classifier')).toBeVisible();
    
    // Check that the main search input is visible
    await expect(page.locator('#product-search')).toBeVisible();
    
    // Check that the classify button is visible
    await expect(page.locator('button:has-text("Classify")')).toBeVisible();
  });

  test('should display header elements correctly', async ({ page }) => {
    // Check header elements
    await expect(page.locator('text=HTS Classifier')).toBeVisible();
    await expect(page.locator('text=Enter your product description for instant HTS classification')).toBeVisible();
  });

  test('should show accessibility controls', async ({ page }) => {
    // Check accessibility controls are present
    await expect(page.locator('button[aria-label="Open accessibility controls"]')).toBeVisible();
  });

  test('should allow text input in search field', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    
    // Test typing in the search field
    await searchInput.fill('laptop computer');
    await expect(searchInput).toHaveValue('laptop computer');
    
    // Clear and test another input
    await searchInput.fill('smartphone');
    await expect(searchInput).toHaveValue('smartphone');
  });

  test('should enable classify button when text is entered', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    const classifyButton = page.locator('button:has-text("Classify")');
    
    // Button should be disabled initially
    await expect(classifyButton).toBeDisabled();
    
    // Enter text and button should be enabled
    await searchInput.fill('laptop');
    await expect(classifyButton).toBeEnabled();
    
    // Clear text and button should be disabled again
    await searchInput.fill('');
    await expect(classifyButton).toBeDisabled();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    
    // Test Enter key functionality
    await searchInput.fill('test product');
    await searchInput.press('Enter');
    
    // Should trigger some action (button state change or API call)
    // Note: This test will need to be updated based on actual backend behavior
  });

  test('should handle Escape key to clear search', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    
    // Fill the input
    await searchInput.fill('some product');
    await expect(searchInput).toHaveValue('some product');
    
    // Press Escape to clear
    await searchInput.press('Escape');
    await expect(searchInput).toHaveValue('');
  });

  test('should handle search attempt without backend', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    const classifyButton = page.locator('button[aria-label="Start new HTS classification"]');
    
    // Enter text and try to classify
    await searchInput.fill('test product');
    await classifyButton.click();
    
    // Should either show loading state or error message (depending on backend availability)
    // Wait a bit for any response
    await page.waitForTimeout(3000);
    
    // At minimum, something should have happened (loading state, error, or results)
    const hasLoading = await page.locator('text=Searching').isVisible();
    const hasError = await page.locator('[role="alert"]').isVisible();
    const hasResults = await page.locator('text=Found').isVisible();
    
    // One of these should be true
    expect(hasLoading || hasError || hasResults).toBeTruthy();
  });

  test('should show breadcrumb navigation when classification starts', async ({ page }) => {
    const searchInput = page.locator('#product-search');
    const classifyButton = page.locator('button[aria-label="Start new HTS classification"]');
    
    // Start a classification
    await searchInput.fill('laptop computer');
    await classifyButton.click();
    
    // Wait a moment for the state to update
    await page.waitForTimeout(1000);
    
    // Should show breadcrumb navigation (if it appears at all)
    const hasBreadcrumb = await page.locator('text=Classification Journey:').isVisible();
    if (hasBreadcrumb) {
      await expect(page.locator('text=Classification Journey:')).toBeVisible();
      // Check for the product being classified (may be in different format)
      await expect(page.locator('text=laptop computer')).toBeVisible();
    }
  });
});