const canvas = document.getElementById('simCanvas');
const labelsContainer = document.getElementById('labelsContainer');
const loadingEl = document.getElementById('loading');
const runDurationInput = document.getElementById('runDurationInput');
const runStepsInput = document.getElementById('runStepsInput');
const runSummaryEl = document.getElementById('runSummary');
const runtimePresetsEl = document.getElementById('runtimePresets');
const advancedStepsRow = document.getElementById('advancedStepsRow');
const toggleAdvancedStepsEl = document.getElementById('toggleAdvancedSteps');

let BODY_COLORS = ['#4dabf7', '#ff6b6b', '#51cf66'];
let COM_COLOR = '#ffd43b';
let SUN_DIRECTION = new THREE.Vector3(320, 130, 230);
let SUN_COLOR = '#ffd27a';
const THREE_BODY_DT_SECONDS = 0.0005;
const PLUTO_DT_SECONDS = 1000;

let RUN_CONFIG = {
    three_body: {
        dt: THREE_BODY_DT_SECONDS,
        defaultDurationSec: 6.0,
        minDurationSec: 0.001,
        maxDurationSec: 60.0,
        durationStep: 0.1,
        durationDecimals: 3,
        presets: [
            { label: '3 s', seconds: 3 },
            { label: '6 s', seconds: 6 },
            { label: '12 s', seconds: 12 },
            { label: '30 s', seconds: 30 },
        ],
    },
    pluto_system: {
        dt: PLUTO_DT_SECONDS,
        defaultDurationSec: 4_000_000,
        minDurationSec: 1000,
        maxDurationSec: 4_000_000,
        durationStep: 1000,
        durationDecimals: 0,
        presets: [
            { label: '1 day', seconds: 86_400 },
            { label: '7 days', seconds: 604_800 },
            { label: '30 days', seconds: 2_592_000 },
            { label: '46 days', seconds: 4_000_000 },
        ],
    },
};

let PLUTO_VISUALS = {
    Pluto:   { color: '#b89a82', emissive: '#5f4738', trail: '#d3b59a', radius: 0.46, accent: '#ded1c4', crater: '#8b7663' },
    Charon:  { color: '#bfc6cc', emissive: '#606970', trail: '#d6dde3', radius: 0.34, accent: '#e0e4e8', crater: '#8d949b' },
    Styx:    { color: '#8aa4c8', emissive: '#334a66', trail: '#a5bddd', radius: 0.16, accent: '#b8c8de', crater: '#566b85' },
    Nix:     { color: '#8f9daf', emissive: '#3a4a5e', trail: '#afbdd1', radius: 0.18, accent: '#c2ccd9', crater: '#5d6d82' },
    Kerberos:{ color: '#b08d7a', emissive: '#5a4135', trail: '#caa894', radius: 0.17, accent: '#cdb29f', crater: '#7c5f50' },
    Hydra:   { color: '#9ba7b8', emissive: '#434f60', trail: '#b8c4d6', radius: 0.20, accent: '#c7d0dc', crater: '#667588' },
};
let PLUTO_VISUAL_FALLBACK = { color: '#d0d6de', emissive: '#5b6673', trail: '#c4cfdb', radius: 0.16, accent: '#e5e9ef', crater: '#909aa8' };
const bodyMapCache = new Map();

let VISUAL_CONFIG = {
    renderer: {
        toneMappingExposure: 1.05,
        shadowsEnabled: true,
    },
    ui_defaults: {
        showLabels: true,
        showTrails: true,
        showCOM: true,
    },
    camera: {
        fov: 60,
        minDistance: 0.2,
        maxDistance: 300,
        resetZ: {
            three_body: 20,
            pluto_system: 24,
        },
    },
    starfield: {
        count: 2000,
        minRadius: 300,
        maxRadius: 450,
        pointSize: 0.8,
        opacity: 0.6,
    },
    lighting: {
        ambient: { color: 0x404860, intensity: 0.22 },
        hemisphere: { skyColor: 0x8da4ff, groundColor: 0x111115, intensity: 0.22 },
        sun: {
            color: 0xfff1d8,
            intensity: 1.35,
            shadowMapSize: 2048,
            shadowBias: -0.00025,
            shadowNormalBias: 0.025,
            shadowNear: 1,
            shadowFar: 1000,
        },
        rim: { color: 0x7aa4ff, intensity: 0.34, oppositeScale: -0.48 },
        modes: {
            pluto_on: { ambient: 0.14, hemisphere: 0.20, sun: 1.35, rim: 0.34 },
            pluto_off: { ambient: 0.30, hemisphere: 0.30, sun: 0.0, rim: 0.0 },
            other: { ambient: 0.24, hemisphere: 0.22, sun: 1.15, rim: 0.30 },
        },
    },
    sun_visual: {
        radius: 4.8,
        haloScale: 1.9,
        haloOpacity: 0.18,
        haloColor: 0xffe4a8,
    },
    pluto_rendering: {
        sphereSegments: 42,
        fallbackSegments: 20,
        plutoBumpScale: 0.048,
        moonBumpScale: 0.034,
        plutoRoughness: 0.84,
        moonRoughness: 0.9,
        metalness: 0.02,
        emissiveIntensity: 0.045,
        glowScale: 1.1,
        glowOpacityPluto: 0.13,
        glowOpacityMoon: 0.08,
    },
    shadow: {
        orbitRadius: 13,
        sizeFactor: 1.45,
        minSize: 12,
    },
};

// Simulation state
let history = [];
let currentStep = 0;
let isPlaying = false;
let playSpeed = 5;
let showTrails = true;
let showLabels = true;
let showCOM = true;
let showSun = true;
let labelElements = {};
let visibleBodies = new Set();
let scenario = '';
let worldScale = 1;
let runControlsScenario = null;
let showAdvancedSteps = false;

