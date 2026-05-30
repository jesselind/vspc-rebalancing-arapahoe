/** Path fragments commonly probed by scanners; CEI does not serve any of these. */
const PROBE_PATH_MARKERS = [
  "wp-",
  "wordpress",
  "phpmyadmin",
  "/.env",
  "/.git",
  "/cgi-bin/",
] as const;

export function isProbePath(pathname: string): boolean {
  const path = pathname.toLowerCase();
  if (path === "/xmlrpc.php") {
    return true;
  }
  return PROBE_PATH_MARKERS.some((marker) => path.includes(marker));
}
