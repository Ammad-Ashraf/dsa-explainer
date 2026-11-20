import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: { ecmaVersion: 2022, globals: globals.browser },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // An effect may only return a cleanup function. Arrow bodies like `() => window.scrollTo(0, 0)` hand React
      // whatever the call returns, which crashed in-app navigation once; block bodies make the intent explicit.
      "no-restricted-syntax": ["error", {
        selector: "CallExpression[callee.name='useEffect'] > ArrowFunctionExpression[body.type!='BlockStatement'][body.type!='ArrowFunctionExpression']",
        message: "Give effects a block body: an effect must return nothing or a cleanup function.",
      }],
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
);
