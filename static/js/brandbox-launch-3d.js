/**
 * Stitch ANIMATION_35 — AI Engine (Three.js r125)
 * Emerald octahedron core + wireframe shell + orbiting data bits.
 */
(function () {
  function initAiEngine3D(container) {
    if (!container || typeof THREE === "undefined") return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      container.classList.add("is-static");
      return;
    }

    const scene = new THREE.Scene();
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x10b981, 2);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    const purpleLight = new THREE.PointLight(0xad7bff, 1.2);
    purpleLight.position.set(-4, -2, 4);
    scene.add(purpleLight);

    const engineGroup = new THREE.Group();
    scene.add(engineGroup);

    const coreGeo = new THREE.OctahedronGeometry(1, 0);
    const coreMat = new THREE.MeshPhongMaterial({
      color: 0x10b981,
      emissive: 0x10b981,
      emissiveIntensity: 0.5,
      flatShading: true,
      transparent: true,
      opacity: 0.9,
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    engineGroup.add(core);

    const shellGeo = new THREE.IcosahedronGeometry(1.5, 1);
    const shellMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      wireframe: true,
      transparent: true,
      opacity: 0.2,
    });
    const shell = new THREE.Mesh(shellGeo, shellMat);
    engineGroup.add(shell);

    const bitsCount = 12;
    const bits = [];
    for (let i = 0; i < bitsCount; i++) {
      const bitGeo = new THREE.BoxGeometry(0.1, 0.1, 0.1);
      const bitMat = new THREE.MeshPhongMaterial({ color: 0xffffff });
      const bit = new THREE.Mesh(bitGeo, bitMat);

      const angle = (i / bitsCount) * Math.PI * 2;
      const radius = 1.8 + Math.random() * 0.5;
      bit.position.set(
        Math.cos(angle) * radius,
        (Math.random() - 0.5) * 2,
        Math.sin(angle) * radius
      );
      bit.userData = {
        angle: angle,
        radius: radius,
        speed: 0.01 + Math.random() * 0.02,
        yOffset: Math.random() * Math.PI * 2,
      };

      bits.push(bit);
      engineGroup.add(bit);
    }

    camera.position.z = 6.5;

    let frameId = 0;
    let running = true;

    function animate() {
      if (!running) return;
      frameId = requestAnimationFrame(animate);

      const time = performance.now() * 0.001;

      engineGroup.rotation.y += 0.005;
      engineGroup.rotation.z += 0.002;

      const pulse = 1 + Math.sin(time * 2) * 0.1;
      core.scale.set(pulse, pulse, pulse);
      core.rotation.x += 0.01;

      bits.forEach(function (bit) {
        bit.userData.angle += bit.userData.speed;
        bit.position.x = Math.cos(bit.userData.angle) * bit.userData.radius;
        bit.position.z = Math.sin(bit.userData.angle) * bit.userData.radius;
        bit.position.y = Math.sin(time + bit.userData.yOffset) * 0.5;
        bit.rotation.x += 0.05;
        bit.rotation.y += 0.05;
      });

      renderer.render(scene, camera);
    }

    animate();

    function onResize() {
      const newWidth = container.clientWidth || window.innerWidth;
      const newHeight = container.clientHeight || window.innerHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    }

    window.addEventListener("resize", onResize);

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) {
        running = false;
        cancelAnimationFrame(frameId);
      } else if (!running) {
        running = true;
        animate();
      }
    });
  }

  function boot() {
    const el = document.getElementById("brandbox-launch-scene");
    if (el) initAiEngine3D(el);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
