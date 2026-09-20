import type { ComponentProps } from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn("ui-input", className)} {...props} />;
}
export function SearchInput({ className, ...props }: ComponentProps<"input">) {
  return (
    <div className={cn("search-input", className)}>
      <Search aria-hidden="true" />
      <Input type="search" {...props} />
    </div>
  );
}
