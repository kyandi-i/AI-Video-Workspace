import { test, expect, type APIRequestContext } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const fixture = (name = "storyboard.png") =>
  resolve(
    process.env.AVW_E2E_RUN_DIRECTORY ?? "../.workspace/e2e",
    "fixtures",
    name,
  );
async function seed(request: APIRequestContext) {
  const post = async (path: string, data: object) => {
    const r = await request.post(`/api${path}`, { data });
    expect(r.ok()).toBeTruthy();
    return r.json();
  };
  const project = await post("/projects", {
    name: `Storyboard ${crypto.randomUUID()}`,
  });
  const script = await post(`/projects/${project.id}/scripts`, { name: "SPF" });
  const scene = await post(`/projects/${project.id}/scenes`, {
    script_id: script.id,
    name: "风淋室",
  });
  const shot = await post(`/scenes/${scene.id}/shots`, {
    project_id: project.id,
    shot_code: "S13",
    title: "风淋",
    duration_seconds: 10,
  });
  return { project, shot, post };
}

for (const theme of ["dark", "light"] as const) {
  for (const width of [1024, 1280]) {
    test(`Phase 9 import history selection source preview ${theme} ${width}`, async ({
      page,
      request,
    }) => {
      const { shot, post } = await seed(request);
      await request.put("/api/settings/ai", {
        data: {
          api_base_url: "https://unused.invalid/v1",
          model: "fake-model",
          api_key: "fake-storyboard-key",
        },
      });
      const template = await post("/prompt-templates", {
        name: `Grid ${shot.id}`,
        scope: "GLOBAL",
        category: "STORYBOARD_6GRID",
        template_content: "{{shot_context}}",
      });
      const preview = await post(`/shots/${shot.id}/prompts/preview`, {
        template_id: template.id,
      });
      const prompt = await post(`/shots/${shot.id}/prompts/generate`, {
        template_id: template.id,
        input_hash: preview.input_hash,
        operation_id: crypto.randomUUID(),
      });
      await page.addInitScript(
        (value) => localStorage.setItem("avw.ui.theme", value),
        theme,
      );
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`/shots/${shot.id}/workspace`);
      const panel = page.getByRole("region", {
        name: "Storyboard",
        exact: true,
      });
      await expect(panel.getByText(/No storyboards yet/)).toBeVisible();
      await expect(
        panel.getByRole("combobox", { name: "Storyboard source Prompt" }),
      ).toContainText("Selected 六宫格 Prompt V1");
      await panel.getByLabel("Storyboard notes").fill("外部生成结果 A");
      await panel
        .getByLabel("Import storyboard image")
        .setInputFiles(fixture());
      const v1 = panel.getByRole("article", {
        name: "Storyboard V1",
        exact: true,
      });
      await expect(v1.getByText("Selected", { exact: true })).toBeVisible();
      await expect(
        v1.getByText("Source Prompt V1 · STORYBOARD_6GRID"),
      ).toBeVisible();
      await expect(
        v1.getByRole("img", {
          name: "Storyboard V1 thumbnail",
          exact: true,
        }),
      ).toHaveJSProperty("naturalWidth", 512);
      await panel.getByLabel("Storyboard notes").fill("外部生成结果 B");
      await panel
        .getByLabel("Import storyboard image")
        .setInputFiles(fixture("scene.png"));
      const v2 = panel.getByRole("article", {
        name: "Storyboard V2",
        exact: true,
      });
      await expect(v2.getByText("Selected", { exact: true })).toBeVisible();
      await expect(v1.getByText("Selected", { exact: true })).toHaveCount(0);
      await expect(panel.getByRole("article").first()).toHaveAccessibleName(
        "Storyboard V2",
      );
      await v1.getByRole("button", { name: "Select", exact: true }).click();
      await expect(v1.getByText("Selected", { exact: true })).toBeVisible();
      await expect(panel.getByText("Selected", { exact: true })).toHaveCount(1);
      await page.reload();
      await expect(v1.getByText("Selected", { exact: true })).toBeVisible();
      await v1.getByRole("button", { name: "View", exact: true }).click();
      const detail = page.getByRole("dialog", {
        name: "Storyboard V1",
        exact: true,
      });
      await expect(
        detail.getByRole("img", {
          name: "Storyboard V1 original",
          exact: true,
        }),
      ).toHaveJSProperty("naturalWidth", 640);
      await detail.getByRole("button", { name: "关闭", exact: true }).click();
      const history = await (
        await request.get(`/api/shots/${shot.id}/storyboards`)
      ).json();
      expect(
        history.map(
          (r: { source_prompt_record_id: string }) => r.source_prompt_record_id,
        ),
      ).toEqual([prompt.id, prompt.id]);
      expect(history.map((r: { version: number }) => r.version)).toEqual([
        2, 1,
      ]);
      await expect(page.locator("body")).toHaveJSProperty("scrollWidth", width);
      await panel.screenshot({
        path: resolve(
          "../.workspace/phase9",
          `storyboard-${theme}-${width}.png`,
        ),
      });
    });
  }
}

