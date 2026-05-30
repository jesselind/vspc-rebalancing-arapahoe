import { readFile } from "node:fs/promises";
import path from "node:path";
import { getCloudflareContext } from "@opennextjs/cloudflare";
import { MAP_ASSET_PATH, MAP_FILE_NAME, resolveMapDownloadPath } from "./downloads";

async function readMapFromDisk(): Promise<Uint8Array | null> {
  const candidates = [
    resolveMapDownloadPath(),
    path.join("/bundle/content/maps", MAP_FILE_NAME),
    path.join("/bundle", MAP_FILE_NAME),
  ];

  for (const filePath of candidates) {
    try {
      return new Uint8Array(await readFile(filePath));
    } catch {
      // try next path
    }
  }

  return null;
}

/** Stream from Workers static assets (production). */
export async function fetchMapPdfFromAssets(): Promise<Response | null> {
  try {
    const { env } = await getCloudflareContext({ async: true });
    if (!env.ASSETS) {
      return null;
    }

    const response = await env.ASSETS.fetch(
      new Request(`https://cei.internal/${MAP_ASSET_PATH}`, { method: "GET" }),
    );
    return response.ok ? response : null;
  } catch {
    return null;
  }
}

export async function loadMapPdfBytes(): Promise<Uint8Array> {
  const fromDisk = await readMapFromDisk();
  if (fromDisk) {
    return fromDisk;
  }

  const fromAssets = await fetchMapPdfFromAssets();
  if (fromAssets) {
    return new Uint8Array(await fromAssets.arrayBuffer());
  }

  throw new Error("Map PDF not found in worker bundle or assets.");
}
