// Renders Bedrock geometry + texture with three.js (Blockbench conventions) to PNG previews.
// usage (needs: npm i three playwright): node tools/preview_render.js <name> <geo.json> <texture.png> <out.png> [views] [pose.json]
// views: front, back, side, three, top. pose.json (all optional): {"<bone>": {"rotation": [x,y,z], "position": [x,y,z]},
//   "__hide": ["bone", ...], "__scale": 0.9, "__clean": true (no grid or player box), "__focus": [x, y, z, half_height]}
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const [, , name, geoPath, texPath, outPath, viewsArg, posePath] = process.argv;
const geo = JSON.parse(fs.readFileSync(geoPath, 'utf8'));
const tex = 'data:image/png;base64,' + fs.readFileSync(texPath).toString('base64');
const views = (viewsArg || 'front,three,side,back').split(',');
const pose = posePath ? JSON.parse(fs.readFileSync(posePath, 'utf8')) : {};

const html = `<!doctype html><html><body style="margin:0;background:#1d1f24">
<canvas id="c" width="${360 * views.length}" height="420"></canvas></body></html>`;

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 360 * views.length, height: 420 }, deviceScaleFactor: 1 });
  await page.setContent(html);
  await page.addScriptTag({ path: require.resolve('three/build/three.min.js') });
  const err = await page.evaluate(async ({ geo, tex, views, name, pose }) => {
    try {
      const T = THREE;
      const canvas = document.getElementById('c');
      const renderer = new T.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
      renderer.setScissorTest(true);
      const g = geo['minecraft:geometry'][0];
      const tw = g.description.texture_width, th = g.description.texture_height;
      const img = new Image(); img.src = tex; await img.decode();
      const texture = new T.Texture(img);
      texture.magFilter = T.NearestFilter; texture.minFilter = T.NearestFilter;
      texture.colorSpace = T.SRGBColorSpace; texture.needsUpdate = true;
      const blend = name === 'charybdis' || name === 'siren';
      const mat = new T.MeshLambertMaterial({ map: texture, alphaTest: blend ? 0.02 : 0.5, transparent: blend, side: T.DoubleSide });
      const rad = d => d * Math.PI / 180;
      const scene = new T.Scene();
      scene.add(new T.AmbientLight(0xffffff, 0.75));
      const sun = new T.DirectionalLight(0xffffff, 1.6); sun.position.set(-0.4, 1, -0.8); scene.add(sun);
      const groups = {}, pivots = {};
      const bbp = p => new T.Vector3(-p[0], p[1], p[2]);
      for (const b of g.bones) {
        const grp = new T.Group(); groups[b.name] = grp; pivots[b.name] = bbp(b.pivot);
        const r = (b.rotation || [0, 0, 0]).slice();
        let pr = pose[b.name];
        if (Array.isArray(pr)) pr = { rotation: pr };
        if (pr && pr.rotation) { r[0] += pr.rotation[0]; r[1] += pr.rotation[1]; r[2] += pr.rotation[2]; }
        grp.rotation.set(rad(-r[0]), rad(-r[1]), rad(r[2]), 'ZYX');
        grp.userData.pose = pr || {};
        if ((pose.__hide || []).includes(b.name)) grp.visible = false;
      }
      const root = new T.Group(); scene.add(root);
      if (pose.__scale) root.scale.setScalar(pose.__scale);
      for (const b of g.bones) {
        const grp = groups[b.name], pv = pivots[b.name];
        if (b.parent && groups[b.parent]) { grp.position.copy(pv).sub(pivots[b.parent]); groups[b.parent].add(grp); }
        else { grp.position.copy(pv); root.add(grp); }
        const pp = grp.userData.pose;
        if (pp.position) grp.position.add(new T.Vector3(-pp.position[0], pp.position[1], pp.position[2]));
        if (pp.scale !== undefined) grp.scale.setScalar(Array.isArray(pp.scale) ? pp.scale[0] : pp.scale);
        for (const c of (b.cubes || [])) {
          const [w, h, d] = c.size; const [u, v] = c.uv;
          const geom = new T.BoxGeometry(w, h, d);
          // three face order: +x(east) -x(west) +y(up) -y(down) +z(south) -z(north)
          const R = {
            east: [u, v + d, d, h], west: [u + d + w, v + d, d, h], up: [u + d, v, w, d],
            down: [u + d + w, v, w, d], south: [u + 2 * d + w, v + d, w, h], north: [u + d, v + d, w, h]
          };
          const order = ['east', 'west', 'up', 'down', 'south', 'north'];
          const uv = geom.attributes.uv;
          for (let f = 0; f < 6; f++) {
            const [fu, fv, fw, fh] = R[order[f]];
            for (let k = 0; k < 4; k++) {
              const i = f * 4 + k; const x = uv.getX(i), y = uv.getY(i);
              uv.setXY(i, (fu + x * fw) / tw, 1 - (fv + (1 - y) * fh) / th);
            }
          }
          const mesh = new T.Mesh(geom, mat);
          const from = new T.Vector3(-(c.origin[0] + w), c.origin[1], c.origin[2]);
          const center = from.clone().add(new T.Vector3(w / 2, h / 2, d / 2));
          if (c.rotation) {
            const cp = bbp(c.pivot); const cg = new T.Group();
            cg.position.copy(cp).sub(pv);
            cg.rotation.set(rad(-c.rotation[0]), rad(-c.rotation[1]), rad(c.rotation[2]), 'ZYX');
            mesh.position.copy(center).sub(cp); cg.add(mesh); grp.add(cg);
          } else { mesh.position.copy(center).sub(pv); grp.add(mesh); }
        }
      }
      // scale references: 1-block grid and a 1.8-block player box
      const grid = new T.GridHelper(160, 10, 0x555a66, 0x353943); scene.add(grid);
      const steve = new T.LineSegments(new T.EdgesGeometry(new T.BoxGeometry(9.6, 28.8, 4.8)),
        new T.LineBasicMaterial({ color: 0x5fb3ff }));
      root.updateMatrixWorld(true);
      const box = new T.Box3().setFromObject(root);
      steve.position.set(box.max.x + 10, 14.4, 0); scene.add(steve);
      const size = box.getSize(new T.Vector3()); let ctr = box.getCenter(new T.Vector3());
      let span = Math.max(size.x + 24, size.y, size.z) * 0.62;
      if (pose.__clean) { grid.visible = false; steve.visible = false; span = Math.max(size.x, size.y, size.z) * 0.58; }
      if (pose.__focus) { const f = pose.__focus, k = pose.__scale || 1; ctr = new T.Vector3(-f[0] * k, f[1] * k, f[2] * k); span = f[3] * k; }
      const dirs = { front: [0, 0, -1], back: [0, 0, 1], side: [-1, 0, 0], three: [-0.75, 0.25, -1], top: [0, 1, -0.3] };
      const W = 360, H = 420;
      views.forEach((vname, i) => {
        const dv = new T.Vector3(...dirs[vname]).normalize();
        const cam = new T.OrthographicCamera(-span * W / H, span * W / H, span, -span, 1, 2000);
        cam.position.copy(ctr).add(dv.multiplyScalar(600)); cam.lookAt(ctr);
        renderer.setViewport(i * W, 0, W, H); renderer.setScissor(i * W, 0, W, H);
        renderer.setClearColor(0x1d1f24); renderer.render(scene, cam);
      });
      return null;
    } catch (e) { return String(e.stack || e); }
  }, { geo, tex, views, name, pose });
  if (err) { console.error(err); process.exit(1); }
  await page.locator('#c').screenshot({ path: outPath });
  await browser.close();
  console.log('wrote', outPath);
})();
