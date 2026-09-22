import { test, expect } from "@playwright/test";

test("settings switches through the existing API and clears the old workspace view", async ({
  page,
}) => {
  // Mock this UI contract so parallel E2E workers never switch their shared server.
  let selected = "A:/isolated-workspace";
  let writes = 0;
  await page.route("**/api/settings/workspace", async (route) => {
    if (route.request().method() === "PUT") {
      writes++;
      selected = route.request().postDataJSON().workspace_root;
    }
    await route.fulfill({
      json: {
        workspace_root: selected,
        database_path: `${selected}/data/workspace.db`,
        initialized: true,
      },
    });
  });
  await page.goto("/settings");
  await expect(
    page.getByText("A:/isolated-workspace", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/不会搬迁当前文件/)).toBeVisible();
  await page.getByLabel("新工作空间的绝对路径").fill("B:/isolated-workspace");
  await page.getByRole("button", { name: "保存并切换工作空间" }).click();
  await expect(
    page.getByText("B:/isolated-workspace", { exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("新工作空间的绝对路径")).toHaveValue("");
  expect(writes).toBe(1);
});

test("workspace switch failure keeps the selection and permits retry", async ({
  page,
}) => {
  await page.route("**/api/settings/workspace", async (route) => {
    if (route.request().method() === "GET") return route.continue();
    await route.fulfill({
      status: 400,
      json: {
        code: "WORKSPACE_INVALID",
        message: "请选择有效的绝对路径。",
        details: {},
      },
    });
  });
  await page.goto("/settings");
  const original = await page
    .locator(".metadata-list .path-value")
    .first()
    .textContent();
  await page.getByLabel("新工作空间的绝对路径").fill("../invalid");
  await page.getByRole("button", { name: "保存并切换工作空间" }).click();
  await expect(
    page.getByText("请选择有效的绝对路径。", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "保存并切换工作空间" }),
  ).toBeEnabled();
  await expect(page.getByLabel("新工作空间的绝对路径")).toHaveValue(
    "../invalid",
  );
  await expect(page.locator(".metadata-list .path-value").first()).toHaveText(
    original!,
  );
});

test("real local services, honest empty states, and local SVG icons", async ({
  page,
}) => {
  const errors: string[] = [];
  const external: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    if (
      /^https?:/.test(request.url()) &&
      new URL(request.url()).hostname !== "127.0.0.1"
    )
      external.push(request.url());
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "工作空间概览" }),
  ).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("Local · 已连接");
  await expect(
    page.getByRole("link", { name: "Projects", exact: true }),
  ).toHaveAttribute("href", "/projects");
  await expect(page.getByRole("heading", { name: "最近项目" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText(
    /Phase|待开发|FastAPI v|每个好故事/,
  );
  expect(await page.locator("svg.lucide").count()).toBeGreaterThan(10);
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
});

test("dark is default; light persists and settings uses the same preference", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "切换到浅色模式" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Light", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Dark", exact: true }).click();
  expect(await page.evaluate(() => ({ ...localStorage }))).toEqual({
    "avw.ui.theme": "dark",
  });
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

test("blocked preference storage still allows in-memory theme changes", async ({
  page,
}) => {
  await page.addInitScript(() =>
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new DOMException("Blocked", "SecurityError");
      },
    }),
  );
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "切换到浅色模式" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("status")).toHaveText("Local · 已连接");
});

