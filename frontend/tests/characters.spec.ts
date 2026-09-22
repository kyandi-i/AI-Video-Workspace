import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
async function seed(request: APIRequestContext, name: string) {
  const project = await (
    await request.post("/api/projects", { data: { name } })
  ).json();
  const script = await (
    await request.post(`/api/projects/${project.id}/scripts`, {
      data: { name: "培训" },
    })
  ).json();
  const scene = await (
    await request.post(`/api/projects/${project.id}/scenes`, {
      data: { name: "风淋", script_id: script.id },
    })
  ).json();
  const shot = await (
    await request.post(`/api/scenes/${scene.id}/shots`, {
      data: { project_id: project.id, shot_code: "S13", title: "风淋" },
    })
  ).json();
  const asset = await (
    await request.post(
      `/api/assets/upload?filename=${encodeURIComponent(name + ".png")}`,
      {
        data: readFileSync(
          resolve(
            process.env.AVW_E2E_RUN_DIRECTORY ?? "../.workspace/e2e",
            "fixtures/reference.png",
          ),
        ),
        headers: { "Content-Type": "application/octet-stream" },
      },
    )
  ).json();
  return { project, shot, asset };
}
async function form(page: Page, title: string, name: string) {
  await page.getByRole("button", { name: title, exact: true }).click();
  const dialog = page.getByRole("dialog", { name: title, exact: true });
  await dialog.getByRole("textbox", { name: "名称", exact: true }).fill(name);
  await dialog.getByRole("button", { name: "保存", exact: true }).click();
  await expect(dialog).toHaveCount(0);
}
for (const theme of ["dark", "light"] as const) {
  test(`character production flow, asset picker, shot conflict, deletion and restore (${theme})`, async ({
    page,
    request,
  }) => {
    const name = `Phase4-${theme}-${Date.now()}`;
    const { project, shot, asset } = await seed(request, name);
    const characterName = "SPF培训女员工" + "长期角色".repeat(12);
    let characterId = "";
    try {
      await page.goto(`/projects/${project.id}`);
      if (theme === "light")
        await page.getByRole("button", { name: "切换到浅色模式" }).click();
      await page.setViewportSize({ width: 1280, height: 800 });
      await page
        .getByRole("navigation", { name: "项目导航" })
        .getByRole("link", { name: "Characters", exact: true })
        .click();
      await expect(
        page.getByRole("heading", { name: "No characters yet" }),
      ).toBeVisible();
      await form(page, "创建角色", characterName);
      await page.locator(".character-card .entity-hit-area").click();
      await expect(page).toHaveURL(/characters\/[0-9a-f-]{36}$/);
      characterId = page.url().split("/").at(-1)!;
      await form(page, "编辑角色", characterName + "修改");
      await form(page, "创建角色状态", "基础状态");
      const stateName = "黄色 PPE + 双层手套" + "装备约束".repeat(12);
      await form(page, "创建角色状态", stateName);
      await page
        .getByRole("region", { name: stateName, exact: true })
        .getByRole("button", { name: "编辑角色状态", exact: true })
        .click();
      const stateEditor = page.getByRole("dialog", {
        name: "编辑角色状态",
        exact: true,
      });
      await stateEditor
        .getByRole("textbox", { name: "描述", exact: true })
        .fill("黄色 PPE，双层手套覆盖袖口。");
      await page.screenshot({
        path: `test-results/phase4-state-form-${theme}.png`,
        animations: "disabled",
      });
      await stateEditor
        .getByRole("button", { name: "保存", exact: true })
        .click();
      await expect(stateEditor).toHaveCount(0);
      let stateCard = page.getByRole("region", {
        name: stateName,
        exact: true,
      });
      await stateCard
        .getByRole("button", { name: `上移 ${stateName}`, exact: true })
        .click();
      await expect(page.locator(".state-card").first()).toHaveAttribute(
        "aria-label",
        stateName,
      );
      await expect(
        stateCard.getByRole("button", {
          name: `上移 ${stateName}`,
          exact: true,
        }),
      ).toBeDisabled();
      await page
        .getByRole("region", {
          name: "Character Reference Assets",
          exact: true,
        })
        .getByRole("button", { name: "Bind Asset", exact: true })
        .click();
      let picker = page.getByRole("dialog", { name: "选择已有资产" });
      await picker.getByRole("searchbox", { name: "搜索已有资产" }).fill(name);
      await picker.getByRole("combobox", { name: "选择资产类型" }).click();
      await page.getByRole("option", { name: "Image", exact: true }).click();
      await expect(picker.locator(".entity-card")).toHaveCount(1);
      await picker.locator(".entity-hit-area").click();
      await expect(picker).toContainText("已选择");
      const searchBox = await picker
        .getByRole("searchbox", { name: "搜索已有资产" })
        .boundingBox();
      const selectBox = await picker
        .getByRole("combobox", { name: "选择资产类型" })
        .boundingBox();
      expect(searchBox!.width).toBeGreaterThan(200);
      expect(Math.abs(searchBox!.height - selectBox!.height)).toBeLessThan(1);
      await page.screenshot({
        path: `test-results/phase4-picker-${theme}.png`,
        animations: "disabled",
      });
      await picker.getByRole("button", { name: "确认绑定" }).click();
      await expect(picker).toHaveCount(0);
      await stateCard.locator("summary").click();
      await stateCard
        .getByRole("button", { name: "Bind Asset", exact: true })
        .click();
      picker = page.getByRole("dialog", { name: "选择已有资产" });
      await picker.getByRole("searchbox", { name: "搜索已有资产" }).fill(name);
      await picker.locator(".entity-hit-area").click();
      await picker.getByRole("button", { name: "确认绑定" }).click();
      await expect(picker).toHaveCount(0);
      await expect(stateCard.locator(".reference-item")).toHaveCount(1);
      await page.screenshot({
        path: `test-results/phase4-detail-${theme}-1280.png`,
        animations: "disabled",
        fullPage: true,
      });
      await page.setViewportSize({ width: 1024, height: 720 });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await page.screenshot({
        path: `test-results/phase4-detail-${theme}-1024.png`,
        animations: "disabled",
        fullPage: true,
      });
      await page.goto(`/shots/${shot.id}`);
      await page
        .getByRole("combobox", { name: "选择角色", exact: true })
        .click();
      await page
        .getByRole("option", { name: characterName + "修改", exact: true })
        .click();
      await page
        .getByRole("combobox", { name: "选择角色状态", exact: true })
        .click();
      await page.getByRole("option", { name: stateName, exact: true }).click();
      await page
        .getByRole("button", { name: "Add Character State", exact: true })
        .click();
      await expect(page.locator(".shot-character-list")).toContainText(
        stateName,
      );
      await page.reload();
      await expect(page.locator(".shot-character-list")).toContainText(
        stateName,
      );
      await page
        .getByRole("combobox", { name: "选择角色", exact: true })
        .click();
      await page
        .getByRole("option", { name: characterName + "修改", exact: true })
        .click();
      await page
        .getByRole("combobox", { name: "选择角色状态", exact: true })
        .click();
      await page.getByRole("option", { name: "基础状态", exact: true }).click();
      await page
        .getByRole("button", { name: "Add Character State", exact: true })
        .click();
      await expect(page.getByRole("alert")).toContainText(
        "该镜头已绑定此角色的其他状态",
      );
      await page.screenshot({
        path: `test-results/phase4-shot-${theme}.png`,
        animations: "disabled",
      });
      await page.goto(`/projects/${project.id}/characters/${characterId}`);
      stateCard = page.getByRole("region", { name: stateName, exact: true });
      await stateCard
        .getByRole("button", { name: `删除 ${stateName}`, exact: true })
        .click();
      await page.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
        "正在被 1 个镜头使用",
      );
      await page.getByRole("button", { name: "取消", exact: true }).click();
      await page.goto(`/shots/${shot.id}`);
      await page
        .getByRole("button", { name: "解除角色状态绑定", exact: true })
        .click();
      await expect(page.locator(".shot-character-list li")).toHaveCount(0);
      await page.goto(`/projects/${project.id}/characters/${characterId}`);
      stateCard = page.getByRole("region", { name: stateName, exact: true });
      await stateCard
        .getByRole("button", { name: `删除 ${stateName}`, exact: true })
        .click();
      await page.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(stateCard).toHaveCount(0);
      await page
        .getByRole("button", { name: "显示已删除状态", exact: true })
        .click();
      await stateCard
        .getByRole("button", { name: "恢复状态", exact: true })
        .click();
      await expect(stateCard).toContainText("State reference assets · 0");
      await page
        .getByRole("button", { name: `删除 ${characterName}修改`, exact: true })
        .click();
      await page.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(
        page.getByRole("heading", { name: "No characters yet" }),
      ).toBeVisible();
      await page
        .getByRole("button", { name: "显示已删除", exact: true })
        .click();
      await page
        .getByRole("button", { name: `恢复 ${characterName}修改`, exact: true })
        .click();
      await page
        .getByRole("searchbox", { name: "搜索角色" })
        .fill(characterName);
      await expect(page.locator(".character-card")).toHaveCount(1);
      await page.screenshot({
        path: `test-results/phase4-list-${theme}.png`,
        animations: "disabled",
      });
    } finally {
      if (characterId) await request.delete(`/api/characters/${characterId}`);
      await request.delete(`/api/projects/${project.id}`);
      await request.delete(`/api/assets/${asset.id}`);
    }
  });
}

