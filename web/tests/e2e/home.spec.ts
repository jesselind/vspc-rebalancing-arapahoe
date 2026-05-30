import { expect, test } from "@playwright/test";

test("loads homepage and precinct lookup", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Voter Service Polling Center (VSPC) Lookup" }),
  ).toBeVisible();
  const voterLookupLink = page.getByRole("link", {
    name: /Look it up with the county registered voter search/i,
  });
  await expect(voterLookupLink).toHaveAttribute("href", "https://arapahoevoterlookup.arapahoegov.com/");
  await expect(voterLookupLink).toHaveAttribute("target", "_blank");
  await page.getByLabel("Precinct number").fill("101");
  await page.getByRole("button", { name: "Find VSPC" }).click();
  await expect(page.getByText(/Distance to assigned VSPC:/)).toBeVisible();
  await expect(page.getByText("City of Sheridan Municipal Building").first()).toBeVisible();
  const mapsLink = page.getByRole("link", { name: /4101 S Federal Blvd/i });
  await expect(mapsLink).toHaveAttribute("href", /google\.com\/maps/);
});

test("precinct lookup clear resets field and results", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Precinct number").fill("101");
  await page.getByRole("button", { name: "Find VSPC" }).click();
  await expect(page.getByText(/Distance to assigned VSPC:/)).toBeVisible();

  await page.getByRole("button", { name: "Clear precinct and start over" }).click();
  await expect(page.getByLabel("Precinct number")).toHaveValue("");
  await expect(page.getByText(/Distance to assigned VSPC:/)).not.toBeVisible();
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

test("links to county map PDF on GitHub", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "County map (PDF)" })).toBeVisible();
  const mapLink = page.getByRole("link", { name: "Open county map (PDF)" });
  await expect(mapLink).toHaveAttribute("href", /raw\.githubusercontent\.com/);
  await expect(mapLink).toHaveAttribute("target", "_blank");
});
