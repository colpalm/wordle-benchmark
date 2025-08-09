import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      // Allow unescaped apostrophes and quotes in JSX text for better readability
      // Modern React handles escaping automatically, making manual encoding unnecessary
      "react/no-unescaped-entities": "off",
    },
  },
];

export default eslintConfig;