let icState = {
    masses: [3.0, 4.0, 5.0],
    positions: [[1.0, 3.0], [-2.0, -1.0], [1.0, -1.0]],
    velocities: [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
};

function applyRenderConfig(config) {
    if (!config || typeof config !== 'object') return;

    if (Array.isArray(config.body_colors) && config.body_colors.length >= 3) {
        BODY_COLORS = config.body_colors;
    }
    if (typeof config.com_color === 'string') {
        COM_COLOR = config.com_color;
    }

    if (config.run_config && typeof config.run_config === 'object') {
        RUN_CONFIG = {
            ...RUN_CONFIG,
            ...config.run_config,
        };
    }

    if (config.pluto_visuals && typeof config.pluto_visuals === 'object') {
        PLUTO_VISUALS = {
            ...PLUTO_VISUALS,
            ...config.pluto_visuals,
        };
        bodyMapCache.clear();
    }

    if (config.pluto_visual_fallback && typeof config.pluto_visual_fallback === 'object') {
        PLUTO_VISUAL_FALLBACK = {
            ...PLUTO_VISUAL_FALLBACK,
            ...config.pluto_visual_fallback,
        };
        bodyMapCache.clear();
    }

    if (config.sun && typeof config.sun === 'object') {
        if (typeof config.sun.color === 'string') {
            SUN_COLOR = config.sun.color;
        }
        if (Array.isArray(config.sun.direction) && config.sun.direction.length === 3) {
            const [x, y, z] = config.sun.direction;
            if ([x, y, z].every(v => Number.isFinite(Number(v)))) {
                SUN_DIRECTION = new THREE.Vector3(Number(x), Number(y), Number(z));
            }
        }
        if (typeof config.sun.enabled_by_default === 'boolean') {
            showSun = config.sun.enabled_by_default;
        }
    }

    if (config.visual_config && typeof config.visual_config === 'object') {
        VISUAL_CONFIG = mergeConfig(VISUAL_CONFIG, config.visual_config);
    }

    if (VISUAL_CONFIG.ui_defaults && typeof VISUAL_CONFIG.ui_defaults === 'object') {
        if (typeof VISUAL_CONFIG.ui_defaults.showLabels === 'boolean') showLabels = VISUAL_CONFIG.ui_defaults.showLabels;
        if (typeof VISUAL_CONFIG.ui_defaults.showTrails === 'boolean') showTrails = VISUAL_CONFIG.ui_defaults.showTrails;
        if (typeof VISUAL_CONFIG.ui_defaults.showCOM === 'boolean') showCOM = VISUAL_CONFIG.ui_defaults.showCOM;
    }
}

function mergeConfig(baseObj, overrideObj) {
    const merged = { ...baseObj };
    Object.keys(overrideObj).forEach((key) => {
        const baseVal = baseObj[key];
        const overrideVal = overrideObj[key];
        if (
            baseVal && typeof baseVal === 'object' && !Array.isArray(baseVal) &&
            overrideVal && typeof overrideVal === 'object' && !Array.isArray(overrideVal)
        ) {
            merged[key] = mergeConfig(baseVal, overrideVal);
        } else {
            merged[key] = overrideVal;
        }
    });
    return merged;
}

function loadRenderConfig() {
    return fetch('/api/render-config')
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(cfg => applyRenderConfig(cfg))
        .catch(err => {
            console.warn('Using local fallback render config:', err);
        });
}

function hexToInt(hex) {
    return parseInt(hex.slice(1), 16);
}

function getScenarioRunConfig() {
    return RUN_CONFIG[scenario] || RUN_CONFIG.three_body;
}

function getPlutoVisual(name) {
    return PLUTO_VISUALS[name] || PLUTO_VISUAL_FALLBACK;
}

function seededRngFromString(seedStr) {
    let seed = 2166136261;
    for (let i = 0; i < seedStr.length; i++) {
        seed ^= seedStr.charCodeAt(i);
        seed = Math.imul(seed, 16777619);
    }
    return function() {
        seed += 0x6D2B79F5;
        let t = seed;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

function hexToRgb(hex) {
    const v = hexToInt(hex);
    return { r: (v >> 16) & 255, g: (v >> 8) & 255, b: v & 255 };
}

function rgbToCss(rgb) {
    const rr = Math.max(0, Math.min(255, Math.round(rgb.r)));
    const gg = Math.max(0, Math.min(255, Math.round(rgb.g)));
    const bb = Math.max(0, Math.min(255, Math.round(rgb.b)));
    return `rgb(${rr}, ${gg}, ${bb})`;
}

function blendRgb(a, b, t) {
    const k = Math.max(0, Math.min(1, t));
    return {
        r: a.r + (b.r - a.r) * k,
        g: a.g + (b.g - a.g) * k,
        b: a.b + (b.b - a.b) * k,
    };
}

function createBodySurfaceMaps(bodyName) {
    const key = `pluto:${bodyName}`;
    if (bodyMapCache.has(key)) return bodyMapCache.get(key);

    const visual = getPlutoVisual(bodyName);
    const baseRgb = hexToRgb(visual.color);
    const accentRgb = hexToRgb(visual.accent || visual.color);
    const craterRgb = hexToRgb(visual.crater || visual.emissive || visual.color);
    const rng = seededRngFromString(bodyName);

    const size = 512;
    const albedoCanvas = document.createElement('canvas');
    const bumpCanvas = document.createElement('canvas');
    albedoCanvas.width = size;
    albedoCanvas.height = size;
    bumpCanvas.width = size;
    bumpCanvas.height = size;

    const aCtx = albedoCanvas.getContext('2d');
    const bCtx = bumpCanvas.getContext('2d');

    aCtx.fillStyle = visual.color;
    aCtx.fillRect(0, 0, size, size);
    bCtx.fillStyle = '#808080';
    bCtx.fillRect(0, 0, size, size);

    for (let layer = 0; layer < 5; layer++) {
        const patches = 130 + layer * 95;
        const radiusMin = Math.max(1.5, 22 - layer * 4.2);
        const radiusMax = Math.max(radiusMin + 0.5, 36 - layer * 5.2);
        for (let i = 0; i < patches; i++) {
            const x = rng() * size;
            const y = rng() * size;
            const r = radiusMin + rng() * (radiusMax - radiusMin);
            const mixAmount = 0.18 + rng() * 0.82;
            const col = blendRgb(baseRgb, accentRgb, mixAmount);

            const albedoGrad = aCtx.createRadialGradient(x, y, 0, x, y, r);
            albedoGrad.addColorStop(0, rgbToCss(col));
            albedoGrad.addColorStop(1, 'rgba(0,0,0,0)');
            aCtx.globalAlpha = 0.04 + rng() * 0.07;
            aCtx.fillStyle = albedoGrad;
            aCtx.beginPath();
            aCtx.arc(x, y, r, 0, Math.PI * 2);
            aCtx.fill();

            const h = Math.round(128 + (rng() - 0.5) * 24);
            const bumpGrad = bCtx.createRadialGradient(x, y, 0, x, y, r);
            bumpGrad.addColorStop(0, `rgb(${h},${h},${h})`);
            bumpGrad.addColorStop(1, 'rgba(128,128,128,0)');
            bCtx.globalAlpha = 0.04 + rng() * 0.06;
            bCtx.fillStyle = bumpGrad;
            bCtx.beginPath();
            bCtx.arc(x, y, r, 0, Math.PI * 2);
            bCtx.fill();
        }
    }

    const craterCount = bodyName === 'Pluto' ? 120 : 64;
    for (let i = 0; i < craterCount; i++) {
        const x = rng() * size;
        const y = rng() * size;
        const r = bodyName === 'Pluto' ? (2 + rng() * 10) : (1.5 + rng() * 7);

        const craterGrad = aCtx.createRadialGradient(x, y, 0, x, y, r);
        craterGrad.addColorStop(0, rgbToCss(craterRgb));
        craterGrad.addColorStop(1, 'rgba(0,0,0,0)');
        aCtx.globalAlpha = 0.10 + rng() * 0.13;
        aCtx.fillStyle = craterGrad;
        aCtx.beginPath();
        aCtx.arc(x, y, r, 0, Math.PI * 2);
        aCtx.fill();

        const bumpGrad = bCtx.createRadialGradient(x, y, 0, x, y, r);
        bumpGrad.addColorStop(0, 'rgba(70,70,70,0.85)');
        bumpGrad.addColorStop(0.65, 'rgba(120,120,120,0.3)');
        bumpGrad.addColorStop(1, 'rgba(128,128,128,0)');
        bCtx.globalAlpha = 0.3;
        bCtx.fillStyle = bumpGrad;
        bCtx.beginPath();
        bCtx.arc(x, y, r * 1.05, 0, Math.PI * 2);
        bCtx.fill();
    }

    if (bodyName === 'Pluto') {
        const heartX = size * 0.58;
        const heartY = size * 0.52;
        const heartR = size * 0.15;
        const light = blendRgb(baseRgb, accentRgb, 0.95);

        aCtx.globalAlpha = 0.38;
        aCtx.fillStyle = rgbToCss(light);
        aCtx.beginPath();
        aCtx.arc(heartX - heartR * 0.6, heartY - heartR * 0.42, heartR, 0, Math.PI * 2);
        aCtx.arc(heartX + heartR * 0.46, heartY - heartR * 0.42, heartR * 0.92, 0, Math.PI * 2);
        aCtx.fill();
        aCtx.beginPath();
        aCtx.moveTo(heartX - heartR * 1.35, heartY - heartR * 0.04);
        aCtx.lineTo(heartX + heartR * 1.35, heartY - heartR * 0.04);
        aCtx.lineTo(heartX, heartY + heartR * 1.88);
        aCtx.closePath();
        aCtx.fill();

        bCtx.globalAlpha = 0.25;
        bCtx.fillStyle = '#9d9d9d';
        bCtx.beginPath();
        bCtx.ellipse(heartX, heartY + heartR * 0.2, heartR * 1.25, heartR * 1.05, 0, 0, Math.PI * 2);
        bCtx.fill();
    }

    aCtx.globalAlpha = 1;
    bCtx.globalAlpha = 1;

    const albedo = new THREE.CanvasTexture(albedoCanvas);
    albedo.wrapS = THREE.RepeatWrapping;
    albedo.wrapT = THREE.ClampToEdgeWrapping;
    albedo.encoding = THREE.sRGBEncoding;
    albedo.needsUpdate = true;

    const bump = new THREE.CanvasTexture(bumpCanvas);
    bump.wrapS = THREE.RepeatWrapping;
    bump.wrapT = THREE.ClampToEdgeWrapping;
    bump.needsUpdate = true;

    const maps = { albedo, bump };
    bodyMapCache.set(key, maps);
    return maps;
}

function formatDurationForInput(seconds, cfg) {
    if (cfg.durationDecimals === 0) return String(Math.round(seconds));
    return seconds.toFixed(cfg.durationDecimals);
}

function formatDurationHuman(seconds) {
    if (seconds >= 86400) return `${(seconds / 86400).toFixed(1)} days`;
    if (seconds >= 3600) return `${(seconds / 3600).toFixed(1)} hours`;
    if (seconds >= 1) return `${seconds.toFixed(2)} s`;
    return `${seconds.toFixed(4)} s`;
}

// ---- Three.js Setup ----
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x000000, 1);
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = VISUAL_CONFIG.renderer.toneMappingExposure;
if ('physicallyCorrectLights' in renderer) renderer.physicallyCorrectLights = true;
renderer.shadowMap.enabled = VISUAL_CONFIG.renderer.shadowsEnabled;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(VISUAL_CONFIG.camera.fov, window.innerWidth / window.innerHeight, 0.01, 5000);
camera.position.set(0, 0, VISUAL_CONFIG.camera.resetZ.three_body);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.screenSpacePanning = false;
controls.minDistance = VISUAL_CONFIG.camera.minDistance;
controls.maxDistance = VISUAL_CONFIG.camera.maxDistance;
controls.target.set(0, 0, 0);

let ambientLight = null;
let hemiLight = null;
let sunLight = null;
let rimLight = null;
let sunGroup = null;

function setupSystemLights() {
    ambientLight = new THREE.AmbientLight(
        VISUAL_CONFIG.lighting.ambient.color,
        VISUAL_CONFIG.lighting.ambient.intensity
    );
    scene.add(ambientLight);

    hemiLight = new THREE.HemisphereLight(
        VISUAL_CONFIG.lighting.hemisphere.skyColor,
        VISUAL_CONFIG.lighting.hemisphere.groundColor,
        VISUAL_CONFIG.lighting.hemisphere.intensity
    );
    scene.add(hemiLight);

    sunLight = new THREE.DirectionalLight(VISUAL_CONFIG.lighting.sun.color, VISUAL_CONFIG.lighting.sun.intensity);
    sunLight.position.copy(SUN_DIRECTION);
    sunLight.target.position.set(0, 0, 0);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = VISUAL_CONFIG.lighting.sun.shadowMapSize;
    sunLight.shadow.mapSize.height = VISUAL_CONFIG.lighting.sun.shadowMapSize;
    sunLight.shadow.bias = VISUAL_CONFIG.lighting.sun.shadowBias;
    sunLight.shadow.normalBias = VISUAL_CONFIG.lighting.sun.shadowNormalBias;
    sunLight.shadow.camera.near = VISUAL_CONFIG.lighting.sun.shadowNear;
    sunLight.shadow.camera.far = VISUAL_CONFIG.lighting.sun.shadowFar;
    scene.add(sunLight);
    scene.add(sunLight.target);

    rimLight = new THREE.DirectionalLight(VISUAL_CONFIG.lighting.rim.color, VISUAL_CONFIG.lighting.rim.intensity);
    rimLight.position.copy(SUN_DIRECTION).multiplyScalar(VISUAL_CONFIG.lighting.rim.oppositeScale);
    scene.add(rimLight);

    sunGroup = new THREE.Group();
    const sunCore = new THREE.Mesh(
        new THREE.SphereGeometry(VISUAL_CONFIG.sun_visual.radius, 28, 28),
        new THREE.MeshBasicMaterial({ color: hexToInt(SUN_COLOR) })
    );
    const sunHalo = new THREE.Mesh(
        new THREE.SphereGeometry(VISUAL_CONFIG.sun_visual.radius * VISUAL_CONFIG.sun_visual.haloScale, 26, 26),
        new THREE.MeshBasicMaterial({
            color: VISUAL_CONFIG.sun_visual.haloColor,
            transparent: true,
            opacity: VISUAL_CONFIG.sun_visual.haloOpacity,
            blending: THREE.AdditiveBlending,
            side: THREE.BackSide,
            depthWrite: false,
        })
    );
    sunGroup.position.copy(SUN_DIRECTION);
    sunGroup.add(sunCore);
    sunGroup.add(sunHalo);
    scene.add(sunGroup);
}

function refreshSunVisuals() {
    if (!sunLight || !rimLight || !sunGroup) return;
    sunLight.position.copy(SUN_DIRECTION);
    rimLight.position.copy(SUN_DIRECTION).multiplyScalar(VISUAL_CONFIG.lighting.rim.oppositeScale);
    sunGroup.position.copy(SUN_DIRECTION);
    if (sunGroup.children[0] && sunGroup.children[0].material) {
        sunGroup.children[0].material.color.set(hexToInt(SUN_COLOR));
    }
}

function configureSunShadowFrustum() {
    if (!sunLight) return;
    const orbitRadius = VISUAL_CONFIG.shadow.orbitRadius;
    const cameraSize = Math.max(VISUAL_CONFIG.shadow.minSize, orbitRadius * VISUAL_CONFIG.shadow.sizeFactor);
    sunLight.shadow.camera.left = -cameraSize;
    sunLight.shadow.camera.right = cameraSize;
    sunLight.shadow.camera.top = cameraSize;
    sunLight.shadow.camera.bottom = -cameraSize;
    sunLight.shadow.camera.updateProjectionMatrix();
    sunLight.target.position.set(0, 0, 0);
    sunLight.target.updateMatrixWorld();
}

function applySunLightingMode() {
    if (!ambientLight || !hemiLight || !sunLight || !rimLight || !sunGroup) return;
    const usePlutoLighting = scenario === 'pluto_system';
    const sunOn = usePlutoLighting && showSun;

    const mode = usePlutoLighting
        ? (sunOn ? VISUAL_CONFIG.lighting.modes.pluto_on : VISUAL_CONFIG.lighting.modes.pluto_off)
        : VISUAL_CONFIG.lighting.modes.other;

    ambientLight.intensity = mode.ambient;
    hemiLight.intensity = mode.hemisphere;
    sunLight.intensity = mode.sun;
    rimLight.intensity = mode.rim;

    sunGroup.visible = sunOn;
    sunLight.castShadow = sunOn;
    renderer.shadowMap.enabled = sunOn;

    bodyMeshes.forEach((mesh) => {
        mesh.castShadow = sunOn;
        mesh.receiveShadow = sunOn;
    });
}

setupSystemLights();
refreshSunVisuals();

// Scene object handles
let bodyMeshes = [], trailLines = [], comGroup = null, starPoints = null;

// ---- Resize ----
function resizeCanvas() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    buildStarfield();
}
window.addEventListener('resize', resizeCanvas);

// ---- Starfield ----
function buildStarfield() {
    if (starPoints) { scene.remove(starPoints); starPoints.geometry.dispose(); starPoints.material.dispose(); }
    const n = VISUAL_CONFIG.starfield.count;
    const pos = new Float32Array(n * 3);
    const minRadius = VISUAL_CONFIG.starfield.minRadius;
    const maxRadius = VISUAL_CONFIG.starfield.maxRadius;
    for (let i = 0; i < n; i++) {
        const phi = Math.acos(2 * Math.random() - 1);
        const theta = Math.random() * Math.PI * 2;
        const r = minRadius + Math.random() * (maxRadius - minRadius);
        pos[i*3]   = r * Math.sin(phi) * Math.cos(theta);
        pos[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
        pos[i*3+2] = r * Math.cos(phi);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    starPoints = new THREE.Points(geo, new THREE.PointsMaterial({
        color: 0xffffff,
        size: VISUAL_CONFIG.starfield.pointSize,
        sizeAttenuation: true,
        transparent: true,
        opacity: VISUAL_CONFIG.starfield.opacity,
    }));
    scene.add(starPoints);
}

// ---- World scale ----
function computeWorldScale() {
    let maxR = 0;
    for (const frame of history) {
        for (const b of frame.bodies) {
            maxR = Math.max(maxR, Math.abs(b.position[0]), Math.abs(b.position[1]));
        }
    }
    worldScale = 12 / (maxR || 1);
}

// ---- Build / dispose Three.js scene objects ----
function disposeSceneObjects() {
    bodyMeshes.forEach((mesh) => {
        mesh.traverse((child) => {
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (Array.isArray(child.material)) child.material.forEach(m => m.dispose());
                else child.material.dispose();
            }
        });
        scene.remove(mesh);
    });
    trailLines.forEach((line) => {
        scene.remove(line);
        line.geometry.dispose();
        line.material.dispose();
    });
    bodyMeshes = [];
    trailLines = [];
    if (comGroup) {
        comGroup.traverse(c => {
            if (c.geometry) c.geometry.dispose();
            if (c.material) c.material.dispose();
        });
        scene.remove(comGroup);
        comGroup = null;
    }
}

function buildSceneObjects() {
    disposeSceneObjects();
    if (!history.length) return;
    const s0 = history[0];

    s0.bodies.forEach((body, i) => {
        const style = scenario === 'three_body'
            ? {
                color: BODY_COLORS[i % BODY_COLORS.length],
                emissive: BODY_COLORS[i % BODY_COLORS.length],
                trail: BODY_COLORS[i % BODY_COLORS.length],
                radius: 0.08 + Math.sqrt(body.mass) * 0.07,
            }
            : getPlutoVisual(body.name);
        const col = hexToInt(style.color);
        const emissive = hexToInt(style.emissive || style.color);
        const r = style.radius;
        const sphereSegments = scenario === 'pluto_system'
            ? VISUAL_CONFIG.pluto_rendering.sphereSegments
            : VISUAL_CONFIG.pluto_rendering.fallbackSegments;

        const bodyMaps = scenario === 'pluto_system' ? createBodySurfaceMaps(body.name) : null;
        const material = scenario === 'pluto_system'
            ? new THREE.MeshStandardMaterial({
                color: col,
                map: bodyMaps.albedo,
                bumpMap: bodyMaps.bump,
                bumpScale: body.name === 'Pluto'
                    ? VISUAL_CONFIG.pluto_rendering.plutoBumpScale
                    : VISUAL_CONFIG.pluto_rendering.moonBumpScale,
                emissive,
                emissiveIntensity: VISUAL_CONFIG.pluto_rendering.emissiveIntensity,
                roughness: body.name === 'Pluto'
                    ? VISUAL_CONFIG.pluto_rendering.plutoRoughness
                    : VISUAL_CONFIG.pluto_rendering.moonRoughness,
                metalness: VISUAL_CONFIG.pluto_rendering.metalness,
            })
            : new THREE.MeshPhongMaterial({
                color: col,
                emissive,
                emissiveIntensity: 0.35,
                shininess: 35,
            });

        const mesh = new THREE.Mesh(
            new THREE.SphereGeometry(r, sphereSegments, sphereSegments),
            material
        );

        if (scenario === 'pluto_system') {
            const glowCol = hexToInt(style.accent || style.color);
            const glow = new THREE.Mesh(
                new THREE.SphereGeometry(r * VISUAL_CONFIG.pluto_rendering.glowScale, 26, 26),
                new THREE.MeshBasicMaterial({
                    color: glowCol,
                    transparent: true,
                    opacity: body.name === 'Pluto'
                        ? VISUAL_CONFIG.pluto_rendering.glowOpacityPluto
                        : VISUAL_CONFIG.pluto_rendering.glowOpacityMoon,
                    blending: THREE.AdditiveBlending,
                    side: THREE.BackSide,
                    depthWrite: false,
                })
            );
            mesh.add(glow);
        }

        mesh.castShadow = scenario === 'pluto_system' && showSun;
        mesh.receiveShadow = scenario === 'pluto_system' && showSun;
        scene.add(mesh);
        bodyMeshes.push(mesh);

        const pts = new Float32Array(history.length * 3);
        for (let s = 0; s < history.length; s++) {
            const p = history[s].bodies[i].position;
            pts[s * 3] = p[0] * worldScale;
            pts[s * 3 + 1] = p[1] * worldScale;
            pts[s * 3 + 2] = 0;
        }
        const tGeo = new THREE.BufferGeometry();
        tGeo.setAttribute('position', new THREE.BufferAttribute(pts, 3));
        tGeo.setDrawRange(0, 0);
        const tCol = hexToInt(style.trail || style.color);
        const line = new THREE.Line(tGeo, new THREE.LineBasicMaterial({ color: tCol, transparent: true, opacity: 0.55 }));
        scene.add(line);
        trailLines.push(line);
    });

    comGroup = new THREE.Group();
    comGroup.add(new THREE.Mesh(
        new THREE.SphereGeometry(0.1, 8, 8),
        new THREE.MeshBasicMaterial({ color: hexToInt(COM_COLOR) })
    ));
    const cg = new THREE.BufferGeometry();
    cg.setAttribute('position', new THREE.BufferAttribute(
        new Float32Array([-0.45, 0, 0, 0.45, 0, 0, 0, -0.45, 0, 0, 0.45, 0]), 3
    ));
    comGroup.add(new THREE.LineSegments(cg, new THREE.LineBasicMaterial({
        color: hexToInt(COM_COLOR),
        transparent: true,
        opacity: 0.5,
    })));
    scene.add(comGroup);

    configureSunShadowFrustum();
    applySunLightingMode();

    camera.position.set(0, 0,
        scenario === 'pluto_system'
            ? VISUAL_CONFIG.camera.resetZ.pluto_system
            : VISUAL_CONFIG.camera.resetZ.three_body
    );
    camera.up.set(0, 1, 0);
    controls.target.set(0, 0, 0);
    controls.update();
}

// ---- Data fetching ----
function fetchSimulation(customParams) {
    scenario = new URLSearchParams(window.location.search).get('scenario') || 'pluto_system';
    loadingEl.style.display = '';
    let url = `/api/simulate/${scenario}`;
    if (customParams) url += '?' + customParams;
    fetch(url)
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            loadingEl.style.display = 'none';
            if (data.error) {
                loadingEl.style.display = '';
                loadingEl.textContent = 'Error: ' + data.error;
                return;
            }
            history = data.history;
            currentStep = 0;
            clearLabels();
            initVisibility();
            computeWorldScale();
            buildSceneObjects();
            populateDropdowns();
            populateObjectsList();
            setupScenarioUI();
            document.getElementById('timeSlider').max = history.length - 1;
        })
        .catch(err => {
            loadingEl.textContent = 'Error loading simulation';
            console.error(err);
        });
}

