"""Deletable starter assets using the host's sandboxed frontend bridge."""

HTML = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>My greeting</title>
<style>
body { font: 1rem var(--ui-font-family, system-ui); color: var(--ui-text, #25262a); background: var(--ui-bg, #f5f5f6); padding: 1rem; }
input, button { font: inherit; padding: .5rem; min-height: 44px; box-sizing: border-box; border: 1px solid var(--ui-border, #95969d); border-radius: var(--ui-radius-control, 8px); }
input { color: var(--ui-text, #25262a); background: var(--ui-surface, #fff); max-width: 100%; }
button { color: var(--ui-on-accent, #18191d); background: var(--ui-accent, #efab54); cursor: pointer; }
button:disabled { cursor: wait; opacity: .65; }
:focus-visible { outline: 2px solid var(--ui-accent, #c07018); outline-offset: 2px; }
* { scrollbar-color: var(--ui-border, #95969d) var(--ui-bg, #f5f5f6); }
label { display: block; margin-bottom: .5rem; }
</style>
<h1>My greeting</h1>
<div id="greeting">
  <label for="name">Your name</label>
  <input id="name" value="world" maxlength="80">
  <button type="button">Say hello</button>
</div>
<p id="result" role="status" aria-live="polite">Ready to greet you.</p>
<script src="hello.js"></script>
</html>
"""

JAVASCRIPT = """"use strict";
const form = document.getElementById("greeting");
const output = document.getElementById("result");
const button = form.querySelector("button");
const themeRequest = "theme-" + Array.from(crypto.getRandomValues(new Uint32Array(4))).join("-");
function appearance(value) {
  if (!value || typeof value.tokens !== "object" || value.tokens === null) return;
  for (const [key, token] of Object.entries(value.tokens)) {
    if (/^--ui-[a-z0-9-]+$/.test(key) && typeof token === "string" && token.length <= 256)
      document.documentElement.style.setProperty(key, token);
  }
  document.documentElement.style.colorScheme = value.mode === "dark" ? "dark" : "light";
}
parent.postMessage({type: "plugin-api-request", requestId: themeRequest, method: "plugin.theme", payload: {}}, "*");
let pending;
let timer;
function finish(message) {
  clearTimeout(timer);
  pending = undefined;
  button.disabled = false;
  output.textContent = message;
}
button.addEventListener("click", () => {
  if (pending) return;
  pending = Array.from(crypto.getRandomValues(new Uint32Array(4))).join("-");
  button.disabled = true;
  output.textContent = "Greeting…";
  timer = setTimeout(() => finish("The host did not respond. Check plugin diagnostics."), 10000);
  parent.postMessage({type: "plugin-api-request", requestId: pending,
    method: "plugin.run-action", payload: {actionId: "greet",
      values: {name: document.getElementById("name").value}}}, "*");
});
window.addEventListener("message", (event) => {
  const data = event.data;
  if (event.source !== parent || !data) return;
  if (data.type === "plugin-appearance-changed") { appearance(data.appearance); return; }
  if (data.type === "plugin-api-response" && data.requestId === themeRequest) { appearance(data.result); return; }
  if (!pending ||
      data.type !== "plugin-api-response" || data.requestId !== pending) return;
  finish(typeof data.error === "string" ? data.error :
    typeof data.result?.message === "string" ? data.result.message : "Action completed.");
});
"""
