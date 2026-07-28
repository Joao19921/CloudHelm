import { cp, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const dist = join(root, "dist");
await mkdir(dist, { recursive: true });
for (const file of [".nojekyll", "config.js", "styles.css", "demo.html", "backoffice.html", "backoffice.js", "assets"]) {
  await cp(join(root, "..", "frontend", file), join(dist, file), { recursive: true });
}