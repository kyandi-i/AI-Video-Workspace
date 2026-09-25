import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";

test.describe.configure({ mode: "serial" });

async function configure(
  request: APIRequestContext,
  key = "fake-browser-credential",
) {
  const r = await request.put("/api/settings/ai", {
    data: {
      api_base_url: "https://unused.invalid/v1",
      model: "fake-model",
      api_key: key,
    },
  });
  expect(r.ok()).toBeTruthy();
}
async function seed(
  request: APIRequestContext,
  action = "人物从二更进入风淋室，双门互锁。",
) {
  const post = async (path: string, data: object) => {
    const r = await request.post(`/api${path}`, { data });
    expect(r.ok()).toBeTruthy();
    return r.json();
  };
  const project = await post("/projects", { name: `Generation ${Date.now()}` });
  const script = await post(`/projects/${project.id}/scripts`, { name: "SPF" });
  const scene = await post(`/projects/${project.id}/scenes`, {
    script_id: script.id,
    name: "风淋室",
    fixed_constraints: "两门位置固定",
  });
  const shot = await post(`/scenes/${scene.id}/shots`, {
    project_id: project.id,
    shot_code: "S13",
    title: "风淋",
    duration_seconds: 10,
    main_action: action,
    key_constraints: "人物不得正对镜头",
    negative_constraints: "禁止两门同时开启",
    free_notes: "自然连续步态",
  });
  const character = await post(`/projects/${project.id}/characters`, {
    name: "SPF培训女员工",
  });
  const state = await post(`/characters/${character.id}/states`, {
    name: "黄色 PPE + 双层手套",
  });
  await post(`/shots/${shot.id}/character-states`, {
    character_state_id: state.id,
  });
  const template = await post("/prompt-templates", {
    name: `Prompt ${shot.id}`,
    scope: "PROJECT",
    project_id: project.id,
    category: "VIDEO_GENERATION",
    template_content:
      "真实镜头：{{shot_code}}\n{{shot_context}}\n素材：{{reference_assets_context}}",
  });
  return { shot, template };
}
async function selectTemplate(page: Page, name: string) {
  await page
    .getByRole("button", { name: "Browse Templates", exact: true })
    .click();
  const picker = page.getByRole("dialog", { name: "Prompt Template Picker" });
  await picker.getByLabel("Search templates").fill(name);
  await picker
    .getByRole("button", { name: "Select Template", exact: true })
    .click();
  await picker.getByRole("button", { name: "关闭", exact: true }).click();
}

test("AI settings writes, masks, preserves and clears key", async ({
  page,
  request,
}) => {
  await configure(request, "");
  await page.goto("/settings");
  const panel = page.getByRole("region", { name: "AI Provider", exact: true });
  await panel
    .getByLabel("API Base URL", { exact: true })
    .fill("https://unused.invalid/v1");
  await panel.getByLabel("Model", { exact: true }).fill("fake-model");
  const synthetic = "fake-browser-credential";
  await panel.getByLabel("API Key", { exact: true }).fill(synthetic);
  await panel
    .getByRole("button", { name: "Save AI Settings", exact: true })
    .click();
  await expect(
    panel.getByText("AI Settings saved", { exact: true }),
  ).toBeVisible();
  await expect(panel.getByLabel("API Key", { exact: true })).toHaveValue("");
  const read = await request.get("/api/settings/ai");
  expect(await read.text()).not.toContain(synthetic);
  expect((await read.json()).api_key_configured).toBe(true);
  await page.reload();
  await expect(
    panel.getByText("API Key configured", { exact: true }),
  ).toBeVisible();
  await panel
    .getByRole("button", { name: "Save AI Settings", exact: true })
    .click();
  await expect(
    panel.getByText("AI Settings saved", { exact: true }),
  ).toBeVisible();
  expect(
    (await (await request.get("/api/settings/ai")).json()).api_key_configured,
  ).toBe(true);
  await panel.getByRole("checkbox").check();
  await panel
    .getByRole("button", { name: "Save AI Settings", exact: true })
    .click();
  await expect(
    panel.getByText("API Key not configured", { exact: true }),
  ).toBeVisible();
});

