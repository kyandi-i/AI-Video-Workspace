import { test, expect, type APIRequestContext } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const fixture = (name: string) => resolve(process.env.AVW_E2E_RUN_DIRECTORY ?? "../.workspace/e2e", "fixtures", name);
async function seed(request: APIRequestContext) {
  const post = async (path: string, data: object) => {
    const r = await request.post(`/api${path}`, { data });
    expect(r.ok()).toBeTruthy();
    return r.json();
  };
  const project = await post("/projects", { name: `Video ${crypto.randomUUID()}` });
  const script = await post(`/projects/${project.id}/scripts`, { name: "SPF" });
  const scene = await post(`/projects/${project.id}/scenes`, { script_id: script.id, name: "风淋室" });
  const shot = await post(`/scenes/${scene.id}/shots`, { project_id: project.id, shot_code: "S13", title: "风淋", duration_seconds: 10 });
  return { project, shot, post };
}

for (const theme of ["dark", "light"] as const) {
  for (const width of [1024, 1280]) {
    test(`Phase 10 video lifecycle ${theme} ${width}`, async ({ page, request }) => {
      const { shot, post } = await seed(request);
      await request.put("/api/settings/ai", { data: { api_base_url: "https://unused.invalid/v1", model: "fake-model", api_key: "fake-video-key" } });
      const template = await post("/prompt-templates", { name: `Video ${shot.id}`, scope: "GLOBAL", category: "VIDEO_GENERATION", template_content: "{{shot_context}}" });
      const preview = await post(`/shots/${shot.id}/prompts/preview`, { template_id: template.id });
      const prompt = await post(`/shots/${shot.id}/prompts/generate`, { template_id: template.id, input_hash: preview.input_hash, operation_id: crypto.randomUUID() });
      const sbResponse = await request.post(`/api/shots/${shot.id}/storyboards/import?filename=storyboard.png`, { data: readFileSync(fixture("storyboard.png")) });
      expect(sbResponse.status()).toBe(201);
      const storyboard = await sbResponse.json();
      await page.addInitScript((value) => localStorage.setItem("avw.ui.theme", value), theme);
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`/shots/${shot.id}/workspace`);
      const panel = page.getByRole("region", { name: "Video Results", exact: true });
      await expect(panel.getByText(/No selected video/)).toBeVisible();
      await panel.getByRole("combobox", { name: "Video source Storyboard", exact: true }).click();
      await page.getByRole("option", { name: "Storyboard V1 · Selected", exact: true }).click();
      await panel.getByRole("combobox", { name: "Video source Prompt", exact: true }).click();
      await page.getByRole("option", { name: "VIDEO_GENERATION · V1 · Selected", exact: true }).click();
      await panel.getByLabel("Video notes", { exact: true }).fill("视频结果 A");
      await panel.getByLabel("Import video file", { exact: true }).setInputFiles(fixture("video.mp4"));
      const v1 = panel.getByRole("article", { name: "Video V1", exact: true });
      await expect(v1.getByText("Selected", { exact: true })).toBeVisible();
      await expect(v1.getByText("Source Storyboard V1", { exact: true })).toBeVisible();
      await expect(v1.getByText("Source Prompt V1 · VIDEO_GENERATION", { exact: true })).toBeVisible();
      await panel.getByLabel("Video notes", { exact: true }).fill("视频结果 B");
      await panel.getByLabel("Import video file", { exact: true }).setInputFiles(fixture("video.mp4"));
      const v2 = panel.getByRole("article", { name: "Video V2", exact: true });
      await expect(v2.getByText("Selected", { exact: true })).toBeVisible();
      await expect(v1.getByText("Selected", { exact: true })).toHaveCount(0);
      await v1.getByRole("button", { name: "Select", exact: true }).click();
      await expect(v1.getByText("Selected", { exact: true })).toBeVisible();
      await expect(panel.getByText("Selected", { exact: true })).toHaveCount(1);
      await page.reload();
      await expect(v1.getByText("Selected", { exact: true })).toBeVisible();
      await expect(panel.locator("video")).toHaveCount(0);
      await v1.getByRole("button", { name: "Preview", exact: true }).click();
      const dialog = page.getByRole("dialog", { name: "Video V1", exact: true });
      const video = dialog.getByLabel("Video V1 playback", { exact: true });
      await expect(video).toHaveJSProperty("videoWidth", 160);
      await expect(video).toHaveJSProperty("paused", true);
      await video.evaluate((node: HTMLVideoElement) => node.play());
      await expect.poll(() => video.evaluate((node: HTMLVideoElement) => node.currentTime)).toBeGreaterThan(0);
      await dialog.getByRole("button", { name: "关闭", exact: true }).click();
      await v1.getByRole("button", { name: "删除 Video V1", exact: true }).click();
      const confirmation = page.getByRole("dialog", { name: "删除 Video V1？", exact: true });
      await confirmation.getByRole("button", { name: "确认删除", exact: true }).click();
      await expect(v1).toHaveCount(0);
      await expect(panel.getByText(/No selected video/)).toBeVisible();
      await panel.getByRole("checkbox", { name: "Show deleted videos", exact: true }).check();
      await v1.getByRole("button", { name: "Restore", exact: true }).click();
      await expect(v1.getByText("Deleted", { exact: true })).toHaveCount(0);
      await expect(panel.getByText("Selected", { exact: true })).toHaveCount(0);
      await page.reload();
      await expect(v1.getByText("视频结果 A", { exact: true })).toBeVisible();
      const history = await (await request.get(`/api/shots/${shot.id}/video-results`)).json();
      expect(history.map((r: { version: number }) => r.version)).toEqual([2, 1]);
      expect(history.every((r: { source_storyboard_id: string; source_prompt_record_id: string }) => r.source_storyboard_id === storyboard.id && r.source_prompt_record_id === prompt.id)).toBeTruthy();
      await expect(page.locator("body")).toHaveJSProperty("scrollWidth", width);
      await panel.screenshot({ path: resolve("../.workspace/phase10", `video-${theme}-${width}.png`) });
    });
  }
}

