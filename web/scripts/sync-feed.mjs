import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(scriptDir, "..");
const source = resolve(webRoot, "..", "docs", "feed.json");
const target = resolve(webRoot, "public", "feed.json");

await mkdir(dirname(target), { recursive: true });
await copyFile(source, target);
