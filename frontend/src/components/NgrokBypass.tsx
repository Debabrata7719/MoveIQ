"use client";

import { useEffect } from "react";

export function NgrokBypass() {
  useEffect(() => {
    if (typeof window !== "undefined") {
      const originalFetch = window.fetch;
      window.fetch = async (...args) => {
        let [resource, config] = args;
        
        const urlStr = resource instanceof Request ? resource.url : String(resource || "");
        if (urlStr.includes("ngrok")) {
          config = config || {};
          const headers = new Headers(config.headers || (resource instanceof Request ? resource.headers : {}));
          headers.set("ngrok-skip-browser-warning", "true");
          config.headers = headers;
        }
        
        return originalFetch(resource, config);
      };
    }
  }, []);

  return null;
}