test("character loading error retry, pending save and import auto-binding", async ({
  page,
  request,
}) => {
  const name = `Phase4-import-${Date.now()}`;
  const { project, asset } = await seed(request, name);
  await page.route("**/api/projects/*/characters?**", (route) =>
    route.fulfill({
      status: 503,
      json: { code: "UNAVAILABLE", message: "角色列表暂时不可用", details: {} },
    }),
  );
  await page.goto(`/projects/${project.id}/characters`);
  await expect(page.getByRole("alert")).toContainText("角色列表暂时不可用");
  await page.unroute("**/api/projects/*/characters?**");
  await page.getByRole("button", { name: "重试", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "No characters yet" }),
  ).toBeVisible();
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let writes = 0;
  await page.route(
    `**/api/projects/${project.id}/characters`,
    async (route) => {
      writes++;
      await gate;
      await route.continue();
    },
  );
  await page.getByRole("button", { name: "创建角色", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "创建角色", exact: true });
  await dialog.getByRole("textbox", { name: "名称", exact: true }).fill(name);
  await dialog.getByRole("button", { name: "保存", exact: true }).click();
  await expect(dialog.getByRole("button", { name: "保存中…" })).toBeDisabled();
  await expect(dialog.getByRole("button", { name: "取消" })).toBeDisabled();
  expect(writes).toBe(1);
  release();
  await expect(dialog).toHaveCount(0);
  await page.locator(".character-card .entity-hit-area").click();
  await expect(page).toHaveURL(/characters\/[0-9a-f-]{36}$/);
  const characterId = page.url().split("/").at(-1)!;
  try {
    await page
      .getByRole("button", { name: "Import Asset", exact: true })
      .click();
    await page
      .getByLabel("选择资产文件")
      .setInputFiles({
        name: name + "-new.png",
        mimeType: "image/png",
        buffer: readFileSync(
          resolve(
            process.env.AVW_E2E_RUN_DIRECTORY ?? "../.workspace/e2e",
            "fixtures/reference.png",
          ),
        ),
      });
    await expect(page.locator(".import-results")).toContainText("已导入");
    await expect(page.locator(".reference-item")).toHaveCount(1);
    await page.reload();
    await expect(page.locator(".reference-item")).toHaveCount(1);
  } finally {
    const character = await (
      await request.get(`/api/characters/${characterId}`)
    ).json();
    await request.delete(`/api/characters/${characterId}`);
    for (const item of character.assets)
      await request.delete(`/api/assets/${item.id}`);
    await request.delete(`/api/assets/${asset.id}`);
    await request.delete(`/api/projects/${project.id}`);
  }
});
