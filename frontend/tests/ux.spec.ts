import {
  test,
  expect,
  type Page,
  type APIRequestContext,
  type Locator,
} from "@playwright/test";

const shotLabels = [
  "Draft",
  "Asset Preparing",
  "Storyboard Prompt Ready",
  "Storyboard Ready",
  "Video Prompt Ready",
  "Video Generating",
  "Review",
  "Done",
];
const projectLabels = ["Draft", "Active", "Paused", "Completed", "Archived"];

async function seed(request: APIRequestContext) {
  const project = await (
    await request.post("/api/projects", {
      data: {
        name: `UX 验收 · 风淋室 ${Date.now()}`,
        description: "Phase 2.5 隔离测试项目",
      },
    })
  ).json();
  const script = await (
    await request.post(`/api/projects/${project.id}/scripts`, {
      data: { name: "工作流程剧本" },
    })
  ).json();
  const scenes = [];
  for (const name of [
    "入口场景",
    "长场景名称 · " + "设备走廊与入口空间约束".repeat(18),
  ]) {
    scenes.push(
      await (
        await request.post(`/api/projects/${project.id}/scenes`, {
          data: { name, script_id: script.id },
        })
      ).json(),
    );
  }
  const shots = [];
  for (const [shot_code, title, status] of [
    ["S13", "进入风淋室", "STORYBOARD_PROMPT_READY"],
    ["S14", "长镜头标题 · " + "进入走廊观察环境".repeat(20), "REVIEW"],
    ["S15", "离开风淋室", "DONE"],
  ]) {
    shots.push(
      await (
        await request.post(`/api/scenes/${scenes[0].id}/shots`, {
          data: {
            project_id: project.id,
            shot_code,
            title,
            status,
            duration_seconds: 8,
            creative_requirement: "固定机位，保持门与设备的位置一致。",
          },
        })
      ).json(),
    );
  }
  return { project, script, scenes, shots };
}

async function insideViewport(page: Page, locator: Locator) {
  const bounds = await locator.boundingBox();
  expect(bounds).not.toBeNull();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.y).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(
    page.viewportSize()!.width + 1,
  );
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(
    page.viewportSize()!.height + 1,
  );
}

async function checkOptions(page: Page, trigger: Locator, labels: string[]) {
  const triggerHeight = (await trigger.boundingBox())!.height;
  await trigger.click();
  await expect(page.getByRole("option")).toHaveText(labels);
  await insideViewport(page, page.getByRole("listbox"));
  const boxes = await page.getByRole("option").evaluateAll((options) =>
    options.map((option) => {
      const item = option.getBoundingClientRect();
      // Measure actual text independently of the indicator, including unchecked rows.
      const text = option.querySelector(".select-item-text")!;
      const rect = text.getBoundingClientRect();
      const indicator = option
        .querySelector(".select-indicator")
        ?.getBoundingClientRect();
      return {
        y: item.y,
        height: item.height,
        textTop: rect.top - item.top,
        textBottom: item.bottom - rect.bottom,
        textRight: item.right - rect.right,
        center: Math.abs(rect.y + rect.height / 2 - item.y - item.height / 2),
        indicatorGap: indicator ? indicator.left - rect.right : null,
        position: getComputedStyle(text).position,
      };
    }),
  );
  boxes.forEach((box, index) => {
    expect(box.height).toBe(triggerHeight);
    expect(box.position).toBe("static");
    expect(box.textTop).toBeGreaterThanOrEqual(0);
    expect(box.textBottom).toBeGreaterThanOrEqual(0);
    expect(box.center).toBeLessThanOrEqual(1);
    expect(box.textRight).toBeGreaterThanOrEqual(38);
    if (box.indicatorGap !== null)
      expect(box.indicatorGap).toBeGreaterThanOrEqual(8);
    if (index) expect(box.y - boxes[index - 1].y).toBe(box.height);
  });
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
}

