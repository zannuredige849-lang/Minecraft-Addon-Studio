// Forms resolve through a per-player responder set by the test: responder(player, form) -> { selection } | { canceled, reason }.
export const FormCancelationReason = { UserBusy: "UserBusy", UserClosed: "UserClosed" };
export const ui = { responders: new Map(), shown: [] };
class Base {
  constructor(kind) { this.kind = kind; this.buttons = []; }
  title(t) { this._title = t; return this; } body(b) { this._body = b; return this; }
  async show(p) {
    ui.shown.push([p.name, this]);
    const r = ui.responders.get(p.name);
    const res = r ? r(p, this) : { canceled: true, reason: "UserClosed" };
    if (!res) return new Promise(() => { });      // never answers (AFK player)
    return res.canceled ? { canceled: true, cancelationReason: res.reason ?? "UserClosed" } : { canceled: false, selection: res.selection };
  }
}
export class ActionFormData extends Base { constructor() { super("action"); } button(t, icon) { this.buttons.push({ t, icon }); return this; } }
export class MessageFormData extends Base { constructor() { super("message"); } button1(t) { this.b1 = t; return this; } button2(t) { this.b2 = t; return this; } }
export class ModalFormData extends Base { constructor() { super("modal"); } toggle() { return this; } dropdown() { return this; } textField() { return this; } slider() { return this; } }
