import { vi } from "vitest";

/**
 * Blockiert jeden echten Netzwerkzugriff (XMLHttpRequest und fetch) und protokolliert Versuche.
 * Damit lässt sich nachweisen, dass der Demo-Modus ohne Backend-Requests auskommt.
 */
export function blockNetwork() {
  const attempts: string[] = [];

  class BlockedXMLHttpRequest {
    open(method: string, url: string) {
      attempts.push(`${method.toUpperCase()} ${url}`);
      throw new Error("Netzwerkzugriff im Test blockiert");
    }
  }

  vi.stubGlobal("XMLHttpRequest", BlockedXMLHttpRequest);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      attempts.push(`FETCH ${String(input)}`);
      throw new Error("Netzwerkzugriff im Test blockiert");
    }),
  );

  return attempts;
}
