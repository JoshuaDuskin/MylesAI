import * as THREE from 'three';

// Graceful degradation: Check for WebGL support
const isWebGLSupported = !!document.createElement('canvas').getContext('webgl');
if (!isWebGLSupported) {
    console.warn('WebGL not supported. Falling back to canvas fallback.');
    return;
}

// Scene Setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e); // Dark blue background
scene.fog = new THREE.FogExp2(0x1a1a2e, 0.03);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 5;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);

// Inline Styles Injection
const style = document.createElement('style');
style.textContent = `
    body { margin: 0; overflow: hidden; background-color: #1a1a2e; }
    canvas { display: block; }
`;
document.head.appendChild(style);

// Cube Geometry and Material
const cubeGeometry = new THREE.BoxGeometry(1, 1, 1);
const cubeMaterial = new THREE.MeshStandardMaterial({ 
    color: 0x0f3460,
    roughness: 0.4,
    metalness: 0.7,
    wireframe: false
});
const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
scene.add(cube);

// Floating Particles
const particleCount = 200;
const particlesGeometry = new THREE.BufferGeometry();
const positions = new Float32Array(particleCount * 3);
for (let i = 0; i < particleCount * 3; i++) {
    positions[i] = (Math.random() - 0.5) * 10; // Spread particles
}
particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

const particlesMaterial = new THREE.PointsMaterial({
    color: 0xe94560,
    size: 0.05,
    transparent: true,
    opacity: 0.8
});

const particles = new THREE.Points(particlesGeometry, particlesMaterial);
scene.add(particles);

// Animation Loop
function animate() {
    requestAnimationFrame(animate);

    // Rotate Cube
    cube.rotation.x += 0.01;
    cube.rotation.y += 0.01;

    // Animate Particles (gentle floating)
    const positionsAttribute = particles.geometry.attributes.position;
    for (let i = 0; i < particleCount; i++) {
        const x = positionsAttribute.getX(i);
        const y = positionsAttribute.getY(i);
        const z = positionsAttribute.getZ(i);

        // Simple sine wave motion for Y axis
        positionsAttribute.setY(i, y + Math.sin(Date.now() * 0.001 + i) * 0.02);
    }
    particles.geometry.attributes.position.needsUpdate = true;

    renderer.render(scene, camera);
}

// Handle Window Resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Start Animation
animate();