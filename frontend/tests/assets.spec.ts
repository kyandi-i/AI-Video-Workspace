import { test, expect, type APIRequestContext } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const fixture = (name: string) =>
  resolve(
    process.env.AVW_E2E_RUN_DIRECTORY ?? "../.workspace/e2e",
    "fixtures",
    name,
  );
async function seedProject(request: APIRequestContext, name: string) {
  const project = await (
    await request.post("/api/projects", { data: { name } })
  ).json();
  const script = await (
    await request.post(`/api/projects/${project.id}/scripts`, {
      data: { name: "SPF script" },
    })
  ).json();
  const scene = await (
    await request.post(`/api/projects/${project.id}/scenes`, {
      data: { name: "入口", script_id: script.id },
    })
  ).json();
  const shot = await (
    await request.post(`/api/scenes/${scene.id}/shots`, {
      data: { project_id: project.id, shot_code: "S13", title: "进入风淋室" },
    })
  ).json();
  return { project, shot };
}

for (const theme of ["dark", "light"] as const) {
  test(`asset library import, grid/list, metadata, tags, bindings and persistence (${theme})`, async ({
    page,
    request,
  }) => {
    const prefix = `E2E-${theme}-${Date.now()}`;
    const { project, shot } = await seedProject(request, prefix);
    const tagName = `${prefix}-参考图-${"长标签".repeat(10)}`;
    const imported: string[] = [];
    page.on("response", async (response) => {
      if (
        response.url().includes("/api/assets/upload") &&
        response.status() === 201
      )
        imported.push((await response.json()).id);
    });
    try {
      await page.goto("/assets");
      if (theme === "light")
        await page.getByRole("button", { name: "切换到浅色模式" }).click();
      await page.setViewportSize({ width: 1280, height: 800 });
      const data = readFileSync(fixture("reference.png"));
      await page.getByLabel("选择资产文件").setInputFiles([
        { name: `${prefix}-人物.png`, mimeType: "image/png", buffer: data },
        {
          name: `${prefix}-损坏.png`,
          mimeType: "image/png",
          buffer: Buffer.from("not an image"),
        },
        {
          name: `${prefix}-${"长场景参考图".repeat(25)}.png`,
          mimeType: "image/png",
          buffer: readFileSync(fixture("scene.png")),
        },
      ]);
      await expect(page.locator(".import-results")).toContainText("文件损坏");
      await expect(page.locator(".import-results")).toContainText("已导入");
      await expect(
        page.getByRole("button", { name: "Import Asset", exact: true }),
      ).toBeEnabled();
      await page.getByRole("searchbox", { name: "搜索资产" }).fill(prefix);
      await expect(page.locator(".asset-grid .entity-card")).toHaveCount(2);
      await page.screenshot({
        animations: "disabled",
        path: `test-results/phase3-grid-${theme}.png`,
      });
      await page
        .getByRole("button", { name: "List View", exact: true })
        .click();
      await expect(page.locator(".asset-table tbody tr")).toHaveCount(2);
      await page.screenshot({
        animations: "disabled",
        path: `test-results/phase3-list-${theme}.png`,
      });
      await page
        .getByRole("button", { name: `${prefix}-人物.png`, exact: true })
        .click();
      const sheet = page.getByRole("dialog");
      await expect(sheet).toContainText("640 × 360");
      await expect(sheet).toContainText("image/png");
      await page.getByRole("button", { name: "编辑资产", exact: true }).click();
      const editor = page.getByRole("dialog", {
        name: "编辑资产",
        exact: true,
      });
      await editor
        .getByRole("textbox", { name: "名称", exact: true })
        .fill(`${prefix}-人物四视图`);
      await editor
        .getByRole("combobox", { name: "资产类型", exact: true })
        .click();
      await page
        .getByRole("option", { name: "Storyboard 6-Grid", exact: true })
        .click();
      await editor.getByRole("button", { name: "保存", exact: true }).click();
      await expect(editor).toHaveCount(0);
      await page
        .getByRole("textbox", { name: "新标签", exact: true })
        .fill(tagName);
      await page.getByRole("button", { name: "添加标签", exact: true }).click();
      await expect(
        page.getByRole("button", {
          name: `移除标签 ${tagName}`,
          exact: true,
        }),
      ).toBeVisible();
      await page
        .getByRole("combobox", { name: "绑定项目", exact: true })
        .click();
      await page.getByRole("option", { name: prefix, exact: true }).click();
      await page.getByRole("button", { name: "绑定项目", exact: true }).click();
      await expect(
        page.getByRole("button", { name: "解除项目绑定", exact: true }),
      ).toBeVisible();
      await page
        .getByRole("combobox", { name: "绑定镜头", exact: true })
        .click();
      await page
        .getByRole("option", { name: "S13 · 进入风淋室", exact: true })
        .click();
      await page.getByRole("button", { name: "绑定镜头", exact: true }).click();
      await expect(
        page.getByRole("button", { name: "解除镜头绑定", exact: true }),
      ).toBeVisible();
      expect(
        await page
          .locator(".detail-scroll .scroll-viewport")
          .evaluate((el) => el.scrollWidth <= el.clientWidth),
      ).toBe(true);
      await page.reload();
      await expect(
        sheet.getByRole("link", { name: prefix, exact: true }),
      ).toBeVisible();
      await expect(
        sheet.getByRole("link", { name: "S13 · 进入风淋室", exact: true }),
      ).toBeVisible();
      await page.screenshot({
        animations: "disabled",
        path: `test-results/phase3-detail-${theme}.png`,
      });
      await sheet
        .getByRole("link", { name: "S13 · 进入风淋室", exact: true })
        .scrollIntoViewIfNeeded();
      await page.screenshot({
        animations: "disabled",
        path: `test-results/phase3-bindings-${theme}.png`,
      });
      await page.setViewportSize({ width: 1024, height: 720 });
      expect(
        await page
          .locator(".detail-scroll .scroll-viewport")
          .evaluate((el) => el.scrollWidth <= el.clientWidth),
      ).toBe(true);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await page
        .getByRole("button", { name: `删除 ${prefix}-人物四视图`, exact: true })
        .click();
      await expect(page.getByRole("dialog").last()).toContainText(
        "请先解除绑定",
      );
      await page.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(page.getByRole("alert")).toContainText(
        "资产仍被项目或镜头引用",
      );
      await page.getByRole("button", { name: "取消", exact: true }).click();
      await page
        .getByRole("button", { name: "解除镜头绑定", exact: true })
        .click();
      await expect(
        page.getByRole("button", { name: "解除镜头绑定", exact: true }),
      ).toHaveCount(0);
      await page
        .getByRole("button", { name: "解除项目绑定", exact: true })
        .click();
      await expect(
        page.getByRole("button", { name: "解除项目绑定", exact: true }),
      ).toHaveCount(0);
      await page
        .getByRole("button", { name: `移除标签 ${tagName}`, exact: true })
        .click();
      await expect(
        page.getByRole("button", {
          name: `移除标签 ${tagName}`,
          exact: true,
        }),
      ).toHaveCount(0);
      await page.keyboard.press("Escape");
      await page
        .getByRole("combobox", { name: "资产类型筛选", exact: true })
        .click();
      await page
        .getByRole("option", { name: "Storyboard 6-Grid", exact: true })
        .click();
      await expect(page.locator(".asset-table tbody tr")).toHaveCount(1);
      await page
        .getByRole("combobox", { name: "标签筛选", exact: true })
        .click();
      await page.getByRole("option", { name: tagName, exact: true }).click();
      await expect(
        page.getByRole("heading", { name: "没有匹配的资产" }),
      ).toBeVisible();
      await page.getByRole("button", { name: "清除筛选", exact: true }).click();
      await expect(page.locator("body")).not.toContainText("STORYBOARD_6GRID");
    } finally {
      for (const id of imported) {
        await request.delete(`/api/projects/${project.id}/assets/${id}`);
        await request.delete(`/api/shots/${shot.id}/assets/${id}`);
        await request.delete(`/api/assets/${id}`);
      }
      await request.delete(`/api/projects/${project.id}`);
    }
  });
}

