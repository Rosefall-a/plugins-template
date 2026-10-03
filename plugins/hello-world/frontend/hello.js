"use strict";
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
