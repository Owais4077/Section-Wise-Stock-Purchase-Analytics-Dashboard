import assert from "node:assert/strict";
import test from "node:test";
import fs from "node:fs";

test("project is a Next.js app and does not expose a Python Vercel entrypoint", () => {
  assert.equal(fs.existsSync("app.py"), false);
  assert.equal(fs.existsSync("package.json"), true);
  const packageJson = JSON.parse(fs.readFileSync("package.json", "utf8"));
  assert.equal(packageJson.scripts.build, "next build");
});
