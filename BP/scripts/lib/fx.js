// Messages, sounds and particles. Text goes out as translate keys so every player reads the game in their own language
// (English and Russian lang files ship in both packs). Sounds are the add-on's own: odyssey.<creature>.<name>.
import { runCommand, playersNear, add } from "./util.js";

export const msg = (key, ...args) => ({ rawtext: [args.length ? { translate: key, with: args } : { translate: key }] });
export const tell = (p, key, ...args) => { try { p.sendMessage(msg(key, ...args)); } catch { } };
export const bar = (p, key, ...args) => { try { p.onScreenDisplay.setActionBar(msg(key, ...args)); } catch { } };
export const say = (dim, loc, r, key, ...args) => { for (const p of playersNear(dim, loc, r)) tell(p, key, ...args); };
export const title = (p, key, subKey) => {
  try {
    p.onScreenDisplay.setTitle(msg(key), { subtitle: msg(subKey), fadeInDuration: 10, stayDuration: 70, fadeOutDuration: 30 });
  } catch { }
};

/** A sound everyone nearby hears, from a place in the world. */
export const sound = (dim, id, loc, volume = 1, pitch = 1) => {
  runCommand(dim, `playsound ${id} @a ${loc.x.toFixed(1)} ${loc.y.toFixed(1)} ${loc.z.toFixed(1)} ${volume} ${pitch}`);
};
/** A sound only one player hears (the Sirens' song is different for each listener). */
export const hear = (p, id, location, volume = 1, pitch = 1) => {
  try { p.playSound(id, location ? { location, volume, pitch } : { volume, pitch }); } catch { }
};

const badParticles = new Set();
export const particle = (dim, id, loc) => {
  if (badParticles.has(id)) return;
  try { dim.spawnParticle(id, loc); } catch { badParticles.add(id); }
};
/** A burst of particles spread over a disc. */
export const burst = (dim, id, loc, r = 2, n = 8) => {
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2, d = Math.random() * r;
    particle(dim, id, add(loc, { x: Math.cos(a) * d, y: Math.random() * 0.6, z: Math.sin(a) * d }));
  }
};
export const fogOn = (p, fogId, tag) => { try { p.runCommandAsync(`fog @s push ${fogId} ${tag}`); } catch { } };
export const fogOff = (p, tag) => { try { p.runCommandAsync(`fog @s remove ${tag}`); } catch { } };
