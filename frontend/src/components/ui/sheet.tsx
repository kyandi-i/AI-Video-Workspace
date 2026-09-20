import type { ComponentProps } from "react";
import { DialogContent } from "./dialog";
import { cn } from "@/lib/utils";

export {
  Dialog as Sheet,
  DialogTrigger as SheetTrigger,
  DialogClose as SheetClose,
  DialogTitle as SheetTitle,
  DialogDescription as SheetDescription,
  DialogHeader as SheetHeader,
  DialogFooter as SheetFooter,
} from "./dialog";
export function SheetContent({
  className,
  ...props
}: ComponentProps<typeof DialogContent>) {
  return <DialogContent className={cn("ui-sheet", className)} {...props} />;
}
