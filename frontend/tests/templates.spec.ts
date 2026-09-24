import { test, expect, type Page } from "@playwright/test";

async function choose(page: Page, label: string, value: string) {
  await page.getByRole("combobox", { name: label, exact: true }).click();
  await page.getByRole("option", { name: value, exact: true }).click();
}
async function noOverflow(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  for (const element of await page
    .locator(
      ".template-editor, .template-picker, .template-fields, .placeholder-panel",
    )
    .all()) {
    expect(
      await element.evaluate((e) => e.scrollWidth <= e.clientWidth + 1),
    ).toBeTruthy();
  }
}

for (const theme of ["dark", "light"] as const) {
  for (const width of [1024, 1280]) {
    test(`template workflow ${theme} ${width}`, async ({ page, request }) => {
      const prefix = `Templates ${theme} ${width} ${Date.now()}`;
      const project = await (
        await request.post("/api/projects", { data: { name: prefix } })
      ).json();
      const errors: string[] = [];
      page.on("pageerror", (e) => errors.push(e.message));
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/prompt-templates");
      if (theme === "light")
        await page.getByRole("button", { name: "切换到浅色模式" }).click();
      await page.getByRole("button", { name: "Create Template" }).click();
      const editor = page.getByRole("dialog", {
        name: "Template Editor",
        exact: true,
      });
      await editor.getByLabel("Name", { exact: true }).fill(prefix);
      await editor
        .getByLabel("Description", { exact: true })
        .fill(`Find ${prefix}`);
      await choose(page, "Template category", "Video Generation");
      const content = editor.getByLabel("Template Content", { exact: true });
      await content.fill("【参考】\n前后\n{% for %} <b>纯文本</b>");
      await content.evaluate((el: HTMLTextAreaElement) => {
        el.focus();
        el.setSelectionRange(6, 6);
      });
      await editor
        .getByRole("button", { name: "Main Action", exact: true })
        .click();
      await expect(content).toHaveValue(
        "【参考】\n前{{main_action}}后\n{% for %} <b>纯文本</b>",
      );
      await editor
        .getByRole("button", { name: "Preview", exact: true })
        .click();
      await expect(editor.locator(".template-preview pre")).toContainText(
        "人物进入风淋室",
      );
      await expect(editor.getByRole("status")).toHaveText("Unsaved");
      // Preview has not persisted a new template.
      expect(
        await (
          await request.get(
            `/api/prompt-templates?search=${encodeURIComponent(prefix)}`,
          )
        ).json(),
      ).toEqual([]);
      await noOverflow(page);
      await expect(
        editor.getByRole("button", { name: "Save Template" }),
      ).toBeInViewport();
      await page.screenshot({
        path: `test-results/phase6-template-editor-${theme}-${width}.png`,
      });
      await editor.getByRole("button", { name: "Save Template" }).click();
      await expect(editor.getByRole("status")).toHaveText("Saved");
      await editor.getByRole("button", { name: "Close", exact: true }).click();
      await page.getByLabel("Search templates").fill(prefix);
      await choose(page, "Scope filter", "Global");
      await choose(page, "Category filter", "Video Generation");
      const row = page
        .locator(".template-row")
        .filter({
          has: page.getByRole("heading", { name: prefix, exact: true }),
        });
      await expect(row).toBeVisible();
      await row.getByRole("button", { name: "Edit", exact: true }).click();
      await editor
        .getByLabel("Description", { exact: true })
        .fill(`Edited ${prefix}`);
      await editor.getByRole("button", { name: "Save Template" }).click();
      await expect(editor.getByRole("status")).toHaveText("Saved");
      await editor.getByRole("button", { name: "Close", exact: true }).click();
      await page.reload();
      await page.getByLabel("Search templates").fill(prefix);
      await expect(row).toContainText(`Edited ${prefix}`);
      await row.getByRole("button", { name: "Duplicate", exact: true }).click();
      await expect(
        page.getByRole("heading", { name: `${prefix} Copy`, exact: true }),
      ).toBeVisible();
      await row
        .getByRole("button", { name: "Copy to Project", exact: true })
        .click();
      await choose(page, "Target project", prefix);
      await page.getByRole("button", { name: "Confirm Copy" }).click();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await choose(page, "Scope filter", "Global");
      await row.getByRole("button", { name: "Delete", exact: true }).click();
      await page.getByRole("button", { name: "Confirm Delete" }).click();
      await expect(row).toHaveCount(0);
      await page.getByLabel("Show deleted templates").check();
      await row.getByRole("button", { name: "Restore", exact: true }).click();
      await expect(
        row.getByRole("button", { name: "Edit", exact: true }),
      ).toBeVisible();
      await page.screenshot({
        path: `test-results/phase6-template-library-${theme}-${width}.png`,
      });
      await page.goto(`/projects/${project.id}/prompt-templates`);
      await page.getByRole("button", { name: "Create Template" }).click();
      await expect(
        page.getByRole("combobox", { name: "Template scope", exact: true }),
      ).toContainText("Project");
      await editor
        .getByLabel("Name", { exact: true })
        .fill(`${prefix} project`);
      await content.fill("项目模板 {{shot_code}}\n{{shot_context}}");
      await editor.getByRole("button", { name: "Save Template" }).click();
      await expect(editor.getByRole("status")).toHaveText("Saved");
      await editor.getByRole("button", { name: "Close", exact: true }).click();
      await page.getByLabel("Search templates").fill(prefix);
      await choose(page, "Scope filter", "Project");
      await expect(page.locator(".template-row")).toHaveCount(2);
      await noOverflow(page);
      expect(errors).toEqual([]);
    });
  }
}

