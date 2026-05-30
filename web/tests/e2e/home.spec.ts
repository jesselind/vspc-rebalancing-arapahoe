import { expect, test } from "@playwright/test";

test("loads homepage and precinct lookup", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Voter Service Polling Center (VSPC) Lookup" }),
  ).toBeVisible();
  await page.getByLabel("Precinct number").fill("101");
  await page.getByRole("button", { name: "Find VSPC" }).click();
  await expect(page.getByText(/Distance to assigned VSPC:/)).toBeVisible();
  await expect(page.getByText("City of Sheridan Municipal Building").first()).toBeVisible();
  const mapsLink = page.getByRole("link", { name: /4101 S Federal Blvd/i });
  await expect(mapsLink).toHaveAttribute("href", /google\.com\/maps/);
});

test("precinct lookup submits on Enter key", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Precinct number").fill("102");
  await page.keyboard.press("Enter");
  await expect(page.getByText(/Distance to assigned VSPC:/)).toBeVisible();
});

test("renders csv tabs and download links", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Reports" })).toBeVisible();

  await page.getByRole("tab", { name: "VSPC Locations" }).click();
  const downloadLink = page.getByRole("link", { name: "Download VSPC Locations.csv" });
  await expect(downloadLink).toBeVisible();
  await expect(downloadLink).toHaveAttribute(
    "href",
    /\/api\/download\?file=VSPC%20Locations\.csv&disposition=attachment/,
  );
});

test("shows map viewer state", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "County map (PDF)" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Email support" })).toBeVisible();

  // PDF loading text is transient on fast machines, so accept either state:
  // still loading OR already loaded with viewer actions visible.
  const loadingText = page.getByText("Loading map PDF...");
  const openInNewTab = page.getByRole("link", { name: "Open in new tab" });

  await expect
    .poll(
      async () => {
        const loadingVisible = await loadingText.isVisible().catch(() => false);
        const loadedVisible = await openInNewTab.isVisible().catch(() => false);
        return loadingVisible || loadedVisible;
      },
      { timeout: 5000 },
    )
    .toBe(true);
});
