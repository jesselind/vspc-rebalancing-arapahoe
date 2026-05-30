import { cp, mkdir } from "node:fs/promises";
import path from "node:path";

const root = path.resolve(process.cwd(), "..");
const webRoot = process.cwd();

const tasks = [
  {
    from: path.join(root, "output"),
    to: path.join(webRoot, "content", "data"),
  },
  {
    from: path.join(root, "maps"),
    to: path.join(webRoot, "content", "maps"),
  },
];

for (const task of tasks) {
  await mkdir(task.to, { recursive: true });
  await cp(task.from, task.to, { recursive: true });
}

console.log("Static assets synced from ../output and ../maps into ./content.");
