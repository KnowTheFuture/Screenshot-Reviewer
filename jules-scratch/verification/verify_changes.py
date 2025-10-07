import re
from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # 1. Navigate to the app
        page.goto("http://localhost:5173")

        # 2. Open settings and change theme
        page.get_by_role("button", name="⚙️ Settings").click()

        # Wait for settings modal to appear
        settings_modal = page.locator(".settings-surface")
        expect(settings_modal).to_be_visible()

        # Change theme to Matrix
        theme_selector = page.locator("#theme")
        theme_selector.select_option("matrix")
        expect(page.locator("body")).to_have_attribute("data-theme", "matrix")

        # 3. Change category color
        # Assuming there's at least one category to change the color of
        category_color_input = page.locator('label:has-text("General") input[type="color"]').first
        if category_color_input.is_visible():
            category_color_input.set_input_files([]) # This is a trick to set color
            page.evaluate("input => input.value = '#ff00ff'", category_color_input)
            page.evaluate("input => input.dispatchEvent(new Event('input', { bubbles: true }))", category_color_input)
            page.evaluate("input => input.dispatchEvent(new Event('change', { bubbles: true }))", category_color_input)

        # Close settings
        page.get_by_role("button", name="Close").click()

        # 4. Reclassify an image
        # Select the first screenshot
        first_screenshot = page.locator(".screenshot-card").first
        expect(first_screenshot).to_be_visible()
        first_screenshot.click()

        # Get the initial count of pending screenshots
        pending_button = page.get_by_role('button', name=re.compile(r'Pending \d+'))
        initial_pending_text = pending_button.inner_text()
        initial_pending_count_match = re.search(r'(\d+)', initial_pending_text)
        initial_pending_count = int(initial_pending_count_match.group(1)) if initial_pending_count_match else 0

        # Click reclassify button
        page.get_by_role("button", name="Mark as Pending").click()

        # Accept the confirmation dialog
        page.once("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name="Mark as Pending").click()

        # 5. Verify the reclassification
        # Check that the pending count has increased
        expect(pending_button).to_contain_text(str(initial_pending_count + 1))

        # Take screenshot
        page.screenshot(path="jules-scratch/verification/verification.png")

    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)