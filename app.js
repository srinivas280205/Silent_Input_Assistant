const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const VOCABULARY = ['yes', 'no', 'help', 'water', 'pain', 'stop'];

// Dirichlet-like distribution for realistic confidence scores
function dirichletSample(n, alpha = 1.8) {
  const samples = Array.from({ length: n }, () => -Math.log(Math.random() + 1e-9) * alpha);
  const total = samples.reduce((a, b) => a + b, 0);
  return samples.map(s => s / total);
}

// Simulate Whisper CNN Model (Model A)
function simulateWhisperModel(noiseLevel) {
  const scores = dirichletSample(6);
  const topIdx = scores.indexOf(Math.max(...scores));
  // Noise reduces audio confidence
  const rawConf = Math.max(...scores);
  const conf = rawConf * (1 - noiseLevel * 0.55);
  return {
    word: VOCABULARY[topIdx],
    confidence: Math.round(conf * 100 * 10) / 10,
    scores: Object.fromEntries(VOCABULARY.map((w, i) => [w, Math.round(scores[i] * 100 * 10) / 10])),
    _raw: scores
  };
}

// Simulate Lip CNN+LSTM Model (Model B)
function simulateLipModel(lightingLevel) {
  const scores = dirichletSample(6);
  const topIdx = scores.indexOf(Math.max(...scores));
  // Poor lighting reduces video confidence
  const rawConf = Math.max(...scores);
  const conf = rawConf * (0.3 + lightingLevel * 0.7);
  return {
    word: VOCABULARY[topIdx],
    confidence: Math.round(conf * 100 * 10) / 10,
    scores: Object.fromEntries(VOCABULARY.map((w, i) => [w, Math.round(scores[i] * 100 * 10) / 10])),
    _raw: scores
  };
}

// Dynamic Weighted Fusion
function dynamicFusion(whisper, lip, noiseLevel, lightingLevel) {
  // Environment-aware weight calculation
  const audioWeight = Math.max(0.05, 1.0 - noiseLevel);
  const videoWeight = Math.max(0.05, 0.3 + lightingLevel * 0.7);
  const total = audioWeight + videoWeight;
  const aw = audioWeight / total;
  const vw = videoWeight / total;

  // Weighted fusion of raw probability vectors
  const fusedScores = VOCABULARY.map((_, i) => aw * whisper._raw[i] + vw * lip._raw[i]);
  const topIdx = fusedScores.indexOf(Math.max(...fusedScores));
  const conf = Math.max(...fusedScores);

  return {
    word: VOCABULARY[topIdx],
    confidence: Math.round(conf * 100 * 10) / 10,
    scores: Object.fromEntries(VOCABULARY.map((w, i) => [w, Math.round(fusedScores[i] * 100 * 10) / 10])),
    audio_weight: Math.round(aw * 100),
    video_weight: Math.round(vw * 100)
  };
}

// ── API Routes ───────────────────────────────────────────────────────────────

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/predict', (req, res) => {
  const noiseLevel   = Math.min(1, Math.max(0, (req.body.noise_level   ?? 0.3)));
  const lightingLevel = Math.min(1, Math.max(0, (req.body.lighting_level ?? 0.8)));

  const whisperResult = simulateWhisperModel(noiseLevel);
  const lipResult     = simulateLipModel(lightingLevel);
  const fusionResult  = dynamicFusion(whisperResult, lipResult, noiseLevel, lightingLevel);

  // Simulated latency in ms (1.4 – 2.2s range, like the paper states ~1.8s)
  const latency = (1400 + Math.random() * 800).toFixed(0);

  res.json({
    whisper: { word: whisperResult.word, confidence: whisperResult.confidence, scores: whisperResult.scores },
    lip:     { word: lipResult.word,     confidence: lipResult.confidence,     scores: lipResult.scores     },
    fusion:  fusionResult,
    latency_ms: parseInt(latency),
    environment: {
      noise_level:    Math.round(noiseLevel * 100),
      lighting_level: Math.round(lightingLevel * 100)
    }
  });
});

app.get('/status', (req, res) => {
  res.json({ camera: true, microphone: true, models_loaded: true, mode: 'SIMULATION', version: '1.0.0' });
});

// ── Start (local) / Export (Vercel) ─────────────────────────────────────────

const PORT = process.env.PORT || 5000;

if (require.main === module) {
  app.listen(PORT, () => {
    console.log('');
    console.log('  ╔══════════════════════════════════════════════════════╗');
    console.log('  ║   Silent Input Assistant — Simulation Demo           ║');
    console.log('  ║   CNN–RNN Multimodal Lip & Whisper Recognition       ║');
    console.log('  ╠══════════════════════════════════════════════════════╣');
    console.log(`  ║   Running at:  http://localhost:${PORT}                  ║`);
    console.log('  ║   Mode:        SIMULATION (no real models needed)    ║');
    console.log('  ╚══════════════════════════════════════════════════════╝');
    console.log('');
  });
}

module.exports = app;
