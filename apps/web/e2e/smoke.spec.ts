import { test, expect } from '@playwright/test';

test('homepage smoke test', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Verify page title
  await expect(page).toHaveTitle(/Celebrity Look-Alike/i);
  
  // Verify main heading
  const heading = page.locator('h1');
  await expect(heading).toContainText(/Find Your Celebrity Twin/i);

  // Verify privacy badge presence
  const badge = page.locator('text=Zero Persistent Upload Storage');
  await expect(badge).toBeVisible();
});