function clearLabels() {
    labelsContainer.innerHTML = '';
    labelElements = {};
}

function initVisibility() {
    if (!history.length) return;
    visibleBodies = new Set(history[0].bodies.map(b => b.name));
}

function setupScenarioUI() {
    const isThreeBody = scenario === 'three_body';
    const scenarioChanged = runControlsScenario !== scenario;
    const icTabBtn = document.getElementById('icTabBtn');
    const showCOMCheck = document.getElementById('showCOMCheck');
    const showSunRow = document.getElementById('showSunRow');
    const showSunCheck = document.getElementById('showSunCheck');
    const icEditorSection = document.getElementById('icEditorSection');
    const randomizeBtn = document.getElementById('randomizeBtn');
    const runBtn = document.getElementById('runBtn');

    icTabBtn.style.display = '';
    icTabBtn.textContent = isThreeBody ? 'Initial Cond.' : 'Run Setup';
    icEditorSection.style.display = isThreeBody ? '' : 'none';
    randomizeBtn.style.display = isThreeBody ? '' : 'none';
    runBtn.textContent = isThreeBody ? 'Run Simulation' : 'Run Pluto Simulation';
    showSunRow.style.display = isThreeBody ? 'none' : '';
    showSunCheck.checked = showSun;

    if (isThreeBody) {
        const s0 = history[0];
        icState.masses = s0.bodies.map(b => b.mass);
        icState.positions = s0.bodies.map(b => [b.position[0], b.position[1]]);
        icState.velocities = s0.bodies.map(b => [b.velocity[0], b.velocity[1]]);
        buildICEditor();
    }

    if (scenarioChanged) {
        showCOM = isThreeBody;
        showCOMCheck.checked = showCOM;
    }

    setupRunControls();
    applySunLightingMode();
}

