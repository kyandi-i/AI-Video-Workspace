import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";

type QueryState = {
  isPending: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => unknown;
};
export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => unknown;
}) {
  return (
    <div className="error-banner" role="alert">
      <AlertCircle size={18} aria-hidden="true" />
      <div>
        <strong>暂时无法加载</strong>
        <p>{message}</p>
      </div>
      <Button variant="secondary" onClick={() => void onRetry()}>
        重试
      </Button>
    </div>
  );
}
export function QueryState({ queries }: { queries: QueryState[] }) {
  const failed = queries.find((query) => query.isError);
  if (failed)
    return (
      <ErrorState
        message={failed.error?.message ?? "请稍后重试。"}
        onRetry={failed.refetch}
      />
    );
  return (
    <div className="workflow-loading" aria-label="加载中">
      {[0, 1, 2].map((index) => (
        <Skeleton key={index} className="workflow-skeleton" />
      ))}
    </div>
  );
}

// Background failures keep the last successful content and controls on screen.
export function QueryErrors({ queries }: { queries: QueryState[] }) {
  const failed = queries.find((query) => query.isError);
  return failed ? (
    <ErrorState
      message={failed.error?.message ?? "请稍后重试。"}
      onRetry={failed.refetch}
    />
  ) : null;
}
