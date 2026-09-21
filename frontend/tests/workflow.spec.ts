import { test, expect, type Page, type Locator } from "@playwright/test";

async function save(page: Page) {
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: "保存", exact: true }).click();
  await expect(dialog).toHaveCount(0);
}

async function createScene(page: Page, name: string) {
  await page
    .getByRole("button", { name: "创建场景", exact: true })
    .first()
    .click();
  await page.getByLabel("场景名称", { exact: false }).fill(name);
  await page
    .getByLabel("固定约束", { exact: true })
    .fill("入口在左侧，镜子固定在北墙");
  await page.getByLabel("负面约束", { exact: true }).fill("不改变门的位置");
  await save(page);
  return page.getByRole("region", { name: `场景 ${name}`, exact: true });
}

async function createShot(
  page: Page,
  region: Locator,
  code: string,
  title: string,
) {
  await region.getByRole("button", { name: "创建镜头" }).first().click();
  await page.getByLabel("镜头编号").fill(code);
  await page.getByLabel("镜头标题").fill(title);
  await page.getByLabel("时长（秒）").fill("6.5");
  await page.getByLabel("创作要求").fill("固定机位，人物进入画面");
  await save(page);
}

for (const theme of ["dark", "light"]) {
  test(`complete persistent project workflow (${theme})`, async ({
    page,
    request,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    const name = `E2E ${theme} ${Date.now()}`;
    let projectId = "";
    try {
      await page.goto("/projects");
      if (theme === "light")
        await page.getByRole("button", { name: "切换到浅色模式" }).click();
      await page
        .getByRole("button", { name: "创建项目", exact: true })
        .first()
        .click();
      await page.getByLabel("项目名称").fill(`  ${name}  `);
      await page
        .getByLabel("描述", { exact: true })
        .fill("真实浏览器验收项目，独立测试数据库。");
      await save(page);
      const card = page.getByRole("article", { name, exact: true });
      await card.getByRole("link", { name: "打开项目" }).click();
      await expect(
        page.getByRole("heading", { name, exact: true }),
      ).toBeVisible();
      projectId = new URL(page.url()).pathname.split("/")[2];
      await page.getByRole("button", { name: "编辑项目", exact: true }).click();
      await page.getByLabel("描述", { exact: true }).fill("已编辑的项目描述");
      await save(page);
      await page
        .getByRole("navigation", { name: "项目导航" })
        .getByRole("link", { name: "Script", exact: true })
        .click();
      await page
        .getByRole("button", { name: "创建剧本", exact: true })
        .first()
        .click();
      await page.getByLabel("剧本名称").fill("第一版剧本");
      await save(page);
      await page.getByRole("button", { name: "编辑剧本" }).click();
      await page
        .getByLabel("描述", { exact: true })
        .fill("场景与镜头的第一版结构");
      await save(page);
      let first = await createScene(page, "入口");
      await createShot(page, first, "S01", "走进入口");
      await createShot(page, first, "S02", "观察环境");
      const second = await createScene(page, "走廊");
      await createShot(page, second, "S03", "走向尽头");
      await first.getByRole("button", { name: "编辑场景" }).click();
      await expect(page.getByLabel("固定约束", { exact: true })).toHaveValue(
        "入口在左侧，镜子固定在北墙",
      );
      await page.getByLabel("场景名称").fill("风淋入口");
      await page.getByLabel("描述", { exact: true }).fill("人物进入前的准备区");
      await save(page);
      first = page.getByRole("region", { name: "场景 风淋入口", exact: true });
      await first
        .getByRole("row", { name: "S02 观察环境" })
        .getByRole("button", { name: "编辑镜头" })
        .click();
      await page.getByLabel("镜头标题").fill("观察入口");
      await page.getByRole("combobox", { name: "状态", exact: true }).click();
      await page.getByRole("option", { name: "Done", exact: true }).click();
      await save(page);
      await first.getByRole("button", { name: "上移 S02" }).click();
      await expect(first.locator("tbody tr").first()).toHaveAttribute(
        "aria-label",
        "S02 观察入口",
      );
      await first.getByRole("button", { name: "下移 S02" }).click();
      await expect(first.locator("tbody tr").first()).toHaveAttribute(
        "aria-label",
        "S01 走进入口",
      );
      await expect(
        first.getByRole("button", { name: "上移 S01" }),
      ).toBeDisabled();
      await page.reload();
      await expect(
        page.getByRole("region", { name: "场景 风淋入口", exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole("row", { name: "S02 观察入口" }),
      ).toBeVisible();
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.screenshot({
        path: `test-results/phase2-script-${theme}.png`,
        fullPage: true,
      });

      await page
        .getByRole("navigation", { name: "项目导航" })
        .getByRole("link", { name: "Shots", exact: true })
        .click();
      await expect(page.locator("tbody tr")).toHaveCount(3);
      await page.getByRole("combobox", { name: "场景筛选" }).click();
      await page.getByRole("option", { name: "风淋入口", exact: true }).click();
      await expect(page.locator("tbody tr")).toHaveCount(2);
      await page.getByRole("combobox", { name: "状态筛选" }).click();
      await page.getByRole("option", { name: "Done", exact: true }).click();
      await expect(page.locator("tbody tr")).toHaveCount(1);
      await page.getByRole("searchbox", { name: "搜索镜头" }).fill("missing");
      await expect(page.locator("tbody tr")).toHaveCount(0);
      await page.getByRole("searchbox", { name: "搜索镜头" }).fill("s02");
      await expect(page.locator("tbody tr")).toHaveCount(1);
      await page.getByRole("link", { name: "打开", exact: true }).click();
      await expect(
        page.getByRole("heading", { name: "S02 · 观察入口" }),
      ).toBeVisible();
      await expect(
        page.getByText("固定机位，人物进入画面", { exact: true }),
      ).toBeVisible();
      await page.getByRole("button", { name: "编辑镜头", exact: true }).click();
      await page.getByLabel("时长（秒）").fill("8");
      await save(page);
      await expect(page.getByText("8 秒", { exact: true })).toBeVisible();
      await page.reload();
      await expect(page.getByText("8 秒", { exact: true })).toBeVisible();
      await page.getByRole("link", { name: "返回镜头列表" }).click();
      await expect(page.locator("tbody tr")).toHaveCount(1);
      await page.getByRole("button", { name: "清除筛选", exact: true }).click();
      await expect(page.locator("tbody tr")).toHaveCount(3);
      await page.screenshot({
        path: `test-results/phase2-shots-${theme}.png`,
        fullPage: true,
      });
      for (const width of [1920, 1280, 1024, 390]) {
        await page.setViewportSize({ width, height: 1000 });
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
          ),
        ).toBe(true);
      }
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.getByRole("button", { name: "删除 S01", exact: true }).click();
      await page.getByRole("button", { name: "取消", exact: true }).click();
      await expect(page.locator("tbody tr")).toHaveCount(3);
      await page.getByRole("button", { name: "删除 S01", exact: true }).click();
      await page.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(page.locator("tbody tr")).toHaveCount(2);
      await page
        .getByRole("navigation", { name: "项目导航" })
        .getByRole("link", { name: "Scenes", exact: true })
        .click();
      await expect(
        page
          .getByRole("region", { name: "场景 风淋入口", exact: true })
          .getByText("1 shots", { exact: false }),
      ).toBeVisible();
      await page
        .getByRole("button", { name: "删除 风淋入口", exact: true })
        .click();
      await page.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(
        page.getByRole("region", { name: "场景 风淋入口", exact: true }),
      ).toHaveCount(0);
      await page
        .getByRole("navigation", { name: "项目导航" })
        .getByRole("link", { name: "Shots", exact: true })
        .click();
      await expect(page.locator("tbody tr")).toHaveCount(1);
      await page.reload();
      await expect(
        page.getByRole("row", { name: "S03 走向尽头" }),
      ).toBeVisible();
      const stats = await request.get(`/api/projects/${projectId}/stats`);
      expect(await stats.json()).toEqual({ scripts: 1, scenes: 1, shots: 1 });
      await page
        .getByRole("navigation", { name: "项目导航" })
        .getByRole("link", { name: "Script", exact: true })
        .click();
      await page
        .getByRole("button", { name: "删除 第一版剧本", exact: true })
        .click();
      await page.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(
        page.getByRole("heading", { name: "还没有剧本" }),
      ).toBeVisible();
      await page
        .getByRole("navigation", { name: "主导航" })
        .getByRole("link", { name: "Projects", exact: true })
        .click();
      await page
        .getByRole("article", { name, exact: true })
        .getByRole("button", { name: `删除 ${name}`, exact: true })
        .click();
      await page.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(
        page.getByRole("article", { name, exact: true }),
      ).toHaveCount(0);
      expect(errors).toEqual([]);
      expect(
        await page.evaluate(() =>
          Object.keys(localStorage).filter((key) => key !== "avw.ui.theme"),
        ),
      ).toEqual([]);
    } finally {
      if (projectId) await request.delete(`/api/projects/${projectId}`);
    }
  });
}

test("forms validate immediately, wait for save, and display readable API errors", async ({
  page,
  request,
}) => {
  await page.goto("/projects");
  await page
    .getByRole("button", { name: "创建项目", exact: true })
    .first()
    .click();
  await page.getByLabel("项目名称").fill(" ");
  await expect(page.getByText("此项不能为空", { exact: true })).toBeVisible();
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/projects", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    await gate;
    await route.fulfill({
      status: 409,
      json: {
        code: "TEST_CONFLICT",
        message: "测试：保存暂时不可用",
        details: {},
      },
    });
  });
  await page.getByLabel("项目名称").fill("Pending");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "保存", exact: true })
    .click();
  await expect(page.getByRole("button", { name: "保存中…" })).toBeDisabled();
  await expect(page.getByLabel("项目名称")).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "关闭", exact: true }),
  ).toBeDisabled();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeVisible();
  release();
  await expect(page.getByRole("alert")).toContainText("测试：保存暂时不可用");
  await page.unroute("**/api/projects");
  await page.getByRole("button", { name: "取消", exact: true }).click();

  const project = await (
    await request.post("/api/projects", {
      data: { name: `Conflict ${Date.now()}` },
    })
  ).json();
  try {
    const script = await (
      await request.post(`/api/projects/${project.id}/scripts`, {
        data: { name: "Script" },
      })
    ).json();
    const scene = await (
      await request.post(`/api/projects/${project.id}/scenes`, {
        data: { name: "Scene", script_id: script.id },
      })
    ).json();
    await request.post(`/api/scenes/${scene.id}/shots`, {
      data: { project_id: project.id, shot_code: "S01", title: "Existing" },
    });
    await page.goto(`/projects/${project.id}/shots`);
    await page.getByRole("button", { name: "创建镜头", exact: true }).click();
    await page.getByLabel("镜头编号").fill("S01");
    await page.getByLabel("镜头标题").fill("Duplicate");
    await page.getByLabel("时长（秒）").fill("-1");
    await expect(page.getByText("请输入大于或等于 0 的数值")).toBeVisible();
    await page.getByLabel("时长（秒）").fill("0");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "保存", exact: true })
      .click();
    await expect(page.getByRole("alert")).toContainText("镜头编号已存在");
  } finally {
    await request.delete(`/api/projects/${project.id}`);
  }
});

