// Positions children of ConstraintLayout / RelativeLayout containers and sizes children of
// Linear/Frame/Scroll containers, emulating Android measure rules closely enough for review renders.
(function () {
  const num = v => (v == null || v === '' || isNaN(+v)) ? null : +v;
  const A = (el, k) => el.getAttribute('data-' + k);
  const kids = el => [...el.children].filter(c => c.classList.contains('v'));
  const margins = el => (A(el, 'm') || '0,0,0,0').split(',').map(Number);
  const pad = el => { const s = getComputedStyle(el); return [parseFloat(s.paddingLeft), parseFloat(s.paddingTop), parseFloat(s.paddingRight), parseFloat(s.paddingBottom)]; };
  const has = (s, ...ws) => ws.some(w => (s || '').split('|').map(x => x.trim()).includes(w));

  // ---------- CSS sizing for flow containers ----------
  function flowSize(parent) {
    const kind = A(parent, 'kind');
    const ori = A(parent, 'ori') || 'v';
    const grav = A(parent, 'gravity') || '';
    if (kind === 'linear') {
      parent.style.flexDirection = ori === 'v' ? 'column' : 'row';
      if (ori === 'v') {
        if (has(grav, 'center', 'center_vertical')) parent.style.justifyContent = 'center';
        if (has(grav, 'bottom')) parent.style.justifyContent = 'flex-end';
      } else {
        if (has(grav, 'center', 'center_horizontal')) parent.style.justifyContent = 'center';
        if (has(grav, 'end', 'right')) parent.style.justifyContent = 'flex-end';
      }
    }
    if (kind === 'scroll') parent.style.flexDirection = ori === 'h' ? 'row' : 'column';
    for (const c of kids(parent)) {
      const [ml, mt, mr, mb] = margins(c);
      c.style.margin = `${mt}px ${mr}px ${mb}px ${ml}px`;
      const w = A(c, 'w'), h = A(c, 'h'), lg = A(c, 'lg') || '', wt = num(A(c, 'weight'));
      if (kind === 'linear' || kind === 'scroll') {
        const vert = (kind === 'scroll' && ori !== 'h') || (kind === 'linear' && ori === 'v');
        const main = vert ? h : w, cross = vert ? w : h;
        const mainProp = vert ? 'height' : 'width', crossProp = vert ? 'width' : 'height';
        c.style.flexShrink = '1';
        if (wt && wt > 0) { c.style.flex = `${wt} 1 0px`; if (main !== 'zero' && num(main) == null) c.style.flexBasis = 'auto'; }
        else if (main === 'match') c.style.flex = '1 1 auto';
        else if (num(main) != null) { c.style[mainProp] = main + 'px'; c.style.flexShrink = '0'; }
        else c.style.flex = '0 1 auto';
        if (cross === 'match') c.style.alignSelf = 'stretch';
        else {
          if (num(cross) != null) c.style[crossProp] = cross + 'px';
          let a = 'flex-start';
          const g = lg || grav;
          if (vert) { if (has(g, 'center', 'center_horizontal')) a = 'center'; else if (has(g, 'end', 'right')) a = 'flex-end'; }
          else { if (has(g, 'center', 'center_vertical')) a = 'center'; else if (has(g, 'bottom')) a = 'flex-end'; }
          c.style.alignSelf = a;
        }
      } else if (kind === 'frame' || parent.id === 'screen') {
        if (w === 'match') c.style.justifySelf = 'stretch';
        else { if (num(w) != null) c.style.width = w + 'px'; c.style.justifySelf = has(lg, 'center', 'center_horizontal') ? 'center' : has(lg, 'end', 'right') ? 'end' : 'start'; }
        if (h === 'match') c.style.alignSelf = 'stretch';
        else { if (num(h) != null) c.style.height = h + 'px'; c.style.alignSelf = has(lg, 'center', 'center_vertical') ? 'center' : has(lg, 'bottom') ? 'end' : 'start'; }
      } else if (kind === 'list') {
        c.style.alignSelf = 'stretch';
      }
      const ck = A(c, 'kind');
      if (ck && ck !== 'constraint' && ck !== 'relative') flowSize(c);
      else if (ck === 'constraint' || ck === 'relative') prepAbs(c);
    }
  }
  function prepAbs(container) {
    for (const c of kids(container)) {
      c.style.position = 'absolute';
      c.style.margin = '0';
      const ck = A(c, 'kind');
      if (ck === 'constraint' || ck === 'relative') prepAbs(c); else flowSize(c);
    }
  }

  // ---------- anchor solver ----------
  const H_KEYS = {
    constraint: {
      L: [['constraintleft-toleftof', 'L'], ['constraintstart-tostartof', 'L'], ['constraintleft-torightof', 'R'], ['constraintstart-toendof', 'R']],
      R: [['constraintright-torightof', 'R'], ['constraintend-toendof', 'R'], ['constraintright-toleftof', 'L'], ['constraintend-tostartof', 'L']],
    },
    relative: {
      L: [['toendof', 'R'], ['torightof', 'R'], ['alignstart', 'L'], ['alignleft', 'L']],
      R: [['tostartof', 'L'], ['toleftof', 'L'], ['alignend', 'R'], ['alignright', 'R']],
    },
  };
  const V_KEYS = {
    constraint: {
      L: [['constrainttop-totopof', 'L'], ['constrainttop-tobottomof', 'R'], ['constraintbaseline-tobaselineof', 'L']],
      R: [['constraintbottom-tobottomof', 'R'], ['constraintbottom-totopof', 'L']],
    },
    relative: {
      L: [['below', 'R'], ['aligntop', 'L'], ['alignbaseline', 'L']],
      R: [['above', 'L'], ['alignbottom', 'R']],
    },
  };

  function solve(C) {
    const kind = A(C, 'kind');
    const [pl, pt, pr, pb] = pad(C);
    const W = Math.max(0, C.clientWidth - pl - pr);
    const ch = kids(C);
    const byId = {};
    const S = new Map();
    for (const c of ch) {
      const id = A(c, 'id'); if (id) byId[id] = c;
      S.set(c, { gone: c.classList.contains('gone'), x: null, w: null, y: null, h: null, m: margins(c) });
    }
    const target = (c, key) => A(c, key);
    const edge = (name, side, axis, size) => {
      if (name === 'parent') return side === 'L' ? 0 : size;
      const t = byId[name]; if (!t) return undefined;
      const s = S.get(t); if (!s) return undefined;
      const p = axis === 'h' ? s.x : s.y, d = axis === 'h' ? s.w : s.h;
      if (p == null || d == null) return null;
      return side === 'L' ? p : p + d;
    };
    function anchors(c, axis, size) {
      const keys = (axis === 'h' ? H_KEYS : V_KEYS)[kind];
      const res = { L: undefined, R: undefined, pending: false };
      for (const side of ['L', 'R']) {
        for (const [k, tside] of keys[side]) {
          const t = target(c, k); if (t == null) continue;
          const e = edge(t, tside, axis, size);
          if (e === null) res.pending = true; else if (e !== undefined) res[side] = e;
          break;
        }
      }
      if (kind === 'relative') {
        const pS = axis === 'h' ? ['alignparentstart', 'alignparentleft'] : ['alignparenttop'];
        const pE = axis === 'h' ? ['alignparentend', 'alignparentright'] : ['alignparentbottom'];
        if (res.L === undefined && pS.some(k => A(c, k) === 'true')) res.L = 0;
        if (res.R === undefined && pE.some(k => A(c, k) === 'true')) res.R = size;
        const cen = A(c, 'centerinparent') === 'true' || A(c, axis === 'h' ? 'centerhorizontal' : 'centervertical') === 'true';
        if (cen) res.center = true;
      }
      return res;
    }
    function measureW(c, avail) {
      const spec = A(c, 'w');
      if (num(spec) != null && spec !== 'zero') return +spec;
      const ck = A(c, 'kind');
      if (ck === 'constraint' || ck === 'relative') return Math.max(0, avail);
      c.style.width = 'max-content';
      const mw = c.getBoundingClientRect().width;
      c.style.width = '';
      return Math.min(mw, Math.max(0, avail));
    }
    // guidelines
    for (const c of ch) {
      if (A(c, 'kind') !== 'guide') continue;
      const s = S.get(c);
      const ori = A(c, 'guide');
      const pct = num(A(c, 'constraintguide-percent')), beg = num(A(c, 'constraintguide-begin')), end = num(A(c, 'constraintguide-end'));
      if (ori === 'vertical') { s.x = pct != null ? W * pct : beg != null ? beg : end != null ? W - end : 0; s.w = 0; s.y = 0; s.h = 0; }
      else { s.vguide = { pct, beg, end }; s.x = 0; s.w = 0; }
    }
    // ---- horizontal
    let changed = true, guard = 0;
    const doneH = c => S.get(c).x != null && S.get(c).w != null;
    while (ch.some(c => !doneH(c)) && guard++ < 60) {
      changed = false;
      for (const c of ch) {
        if (doneH(c)) continue;
        const s = S.get(c); const [ml, , mr] = s.m;
        const a = anchors(c, 'h', W);
        if (a.pending && !s.force) continue;
        if (s.gone) { s.w = 0; s.x = a.L !== undefined ? a.L : a.R !== undefined ? a.R : 0; changed = true; continue; }
        const spec = A(c, 'w');
        const L = a.L, R = a.R;
        const bias = num(A(c, 'constrainthorizontal-bias')) ?? 0.5;
        const pctW = num(A(c, 'constraintwidth-percent'));
        let w;
        if (spec === 'match') { w = (kind === 'relative' && L !== undefined && R !== undefined) ? R - L - ml - mr : W - ml - mr; s.x = kind === 'relative' && L !== undefined ? L + ml : ml; s.w = Math.max(0, w); changed = true; continue; }
        if (spec === 'zero' && kind === 'constraint') {
          const l = L !== undefined ? L : 0, r = R !== undefined ? R : W;
          w = pctW != null ? W * pctW : Math.max(0, r - l - ml - mr);
          s.w = w; s.x = pctW != null ? l + ml + ((r - mr) - (l + ml) - w) * bias : l + ml; changed = true; continue;
        }
        if (kind === 'relative' && L !== undefined && R !== undefined && spec !== 'wrap' && num(spec) == null) { s.x = L + ml; s.w = Math.max(0, R - L - ml - mr); changed = true; continue; }
        const avail = (L !== undefined && R !== undefined) ? (R - mr) - (L + ml) : (L !== undefined ? W - L - ml - mr : R !== undefined ? R - mr - ml : W - ml - mr);
        w = measureW(c, avail);
        s.w = w;
        if (kind === 'relative') {
          if (a.center) s.x = (W - w) / 2;
          else if (L !== undefined && R !== undefined) s.x = L + ml;
          else if (L !== undefined) s.x = L + ml;
          else if (R !== undefined) s.x = R - mr - w;
          else s.x = ml;
        } else {
          if (L !== undefined && R !== undefined) s.x = (L + ml) + ((R - mr) - (L + ml) - w) * bias;
          else if (L !== undefined) s.x = L + ml;
          else if (R !== undefined) s.x = R - mr - w;
          else s.x = ml;
        }
        changed = true;
      }
      if (!changed) { const u = ch.find(c => !doneH(c)); if (u) S.get(u).force = true; }
    }
    // apply widths so heights can be measured
    for (const c of ch) {
      const s = S.get(c);
      c.style.left = (pl + (s.x || 0)) + 'px';
      c.style.width = Math.max(0, s.w || 0) + 'px';
      s.force = false;
      if (s.gone) continue;
      const ck = A(c, 'kind');
      if (ck === 'constraint' || ck === 'relative') solve(c); else solveWithin(c);
    }
    // ---- vertical
    const hSpec = A(C, 'h');
    let H = null;
    if (num(hSpec) != null) H = +hSpec - pt - pb;
    else if (hSpec === 'match' && C.clientHeight > pt + pb + 1) H = C.clientHeight - pt - pb;
    const measureH = (c) => {
      const spec = A(c, 'h');
      if (num(spec) != null && spec !== 'zero') return +spec;
      const ratio = A(c, 'constraintdimensionratio');
      if (ratio && (spec === 'zero' || spec === 'wrap')) {
        const m = ratio.replace(/^[HW],/, '').split(':').map(Number);
        if (m.length === 2 && m[0] > 0) return S.get(c).w * m[1] / m[0];
      }
      const ck = A(c, 'kind');
      if ((ck === 'constraint' || ck === 'relative') && c.style.height) return parseFloat(c.style.height);
      c.style.height = '';
      return c.getBoundingClientRect().height;
    };
    function vpass(Hc, allowParentBottom) {
      let guard2 = 0, prog = true;
      const doneV = c => S.get(c).y != null && S.get(c).h != null;
      while (ch.some(c => !doneV(c)) && guard2++ < 60) {
        prog = false;
        for (const c of ch) {
          if (doneV(c)) continue;
          const s = S.get(c); const [, mt, , mb] = s.m;
          if (s.vguide) {
            if (Hc == null && s.vguide.beg == null) continue;
            const g = s.vguide; s.y = g.pct != null ? Hc * g.pct : g.beg != null ? g.beg : Hc - g.end; s.h = 0; prog = true; continue;
          }
          const a = anchors(c, 'v', Hc == null ? null : Hc);
          if (a.pending && !s.force) continue;
          const T = a.L === undefined ? undefined : a.L;
          let B = a.R;
          if (B === null || (B !== undefined && Hc == null && (A(c, 'constraintbottom-tobottomof') === 'parent' || A(c, 'alignparentbottom') === 'true'))) {
            if (!allowParentBottom) { if (T === undefined) continue; B = undefined; }
          }
          if (s.gone) { s.h = 0; s.y = T !== undefined ? T : B !== undefined ? B : 0; prog = true; continue; }
          const spec = A(c, 'h');
          const bias = num(A(c, 'constraintvertical-bias')) ?? 0.5;
          if (spec === 'match' && Hc != null) { s.y = mt; s.h = Math.max(0, Hc - mt - mb); prog = true; continue; }
          if (spec === 'zero' && kind === 'constraint' && T !== undefined && B !== undefined && !A(c, 'constraintdimensionratio')) {
            s.y = T + mt; s.h = Math.max(0, B - T - mt - mb); c.style.height = s.h + 'px'; prog = true; continue;
          }
          const h = measureH(c); s.h = h;
          if (kind === 'relative' && a.center && Hc != null) s.y = (Hc - h) / 2;
          else if (T !== undefined && B !== undefined) s.y = kind === 'relative' ? T + mt : (T + mt) + ((B - mb) - (T + mt) - h) * bias;
          else if (T !== undefined) s.y = T + mt;
          else if (B !== undefined) s.y = B - mb - h;
          else s.y = mt;
          prog = true;
        }
        if (!prog) { const u = ch.find(c => !doneV(c)); if (!u) break; if (S.get(u).force) break; S.get(u).force = true; }
      }
    }
    if (H == null) {
      vpass(null, false);
      let content = 0;
      for (const c of ch) { const s = S.get(c); if (s.y != null && !s.gone) content = Math.max(content, s.y + s.h + s.m[3]); }
      for (const c of ch) { const s = S.get(c); if (s.y == null && !s.gone) { content = Math.max(content, measureH(c) + s.m[1] + s.m[3]); } }
      H = content;
      for (const c of ch) { const s = S.get(c); if (s.y == null) s.h = null; s.force = false; }
      vpass(H, true);
    } else vpass(H, true);
    let bottom = 0;
    for (const c of ch) {
      const s = S.get(c);
      c.style.top = (pt + (s.y || 0)) + 'px';
      if (s.h != null && A(c, 'h') !== 'wrap') c.style.height = s.h + 'px';
      if (!s.gone) bottom = Math.max(bottom, (s.y || 0) + (s.h || 0) + s.m[3]);
    }
    if (num(hSpec) == null && !(hSpec === 'match' && C.clientHeight > pt + pb + 1)) C.style.height = (Math.max(H, bottom) + pt + pb) + 'px';
    else if (hSpec === 'match' && bottom > H) C.style.minHeight = (bottom + pt + pb) + 'px';
  }

  function solveWithin(el) {
    for (const c of kids(el)) {
      const ck = A(c, 'kind');
      if (ck === 'constraint' || ck === 'relative') solve(c); else solveWithin(c);
    }
  }

  function run() {
    const root = document.getElementById('screen');
    flowSize(root);
    solveWithin(root);
    // second pass picks up heights that changed after nested solves
    solveWithin(root);
    document.body.setAttribute('data-done', '1');
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(run); else window.addEventListener('load', run);
})();
