"""STT: one utterance in, its transcript out, over the KServe v2 binary protocol (`http:stt`).

Lifted from the callbot (educa-reminder-agent `src/call/stt/ops.py` `STTOp`, staging 229ba89), unchanged except the
imports. The embedding output is the callbot's noise gate's; `need_embedding: false` on `http:stt` skips it here.
"""

from __future__ import annotations

import json
import struct
from typing import Any, Dict, Optional

import numpy as np
from operonx.core.loggings import LOGGER
from operonx.core.ops.base import BaseOp
from operonx.core.utils.common import Param
from operonx.providers.ops._utils import resolve_hub

from voice import _endpoints  # noqa: F401 — registers the `http:` resource category
from voice._wav import speech_samples


class STTOp(BaseOp):
    """STT over the KServe v2 REST gateway. Stateless per call (bound=io); `resource` is an `http:` entry in
    resources.yaml, resolved on first use (the graph is built before `operonx.bootstrap()` runs)."""

    type = "code"
    bound = "io"

    show_keys_default = ("transcript",)

    def __init__(
        self,
        resource: str = "stt",
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        kwargs.setdefault("bound", "io")
        super().__init__(**kwargs)
        self.resource = resource
        self._ep = None
        self._initialized = False

        parsed_inputs = {
            "speech_audio": Param(required=True),
        }
        parsed_outputs = {
            "transcript": Param(type=str),
            "embedding": Param(),
        }
        self.inputs = self._merge_params(parsed_inputs, self._normalize_params(inputs))
        self.outputs = self._merge_params(parsed_outputs, self._normalize_params(outputs))

        self._set_core(self._process)

    def warmup(self) -> None:
        """Resolve the endpoint at engine startup, not on the first call."""
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        """One hub lookup per op, then the infer URL and the tensor names, once."""
        if self._initialized:
            return
        ep = resolve_hub().get(f"http:{self.resource}")
        if ep is None:
            raise RuntimeError(f"http:{self.resource} is not declared in resources.yaml")
        self._ep = ep
        model = ep.opt("model", "fastconformer_asr")
        version = str(ep.opt("version", "") or "").strip()
        base = ep.url
        self._infer_url = (
            f"{base}/v2/models/{model}/versions/{version}/infer" if version else f"{base}/v2/models/{model}/infer"
        )
        # This gateway wants the header lower-cased.
        self._headers = {k.lower(): v for k, v in ep.headers.items()}
        self._text_name = ep.opt("output_text_name", "TRANSCRIPT")
        self._emb_name = ep.opt("output_emb_name", "EMBEDDING")
        self._audio_name = ep.opt("audio_input_name", "AUDIO_SIGNAL")
        self._need_embedding = ep.flag("need_embedding", True)
        self._initialized = True

    @staticmethod
    def _decode_transcript(out: Dict[str, Any]) -> str:
        """The transcript from one KServe v2 BYTES output in JSON form (no base64 guessing)."""
        data = out.get("data")
        if not data:
            return ""
        val = data[0] if isinstance(data, list) else data
        if isinstance(val, (bytes, bytearray)):
            return val.decode("utf-8", errors="replace").strip()
        if isinstance(val, str):
            return val.strip()
        return str(val).strip()

    @staticmethod
    def _parse_embedding(out: Dict[str, Any]) -> Optional[np.ndarray]:
        """The FP32 (D, T) embedding from one KServe v2 output in JSON form."""
        data = out.get("data")
        shape = out.get("shape")
        if not data or not shape:
            return None
        try:
            arr = np.asarray(data, dtype=np.float32).reshape(shape)
        except Exception as e:
            LOGGER.error("[stt] embedding reshape failed shape=%s: %s", shape, e)
            return None
        return np.squeeze(arr)

    def _parse_binary_response(self, content: bytes, header_len: int) -> Dict[str, Any]:
        """The outputs of a binary KServe v2 reply: a JSON header, then each output's bytes in order (BYTES:
        a 4-byte little-endian length + utf-8). A plain JSON reply falls back to `data`."""
        hdr = json.loads(content[:header_len]) if header_len else json.loads(content)
        out: Dict[str, Any] = {"transcript": "", "embedding": None}
        offset = header_len
        for o in hdr.get("outputs", []):
            size = int((o.get("parameters") or {}).get("binary_data_size") or 0)
            chunk = content[offset : offset + size]
            offset += size
            if o.get("name") == self._text_name:
                if size >= 4:
                    (n,) = struct.unpack_from("<I", chunk, 0)
                    out["transcript"] = chunk[4 : 4 + n].decode("utf-8", errors="replace").strip()
                else:
                    out["transcript"] = self._decode_transcript(o)
            elif o.get("name") == self._emb_name:
                if size:
                    arr = np.frombuffer(chunk, dtype="<f4").reshape(o["shape"])
                    out["embedding"] = np.squeeze(arr)
                else:
                    out["embedding"] = self._parse_embedding(o)
        return out

    async def _process(self, speech_audio):
        self._ensure_initialized()
        audio = speech_samples(speech_audio)
        if audio.size == 0:
            yield {"transcript": "", "embedding": None}
            return

        # Binary (KServe v2 binary extension), not a JSON list: same result, ~4x faster, no event-loop stall.
        raw = np.ascontiguousarray(audio, dtype="<f4").tobytes()
        req_outputs = [{"name": self._text_name, "parameters": {"binary_data": True}}]
        if self._need_embedding:
            req_outputs.append({"name": self._emb_name, "parameters": {"binary_data": True}})
        header = json.dumps(
            {
                "inputs": [
                    {
                        "name": self._audio_name,
                        "shape": [1, int(audio.size)],
                        "datatype": "FP32",
                        "parameters": {"binary_data_size": len(raw)},
                    }
                ],
                "outputs": req_outputs,
            }
        ).encode()

        try:
            resp = await self._ep.client.post(
                self._infer_url,
                content=header + raw,
                headers={
                    **self._headers,
                    "content-type": "application/octet-stream",
                    "inference-header-content-length": str(len(header)),
                },
            )
        except Exception as e:
            LOGGER.error("[stt] request failed: %s", e)
            yield {"transcript": "", "embedding": None}
            return

        if resp.status_code != 200:
            LOGGER.error("[stt] http %s: %s", resp.status_code, resp.text[:200])
            yield {"transcript": "", "embedding": None}
            return

        try:
            ihl = int(resp.headers.get("inference-header-content-length", 0))
            parsed = self._parse_binary_response(resp.content, ihl)
        except Exception as e:
            LOGGER.error("[stt] parse response failed: %s", e)
            yield {"transcript": "", "embedding": None}
            return

        yield {"transcript": parsed["transcript"], "embedding": parsed["embedding"]}
