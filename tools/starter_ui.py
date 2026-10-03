"""Deletable starter assets using the host's sandboxed frontend bridge."""

HTML = '''<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>My greeting</title>
<style>
body { font: 1rem system-ui; color: #eee; background: #111; padding: 1rem; }
input, button { font: inherit; padding: .5rem; }
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
'''

JAVASCRIPT = '''"use strict";
const form = document.getElementById("greeting");
const output = document.getElementById("result");
const button = form.querySelector("button");
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
  if (event.source !== parent || !pending || !data ||
      data.type !== "plugin-api-response" || data.requestId !== pending) return;
  finish(typeof data.error === "string" ? data.error :
    typeof data.result?.message === "string" ? data.result.message : "Action completed.");
});
'''
