import * as Primitive from "@radix-ui/react-dialog";
import type { ComponentProps } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Dialog = Primitive.Root;
export const DialogTrigger = Primitive.Trigger;
export const DialogClose = Primitive.Close;
export function DialogTitle({
  className,
  ...props
}: ComponentProps<typeof Primitive.Title>) {
  return (
    <Primitive.Title className={cn("dialog-title", className)} {...props} />
  );
}
export function DialogDescription({
  className,
  ...props
}: ComponentProps<typeof Primitive.Description>) {
  return (
    <Primitive.Description
      className={cn("dialog-description", className)}
      {...props}
    />
  );
}
export function DialogHeader({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("dialog-header", className)} {...props} />;
}
export function DialogFooter({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("dialog-footer", className)} {...props} />;
}
export function DialogContent({
  className,
  children,
  ...props
}: ComponentProps<typeof Primitive.Content>) {
  return (
    <Primitive.Portal>
      <Primitive.Overlay className="ui-overlay" />
      <Primitive.Content className={cn("ui-dialog", className)} {...props}>
        {children}
        <Primitive.Close
          className="ui-button button-ghost button-icon dialog-close"
          aria-label="关闭"
        >
          <X size={16} />
        </Primitive.Close>
      </Primitive.Content>
    </Primitive.Portal>
  );
}
