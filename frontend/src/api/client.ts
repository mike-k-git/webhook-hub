import createClient from "openapi-fetch";
import type { paths } from "./schema";
export const client = createClient<paths>({
  baseUrl: `${window.location.origin}/api`,
  fetch: (request) => globalThis.fetch(request),
});
