// The move runner. Every creature move is a one-shot with a fixed length and named key frames (data/moves.js, generated
// from the same table that builds the animation and its sound cues). `perform` sets the creature's `studio:anim`
// property: the client's animation controller enters that move's state and plays the animation from frame 0; the script
// runs the effect of each key frame on the same tick the animation reaches it, then clears the property.
import { MOVES } from "../data/moves.js";
import { now, valid, later, prop, setProp, safe, effect } from "./util.js";

const running = new Map();   // creature id -> { name, token, entity, start, until, tick }
let seq = 0;

export const moveSpec = (e, name) => MOVES[e.typeId.replace("studio:", "")]?.[name];
export const busy = (e) => { const r = running.get(e.id); return !!r && now() < r.until; };
export const currentMove = (e) => { const r = running.get(e.id); return r && now() < r.until ? r.name : undefined; };
/** Ticks since the running move started. */
export const elapsed = (e) => { const r = running.get(e.id); return r ? now() - r.start : 0; };

/**
 * Start a move. `on` maps key-frame names of the move (hit, bite, grab, release...) to functions called with
 * (creature, index) - index counts through frames that come as a list (two bites). `on.start`, `on.tick(creature, t)`
 * and `on.done` are called when the move starts, every tick while it runs, and when it ends.
 * Returns false when the creature is already busy (unless `force`).
 */
export function perform(e, name, on = {}, { force = false, still = true } = {}) {
  const spec = moveSpec(e, name);
  if (!spec) throw new Error(`no move ${e?.typeId}.${name}`);
  if (!valid(e) || (busy(e) && !force)) return false;
  const token = ++seq, start = now();
  running.set(e.id, { name, token, entity: e, start, until: start + spec.len, tick: on.tick });
  setProp(e, "studio:anim", name);
  if (still) effect(e, "slowness", spec.len + 2, 6);     // creatures stand still while they act
  const alive = () => valid(e) && running.get(e.id)?.token === token;
  if (on.start) safe(`${name}.start`, () => on.start(e));
  for (const [key, fn] of Object.entries(on)) {
    if (key === "start" || key === "tick" || key === "done") continue;
    const frames = spec[key];
    if (frames === undefined) throw new Error(`move ${e.typeId}.${name} has no key frame '${key}'`);
    (Array.isArray(frames) ? frames : [frames]).forEach((t, i) => later(t, () => { if (alive()) fn(e, i); }));
  }
  later(spec.len, () => {
    if (!valid(e)) return;
    if (running.get(e.id)?.token !== token) return;
    running.delete(e.id);
    if (prop(e, "studio:anim", "none") === name) setProp(e, "studio:anim", "none");
    if (on.done) safe(`${name}.done`, () => on.done(e));
  });
  return true;
}

/** Stop whatever a creature is doing (it died, was removed, or something else took over). */
export function cancel(e) {
  if (!e || !running.has(e.id)) return;
  running.delete(e.id);
  if (valid(e) && prop(e, "studio:anim", "none") !== "none") setProp(e, "studio:anim", "none");
}

/** Per-tick callbacks of running moves. */
export function tickMoves() {
  for (const [id, r] of running) {
    if (!valid(r.entity)) { running.delete(id); continue; }
    if (r.tick) safe(`${r.name}.tick`, () => r.tick(r.entity, now() - r.start));
  }
}