async function checkForm(page: Page) {
  const dialog = page.getByRole("dialog");
  await insideViewport(page, dialog);
  const controls = await dialog
    .locator("input.ui-input, button.select-trigger, .dialog-footer button")
    .evaluateAll((nodes) =>
      nodes.map((node) => {
        const style = getComputedStyle(node);
        return {
          height: node.getBoundingClientRect().height,
          radius: style.borderRadius,
          font: style.fontSize,
          line: style.lineHeight,
        };
      }),
    );
  expect(controls.length).toBeGreaterThan(2);
  expect(new Set(controls.map((control) => JSON.stringify(control))).size).toBe(
    1,
  );
  expect(controls[0].height).toBe(36);
  await expect(dialog.locator(".dialog-footer button")).toHaveText([
    "取消",
    "保存",
  ]);
  const header = await dialog.locator(".dialog-header").boundingBox();
  const footer = await dialog.locator(".dialog-footer").boundingBox();
  await dialog.locator(".form-body").evaluate((element) => {
    element.scrollTop = element.scrollHeight;
  });
  expect((await dialog.locator(".dialog-header").boundingBox())!.y).toBe(
    header!.y,
  );
  expect((await dialog.locator(".dialog-footer").boundingBox())!.y).toBe(
    footer!.y,
  );
  await insideViewport(page, dialog.locator(".dialog-footer"));
  const widths = await dialog
    .locator(".form-field .ui-input")
    .evaluateAll((nodes) =>
      nodes.map((node) => node.getBoundingClientRect().width),
    );
  expect(new Set(widths).size).toBe(1);
}

