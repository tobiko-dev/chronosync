import webview
import json
import os
import ctypes
import threading # Added for non-blocking timers

# API class to bridge Javascript and Windows
class ChronoApi:
    def __init__(self):
        self.window = None
        self.config_file = 'chrono_config.json'

    def set_window(self, window):
        self.window = window

    def bring_to_front(self):
        if self.window:
            self.window.restore()
            self.window.show()
            self.window.on_top = True
            
            # Use a non-blocking background timer instead of time.sleep() 
            # to prevent the app from freezing when the alarm goes off!
            def reset_top():
                self.window.on_top = False
            threading.Timer(0.1, reset_top).start()

    # Upgraded Python method to save ALL settings (Theme + Presets)
    def save_data(self, json_string):
        try:
            with open(self.config_file, 'w') as f:
                f.write(json_string)
        except Exception as e:
            print("Could not save config:", e)

    # Upgraded Python method to load settings
    def get_data(self):
        try:
            # Check for the unified config file
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return f.read()
                    
            # Migrate from the old theme-only file if it exists
            old_file = 'chrono_theme.json'
            if os.path.exists(old_file):
                with open(old_file, 'r') as f:
                    old_data = json.load(f)
                    return json.dumps({"theme": old_data.get("theme", "red"), "presets": [15, 30, 45]})
        except Exception:
            pass
            
        # Default config if no files exist
        return json.dumps({"theme": "red", "presets": [15, 30, 45]})

