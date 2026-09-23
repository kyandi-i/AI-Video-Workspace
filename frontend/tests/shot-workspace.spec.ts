import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

async function seed(request: APIRequestContext) {
  const post = async (url: string, data: object) => {
    const response = await request.post(`/api${url}`, { data });
    expect(response.ok()).toBeTruthy();
    return response.json();
  };
  const project = await post("/projects", { name: `Workspace ${Date.now()}` });
  const script = await post(`/projects/${project.id}/scripts`, {
    name: "Training",
  });
  const scene = await post(`/projects/${project.id}/scenes`, {
    script_id: script.id,
    name: "风淋室",
    description: "二更与核心区之间的风淋空间",
    fixed_constraints: "喷嘴阵列固定，两端分别为入口与出口。",
    negative_constraints: "禁止改变设备位置。",
  });
  const previous = await post(`/scenes/${scene.id}/shots`, {
    project_id: project.id,
    shot_code: "S9",
    title: "准备",
  });
  const shot = await post(`/scenes/${scene.id}/shots`, {
    project_id: project.id,
    shot_code: "S13",
    title: "风淋",
    creative_requirement: "旧版创作要求需保留",
  });
  const character = await post(`/projects/${project.id}/characters`, {
    name: "女员工",
    description: "培训员工",
  });
  const first = await post(`/characters/${character.id}/states`, {
    name: "黄色 PPE",
  });
  const second = await post(`/characters/${character.id}/states`, {
    name: "黄色 PPE + 双层手套",
  });
  const file = readFileSync(
    resolve(process.env.AVW_E2E_RUN_DIRECTORY!, "fixtures/reference.png"),
  );
  const asset = await (
    await request.post(`/api/assets/upload?filename=Workspace-${shot.id}.png`, {
      data: file,
      headers: { "Content-Type": "application/octet-stream" },
    })
  ).json();
  await post(`/characters/${character.id}/assets`, { asset_id: asset.id });
  await post(`/character-states/${second.id}/assets`, { asset_id: asset.id });
  return { project, shot, previous, character, first, second, asset, file };
}
async function choose(page: Page, label: string, value: string) {
  await page.getByRole("combobox", { name: label, exact: true }).click();
  await page.getByRole("option", { name: value, exact: true }).click();
}
const inputs = {
  "Main Action":
    "人物从二更进入风淋室，入口门关闭后完成风淋，风淋结束后出口门开启，人物进入核心区。",
  "Key Constraints":
    "两扇门严格互锁。\n人物保持自然连续步态。\n人物不得正对镜头。",
  "Negative Constraints":
    "禁止两门同时开启。\n禁止黄色脚套呈鞋形。\n禁止设备位置漂移。",
  "Free Notes": "固定机位，保持设备与服装连续性。",
};
for (const theme of ["dark", "light"] as const) {
  test(`shot workspace production flow ${theme}`, async ({ page, request }) => {
    const { project, shot, asset, file } = await seed(request);
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`/projects/${project.id}/shots`);
    if (theme === "light")
      await page.getByRole("button", { name: "切换到浅色模式" }).click();
    await page
      .getByRole("row", { name: "S13 风淋" })
      .getByRole("link", { name: "Workspace", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "S13 · 风淋" }),
    ).toBeVisible();
    await expect(
      page.getByRole("region", { name: "Scene Context" }),
    ).toContainText("喷嘴阵列固定");
    await expect(
      page.getByRole("button", { name: "Next Shot" }),
    ).toBeDisabled();
    await expect(page.getByText("No characters assigned")).toBeVisible();
    await page
      .getByLabel("Main Action", { exact: true })
      .fill("draft survives relation refresh");
    await choose(page, "选择角色", "女员工");
    await choose(page, "选择角色状态", "黄色 PPE");
    await page.getByRole("button", { name: "Add Character State" }).click();
    await expect(page.locator(".workspace-character")).toContainText(
      "黄色 PPE",
    );
    await page.getByRole("button", { name: "Change State" }).click();
    await choose(page, "选择角色状态", "黄色 PPE + 双层手套");
    await page.getByRole("button", { name: "Replace State" }).click();
    await expect(page.locator(".workspace-character strong")).toHaveText(
      "黄色 PPE + 双层手套",
    );
    await expect(page.locator(".workspace-character")).toHaveCount(1);
    await expect(
      page.getByText("Character references", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("State references", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Bind Asset", exact: true }).click();
    const picker = page.getByRole("dialog");
    await picker.getByRole("searchbox").fill(asset.name);
    await picker
      .getByRole("button", {
        name: new RegExp(asset.name.replaceAll(".", "\\.")),
      })
      .click();
    await picker.getByRole("button", { name: "确认绑定" }).click();
    await expect(picker).toHaveCount(0);
    const references = page.getByRole("region", {
      name: "Reference Assets",
      exact: true,
    });
    await expect(references.locator(".reference-item")).toHaveCount(1);
    await references
      .getByRole("button", { name: `Unbind ${asset.name}` })
      .click();
    await expect(references.locator(".reference-item")).toHaveCount(0);
    await references
      .getByRole("button", { name: "Import Asset", exact: true })
      .click();
    await page.getByLabel("选择资产文件").setInputFiles({
      name: `Shot-${theme}.png`,
      mimeType: "image/png",
      buffer: file,
    });
    await expect(references.locator(".reference-item")).toHaveCount(1);
    await expect(page.getByText("已导入", { exact: true })).toBeVisible();
    await references
      .getByRole("button", { name: "Import Asset", exact: true })
      .first()
      .click();
    await expect(page.getByLabel("Main Action", { exact: true })).toHaveValue(
      "draft survives relation refresh",
    );
    for (const [label, text] of Object.entries(inputs))
      await page.getByRole("textbox", { name: label, exact: true }).fill(text);
    await page.getByLabel("Duration (seconds)").fill("10");
    await choose(page, "Production Status", "Asset Preparing");
    await expect(
      page.getByText("Unsaved changes", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Save Changes" }).click();
    await expect(page.getByText("Saved", { exact: true })).toBeVisible();
    await page.reload();
    for (const [label, text] of Object.entries(inputs))
      await expect(
        page.getByRole("textbox", { name: label, exact: true }),
      ).toHaveValue(text);
    await expect(page.getByLabel("Duration (seconds)")).toHaveValue("10");
    await page
      .getByText("Legacy Creative Requirement", { exact: true })
      .click();
    await expect(
      page.getByText("旧版创作要求需保留", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Previous Shot" }).click();
    await expect(
      page.getByRole("heading", { name: "S9 · 准备" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Previous Shot" }),
    ).toBeDisabled();
    await page.getByRole("button", { name: "Next Shot" }).click();
    await expect(
      page.getByRole("textbox", { name: "Main Action", exact: true }),
    ).toHaveValue(inputs["Main Action"]);
    for (const width of [1280, 1024]) {
      await page.setViewportSize({ width, height: 900 });
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
          ),
        )
        .toBe(true);
      await page
        .getByLabel("Main Action", { exact: true })
        .scrollIntoViewIfNeeded();
      await expect(
        page.getByRole("button", { name: "Save Changes" }),
      ).toBeInViewport();
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({
        path: `../docs/screenshots/phase5-shot-workspace-${theme}${width === 1024 ? "-1024" : ""}.png`,
        fullPage: true,
      });
      if (theme === "dark" && width === 1024)
        await page.screenshot({
          path: "../docs/screenshots/phase5-shot-workspace-1024.png",
          fullPage: true,
        });
    }
    expect(errors).toEqual([]);
    const images = await page
      .locator(".shot-workspace img")
      .evaluateAll((elements) =>
        elements.map((e) => (e as HTMLImageElement).getAttribute("src")),
      );
    expect(images.every((url) => url?.endsWith("/thumbnail"))).toBe(true);
    await page.getByRole("button", { name: "Remove", exact: true }).click();
    await expect(page.getByText("No characters assigned")).toBeVisible();
    expect((await request.get(`/api/shots/${shot.id}`)).ok()).toBeTruthy();
  });
}

test("workspace dirty navigation, failed save, duplicate submit and retry", async ({
  page,
  request,
}) => {
  const { shot, project } = await seed(request);
  await page.goto(`/projects/${project.id}/shots`);
  await page
    .getByRole("row", { name: "S13 风淋" })
    .getByRole("link", { name: "Workspace", exact: true })
    .click();
  await page.getByLabel("Main Action", { exact: true }).fill("unsaved draft");
  await page.getByRole("button", { name: "Previous Shot" }).click();
  await expect(
    page.getByRole("dialog", { name: "Unsaved changes" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Stay", exact: true }).click();
  await expect(page.getByLabel("Main Action", { exact: true })).toHaveValue(
    "unsaved draft",
  );
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await expect(
    page.getByRole("dialog", { name: "Unsaved changes" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Stay", exact: true }).click();
  let count = 0;
  await page.route(`**/api/shots/${shot.id}`, async (route) => {
    if (route.request().method() !== "PATCH") return route.continue();
    count++;
    await new Promise((resolve) => setTimeout(resolve, 400));
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ code: "TEST", message: "保存暂时不可用" }),
    });
  });
  await page.getByRole("button", { name: "Save Changes" }).dblclick();
  await expect(page.getByText("Save failed", { exact: true })).toBeVisible();
  expect(count).toBe(1);
  await expect(page.getByLabel("Main Action", { exact: true })).toHaveValue(
    "unsaved draft",
  );
  await page.unroute(`**/api/shots/${shot.id}`);
  await page.getByRole("button", { name: "Save Changes" }).click();
  await expect(page.getByText("Saved", { exact: true })).toBeVisible();
  await page.getByLabel("Free Notes", { exact: true }).fill("discard me");
  await page.goBack();
  await expect(
    page.getByRole("dialog", { name: "Unsaved changes" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Discard and Leave" }).click();
  await expect(page).not.toHaveURL(new RegExp(`/shots/${shot.id}/workspace$`));
  await request.patch(`/api/shots/${shot.id}`, {
    data: { main_action: "edited elsewhere" },
  });
  await page
    .getByRole("row", { name: "S13 风淋" })
    .getByRole("link", { name: "Workspace", exact: true })
    .click();
  await expect(page.getByLabel("Main Action", { exact: true })).toHaveValue(
    "edited elsewhere",
  );
});

test("workspace loading failure has friendly retry", async ({
  page,
  request,
}) => {
  const { shot } = await seed(request);
  await page.route(`**/api/shots/${shot.id}/workspace`, (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ code: "TEST", message: "上下文暂时不可用" }),
    }),
  );
  await page.goto(`/shots/${shot.id}/workspace`);
  await expect(page.getByRole("alert")).toContainText("上下文暂时不可用");
  await page.unroute(`**/api/shots/${shot.id}/workspace`);
  await page.getByRole("button", { name: "重试" }).click();
  await expect(page.getByRole("heading", { name: "S13 · 风淋" })).toBeVisible();
});

test("workspace limits reference previews and opens asset detail", async ({
  page,
  request,
}) => {
  const { shot, asset, file } = await seed(request);
  for (let i = 0; i < 7; i++) {
    const media =
      i === 0
        ? asset
        : await (
            await request.post(`/api/assets/upload?filename=Ref-${i}.png`, {
              data: file,
              headers: { "Content-Type": "application/octet-stream" },
            })
          ).json();
    expect(
      (
        await request.post(`/api/shots/${shot.id}/assets`, {
          data: { asset_id: media.id },
        })
      ).ok(),
    ).toBeTruthy();
  }
  await page.goto(`/shots/${shot.id}/workspace`);
  const references = page.getByRole("region", {
    name: "Reference Assets",
    exact: true,
  });
  await expect(references.locator(".reference-item")).toHaveCount(6);
  await references.getByRole("button", { name: "View All (7)" }).click();
  await expect(references.locator(".reference-item")).toHaveCount(7);
  await references.locator(".reference-item button").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
});
