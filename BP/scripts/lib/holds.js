// A victim carried by a creature: pinned, tick by tick, to where the creature's hand, mouth or weapon point is in the
// animation. The positions come from data/moves.js (PATHS), sampled from the animation itself, so what the player sees
// and what the server does are the same motion.
import { PATHS } from "../data/moves.js";
import { now, valid, add, forward, right, effect, safe } from "./util.js";

const holds = new Map();   // victim id -> hold

/** Position [forward, up, right] (blocks from the holder's feet) of a labelled point at tick t of a move. */
export function pathAt(key, label, t) {
  const pts = PATHS[key]?.[label];
  if (!pts || !pts.length) return [0, 0, 0];
  const x = Math.max(0, Math.min(pts.length - 1, t / 2));
  const i = Math.floor(x), k = x - i, a = pts[i], b = pts[Math.min(pts.length - 1, i + 1)];
  return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
}
/** [forward, up, right] -> an offset in the world, for a holder facing where it faces. */
export function worldOffset(holder, [f, u, r]) {
  const F = forward(holder), R = right(holder);
  return { x: F.x * f + R.x * r, y: u, z: F.z * f + R.z * r };
}
/** An `at` function that follows a path of a move, starting `from` ticks into it. */
export const follow = (key, label, from = 0) => (holder, t) => worldOffset(holder, pathAt(key, label, from + t));

export const isHeld = (e) => holds.has(e.id);
export const holdsOf = (holder) => [...holds.values()].filter((h) => h.holder === holder);

/**
 * Pin `victim` to `holder` for `ticks`. `at(holder, t)` is the offset from the holder's feet at tick t of the hold.
 * onTick(victim, holder, t) runs every `every` ticks; onRelease(victim, holder) when the hold ends (or the holder is
 * gone: holder is undefined then). Returns false if the victim is already held.
 */
export function hold(victim, holder, { ticks, at, every, onTick, onRelease }) {
  if (!valid(victim) || !valid(holder) || holds.has(victim.id)) return false;
  holds.set(victim.id, { victim, holder, until: now() + ticks, start: now(), at, every, onTick, onRelease });
  return true;
}
export function release(victim) {
  const h = holds.get(victim?.id);
  if (!h) return;
  holds.delete(victim.id);
  if (valid(victim)) {
    effect(victim, "slow_falling", 60, 0);                    // set down gently: no fall damage from the carry
    if (h.onRelease) safe("hold.release", () => h.onRelease(victim, valid(h.holder) ? h.holder : undefined));
  }
}
export function tickHolds() {
  for (const [id, h] of [...holds]) {
    const { victim, holder } = h;
    if (!valid(victim) || !valid(holder) || now() >= h.until) { release(victim ?? { id }); holds.delete(id); continue; }
    const t = now() - h.start;
    try { victim.teleport(add(holder.location, h.at(holder, t)), { keepVelocity: false }); } catch { }
    if (h.every && t > 0 && t % h.every === 0 && h.onTick) safe("hold.tick", () => h.onTick(victim, holder, t));
  }
}
export function dropAllOf(id) { holds.delete(id); }
