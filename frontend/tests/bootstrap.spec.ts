import { test, expect } from "@playwright/test";

test("invalid saved theme falls back to dark before application startup", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("avw.ui.theme", "invalid"),
  );
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("status")).toHaveText("Local · 已连接");
});

test("theme preference synchronizes across open workspace tabs", async ({
  page,
  context,
}) => {
  await page.goto("/");
  const second = await context.newPage();
  await second.goto("/settings");
  await page.getByRole("button", { name: "切换到浅色模式" }).click();
  await expect(second.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(
    second.getByRole("button", { name: "Light", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
});
