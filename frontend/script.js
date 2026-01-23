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
const visemeMapping = {
    'sil': 'viseme_sil',
    'A': 'viseme_aa',
    'B': 'viseme_PP',
    'C': 'viseme_CH',
    'D': 'viseme_DD',
    'E': 'viseme_E',
    'F': 'viseme_FF',
    'G': 'viseme_E',
    'H': 'viseme_aa',
    'X': 'viseme_nn',
    'O': 'viseme_O',
    'P': 'viseme_PP',
    'R': 'viseme_RR',
    'S': 'viseme_SS',
    'T': 'viseme_TH',
    'U': 'viseme_U'
};

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

const discoveredMorphTargets = new Map();
let lastViseme = 'X';
let visemeTransition = 0;
const visemeBlendDamping = 0.18;

function smoothMorphInfluence(mesh, morphIndex, targetValue, damping = visemeBlendDamping) {
    const current = mesh.morphTargetInfluences[morphIndex] || 0;
    mesh.morphTargetInfluences[morphIndex] = THREE.MathUtils.lerp(current, targetValue, damping);
}

function initLipsync() {
    if (window.WLipsync) {
        lipsyncManager = new window.WLipsync();
        console.log('Lip sync initialized (window.WLipsync)');
        document.getElementById('lipsyncStatus').textContent = 'WLipsync Ready';
        document.getElementById('lipsyncStatus').style.color = '#00ff00';
        return true;
    }
    
    console.warn('Lipsync library not found.');
    document.getElementById('lipsyncStatus').textContent = 'Not loaded';
    document.getElementById('lipsyncStatus').style.color = '#ff0000';
    return false;
}

