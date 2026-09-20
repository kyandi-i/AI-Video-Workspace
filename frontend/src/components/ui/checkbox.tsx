import * as Primitive from "@radix-ui/react-checkbox";
import type { ComponentProps } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export function Checkbox({
  className,
  ...props
}: ComponentProps<typeof Primitive.Root>) {
  return (
    <Primitive.Root className={cn("ui-checkbox", className)} {...props}>
      <Primitive.Indicator>
        <Check size={12} />
      </Primitive.Indicator>
    </Primitive.Root>
  );
}
