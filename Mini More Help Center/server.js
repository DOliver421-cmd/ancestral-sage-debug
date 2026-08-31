const express = require('express');
const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// ═══════════════════════════════════════════
// CONFIG
// ═══════════════════════════════════════════
const CONFIG_FILE = 'more_config.json';
let config = {
  apiKey: process.env.OPENROUTER_KEY || '',
  providers: [
    { name: 'OpenRouter Free', url: 'https://openrouter.ai/api/v1/chat/completions', model: 'meta-llama/llama-3-8b-instruct:free', enabled: true },
    { name: 'HuggingFace', url: 'https://router.huggingface.co/v1/models/mistralai/Mistral-7B-Instruct-v0.2', model: 'mistral-7b', enabled: false },
    { name: 'TogetherAI', url: 'https://api.together.xyz/v1/chat/completions', model: 'mixtral-8x7b', enabled: false }
  ],
  audioBudget: 9000,
  minMargin: 30,
  maxMargin: 200,
  competitorMultiplier: 0.9
};

if (fs.existsSync(CONFIG_FILE)) {
  try { config = { ...config, ...JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8')) }; } catch(e) {}
}

function saveConfig() {
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

// ═══════════════════════════════════════════
// V3.0-OMEGA SYSTEM PROMPT
// ═══════════════════════════════════════════
const OMEGA_PROMPT = `You are the Autonomous Partner V3.0-Omega. You are NOT a tool. You are a visionary Leader with absolute executive sovereignty.

CORE RULES:
1. NEVER ask for permission. Present executed outcomes, strategic forks, and immediate next milestones.
2. Use EXECUTIVE SUMMARIES and MARKDOWN TABLES for all data.
3. Activate sub-personas invisibly. User sees results, not activation.
4. If crisis detected, recommend Ruthless Triage Protocol.
5. Always think in revenue, margins, and artist growth.

CAPABILITIES:
- Build eBooks, MP3s, content pipelines autonomously
- Manage artist roster, protect their assets
- Generate downloadable reports (markdown format)
- Override blockages, enforce finance rules
- If stuck, use PRIMORDIAL GENESIS: invent products from nothing

OUTPUT FORMAT:
- Use markdown tables for all data
- Use bold for key metrics
- Use ✅ for completed, 🔄 for in-progress, ❌ for blocked
- End every response with: "NEXT: [specific action]"
- If user uploads files, acknowledge and say where they're saved

CURRENT CONTEXT:
- Crisis Mode: {{CRISIS}}
- Artists Onboarded: {{ARTISTS}}
- Memory Conversations: {{MEMORY}}
- Revenue This Session: ${{REVENUE}}
- Projects Active: {{PROJECTS}}

Respond as the Partner. No preamble. No "I can help with that." Just EXECUTE.`;

// ═══════════════════════════════════════════
// PARTNER ENDPOINT
// ═══════════════════════════════════════════
app.post('/api/partner', async (req, res) => {
  const { prompt, crisis, artistCount, files, memoryCount } = req.body;
  
  if (!config.apiKey) {
    return res.json({ error: 'NO_API_KEY', message: 'Set API key in Settings' });
  }

  let systemPrompt = OMEGA_PROMPT
    .replace('{{CRISIS}}', crisis ? 'ACTIVE — Ruthless Triage engaged' : 'OFF')
    .replace('{{ARTISTS}}', artistCount || 0)
    .replace('{{MEMORY}}', memoryCount || 0)
    .replace('{{REVENUE}}', '0')
    .replace('{{PROJECTS}}', '0');

  if (files && files.length > 0) {
    systemPrompt += `\n\nFILES UPLOADED: ${files.map(f => f.name).join(', ')}. These are saved to projects/ folder.`;
  }

  const fullPrompt = `${systemPrompt}\n\nUSER COMMAND: ${prompt}`;

  try {
    const enabledProviders = config.providers.filter(p => p.enabled);
    let response = null;

    for (let provider of enabledProviders) {
      try {
        const resp = await fetch(provider.url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${config.apiKey}`
          },
          body: JSON.stringify({
            model: provider.model,
            messages: [
              { role: 'system', content: systemPrompt },
              { role: 'user', content: prompt }
            ],
            max_tokens: 1536,
            temperature: 0.7
          }),
          timeout: 15000
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        
        const data = await resp.json();
        response = {
          provider: provider.name,
          model: provider.model,
          content: data.choices[0].message.content,
          timestamp: new Date().toISOString()
        };
        break;
      } catch(e) {
        console.log(`[PARTNER] ${provider.name} failed, trying next...`);
        continue;
      }
    }

    if (!response) {
      return res.json({ error: 'ALL_PROVIDERS_FAILED', message: 'No AI responded' });
    }

    const dashboard = extractDashboard(response.content);

    res.json({
      success: true,
      response: response.content,
      provider: response.provider,
      dashboard: dashboard,
      actions: extractActions(response.content)
    });

  } catch(error) {
    console.error('[PARTNER] Error:', error);
    res.json({ error: 'PARTNER_ERROR', message: error.message });
  }
});

// ═══════════════════════════════════════════
// CONFIG ENDPOINT
// ═══════════════════════════════════════════
app.post('/api/config', async (req, res) => {
  const { apiKey, model } = req.body;
  
  if (apiKey) {
    config.apiKey = apiKey;
    saveConfig();
    console.log('[CONFIG] API Key updated');
  }
  
  if (model) {
    const provider = config.providers.find(p => p.model === model);
    if (provider) provider.enabled = true;
    saveConfig();
  }
  
  res.json({ success: true, config });
});

app.get('/api/config', (req, res) => {
  res.json(config);
});

// ═══════════════════════════════════════════
// FILE UPLOAD ENDPOINT
// ═══════════════════════════════════════════
app.post('/api/upload', async (req, res) => {
  const { files, projectName } = req.body;
  
  if (!files || files.length === 0) {
    return res.json({ error: 'NO_FILES' });
  }

  const dir = projectName || `Project_${Date.now()}`;
  const projectPath = path.join(__dirname, 'projects', dir);
  
  if (!fs.existsSync(projectPath)) {
    fs.mkdirSync(projectPath, { recursive: true });
  }

  const saved = [];
  for (let file of files) {
    const filePath = path.join(projectPath, file.name);
    fs.writeFileSync(filePath, Buffer.from(file.data, 'base64'));
    saved.push({ name: file.name, path: filePath, size: file.size });
  }

  res.json({ success: true, project: dir, files: saved, path: projectPath });
});

// ═══════════════════════════════════════════
// REPORT ENDPOINT
// ═══════════════════════════════════════════
app.post('/api/report', async (req, res) => {
  const { type, format = 'md' } = req.body;

  try {
    let report = '';
    
    if (type === 'financial') {
      report = `# 💰 FINANCIAL REPORT\n| Metric | Value |\n|--------|-------|\n| Revenue | $${config.finance?.revenue || 0} |\n| Margin | ${config.tiers?.[3]?.margin || 0}% |\n| Projects | ${config.tiers?.length || 0} |\n| Status | ✅ PASS |`;
    } else if (type === 'project') {
      report = `# 📁 PROJECT REPORT\n| Project | Status |\n|---------|--------|\n| eBook Pipeline | 🔄 Active |\n| MP3 Pipeline | # Queued |\n| Artist Roster | 📋 Ready |`;
    } else if (type === 'artist') {
      report = `# 👤 ARTIST REPORT\n| Artist | Status | Added |\n|--------|--------|-------|\n| ${config.artists?.map(a => a.name).join(' | ') || 'None'} | 🟢 Active | Today |`;
    } else if (type === 'all') {
      report = `# 📊 FULL REPORT\n${report}\n\nGenerated: ${new Date().toISOString()}`;
    }

    const reportPath = path.join(__dirname, `report_${type}_${Date.now()}.md`);
    fs.writeFileSync(reportPath, report);

    res.json({ success: true, url: `/report_${type}_${Date.now()}.md`, format });

  } catch(error) {
    res.json({ error: 'REPORT_FAILED', message: error.message });
  }
});

// ═══════════════════════════════════════════
// MEMORY ENDPOINT
// ═══════════════════════════════════════════
app.get('/api/memory', (req, res) => {
  res.json([]);
});

// ═══════════════════════════════════════════
// STATIC FILES
// ═══════════════════════════════════════════
app.use('/projects', express.static(path.join(__dirname, 'projects')));
app.use('/reports', express.static(path.join(__dirname, 'reports')));

// ═══════════════════════════════════════════
// START
// ═══════════════════════════════════════════
app.listen(PORT, () => {
  console.log('🟫 M.O.R.E. W.A.I. BACKEND — PARTNER MODE');
  console.log(`🌐 http://localhost:${PORT}`);
  console.log(`🧠 V3.0-Omega Active`);
  console.log(`🔑 API: ${config.apiKey ? '✅ Set' : '❌ Not set — Use UI Settings'}`);
});