function buildICEditor() {
    const editor = document.getElementById('icEditor');
    editor.innerHTML = '';
    for (let i = 0; i < 3; i++) {
        const color = BODY_COLORS[i];
        const div = document.createElement('div');
        div.className = 'ic-body';
        div.style.borderLeftColor = color;
        div.innerHTML = `
            <h4 style="color:${color}">Body ${i + 1}</h4>
            <div class="ic-row"><label>Mass</label><input type="number" step="0.1" data-i="${i}" data-field="mass" value="${icState.masses[i].toFixed(2)}"></div>
            <div class="ic-row"><label>X</label><input type="number" step="0.1" data-i="${i}" data-field="px" value="${icState.positions[i][0].toFixed(3)}">
                                <label>Y</label><input type="number" step="0.1" data-i="${i}" data-field="py" value="${icState.positions[i][1].toFixed(3)}"></div>
            <div class="ic-row"><label>Vx</label><input type="number" step="0.1" data-i="${i}" data-field="vx" value="${icState.velocities[i][0].toFixed(3)}">
                                <label>Vy</label><input type="number" step="0.1" data-i="${i}" data-field="vy" value="${icState.velocities[i][1].toFixed(3)}"></div>
        `;
        editor.appendChild(div);
    }
    editor.querySelectorAll('input').forEach(inp => {
        inp.addEventListener('change', () => {
            const i = parseInt(inp.dataset.i);
            const v = parseFloat(inp.value);
            switch (inp.dataset.field) {
                case 'mass': icState.masses[i] = v; break;
                case 'px': icState.positions[i][0] = v; break;
                case 'py': icState.positions[i][1] = v; break;
                case 'vx': icState.velocities[i][0] = v; break;
                case 'vy': icState.velocities[i][1] = v; break;
            }
        });
    });
}

