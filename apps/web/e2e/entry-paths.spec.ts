import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("welcome entry paths are accessible and lead to their respective flows", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "A calmer place to teach, practice, and remember progress." })).toBeVisible();
  await expect(page.getByRole("link", { name: /create a course/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /join a course/i })).toBeVisible();
  const results = await new AxeBuilder({ page }).include("main").analyze();
  expect(results.violations).toEqual([]);
  await page.getByRole("link", { name: /create a course/i }).click();
  await expect(page).toHaveURL(/\/instructor\/courses\/new$/);
  await expect(page.getByLabel("Course title")).toBeVisible();
  await page.goto("/");
  await page.getByRole("link", { name: /join a course/i }).click();
  await expect(page).toHaveURL(/\/student\/join$/);
  await expect(page.getByLabel("Enrollment code")).toBeVisible();
});

test("welcome layout remains within the viewport and theme control is keyboard-accessible", async ({ page }) => {
  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  }
  const toggle = page.getByRole("button", { name: /switch to (dark|light) theme/i });
  await expect(toggle).toBeVisible();
  const before = await page.locator("html").getAttribute("data-theme");
  await toggle.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("html")).not.toHaveAttribute("data-theme", before ?? "");
});

test("course setup keeps an instructor's local draft across a refresh", async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => {
    localStorage.removeItem("office-hours-course-draft");
    localStorage.removeItem("office-hours-course-draft:step");
  });
  await page.goto("/instructor/courses/new");
  await page.getByLabel("Course title").fill("Discrete Mathematics");
  await page.getByLabel(/course code/i).fill("MATH-250");
  await page.getByRole("button", { name: /continue/i }).click();
  await expect(page.getByRole("heading", { name: "Learning objectives" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Learning objectives" })).toBeVisible();
  await page.getByRole("button", { name: "Back" }).click();
  await expect(page.getByLabel("Course title")).toHaveValue("Discrete Mathematics");
  await expect(page.getByLabel(/course code/i)).toHaveValue("MATH-250");
});