test("editor validation and unsaved protection", async ({ page }) => {
  await page.goto("/prompt-templates");
  await page.getByRole("button", { name: "Create Template" }).click();
  const editor = page.getByRole("dialog", {
    name: "Template Editor",
    exact: true,
  });
  await editor
    .getByLabel("Name", { exact: true })
    .fill(`Invalid ${Date.now()}`);
  await editor.getByLabel("Template Content").fill("{{main_aciton}}");
  await editor.getByRole("button", { name: "Save Template" }).click();
  await expect(editor.getByRole("alert")).toContainText(
    "Unknown placeholder: main_aciton",
  );
  await expect(editor.getByRole("status")).toHaveText("Save failed");
  await editor.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("button", { name: "Stay", exact: true }).click();
  await expect(editor.getByLabel("Template Content")).toHaveValue(
    "{{main_aciton}}",
  );
  await editor.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("button", { name: "Discard and Close" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

for (const theme of ["dark", "light"] as const) {
  test(`shot template picker ${theme}`, async ({ page, request }) => {
    const prefix = `Picker ${theme} ${Date.now()}`;
    const post = async (url: string, data: object) => {
      const r = await request.post(`/api${url}`, { data });
      expect(r.ok()).toBeTruthy();
      return r.json();
    };
    const p = await post("/projects", { name: prefix });
    const other = await post("/projects", { name: `${prefix} other` });
    const script = await post(`/projects/${p.id}/scripts`, { name: "Script" });
    const scene = await post(`/projects/${p.id}/scenes`, {
      script_id: script.id,
      name: "Scene",
    });
    const shot = await post(`/scenes/${scene.id}/shots`, {
      project_id: p.id,
      shot_code: "S13",
      title: "风淋",
    });
    const base = {
      category: "VIDEO_GENERATION",
      template_content:
        "【参考】{{shot_code}}\n{{main_action}}\n<script>plain text</script>",
    };
    await post("/prompt-templates", {
      ...base,
      scope: "GLOBAL",
      name: `${prefix} Global`,
    });
    await post("/prompt-templates", {
      ...base,
      scope: "PROJECT",
      project_id: p.id,
      name: `${prefix} Project`,
    });
    await post("/prompt-templates", {
      ...base,
      scope: "PROJECT",
      project_id: other.id,
      name: `${prefix} hidden`,
    });
    const before = await (await request.get(`/api/shots/${shot.id}`)).json();
    await page.setViewportSize({ width: 1024, height: 900 });
    await page.goto(`/shots/${shot.id}/workspace`);
    if (theme === "light")
      await page.getByRole("button", { name: "切换到浅色模式" }).click();
    await page.getByRole("button", { name: "Browse Templates" }).click();
    const picker = page.getByRole("dialog", { name: "Prompt Template Picker" });
    await picker.getByLabel("Search templates").fill(prefix);
    await choose(page, "Category filter", "Video Generation");
    await expect(picker.locator(".template-row")).toHaveCount(2);
    await picker
      .getByRole("button", { name: "Preview Template", exact: true })
      .first()
      .click();
    await picker.getByRole("button", { name: "Preview", exact: true }).click();
    await expect(picker.locator(".template-preview pre")).toContainText("S13");
    await picker
      .getByRole("button", { name: "Select Template", exact: true })
      .first()
      .click();
    await expect(
      picker.getByRole("button", { name: "Selected", exact: true }),
    ).toBeVisible();
    await noOverflow(page);
    await page.screenshot({
      path: `test-results/phase6-shot-template-picker-${theme}-1024.png`,
    });
    await picker.getByRole("button", { name: "关闭", exact: true }).click();
    expect(await (await request.get(`/api/shots/${shot.id}`)).json()).toEqual(
      before,
    );
    await page.reload();
    await expect(page.getByText("已选择模板 · 仅本次浏览")).toHaveCount(0);
  });
}
