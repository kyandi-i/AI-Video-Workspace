import { test, expect } from "@playwright/test";

test("connects to the real backend and renders the initialization workspace", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "创作工作台", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("连接正常");
  await expect(
    page.getByRole("button", { name: "项目 待开发" }),
  ).toBeDisabled();
  await page.getByRole("link", { name: "查看开发路线" }).click();
  await expect(page).toHaveURL(/#roadmap$/);
  expect(errors).toEqual([]);
});

test("shows connection failures and recovers on retry", async ({ page }) => {
  await page.route("**/api/health", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        code: "UNAVAILABLE",
        message: "测试连接中断",
        details: {},
      }),
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("测试连接中断");
  await page.unroute("**/api/health");
  await page.getByRole("button", { name: "重新检查连接" }).click();
  await expect(page.getByRole("status")).toHaveText("连接正常");
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("unknown route returns an actionable page", async ({ page }) => {
  await page.goto("/not-a-page");
  await expect(page.getByRole("heading", { name: "页面不存在" })).toBeVisible();
  await page.getByRole("link", { name: "返回概览" }).click();
  await expect(page.getByRole("status")).toHaveText("连接正常");
});

test("workspace fits the desktop and narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("连接正常");
  await page.screenshot({
    path: "test-results/workspace-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
