import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eef6ff",
          100: "#d9eaff",
          200: "#bcdaff",
          300: "#8ec2ff",
          400: "#599eff",
          500: "#3377f6",
          600: "#1d58e3",
          700: "#1746b7",
          800: "#183c94",
          900: "#1a3574",
        },
        accent: {
          50: "#fff8eb",
          100: "#ffedc6",
          200: "#ffd988",
          300: "#ffbf4a",
          400: "#ffa420",
          500: "#f98307",
          600: "#dd5f02",
          700: "#b74206",
          800: "#94330c",
          900: "#7a2b0d",
        },
        ink: {
          50: "#f7f8fa",
          100: "#eef0f4",
          200: "#dde1e9",
          300: "#c2c9d6",
          400: "#9aa5b8",
          500: "#74819a",
          600: "#5b677f",
          700: "#4a5368",
          800: "#3c4354",
          900: "#2c313f",
          950: "#1b1f29",
        },
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(27 31 41 / 0.06), 0 1px 3px 0 rgb(27 31 41 / 0.08)",
        pop: "0 10px 30px -10px rgb(27 31 41 / 0.25)",
      },
      borderRadius: {
        xl: "0.875rem",
      },
    },
  },
  plugins: [],
};

export default config;
