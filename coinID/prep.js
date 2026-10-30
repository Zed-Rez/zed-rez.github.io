// prep.js -- photo -> the 512 x 512 faces the model reads, in the browser (the server takes nothing else).
// A port of coin-visualizer/app/src/autocrop.rs and preprocess.rs: find the coin(s) on a plain background (two coins =
// a combined obverse + reverse photo), else the infer_v6 framing (aspect split / whole frame); square centre crop; then
// Pillow's resize((512, 512), BILINEAR, reducing_gap=2.0), bit-exact (Image.reduce pre-shrink + fixed-point bilinear);
// sent as JPEG q92, the form the training faces were cached in (~80 KB vs ~400 KB as PNG: the server is on a home Wi-Fi).
// Images are decoded without EXIF rotation or colour management, as Pillow's Image.open(...).convert("RGB") does.
"use strict";
(function (root) {
  const S512 = 512;
  const PHOTO_EXT = ["jpg", "jpeg", "jfif", "png", "tif", "tiff", "webp", "bmp"];

  // ---- decode -------------------------------------------------------------------------------------------------------
  // {w, h, px: Uint8Array RGB}
  function rgbFromRGBA(w, h, a) {
    const px = new Uint8Array(w * h * 3);
    for (let i = 0, j = 0; i < w * h; i++, j += 4) { px[i * 3] = a[j]; px[i * 3 + 1] = a[j + 1]; px[i * 3 + 2] = a[j + 2]; }
    return { w, h, px };
  }

  const MAX_PIXELS = 60e6;

  async function decodeBrowser(blob) {
    const opts = { imageOrientation: "none", colorSpaceConversion: "none", premultiplyAlpha: "none" };
    let bm;
    try { bm = await createImageBitmap(blob, opts); }
    catch (e) { bm = await createImageBitmap(blob); }   // older browsers without the options
    if (bm.width * bm.height > MAX_PIXELS) { bm.close(); throw new Error("photo too large"); }
    const c = document.createElement("canvas"); c.width = bm.width; c.height = bm.height;
    const g = c.getContext("2d", { willReadFrequently: true, colorSpace: "srgb" });
    g.drawImage(bm, 0, 0); bm.close();
    return rgbFromRGBA(c.width, c.height, g.getImageData(0, 0, c.width, c.height, { colorSpace: "srgb" }).data);
  }

  let tiffLib = null;
  function loadScript(src, integrity) {
    return new Promise((ok, bad) => {
      const s = document.createElement("script"); s.src = src; s.integrity = integrity; s.crossOrigin = "anonymous";
      s.onload = ok; s.onerror = () => bad(new Error("could not load the TIFF reader")); document.head.appendChild(s);
    });
  }
  function tiff() {
    // UTIF.js reads TIFF (no browser but Safari does); pako inflates Deflate-compressed TIFFs. Loaded only when needed.
    tiffLib = tiffLib || loadScript("https://cdn.jsdelivr.net/npm/pako@2.1.0/dist/pako_inflate.min.js",
      "sha384-taEjHL+GUvC8IhXeCaTNUxz3O8ItsajGFLDFj4v/VJvM24HU36qP/6sRpuAGGfeT")
      .then(() => loadScript("https://cdn.jsdelivr.net/npm/utif@3.1.0/UTIF.js",
        "sha384-RyBmXHdfZ/Uon+ud+/AqSyWpUWnKYt2tkRG/P4gWoRUGDU+qIAV3tGBPNlYTBZEF"));
    return tiffLib;
  }
  async function decodeTiff(blob) {
    await tiff();
    const buf = await blob.arrayBuffer(), U = root.UTIF;
    const ifds = U.decode(buf);
    // the first full-resolution image (some TIFFs lead with a thumbnail)
    let best = ifds[0];
    for (const d of ifds) if ((d.t256 ? d.t256[0] : 0) * (d.t257 ? d.t257[0] : 0) > (best.t256 ? best.t256[0] : 0) * (best.t257 ? best.t257[0] : 0)) best = d;
    if (best.t256[0] * best.t257[0] > MAX_PIXELS) throw new Error("photo too large");
    U.decodeImage(buf, best);
    return rgbFromRGBA(best.width, best.height, U.toRGBA8(best));
  }

  function isTiff(head) {
    return (head[0] === 0x49 && head[1] === 0x49 && head[2] === 0x2a && head[3] === 0) || (head[0] === 0x4d && head[1] === 0x4d && head[2] === 0 && head[3] === 0x2a);
  }

  async function decode(file) {
    const head = new Uint8Array(await file.slice(0, 4).arrayBuffer());
    if (isTiff(head)) {
      try { return await decodeBrowser(file); } catch (e) { return decodeTiff(file); }   // Safari reads TIFF itself
    }
    return decodeBrowser(file);
  }

  function isPhoto(file) {
    const ext = (file.name.split(".").pop() || "").toLowerCase();
    return PHOTO_EXT.includes(ext) || /^image\//.test(file.type || "");
  }

  // ---- Pillow: Image.resize(size, BILINEAR, reducing_gap) ------------------------------------------------------------
  const PRECISION_BITS = 32 - 8 - 2;
  const f32 = Math.fround;

  function crop(im, x0, y0, x1, y1) {
    // PIL Image.crop: integer box, areas outside the image are black
    const w = Math.max(x1 - x0, 0), h = Math.max(y1 - y0, 0), px = new Uint8Array(w * h * 3);
    for (let y = 0; y < h; y++) {
      const sy = y0 + y;
      if (sy < 0 || sy >= im.h) continue;
      for (let x = 0; x < w; x++) {
        const sx = x0 + x;
        if (sx < 0 || sx >= im.w) continue;
        const s = (sy * im.w + sx) * 3, d = (y * w + x) * 3;
        px[d] = im.px[s]; px[d + 1] = im.px[s + 1]; px[d + 2] = im.px[s + 2];
      }
    }
    return { w, h, px };
  }

  // libImaging Reduce.c (UINT8 path), block sums with the float-derived fixed-point multiplier
  function pilReduce(im, xs, ys, rb) {
    const [bx, by] = rb, bw = rb[2] - rb[0], bh = rb[3] - rb[1];
    const ow = Math.floor((bw + xs - 1) / xs), oh = Math.floor((bh + ys - 1) / ys), out = new Uint8Array(ow * oh * 3);
    const div = (n) => Math.trunc(f32(4294967296 / f32(256 * n))) >>> 0;
    for (let y = 0; y < oh; y++) {
      const yf = by + y * ys, yt = Math.min(yf + ys, by + bh);
      for (let x = 0; x < ow; x++) {
        const xf = bx + x * xs, xt = Math.min(xf + xs, bx + bw), n = (xt - xf) * (yt - yf), m = div(n), amend = n >>> 1;
        for (let c = 0; c < 3; c++) {
          let ss = amend;
          for (let yy = yf; yy < yt; yy++) { let i = (yy * im.w + xf) * 3 + c; for (let xx = xf; xx < xt; xx++, i += 3) ss += im.px[i]; }
          out[(y * ow + x) * 3 + c] = Math.imul(ss, m) >>> 24;
        }
      }
    }
    return { w: ow, h: oh, px: out };
  }

  // precompute_coeffs + normalize_coeffs_8bpc for the bilinear filter (support 1.0)
  function coeffs(inSize, in0, in1, outSize) {
    const scale = f32(in1 - in0) / outSize, filterscale = Math.max(scale, 1), support = filterscale;
    const ksize = Math.ceil(support) * 2 + 1, bounds = new Int32Array(outSize * 2), kk = new Int32Array(outSize * ksize);
    const inv = 1 / filterscale, k = new Float64Array(ksize);
    for (let xx = 0; xx < outSize; xx++) {
      const center = in0 + (xx + 0.5) * scale;
      let ww = 0;
      const xmin = Math.max(Math.trunc(center - support + 0.5), 0);
      const xmax = Math.min(Math.trunc(center + support + 0.5), inSize) - xmin;
      for (let x = 0; x < xmax; x++) {
        const t = Math.abs((x + xmin - center + 0.5) * inv), w = t < 1 ? 1 - t : 0;
        k[x] = w; ww += w;
      }
      for (let x = 0; x < xmax; x++) {
        if (ww !== 0) k[x] /= ww;
        const v = k[x] * (1 << PRECISION_BITS);
        kk[xx * ksize + x] = k[x] < 0 ? Math.trunc(-0.5 + v) : Math.trunc(0.5 + v);
      }
      bounds[xx * 2] = xmin; bounds[xx * 2 + 1] = xmax;
    }
    return { ksize, bounds, kk };
  }

  const clip8 = (v) => { v = v >> PRECISION_BITS; return v < 0 ? 0 : v > 255 ? 255 : v; };

  // ImagingResampleInner with the bilinear filter, 3-band 8-bit path: horizontal pass, then vertical pass
  function resampleBilinear(im, ow, oh, b) {
    const needH = ow !== im.w || b[0] !== 0 || b[2] !== ow, needV = oh !== im.h || b[1] !== 0 || b[3] !== oh;
    const half = 1 << (PRECISION_BITS - 1);
    const cv = coeffs(im.h, b[1], b[3], oh);
    let cur = im;
    if (needH) {
      const ch = coeffs(im.w, b[0], b[2], ow), t = new Uint8Array(ow * im.h * 3);
      for (let y = 0; y < im.h; y++) {
        const line = y * im.w * 3;
        for (let xx = 0; xx < ow; xx++) {
          const xmin = ch.bounds[xx * 2], xmax = ch.bounds[xx * 2 + 1], ko = xx * ch.ksize;
          let s0 = half, s1 = half, s2 = half;
          for (let x = 0; x < xmax; x++) {
            const p = line + (x + xmin) * 3, kv = ch.kk[ko + x];
            s0 += im.px[p] * kv; s1 += im.px[p + 1] * kv; s2 += im.px[p + 2] * kv;
          }
          const o = (y * ow + xx) * 3;
          t[o] = clip8(s0); t[o + 1] = clip8(s1); t[o + 2] = clip8(s2);
        }
      }
      cur = { w: ow, h: im.h, px: t };
    }
    if (!needV) return cur;
    const out = new Uint8Array(cur.w * oh * 3);
    for (let yy = 0; yy < oh; yy++) {
      const ymin = cv.bounds[yy * 2], ymax = cv.bounds[yy * 2 + 1], ko = yy * cv.ksize;
      for (let xx = 0; xx < cur.w; xx++) {
        let s0 = half, s1 = half, s2 = half;
        for (let y = 0; y < ymax; y++) {
          const p = ((y + ymin) * cur.w + xx) * 3, kv = cv.kk[ko + y];
          s0 += cur.px[p] * kv; s1 += cur.px[p + 1] * kv; s2 += cur.px[p + 2] * kv;
        }
        const o = (yy * cur.w + xx) * 3;
        out[o] = clip8(s0); out[o + 1] = clip8(s1); out[o + 2] = clip8(s2);
      }
    }
    return { w: cur.w, h: oh, px: out };
  }

  function pilResizeBilinear(im, ow, oh, reducingGap) {
    if (im.w === ow && im.h === oh) return im;
    let box = [0, 0, im.w, im.h], src = im;
    let fx = Math.max(Math.trunc(im.w / ow / reducingGap), 0), fy = Math.max(Math.trunc(im.h / oh / reducingGap), 0);
    fx = fx || 1; fy = fy || 1;
    if (fx > 1 || fy > 1) {
      const supX = 0.5 * im.w / ow, supY = 0.5 * im.h / oh;
      const rb = [Math.max(Math.trunc(-supX), 0), Math.max(Math.trunc(-supY), 0), Math.min(Math.ceil(im.w + supX), im.w), Math.min(Math.ceil(im.h + supY), im.h)];
      src = pilReduce(im, fx, fy, rb);
      box = [(box[0] - rb[0]) / fx, (box[1] - rb[1]) / fy, (box[2] - rb[0]) / fx, (box[3] - rb[1]) / fy];
    }
    return resampleBilinear(src, ow, oh, box.map(f32));   // the C side takes the box as float
  }

  // square centre crop of a box, resized to 512 x 512 (infer_v6.faces / prep_cache512.crop); Python int() truncates
  function crop512(im, b) {
    const [x0, y0, x1, y1] = b, s = Math.min(x1 - x0, y1 - y0), cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const c = crop(im, Math.trunc(cx - s / 2), Math.trunc(cy - s / 2), Math.trunc(cx + s / 2), Math.trunc(cy + s / 2));
    return pilResizeBilinear(c, S512, S512, 2.0);
  }

  // infer_v6.faces "auto": combined photos split at aspect >= 1.6 (left/right) or <= 1/1.6 (top/bottom)
  function faceBoxes(w, h, split) {
    const r = w / h;
    if (split && r >= 1.6) return [[0, 0, w / 2, h], [w / 2, 0, w, h]];
    if (split && r <= 1 / 1.6) return [[0, 0, w, h / 2], [0, h / 2, w, h]];
    return [[0, 0, w, h]];
  }

  // ---- autocrop -------------------------------------------------------------------------------------------------------
  // masks are Uint8Array 0/1, w x h; one step of scipy binary_dilation / erosion with the cross (border value 0)
  function step(m, w, h, dilate) {
    const o = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x, c = m[i], l = x > 0 ? m[i - 1] : 0, r = x + 1 < w ? m[i + 1] : 0, u = y > 0 ? m[i - w] : 0, d = y + 1 < h ? m[i + w] : 0;
      o[i] = dilate ? (c | l | r | u | d) : (c & l & r & u & d);
    }
    return o;
  }
  function iterate(m, w, h, dilate, n) { for (let i = 0; i < n; i++) m = step(m, w, h, dilate); return m; }
  const closing = (m, w, h, n) => iterate(iterate(m, w, h, true, n), w, h, false, n);
  const opening = (m, w, h, n) => iterate(iterate(m, w, h, false, n), w, h, true, n);

  // binary_fill_holes: background = what is 4-connected to the border
  function fillHoles(m, w, h) {
    const out = new Uint8Array(w * h), st = [];
    for (let x = 0; x < w; x++) st.push(x, (h - 1) * w + x);
    for (let y = 0; y < h; y++) st.push(y * w, y * w + w - 1);
    while (st.length) {
      const i = st.pop();
      if (out[i] || m[i]) continue;
      out[i] = 1;
      const x = i % w, y = (i / w) | 0;
      if (x > 0) st.push(i - 1);
      if (x + 1 < w) st.push(i + 1);
      if (y > 0) st.push(i - w);
      if (y + 1 < h) st.push(i + w);
    }
    for (let i = 0; i < w * h; i++) out[i] = out[i] ? 0 : 1;
    return out;
  }

  // ndimage.label (4-connectivity) + find_objects: per blob [y0, x0, y1, x1, area]
  function blobs(m, w, h) {
    const seen = new Uint8Array(w * h), out = [];
    for (let s = 0; s < w * h; s++) {
      if (!m[s] || seen[s]) continue;
      let y0 = h, x0 = w, y1 = 0, x1 = 0, a = 0;
      const st = [s]; seen[s] = 1;
      while (st.length) {
        const i = st.pop(), x = i % w, y = (i / w) | 0;
        if (y < y0) y0 = y; if (x < x0) x0 = x; if (y + 1 > y1) y1 = y + 1; if (x + 1 > x1) x1 = x + 1; a++;
        const push = (j) => { if (m[j] && !seen[j]) { seen[j] = 1; st.push(j); } };
        if (x > 0) push(i - 1);
        if (x + 1 < w) push(i + 1);
        if (y > 0) push(i - w);
        if (y + 1 < h) push(i + w);
      }
      out.push([y0, x0, y1, x1, a]);
    }
    return out;
  }

  // foreground mask at max side 400 and the scale factor; null if the background is not plain
  function foreground(im) {
    const f = Math.max(im.w, im.h) / 400;
    const gw = Math.max(Math.round(im.w / f), 1), gh = Math.max(Math.round(im.h / f), 1);
    const g = pilResizeBilinear(im, gw, gh, Infinity);
    const border = [];
    const px = (x, y) => { const i = (y * gw + x) * 3; return [g.px[i], g.px[i + 1], g.px[i + 2]]; };
    for (let x = 0; x < gw; x++) border.push(px(x, 0), px(x, gh - 1));
    for (let y = 0; y < gh; y++) border.push(px(0, y), px(gw - 1, y));
    // most common quantised border colour; its median is the background (scale bars sit on the edge)
    const key = (p) => Math.trunc(p[0] / 24) * 10000 + Math.trunc(p[1] / 24) * 100 + Math.trunc(p[2] / 24);
    const cnt = new Map();
    for (const p of border) { const k = key(p); cnt.set(k, (cnt.get(k) || 0) + 1); }
    let top = null, tc = -1;
    for (const [k, c] of cnt) if (c > tc || (c === tc && k < top)) { top = k; tc = c; }
    const bg = [0, 0, 0];
    for (let c = 0; c < 3; c++) {
      const v = border.filter((p) => key(p) === top).map((p) => p[c]).sort((a, b) => a - b), n = v.length;
      bg[c] = n % 2 ? v[n >> 1] : f32((v[n / 2 - 1] + v[n / 2]) / 2);
    }
    const dist = (r, gg, b) => f32(f32(Math.abs(r - bg[0]) + Math.abs(gg - bg[1])) + Math.abs(b - bg[2]));
    const plain = border.filter((p) => dist(p[0], p[1], p[2]) < 40).length / border.length;
    if (plain < 0.3) return null;
    const m = new Uint8Array(gw * gh);
    for (let i = 0; i < gw * gh; i++) m[i] = dist(g.px[i * 3], g.px[i * 3 + 1], g.px[i * 3 + 2]) > 60 ? 1 : 0;
    return { m: fillHoles(closing(m, gw, gh, 3), gw, gh), w: gw, h: gh, f };
  }

  // coin-like blobs, largest box first: min side >= 40, aspect 0.75..1.33, off the edge, disc-like fill
  function coinLike(m, w, h) {
    const c = [];
    for (const [y0, x0, y1, x1, a] of blobs(m, w, h)) {
      const hh = y1 - y0, ww = x1 - x0, r = ww / hh;
      if (Math.min(hh, ww) < 40 || r < 0.75 || r > 1.33) continue;
      if (y0 <= 1 || x0 <= 1 || y1 >= h - 1 || x1 >= w - 1) continue;
      const fill = a / (hh * ww);
      if (fill < 0.62 || fill > 0.92) continue;
      c.push([hh * ww, [y0, x0, y1, x1]]);
    }
    c.sort((a, b) => b[0] - a[0]);   // stable, as Rust's sort_by
    return c.map((x) => x[1]);
  }

  function toBox(s, pad, f, w, h) {
    const [y0, x0, y1, x1] = s, m = pad + 0.04 * Math.max(y1 - y0, x1 - x0);
    return [Math.max((x0 - m) * f, 0), Math.max((y0 - m) * f, 0), Math.min((x1 + m) * f, w), Math.min((y1 + m) * f, h)];
  }
  const area = (s) => (s[2] - s[0]) * (s[3] - s[1]);

  // exactly two coin-like blobs of similar size, ordered left -> right (or top -> bottom)
  function two(fg, w, h, pad) {
    const c = coinLike(fg.m, fg.w, fg.h).slice(0, 3);
    if (c.length < 2 || (c.length === 3 && area(c[2]) > 0.5 * area(c[1])) || area(c[1]) < 0.5 * area(c[0])) return null;
    const cx = (s) => (s[1] + s[3]) / 2, cy = (s) => (s[0] + s[2]) / 2;
    const t = [c[0], c[1]];
    if (Math.abs(cx(t[0]) - cx(t[1])) >= Math.abs(cy(t[0]) - cy(t[1]))) t.sort((a, b) => cx(a) - cx(b));
    else t.sort((a, b) => cy(a) - cy(b));
    return t.map((s) => toBox(s, pad, fg.f, w, h));
  }

  // one clearly dominant coin-like blob
  function one(fg, w, h, pad) {
    const c = coinLike(fg.m, fg.w, fg.h);
    if (!c.length) return null;
    if (c.length === 1 || area(c[1]) < 0.5 * area(c[0])) return toBox(c[0], pad, fg.f, w, h);
    return null;
  }

  // face boxes: two coins (a combined obv + rev photo), one coin, or the infer_v6 framing; kind = pair|coin|split|frame
  function findFaces(im, auto) {
    const fallback = () => { const b = faceBoxes(im.w, im.h, true); return { boxes: b, kind: b.length === 2 ? "split" : "frame" }; };
    if (!auto) return fallback();
    const fg0 = foreground(im);
    if (!fg0) return fallback();
    const masks = [0, 4, 8].map((it) => [it, { ...fg0, m: it ? opening(fg0.m, fg0.w, fg0.h, it) : fg0.m }]);
    for (const [it, fg] of masks) { const b = two(fg, im.w, im.h, it); if (b) return { boxes: b, kind: "pair" }; }
    for (const [it, fg] of masks) { const b = one(fg, im.w, im.h, it); if (b) return { boxes: [b], kind: "coin" }; }
    return fallback();
  }

  // ---- out ----------------------------------------------------------------------------------------------------------
  function toJPEG(face) {
    const c = document.createElement("canvas"); c.width = face.w; c.height = face.h;
    const g = c.getContext("2d"), d = g.createImageData(face.w, face.h);
    for (let i = 0; i < face.w * face.h; i++) { d.data[i * 4] = face.px[i * 3]; d.data[i * 4 + 1] = face.px[i * 3 + 1]; d.data[i * 4 + 2] = face.px[i * 3 + 2]; d.data[i * 4 + 3] = 255; }
    g.putImageData(d, 0, 0);
    return new Promise((ok, bad) => c.toBlob((b) => (b ? ok(b) : bad(new Error("could not encode a face"))), "image/jpeg", 0.92));
  }

  // one photo -> its faces as 512 px JPEG blobs
  async function photoFaces(file, auto) {
    const im = await decode(file);
    if (im.w < 64 || im.h < 64) throw new Error("photo too small");
    const { boxes, kind } = findFaces(im, auto);
    const faces = [];
    for (const b of boxes) faces.push(await toJPEG(crop512(im, b)));
    return { faces, kind };
  }

  root.CoinPrep = { PHOTO_EXT, isPhoto, decode, photoFaces, findFaces, crop512, pilResizeBilinear, faceBoxes };
})(typeof window !== "undefined" ? window : globalThis);
