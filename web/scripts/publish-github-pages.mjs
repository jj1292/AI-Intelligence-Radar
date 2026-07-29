import { cp, mkdir, rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(scriptDirectory, "..");
const repositoryRoot = resolve(webRoot, "..");
const clientRoot = resolve(webRoot, "dist/client");
const docsRoot = resolve(repositoryRoot, "docs");

await mkdir(docsRoot, { recursive: true });
await rm(resolve(docsRoot, "assets"), { recursive: true, force: true });
await cp(resolve(clientRoot, "index.html"), resolve(docsRoot, "index.html"));
await cp(resolve(clientRoot, "assets"), resolve(docsRoot, "assets"), {
  recursive: true,
});

console.log("Published the verified web build into docs/ without replacing feed.xml or feed.json.");