async function initScene() {
    console.log('Waiting for Wlipsync library...');
    let retries = 0;
    const maxRetries = 2;
    
    while (!initLipsync() && retries < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 100));
        retries++;
        
        if (retries % 10 === 0) {
            console.log(`Still waiting for lipsync... (${retries * 100}ms)`);
        }
    }
    
    if (retries >= maxRetries) {
        console.error('Lipsync library failed to load');
        console.log('Switching to fallback audio-reactive lip sync');
        document.getElementById('lipsyncStatus').textContent = 'Using fallback';
        document.getElementById('lipsyncStatus').style.color = '#ffaa00';
        useFallbackLipsync = true;
        setupFallbackLipsync();
    }
    
    scene = new THREE.Scene();
    const bgColor1 = new THREE.Color(0x1f2126);
    const bgColor2 = new THREE.Color(0x0f1115);
    scene.background = bgColor1;
    
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 1.6, 1.5);
    // camera.lookAt(0, 1.5, 0);
    
    renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        powerPreference: "high-performance",
        alpha: false
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    renderer.outputEncoding = THREE.sRGBEncoding;
    document.getElementById('canvas-container').appendChild(renderer.domElement);
    
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
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
    
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
    fillLight.position.set(-5, 3, -5);
    scene.add(fillLight);
    
    const rimLight = new THREE.DirectionalLight(0x88ccff, 0.5);
    rimLight.position.set(-3, 5, -8);
    scene.add(rimLight);
    
    const pointLight = new THREE.PointLight(0xffffff, 0.3, 20);
    pointLight.position.set(0, 3, 5);
    scene.add(pointLight);
    
    clock = new THREE.Clock();
    
    // setupControls();
    
    try {
        await loadCustomModel('/frontend/assets/avatar.glb');
        console.log('Custom model loaded');
    } catch (error) {
        console.log('Using default avatar');
        createDefaultAvatar();
    }
    // // Play intro speech after model loads
    // setTimeout(() => {
    //     playIntroSpeech();
    // }, 10); // Small delay to ensure everything is ready
                
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
                // avatar.position.set(0, 0, 0);
                // avatar.castShadow = true;
                
                // avatar.userData.originalRotation = avatar.rotation.clone();
                // avatar.userData.originalPosition = avatar.position.y;
                scene.add(avatar);
                avatar.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                        
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
                            
                            const meshMorphs = {};
                            const allMorphNames = Object.keys(child.morphTargetDictionary);
                            
                            Object.keys(visemeMapping).forEach(visemeKey => {
                                const standardName = visemeMapping[visemeKey];
                                const variations = visemeNameVariations[standardName] || [standardName];
                                
                                for (const morphName of allMorphNames) {
                                    const morphNameLower = morphName.toLowerCase();
                                    
                                    for (const variation of variations) {
                                        if (morphNameLower === variation.toLowerCase() || 
                                            morphNameLower.includes(variation.toLowerCase().replace('viseme_', ''))) {
                                            const morphIndex = child.morphTargetDictionary[morphName];
                                            if (morphIndex !== undefined) {
                                                meshMorphs[visemeKey] = {
                                                    index: morphIndex,
                                                    name: morphName
                                                };
                                                console.log(`Mapped viseme "${visemeKey}" to morph "${morphName}" (index ${morphIndex})`);
                                                break;
                                            }
                                        }
                                    }
                                    if (meshMorphs[visemeKey]) break;
                                }
                            });
                            
                            discoveredMorphTargets.set(child, meshMorphs);
                            const foundVisemes = Object.keys(meshMorphs);
                            console.log(`Total visemes found for ${child.name}: ${foundVisemes.length}`);
                            if (foundVisemes.length > 0) {
                                console.log(`Found visemes: ${foundVisemes.join(', ')}`);
                            } else {
                                console.warn(`No visemes found! Available morph targets:`, allMorphNames.filter(n => n.toLowerCase().includes('viseme') || n.toLowerCase().includes('mouth') || n.toLowerCase().includes('lip')));
                            }
                        }
                    }
                    
                    if (child.isBone) {
                        const n = child.name.toLowerCase();
                        if (n.includes('head')) headBone = child;
                        if (n.includes('neck')) if (neckBone) {
                            neckBone.scale.y = 1.3; // try values between 1.2 – 1.5
                            neckBone.updateMatrixWorld(true);
                            neckbone = child;
                        }
                        if (n.includes('spine')) spineBone = child;

                        if (n.includes('left') && (n.includes('arm'))) {
                            child.rotation.x = Math.PI /4.5;
                            child.rotation.y = Math.PI/10;
                            child.rotation.z = Math.PI/40;
                        }

                        if (n.includes('right') && (n.includes('arm'))) {
                            child.rotation.x = Math.PI /4.5;
                            child.rotation.y = -Math.PI/10;
                            child.rotation.z = -Math.PI/40;
                        }
                    }
                });
                
                document.getElementById('morphCount').textContent = morphTargetMeshes.length;
                if (morphTargetMeshes.length > 0) {
                    document.getElementById('morphCount').style.color = '#00ff00';
                } else {
                    document.getElementById('morphCount').style.color = '#ff0000';
                }
                
                const box = new THREE.Box3().setFromObject(avatar);
                const size = box.getSize(new THREE.Vector3());
                avatar.position.y -= box.min.y;
                avatar.position.y -= size.y * 0.05;
                const lookY = box.max.y - size.y * 0.15;
                camera.lookAt(0, lookY, 0);
                // const maxSize = Math.max(size.x, size.y, size.z);
                // const scale = 2 / maxSize;
                // avatar.scale.multiplyScalar(scale);
                

                if (gltf.animations.length) {
                    mixer = new THREE.AnimationMixer(avatar);
                    mixer.clipAction(gltf.animations[0]).play();
                }
                
                // // Play intro speech after model loads
                // setTimeout(() => {
                //     playIntroSpeech();
                // }, 10); // Small delay to ensure everything is ready
                
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
    
    avatar.userData.originalPosition = avatar.position.y;
    avatar.userData.originalRotation = avatar.rotation.clone();
    
    scene.add(avatar);
    
    // Play intro speech after default avatar loads
    setTimeout(() => {
        playIntroSpeech();
    }, 500);
}

function setupFallbackLipsync() {
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        dataArray = new Uint8Array(analyser.frequencyBinCount);
        console.log('Fallback audio analyzer initialized');
    } catch (e) {
        console.error('Failed to setup fallback lipsync:', e);
    }
}

function getFallbackViseme() {
    if (!analyser || !dataArray) return 'X';
    
    analyser.getByteFrequencyData(dataArray);
    
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
    
    if (average < 5) {
        return 'X';
    }
    
    if (maxFreqIndex < dataArray.length * 0.2) {
        if (average > 60) return 'A';
        if (average > 40) return 'O';
        return 'U';
    }
    
    if (maxFreqIndex < dataArray.length * 0.4) {
        if (average > 50) return 'E';
        return 'H';
    }
    
    if (maxFreqIndex < dataArray.length * 0.6) {
        if (average > 45) return 'C';
        if (average > 30) return 'S';
        return 'T';
    }
    
    if (average > 35) return 'F';
    if (average > 20) return 'T';
    
    if (average > 50) return 'A';
    if (average > 30) return 'E';
    if (average > 15) return 'B';
    return 'X';
}