test("workflow loading, missing entity, and retry states", async ({ page }) => {
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/projects", async (route) => {
    await gate;
    await route.continue();
  });
  await page.goto("/projects");
  await expect(page.getByLabel("加载中")).toBeVisible();
  release();
  await expect(page.getByLabel("加载中")).toHaveCount(0);
  await page.goto("/projects/00000000-0000-0000-0000-000000000001");
  await expect(page.getByRole("alert")).toContainText("不存在或已删除");
  await expect(
    page.getByRole("button", { name: "重试", exact: true }),
  ).toBeVisible();
});

test("cascade deletion evicts a previously opened shot on browser Back", async ({
  page,
  request,
}) => {
  const project = await (
    await request.post("/api/projects", {
      data: { name: `Cache ${Date.now()}` },
    })
  ).json();
  try {
    const script = await (
      await request.post(`/api/projects/${project.id}/scripts`, {
        data: { name: "Script" },
      })
    ).json();
    const scene = await (
      await request.post(`/api/projects/${project.id}/scenes`, {
        data: { script_id: script.id, name: "Scene" },
      })
    ).json();
    const shot = await (
      await request.post(`/api/scenes/${scene.id}/shots`, {
        data: {
          project_id: project.id,
          shot_code: "S01",
          title: "Cached shot",
        },
      })
    ).json();
    await page.goto(`/shots/${shot.id}`);
    await expect(
      page.getByRole("heading", { name: "S01 · Cached shot" }),
    ).toBeVisible();
    await page.getByRole("link", { name: "返回镜头列表" }).click();
    await page
      .getByRole("navigation", { name: "项目导航" })
      .getByRole("link", { name: "Scenes", exact: true })
      .click();
    await page.getByRole("button", { name: "删除 Scene", exact: true }).click();
    await page.getByRole("button", { name: "确认删除", exact: true }).click();
    await expect(
      page.getByRole("region", { name: "场景 Scene", exact: true }),
    ).toHaveCount(0);
    await page.goBack();
    await page.goBack();
    await expect(page).toHaveURL(new RegExp(`/shots/${shot.id}$`));
    await expect(page.getByRole("alert")).toContainText("不存在或已删除");
    await expect(
      page.getByRole("heading", { name: "S01 · Cached shot" }),
    ).toHaveCount(0);
  } finally {
    await request.delete(`/api/projects/${project.id}`);
  }
});