function setRunSummary(durationSec, steps, cfg) {
    runSummaryEl.textContent = `${steps.toLocaleString()} steps • Δt=${cfg.dt}s • total ${formatDurationHuman(durationSec)}`;
}

function syncDurationToSteps(normalize = false) {
    const cfg = getScenarioRunConfig();
    let durationSec = Number.parseFloat(runDurationInput.value);
    if (!Number.isFinite(durationSec) || durationSec <= 0) {
        durationSec = cfg.defaultDurationSec;
    }
    durationSec = Math.max(cfg.minDurationSec, Math.min(cfg.maxDurationSec, durationSec));
    const steps = Math.max(1, Math.round(durationSec / cfg.dt));
    runStepsInput.value = String(steps);
    if (normalize) {
        runDurationInput.value = formatDurationForInput(durationSec, cfg);
    }
    setRunSummary(durationSec, steps, cfg);
    return { durationSec, steps, cfg };
}

function syncStepsToDuration(normalize = false) {
    const cfg = getScenarioRunConfig();
    let steps = Number.parseInt(runStepsInput.value, 10);
    if (!Number.isFinite(steps) || steps < 1) {
        steps = Math.max(1, Math.round(cfg.defaultDurationSec / cfg.dt));
    }
    const durationSec = Math.max(cfg.minDurationSec, steps * cfg.dt);
    if (normalize) {
        runStepsInput.value = String(steps);
    }
    runDurationInput.value = formatDurationForInput(durationSec, cfg);
    setRunSummary(durationSec, steps, cfg);
    return { durationSec, steps, cfg };
}

