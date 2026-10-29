/* The microphone's samples as 20 ms frames of 16-bit PCM at the browser's own rate (docs/VOICE_PLAN.md V-D2): the
   server's VAD resamples. Each frame also carries its loudness, which the panel's orb draws. */
class Capture extends AudioWorkletProcessor {
  constructor() {
    super();
    this.size = Math.round(sampleRate / 50);
    this.buf = new Int16Array(this.size);
    this.at = 0;
    this.sum = 0;
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) {
      const s = Math.max(-1, Math.min(1, ch[i]));
      this.sum += s * s;
      this.buf[this.at++] = s < 0 ? s * 0x8000 : s * 0x7fff;
      if (this.at === this.size) {
        const frame = this.buf.buffer.slice(0);
        this.port.postMessage({frame, level: Math.sqrt(this.sum / this.size)}, [frame]);
        this.at = 0;
        this.sum = 0;
      }
    }
    return true;
  }
}
registerProcessor("mf-capture", Capture);