test("drop video, playback metadata and failed import recovery", async ({
  page,
  request,
}) => {
  const name = `E2E-video-${Date.now()}.mp4`;
  const imported: string[] = [];
  page.on("response", async (response) => {
    if (
      response.url().includes("/api/assets/upload") &&
      response.status() === 201
    )
      imported.push((await response.json()).id);
  });
  try {
    await page.goto("/assets");
    const dataTransfer = await page.evaluateHandle(
      ({ data, name }) => {
        const transfer = new DataTransfer();
        transfer.items.add(
          new File([new Uint8Array(data)], name, { type: "video/mp4" }),
        );
        return transfer;
      },
      { data: [...readFileSync(fixture("video.mp4"))], name },
    );
    await page
      .getByRole("region", { name: "导入资产区域" })
      .dispatchEvent("drop", { dataTransfer });
    await expect(page.locator(".import-results")).toContainText("已导入");
    await page.getByRole("searchbox", { name: "搜索资产" }).fill(name);
    await page.locator(".asset-grid .entity-hit-area").click();
    await expect(page.getByRole("dialog")).toContainText("160 × 90 · 1.0s");
    const video = page.locator("video");
    await expect
      .poll(() => video.evaluate((el: HTMLVideoElement) => el.readyState))
      .toBeGreaterThan(0);
    expect(await video.evaluate((el: HTMLVideoElement) => el.paused)).toBe(
      true,
    );
    await video.evaluate((el: HTMLVideoElement) => el.play());
    await expect
      .poll(() => video.evaluate((el: HTMLVideoElement) => el.currentTime))
      .toBeGreaterThan(0);
  } finally {
    for (const id of imported) await request.delete(`/api/assets/${id}`);
  }
});

