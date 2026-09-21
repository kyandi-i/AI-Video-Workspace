import * as Primitive from "@radix-ui/react-select";
import type { ComponentProps } from "react";
import { Check, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

export const Select = Primitive.Root;
export function SelectValue({
  className,
  ...props
}: ComponentProps<typeof Primitive.Value>) {
  // Radix deliberately ignores className/style on Value and ItemText.
  // Own the layout outside those primitives while preserving their text portal.
  return (
    <span className={cn("select-value", className)}>
      <Primitive.Value {...props} />
    </span>
  );
}
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
      <Primitive.Icon className="select-icon">
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
        collisionPadding={12}
        className={cn("ui-popover select-content", className)}
        {...props}
      >
        <Primitive.ScrollUpButton className="select-scroll">
          <ChevronUp size={14} />
        </Primitive.ScrollUpButton>
        <Primitive.Viewport className="select-viewport">
          {children}
        </Primitive.Viewport>
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
      <span
        className="select-item-text"
        title={typeof children === "string" ? children : undefined}
      >
        <Primitive.ItemText>{children}</Primitive.ItemText>
      </span>
      <Primitive.ItemIndicator className="select-indicator">
        <Check size={14} />
      </Primitive.ItemIndicator>
    </Primitive.Item>
  );
}
