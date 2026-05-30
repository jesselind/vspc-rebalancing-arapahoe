import { copyFile, mkdir } from "node:fs/promises";
import path from "node:path";

const webRoot = process.cwd();
const source = path.join(webRoot, "content", "maps", "full-county-1_50000.pdf");
const assetsDir = path.join(webRoot, ".open-next", "assets");
const dest = path.join(assetsDir, "cei-map.pdf");

await mkdir(assetsDir, { recursive: true });
await copyFile(source, dest);
console.log(`Staged map PDF for Workers ASSETS at .open-next/assets/cei-map.pdf`);
