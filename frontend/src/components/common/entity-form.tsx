import { useId, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { notify } from "@/lib/notifications";

export type Field = {
  name: string;
  label: string;
  required?: boolean;
  kind?: "text" | "textarea" | "number" | "select";
  options?: { value: string; label: string }[];
  maxLength?: number;
};
export type Values = Record<string, string>;

export function Choice({
  label,
  value,
  options,
  onChange,
  id,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  id?: string;
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger id={id} aria-label={label}>
        <SelectValue placeholder="请选择" />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function Form({
  fields,
  initial,
  onSave,
  onClose,
  pending,
  setPending,
}: {
  fields: Field[];
  initial: Values;
  onSave: (values: Values) => Promise<unknown>;
  onClose: () => void;
  pending: boolean;
  setPending: (pending: boolean) => void;
}) {
  const id = useId();
  const [values, setValues] = useState(initial);
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const errors = Object.fromEntries(
    fields.map((field) => {
      const value = values[field.name] ?? "";
      return [
        field.name,
        field.required && !value.trim()
          ? "此项不能为空"
          : field.kind === "number" &&
              (!value.trim() ||
                !Number.isFinite(Number(value)) ||
                Number(value) < 0)
            ? "请输入大于或等于 0 的数值"
            : "",
      ];
    }),
  );
  return (
    <form
      className="entity-form"
      noValidate
      onSubmit={async (event) => {
        event.preventDefault();
        setTouched(
          Object.fromEntries(fields.map((field) => [field.name, true])),
        );
        if (pending || Object.values(errors).some(Boolean)) return;
        setPending(true);
        setError("");
        try {
          await onSave(values);
          notify.success("保存成功");
          onClose();
        } catch (cause) {
          setError(
            cause instanceof Error ? cause.message : "保存失败，请重试。",
          );
        } finally {
          setPending(false);
        }
      }}
    >
      <fieldset disabled={pending} className="form-fields">
        {fields.map((field) => {
          const controlId = `${id}-${field.name}`;
          const props = {
            id: controlId,
            value: values[field.name] ?? "",
            required: field.required,
            maxLength: field.maxLength,
            "aria-invalid": Boolean(touched[field.name] && errors[field.name]),
            "aria-describedby":
              touched[field.name] && errors[field.name]
                ? `${controlId}-error`
                : undefined,
            onBlur: () =>
              setTouched((current) => ({ ...current, [field.name]: true })),
            onChange: (
              event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
            ) => {
              setValues((current) => ({
                ...current,
                [field.name]: event.target.value,
              }));
              setTouched((current) => ({ ...current, [field.name]: true }));
            },
          };
          return (
            <div className="form-field" key={field.name}>
              <label htmlFor={controlId}>
                {field.label}
                {field.required && <span aria-hidden="true"> *</span>}
              </label>
              {field.kind === "select" ? (
                <Choice
                  id={controlId}
                  label={field.label}
                  value={values[field.name] ?? ""}
                  options={field.options ?? []}
                  onChange={(value) =>
                    setValues((current) => ({
                      ...current,
                      [field.name]: value,
                    }))
                  }
                />
              ) : field.kind === "textarea" ? (
                <Textarea {...props} rows={3} />
              ) : (
                <Input
                  {...props}
                  type={field.kind === "number" ? "number" : "text"}
                  min={field.kind === "number" ? 0 : undefined}
                  step={field.kind === "number" ? "any" : undefined}
                />
              )}
              {touched[field.name] && errors[field.name] && (
                <span id={`${controlId}-error`} className="field-error">
                  {errors[field.name]}
                </span>
              )}
            </div>
          );
        })}
      </fieldset>
      {error && (
        <div role="alert" className="error-banner">
          {error}
        </div>
      )}
      <DialogFooter>
        <Button
          type="button"
          variant="secondary"
          disabled={pending}
          onClick={onClose}
        >
          取消
        </Button>
        <Button type="submit" disabled={pending}>
          {pending ? "保存中…" : "保存"}
        </Button>
      </DialogFooter>
    </form>
  );
}

export function EntityForm({
  title,
  fields,
  initial,
  onSave,
  trigger,
}: {
  title: string;
  fields: Field[];
  initial: Values;
  onSave: (values: Values) => Promise<unknown>;
  trigger: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        if (!pending) setOpen(value);
      }}
    >
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent
        closeDisabled={pending}
        onInteractOutside={(event) => event.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            填写基本信息，保存到本地工作空间。
          </DialogDescription>
        </DialogHeader>
        <Form
          fields={fields}
          initial={initial}
          onSave={onSave}
          onClose={() => setOpen(false)}
          pending={pending}
          setPending={setPending}
        />
      </DialogContent>
    </Dialog>
  );
}

export function DeleteEntity({
  name,
  description,
  onDelete,
}: {
  name: string;
  description: string;
  onDelete: () => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        if (!pending) {
          setOpen(value);
          setError("");
        }
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm" variant="ghost" aria-label={`删除 ${name}`}>
          删除
        </Button>
      </DialogTrigger>
      <DialogContent closeDisabled={pending}>
        <DialogHeader>
          <DialogTitle>删除 {name}？</DialogTitle>
          <DialogDescription>
            {description} 数据将保留在本地，删除后从列表中隐藏。
          </DialogDescription>
        </DialogHeader>
        {error && (
          <div role="alert" className="error-banner">
            {error}
          </div>
        )}
        <DialogFooter>
          <Button
            variant="secondary"
            disabled={pending}
            onClick={() => setOpen(false)}
          >
            取消
          </Button>
          <Button
            variant="destructive"
            disabled={pending}
            onClick={async () => {
              setPending(true);
              setError("");
              try {
                await onDelete();
                setOpen(false);
                notify.success("已删除");
              } catch (cause) {
                setError(cause instanceof Error ? cause.message : "删除失败");
              } finally {
                setPending(false);
              }
            }}
          >
            {pending ? "删除中…" : "确认删除"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
