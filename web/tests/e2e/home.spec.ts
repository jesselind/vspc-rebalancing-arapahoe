import { expect, test } from "@playwright/test";

test("loads homepage and precinct lookup", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Voter Service Polling Center (VSPC) Lookup" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Official county VSPC locations and hours" }).click();
  const countyVspcLink = page.getByRole("link", { name: /VSPC locations and hours/i });
  await expect(countyVspcLink).toHaveAttribute(
    "href",
    "https://www.arapahoeco.gov/your_county/arapahoevotes/voting_locations/voter_service_polling_centers.php",
  );
  await expect(countyVspcLink).toHaveAttribute("target", "_blank");
  await page.getByRole("textbox", { name: "Precinct number" }).fill("101");
  await page.getByRole("button", { name: "Find VSPC" }).click();
  await expect(page.getByText(/Distance to assigned VSPC:/)).toBeVisible();
  await expect(page.getByText("City of Sheridan Municipal Building").first()).toBeVisible();
  const mapsLink = page.getByRole("link", { name: /4101 S Federal Blvd/i });
  await expect(mapsLink).toHaveAttribute("href", /google\.com\/maps/);
});

test("precinct lookup clear resets field and results", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("textbox", { name: "Precinct number" }).fill("101");
  await page.getByRole("button", { name: "Find VSPC" }).click();
  await expect(page.getByText(/Distance to assigned VSPC:/)).toBeVisible();

  await page.getByRole("button", { name: "Clear precinct and start over" }).click();
  await expect(page.getByRole("textbox", { name: "Precinct number" })).toHaveValue("");
  await expect(page.getByText(/Distance to assigned VSPC:/)).not.toBeVisible();
});

test("precinct lookup submits on Enter key", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("textbox", { name: "Precinct number" }).fill("102");
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

test("links to county map PDF", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "County map (PDF)" })).toBeVisible();

  const openLink = page.getByRole("link", { name: "Open county map (PDF)" });
  await expect(openLink).toHaveAttribute("href", "/api/map-pdf");
  await expect(openLink).toHaveAttribute("target", "_blank");

  const downloadLink = page.getByRole("link", { name: "Download county map (PDF)" });
  await expect(downloadLink).toHaveAttribute("href", "/api/map-pdf?disposition=attachment");
  await expect(downloadLink).toHaveAttribute("download", "full-county-1_50000.pdf");
});

test("links to open-source repository in footer", async ({ page }) => {
  await page.goto("/");
  const footerRepoLink = page.getByRole("contentinfo").getByRole("link", { name: "View project on GitHub" });
  await expect(footerRepoLink).toHaveAttribute("href", "https://github.com/jesselind/vspc-rebalancing-arapahoe");
  await expect(footerRepoLink).toHaveAttribute("target", "_blank");
});
