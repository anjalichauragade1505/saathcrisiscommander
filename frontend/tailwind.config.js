/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bgmain: "#0B0F1A",
        panel: "#111827",
        panelborder: "rgba(34,211,238,0.15)",
        cyan: { DEFAULT: "#22D3EE" },
        violet: { DEFAULT: "#8B5CF6" },
        critical: "#EF4444",
        high: "#F59E0B",
        moderate: "#EAB308",
        safe: "#22C55E",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