# HTML payload with the new UX features
HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2030+ Timer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #121316;
            --bg-surface: rgba(22, 24, 28, 0.75);
            /* Dynamic Theme Variables */
            --accent-main: #D90429;
            --accent-dark: rgb(115, 0, 0);
            --bg-glow: rgba(115, 0, 0, 0.15);
            --accent-shadow: rgba(217, 4, 41, 0.2);
            --accent-glow: rgba(217, 4, 41, 0.4);
            
            --text-main: #F3F4F6;
            --text-muted: #8D99AE;
            --glass-border: rgba(255, 255, 255, 0.04);
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: 
                radial-gradient(circle at 50% 50%, var(--bg-glow), transparent 60%);
            transition: background-image 0.5s ease;
        }

        .glass-panel {
            background: var(--bg-surface);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            box-shadow: 0 0 20px var(--accent-shadow);
            transition: box-shadow 0.5s ease;
        }

        .timer-ring {
            transition: stroke-dashoffset 0.1s linear, stroke 0.3s ease;
            transform: rotate(-90deg);
            transform-origin: center;
            filter: drop-shadow(0 0 8px var(--accent-glow));
        }

        .timer-ring-bg {
            stroke: rgba(255, 255, 255, 0.03);
            transform: rotate(-90deg);
            transform-origin: center;
        }

        .control-btn {
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .control-btn::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0));
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .control-btn:hover::before { opacity: 1; }
        .control-btn:active { transform: scale(0.95); }
        .control-btn:disabled { opacity: 0.3; cursor: not-allowed; transform: scale(1); }

        .adjust-btn {
            color: var(--text-muted);
            transition: color 0.2s, transform 0.2s;
        }
        .adjust-btn:hover:not(:disabled) {
            color: var(--text-main);
            transform: scale(1.1);
        }

        .glow-active { animation: pulse-glow 2s infinite alternate; }
        @keyframes pulse-glow {
            0% { box-shadow: 0 0 15px var(--accent-shadow); }
            100% { box-shadow: 0 0 30px var(--accent-glow); }
        }
        
        .alarm-glow {
            animation: alarm-pulse 0.6s infinite alternate;
            border-color: var(--accent-main) !important;
        }
        @keyframes alarm-pulse {
            0% { box-shadow: 0 0 20px var(--accent-shadow); }
            100% { box-shadow: 0 0 60px var(--accent-main); }
        }
        
        .font-mono-num {
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.02em;
        }

        /* Hides standard scrollbar */
        ::-webkit-scrollbar { display: none; }
        
        /* Custom styled scrollbar just for the presets list */
        .custom-scrollbar::-webkit-scrollbar { width: 4px; display: block; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
        
        input[type="number"]::-webkit-inner-spin-button, 
        input[type="number"]::-webkit-outer-spin-button { 
            -webkit-appearance: none; 
            margin: 0; 
        }

        /* Futuristic loading spinner */
        .loader-ring {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: 3px solid rgba(255, 255, 255, 0.05);
            border-top-color: rgba(255, 255, 255, 0.8);
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="antialiased selection:bg-white/10">

    <!-- Loading Overlay -->
    <div id="loading-overlay" class="fixed inset-0 z-50 flex items-center justify-center bg-[#121316] backdrop-blur-md transition-opacity duration-300">
        <div class="loader-ring"></div>
    </div>

    <div class="glass-panel rounded-3xl p-8 w-full max-w-md flex flex-col items-center relative z-10 opacity-0 transition-all duration-500" id="app-container" style="transform: translateY(20px) scale(0.95);">
        
        <!-- Header, Preset Menu & Theme Menu -->
        <div class="w-full flex justify-between items-center mb-8 px-2 relative z-30">
            
            <!-- Clickable Logo (Presets) -->
            <div class="relative">
                <button class="relative group p-1 -ml-1 rounded-md hover:bg-white/5 transition-colors" onclick="togglePresetMenu(event)" id="preset-trigger-btn">
                    <span class="text-xs uppercase tracking-[0.2em] text-[var(--text-muted)] font-semibold flex items-center gap-2 group-hover:text-[var(--accent-main)] transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3 text-[var(--accent-main)] transition-colors duration-500"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                        Chrono-Sync
                    </span>
                </button>
                
                <!-- Roll-out Preset Menu -->
                <div id="preset-menu" class="absolute top-10 left-0 w-48 bg-[#1A1C20] border border-[var(--glass-border)] rounded-xl p-3 flex flex-col gap-2 shadow-2xl opacity-0 pointer-events-none scale-95 transition-all duration-200 origin-top-left z-40">
                    <div class="text-[9px] text-[var(--text-muted)] font-bold tracking-widest px-1">SAVED PRESETS</div>
                    
                    <div id="preset-list" class="flex flex-col gap-1 max-h-40 overflow-y-auto custom-scrollbar pr-1 -mr-1">
                        <!-- Populated by JS -->
                    </div>
                    
                    <button onclick="showAddPresetForm(event)" id="btn-show-add" class="mt-1 py-1.5 rounded-md border border-dashed border-[var(--glass-border)] text-[var(--text-muted)] hover:text-white hover:border-white/20 hover:bg-white/5 text-[10px] font-bold tracking-wider transition-all">+ NEW PRESET</button>
                    
                    <div id="add-preset-form" class="hidden flex-col gap-2 mt-1 p-2 bg-black/30 rounded-lg border border-[var(--glass-border)]">
                        <div class="flex gap-2">
                            <input type="number" id="preset-m" placeholder="MM" min="0" max="10" class="w-full bg-transparent border-b border-[var(--glass-border)] text-white text-center text-sm font-mono-num outline-none focus:border-[var(--accent-main)] transition-colors" />
                            <span class="text-[var(--text-muted)] pt-1">:</span>
                            <input type="number" id="preset-s" placeholder="SS" min="0" max="59" class="w-full bg-transparent border-b border-[var(--glass-border)] text-white text-center text-sm font-mono-num outline-none focus:border-[var(--accent-main)] transition-colors" />
                        </div>
                        <div class="flex gap-1 mt-1">
                            <button onclick="saveNewPreset(event)" class="flex-1 py-1 bg-[var(--accent-main)]/20 text-[var(--accent-main)] hover:bg-[var(--accent-main)] hover:text-white rounded text-[10px] font-bold tracking-wider transition-colors">SAVE</button>
                            <button onclick="hideAddPresetForm(event)" class="flex-1 py-1 border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-white rounded text-[10px] font-bold tracking-wider transition-colors">CANCEL</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Clickable Dot (Themes) -->
            <div class="relative">
                <button id="theme-btn" class="p-2 -mr-2 hover:bg-white/5 rounded-full transition-colors relative z-20" onclick="toggleThemeMenu(event)">
                    <div class="h-2 w-2 rounded-full bg-[var(--text-muted)] transition-colors duration-300" id="status-indicator"></div>
                </button>
                
                <!-- Roll-out Color Menu -->
                <div id="theme-menu" class="absolute top-10 right-0 bg-[#1A1C20] border border-[var(--glass-border)] rounded-full p-2 flex flex-col gap-3 shadow-2xl opacity-0 pointer-events-none scale-95 transition-all duration-200 origin-top-right z-30">
                    <button class="w-4 h-4 rounded-full bg-[#D90429] hover:scale-125 transition-transform shadow-[0_0_8px_rgba(217,4,41,0.5)]" onclick="applyTheme('red', event)"></button>
                    <button class="w-4 h-4 rounded-full bg-[#00E5FF] hover:scale-125 transition-transform shadow-[0_0_8px_rgba(0,229,255,0.5)]" onclick="applyTheme('cyan', event)"></button>
                    <button class="w-4 h-4 rounded-full bg-[#D500F9] hover:scale-125 transition-transform shadow-[0_0_8px_rgba(213,0,249,0.5)]" onclick="applyTheme('purple', event)"></button>
                    <button class="w-4 h-4 rounded-full bg-[#00E676] hover:scale-125 transition-transform shadow-[0_0_8px_rgba(0,230,118,0.5)]" onclick="applyTheme('green', event)"></button>
                    <button class="w-4 h-4 rounded-full bg-[#FFD600] hover:scale-125 transition-transform shadow-[0_0_8px_rgba(255,214,0,0.5)]" onclick="applyTheme('gold', event)"></button>
                </div>
            </div>
        </div>

        <!-- Timer Display Area -->
        <div id="dial-area" class="relative w-80 h-80 flex justify-center items-center mb-10 cursor-grab active:cursor-grabbing rounded-full touch-none group">
            <svg class="absolute top-0 left-0 w-full h-full pointer-events-none" viewBox="0 0 100 100">
                <circle class="timer-ring-bg" cx="50" cy="50" r="45" fill="none" stroke-width="1.5" />
                <circle id="progress-ring" class="timer-ring" cx="50" cy="50" r="45" fill="none" stroke-width="2.5" stroke="var(--accent-main)" stroke-linecap="round" stroke-dasharray="282.743 282.743" stroke-dashoffset="254.469" />
                <circle id="progress-handle" cx="50" cy="5" r="3.5" fill="var(--text-main)" class="transition-transform duration-100 ease-linear origin-center opacity-70 group-hover:opacity-100" style="filter: drop-shadow(0 0 4px rgba(255,255,255,0.5)); transform: rotate(36deg);" />
            </svg>

            <div class="flex flex-col items-center z-10 select-none pointer-events-none">
                <div class="flex items-end justify-center mb-1 font-mono-num">
                    <span id="display-minutes" class="text-6xl font-light tracking-tighter leading-none">01</span>
                    <span class="text-4xl font-light text-[var(--text-muted)] pb-1 mx-1 animate-pulse" style="animation-duration: 1s;">:</span>
                    <span id="display-seconds" class="text-6xl font-light tracking-tighter leading-none">00</span>
                </div>
                
                <div id="setup-controls" class="flex flex-col items-center gap-1 mt-3 transition-opacity duration-300 pointer-events-auto">
                    <div class="flex items-center gap-3">
                        <button class="adjust-btn px-3 py-1 rounded-md hover:bg-white/5 text-sm font-bold tracking-widest border border-transparent hover:border-white/10 text-white" onclick="adjustTime(-10)">-10S</button>
                        <button class="text-[10px] uppercase tracking-widest text-[var(--text-muted)] hover:text-white font-bold w-10 text-center transition-colors py-1 rounded-md hover:bg-white/5 border border-transparent hover:border-white/10" id="btn-max" onclick="setMaxTime()">MAX</button>
                        <button class="adjust-btn px-3 py-1 rounded-md hover:bg-white/5 text-sm font-bold tracking-widest border border-transparent hover:border-white/10 text-white" onclick="adjustTime(10)">+10S</button>
                    </div>
                    <div class="flex items-center gap-8 mt-1">
                        <button class="adjust-btn px-2 py-1 rounded-md hover:bg-white/5 text-[10px] font-bold tracking-widest border border-transparent hover:border-white/10" onclick="adjustTime(-60)">-1M</button>
                        <button class="adjust-btn px-2 py-1 rounded-md hover:bg-white/5 text-[10px] font-bold tracking-widest border border-transparent hover:border-white/10" onclick="adjustTime(60)">+1M</button>
                    </div>
                </div>
                
                <div id="running-label" class="opacity-0 hidden text-[10px] uppercase tracking-widest text-[var(--accent-main)] font-semibold mt-8 transition-opacity duration-300 transition-colors">
                    ACTIVE
                </div>
            </div>
        </div>

        <!-- Main Controls -->
        <div class="flex justify-center items-center gap-6 w-full px-4">
            <button id="btn-reset" class="control-btn w-12 h-12 rounded-full flex justify-center items-center border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-white hover:border-white/20 disabled:opacity-30 disabled:hover:border-[var(--glass-border)] disabled:hover:text-[var(--text-muted)]" disabled onclick="resetTimer()">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
            </button>

            <button id="btn-toggle" class="control-btn w-16 h-16 rounded-full flex justify-center items-center bg-gradient-to-br from-[var(--accent-main)] to-[var(--accent-dark)] text-white transition-all duration-500" style="box-shadow: 0 0 20px var(--accent-shadow);" onclick="toggleTimer()">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6 ml-1" id="icon-play"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6 hidden" id="icon-pause"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
            </button>
            
            <button id="btn-stop" class="control-btn w-12 h-12 rounded-full flex justify-center items-center border border-[var(--glass-border)] text-[var(--text-muted)] hover:text-[var(--accent-main)] hover:border-[var(--accent-main)] disabled:opacity-30 disabled:hover:border-[var(--glass-border)] disabled:hover:text-[var(--text-muted)]" disabled onclick="stopTimer()">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="0" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
            </button>
        </div>
        
        <div id="pause-toast" class="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-[var(--bg-surface)] backdrop-blur-md border border-[var(--glass-border)] text-white px-4 py-2 rounded-full text-[10px] tracking-widest font-bold opacity-0 transition-opacity duration-300 pointer-events-none shadow-lg z-20">
            PRESS AGAIN TO PAUSE
        </div>

    </div>

    <script>
        const MAX_TIME = 10 * 60;
        const DEFAULT_TIME = 1 * 60;
        
        let totalSeconds = DEFAULT_TIME;
        let remainingSeconds = DEFAULT_TIME;
        let timerInterval = null;
        let isRunning = false;
        let isRinging = false;
        let alarmInterval = null;
        let audioCtx = null;
        
        const elMinutes = document.getElementById('display-minutes');
        const elSeconds = document.getElementById('display-seconds');
        const progressRing = document.getElementById('progress-ring');
        const progressHandle = document.getElementById('progress-handle');
        const dialArea = document.getElementById('dial-area');
        
        const btnToggle = document.getElementById('btn-toggle');
        const btnReset = document.getElementById('btn-reset');
        const btnStop = document.getElementById('btn-stop');
        const iconPlay = document.getElementById('icon-play');
        const iconPause = document.getElementById('icon-pause');
        
        const setupControls = document.getElementById('setup-controls');
        const runningLabel = document.getElementById('running-label');
        const statusIndicator = document.getElementById('status-indicator');
        const appContainer = document.getElementById('app-container');
        const pauseToast = document.getElementById('pause-toast');
        const themeMenu = document.getElementById('theme-menu');
        const presetMenu = document.getElementById('preset-menu');
        
        // --- Unified App Config (Themes & Presets) ---
        let appConfig = {
            theme: 'red',
            presets: [15, 30, 45]
        };

        const themes = {
            red: { main: '#D90429', dark: 'rgb(115, 0, 0)', bgGlow: 'rgba(115, 0, 0, 0.15)', shadow: 'rgba(217, 4, 41, 0.2)', glow: 'rgba(217, 4, 41, 0.4)' },
            cyan: { main: '#00E5FF', dark: 'rgb(0, 100, 150)', bgGlow: 'rgba(0, 150, 200, 0.15)', shadow: 'rgba(0, 229, 255, 0.2)', glow: 'rgba(0, 229, 255, 0.4)' },
            purple: { main: '#D500F9', dark: 'rgb(80, 0, 120)', bgGlow: 'rgba(120, 0, 180, 0.15)', shadow: 'rgba(213, 0, 249, 0.2)', glow: 'rgba(213, 0, 249, 0.4)' },
            green: { main: '#00E676', dark: 'rgb(0, 100, 40)', bgGlow: 'rgba(0, 180, 80, 0.15)', shadow: 'rgba(0, 230, 118, 0.2)', glow: 'rgba(0, 230, 118, 0.4)' },
            gold: { main: '#FFD600', dark: 'rgb(120, 90, 0)', bgGlow: 'rgba(180, 140, 0, 0.15)', shadow: 'rgba(255, 214, 0, 0.2)', glow: 'rgba(255, 214, 0, 0.4)' }
        };

        // --- Menu UI Logic ---
        let isThemeMenuOpen = false;
        let isPresetMenuOpen = false;
        let isAppReady = false; // Flag to check if fully initialized

        function toggleThemeMenu(e) {
            if (!isAppReady) return;
            e.stopPropagation();
            if (isPresetMenuOpen) closePresetMenu();
            isThemeMenuOpen = !isThemeMenuOpen;
            if (isThemeMenuOpen) {
                themeMenu.classList.remove('opacity-0', 'pointer-events-none', 'scale-95');
                themeMenu.classList.add('opacity-100', 'scale-100');
            } else {
                closeThemeMenu();
            }
        }

        function togglePresetMenu(e) {
            if (!isAppReady) return;
            e.stopPropagation();
            if (isThemeMenuOpen) closeThemeMenu();
            isPresetMenuOpen = !isPresetMenuOpen;
            if (isPresetMenuOpen) {
                presetMenu.classList.remove('opacity-0', 'pointer-events-none', 'scale-95');
                presetMenu.classList.add('opacity-100', 'scale-100');
            } else {
                closePresetMenu();
            }
        }

        function closeThemeMenu() {
            isThemeMenuOpen = false;
            themeMenu.classList.add('opacity-0', 'pointer-events-none', 'scale-95');
            themeMenu.classList.remove('opacity-100', 'scale-100');
        }

        function closePresetMenu() {
            isPresetMenuOpen = false;
            presetMenu.classList.add('opacity-0', 'pointer-events-none', 'scale-95');
            presetMenu.classList.remove('opacity-100', 'scale-100');
            hideAddPresetForm(); // reset form state
        }

        document.addEventListener('click', (e) => {
            if (isThemeMenuOpen && !themeMenu.contains(e.target)) closeThemeMenu();
            if (isPresetMenuOpen && !presetMenu.contains(e.target)) closePresetMenu();
        });
        
        // Prevent clicks inside menus from bubbling up and closing them
        themeMenu.addEventListener('click', e => e.stopPropagation());
        presetMenu.addEventListener('click', e => e.stopPropagation());

        // --- Persistence Logic ---

        // The core initialization function that safely loads all settings and removes the loader
        function initializeApp(savedDataStr) {
            if (isAppReady) return;
            isAppReady = true;

            try {
                if (savedDataStr) {
                    let parsedData = JSON.parse(savedDataStr);
                    if (parsedData) appConfig = parsedData;
                }
                
                applyTheme(appConfig.theme || 'red', null, true); // true = skip save during init
                renderPresets();
                updateDisplay();
                updateUIState();
            } catch (error) {
                console.error("Initialization error:", error);
            } finally {
                // ALWAYS clear the loading screen, even if settings failed to parse
                const loader = document.getElementById('loading-overlay');
                if (loader) {
                    loader.style.opacity = '0';
                    setTimeout(() => loader.remove(), 300);
                }

                // Animate app entry safely
                if (appContainer) {
                    appContainer.style.transition = 'all 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
                    appContainer.style.opacity = '1';
                    appContainer.style.transform = 'translateY(0) scale(1)';
                }
            }
        }

        function saveConfig() {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.save_data(JSON.stringify(appConfig));
            } else {
                localStorage.setItem('chronoConfig', JSON.stringify(appConfig));
            }
        }

        function applyTheme(themeName, event, skipSave = false) {
            if (event) event.stopPropagation();
            const theme = themes[themeName] || themes.red;
            
            document.documentElement.style.setProperty('--accent-main', theme.main);
            document.documentElement.style.setProperty('--accent-dark', theme.dark);
            document.documentElement.style.setProperty('--bg-glow', theme.bgGlow);
            document.documentElement.style.setProperty('--accent-shadow', theme.shadow);
            document.documentElement.style.setProperty('--accent-glow', theme.glow);
            
            appConfig.theme = themeName;
            if (!skipSave) saveConfig();
            closeThemeMenu();
        }

        // --- Preset Logic ---
        function renderPresets() {
            const list = document.getElementById('preset-list');
            list.innerHTML = '';
            
            if (appConfig.presets.length === 0) {
                list.innerHTML = '<div class="text-xs text-[var(--text-muted)] text-center py-2 opacity-50 italic">No presets saved</div>';
                return;
            }
            
            appConfig.presets.forEach((seconds, index) => {
                const {m, s} = formatTime(seconds);
                const el = document.createElement('div');
                el.className = 'flex justify-between items-center group/item p-1 hover:bg-white/5 rounded-md cursor-pointer transition-colors';
                el.innerHTML = `
                    <div class="flex-1 font-mono-num text-sm text-[var(--text-main)] group-hover/item:text-[var(--accent-main)] transition-colors font-semibold px-2" onclick="applyPreset(${seconds})">
                        ${m}:${s}
                    </div>
                    <button class="opacity-0 group-hover/item:opacity-100 text-[var(--text-muted)] hover:text-red-500 transition-all p-1" onclick="deletePreset(${index})" title="Delete Preset">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                    </button>
                `;
                list.appendChild(el);
            });
        }

        function applyPreset(seconds) {
            if (!isAppReady || isRunning) return; 
            if (isRinging) stopAlarm();
            
            totalSeconds = seconds;
            remainingSeconds = seconds;
            updateDisplay();
            updateUIState();
            closePresetMenu();
        }

        function deletePreset(index) {
            if (!isAppReady) return;
            appConfig.presets.splice(index, 1);
            saveConfig();
            renderPresets();
        }

        function showAddPresetForm(e) {
            if (!isAppReady) return;
            if(e) e.stopPropagation();
            document.getElementById('btn-show-add').classList.add('hidden');
            document.getElementById('add-preset-form').classList.remove('hidden');
            document.getElementById('add-preset-form').classList.add('flex');
            
            // Pre-fill with current dial time
            const {m, s} = formatTime(remainingSeconds);
            document.getElementById('preset-m').value = remainingSeconds > 0 ? m : '';
            document.getElementById('preset-s').value = remainingSeconds > 0 ? s : '';
            document.getElementById('preset-m').focus();
        }

        function hideAddPresetForm(e) {
            if(e) e.stopPropagation();
            document.getElementById('add-preset-form').classList.add('hidden');
            document.getElementById('add-preset-form').classList.remove('flex');
            document.getElementById('btn-show-add').classList.remove('hidden');
        }

        function saveNewPreset(e) {
            if (!isAppReady) return;
            if(e) e.stopPropagation();
            let m = parseInt(document.getElementById('preset-m').value) || 0;
            let s = parseInt(document.getElementById('preset-s').value) || 0;
            
            if (m > 10) m = 10;
            if (m === 10) s = 0; // Max time hard cap
            if (s > 59) s = 59;
            if (m < 0) m = 0;
            if (s < 0) s = 0;
            
            const total = (m * 60) + s;
            if (total > 0 && total <= MAX_TIME) {
                // Check for duplicates
                if (!appConfig.presets.includes(total)) {
                    appConfig.presets.push(total);
                    appConfig.presets.sort((a, b) => a - b); // Sort ascending
                    saveConfig();
                }
                renderPresets();
                hideAddPresetForm();
            }
        }


        // Prevent dragging the dial when interacting with controls
        setupControls.addEventListener('mousedown', e => e.stopPropagation());
        setupControls.addEventListener('touchstart', e => e.stopPropagation(), { passive: false });
        setupControls.addEventListener('click', e => e.stopPropagation());

        const fixedRadius = 45; 
        const circumference = fixedRadius * 2 * Math.PI;
        progressRing.style.strokeDasharray = `${circumference} ${circumference}`;
        
        // --- Keyboard Controls & Toast Logic ---
        let pausePending = false;
        let pauseTimeout = null;

        window.addEventListener('keydown', (e) => {
            if (!isAppReady) return;
            if (e.code === 'Space' || e.key === 'Enter') {
                e.preventDefault(); 
                
                if (isRinging) {
                    stopAlarm();
                    return;
                }

                if (!isRunning && remainingSeconds > 0) {
                    toggleTimer();
                } else if (isRunning) {
                    if (!pausePending) {
                        pausePending = true;
                        pauseToast.classList.remove('opacity-0');
                        
                        pauseTimeout = setTimeout(() => {
                            pausePending = false;
                            pauseToast.classList.add('opacity-0');
                        }, 2000); 
                    } else {
                        clearTimeout(pauseTimeout);
                        pausePending = false;
                        pauseToast.classList.add('opacity-0');
                        toggleTimer();
                    }
                }
            }
        });

        function formatTime(seconds) {
            const m = Math.floor(seconds / 60);
            const s = seconds % 60;
            return {
                m: m.toString().padStart(2, '0'),
                s: s.toString().padStart(2, '0')
            };
        }

        function updateDisplay() {
            const timeStr = formatTime(remainingSeconds);
            elMinutes.textContent = timeStr.m;
            elSeconds.textContent = timeStr.s;

            let progress = remainingSeconds / MAX_TIME;
            
            if (isRunning && remainingSeconds < (MAX_TIME * 0.05) && remainingSeconds > 0) {
                 progressRing.style.stroke = '#FFFFFF'; 
                 statusIndicator.classList.replace('bg-[var(--accent-main)]', 'bg-[#FFFFFF]');
            } else {
                 progressRing.style.stroke = 'var(--accent-main)';
                 if (isRunning) {
                     statusIndicator.classList.replace('bg-[var(--text-muted)]', 'bg-[var(--accent-main)]');
                     statusIndicator.classList.replace('bg-[#FFFFFF]', 'bg-[var(--accent-main)]');
                 }
            }

            const offset = circumference - (progress * circumference);
            progressRing.style.strokeDashoffset = offset;

            const angle = progress * 360;
            progressHandle.style.transform = `rotate(${angle}deg)`;
        }

        function updateUIState() {
            if (isRinging) {
                iconPlay.classList.add('hidden');
                iconPause.classList.add('hidden');
                setupControls.classList.add('opacity-0', 'pointer-events-none');
                dialArea.classList.remove('cursor-grab', 'active:cursor-grabbing');
                
                setTimeout(() => {
                    setupControls.classList.add('hidden');
                    runningLabel.textContent = "ALARM - PRESS STOP";
                    runningLabel.classList.remove('hidden');
                    setTimeout(() => runningLabel.classList.remove('opacity-0'), 50);
                }, 300);

                btnReset.disabled = true;
                btnStop.disabled = false;
                btnStop.style.borderColor = "var(--accent-glow)";
                btnStop.style.color = "var(--accent-main)";
                
                appContainer.classList.remove('glow-active');
                appContainer.classList.add('alarm-glow');
                statusIndicator.classList.replace('bg-[var(--text-muted)]', 'bg-[#FFFFFF]');
                statusIndicator.classList.replace('bg-[var(--accent-main)]', 'bg-[#FFFFFF]');
                
            } else if (isRunning) {
                iconPlay.classList.add('hidden');
                iconPause.classList.remove('hidden');
                setupControls.classList.add('opacity-0', 'pointer-events-none');
                dialArea.classList.remove('cursor-grab', 'active:cursor-grabbing');
                
                setTimeout(() => {
                    setupControls.classList.add('hidden');
                    runningLabel.textContent = "ACTIVE";
                    runningLabel.classList.remove('hidden');
                    setTimeout(() => runningLabel.classList.remove('opacity-0'), 50);
                }, 300);

                btnReset.disabled = true;
                btnStop.disabled = false;
                btnStop.style.borderColor = "";
                btnStop.style.color = "";
                
                appContainer.classList.add('glow-active');
                appContainer.classList.remove('alarm-glow');
                statusIndicator.classList.replace('bg-[var(--text-muted)]', 'bg-[var(--accent-main)]');
                statusIndicator.classList.replace('bg-[#FFFFFF]', 'bg-[var(--accent-main)]');
                
            } else {
                iconPlay.classList.remove('hidden');
                iconPause.classList.add('hidden');
                dialArea.classList.add('cursor-grab');
                runningLabel.classList.add('opacity-0');
                
                setTimeout(() => {
                    runningLabel.classList.add('hidden');
                    setupControls.classList.remove('hidden');
                    setTimeout(() => setupControls.classList.remove('opacity-0', 'pointer-events-none'), 50);
                }, 300);

                btnReset.disabled = (totalSeconds === 0 && remainingSeconds === 0);
                btnStop.disabled = (remainingSeconds === totalSeconds);
                btnStop.style.borderColor = "";
                btnStop.style.color = "";

                if (remainingSeconds <= 0) {
                    btnToggle.disabled = true;
                    btnToggle.style.opacity = '0.5';
                } else {
                    btnToggle.disabled = false;
                    btnToggle.style.opacity = '1';
                }
                
                appContainer.classList.remove('glow-active', 'alarm-glow');
                statusIndicator.className = 'h-2 w-2 rounded-full bg-[var(--text-muted)] transition-colors duration-300';
            }
        }

        // --- Robust Clamped Drag Logic ---
        let isDragging = false;
        let lastAngle = 0;
        let cumulativeAngle = 0; 

        function getAngle(x, y) {
            const rect = dialArea.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            let angle = Math.atan2(y - centerY, x - centerX) * (180 / Math.PI);
            angle += 90; 
            if (angle < 0) angle += 360;
            return angle;
        }

        function handleDragStart(e) {
            if (!isAppReady || isRunning || isRinging) return;
            isDragging = true;
            dialArea.classList.add('cursor-grabbing');
            dialArea.classList.remove('cursor-grab');
            
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            
            lastAngle = getAngle(clientX, clientY);
            cumulativeAngle = (remainingSeconds / MAX_TIME) * 360;
        }

        function handleDragMove(e) {
            if (!isDragging || !isAppReady || isRunning || isRinging) return;
            e.preventDefault(); 
            
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            const currentAngle = getAngle(clientX, clientY);
            
            let delta = currentAngle - lastAngle;
            
            if (delta > 180) delta -= 360;
            if (delta < -180) delta += 360;
            
            cumulativeAngle += delta;
            
            if (cumulativeAngle < 0) cumulativeAngle = 0;
            if (cumulativeAngle > 360) cumulativeAngle = 360;
            
            lastAngle = currentAngle;

            let seconds = Math.round((cumulativeAngle / 360) * MAX_TIME);
            
            // Major Performance Optimization: Only trigger heavy UI updates if the time actually ticked!
            if (seconds !== remainingSeconds) {
                totalSeconds = seconds;
                remainingSeconds = seconds;
                updateDisplay();
                
                btnReset.disabled = (totalSeconds === 0 && remainingSeconds === 0);
                btnStop.disabled = true;
                if (remainingSeconds <= 0) {
                    btnToggle.disabled = true;
                    btnToggle.style.opacity = '0.5';
                } else {
                    btnToggle.disabled = false;
                    btnToggle.style.opacity = '1';
                }
            }
        }

        function handleDragEnd() {
            if (!isDragging) return;
            isDragging = false;
            dialArea.classList.remove('cursor-grabbing');
            dialArea.classList.add('cursor-grab');
            updateUIState(); 
        }

        dialArea.addEventListener('mousedown', handleDragStart);
        window.addEventListener('mousemove', handleDragMove);
        window.addEventListener('mouseup', handleDragEnd);
        dialArea.addEventListener('touchstart', handleDragStart, { passive: false });
        window.addEventListener('touchmove', handleDragMove, { passive: false });
        window.addEventListener('touchend', handleDragEnd);

        function setMaxTime() {
            if (!isAppReady || isRunning || isRinging) return;
            totalSeconds = MAX_TIME;
            remainingSeconds = MAX_TIME;
            updateDisplay();
            updateUIState();
        }

        function adjustTime(secondsToAdd) {
            if (!isAppReady || isRunning || isRinging) return;
            totalSeconds += secondsToAdd;
            if (totalSeconds < 0) totalSeconds = 0;
            if (totalSeconds > MAX_TIME) totalSeconds = MAX_TIME;
            remainingSeconds = totalSeconds;
            updateDisplay();
            updateUIState();
        }

        function toggleTimer() {
            if (!isAppReady) return;
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') audioCtx.resume();

            if (isRinging) {
                stopAlarm();
                return;
            }

            if (isRunning) {
                clearInterval(timerInterval);
                isRunning = false;
                updateUIState();
            } else {
                if (remainingSeconds === 0) return; 
                
                isRunning = true;
                updateUIState();
                
                timerInterval = setInterval(() => {
                    remainingSeconds--;
                    updateDisplay();
                    
                    if (remainingSeconds <= 0) {
                        timerComplete();
                    }
                }, 1000);
            }
        }

        function resetTimer() {
            if (!isAppReady || isRunning || isRinging) return;
            totalSeconds = 0;
            remainingSeconds = 0;
            updateDisplay();
            updateUIState();
        }
        
        function stopTimer() {
            if (!isAppReady) return;
            if (isRinging) {
                stopAlarm();
                return;
            }
            clearInterval(timerInterval);
            isRunning = false;
            remainingSeconds = totalSeconds; 
            updateDisplay();
            updateUIState();
            progressRing.style.stroke = 'var(--accent-main)';
        }

        function timerComplete() {
            clearInterval(timerInterval);
            isRunning = false;
            isRinging = true;
            remainingSeconds = 0;
            updateDisplay();
            updateUIState();
            
            progressRing.style.strokeDashoffset = circumference; 
            
            // Call Python API to bring window to the front
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.bring_to_front();
            }

            playBeepSequence();

            if (document.hasFocus()) {
                setTimeout(() => {
                    if (isRinging) stopAlarm();
                }, 1500);
            } else {
                alarmInterval = setInterval(playBeepSequence, 1500);
            }
        }
        
        function stopAlarm() {
            isRinging = false;
            clearInterval(alarmInterval);
            progressRing.style.stroke = 'var(--accent-main)';
            
            remainingSeconds = totalSeconds;
            updateDisplay();
            updateUIState();
        }

        function playBeepSequence() {
            try {
                if (!audioCtx) return;
                
                const playBeep = (freq, type, duration, delay) => {
                    setTimeout(() => {
                        const oscillator = audioCtx.createOscillator();
                        const gainNode = audioCtx.createGain();
                        
                        oscillator.type = type;
                        oscillator.frequency.setValueAtTime(freq, audioCtx.currentTime);
                        
                        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
                        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
                        
                        oscillator.connect(gainNode);
                        gainNode.connect(audioCtx.destination);
                        
                        oscillator.start();
                        oscillator.stop(audioCtx.currentTime + duration);
                    }, delay);
                };

                playBeep(600, 'square', 0.15, 0);
                playBeep(400, 'square', 0.15, 200);
                playBeep(600, 'square', 0.15, 400);
                playBeep(400, 'square', 0.15, 600);
            } catch (e) {
                console.log("Audio not supported or blocked");
            }
        }

        // --- Safe & Official Initialization Sequence ---
        
        // The officially supported way to wait for Python backend
        window.addEventListener('pywebviewready', function() {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.get_data()
                    .then(data => initializeApp(data))
                    .catch(e => initializeApp(null));
            } else {
                initializeApp(null);
            }
        });

        // Failsafe: if running in a normal browser or if the backend completely hangs
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                if (!isAppReady) {
                    console.log("Backend timeout, booting locally.");
                    let savedStr = localStorage.getItem('chronoConfig');
                    initializeApp(savedStr);
                }
            }, 800); // 800ms is plenty of time for pywebview to attach properly
        });
        
    </script>
</body>
</html>"""

if __name__ == '__main__':
    api = ChronoApi()
    
    # Calculate perfect center of screen on Windows
    window_width = 480
    window_height = 620
    try:
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        pos_x = int((screen_width - window_width) / 2)
        pos_y = int((screen_height - window_height) / 2)
    except Exception:
        pos_x = None
        pos_y = None
    
    window = webview.create_window(
        title='Chrono-Sync 2030+',
        html=HTML_CONTENT,
        width=window_width,       
        height=window_height,
        x=pos_x,         
        y=pos_y,         
        resizable=False, 
        background_color='#121316',
        js_api=api
    )
    
    api.set_window(window)
    webview.start(private_mode=False)