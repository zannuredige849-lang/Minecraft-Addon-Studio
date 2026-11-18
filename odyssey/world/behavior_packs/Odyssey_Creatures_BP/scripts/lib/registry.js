// Which add-on creatures exist right now. One scan every few ticks keeps the per-creature loops cheap however many
// players and creatures there are (a scan per creature type per tick would not scale).
import { world } from "@minecraft/server";
import { DIMENSIONS, valid, warn } from "./util.js";

const TYPES = ["studio:cyclops", "studio:laestrygonian", "studio:laestrygonian_child", "studio:circe", "studio:circe_sister",
  "studio:siren", "studio:scylla", "studio:charybdis", "studio:shade", "studio:tiresias", "studio:sun_cattle", "studio:calypso",
  "studio:athena", "studio:trojan_horse", "studio:boulder", "studio:greek_ship", "studio:ship_crew"];
const cache = new Map(TYPES.map((t) => [t, []]));

export function refresh() {
  for (const type of TYPES) {
    const list = [];
    for (const id of DIMENSIONS) {
      try { list.push(...world.getDimension(id).getEntities({ type })); } catch (err) { if (id === DIMENSIONS[0]) warn("registry", err); }
    }
    cache.set(type, list);
  }
}
/** The creatures of a type (cached; dead ones are filtered out). */
export const creatures = (type) => (cache.get(type) ?? []).filter(valid);
export function track(entity) {
  const list = cache.get(entity?.typeId);
  if (list && !list.includes(entity)) list.push(entity);
}
