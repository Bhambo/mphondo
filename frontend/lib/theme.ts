export const Colors = {
  mz: {
    primary: "#E53935",
    primaryDark: "#C62828",
    primaryLight: "#EF9A9A",
    accent: "#FF7043",
    tint: "rgba(229,57,53,0.12)",
  },
  es: {
    primary: "#2D7AF6",
    primaryDark: "#1D4ED8",
    primaryLight: "#93C5FD",
    accent: "#38BDF8",
    tint: "rgba(45,122,246,0.12)",
  },
  surface: {
    bg: "#0F0F14",
    level1: "#16161D",
    level2: "#1E1E28",
    level3: "#26263A",
    border: "#2E2E40",
    borderFaint: "#1E1E2A",
  },
  ink: {
    primary: "#F2F2F7",
    muted: "#8E8EA0",
    faint: "#4A4A5A",
  },
  positive: "#22C55E",
  negative: "#EF4444",
  warning: "#F59E0B",
} as const;

export type ModuleType = "mz" | "es";

export function moduleColors(module: ModuleType) {
  return Colors[module];
}

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const Radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  pill: 9999,
} as const;

export const Typography = {
  displayLg: { fontSize: 32, fontWeight: "700" as const, letterSpacing: -0.5 },
  displaySm: { fontSize: 24, fontWeight: "700" as const, letterSpacing: -0.3 },
  headingLg: { fontSize: 20, fontWeight: "600" as const },
  headingSm: { fontSize: 17, fontWeight: "600" as const },
  bodyLg: { fontSize: 16, fontWeight: "400" as const, lineHeight: 24 },
  bodySm: { fontSize: 14, fontWeight: "400" as const, lineHeight: 20 },
  caption: { fontSize: 12, fontWeight: "400" as const, lineHeight: 16 },
  mono: { fontSize: 15, fontFamily: "JetBrainsMono" },
} as const;
