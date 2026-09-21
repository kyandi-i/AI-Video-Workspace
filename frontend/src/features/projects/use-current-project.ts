import { useOutletContext } from "react-router-dom";
import type { Project } from "./types";
export const useCurrentProject = () => useOutletContext<Project>();
