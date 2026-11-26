import { copyFile, cp, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(scriptDir, "..");
const source = resolve(webRoot, "..", "docs", "feed.json");
const target = resolve(webRoot, "public", "feed.json");

await mkdir(dirname(target), { recursive: true });
await copyFile(source, target);
for (const name of ["morning-edition.json", "morning-edition.xml", "morning-archive.json", "editions", "intelligence.json", "research-trends.json"]) {
  try {
    await cp(resolve(source, "..", name), resolve(target, "..", name), { recursive: true });
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
}
