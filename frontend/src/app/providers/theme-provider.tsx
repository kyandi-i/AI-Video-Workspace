import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useState,
  type PropsWithChildren,
} from "react";
import { THEME_KEY, ThemeContext, type Theme } from "@/lib/theme";

export function ThemeProvider({ children }: PropsWithChildren) {
  const [theme, updateTheme] = useState<Theme>(() =>
    document.documentElement.dataset.theme === "light" ? "light" : "dark",
  );
  const setTheme = useCallback((value: Theme) => {
    updateTheme(value);
    try {
      localStorage.setItem(THEME_KEY, value);
    } catch {
      /* A blocked preference store must not break the UI. */
    }
  }, []);
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    const meta = document.querySelector('meta[name="theme-color"]');
    meta?.setAttribute(
      "content",
      getComputedStyle(document.documentElement)
        .getPropertyValue("--background")
        .trim(),
    );
  }, [theme]);
  useEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key === THEME_KEY)
        updateTheme(event.newValue === "light" ? "light" : "dark");
    };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