function renderRuntimePresets() {
    const cfg = getScenarioRunConfig();
    runtimePresetsEl.innerHTML = '';
    cfg.presets.forEach((preset) => {
        const btn = document.createElement('button');
        btn.className = 'preset-btn';
        btn.type = 'button';
        btn.textContent = preset.label;
        btn.addEventListener('click', () => {
            runDurationInput.value = formatDurationForInput(preset.seconds, cfg);
            syncDurationToSteps(true);
        });
        runtimePresetsEl.appendChild(btn);
    });
}

function bindRunControlEvents() {
    if (runDurationInput.dataset.bound === '1') return;
    runDurationInput.addEventListener('input', () => syncDurationToSteps(false));
    runDurationInput.addEventListener('change', () => syncDurationToSteps(true));
    runStepsInput.addEventListener('input', () => syncStepsToDuration(false));
    runStepsInput.addEventListener('change', () => syncStepsToDuration(true));
    toggleAdvancedStepsEl.addEventListener('click', (e) => {
        e.preventDefault();
        showAdvancedSteps = !showAdvancedSteps;
        advancedStepsRow.style.display = showAdvancedSteps ? '' : 'none';
        toggleAdvancedStepsEl.textContent = showAdvancedSteps ? 'Advanced: hide steps' : 'Advanced: show steps';
    });
    runDurationInput.dataset.bound = '1';
}

