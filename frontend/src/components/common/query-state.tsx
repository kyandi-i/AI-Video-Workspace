import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type QueryState = {
  isPending: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => unknown;
};
export function QueryState({ queries }: { queries: QueryState[] }) {
  const failed = queries.find((query) => query.isError);
  if (failed)
    return (
      <div className="error-banner" role="alert">
        {failed.error?.message}
        <Button variant="secondary" onClick={() => void failed.refetch()}>
          重试
        </Button>
      </div>
    );
  return (
    <div className="workflow-loading" aria-label="加载中">
      {[0, 1, 2].map((index) => (
        <Skeleton key={index} className="workflow-skeleton" />
      ))}
    </div>
  );
}
