import { test, expect, type APIRequestContext, type Page } from "@playwright/test";
import { readFileSync, renameSync, realpathSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";

const runRoot = () => {
  const directory = process.env.AVW_E2E_RUN_DIRECTORY;
  if (!directory) throw new Error("An isolated E2E run directory is required");
  const root = realpathSync(directory);
  const rel = relative(realpathSync(resolve("../.workspace/e2e")), root);
  if (isAbsolute(rel) || rel.startsWith("..") || !rel.startsWith("run-")) {
    throw new Error("Refusing a non-isolated E2E directory");
  }
  return root;
};

async function seed(request: APIRequestContext) {
  const post = async (path: string, data: object) => {
    const response = await request.post(`/api${path}`, { data });
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  };
  const name = `P11-${crypto.randomUUID()} 风淋项目与视频生产验收`;
  const project = await post("/projects", { name });
  const script = await post(`/projects/${project.id}/scripts`, { name: "验收剧本" });
  const scene = await post(`/projects/${project.id}/scenes`, { script_id: script.id, name: "风淋室" });
  const shot = await post(`/scenes/${scene.id}/shots`, {
    project_id: project.id, shot_code: "S13", title: "进入风淋室", duration_seconds: 10,
  });
  const configured = await request.put("/api/settings/ai", {
    data: { api_base_url: "https://unused.invalid/v1", model: "fake-model", api_key: "fake-phase11-key" },
  });
  expect(configured.ok()).toBeTruthy();
  const template = await post("/prompt-templates", {
    name: `Template ${shot.id}`, scope: "PROJECT", project_id: project.id,
    category: "VIDEO_GENERATION", template_content: "{{shot_context}}",
  });
  const preview = await post(`/shots/${shot.id}/prompts/preview`, { template_id: template.id });
  const prompt = await post(`/shots/${shot.id}/prompts/generate`, {
    template_id: template.id, input_hash: preview.input_hash, operation_id: crypto.randomUUID(),
  });
  const sb = await request.post(`/api/shots/${shot.id}/storyboards/import?filename=storyboard.png`, {
    data: readFileSync(resolve(runRoot(), "fixtures/storyboard.png")),
  });
  expect(sb.status()).toBe(201);
  const storyboard = await sb.json();
  const video = await request.post(`/api/shots/${shot.id}/video-results/import?filename=video.mp4&source_storyboard_id=${storyboard.id}&source_prompt_record_id=${prompt.id}`, {
    data: readFileSync(resolve(runRoot(), "fixtures/video.mp4")),
  });
  expect(video.status()).toBe(201);
  return { project, shot, storyboard, post };
}

async function noOverflow(page: Page, width: number) {
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", width);
  await expect(page.locator("html")).toHaveJSProperty("scrollWidth", width);
}

for (const theme of ["dark", "light"] as const) {
  for (const width of [1024, 1280]) {
    test(`Phase 11 export and recycle lifecycle ${theme} ${width}`, async ({ page, request }, info) => {
      const { project, post } = await seed(request);
      await page.addInitScript((value) => localStorage.setItem("avw.ui.theme", value), theme);
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`/projects/${project.id}`);
      const exportButton = page.getByRole("button", { name: "Export Project", exact: true });
      await expect(exportButton).toBeVisible();
      await expect(exportButton).toBeEnabled();
      await exportButton.click();
      const downloadLink = page.getByRole("link", { name: "Download ZIP", exact: true });
      await expect(downloadLink).toBeVisible();
      const downloading = page.waitForEvent("download");
      await downloadLink.click();
      const download = await downloading;
      expect(await download.failure()).toBeNull();
      expect(download.suggestedFilename()).toBe(`${project.name}.zip`);
      await download.saveAs(info.outputPath("project.zip"));
      await expect(page.getByText(/Traceback|IntegrityError|Internal Server Error/)).toHaveCount(0);
      await noOverflow(page, width);
      await page.screenshot({ path: info.outputPath(`export-${theme}-${width}.png`) });

      const character = await post(`/projects/${project.id}/characters`, {
        name: `${project.name} 长名称角色测试用于检查换行和恢复操作`,
      });
      const another = await post(`/projects/${project.id}/scripts`, { name: `${project.name} 回收剧本` });
      expect((await request.delete(`/api/characters/${character.id}`)).status()).toBe(204);
      expect((await request.delete(`/api/scripts/${another.id}`)).status()).toBe(204);
      await page.getByRole("navigation", { name: "主导航", exact: true })
        .getByRole("link", { name: "Recycle Bin", exact: true }).click();
      await expect(page.getByRole("heading", { name: "Recycle Bin", exact: true })).toBeVisible();
      await page.getByRole("textbox", { name: "Search deleted items", exact: true }).fill(project.name);
      const list = page.getByRole("list", { name: "Deleted items", exact: true });
      await expect(list.getByRole("listitem")).toHaveCount(2);
      const row = list.getByRole("listitem").filter({ has: page.getByText(character.name, { exact: true }) });
      await expect(row.getByText("Character", { exact: true })).toBeVisible();
      await expect(row.getByText(project.name, { exact: true })).toBeVisible();
      await expect(row.locator("time")).toHaveAttribute("datetime", /\d{4}-\d{2}-\d{2}T/);
      const filter = page.getByRole("combobox", { name: "Entity type", exact: true });
      await filter.click();
      await page.getByRole("option", { name: "Character", exact: true }).click();
      await expect(list.getByRole("listitem")).toHaveCount(1);
      const restore = row.getByRole("button", { name: `Restore ${character.name}`, exact: true });
      await expect(restore).toBeInViewport();
      await noOverflow(page, width);
      await page.screenshot({ path: info.outputPath(`recycle-${theme}-${width}.png`) });
      await restore.click();
      await expect(page.getByRole("status").filter({ hasText: `已恢复 ${character.name}` })).toBeVisible();
      await expect(row).toHaveCount(0);
      await expect(page.getByText("No deleted items", { exact: true })).toBeVisible();
      const active = await request.get(`/api/characters/${character.id}`);
      expect(active.status()).toBe(200);
      expect((await active.json()).deleted_at).toBeNull();
      await filter.click();
      await page.getByRole("option", { name: "Script", exact: true }).click();
      await list.getByRole("button", { name: `Restore ${another.name}`, exact: true }).click();
      await filter.click();
      await page.getByRole("option", { name: "All types", exact: true }).click();
      await expect(page.getByText("No deleted items", { exact: true })).toBeVisible();
      const deleted = await request.get(`/api/recycle-bin?search=${encodeURIComponent(project.name)}`);
      expect((await deleted.json()).items).toEqual([]);
    });
  }
}