function setupRunControls() {
    bindRunControlEvents();
    const cfg = getScenarioRunConfig();
    runDurationInput.min = String(cfg.minDurationSec);
    runDurationInput.max = String(cfg.maxDurationSec);
    runDurationInput.step = String(cfg.durationStep);

    if (runControlsScenario !== scenario) {
        runDurationInput.value = formatDurationForInput(cfg.defaultDurationSec, cfg);
        runControlsScenario = scenario;
    }
    renderRuntimePresets();
    syncDurationToSteps(true);
}

function runSimulation() {
    const { steps, cfg } = syncDurationToSteps(true);
    const params = new URLSearchParams({
        dt: String(cfg.dt),
        steps: String(steps),
    });

    if (scenario === 'three_body') {
        const pos = icState.positions.flat().join(',');
        const vel = icState.velocities.flat().join(',');
        const mass = icState.masses.join(',');
        params.set('pos', pos);
        params.set('vel', vel);
        params.set('mass', mass);
    }

    fetchSimulation(params.toString());
}

function randomizeIC() {
    for (let i = 0; i < 3; i++) {
        icState.masses[i] = +(1 + Math.random() * 5).toFixed(2);
        icState.positions[i] = [+((Math.random() - 0.5) * 4).toFixed(3), +((Math.random() - 0.5) * 4).toFixed(3)];
        icState.velocities[i] = [0, 0];
    }
    buildICEditor();
    runSimulation();
}

document.getElementById('runBtn').addEventListener('click', runSimulation);
document.getElementById('randomizeBtn').addEventListener('click', randomizeIC);

function populateDropdowns() {
    if (!history.length) return;
    const names = history[0].bodies.map(b => b.name);
    const sel = document.getElementById('cameraFocus');
    const cur = sel.value;
    sel.innerHTML = '<option value="barycenter">Barycenter</option>';
    names.forEach(n => {
        const opt = document.createElement('option');
        opt.value = n;
        opt.textContent = n;
        sel.appendChild(opt);
    });
    const preferred = scenario === 'pluto_system' ? 'Pluto' : 'barycenter';
    sel.value = names.includes(cur) || cur === 'barycenter' ? cur : preferred;
}

function populateObjectsList() {
    const list = document.getElementById('objectsList');
    list.innerHTML = '';
    if (!history.length) return;
    const allNames = [...history[0].bodies.map(b => b.name)];
    allNames.forEach(name => {
        const label = document.createElement('label');
        label.className = 'checkbox-row';
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = visibleBodies.has(name);
        cb.addEventListener('change', () => {
            if (cb.checked) visibleBodies.add(name); else visibleBodies.delete(name);
            clearLabels();
        });
        label.appendChild(cb);
        const span = document.createElement('span');
        const bodyIdx = history[0].bodies.findIndex(b => b.name === name);
        if (bodyIdx >= 0) {
            span.style.color = scenario === 'three_body'
                ? BODY_COLORS[bodyIdx % BODY_COLORS.length]
                : getPlutoVisual(name).color;
        }
        span.textContent = name;
        label.appendChild(span);
        list.appendChild(label);
    });
}

// ---- Physics helpers ----
function getBarycenter(state) {
    let tm = 0, cx = 0, cy = 0;
    for (const b of state.bodies) {
        tm += b.mass;
        cx += b.position[0] * b.mass;
        cy += b.position[1] * b.mass;
    }
    return [cx / tm, cy / tm];
}

function getFocusPosition(state) {
    const focus = document.getElementById('cameraFocus').value;
    if (focus === 'barycenter') return getBarycenter(state);
    const body = state.bodies.find(b => b.name === focus);
    return body ? [...body.position] : getBarycenter(state);
}

