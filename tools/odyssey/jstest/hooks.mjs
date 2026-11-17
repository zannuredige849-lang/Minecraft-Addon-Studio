// Module hooks: the add-on imports "@minecraft/server", which only exists inside the game; point it at the mock.
const MOCK = new URL("./server_mock.mjs", import.meta.url).href;
export async function resolve(specifier, context, next) {
  if (specifier === "@minecraft/server") return { url: MOCK, shortCircuit: true };
  return next(specifier, context);
}
export async function load(url, context, next) {
  if (url.includes("/BP/scripts/") && url.endsWith(".js")) return next(url, { ...context, format: "module" });
  return next(url, context);
}
