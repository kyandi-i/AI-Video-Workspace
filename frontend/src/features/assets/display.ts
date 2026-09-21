import { enumOptions, type EnumDisplay } from "@/lib/enum-display";
import { assetTypes, type Asset, type AssetType } from "./types";
export const assetDisplay = {
  IMAGE: { label: "Image", tone: "neutral" },
  VIDEO: { label: "Video", tone: "accent" },
  STORYBOARD_6GRID: { label: "Storyboard 6-Grid", tone: "neutral" },
  OTHER: { label: "Other", tone: "neutral" },
} satisfies Record<AssetType, EnumDisplay>;
export const assetTypeOptions = enumOptions(assetTypes, assetDisplay);
export const sizeLabel = (bytes: number) =>
  bytes < 1024 * 1024
    ? `${(bytes / 1024).toFixed(1)} KiB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MiB`;
export const dimensions = (asset: Asset) =>
  `${asset.width ?? "—"} × ${asset.height ?? "—"}${asset.duration_seconds !== null ? ` · ${asset.duration_seconds.toFixed(1)}s` : ""}`;