// ---- Rendering (called every animation frame) ----
function draw() {
    if (!history.length) return;
    const state = history[currentStep];

    state.bodies.forEach((body, i) => {
        const vis = visibleBodies.has(body.name);
        if (i < bodyMeshes.length) {
            bodyMeshes[i].visible = vis;
            bodyMeshes[i].position.set(
                body.position[0] * worldScale,
                body.position[1] * worldScale,
                0
            );
        }
        if (i < trailLines.length) {
            trailLines[i].visible = vis && showTrails;
            if (vis && showTrails) trailLines[i].geometry.setDrawRange(0, currentStep + 1);
        }
    });

    if (comGroup) {
        const com = getBarycenter(state);
        comGroup.position.set(com[0] * worldScale, com[1] * worldScale, 0);
        comGroup.visible = showCOM;
    }

    Object.values(labelElements).forEach(el => el.style.display = 'none');
    if (showLabels) {
        state.bodies.forEach((body, i) => {
            if (!visibleBodies.has(body.name) || i >= bodyMeshes.length) return;
            const sp = projectToScreen(bodyMeshes[i].position);
            if (!sp) return;
            const col = scenario === 'three_body'
                ? BODY_COLORS[i % BODY_COLORS.length]
                : getPlutoVisual(body.name).color;
            const pxR = scenario === 'three_body'
                ? (10 + Math.sqrt(body.mass) * 5)
                : (8 + getPlutoVisual(body.name).radius * 12);
            setLabel(i, body.name, sp.x + pxR, sp.y - 4, col);
        });
    }

    document.getElementById('timeDisplay').textContent = scenario === 'pluto_system'
        ? (state.time / 86400).toFixed(1) + ' days'
        : 't = ' + state.time.toFixed(2) + ' s';
    document.getElementById('timeSlider').value = currentStep;
}

function projectToScreen(pos3D) {
    const v = pos3D.clone().project(camera);
    if (v.z > 1) return null;
    return {
        x: Math.round((v.x + 1) / 2 * window.innerWidth),
        y: Math.round((-v.y + 1) / 2 * window.innerHeight)
    };
}

function setLabel(key, text, x, y, color) {
    if (!labelElements[key]) {
        const el = document.createElement('div');
        el.className = 'body-label';
        el.textContent = text;
        labelsContainer.appendChild(el);
        labelElements[key] = el;
    }
    const el = labelElements[key];
    el.style.left = x + 'px';
    el.style.top = y + 'px';
    el.style.color = color || '#ddd';
    el.style.display = '';
}

// ---- Animation loop ----
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    if (isPlaying && history.length > 0 && currentStep < history.length - 1) {
        currentStep = Math.min(currentStep + playSpeed, history.length - 1);
        if (currentStep >= history.length - 1) {
            isPlaying = false;
            document.getElementById('playPauseBtn').innerHTML = '&#9654;';
        }
    }
    draw();
    renderer.render(scene, camera);
}

// ---- Event handlers ----
document.getElementById('playPauseBtn').addEventListener('click', () => {
    if (currentStep >= history.length - 1) currentStep = 0;
    isPlaying = !isPlaying;
    document.getElementById('playPauseBtn').innerHTML = isPlaying ? '&#9646;&#9646;' : '&#9654;';
});

document.getElementById('resetBtn').addEventListener('click', () => {
    currentStep = 0;
    isPlaying = false;
    document.getElementById('playPauseBtn').innerHTML = '&#9654;';
});

document.getElementById('timeSlider').addEventListener('input', e => {
    currentStep = parseInt(e.target.value);
});

document.getElementById('speedSlider').addEventListener('input', e => {
    playSpeed = parseInt(e.target.value);
    document.getElementById('speedValue').textContent = playSpeed + 'x';
});

document.getElementById('cameraFocus').addEventListener('change', () => {
    if (!history.length) return;
    const fp = getFocusPosition(history[currentStep]);
    controls.target.set(fp[0] * worldScale, fp[1] * worldScale, 0);
    controls.update();
});

document.getElementById('showLabelsCheck').addEventListener('change', e => {
    showLabels = e.target.checked;
});

document.getElementById('showTrailsCheck').addEventListener('change', e => {
    showTrails = e.target.checked;
});

document.getElementById('showCOMCheck').addEventListener('change', e => {
    showCOM = e.target.checked;
});

document.getElementById('showSunCheck').addEventListener('change', e => {
    showSun = e.target.checked;
    applySunLightingMode();
});

renderer.domElement.addEventListener('dblclick', () => {
    if (!history.length) return;
    const fp = getFocusPosition(history[currentStep]);
    controls.target.set(fp[0] * worldScale, fp[1] * worldScale, 0);
    camera.position.set(
        controls.target.x,
        controls.target.y,
        scenario === 'pluto_system'
            ? VISUAL_CONFIG.camera.resetZ.pluto_system
            : VISUAL_CONFIG.camera.resetZ.three_body
    );
    controls.update();
});

// Panel / tab handling
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('panelTitle').textContent = btn.textContent.trim();
        document.getElementById('sidePanel').classList.add('open');
    });
});

document.getElementById('closePanelBtn').addEventListener('click', () => {
    document.getElementById('sidePanel').classList.remove('open');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
});

document.querySelectorAll('.panel-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab + 'Tab').classList.add('active');
    });
});

setTimeout(() => {
    const hint = document.getElementById('viewHint');
    if (hint) {
        hint.style.opacity = '0';
        setTimeout(() => hint.remove(), 1500);
    }
}, 5000);

loadRenderConfig().finally(() => {
    refreshSunVisuals();
    resizeCanvas();
    fetchSimulation();
    animate();

    const showLabelsCheck = document.getElementById('showLabelsCheck');
    const showTrailsCheck = document.getElementById('showTrailsCheck');
    const showCOMCheck = document.getElementById('showCOMCheck');
    if (showLabelsCheck) showLabelsCheck.checked = showLabels;
    if (showTrailsCheck) showTrailsCheck.checked = showTrails;
    if (showCOMCheck) showCOMCheck.checked = showCOM;
});