test("asset loading, readable errors, retry and upload duplicate prevention", async ({
  page,
  request,
}) => {
  const name = `E2E-pending-${Date.now()}.png`;
  let releaseRead: () => void = () => {};
  const readGate = new Promise<void>((resolve) => {
    releaseRead = resolve;
  });
  await page.route("**/api/assets?**", async (route) => {
    await readGate;
    await route.fulfill({
      status: 503,
      json: { code: "UNAVAILABLE", message: "资产列表暂时不可用", details: {} },
    });
  });
  await page.goto(`/assets?q=${name}`);
  await expect(page.getByLabel("加载中", { exact: true })).toBeVisible();
  releaseRead();
  await expect(page.getByRole("alert")).toContainText("资产列表暂时不可用");
  await page.unroute("**/api/assets?**");
  await page.getByRole("button", { name: "重试", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "没有匹配的资产" }),
  ).toBeVisible();
  let releaseWrite: () => void = () => {};
  const writeGate = new Promise<void>((resolve) => {
    releaseWrite = resolve;
  });
  let writes = 0;
  let identifier = "";
  await page.route("**/api/assets/upload?**", async (route) => {
    writes++;
    await writeGate;
    const result = await route.fetch();
    identifier = (await result.json()).id;
    await route.fulfill({ response: result });
  });
  try {
    const data = readFileSync(fixture("reference.png"));
    await page
      .getByLabel("选择资产文件")
      .setInputFiles({ name, mimeType: "image/png", buffer: data });
    await expect(
      page.getByRole("button", { name: "导入中…", exact: true }),
    ).toBeDisabled();
    await expect(
      page.getByRole("combobox", { name: "导入分类", exact: true }),
    ).toBeDisabled();
    const transfer = await page.evaluateHandle(
      ({ data, name }) => {
        const value = new DataTransfer();
        value.items.add(new File([new Uint8Array(data)], name));
        return value;
      },
      { data: [...data], name },
    );
    await page
      .getByRole("region", { name: "导入资产区域" })
      .dispatchEvent("drop", { dataTransfer: transfer });
    expect(writes).toBe(1);
    releaseWrite();
    await expect(page.locator(".import-results")).toContainText("已导入");
    await expect(page.locator(".asset-grid .entity-card")).toHaveCount(1);
    expect(writes).toBe(1);
  } finally {
    releaseWrite();
    if (identifier) await request.delete(`/api/assets/${identifier}`);
  }
});