test("Phase 11 missing managed media shows error without false success", async ({ page, request }) => {
  const { project, storyboard } = await seed(request);
  const response = await request.get(`/api/assets/${storyboard.asset_id}`);
  expect(response.ok()).toBeTruthy();
  const asset = await response.json();
  const workspace = realpathSync(resolve(runRoot(), "workspace"));
  const media = realpathSync(resolve(workspace, asset.storage_path));
  const rel = relative(workspace, media);
  if (isAbsolute(rel) || rel.startsWith("..") || !rel.startsWith("storage")) {
    throw new Error("Refusing to move media outside the isolated workspace");
  }
  const held = `${media}.phase11-held`;
  renameSync(media, held);
  try {
    await page.goto(`/projects/${project.id}`);
    const result = page.waitForResponse((r) => r.url().endsWith(`/projects/${project.id}/export`));
    await page.getByRole("button", { name: "Export Project", exact: true }).click();
    const failed = await result;
    expect(failed.ok()).toBe(false);
    const error = await failed.json();
    expect(error.message).toBeTruthy();
    await expect(page.getByRole("alert")).toHaveText(error.message);
    await expect(page.getByRole("link", { name: "Download ZIP", exact: true })).toHaveCount(0);
    await expect(page.getByText(/Traceback|IntegrityError|Internal Server Error/)).toHaveCount(0);
  } finally {
    renameSync(held, media);
  }
});
