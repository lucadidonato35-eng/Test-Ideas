/* Outfit rules engine, twin of pipeline/rules.py. Inlined into index.html at build time;
   tests/test_rules.py runs both over every combination to keep them identical. */
(function (root) {
  const match = (p, sel) => Object.keys(sel).filter(f => !f.startsWith("_")).every(f => sel[f].includes(p[f]));
  function check(pcs, P, R, occasion, cold) {
    if (cold === undefined) cold = true;
    const [o, t, b, s] = pcs.map(k => (k ? P[k] : null)), out = [];
    if (b && s) {
      const rule = R.shoes.pairs.find(r => match(s, r.shoes));
      if (!rule) out.push({id: "shoes", lvl: "warn", short: "Shoes ?", msg: `No shoe rule covers ${s.name}`});
      else if (rule.with.some(w => match(b, w))) out.push({id: "shoes", lvl: "ok", short: "Shoes ✓", msg: `${s.name} suit ${b.name.toLowerCase()}`});
      else if (s.style === "sneaker" && b.kind === "trouser") out.push({id: "shoes", lvl: "no", short: "Shoes ✗", msg: "Sneakers undercut tailored trousers"});
      else out.push({id: "shoes", lvl: "no", short: "Shoes ✗", msg: rule.say});
    }
    const cols = new Set([o, t, b, s].filter(Boolean).map(x => x.colour));
    const hit = R.clash.pairs.find(pr => cols.has(pr[0]) && cols.has(pr[1]));
    out.push(hit ? {id: "clash", lvl: "warn", short: `${hit[0][0].toUpperCase() + hit[0].slice(1)} + ${hit[1]}`, msg: R.clash.say}
                 : {id: "clash", lvl: "ok", short: "Palette ✓", msg: "Colours sit in one family"});
    const busy = !!(o && t && R.texture.outer.includes(o.tex) && R.texture.top.includes(t.tex));
    out.push(busy ? {id: "texture", lvl: "warn", short: "Two textures", msg: R.texture.say}
                  : {id: "texture", lvl: "ok", short: "Texture ✓", msg: "One texture hero"});
    if (cold) {
      const W = R.warmth;
      if (t && !o && (t.w || 0) <= W.light) out.push({id: "warmth", lvl: "warn", short: "Too light", msg: W.say_light});
      else if ((o ? o.w || 0 : 0) + (t ? t.w || 0 : 0) < W.min) out.push({id: "warmth", lvl: "warn", short: "Too light", msg: W.say_low});
      else out.push({id: "warmth", lvl: "ok", short: "Warm ✓", msg: `Warm enough for ${W.place}`});
    }
    if (occasion) {
      const off = [o, t, b, s].filter(x => x && !(x.occasions || []).includes(occasion));
      if (off.length) out.push({id: "occasion", lvl: "warn", short: "Off-occasion",
        msg: R.occasion.say.replace("{names}", off.map(x => x.name).join(", ")).replace("{verb}", off.length > 1 ? "are" : "is").replace("{occasion}", occasion.toLowerCase())});
      else out.push({id: "occasion", lvl: "ok", short: `${occasion} ✓`, msg: `Right for ${occasion.toLowerCase()}`});
    }
    const D = R.dress_down;
    if (o && t && b && s && match(o, D.outer) && match(b, D.bottom) && s.style !== "sneaker" && !t.casual)
      out.push({id: "dress_down", lvl: "warn", short: "Puffer + tailoring", msg: D.say});
    return out;
  }
  function verdict(res, R) {
    const V = R.verdict;
    if (res.some(r => r.lvl === "no")) return {cls: "no", txt: V.rethink};
    const w = res.filter(r => r.lvl === "warn").length;
    return w === 0 ? {cls: "ok", txt: V.strong} : w === 1 ? {cls: "warn", txt: V.tweak} : {cls: "no", txt: V.rethink};
  }
  const api = {match, check, verdict};
  if (typeof module !== "undefined") module.exports = api; else root.Rules = api;
})(this);
