# HTS Classifier Frontend Tests

This directory contains Playwright end-to-end tests for the HTS Classifier frontend application.

## Test Structure

### `basic.spec.js`
Tests core functionality:
- Page loading and basic elements
- Search input behavior
- Button states and interactions
- Keyboard navigation
- Error message handling
- Backend connection testing

### `accessibility.spec.js` 
Tests accessibility features:
- Accessibility controls panel
- High contrast mode toggle
- Font size adjustments
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Focus indicators
- Settings persistence

### `e2e-classification.spec.js`
Tests complete classification workflow:
- Breadcrumb navigation
- Classification journey states
- Refine vs New search distinction
- Error handling
- Loading states
- Mobile responsive design
- Keyboard-only navigation
- Tooltip interactions

## Running Tests

### Prerequisites
1. Make sure the backend server is running on `http://localhost:8000`
2. Install dependencies: `npm install`
3. Install Playwright browsers: `npx playwright install`

### Test Commands

```bash
# Run all tests
npm test

# Run tests with UI mode (interactive)
npm run test:ui

# Run tests in debug mode
npm run test:debug

# View test report
npm run test:report

# Run specific test file
npx playwright test tests/basic.spec.js

# Run tests in specific browser
npx playwright test --project=chromium

# Run tests on mobile
npx playwright test --project="Mobile Chrome"
```

### Test Configuration

Tests are configured in `playwright.config.js`:
- **Base URL**: `http://localhost:5173` (Vite dev server)
- **Browsers**: Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari
- **Auto-start**: Automatically starts the dev server before tests
- **Retries**: 2 retries on CI, 0 locally
- **Trace**: Captured on first retry for debugging

## Test Coverage

### ✅ Basic Functionality
- [x] Page loading and rendering
- [x] Search input validation
- [x] Button state management
- [x] Keyboard shortcuts (Enter, Escape)
- [x] Error message display
- [x] Backend connectivity testing

### ✅ Accessibility Features
- [x] Accessibility controls panel
- [x] High contrast mode
- [x] Font size adjustments
- [x] ARIA labels and semantic HTML
- [x] Keyboard navigation
- [x] Screen reader support
- [x] Focus management
- [x] Settings persistence

### ✅ End-to-End Workflows
- [x] Classification journey tracking
- [x] Breadcrumb navigation
- [x] Search refinement vs new search
- [x] Loading and error states
- [x] Mobile responsiveness
- [x] Tooltip interactions
- [x] Keyboard-only workflows

### ⚠️ Backend-Dependent Tests
Some tests require a working backend connection:
- Classification results display
- Clarifying questions workflow
- Multiple options selection
- Complete end-to-end classification

These tests will show skipped/pending states if the backend is not available.

## Writing New Tests

### Test Structure Example
```javascript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Test implementation
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

### Best Practices
1. **Use descriptive test names** that explain what is being tested
2. **Group related tests** using `test.describe()`
3. **Use `test.beforeEach()`** for common setup
4. **Wait for elements** using `await expect()` rather than timeouts
5. **Test accessibility** alongside functionality
6. **Handle async operations** properly with appropriate waits
7. **Test edge cases** and error conditions
8. **Use proper selectors** (prefer `data-testid` or ARIA attributes)

### Useful Selectors
- `#element-id` - ID selector
- `[data-testid="test-id"]` - Test ID attribute
- `[aria-label="button label"]` - ARIA label
- `text=visible text` - Text content
- `button:has-text("Button")` - Button with specific text
- `.class-name` - CSS class

### Common Assertions
```javascript
// Visibility
await expect(element).toBeVisible();
await expect(element).toBeHidden();

// Content
await expect(element).toContainText('text');
await expect(element).toHaveText('exact text');

// Attributes
await expect(element).toHaveAttribute('attr', 'value');
await expect(element).toHaveClass('class-name');

// Form elements
await expect(input).toHaveValue('value');
await expect(button).toBeEnabled();
await expect(button).toBeDisabled();
```

## Debugging Tests

### Debug Mode
```bash
npm run test:debug
```
Opens browser in debug mode with Playwright Inspector.

### Screenshots and Videos
Failed tests automatically capture:
- Screenshots
- Videos (in CI)
- Traces for debugging

### Console Logs
Add debugging to tests:
```javascript
console.log(await page.textContent('selector'));
await page.screenshot({ path: 'debug.png' });
```

## CI/CD Integration

Tests are configured for CI environments:
- Parallel execution disabled on CI
- 2 retry attempts for flaky tests
- HTML report generation
- Trace collection on failures

### GitHub Actions Example
```yaml
- name: Install dependencies
  run: npm ci
  
- name: Install Playwright
  run: npx playwright install --with-deps
  
- name: Run tests
  run: npm test
```

## Maintenance

### Regular Tasks
1. **Update selectors** when UI changes
2. **Add tests** for new features
3. **Review flaky tests** and improve stability
4. **Update browser versions** with Playwright updates
5. **Monitor test performance** and execution time

### Troubleshooting
- **Test timeouts**: Increase timeout or improve waiting strategies
- **Flaky tests**: Add proper waits and state checks
- **Selector issues**: Use more stable selectors
- **Browser issues**: Update Playwright browsers