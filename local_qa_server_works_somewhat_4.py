from flask import Flask, render_template_string, request, jsonify, send_from_directory
import google.generativeai as genai
import os
from gtts import gTTS
import base64
from io import BytesIO

app = Flask(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
conversation_history = {}  # session_id -> list of (question, answer)

# Read the text file
def read_context_file(filepath='resume.txt'):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Context file not found."

def text_to_speech(text):
    """Convert text to speech and return base64 encoded audio"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
        return audio_base64
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        return None

@app.route('/model/<path:filename>')
def serve_model(filename):
    """Serve 3D model files"""
    return send_from_directory('.', filename)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>3D Avatar Q&A with Lip Sync</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1f2126 0%, #0f1115 100%);
            overflow: hidden;
            height: 100vh;
        }
        #canvas-container {
            width: 100%;
            height: 100vh;
            position: relative;
        }
        .ui-overlay {
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
            text-align: center;
        }
        .mic-button {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            border: none;
            background: rgba(255, 255, 255, 0.95);
            color: #667eea;
            font-size: 36px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s;
            margin: 0 auto;
        }
        .mic-button:hover {
            transform: scale(1.1);
        }
        .mic-button.recording {
            background: #f5576c;
            color: white;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(245, 87, 108, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(245, 87, 108, 0); }
            100% { box-shadow: 0 0 0 0 rgba(245, 87, 108, 0); }
        }
        .status {
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            margin-top: 15px;
            font-size: 14px;
            backdrop-filter: blur(10px);
            display: inline-block;
        }
        .transcript {
            position: absolute;
            top: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 30px;
            border-radius: 15px;
            max-width: 600px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            display: none;
            animation: slideDown 0.3s ease;
        }
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
        .transcript-text {
            color: #333;
            font-style: italic;
            margin-bottom: 10px;
        }
        .answer-text {
            color: #555;
            line-height: 1.6;
        }
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            display: none;
            color: white;
            text-align: center;
        }
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        audio {
            display: none;
        }
        .instructions {
            position: absolute;
            top: 30px;
            right: 30px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            font-size: 12px;
            backdrop-filter: blur(10px);
        }
        .instructions h4 {
            margin-bottom: 8px;
        }
        .instructions p {
            margin: 4px 0;
        }
        .debug-panel {
            position: absolute;
            bottom: 30px;
            left: 30px;
            background: rgba(0, 0, 0, 0.8);
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 11px;
            max-width: 300px;
        }
        .debug-panel h4 {
            color: #00ff00;
            margin-bottom: 8px;
        }

        .suggestions-left, .suggestions-right {
        position: absolute;
        top: 150px;
        z-index: 50;
        color: rgba(255, 230, 174, 0.8);
        font-family: 'American Typewriter', serif;
        font-size: 25px;
        line-height: 1.8;
        pointer-events: none;
          }

        .suggestions-left {
            left: 40px;
            text-align: left;
            max-width: 400px;
        }

        .suggestions-right {
            right: 40px;
            text-align: right;
            max-width: 500px;
        }
    </style>
</head>

<body>
    <div id="canvas-container"></div>
    
    <div class="suggestions-right">
    <p>“Tell me about your MSc in AI.”</p>
    <p> </p>
    <p>“What AI tools do you use most?”</p>
    <p> </p>
    <p>“What are your publications?”</p>
    </div>

    <div class="suggestions-left">
    <p>Ask me about my experience</p>
    <p> </p>
    <p>Ask me about my projects</p>
    <p> </p>
    <p>Ask me about my research</p>   
    </div>
    
    <div class="debug-panel" id="debugPanel">
          <h4>Debug Info</h4>
          <div>Lipsync: <span id="lipsyncStatus">Not initialized</span></div>
          <div>Viseme: <span id="currentViseme">-</span></div>
          <div>Morph meshes: <span id="morphCount">0</span></div>
          <div>Speaking: <span id="speakingStatus">No</span></div>
    </div>
    
    <div class="transcript" id="transcript">
        <div class="transcript-text" id="transcriptText"></div>
        <div class="answer-text" id="answerText"></div>
    </div>
    
    <div class="loading" id="loading">
        <div class="spinner"></div>
        <p>Processing...</p>
    </div>
    
    <div class="ui-overlay">
        <button class="mic-button" id="micButton" onclick="toggleRecording()">🎤</button>
        <div class="status" id="status">Click to speak</div>
    </div>
    
    <audio id="audioPlayer"></audio>

    <!-- Load Three.js and GLTFLoader -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    
    <!-- Load wawa-lipsync via UMD - try multiple sources -->
    <script src="https://unpkg.com/wawa-lipsync@1.0.2/dist/index.umd.js" 
            onerror="console.error('Failed to load from unpkg, trying jsdelivr...'); this.onerror=null; this.src='https://cdn.jsdelivr.net/npm/wawa-lipsync@1.0.2/dist/index.umd.js'"></script>
    
    <script>
        let scene, camera, renderer, avatar, mixer, clock;
        let isRecording = false;
        let recognition;
        let isSpeaking = false;
        let lipsyncManager;
        let morphTargetMeshes = [];
        let audioContext, analyser, dataArray;
        let useFallbackLipsync = false;
        
        // Animation state
        let eyeBlinkTimer = 0;
        let eyeBlinkDuration = 0;
        let isBlinking = false;
        let idleAnimationTime = 0;
        let headBone = null;
        let neckBone = null;
        let spineBone = null;

        // Complete Oculus Viseme to morph target mapping (Ready Player Me standard)
        // Ready Player Me uses these exact names in their avatars
        const visemeMapping = {
            'sil': 'viseme_sil',      // Silence
            'A': 'viseme_aa',          // A, I, Y
            'B': 'viseme_PP',          // B, M, P
            'C': 'viseme_CH',          // CH, J, SH, ZH
            'D': 'viseme_DD',          // D, T, N
            'E': 'viseme_E',           // E
            'F': 'viseme_FF',          // F, V
            'G': 'viseme_kk',          // G, K, N (back)
            'H': 'viseme_I',           // I, Y
            'X': 'viseme_nn',          // N, NG
            'O': 'viseme_O',           // O
            'P': 'viseme_PP',          // P, B, M
            'R': 'viseme_RR',          // R
            'S': 'viseme_SS',          // S, Z
            'T': 'viseme_TH',          // TH
            'U': 'viseme_U'            // U, W
        };
        
        // Alternative naming variations (case-insensitive matching)
        const visemeNameVariations = {
            'viseme_aa': ['viseme_aa', 'viseme_AA', 'viseme_A', 'viseme_a'],
            'viseme_PP': ['viseme_PP', 'viseme_pp', 'viseme_P', 'viseme_p', 'viseme_B', 'viseme_b'],
            'viseme_CH': ['viseme_CH', 'viseme_ch', 'viseme_C', 'viseme_c'],
            'viseme_DD': ['viseme_DD', 'viseme_dd', 'viseme_D', 'viseme_d'],
            'viseme_E': ['viseme_E', 'viseme_e'],
            'viseme_FF': ['viseme_FF', 'viseme_ff', 'viseme_F', 'viseme_f'],
            'viseme_kk': ['viseme_kk', 'viseme_KK', 'viseme_K', 'viseme_k', 'viseme_G', 'viseme_g'],
            'viseme_I': ['viseme_I', 'viseme_i'],
            'viseme_nn': ['viseme_nn', 'viseme_NN', 'viseme_N', 'viseme_n'],
            'viseme_O': ['viseme_O', 'viseme_o'],
            'viseme_RR': ['viseme_RR', 'viseme_rr', 'viseme_R', 'viseme_r'],
            'viseme_SS': ['viseme_SS', 'viseme_ss', 'viseme_S', 'viseme_s'],
            'viseme_TH': ['viseme_TH', 'viseme_th', 'viseme_T', 'viseme_t'],
            'viseme_U': ['viseme_U', 'viseme_u'],
            'viseme_sil': ['viseme_sil', 'viseme_SIL', 'viseme_Sil', 'viseme_silence']
        };
        
        // Store discovered morph targets for each mesh
        const discoveredMorphTargets = new Map();
        let lastViseme = 'X';
        let visemeTransition = 0; // For smooth interpolation
        const visemeBlendDamping = 0.18; // Lower = smoother lip motion

        function smoothMorphInfluence(mesh, morphIndex, targetValue, damping = visemeBlendDamping) {
            const current = mesh.morphTargetInfluences[morphIndex] || 0;
            mesh.morphTargetInfluences[morphIndex] = THREE.MathUtils.lerp(current, targetValue, damping);
        }

        // Initialize lipsync manager
        function initLipsync() {
            // Try multiple possible ways the library might be exposed
            if (window.WawaLipsync && window.WawaLipsync.Lipsync) {
                lipsyncManager = new window.WawaLipsync.Lipsync();
                console.log('✓ Lip sync initialized (WawaLipsync.Lipsync)');
                document.getElementById('lipsyncStatus').textContent = 'Ready';
                document.getElementById('lipsyncStatus').style.color = '#00ff00';
                return true;
            } else if (window.Lipsync) {
                lipsyncManager = new window.Lipsync();
                console.log('✓ Lip sync initialized (window.Lipsync)');
                document.getElementById('lipsyncStatus').textContent = 'Ready';
                document.getElementById('lipsyncStatus').style.color = '#00ff00';
                return true;
            } else if (window.lipsync) {
                lipsyncManager = window.lipsync;
                console.log('✓ Lip sync initialized (window.lipsync)');
                document.getElementById('lipsyncStatus').textContent = 'Ready';
                document.getElementById('lipsyncStatus').style.color = '#00ff00';
                return true;
            }
            
            console.warn('Lipsync library not found. Available on window:', Object.keys(window).filter(k => k.toLowerCase().includes('lip')));
            document.getElementById('lipsyncStatus').textContent = 'Not loaded';
            document.getElementById('lipsyncStatus').style.color = '#ff0000';
            return false;
        }

        // Initialize Three.js scene
        async function initScene() {
            // Wait for lipsync library to load with extended timeout
            console.log('Waiting for lipsync library...');
            let retries = 0;
            const maxRetries = 100; // 10 seconds
            
            while (!initLipsync() && retries < maxRetries) {
                await new Promise(resolve => setTimeout(resolve, 100));
                retries++;
                
                if (retries % 10 === 0) {
                    console.log(`Still waiting for lipsync... (${retries * 100}ms)`);
                }
            }
            
            if (retries >= maxRetries) {
                console.error('Lipsync library failed to load after 10 seconds');
                console.log('Window properties:', Object.keys(window).filter(k => k.toLowerCase().includes('lip') || k.toLowerCase().includes('wawa')));
                console.log('Switching to fallback audio-reactive lip sync');
                document.getElementById('lipsyncStatus').textContent = 'Using fallback';
                document.getElementById('lipsyncStatus').style.color = '#ffaa00';
                useFallbackLipsync = true;
                setupFallbackLipsync();
            }
            
            scene = new THREE.Scene();
            // Gradient background (will be animated)
            const bgColor1 = new THREE.Color(0x1f2126);
            const bgColor2 = new THREE.Color(0x0f1115);
            scene.background = bgColor1;
            
         
            
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 1.5, 1.0); // Closer initial position for better zoom
            camera.lookAt(0, 1.5, 0);
            
            renderer = new THREE.WebGLRenderer({ 
                antialias: true,
                powerPreference: "high-performance",
                alpha: false
            });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Better quality on high-DPI displays
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap; // Softer shadows
            renderer.toneMapping = THREE.ACESFilmicToneMapping; // Better color rendering
            renderer.toneMappingExposure = 1.2;
            renderer.outputEncoding = THREE.sRGBEncoding;
            document.getElementById('canvas-container').appendChild(renderer.domElement);
            
            // Enhanced lighting setup
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            
            // Main directional light (sun)
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
            directionalLight.position.set(5, 10, 7.5);
            directionalLight.castShadow = true;
            directionalLight.shadow.mapSize.width = 2048;
            directionalLight.shadow.mapSize.height = 2048;
            directionalLight.shadow.camera.near = 0.5;
            directionalLight.shadow.camera.far = 50;
            directionalLight.shadow.camera.left = -10;
            directionalLight.shadow.camera.right = 10;
            directionalLight.shadow.camera.top = 10;
            directionalLight.shadow.camera.bottom = -10;
            directionalLight.shadow.bias = -0.0001;
            directionalLight.shadow.radius = 4;
            scene.add(directionalLight);
            
            // Fill light (softer, from opposite side)
            const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
            fillLight.position.set(-5, 3, -5);
            scene.add(fillLight);
            
            // Rim light for depth
            const rimLight = new THREE.DirectionalLight(0x88ccff, 0.5);
            rimLight.position.set(-3, 5, -8);
            scene.add(rimLight);
            
            // Point light for subtle glow
            const pointLight = new THREE.PointLight(0xffffff, 0.3, 20);
            pointLight.position.set(0, 3, 5);
            scene.add(pointLight);
            

            
            
            clock = new THREE.Clock();
            
            setupControls();
            
            // Try to load custom model
            try {
                await loadCustomModel('https://500d9852edfa327c10090278dc359d2f.r2.cloudflarestorage.com/portfolio-model/avatar.glb');
                console.log('✓ Custom model loaded');
            } catch (error) {
                console.log('Using default avatar');
                createDefaultAvatar();
            }
            
            // Start animation loop
            animate();
        }

        function setupControls() {
            let isDragging = false;
            let previousMousePosition = { x: 0, y: 0 };
            let rotation = { x: 0, y: 0 };

            renderer.domElement.addEventListener('mousedown', (e) => {
                isDragging = true;
                previousMousePosition = { x: e.clientX, y: e.clientY };
            });

            renderer.domElement.addEventListener('mousemove', (e) => {
                if (isDragging) {
                    const deltaX = e.clientX - previousMousePosition.x;
                    const deltaY = e.clientY - previousMousePosition.y;
                    
                    rotation.y += deltaX * 0.005;
                    rotation.x += deltaY * 0.005;
                    rotation.x = Math.max(-Math.PI / 4, Math.min(Math.PI / 4, rotation.x));
                    
                    previousMousePosition = { x: e.clientX, y: e.clientY };
                }
            });

            renderer.domElement.addEventListener('mouseup', () => {
                isDragging = false;
            });

            renderer.domElement.addEventListener('wheel', (e) => {
                e.preventDefault();
                camera.position.z += e.deltaY * 0.01;
                camera.position.z = Math.max(1.5, Math.min(6, camera.position.z));
            });

            window.cameraRotation = rotation;
        }

        function loadCustomModel(modelPath) {
            return new Promise((resolve, reject) => {
                const loader = new THREE.GLTFLoader();
                
                loader.load(
                    modelPath,
                    (gltf) => {
                        avatar = gltf.scene;
                        avatar.position.set(0, 0, 0);
                        avatar.castShadow = true;
                        
                        // Store original rotation and position for smooth idle animation
                        avatar.userData.originalRotation = avatar.rotation.clone();
                        avatar.userData.originalPosition = avatar.position.y; // Store for breathing animation
                        
                        // Find meshes with morph targets for lip sync and bones for animation
                        avatar.traverse((child) => {
                            if (child.isMesh) {
                                child.castShadow = true;
                                child.receiveShadow = true;
                                
                                // Improve material quality
                                if (child.material) {
                                    if (Array.isArray(child.material)) {
                                        child.material.forEach(mat => {
                                            if (mat.isMeshStandardMaterial || mat.isMeshPhongMaterial) {
                                                mat.roughness = 0.7;
                                                mat.metalness = 0.1;
                                            }
                                        });
                                    } else {
                                        if (child.material.isMeshStandardMaterial || child.material.isMeshPhongMaterial) {
                                            child.material.roughness = 0.7;
                                            child.material.metalness = 0.1;
                                        }
                                    }
                                }
                                
                                if (child.morphTargetDictionary && child.morphTargetInfluences) {
                                    console.log('Found morph target mesh:', child.name);
                                    console.log('Available morphs:', Object.keys(child.morphTargetDictionary));
                                    morphTargetMeshes.push(child);
                                    
                                    // Discover and map viseme morph targets
                                    const meshMorphs = {};
                                    const allMorphNames = Object.keys(child.morphTargetDictionary);
                                    
                                    // Try to find viseme morphs using various naming patterns
                                    Object.keys(visemeMapping).forEach(visemeKey => {
                                        const standardName = visemeMapping[visemeKey];
                                        const variations = visemeNameVariations[standardName] || [standardName];
                                        
                                        // Try exact match first
                                        for (const morphName of allMorphNames) {
                                            const morphNameLower = morphName.toLowerCase();
                                            
                                            // Check if this morph name matches any variation
                                            for (const variation of variations) {
                                                if (morphNameLower === variation.toLowerCase() || 
                                                    morphNameLower.includes(variation.toLowerCase().replace('viseme_', ''))) {
                                                    const morphIndex = child.morphTargetDictionary[morphName];
                                                    if (morphIndex !== undefined) {
                                                        meshMorphs[visemeKey] = {
                                                            index: morphIndex,
                                                            name: morphName
                                                        };
                                                        console.log(`  ✓ Mapped viseme "${visemeKey}" to morph "${morphName}" (index ${morphIndex})`);
                                                        break;
                                                    }
                                                }
                                            }
                                            if (meshMorphs[visemeKey]) break;
                                        }
                                    });
                                    
                                    // Store discovered morphs for this mesh
                                    discoveredMorphTargets.set(child, meshMorphs);
                                    const foundVisemes = Object.keys(meshMorphs);
                                    console.log(`  ✓ Total visemes found for ${child.name}: ${foundVisemes.length}`);
                                    if (foundVisemes.length > 0) {
                                        console.log(`    Found visemes: ${foundVisemes.join(', ')}`);
                                    } else {
                                        console.warn(`    ⚠️ No visemes found! Available morph targets:`, allMorphNames.filter(n => n.toLowerCase().includes('viseme') || n.toLowerCase().includes('mouth') || n.toLowerCase().includes('lip')));
                                    }
                                }
                            }
                            
                            // Find bones for animation
                            if (child.isBone || child.type === 'Bone') {
                                const boneName = child.name.toLowerCase();
                                if (boneName.includes('head') && !headBone) {
                                    headBone = child;
                                    console.log('✓ Found head bone:', child.name);
                                } else if (boneName.includes('neck') && !neckBone) {
                                    neckBone = child;
                                    console.log('✓ Found neck bone:', child.name);
                                } else if (boneName.includes('spine') && !spineBone) {
                                    spineBone = child;
                                    console.log('✓ Found spine bone:', child.name);
                                }
                            }
                        });
                        
                        document.getElementById('morphCount').textContent = morphTargetMeshes.length;
                        if (morphTargetMeshes.length > 0) {
                            document.getElementById('morphCount').style.color = '#00ff00';
                        } else {
                            document.getElementById('morphCount').style.color = '#ff0000';
                        }
                        
                        // Scale model
                        const box = new THREE.Box3().setFromObject(avatar);
                        const size = box.getSize(new THREE.Vector3());
                        const maxSize = Math.max(size.x, size.y, size.z);
                        const scale = 2 / maxSize;
                        avatar.scale.multiplyScalar(scale);
                        
                        avatar = gltf.scene;
                        scene.add(avatar);
                        
                        // Setup animations
                        if (gltf.animations && gltf.animations.length > 0) {
                            mixer = new THREE.AnimationMixer(avatar);
                            const idleAnimation = mixer.clipAction(gltf.animations[0]);
                            idleAnimation.play();
                        }
                        
                        resolve();
                    },
                    (progress) => {
                        if (progress.total) {
                            console.log('Loading:', Math.round(progress.loaded / progress.total * 100) + '%');
                        }
                    },
                    (error) => {
                        reject(error);
                    }
                );
            });
        }

        function createDefaultAvatar() {
            avatar = new THREE.Group();
            
            const headGeometry = new THREE.SphereGeometry(0.3, 32, 32);
            const skinMaterial = new THREE.MeshPhongMaterial({ 
                color: 0xffdbac,
                shininess: 30
            });
            const head = new THREE.Mesh(headGeometry, skinMaterial);
            head.position.y = 1.5;
            head.castShadow = true;
            avatar.add(head);
            avatar.head = head;
            
            const eyeGeometry = new THREE.SphereGeometry(0.05, 16, 16);
            const eyeMaterial = new THREE.MeshPhongMaterial({ color: 0x2c3e50 });
            
            const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
            leftEye.position.set(-0.1, 1.55, 0.25);
            avatar.add(leftEye);
            
            const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
            rightEye.position.set(0.1, 1.55, 0.25);
            avatar.add(rightEye);
            
            const mouthGeometry = new THREE.TorusGeometry(0.08, 0.02, 16, 100, Math.PI);
            const mouthMaterial = new THREE.MeshPhongMaterial({ color: 0x000000 });
            const mouth = new THREE.Mesh(mouthGeometry, mouthMaterial);
            mouth.position.set(0, 1.4, 0.28);
            mouth.rotation.x = Math.PI;
            avatar.add(mouth);
            avatar.mouth = mouth;
            
            const bodyGeometry = new THREE.CylinderGeometry(0.35, 0.4, 0.8, 32);
            const shirtMaterial = new THREE.MeshPhongMaterial({ color: 0x3498db });
            const body = new THREE.Mesh(bodyGeometry, shirtMaterial);
            body.position.y = 0.6;
            body.castShadow = true;
            avatar.add(body);
            avatar.body = body;
            
            const armGeometry = new THREE.CylinderGeometry(0.08, 0.07, 0.7, 16);
            const leftArm = new THREE.Mesh(armGeometry, skinMaterial);
            leftArm.position.set(-0.45, 0.8, 0);
            leftArm.rotation.z = 0.2;
            leftArm.castShadow = true;
            avatar.add(leftArm);
            avatar.leftArm = leftArm;
            
            const rightArm = new THREE.Mesh(armGeometry, skinMaterial);
            rightArm.position.set(0.45, 0.8, 0);
            rightArm.rotation.z = -0.2;
            rightArm.castShadow = true;
            avatar.add(rightArm);
            avatar.rightArm = rightArm;
            
            const legGeometry = new THREE.CylinderGeometry(0.1, 0.09, 0.8, 16);
            const pantsMaterial = new THREE.MeshPhongMaterial({ color: 0x2c3e50 });
            
            const leftLeg = new THREE.Mesh(legGeometry, pantsMaterial);
            leftLeg.position.set(-0.15, -0.2, 0);
            leftLeg.castShadow = true;
            avatar.add(leftLeg);
            
            const rightLeg = new THREE.Mesh(legGeometry, pantsMaterial);
            rightLeg.position.set(0.15, -0.2, 0);
            rightLeg.castShadow = true;
            avatar.add(rightLeg);
            
            // Store original position and rotation for animations
            avatar.userData.originalPosition = avatar.position.y;
            avatar.userData.originalRotation = avatar.rotation.clone();
            
            scene.add(avatar);
        }

        // Fallback lip sync using Web Audio API
        function setupFallbackLipsync() {
            try {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                analyser.fftSize = 256;
                dataArray = new Uint8Array(analyser.frequencyBinCount);
                console.log('✓ Fallback audio analyzer initialized');
            } catch (e) {
                console.error('Failed to setup fallback lipsync:', e);
            }
        }

        function getFallbackViseme() {
            if (!analyser || !dataArray) return 'X';
            
            analyser.getByteFrequencyData(dataArray);
            
            // Calculate average volume and frequency distribution
            let sum = 0;
            let maxFreq = 0;
            let maxFreqIndex = 0;
            
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
                if (dataArray[i] > maxFreq) {
                    maxFreq = dataArray[i];
                    maxFreqIndex = i;
                }
            }
            
            const average = sum / dataArray.length;
            const maxFreqValue = maxFreq;
            
            // More sophisticated viseme detection based on volume and frequency
            if (average < 5) {
                return 'X'; // Silence/closed mouth
            }
            
            // Low frequency sounds (vowels like A, O, U)
            if (maxFreqIndex < dataArray.length * 0.2) {
                if (average > 60) return 'A'; // Wide open (A)
                if (average > 40) return 'O'; // Medium open (O)
                return 'U'; // Slightly open (U)
            }
            
            // Mid frequency sounds (E, I)
            if (maxFreqIndex < dataArray.length * 0.4) {
                if (average > 50) return 'E'; // Medium open (E)
                return 'H'; // Slightly open (I)
            }
            
            // High frequency sounds (consonants)
            if (maxFreqIndex < dataArray.length * 0.6) {
                if (average > 45) return 'C'; // CH, SH sounds
                if (average > 30) return 'S'; // S, Z sounds
                return 'T'; // T, D sounds
            }
            
            // Very high frequency (F, TH)
            if (average > 35) return 'F'; // F, V sounds
            if (average > 20) return 'T'; // TH sounds
            
            // Default based on volume
            if (average > 50) return 'A'; // Wide open
            if (average > 30) return 'E'; // Medium open
            if (average > 15) return 'B'; // Slightly open (B, M, P)
            return 'X'; // Closed
        }

        // Update lip sync based on audio analysis with smooth interpolation
        function updateLipsync() {
            if (!isSpeaking) {
                document.getElementById('speakingStatus').textContent = 'No';
                document.getElementById('currentViseme').textContent = '-';
                
                // Reset all visemes when not speaking
                if (morphTargetMeshes.length > 0) {
                    morphTargetMeshes.forEach(mesh => {
                        const meshMorphs = discoveredMorphTargets.get(mesh);
                        if (meshMorphs) {
                            Object.values(meshMorphs).forEach(morph => {
                                smoothMorphInfluence(mesh, morph.index, 0);
                            });
                        }
                    });
                }
                lastViseme = 'X';
                visemeTransition = 0;
                return;
            }
            
            document.getElementById('speakingStatus').textContent = 'Yes';
            document.getElementById('speakingStatus').style.color = '#00ff00';
            
            let currentViseme;
            
            try {
                if (useFallbackLipsync) {
                    // Use fallback audio-reactive lip sync
                    currentViseme = getFallbackViseme();
                } else if (lipsyncManager) {
                    // Use wawa-lipsync library
                    try {
                        lipsyncManager.processAudio();
                        currentViseme = lipsyncManager.viseme || lipsyncManager.getViseme();
                    } catch (e) {
                        console.warn('Lipsync manager error, using fallback:', e);
                        currentViseme = getFallbackViseme();
                    }
                } else {
                    currentViseme = getFallbackViseme();
                }
                
                // Normalize viseme (handle lowercase, etc.)
                if (currentViseme) {
                    currentViseme = currentViseme.toUpperCase();
                    // Map common variations
                    if (currentViseme === 'SIL' || currentViseme === 'SILENCE') currentViseme = 'sil';
                } else {
                    currentViseme = 'X';
                }
                
                // Update debug display
                document.getElementById('currentViseme').textContent = currentViseme || 'X';
                
                // Smooth transition between visemes
                const transitionSpeed = 0.08; // Slower speed for smoother transitions
                if (currentViseme !== lastViseme) {
                    visemeTransition = Math.max(0, visemeTransition - transitionSpeed);
                    if (visemeTransition <= 0) {
                        lastViseme = currentViseme;
                        visemeTransition = 1.0;
                    }
                } else {
                    visemeTransition = Math.min(1.0, visemeTransition + transitionSpeed);
                }
                
                // Update morph targets for custom models
                if (morphTargetMeshes.length > 0) {
                    morphTargetMeshes.forEach(mesh => {
                        const meshMorphs = discoveredMorphTargets.get(mesh);
                        
                        if (meshMorphs && Object.keys(meshMorphs).length > 0) {
                            // Reset all viseme morphs toward 0 first (softly)
                            Object.values(meshMorphs).forEach(morph => {
                                smoothMorphInfluence(mesh, morph.index, 0);
                            });
                            
                            // Apply current viseme with smooth transition
                            if (meshMorphs[currentViseme]) {
                                const morph = meshMorphs[currentViseme];
                                smoothMorphInfluence(mesh, morph.index, visemeTransition);
                            } else if (meshMorphs['X'] || meshMorphs['sil']) {
                                // Fallback to silence/closed mouth if current viseme not found
                                const fallbackMorph = meshMorphs['X'] || meshMorphs['sil'];
                                smoothMorphInfluence(mesh, fallbackMorph.index, 0.3 * visemeTransition);
                            }
                            
                            // Optional: Blend with previous viseme for smoother transition
                            if (visemeTransition < 1.0 && lastViseme !== currentViseme && meshMorphs[lastViseme]) {
                                const prevMorph = meshMorphs[lastViseme];
                                smoothMorphInfluence(mesh, prevMorph.index, (1.0 - visemeTransition) * 0.3);
                            }
                        } else {
                            // Fallback: try direct morph target dictionary lookup
                            Object.keys(visemeMapping).forEach(visemeKey => {
                                const morphName = visemeMapping[visemeKey];
                                const morphIndex = mesh.morphTargetDictionary[morphName];
                                if (morphIndex !== undefined) {
                                    smoothMorphInfluence(mesh, morphIndex, 0);
                                }
                            });
                            
                            if (currentViseme && visemeMapping[currentViseme]) {
                                const morphName = visemeMapping[currentViseme];
                                const morphIndex = mesh.morphTargetDictionary[morphName];
                                if (morphIndex !== undefined) {
                                    smoothMorphInfluence(mesh, morphIndex, visemeTransition);
                                }
                            }
                        }
                    });
                } else if (avatar && avatar.mouth) {
                    // Fallback animation for default avatar
                    const openAmount = currentViseme && currentViseme !== 'X' && currentViseme !== 'sil' 
                        ? 0.3 * visemeTransition : 0;
                    avatar.mouth.scale.x = THREE.MathUtils.lerp(avatar.mouth.scale.x, 1 + openAmount, visemeBlendDamping);
                    avatar.mouth.scale.y = THREE.MathUtils.lerp(avatar.mouth.scale.y, 1 + openAmount * 0.5, visemeBlendDamping);
                }
            } catch (e) {
                console.error('Lipsync update error:', e);
                document.getElementById('lipsyncStatus').textContent = 'Error: ' + e.message;
                document.getElementById('lipsyncStatus').style.color = '#ff0000';
            }
        }

        // Eye blinking system
        function updateEyeBlink(delta) {
            eyeBlinkTimer += delta;
            
            // Random blink interval (2-6 seconds)
            if (!isBlinking && eyeBlinkTimer > 2 + Math.random() * 4) {
                isBlinking = true;
                eyeBlinkDuration = 0;
                eyeBlinkTimer = 0;
            }
            
            if (isBlinking) {
                eyeBlinkDuration += delta * 8; // Fast blink
                
                if (eyeBlinkDuration >= 1) {
                    isBlinking = false;
                    eyeBlinkDuration = 0;
                }
                
                // Apply blink to morph targets or mesh
                if (morphTargetMeshes.length > 0) {
                    morphTargetMeshes.forEach(mesh => {
                        const blinkMorphs = ['eyeBlinkLeft', 'eyeBlinkRight', 'blink', 'eyeClose'];
                        blinkMorphs.forEach(morphName => {
                            const morphIndex = mesh.morphTargetDictionary[morphName];
                            if (morphIndex !== undefined) {
                                const blinkAmount = Math.sin(eyeBlinkDuration * Math.PI);
                                mesh.morphTargetInfluences[morphIndex] = blinkAmount;
                            }
                        });
                    });
                }
            }
        }
        
        // Enhanced idle animations
        function updateIdleAnimations(delta) {
            if (!avatar || isSpeaking) return;
            
            idleAnimationTime += delta;
            const time = idleAnimationTime;
            
            // Breathing animation - slower frequency for natural breathing
            const breathingCycle = Math.sin(time * 0.85); // Slower breathing (was 1.2, now 0.85)
            const breathingIntensity = breathingCycle * 0.012; // Subtle vertical movement
            
            // Move the entire avatar up and down for breathing
            if (avatar.userData.originalPosition === undefined) {
                avatar.userData.originalPosition = avatar.position.y;
            }
            avatar.position.y = avatar.userData.originalPosition + breathingIntensity;
            
            // Chest expansion (subtle scale for breathing effect)
            const chestExpansion = breathingCycle * 0.01;
            if (spineBone) {
                spineBone.scale.y = 1 + chestExpansion;
            } else if (avatar.body) {
                avatar.body.scale.y = 1 + chestExpansion;
            }
            
            // Subtle head movements (looking around naturally)
            // Head bob should be relative to breathing, not independent
            const headBob = breathingIntensity * 0.3; // Head moves slightly with breathing
            const headTurn = Math.sin(time * 0.3) * 0.08;
            const headNod = Math.sin(time * 0.5) * 0.03;
            
            if (headBone) {
                headBone.rotation.y = headTurn;
                headBone.rotation.x = headNod;
                // Head position relative to body breathing
                headBone.position.y = headBob;
            } else if (avatar.head) {
                avatar.head.rotation.y = headTurn;
                avatar.head.rotation.x = headNod;
                avatar.head.position.y = headBob;
            }
            
            // Subtle body sway
            const bodySway = Math.sin(time * 0.4) * 0.01;
            if (avatar.body) {
                avatar.body.rotation.z = bodySway;
            }
            
            // Gentle arm movements
            if (avatar.leftArm) {
                avatar.leftArm.rotation.x = Math.sin(time * 0.6) * 0.05;
                avatar.leftArm.rotation.z = Math.sin(time * 0.7) * 0.03;
            }
            if (avatar.rightArm) {
                avatar.rightArm.rotation.x = Math.sin(time * 0.65) * 0.05;
                avatar.rightArm.rotation.z = Math.sin(time * 0.75) * 0.03;
            }
            
            // Subtle whole-body idle rotation (very slow, natural)
            if (avatar.userData.originalRotation) {
                const idleRotation = Math.sin(time * 0.1) * 0.05;
                avatar.rotation.y = avatar.userData.originalRotation.y + idleRotation;
            }
        }
        
        // Speaking animations (more expressive)
        function updateSpeakingAnimations(delta) {
            if (!avatar || !isSpeaking) return;
            
            const time = idleAnimationTime;
            
            // Continue breathing while speaking (slightly faster due to speaking)
            const breathingCycle = Math.sin(time * 0.9); // Slightly faster when speaking
            const breathingIntensity = breathingCycle * 0.012;
            
            // Move the entire avatar up and down for breathing
            if (avatar.userData.originalPosition === undefined) {
                avatar.userData.originalPosition = avatar.position.y;
            }
            avatar.position.y = avatar.userData.originalPosition + breathingIntensity;
            
            // Chest expansion
            const chestExpansion = breathingCycle * 0.01;
            if (spineBone) {
                spineBone.scale.y = 1 + chestExpansion;
            } else if (avatar.body) {
                avatar.body.scale.y = 1 + chestExpansion;
            }
            
            // More dynamic head movements while speaking
            if (headBone) {
                headBone.rotation.x = Math.sin(time * 6) * 0.08;
                headBone.rotation.y = Math.sin(time * 4) * 0.1;
                headBone.rotation.z = Math.sin(time * 5) * 0.05;
            } else if (avatar.head) {
                avatar.head.rotation.x = Math.sin(time * 6) * 0.08;
                avatar.head.rotation.y = Math.sin(time * 4) * 0.1;
                avatar.head.rotation.z = Math.sin(time * 5) * 0.05;
            }
            
            // Body movement (rotation only, scale handled by breathing)
            if (avatar.body) {
                avatar.body.rotation.z = Math.sin(time * 5) * 0.03;
            }
            
            // Hand gestures
            if (avatar.leftArm) {
                avatar.leftArm.rotation.x = Math.sin(time * 7) * 0.15;
                avatar.leftArm.rotation.z = Math.sin(time * 6) * 0.08;
            }
            if (avatar.rightArm) {
                avatar.rightArm.rotation.x = Math.sin(time * 7.5) * 0.15;
                avatar.rightArm.rotation.z = Math.sin(time * 6.5) * 0.08;
            }
        }
        
        function animate() {
            requestAnimationFrame(animate);
            
            const delta = clock.getDelta();
            
            // Update animation mixer if available
            if (mixer) mixer.update(delta);
            
            // Update lip sync
            updateLipsync();
            
            // Update eye blinking
            updateEyeBlink(delta);
            
            // Apply camera rotation
            if (window.cameraRotation && avatar) {
                avatar.rotation.y = window.cameraRotation.y;
            }
            
            // Update animations based on state
            if (avatar) {
                if (isSpeaking) {
                    updateSpeakingAnimations(delta);
                } else {
                    updateIdleAnimations(delta);
                }
            }
            
            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // Speech Recognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = function() {
                isRecording = true;
                document.getElementById('micButton').classList.add('recording');
                document.getElementById('status').textContent = 'Listening...';
                document.getElementById('transcript').style.display = 'none';
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                console.log('Recognized:', transcript);
                
                document.getElementById('transcriptText').textContent = 'You: "' + transcript + '"';
                document.getElementById('transcript').style.display = 'block';
                
                processQuestion(transcript);
            };

            recognition.onerror = function(event) {
                console.error('Speech recognition error:', event.error);
                isRecording = false;
                document.getElementById('micButton').classList.remove('recording');
                document.getElementById('status').textContent = 'Error: ' + event.error;
            };

            recognition.onend = function() {
                isRecording = false;
                document.getElementById('micButton').classList.remove('recording');
            };
        }

        function toggleRecording() {
            if (!recognition) {
                alert('Speech recognition not supported');
                return;
            }

            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }

        async function processQuestion(question) {
            const loading = document.getElementById('loading');
            const audioPlayer = document.getElementById('audioPlayer');
            
            loading.style.display = 'block';
            document.getElementById('status').textContent = 'Thinking...';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('status').textContent = 'Error: ' + data.error;
                } else {
                    document.getElementById('answerText').textContent = 'Me: ' + data.answer;
                    
                    if (data.audio) {
                        // Set audio source FIRST (required by wawa-lipsync)
                        audioPlayer.src = 'data:audio/mp3;base64,' + data.audio;
                        
                        console.log('Audio loaded, connecting to lipsync...');
                        
                        // Connect audio to lipsync manager or fallback
                        if (useFallbackLipsync || !lipsyncManager) {
                            // Use Web Audio API for fallback
                            try {
                                // Recreate audio context if needed (some browsers require user interaction)
                                if (!audioContext || audioContext.state === 'closed') {
                                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                                    analyser = audioContext.createAnalyser();
                                    analyser.fftSize = 512; // Higher resolution for better detection
                                    analyser.smoothingTimeConstant = 0.3;
                                    dataArray = new Uint8Array(analyser.frequencyBinCount);
                                    console.log('✓ Recreated audio context');
                                }
                                
                                // Disconnect any existing source
                                if (audioContext.state === 'suspended') {
                                    audioContext.resume();
                                }
                                
                                const source = audioContext.createMediaElementSource(audioPlayer);
                                source.connect(analyser);
                                analyser.connect(audioContext.destination);
                                console.log('✓ Fallback audio analyzer connected');
                                document.getElementById('lipsyncStatus').textContent = 'Fallback active';
                                document.getElementById('lipsyncStatus').style.color = '#00ff00';
                                useFallbackLipsync = true;
                            } catch (e) {
                                console.error('Fallback connection error:', e);
                                // If createMediaElementSource fails (already connected), just use the analyser
                                if (e.name === 'InvalidStateError' || e.message.includes('already connected')) {
                                    console.log('Audio already connected, using existing analyser');
                                    useFallbackLipsync = true;
                                }
                            }
                        } else if (lipsyncManager) {
                            try {
                                lipsyncManager.connectAudio(audioPlayer);
                                console.log('✓ Lipsync connected to audio');
                                document.getElementById('lipsyncStatus').textContent = 'Connected';
                                document.getElementById('lipsyncStatus').style.color = '#00ff00';
                            } catch (e) {
                                console.error('Lipsync connection error:', e);
                                document.getElementById('lipsyncStatus').textContent = 'Error: ' + e.message;
                                document.getElementById('lipsyncStatus').style.color = '#ff0000';
                            }
                        } else {
                            console.error('No lipsync available!');
                            document.getElementById('lipsyncStatus').textContent = 'Not available';
                            document.getElementById('lipsyncStatus').style.color = '#ff0000';
                        }
                        
                        isSpeaking = true;
                        document.getElementById('status').textContent = 'Speaking...';
                        
                        audioPlayer.onended = () => {
                            isSpeaking = false;
                            document.getElementById('status').textContent = 'Click to speak';
                            document.getElementById('speakingStatus').textContent = 'No';
                            document.getElementById('speakingStatus').style.color = '#ffffff';
                        };
                        
                        // Play audio
                        audioPlayer.play().catch(e => {
                            console.log('Autoplay prevented, trying manual play:', e);
                            setTimeout(() => audioPlayer.play(), 100);
                        });
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('status').textContent = 'Error: ' + error.message;
            } finally {
                loading.style.display = 'none';
            }
        }

        window.addEventListener('load', initScene);
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        question = data.get('question', '')
        session_id = data.get('session_id', 'default')  # fallback for single-session use
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400

        print(f"Question received: {question}")

        # Create history for the session if not exists
        if session_id not in conversation_history:
            conversation_history[session_id] = []

        # Format history as text
        history_text = ""
        for q, a in conversation_history[session_id]:
            history_text += f"Previous question: {q}\nPrevious answer: {a}\n\n"

        # Load your RAG context
        context = read_context_file()

        # Build prompt including history
        prompt = f"""
You are assisting the user by answering questions using the provided resume documents only.

Respond in first person ("I", "my experience", "my background") as if you are the owner of the resume.
In case asked about 'tell me about this portfolio.', refer to 'QandA System by Text Extraction from PDF' in projects and phrase it accordingly.
Do NOT invent personal information that is not in the retrieved documents.
If the answer is not found or looks closer to an information you have, first ask a follow up question to clarify, otherwise respond with:
"That information isn't in my resume. Would you like to know anything else?"

Tone: concise, professional, confident, clear.

Conversation history:
{history_text}

RAG Context:
{context}

User question: {question}

Answer:"""

        print("Generating answer with Gemini...")
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        answer_text = response.text

        # Save this Q/A into session history
        conversation_history[session_id].append((question, answer_text))

        print(f"Answer generated: {answer_text[:100]}...")

        print("Converting answer to speech...")
        audio_base64 = text_to_speech(answer_text)

        return jsonify({
            'answer': answer_text,
            'audio': audio_base64
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 70)
    print("🎤 3D Avatar Q&A with Real-Time Lip Sync")
    print("=" * 70)
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    print(f"Server starting on http://localhost:{port}")
    print()
    print("📁 Files needed:")
    print("   - avatar.glb (your 3D model) - optional")
    print("   - resume.txt (your resume content)")
    print()
    print("✨ Features:")
    print("   - Real-time lip syncing with wawa-lipsync")
    print("   - Voice input and output")
    print("   - 3D avatar animations")
    print()
    print("🎮 Controls:")
    print("   - Drag to rotate • Scroll to zoom • Click mic to speak")
    print()
    print("=" * 70)
    app.run(debug=debug, host='0.0.0.0', port=port)
