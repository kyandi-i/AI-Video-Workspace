import { createBrowserRouter, Link } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { Button } from "@/components/ui/button";
import { SettingsPage } from "@/features/settings/settings-page";

export const router = createBrowserRouter([
  ...(import.meta.env.DEV
    ? [{ path: "/__ui", lazy: () => import("@/dev/ui-preview") }]
    : []),
  {
    element: <AppShell />,
    children: [
      { path: "/", element: <DashboardPage /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "/assets", lazy: () => import("@/features/assets/assets-page") },
      {
        path: "/projects",
        lazy: () => import("@/features/projects/projects-page"),
      },
      {
        path: "/projects/:projectId",
        lazy: () => import("@/features/projects/project-layout"),
        children: [
          {
            path: "characters",
            lazy: () => import("@/features/characters/characters-page"),
          },
          {
            path: "characters/:characterId",
            lazy: () => import("@/features/characters/character-detail"),
          },
          {
            index: true,
            lazy: () => import("@/features/projects/project-overview"),
          },
          {
            path: "script",
            lazy: () => import("@/features/scripts/script-page"),
          },
          {
            path: "scenes",
            lazy: () => import("@/features/scenes/scenes-page"),
          },
          { path: "shots", lazy: () => import("@/features/shots/shots-page") },
          {
            path: "assets",
            lazy: () => import("@/features/assets/assets-page"),
          },
        ],
      },
      {
        path: "/shots/:shotId",
        lazy: () => import("@/features/shots/shot-detail"),
      },
      {
        path: "*",
        element: (
          <div className="not-found">
            <h1>页面不存在</h1>
            <p>这个地址暂时没有对应的页面。</p>
            <Button asChild>
              <Link to="/">返回概览</Link>
            </Button>
          </div>
        ),
      },
    ],
  },
]);
