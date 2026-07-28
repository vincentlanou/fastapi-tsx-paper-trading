/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#0b0f19",
        cardBg: "rgba(18, 24, 38, 0.75)",
        cardBorder: "rgba(255, 255, 255, 0.08)",
        tsxBlue: "#3b82f6",
        bullGreen: "#10b981",
        bearRed: "#ef4444",
        goldWarn: "#f59e0b",
        aiPurple: "#8b5cf6",
      },
    },
  },
  plugins: [],
}