for (const theme of ["dark", "light"] as const)
  for (const width of [1024, 1280]) {
    test(`Prompt generation persistence and Copy ${theme} ${width}`, async ({
      page,
      request,
      context,
    }) => {
      await configure(request);
      const { shot, template } = await seed(request);
      await context.grantPermissions(["clipboard-read", "clipboard-write"]);
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`/shots/${shot.id}/workspace`);
      if (theme === "light")
        await page.getByRole("button", { name: "切换到浅色模式" }).click();
      await selectTemplate(page, template.name);
      const input = page.getByLabel("Actual Rendered Input", { exact: true });
      await expect(input).toContainText("人物从二更进入风淋室");
      for (const term of [
        "黄色 PPE + 双层手套",
        "SPF培训女员工",
        "两门位置固定",
        "自然连续步态",
        "禁止两门同时开启",
      ])
        await expect(input).toContainText(term);
      expect(await input.innerText()).not.toMatch(/None|null|undefined/);
      let calls = 0;
      await page.route(
        `**/api/shots/${shot.id}/prompts/generate`,
        async (route) => {
          calls++;
          await new Promise((resolve) => setTimeout(resolve, 700));
          await route.continue();
        },
      );
      await page.getByRole("button", { name: "Generate", exact: true }).click();
      await expect(
        page.getByRole("button", { name: "Generating…", exact: true }),
      ).toBeDisabled();
      await expect(
        page.getByText("Generation saved", { exact: true }),
      ).toBeVisible();
      expect(calls).toBe(1);
      const result = page.getByLabel("Generated Prompt result", {
        exact: true,
      });
      await expect(result).toContainText("FAKE · 风淋 Prompt");
      const persisted = await (
        await request.get(`/api/shots/${shot.id}/prompts/latest`)
      ).json();
      expect(persisted.rendered_input).toBe(await input.innerText());
      expect(persisted.provider).toBe("fake-test-provider");
      await page
        .getByRole("button", { name: "Copy Prompt", exact: true })
        .click();
      await expect(page.getByText("Copied", { exact: true })).toBeVisible();
      expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
        persisted.generated_content,
      );
      await page.reload();
      await expect(result).toHaveText(persisted.generated_content);
      await page.getByText("本次生成使用的输入", { exact: true }).click();
      await expect(page.locator(".prompt-result details pre")).toHaveText(
        persisted.rendered_input,
      );
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await page.screenshot({
        path: `test-results/phase7-prompt-${theme}-${width}.png`,
        fullPage: true,
      });
      await expect(
        page.getByText("Prompt History", { exact: true }),
      ).toHaveCount(0);
    });
  }

test("provider error retains input and Retry saves same operation", async ({
  page,
  request,
}) => {
  await configure(request);
  const { shot, template } = await seed(request, "[[FAKE_RETRY]] 保持双门互锁");
  await page.goto(`/shots/${shot.id}/workspace`);
  await selectTemplate(page, template.name);
  await page.getByRole("button", { name: "Generate", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("超时");
  expect(
    await (await request.get(`/api/shots/${shot.id}/prompts/latest`)).json(),
  ).toBeNull();
  await expect(
    page.getByLabel("Actual Rendered Input", { exact: true }),
  ).toContainText("保持双门互锁");
  await page
    .getByRole("button", { name: "Retry Generation", exact: true })
    .click();
  await expect(
    page.getByText("Generation saved", { exact: true }),
  ).toBeVisible();
});

test("unsaved requirements block generation and missing key is actionable", async ({
  page,
  request,
}) => {
  await configure(request, "");
  const { shot, template } = await seed(request);
  await page.goto(`/shots/${shot.id}/workspace`);
  await selectTemplate(page, template.name);
  await page
    .getByRole("textbox", { name: "Main Action", exact: true })
    .fill("尚未保存的新动作");
  await expect(
    page.getByText("请先 Save Changes，再预览和生成。", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Generate", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Save Changes", exact: true }).click();
  await expect(
    page.getByLabel("Actual Rendered Input", { exact: true }),
  ).toContainText("尚未保存的新动作");
  await page.getByRole("button", { name: "Generate", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("API Key");
  expect(
    await (await request.get(`/api/shots/${shot.id}/prompts/latest`)).json(),
  ).toBeNull();
});