test("Phase 10 existing video asset and invalid import retry", async ({ page, request }) => {
  const { shot } = await seed(request);
  const filename = `existing-${shot.id}.mp4`;
  const response = await request.post(`/api/assets/upload?filename=${filename}`, { data: readFileSync(fixture("video.mp4")) });
  expect(response.status()).toBe(201);
  const asset = await response.json();
  await page.goto(`/shots/${shot.id}/workspace`);
  const panel = page.getByRole("region", { name: "Video Results", exact: true });
  await panel.getByRole("button", { name: "Use Existing Video Asset", exact: true }).click();
  const picker = page.getByRole("dialog", { name: "选择已有资产", exact: true });
  await picker.getByRole("searchbox", { name: "搜索已有资产", exact: true }).fill(filename);
  await picker.getByText(filename, { exact: true }).click();
  await picker.getByRole("button", { name: "确认绑定", exact: true }).click();
  await expect(panel.getByRole("article", { name: "Video V1", exact: true })).toBeVisible();
  const history = await (await request.get(`/api/shots/${shot.id}/video-results`)).json();
  expect(history[0].asset_id).toBe(asset.id);
  await panel.getByLabel("Import video file", { exact: true }).setInputFiles({ name: "invalid.mp4", mimeType: "video/mp4", buffer: Buffer.from("invalid media") });
  await expect(panel.getByRole("alert")).toBeVisible();
  await expect(panel.getByRole("article")).toHaveCount(1);
  await panel.getByLabel("Import video file", { exact: true }).setInputFiles(fixture("video.mp4"));
  await expect(panel.getByRole("article", { name: "Video V2", exact: true }).getByText("Selected", { exact: true })).toBeVisible();
});