function updateLipsync() {
    if (!isSpeaking) {
        document.getElementById('speakingStatus').textContent = 'No';
        document.getElementById('currentViseme').textContent = '-';
        
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
            currentViseme = getFallbackViseme();
        } else if (lipsyncManager) {
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
        
        if (currentViseme) {
            currentViseme = currentViseme.toUpperCase();
            if (currentViseme === 'SIL' || currentViseme === 'SILENCE') currentViseme = 'sil';
        } else {
            currentViseme = 'X';
        }
        
        document.getElementById('currentViseme').textContent = currentViseme || 'X';
        
        const transitionSpeed = 0.08;
        if (currentViseme !== lastViseme) {
            visemeTransition = Math.max(0, visemeTransition - transitionSpeed);
            if (visemeTransition <= 0) {
                lastViseme = currentViseme;
                visemeTransition = 1.0;
            }
        } else {
            visemeTransition = Math.min(1.0, visemeTransition + transitionSpeed);
        }
        
        if (morphTargetMeshes.length > 0) {
            morphTargetMeshes.forEach(mesh => {
                const meshMorphs = discoveredMorphTargets.get(mesh);
                
                if (meshMorphs && Object.keys(meshMorphs).length > 0) {
                    Object.values(meshMorphs).forEach(morph => {
                        smoothMorphInfluence(mesh, morph.index, 0);
                    });
                    
                    if (meshMorphs[currentViseme]) {
                        const morph = meshMorphs[currentViseme];
                        smoothMorphInfluence(mesh, morph.index, visemeTransition);
                    } else if (meshMorphs['X'] || meshMorphs['sil']) {
                        const fallbackMorph = meshMorphs['X'] || meshMorphs['sil'];
                        smoothMorphInfluence(mesh, fallbackMorph.index, 0.3 * visemeTransition);
                    }
                    
                    if (visemeTransition < 1.0 && lastViseme !== currentViseme && meshMorphs[lastViseme]) {
                        const prevMorph = meshMorphs[lastViseme];
                        smoothMorphInfluence(mesh, prevMorph.index, (1.0 - visemeTransition) * 0.3);
                    }
                } else {
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

function updateEyeBlink(delta) {
    eyeBlinkTimer += delta;
    
    if (!isBlinking && eyeBlinkTimer > 2 + Math.random() * 4) {
        isBlinking = true;
        eyeBlinkDuration = 0;
        eyeBlinkTimer = 0;
    }
    
    if (isBlinking) {
        eyeBlinkDuration += delta * 8;
        
        if (eyeBlinkDuration >= 1) {
            isBlinking = false;
            eyeBlinkDuration = 0;
        }
        
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
    if (!avatar || isSpeaking) return console.log('Idle animation skipped, avatar not ready or speaking');
    
    idleAnimationTime += delta;
    const time = idleAnimationTime;
    
    // Reset neck position (move back up)
    if (neckBone) {
        neckBone.position.y = 0;
        neckBone.scale.y = 1;
    }
    
    // Reset head position
    if (headBone) {
        headBone.position.y = 0;
    } else if (avatar.head) {
        avatar.head.position.y = 0;
    }
    
    // Reset spine/chest expansion
    if (spineBone) {
        spineBone.scale.y = 1;
    } else if (avatar.body) {
        avatar.body.scale.y = 1;
    }
    
    // Keep hands straight down (reset arm rotations)
    if (avatar.leftArm) {
        avatar.leftArm.rotation.x = 0;
        avatar.leftArm.rotation.z = 0;
    }
    if (avatar.rightArm) {
        avatar.rightArm.rotation.x = 0;
        avatar.rightArm.rotation.z = 0;
    }
    
    // Only body movement (subtle body sway)
    const bodySway = Math.sin(time * 0.4) * 0.01;
    if (avatar.body) {
        avatar.body.rotation.z = bodySway;
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
    
    // Reset neck position
    if (neckBone) {
        neckBone.position.y = 0;
        neckBone.scale.y = 1;
    }
    
    // Reset head position
    if (headBone) {
        headBone.position.y = 0;
    } else if (avatar.head) {
        avatar.head.position.y = 0;
    }
    
    // Reset spine/chest
    if (spineBone) {
        spineBone.scale.y = 1;
    } else if (avatar.body) {
        avatar.body.scale.y = 1;
    }
    
    // Keep hands straight down (no gestures)
    if (avatar.leftArm) {
        avatar.leftArm.rotation.x = 0;
        avatar.leftArm.rotation.z = 0;
    }
    if (avatar.rightArm) {
        avatar.rightArm.rotation.x = 0;
        avatar.rightArm.rotation.z = 0;
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
    
    // Body movement (rotation only)
    if (avatar.body) {
        avatar.body.rotation.z = Math.sin(time * 5) * 0.03;
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

function toggleRecording() { if (!recognition) { alert('Speech recognition not supported'); return; } if (isRecording) { recognition.stop(); } else { recognition.start(); } }

// Play intro speech when model loads
async function playIntroSpeech() {
    const audioPlayer = document.getElementById('audioPlayer');
    
    try {
        console.log('Fetching intro speech...');
        const response = await fetch('/intro', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.error) {
            console.error('Error getting intro:', data.error);
            return;
        }
        
        if (data.audio) {
            // Set audio source
            audioPlayer.src = 'data:audio/mp3;base64,' + data.audio;
            audioPlayer.playbackRate = 1.1;
            console.log('Intro audio loaded, connecting to lipsync...');
            
            // Connect audio to lipsync manager or fallback
            if (useFallbackLipsync || !lipsyncManager) {
                try {
                    if (!audioContext || audioContext.state === 'closed') {
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        analyser = audioContext.createAnalyser();
                        analyser.fftSize = 512;
                        analyser.smoothingTimeConstant = 0.3;
                        dataArray = new Uint8Array(analyser.frequencyBinCount);
                        console.log('Recreated audio context for intro');
                    }
                    
                    if (audioContext.state === 'suspended') {
                        audioContext.resume();
                    }
                    
                    const source = audioContext.createMediaElementSource(audioPlayer);
                    source.connect(analyser);
                    analyser.connect(audioContext.destination);
                    console.log('Fallback audio analyzer connected for intro');
                    useFallbackLipsync = true;
                } catch (e) {
                    console.error('Fallback connection error:', e);
                    if (e.name === 'InvalidStateError' || e.message.includes('already connected')) {
                        console.log('Audio already connected, using existing analyser');
                        useFallbackLipsync = true;
                    }
                }
            } else if (lipsyncManager) {
                try {
                    lipsyncManager.connectAudio(audioPlayer);
                    console.log('Lipsync connected to intro audio');
                } catch (e) {
                    console.error('Lipsync connection error:', e);
                }
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
                console.log('Autoplay prevented for intro, trying manual play:', e);
                setTimeout(() => audioPlayer.play(), 100);
            });
        }
    } catch (error) {
        console.error('Error playing intro:', error);
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
            document.getElementById('answerText').textContent = 'Avatar: ' + data.answer;
            
            if (data.audio) {
                audioPlayer.src = 'data:audio/mp3;base64,' + data.audio;
                audioPlayer.playbackRate = 1.2;
                console.log('Audio loaded, connecting to lipsync...');
                
                if (useFallbackLipsync || !lipsyncManager) {
                    try {
                        if (!audioContext || audioContext.state === 'closed') {
                            audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            analyser = audioContext.createAnalyser();
                            analyser.fftSize = 512;
                            analyser.smoothingTimeConstant = 0.2;
                            dataArray = new Uint8Array(analyser.frequencyBinCount);
                            console.log('Recreated audio context');
                        }
                        
                        if (audioContext.state === 'suspended') {
                            audioContext.resume();
                        }
                        
                        const source = audioContext.createMediaElementSource(audioPlayer);
                        source.connect(analyser);
                        analyser.connect(audioContext.destination);
                        console.log('Fallback audio analyzer connected');
                        document.getElementById('lipsyncStatus').textContent = 'Fallback active';
                        document.getElementById('lipsyncStatus').style.color = '#00ff00';
                        useFallbackLipsync = true;
                    } catch (e) {
                        console.error('Fallback connection error:', e);
                        if (e.name === 'InvalidStateError' || e.message.includes('already connected')) {
                            console.log('Audio already connected, using existing analyser');
                            useFallbackLipsync = true;
                        }
                    }
                } else if (lipsyncManager) {
                    try {
                        lipsyncManager.connectAudio(audioPlayer);
                        console.log('Lipsync connected to audio');
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
