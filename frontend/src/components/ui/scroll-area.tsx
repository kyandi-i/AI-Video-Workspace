import * as Primitive from "@radix-ui/react-scroll-area";
import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function ScrollArea({
  className,
  children,
  ...props
}: ComponentProps<typeof Primitive.Root>) {
  return (
    <Primitive.Root className={cn("ui-scroll-area", className)} {...props}>
      <Primitive.Viewport className="scroll-viewport">
        {children}
      </Primitive.Viewport>
      <Primitive.Scrollbar orientation="vertical" className="scrollbar">
        <Primitive.Thumb className="scroll-thumb" />
      </Primitive.Scrollbar>
      <Primitive.Scrollbar orientation="horizontal" className="scrollbar">
        <Primitive.Thumb className="scroll-thumb" />
      </Primitive.Scrollbar>
      <Primitive.Corner />
    </Primitive.Root>
  );
}
