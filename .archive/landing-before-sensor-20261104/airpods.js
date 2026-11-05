import * as T from './assets/vendor/three.module.min.js';

export function createPodsScene(canvas, stage) {
  const renderer = new T.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'low-power' });
  renderer.setClearColor(0, 0);
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.22;

  const scene = new T.Scene();
  const camera = new T.PerspectiveCamera(32, 1, .1, 55);
  const rig = new T.Group();
  scene.add(rig);

  const studio = document.createElement('canvas');
  studio.width = 512;
  studio.height = 256;
  const ctx = studio.getContext('2d');
  const sweep = ctx.createLinearGradient(0, 0, 0, 256);
  sweep.addColorStop(0, '#b9c3d6');
  sweep.addColorStop(.48, '#747a87');
  sweep.addColorStop(.64, '#555d6b');
  sweep.addColorStop(1, '#b8c1d0');
  ctx.fillStyle = sweep;
  ctx.fillRect(0, 0, 512, 256);
  function softbox(x, y, w, h, opacity) {
    ctx.save();
    ctx.shadowColor = '#eef5ff';
    ctx.shadowBlur = 20;
    ctx.fillStyle = `rgba(255,255,255,${opacity})`;
    ctx.fillRect(x, y, w, h);
    ctx.restore();
  }
  softbox(18, 52, 54, 106, 1);
  softbox(198, 18, 125, 54, 1);
  softbox(370, 84, 75, 44, .83);
  const env = new T.CanvasTexture(studio);
  env.colorSpace = T.SRGBColorSpace;
  env.mapping = T.EquirectangularReflectionMapping;
  const pmrem = new T.PMREMGenerator(renderer);
  const map = pmrem.fromEquirectangular(env);
  scene.environment = map.texture;
  scene.environmentIntensity = 1.17;
  env.dispose();
  pmrem.dispose();

  scene.add(new T.HemisphereLight(0xffffff, 0x8394b0, 1.4));
  function light(color, intensity, x, y, z) {
    const source = new T.DirectionalLight(color, intensity);
    source.position.set(x, y, z);
    scene.add(source);
  }
  light(0xfff9f4, 2.1, -3, 4, 4);
  light(0xd3e3ff, 1.65, 4, 1, -3);

  const shell = new T.MeshPhysicalMaterial({ color: 0xf7f9ff, roughness: .23, clearcoat: .78, clearcoatRoughness: .15, metalness: .04 });
  const silicone = new T.MeshStandardMaterial({ color: 0xe5e9f0, roughness: .62 });
  const vent = new T.MeshStandardMaterial({ color: 0x191c23, roughness: .4, metalness: .4 });
  const seam = new T.MeshStandardMaterial({ color: 0x929aac, roughness: .48 });
  const steel = new T.MeshStandardMaterial({ color: 0xbbc3cf, roughness: .31, metalness: .73 });
  const led = new T.MeshStandardMaterial({ color: 0x69b88b, emissive: 0x409a65, emissiveIntensity: .45 });

  const sphere = new T.SphereGeometry(1, 40, 24);
  function ellipsoid(parent, mat, x, y, z, sx, sy, sz) {
    const mesh = new T.Mesh(sphere, mat);
    mesh.position.set(x, y, z);
    mesh.scale.set(sx, sy, sz);
    parent.add(mesh);
    return mesh;
  }
  function roundedBox(width, height, depth, radius, material) {
    const geometry = new T.BoxGeometry(width, height, depth, 18, 16, 12);
    const position = geometry.attributes.position;
    const normal = geometry.attributes.normal;
    const half = new T.Vector3(width / 2 - radius, height / 2 - radius, depth / 2 - radius);
    const vertex = new T.Vector3(), inner = new T.Vector3(), direction = new T.Vector3();
    for (let i = 0; i < position.count; i++) {
      vertex.fromBufferAttribute(position, i);
      inner.set(T.MathUtils.clamp(vertex.x, -half.x, half.x), T.MathUtils.clamp(vertex.y, -half.y, half.y), T.MathUtils.clamp(vertex.z, -half.z, half.z));
      direction.subVectors(vertex, inner).normalize();
      vertex.copy(inner).addScaledVector(direction, radius);
      position.setXYZ(i, vertex.x, vertex.y, vertex.z);
      normal.setXYZ(i, direction.x, direction.y, direction.z);
    }
    return new T.Mesh(geometry, material);
  }

  const box = new T.Group();
  rig.add(box);
  box.position.set(0, -.98, 0);
  box.add(roundedBox(3.26, 1.52, 1.12, .47, shell));
  // A fine groove follows the curvature of the case instead of splitting the body into two shapes.
  const path = [];
  const radius = .471;
  for (let corner = 0; corner < 4; corner++) {
    const start = corner * Math.PI / 2;
    const cx = (corner === 0 || corner === 3) ? 1.16 : -1.16;
    const cz = corner < 2 ? .09 : -.09;
    for (let i = 0; i <= 12; i++) {
      const angle = start + i * Math.PI / 24;
      path.push(new T.Vector3(cx + Math.cos(angle) * radius, .25, cz + Math.sin(angle) * radius));
    }
  }
  const groove = new T.CatmullRomCurve3(path, true, 'catmullrom', 0);
  box.add(new T.Mesh(new T.TubeGeometry(groove, 100, .008, 5, true), seam));
  ellipsoid(box, led, 0, -.02, .562, .033, .027, .012);
  const hinge = roundedBox(1.0, .185, .09, .041, steel);
  hinge.position.set(0, .31, -.55);
  box.add(hinge);
  const port = roundedBox(.35, .034, .128, .016, vent);
  port.position.set(0, -.755, 0);
  box.add(port);

  function earbud(side) {
    const group = new T.Group();
    const stem = new T.Mesh(new T.CapsuleGeometry(.145, .84, 10, 24), shell);
    stem.position.set(side * .15, -.49, .01);
    stem.scale.z = .91;
    group.add(stem);
    const body = ellipsoid(group, shell, 0, .02, 0, .455, .35, .32);
    body.rotation.z = .24 * side;
    ellipsoid(group, shell, -side * .255, -.025, .036, .30, .24, .245);
    ellipsoid(group, silicone, -side * .46, -.018, .076, .17, .185, .175);
    ellipsoid(group, vent, -side * .59, -.018, .087, .035, .117, .109);
    const grille = ellipsoid(group, vent, side * .19, .056, .291, .083, .142, .020);
    grille.rotation.z = -.38 * side;
    ellipsoid(group, vent, side * .137, -.39, .141, .048, .088, .009);
    ellipsoid(group, steel, side * .15, -.94, .015, .139, .065, .132);
    ellipsoid(group, vent, side * .15, -.983, .018, .065, .024, .046);
    rig.add(group);
    return group;
  }

  const left = earbud(-1);
  const right = earbud(1);
  let lastP = -1, lastW = 0, lastH = 0;
  canvas.addEventListener('webglcontextlost', () => { delete stage.dataset.ready; });
  canvas.addEventListener('webglcontextrestored', () => { draw(lastP, true); stage.dataset.ready = ''; });

  function draw(progress, force = false) {
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    if (!width || !height || renderer.getContext().isContextLost()) return;
    if (!force && Math.abs(progress - lastP) < .001 && width === lastW && height === lastH) return;
    if (width !== lastW || height !== lastH || force) {
      renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }
    lastP = progress; lastW = width; lastH = height;

    const narrow = camera.aspect < 1.2;
    const distance = narrow ? Math.max(9.7, 9.3 / camera.aspect) : 8.8;
    camera.position.set(0, .7, distance);
    camera.lookAt(0, -.02, 0);
    const t = progress * progress * (3 - 2 * progress);
    rig.position.set(narrow ? 0 : .22, narrow ? .18 : .02, 0);
    rig.rotation.set(.05 + t * .12, -.49 + t * .95, -.095 + t * .15);
    box.rotation.set(-.08, .14, -.015);
    left.position.set(-.86 - t * .14, .86 + t * .29, .23);
    left.rotation.set(.06, -.22 + t * .38, -.30 + t * .17);
    right.position.set(.89 + t * .20, 1.26 + t * .19, -.07);
    right.rotation.set(.19, .28 - t * .63, .39 - t * .12);
    renderer.render(scene, camera);
  }

  return { draw };
}