test("Phase 9 existing asset reuse independent unbind delete and in-use", async ({
  page,
  request,
}) => {
  const { project, shot } = await seed(request);
  const asset = await (
    await request.post(
      "/api/assets/upload?filename=existing-grid.png&asset_type=STORYBOARD_6GRID",
      { data: readFileSync(fixture()) },
    )
  ).json();
  const image = await (
    await request.post(
      "/api/assets/upload?filename=ordinary-image.png&asset_type=IMAGE",
      { data: readFileSync(fixture()) },
    )
  ).json();
  const invalid = await request.post(`/api/shots/${shot.id}/storyboards`, {
    data: { asset_id: image.id },
  });
  expect(invalid.status()).toBe(422);
  await page.goto(`/shots/${shot.id}/workspace`);
  const panel = page.getByRole("region", { name: "Storyboard", exact: true });
  for (const version of [1, 2]) {
    await panel.getByRole("button", { name: "Use Existing Asset" }).click();
    const picker = page.getByRole("dialog", { name: "选择已有资产" });
    await expect(
      picker.getByRole("combobox", { name: "选择资产类型" }),
    ).toBeDisabled();
    await picker.getByLabel("搜索已有资产").fill("existing-grid.png");
    await picker
      .getByText("existing-grid.png", { exact: true })
      .first()
      .click();
    await picker.getByRole("button", { name: "确认绑定", exact: true }).click();
    await expect(
      panel.getByRole("article", {
        name: `Storyboard V${version}`,
        exact: true,
      }),
    ).toBeVisible();
  }
  await request.delete(`/api/projects/${project.id}/assets/${asset.id}`);
  const refs = page.getByRole("region", {
    name: "Reference Assets",
    exact: true,
  });
  await refs
    .getByRole("button", { name: "Unbind existing-grid.png", exact: true })
    .click();
  await expect(refs.getByText(/No reference assets/)).toBeVisible();
  expect((await request.delete(`/api/assets/${asset.id}`)).status()).toBe(409);
  const v1 = panel.getByRole("article", { name: "Storyboard V1", exact: true });
  await v1.getByRole("button", { name: "View", exact: true }).click();
  const detail = page.getByRole("dialog", {
    name: "Storyboard V1",
    exact: true,
  });
  await expect(
    detail.getByRole("img", {
      name: "Storyboard V1 original",
      exact: true,
    }),
  ).toHaveJSProperty("naturalWidth", 640);
  await detail.getByRole("button", { name: "关闭", exact: true }).click();
  await v1
    .getByRole("button", { name: "删除 Storyboard V1", exact: true })
    .click();
  await page.getByRole("button", { name: "确认删除", exact: true }).click();
  await expect(v1).toHaveCount(0);
  await expect(
    panel
      .getByRole("article", { name: "Storyboard V2", exact: true })
      .getByText("Selected", { exact: true }),
  ).toBeVisible();
  expect((await request.get(`/api/assets/${asset.id}/file`)).ok()).toBeTruthy();
});

test("Phase 9 invalid import leaves no version and permits explicit retry", async ({
  page,
  request,
}) => {
  const { shot } = await seed(request);
  await page.goto(`/shots/${shot.id}/workspace`);
  const panel = page.getByRole("region", { name: "Storyboard", exact: true });
  await panel.getByLabel("Import storyboard image").setInputFiles({
    name: "broken.png",
    mimeType: "image/png",
    buffer: Buffer.from("not an image"),
  });
  await expect(panel.getByRole("alert")).toBeVisible();
  await expect(panel.getByText(/No storyboards yet/)).toBeVisible();
  expect(
    await (await request.get(`/api/shots/${shot.id}/storyboards`)).json(),
  ).toEqual([]);
  await panel.getByLabel("Import storyboard image").setInputFiles(fixture());
  await expect(
    panel.getByRole("article", { name: "Storyboard V1", exact: true }),
  ).toBeVisible();
});
