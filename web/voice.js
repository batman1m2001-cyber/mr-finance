/* Talking to the assistant (docs/VOICE_PLAN.md): the microphone streams to WS /api/assistant/voice, which hears the
   question (the callbot's VAD and STT) and says `asked` once the person has been quiet; the panel asks it as any
   typed question, with `voice: true`, and forwards the answer's words back (`say`), which come back as one WAV per
   sentence, played one after another as soon as each is ready.

   Half duplex (V-D6): the microphone is not sent while the assistant thinks or speaks, so it never hears itself;
   once the last sentence has played, it listens again. “Dừng” stops the answer and listens again.

   voice({onState, onHeard, onAsked, onSpeak, onLevel}) → {start, close, active, say, drop, end, stop}.
   States: connecting, listening, thinking, speaking, off. onAsked(text) returns false when the panel cannot ask
   (a turn already running): the microphone listens again. */

const GAP_MS = 250;  // between two sentences: room to take in a number
const b64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0)).buffer;

export function voice({onState = () => {}, onHeard = () => {}, onAsked = () => false, onSpeak = () => {}, onLevel = () => {}} = {}) {
  let ctx = null, stream = null, node = null, ws = null, state = "off";
  let turn = 0, stopped = 0, said = false, spoken = 0;  // the answer being read; the last stopped; words sent; read to its end
  let queue = [], playing = null, timer = 0;

  const set = (s, why) => { state = s; onState(s, why); };
  const send = (m) => { if (ws && ws.readyState === 1) ws.send(m instanceof ArrayBuffer ? m : JSON.stringify(m)); };  // audio as binary

  const listenAgain = () => { send({type: "listen"}); set("listening"); };
  const playNext = () => {
    timer = 0;
    if (playing || !ctx) return;
    const next = queue.shift();
    if (!next) {
      onSpeak(null);
      if (state === "speaking" && spoken === turn) listenAgain();
      return;
    }
    const src = ctx.createBufferSource();
    src.buffer = next.audio; src.connect(ctx.destination);
    playing = src; onSpeak(next.text);
    src.onended = () => { if (playing === src) { playing = null; timer = setTimeout(playNext, GAP_MS); } };
    src.start();
  };
  const hush = () => {
    queue = []; clearTimeout(timer); timer = 0;
    if (playing) { const p = playing; playing = null; try { p.stop(); } catch (_) { /* already ended */ } }
    onSpeak(null);
  };

  const onMessage = async (raw) => {
    let m; try { m = JSON.parse(raw.data); } catch (_) { return; }
    if (m.type === "ready") set("listening");
    else if (m.type === "heard") onHeard(m.text);
    else if (m.type === "asked") {
      turn += 1; said = false; set("thinking");
      if (onAsked(m.text) === false) listenAgain();
    } else if (m.type === "voice") {
      if (m.turn !== turn || turn <= stopped) return;
      try {
        const audio = await ctx.decodeAudioData(b64(m.wav));
        if (m.turn !== turn || turn <= stopped) return;
        queue.push({audio, text: m.text});
        if (state === "thinking") set("speaking");
        if (!playing && !timer) playNext();
      } catch (err) { console.error("voice: a sentence could not be decoded", err); }
    } else if (m.type === "spoken") {
      if (m.turn !== turn || turn <= stopped) return;
      spoken = m.turn;
      if (state === "thinking") set("speaking");  // nothing to read (every sentence failed): listen again
      if (!playing && !timer) playNext();
    }
  };

  async function start() {
    if (state !== "off") return;
    set("connecting");
    // made and resumed inside the click: iOS plays nothing from a context started later
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    ctx.resume();
    try {
      stream = await navigator.mediaDevices.getUserMedia({audio: {channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true}});
      await ctx.audioWorklet.addModule("voice-worklet.js?v=20261026v1");
    } catch (err) {
      close(err.name === "NotAllowedError" ? "Chưa được phép dùng micro: hãy cho phép trong cài đặt của trình duyệt." : `Không mở được micro (${err.message}).`);
      return;
    }
    const mic = ctx.createMediaStreamSource(stream);
    node = new AudioWorkletNode(ctx, "mf-capture");
    node.port.onmessage = ({data}) => {
      if (state !== "listening") return;
      onLevel(data.level);
      send(data.frame);
    };
    mic.connect(node);  // the worklet's output is not connected: nothing of the microphone is played back
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/api/assistant/voice?rate=${ctx.sampleRate}`);
    ws.binaryType = "arraybuffer";
    ws.onmessage = onMessage;
    ws.onclose = (e) => { if (state !== "off") close(e.code === 1000 ? "" : "Mất kết nối giọng nói; bấm micro để thử lại."); };
  }

  function close(why = "") {
    const was = ws; ws = null;
    hush();
    try { was && was.close(1000); } catch (_) { /* closing */ }
    try { node && node.disconnect(); } catch (_) { /* gone */ }
    for (const t of (stream && stream.getTracks()) || []) t.stop();
    try { ctx && ctx.close(); } catch (_) { /* closed */ }
    ctx = stream = node = null;
    set("off", why);
  }

  return {
    start, close,
    active: () => state !== "off",
    state: () => state,
    // the answer as it streams: words (complete sentences are read at once), a tool step (what came before it was a
    // lead-in), the end (with the whole text when no words streamed: the template and fallback paths)
    say: (text) => { if (turn > stopped && text) { said = true; send({type: "say", turn, text}); } },
    drop: () => { if (turn > stopped) send({type: "drop", turn}); },
    end: (text) => { if (turn > stopped) send({type: "say", turn, text: said ? "" : String(text || ""), end: true}); },
    stop: () => { stopped = turn; hush(); send({type: "stop"}); set("listening"); },
  };
}
