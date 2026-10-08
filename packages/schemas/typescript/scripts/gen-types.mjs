// Generates TypeScript types from packages/schemas/json/*.schema.json (impl plan 0.4 / 4.3:
// "Generate Python and TypeScript types from the JSON Schemas; do not maintain competing
// handwritten models."). This is the TS half of scripts/gen_types.py's Python generation --
// same source directory, same exclusion rule, same model-name derivation, so the two never
// drift into different conventions.
//
// Usage:
//   node scripts/gen-types.mjs          regenerate packages/schemas/typescript/src/*.ts
//   node scripts/gen-types.mjs --check  regenerate into memory and fail if any output differs
//                                       from what is committed (mirrors
//                                       test_phase0_generated_types.py's up-to-date check)

import { compile } from "json-schema-to-typescript";
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..", "..", "..", "..");
const SCHEMA_DIR = path.join(ROOT, "packages/schemas/json");
const OUT_DIR = path.join(__dirname, "..", "src");

// Mirrors scripts/gen_types.py SKIP: _identity.schema.json is a $ref-only fragment, not a
// standalone artifact.
const SKIP = new Set(["_identity.schema.json"]);

const HEADER = (schemaRelPath) =>
  `// AUTO-GENERATED from ${schemaRelPath} by packages/schemas/typescript/scripts/gen-types.mjs\n` +
  `// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).\n\n`;

async function main() {
  const checkMode = process.argv.includes("--check");
  mkdirSync(OUT_DIR, { recursive: true });

  const schemaFiles = readdirSync(SCHEMA_DIR)
    .filter((f) => f.endsWith(".schema.json") && !SKIP.has(f))
    .sort();

  let mismatched = [];
  for (const file of schemaFiles) {
    const schemaPath = path.join(SCHEMA_DIR, file);
    const schema = JSON.parse(readFileSync(schemaPath, "utf-8"));
    // model name: strip ".schema.json" the same way scripts/gen_types.py does
    // (schema.stem.replace(".schema", "") on the "*.schema" stem)
    const modelName = file.replace(/\.schema\.json$/, "");
    const pascalName = modelName
      .split(/[_\-]/)
      .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
      .join("");

    const ts = await compile(schema, pascalName, {
      bannerComment: "",
      additionalProperties: false,
      style: { semi: true, singleQuote: false },
    });
    const outFile = path.join(OUT_DIR, `${modelName}.ts`);
    const fullContent = HEADER(`packages/schemas/json/${file}`) + ts;

    if (checkMode) {
      const existing = existsSync(outFile) ? readFileSync(outFile, "utf-8") : null;
      if (existing !== fullContent) mismatched.push(modelName);
    } else {
      writeFileSync(outFile, fullContent);
      console.log(`generated packages/schemas/typescript/src/${modelName}.ts`);
    }
  }

  if (checkMode) {
    if (mismatched.length > 0) {
      console.error(`Out of date / missing TypeScript types: ${mismatched.join(", ")}`);
      console.error("Run: pnpm --filter @shorts-maker/schemas-typescript generate");
      process.exit(1);
    }
    console.log(`All ${schemaFiles.length} TypeScript types are up to date.`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
