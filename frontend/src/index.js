// ═════════════════════════════════════════════════════════════
// 🔥 PUTER.JS INITIALIZATION — ADDED FOR ANCESTRAL SAGE
// ═════════════════════════════════════════════════════════════

// Load Puter.js from CDN
const puterScript = document.createElement('script');
puterScript.src = 'https://js.puter.com/v2/';
puterScript.onload = () => {
    // Initialize Puter when script loads
    if (typeof puter !== 'undefined') {
        puter.init({
            appId: 'ancestral-sage-debug',
            appName: 'Ancestral Sage Debug',
            auth: {
                method: 'anonymous' // No sign-in required
            }
        }).then(() => {
            console.log('✅ Puter.js initialized successfully');
            console.log('👤 Logged in as:', puter.me?.username || 'Anonymous');
            
            // ═════════════════════════════════════════════════════════════
            // 🔥 MEMORY SYNC TEST — RUN AFTER INITIALIZATION
            // ═════════════════════════════════════════════════════════════
            testMemorySync();
            // ═════════════════════════════════════════════════════════════
            
        }).catch(err => {
            console.error('❌ Puter.js initialization failed:', err);
        });
    }
};
document.head.appendChild(puterScript);

// Wait for Puter to load before rendering React app
window.addEventListener('load', () => {
    if (typeof puter === 'undefined') {
        console.warn('⚠️ Puter.js failed to load. Running in offline mode.');
    }
});

// ═════════════════════════════════════════════════════════════
// 🔥 MEMORY SYNC TEST FUNCTION
// ═════════════════════════════════════════════════════════════

// Function to test memory sync
async function testMemorySync() {
    try {
        const memory = await puter.kv.get('ancestral_sage_memory_latest');
        console.log('📊 MEMORY SYNC TEST RESULT:', memory || 'No memory found');
        return memory;
    } catch (error) {
        console.error('❌ MEMORY SYNC TEST FAILED:', error);
        return null;
    }
}

// ═════════════════════════════════════════════════════════════

import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Register service worker for PWA install support
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}
