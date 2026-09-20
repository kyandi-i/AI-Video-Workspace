import { createBrowserRouter, Link } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { Button } from "@/components/ui/button";

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: "/", element: <DashboardPage /> },
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
