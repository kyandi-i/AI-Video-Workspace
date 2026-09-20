import { Image } from "lucide-react";
import { useState, type ComponentProps } from "react";
import { Badge } from "@/components/ui/badge";
import { EntityCard } from "./entity-card";

export function MediaCard({
  src,
  alt,
  mediaType,
  aspectRatio = "16/9",
  fit = "cover",
  ...props
}: Omit<ComponentProps<typeof EntityCard>, "preview"> & {
  src?: string;
  alt?: string;
  mediaType: string;
  aspectRatio?: "16/9" | "1/1" | "3/4";
  fit?: "cover" | "contain";
}) {
  const [failedSource, setFailedSource] = useState<string>();
  return (
    <EntityCard
      {...props}
      preview={
        <div className="media-preview" style={{ aspectRatio }}>
          {src && failedSource !== src ? (
            <img
              src={src}
              alt={alt ?? props.name}
              style={{ objectFit: fit }}
              loading="lazy"
              onError={() => setFailedSource(src)}
            />
          ) : (
            <Image size={26} strokeWidth={1.3} aria-hidden="true" />
          )}
          <Badge className="media-type">{mediaType}</Badge>
        </div>
      }
    />
  );
}
