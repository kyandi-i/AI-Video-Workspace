import { Toaster as Sonner } from "sonner";
import { CircleCheck, CircleAlert, Info, LoaderCircle } from "lucide-react";
import { useTheme } from "@/lib/theme";

export function Toaster() {
  const { theme } = useTheme();
  return (
    <Sonner
      theme={theme}
      position="bottom-right"
      closeButton
      icons={{
        success: <CircleCheck size={16} />,
        error: <CircleAlert size={16} />,
        info: <Info size={16} />,
        loading: <LoaderCircle size={16} />,
      }}
      toastOptions={{ className: "workspace-toast" }}
    />
  );
}
