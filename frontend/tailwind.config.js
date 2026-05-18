/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        // MZ module — Vermelho Maputo
        mz: {
          50: "#FFF0F0",
          100: "#FFDDDD",
          200: "#FFC0C0",
          500: "#E53935",
          600: "#C62828",
          700: "#B71C1C",
        },
        // ES module — Azul Pessoal
        es: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          200: "#BFDBFE",
          500: "#2D7AF6",
          600: "#1D4ED8",
          700: "#1E40AF",
        },
        // Neutral dark background
        surface: {
          DEFAULT: "#0F0F14",
          1: "#16161D",
          2: "#1E1E28",
          3: "#26263A",
          border: "#2E2E40",
        },
        ink: {
          DEFAULT: "#F2F2F7",
          muted: "#8E8EA0",
          faint: "#4A4A5A",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        card: "16px",
        pill: "9999px",
      },
    },
  },
  plugins: [],
};
