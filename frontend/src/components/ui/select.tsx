import * as Primitive from "@radix-ui/react-select";
import type { ComponentProps } from "react";
import { Check, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

export const Select = Primitive.Root;
export const SelectValue = Primitive.Value;
export function SelectTrigger({
  className,
  children,
  ...props
}: ComponentProps<typeof Primitive.Trigger>) {
  return (
    <Primitive.Trigger
      className={cn("ui-input select-trigger", className)}
      {...props}
    >
      {children}
      <Primitive.Icon>
        <ChevronDown size={14} />
      </Primitive.Icon>
    </Primitive.Trigger>
  );
}
export function SelectContent({
  className,
  children,
  ...props
}: ComponentProps<typeof Primitive.Content>) {
  return (
    <Primitive.Portal>
      <Primitive.Content
        position="popper"
        sideOffset={5}
        className={cn("ui-popover select-content", className)}
        {...props}
      >
        <Primitive.ScrollUpButton className="select-scroll">
          <ChevronUp size={14} />
        </Primitive.ScrollUpButton>
        <Primitive.Viewport>{children}</Primitive.Viewport>
        <Primitive.ScrollDownButton className="select-scroll">
          <ChevronDown size={14} />
        </Primitive.ScrollDownButton>
      </Primitive.Content>
    </Primitive.Portal>
  );
}
export function SelectItem({
  className,
  children,
  ...props
}: ComponentProps<typeof Primitive.Item>) {
  return (
    <Primitive.Item className={cn("select-item", className)} {...props}>
      <Primitive.ItemText>{children}</Primitive.ItemText>
      <Primitive.ItemIndicator>
        <Check size={14} />
      </Primitive.ItemIndicator>
    </Primitive.Item>
  );
}