for (const theme of ["dark", "light"]) {
  test(`select layout, labels, keyboard, form sizing and screenshots (${theme})`, async ({
    page,
    request,
  }) => {
    const { project, shots } = await seed(request);
    try {
      await page.addInitScript(
        (value) => localStorage.setItem("avw.ui.theme", value),
        theme,
      );
      await page.setViewportSize({ width: 1280, height: 800 });
      await page.goto(`/shots/${shots[0].id}`);
      await page.getByRole("button", { name: "编辑镜头" }).click();
      await checkForm(page);
      const trigger = page.getByRole("combobox", { name: "状态", exact: true });
      await expect(trigger).toHaveText("Storyboard Prompt Ready");
      await checkOptions(page, trigger, shotLabels);
      for (const label of shotLabels) {
        await trigger.click();
        const option = page.getByRole("option", { name: label, exact: true });
        await option.hover();
        await expect(option).toHaveAttribute("data-highlighted", "");
        await option.click();
        await expect(trigger).toHaveText(label);
      }
      await trigger.focus();
      await page.keyboard.press("ArrowDown");
      await page.keyboard.press("Home");
      await expect(
        page.getByRole("option", { name: "Draft", exact: true }),
      ).toBeFocused();
      await page.keyboard.press("ArrowDown");
      await expect(
        page.getByRole("option", { name: "Asset Preparing", exact: true }),
      ).toBeFocused();
      await page.keyboard.press("Enter");
      await expect(trigger).toHaveText("Asset Preparing");
      await trigger.click();
      await page
        .getByRole("option", { name: "Video Prompt Ready", exact: true })
        .click();
      await trigger.click();
      await expect(
        page.getByRole("option", { name: "Video Prompt Ready", exact: true }),
      ).toHaveAttribute("data-state", "checked");
      await page
        .getByRole("option", { name: "Storyboard Prompt Ready", exact: true })
        .hover();
      await page.screenshot({
        path: `test-results/phase-2.5-shot-select-${theme}.png`,
      });
      await page.keyboard.press("Escape");
      const outgoing = page.waitForRequest(
        (req) =>
          req.method() === "PATCH" &&
          req.url().endsWith(`/shots/${shots[0].id}`),
      );
      await page.getByRole("button", { name: "保存", exact: true }).click();
      expect((await outgoing).postDataJSON().status).toBe("VIDEO_PROMPT_READY");
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page.locator(".page-header .ui-badge")).toHaveText(
        "Video Prompt Ready",
      );

      await page.goto(`/projects/${project.id}`);
      await page.getByRole("button", { name: "编辑项目" }).click();
      await checkForm(page);
      await checkOptions(page, trigger, projectLabels);
      for (const label of projectLabels) {
        await trigger.click();
        await page.getByRole("option", { name: label, exact: true }).click();
        await expect(trigger).toHaveText(label);
      }
      await trigger.click();
      await page.getByRole("option", { name: "Active", exact: true }).click();
      await trigger.click();
      await page.getByRole("option", { name: "Paused", exact: true }).hover();
      await page.screenshot({
        path: `test-results/phase-2.5-project-select-${theme}.png`,
      });
      await page.keyboard.press("Escape");
      await page.getByRole("button", { name: "保存", exact: true }).click();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      expect(
        (await (await request.get(`/api/projects/${project.id}`)).json())
          .status,
      ).toBe("ACTIVE");
      await expect(page.locator(".page-header .ui-badge")).toHaveText("Active");

      for (const [route, button] of [
        ["script", "编辑剧本"],
        ["scenes", "编辑场景"],
        ["shots", "创建镜头"],
      ]) {
        await page.goto(`/projects/${project.id}/${route}`);
        await page
          .getByRole("button", { name: button, exact: true })
          .first()
          .click();
        await checkForm(page);
        if (route === "shots")
          await checkOptions(
            page,
            page.getByRole("combobox", { name: "所属场景" }),
            ["入口场景", "长场景名称 · " + "设备走廊与入口空间约束".repeat(18)],
          );
        await page.getByRole("button", { name: "取消", exact: true }).click();
        if (route === "scenes") {
          await page
            .getByRole("button", { name: "创建场景", exact: true })
            .click();
          await checkForm(page);
          await checkOptions(
            page,
            page.getByRole("combobox", { name: "所属剧本" }),
            ["工作流程剧本"],
          );
          await page.getByRole("button", { name: "取消", exact: true }).click();
        }
      }
      const filters = page.locator(".shot-filters .ui-input");
      expect(
        new Set(
          await filters.evaluateAll((nodes) =>
            nodes.map((node) => node.getBoundingClientRect().height),
          ),
        ).size,
      ).toBe(1);
      await checkOptions(
        page,
        page.getByRole("combobox", { name: "状态筛选" }),
        ["全部状态", ...shotLabels],
      );
      const sceneFilter = page.getByRole("combobox", { name: "场景筛选" });
      const longScene = "长场景名称 · " + "设备走廊与入口空间约束".repeat(18);
      await checkOptions(page, sceneFilter, [
        "全部场景",
        "入口场景",
        longScene,
      ]);
      await sceneFilter.click();
      await page.getByRole("option", { name: longScene, exact: true }).click();
      const valueBounds = (await sceneFilter
        .locator(".select-value")
        .boundingBox())!;
      const iconBounds = (await sceneFilter
        .locator(".select-icon")
        .boundingBox())!;
      expect(valueBounds.x + valueBounds.width).toBeLessThanOrEqual(
        iconBounds.x - 8,
      );
      await expect(
        page.getByRole("heading", { name: "没有匹配的镜头" }),
      ).toBeVisible();
      await page.getByRole("button", { name: "清除筛选", exact: true }).click();
      for (const width of [1366, 1024]) {
        await page.setViewportSize({ width, height: 720 });
        await page
          .getByRole("row", { name: /^S13 / })
          .getByRole("button", { name: "编辑镜头" })
          .click();
        await checkForm(page);
        await checkOptions(page, trigger, shotLabels);
        await page.getByRole("button", { name: "取消", exact: true }).click();
      }
      await page.setViewportSize({ width: 1280, height: 800 });
      await page.screenshot({
        path: `test-results/phase-2.5-shots-${theme}.png`,
      });
    } finally {
      await request.delete(`/api/projects/${project.id}`);
    }
  });

  test(`all existing pages, long rows, deletion, empty states and short navigation (${theme})`, async ({
    page,
    request,
  }) => {
    const { project, scenes } = await seed(request);
    try {
      await page.addInitScript(
        (value) => localStorage.setItem("avw.ui.theme", value),
        theme,
      );
      await page.setViewportSize({ width: 1280, height: 720 });
      for (const route of [
        "/projects",
        `/projects/${project.id}`,
        `/projects/${project.id}/script`,
        `/projects/${project.id}/scenes`,
        `/projects/${project.id}/shots`,
      ]) {
        await page.goto(route);
        await expect(page.getByLabel("加载中")).toHaveCount(0);
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        ).toBe(true);
        await expect(page.locator("main")).not.toContainText(
          /DRAFT|ACTIVE|STORYBOARD_PROMPT_READY|VIDEO_PROMPT_READY|REVIEW|DONE/,
        );
      }
      const rows = page.locator("tbody tr");
      await expect(rows).toHaveCount(3);
      const before = await rows.evaluateAll((nodes) =>
        nodes.map((node) => node.getBoundingClientRect().height),
      );
      expect(new Set(before).size).toBe(1);
      await rows.nth(1).hover();
      expect(
        await rows.evaluateAll((nodes) =>
          nodes.map((node) => node.getBoundingClientRect().height),
        ),
      ).toEqual(before);
      await expect(
        page.getByRole("button", { name: "上移 S13", exact: true }),
      ).toBeDisabled();
      await expect(
        page.getByRole("button", { name: "下移 S15", exact: true }),
      ).toBeDisabled();
      await page.getByRole("button", { name: "上移 S14", exact: true }).click();
      await expect(rows.first()).toHaveAttribute("aria-label", /^S14 /);
      await expect(rows).toHaveCount(3);
      await page.getByRole("searchbox", { name: "搜索镜头" }).fill("S13");
      await expect(rows).toHaveCount(1);
      await rows.getByRole("link", { name: "打开", exact: true }).click();
      await expect(
        page.getByRole("heading", { name: "S13 · 进入风淋室" }),
      ).toBeVisible();
      await page.getByRole("link", { name: "返回镜头列表" }).click();
      await expect(
        page.getByRole("searchbox", { name: "搜索镜头" }),
      ).toHaveValue("S13");
      await page.getByRole("searchbox", { name: "搜索镜头" }).fill("no-match");
      await expect(
        page.getByRole("heading", { name: "没有匹配的镜头" }),
      ).toBeVisible();
      await page.getByRole("button", { name: "清除筛选", exact: true }).click();
      await expect(rows).toHaveCount(3);
      await page
        .getByRole("navigation", { name: "项目导航" })
        .getByRole("link", { name: "Script", exact: true })
        .click();
      await page
        .getByRole("row", { name: /^S13 / })
        .getByRole("link", { name: "打开", exact: true })
        .click();
      await page.getByRole("link", { name: "返回剧本" }).click();
      await expect(page).toHaveURL(
        new RegExp(`/projects/${project.id}/script$`),
      );
      await page
        .getByRole("button", { name: "删除 入口场景", exact: true })
        .click();
      await expect(page.getByRole("dialog")).toContainText(
        "3 个镜头会一并删除",
      );
      await expect(
        page.getByRole("button", { name: "确认删除", exact: true }),
      ).toHaveClass(/button-destructive/);
      await page.screenshot({
        path: `test-results/phase-2.5-delete-${theme}.png`,
      });
      await page.getByRole("button", { name: "取消", exact: true }).click();
      await expect(
        page.getByRole("region", { name: "场景 入口场景", exact: true }),
      ).toBeVisible();
      const empty = page
        .getByRole("region", { name: `场景 ${scenes[1].name}`, exact: true })
        .locator(".empty-state");
      await expect(
        empty.getByRole("heading", { name: "还没有镜头" }),
      ).toBeVisible();
      await empty.getByRole("button", { name: "创建镜头" }).click();
      await expect(
        page.getByRole("dialog", { name: "创建镜头" }),
      ).toBeVisible();
      await page.getByRole("button", { name: "取消", exact: true }).click();
    } finally {
      await request.delete(`/api/projects/${project.id}`);
    }
  });
}

