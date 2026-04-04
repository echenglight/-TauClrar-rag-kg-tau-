import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        medBlue: "#0f2747",
        medCyan: "#1fa9c9",
        medLight: "#f5fbff"
      }
    }
  },
  plugins: []
} satisfies Config;
