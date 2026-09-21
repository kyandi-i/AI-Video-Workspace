import { projectStatuses, type ProjectStatus } from "@/features/projects/types";
import { shotStatuses, type ShotStatus } from "@/features/shots/types";
import { enumOptions, type EnumDisplay } from "./enum-display";

export type WorkflowStatus = ProjectStatus | ShotStatus;
export const statusDisplay = {
  DRAFT: { label: "Draft", tone: "neutral" },
  ACTIVE: { label: "Active", tone: "accent" },
  PAUSED: { label: "Paused", tone: "warning" },
  COMPLETED: { label: "Completed", tone: "success" },
  ARCHIVED: { label: "Archived", tone: "neutral" },
  ASSET_PREPARING: { label: "Asset Preparing", tone: "accent" },
  STORYBOARD_PROMPT_READY: { label: "Storyboard Prompt Ready", tone: "accent" },
  STORYBOARD_READY: { label: "Storyboard Ready", tone: "accent" },
  VIDEO_PROMPT_READY: { label: "Video Prompt Ready", tone: "accent" },
  VIDEO_GENERATING: { label: "Video Generating", tone: "accent" },
  REVIEW: { label: "Review", tone: "warning" },
  DONE: { label: "Done", tone: "success" },
} satisfies Record<WorkflowStatus, EnumDisplay>;

export const projectStatusOptions = enumOptions(projectStatuses, statusDisplay);
export const shotStatusOptions = enumOptions(shotStatuses, statusDisplay);
