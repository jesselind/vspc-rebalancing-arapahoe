import { PROJECT_REPO_SLUG } from "@/lib/project-repo";

/** Map PDF filename when saving a copy. */
export const MAP_PDF_FILENAME = "full-county-1_50000.pdf";

/** Upstream bytes on GitHub (octet-stream there; proxied with application/pdf). */
export const MAP_PDF_SOURCE_URL = `https://raw.githubusercontent.com/${PROJECT_REPO_SLUG}/main/web/content/maps/full-county-1_50000.pdf`;

/** Inline PDF in a new browser tab. */
export const MAP_PDF_OPEN_URL = "/api/map-pdf";

/** Save-as download via same proxy with attachment disposition. */
export const MAP_PDF_DOWNLOAD_URL = "/api/map-pdf?disposition=attachment";