test("one save request, disabled controls, retained content on refresh error and readable retry", async ({
  page,
  request,
}) => {
  const { project, shots } = await seed(request);
  try {
    await page.goto(`/projects/${project.id}/shots`);
    await page
      .getByRole("row", { name: /^S13 / })
      .getByRole("button", { name: "编辑镜头" })
      .click();
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    let writes = 0;
    await page.route(`**/api/shots/${shots[0].id}`, async (route) => {
      if (route.request().method() !== "PATCH") return route.continue();
      writes++;
      await gate;
      await route.continue();
    });
    await page.route(`**/api/projects/${project.id}/shots`, (route) =>
      route.fulfill({
        status: 503,
        json: {
          code: "UNAVAILABLE",
          message: "镜头列表暂时无法刷新",
          details: {},
        },
      }),
    );
    await page
      .getByRole("button", { name: "保存", exact: true })
      .click({ clickCount: 2 });
    await expect(page.getByRole("button", { name: "保存中…" })).toBeDisabled();
    await expect(
      page.getByRole("combobox", { name: "状态", exact: true }),
    ).toBeDisabled();
    await expect(
      page.getByRole("button", { name: "取消", exact: true }),
    ).toBeDisabled();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toBeVisible();
    expect(writes).toBe(1);
    release();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page.getByRole("alert")).toContainText("镜头列表暂时无法刷新");
    await expect(page.locator("tbody tr")).toHaveCount(3);
    await page.unroute(`**/api/projects/${project.id}/shots`);
    await page.getByRole("button", { name: "重试", exact: true }).click();
    await expect(page.getByRole("alert")).toHaveCount(0);
    expect(writes).toBe(1);
  } finally {
    await request.delete(`/api/projects/${project.id}`);
  }
});
