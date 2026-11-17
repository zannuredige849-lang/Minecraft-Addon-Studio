// node --import ./tools/odyssey/jstest/register.mjs tools/odyssey/jstest/test.mjs
import { register } from "node:module";
register("./hooks.mjs", import.meta.url);