test("connection failures recover on retry", async ({ page }) => {
  await page.route("**/api/health", (route) =>
    route.fulfill({
      status: 503,
      json: { code: "UNAVAILABLE", message: "测试连接中断", details: {} },
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("测试连接中断");
  await page.unroute("**/api/health");
  await page.getByRole("button", { name: "重新检查连接" }).click();
  await expect(page.getByRole("status")).toHaveText("Local · 已连接");
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("workspace lookup failure is distinct from service health and can recover", async ({
  page,
}) => {
  await page.route("**/api/settings/workspace", (route) =>
    route.fulfill({
      status: 503,
      json: { code: "UNAVAILABLE", message: "路径暂不可用", details: {} },
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Local · 已连接");
  await expect(page.getByRole("alert")).toContainText("暂时无法读取路径");
  await page.unroute("**/api/settings/workspace");
  await page.getByRole("button", { name: "重试", exact: true }).click();
  await expect(page.locator(".storage-path code")).toContainText("workspace");
});

test("detail sheet reads real metadata, copies path, traps and restores keyboard focus", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const writes: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/") && request.method() !== "GET")
      writes.push(request.method());
  });
  await page.goto("/");
  const trigger = page.getByRole("button", {
    name: "工作空间信息",
    exact: true,
  });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "工作空间信息" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText("数据库文件", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "复制路径" }).click();
  await expect(
    page.getByText("工作空间路径已复制", { exact: true }),
  ).toBeVisible();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain(
    "workspace",
  );
  for (let index = 0; index < 5; index++) await page.keyboard.press("Tab");
  expect(
    await dialog.evaluate((element) =>
      element.contains(document.activeElement),
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
  expect(writes).toEqual([]);
});

test("unknown routes offer return navigation; UI fixture is development-only", async ({
  page,
}) => {
  await page.goto("/not-a-page");
  await expect(page.getByRole("heading", { name: "页面不存在" })).toBeVisible();
  await page.getByRole("link", { name: "返回概览" }).click();
  await expect(page.getByRole("status")).toHaveText("Local · 已连接");
  if (process.env.AVW_E2E_MODE !== "dev") {
    await page.goto("/__ui");
    await expect(
      page.getByRole("heading", { name: "页面不存在" }),
    ).toBeVisible();
  }
});

test("responsive workspace uses full width without horizontal overflow", async ({
  page,
}) => {
  await page.goto("/");
  for (const width of [1920, 1440, 1280, 1024, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      `viewport ${width}`,
    ).toBe(true);
    if (width === 1920)
      expect((await page.locator("main").boundingBox())!.width).toBeGreaterThan(
        1600,
      );
  }
});

test("theme text contrast meets WCAG AA and captures both palettes", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Local · 已连接");
  await expect(page.locator(".storage-path code")).toBeVisible();
  for (const theme of ["dark", "light"]) {
    if (theme === "light")
      await page.getByRole("button", { name: "切换到浅色模式" }).click();
    const ratios = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      const lum = (name: string) => {
        const raw = style.getPropertyValue(`--${name}`).trim().replace("#", "");
        const value =
          raw.length === 3
            ? raw
                .split("")
                .map((char) => char + char)
                .join("")
            : raw;
        const rgb = [0, 2, 4]
          .map((start) => parseInt(value.slice(start, start + 2), 16) / 255)
          .map((v) =>
            v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4,
          );
        return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
      };
      const pairs = [
        ["foreground", "background"],
        ["panel-foreground", "panel"],
        ["card-foreground", "card"],
        ["muted-foreground", "panel"],
        ["muted-foreground", "card"],
        ["sidebar-foreground", "sidebar"],
        ["accent-foreground", "accent"],
        ["success", "panel"],
        ["warning", "panel"],
        ["danger", "panel"],
      ];
      return pairs.map(([fg, bg]) => ({
        pair: `${fg}/${bg}`,
        ratio:
          (Math.max(lum(fg), lum(bg)) + 0.05) /
          (Math.min(lum(fg), lum(bg)) + 0.05),
      }));
    });
    for (const item of ratios)
      expect(item.ratio, `${theme}: ${item.pair}`).toBeGreaterThanOrEqual(4.5);
    await page.screenshot({
      path: `test-results/workspace-${theme}.png`,
      fullPage: true,
      animations: "disabled",
    });
  }
});

test("loading surfaces reserve space until the real workspace arrives", async ({
  page,
}) => {
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/settings/workspace", async (route) => {
    await gate;
    await route.continue();
  });
  await page.goto("/");
  await expect(page.locator(".storage-path .ui-skeleton")).toBeVisible();
  const before = await page.locator(".status-strip").boundingBox();
  release();
  await expect(page.locator(".storage-path code")).toBeVisible();
  expect((await page.locator(".status-strip").boundingBox())!.height).toBe(
    before!.height,
  );
});

if (process.env.AVW_E2E_MODE === "dev") {
  for (const theme of ["dark", "light"])
    test(`component foundation keyboard and feedback interactions (${theme})`, async ({
      page,
    }) => {
      await page.addInitScript(
        (value) => localStorage.setItem("avw.ui.theme", value),
        theme,
      );
      await page.goto("/__ui");
      await expect(
        page.getByRole("heading", { name: "UI Foundation 验收页" }),
      ).toBeVisible();
      await page
        .getByRole("textbox", { name: "名称", exact: true })
        .fill("组件验收");
      await page.getByRole("checkbox", { name: "选择样例" }).check();
      await page.getByRole("switch", { name: "启用样例" }).click();
      await expect(page.getByRole("switch")).toBeChecked();
      const select = page.getByRole("combobox", { name: "比例" });
      await select.focus();
      await page.keyboard.press("ArrowDown");
      await page.getByRole("option", { name: "1:1", exact: true }).click();
      await expect(select).toHaveText("1:1");
      await page.getByRole("tab", { name: "面板一" }).focus();
      await page.keyboard.press("ArrowRight");
      await expect(page.getByRole("tabpanel")).toHaveText("第二个面板内容");
      for (const [button, text] of [
        ["Success toast", "保存成功示例"],
        ["Error toast", "错误反馈示例"],
        ["Info toast", "提示信息示例"],
      ]) {
        await page.getByRole("button", { name: button, exact: true }).click();
        await expect(page.getByText(text, { exact: true })).toBeVisible();
      }
      const trigger = page.getByRole("button", {
        name: "打开 Dialog",
        exact: true,
      });
      await trigger.click();
      await expect(
        page.getByRole("textbox", { name: "对话框输入" }),
      ).toBeFocused();
      await page.keyboard.press("Escape");
      await expect(trigger).toBeFocused();
      await page
        .getByRole("button", { name: "打开 DetailSheet", exact: true })
        .click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.getByRole("button", { name: "完成预览" }).click();
      const media = page.getByRole("button", { name: /16:9 容器/ });
      await media.click();
      await expect(media).toHaveAttribute("aria-pressed", "true");
      await expect(page.locator(".media-preview").nth(0)).toHaveCSS(
        "aspect-ratio",
        "16 / 9",
      );
      await expect(page.locator(".media-preview").nth(1)).toHaveCSS(
        "aspect-ratio",
        "1 / 1",
      );
      await expect(page.locator(".media-preview").nth(2)).toHaveCSS(
        "aspect-ratio",
        "3 / 4",
      );
      await page.screenshot({
        path: `test-results/components-${theme}.png`,
        fullPage: true,
        animations: "disabled",
      });
    });
}
