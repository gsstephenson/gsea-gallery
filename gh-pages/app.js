import { gunzipSync, strFromU8 } from "https://cdn.jsdelivr.net/npm/fflate@0.8.2/esm/browser.js";

const statusEl = document.getElementById("status");
const progressEl = document.getElementById("progress");
const loaderEl = document.getElementById("loader");
const iframeEl = document.getElementById("viewer");
const retryBtn = document.getElementById("retry");
const downloadLink = document.getElementById("download-link");

let blobUrl = null;

async function loadConfig() {
  try {
    const response = await fetch(`config.json?cache-bust=${Date.now()}`);
    if (!response.ok) {
      throw new Error(`Config HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.warn("Falling back to defaults; failed to load config.json", error);
    return {};
  }
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "";
  const units = ["B", "KB", "MB", "GB"];
  const exp = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** exp).toFixed(exp === 0 ? 0 : 1)} ${units[exp]}`;
}

function mergeChunks(chunks, totalLength) {
  if (totalLength === 0) {
    return new Uint8Array(0);
  }
  const merged = new Uint8Array(totalLength);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }
  return merged;
}

async function fetchCompressed(url) {
  const response = await fetch(url, {
    headers: {
      "Accept": "application/octet-stream"
    },
    redirect: "follow"
  });

  if (!response.ok) {
    throw new Error(`Download failed: ${response.status} ${response.statusText}`);
  }

  const contentLength = Number(response.headers.get("content-length"));
  const reader = response.body?.getReader?.();

  if (!reader) {
    const buffer = await response.arrayBuffer();
    return {
      bytes: new Uint8Array(buffer),
      contentLength: buffer.byteLength
    };
  }

  const chunks = [];
  let received = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    if (value) {
      chunks.push(value);
      received += value.length;
      if (Number.isFinite(contentLength)) {
        const pct = ((received / contentLength) * 100).toFixed(1);
        progressEl.textContent = `${pct}%`; // update inline progress
        statusEl.textContent = `Downloading (${pct}%, ${formatBytes(received)} of ${formatBytes(contentLength)})…`;
      } else {
        statusEl.textContent = `Downloading (${formatBytes(received)})…`;
      }
    }
  }

  const totalLength = Number.isFinite(contentLength)
    ? contentLength
    : chunks.reduce((acc, chunk) => acc + chunk.length, 0);

  progressEl.textContent = "100%";

  return {
    bytes: mergeChunks(chunks, totalLength),
    contentLength: totalLength
  };
}

async function bootstrap() {
  loaderEl.setAttribute("aria-hidden", "false");
  retryBtn.hidden = true;
  retryBtn.disabled = true;
  progressEl.textContent = "0%";
  statusEl.textContent = "Loading configuration…";

  const config = await loadConfig();
  const params = new URLSearchParams(window.location.search);

  const releaseUrl = params.get("source") || config.releaseUrl;

  if (!releaseUrl || /REPLACE_WITH_TAG/.test(releaseUrl)) {
    statusEl.textContent = "Configuration required: update config.json with your release asset URL.";
    loaderEl.setAttribute("aria-hidden", "true");
    retryBtn.hidden = false;
    retryBtn.disabled = false;
    return;
  }

  downloadLink.href = releaseUrl;
  if (config.assetFriendlyName) {
    downloadLink.download = `${config.assetFriendlyName}.html.gz`;
    downloadLink.textContent = `Download ${config.assetFriendlyName}`;
  }

  try {
    statusEl.textContent = "Requesting release asset…";
    const { bytes } = await fetchCompressed(releaseUrl);

    statusEl.textContent = "Decompressing payload…";
    const decompressed = gunzipSync(bytes);
    const html = strFromU8(decompressed);

    if (blobUrl) {
      URL.revokeObjectURL(blobUrl);
    }

    blobUrl = URL.createObjectURL(new Blob([html], { type: "text/html" }));
    iframeEl.src = blobUrl;

    loaderEl.setAttribute("aria-hidden", "true");
    statusEl.textContent = "Gallery loaded.";
  } catch (error) {
    console.error(error);
    loaderEl.setAttribute("aria-hidden", "true");
    statusEl.textContent = `Failed to load gallery: ${error.message}`;
    retryBtn.hidden = false;
    retryBtn.disabled = false;
  }
}

retryBtn.addEventListener("click", bootstrap);

window.addEventListener("beforeunload", () => {
  if (blobUrl) {
    URL.revokeObjectURL(blobUrl);
  }
});

bootstrap();
