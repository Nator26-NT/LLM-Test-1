import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// Setup scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111122);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
camera.position.set(2, 2, 2);
camera.lookAt(0, 0, 0);

const canvas = document.getElementById('three-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });

function resizeRenderer() {
    const container = document.querySelector('.viewer-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    renderer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
}
window.addEventListener('resize', resizeRenderer);
resizeRenderer();

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.rotateSpeed = 1.0;
controls.zoomSpeed = 1.2;
controls.panSpeed = 0.8;

const ambientLight = new THREE.AmbientLight(0x404060);
scene.add(ambientLight);
const dirLight = new THREE.DirectionalLight(0xffffff, 1);
dirLight.position.set(1, 2, 1);
scene.add(dirLight);
const backLight = new THREE.DirectionalLight(0x88aaff, 0.5);
backLight.position.set(-1, 1, -1);
scene.add(backLight);

const gridHelper = new THREE.GridHelper(3, 20, 0x888888, 0x444444);
scene.add(gridHelper);

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}
animate();

// Form handling
const form = document.getElementById('generate-form');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const summaryDiv = document.getElementById('summary');
let currentModel = null;

form.addEventListener('submit', async(e) => {
    e.preventDefault();
    loadingDiv.classList.remove('hidden');
    errorDiv.classList.add('hidden');
    summaryDiv.innerHTML = '';

    const formData = new FormData(form);
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`HTTP ${response.status}: ${text.substring(0, 200)}`);
        }
        const data = await response.json();
        summaryDiv.innerHTML = `<strong>Educational Summary:</strong><br>${data.summary}`;
        loadModel(data.model_url);
    } catch (err) {
        errorDiv.textContent = `Error: ${err.message}`;
        errorDiv.classList.remove('hidden');
    } finally {
        loadingDiv.classList.add('hidden');
    }
});

function loadModel(url) {
    if (currentModel) {
        scene.remove(currentModel);
        currentModel = null;
    }
    const loader = new GLTFLoader();
    loader.load(url, (gltf) => {
        currentModel = gltf.scene;
        scene.add(currentModel);
    }, undefined, (error) => {
        console.error('Failed to load model:', error);
        errorDiv.textContent = 'Failed to load 3D model.';
        errorDiv.classList.remove('hidden');
    });
}