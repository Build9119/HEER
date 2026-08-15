#!/usr/bin/env python3
"""voice.py — text-to-speech (speak) and speech-to-text (listen) for HEER.

Stdlib only (optional edge-tts for free neural voices). Three layers,
highest fidelity first:

  speak(text):
    1. ElevenLabs TTS if ELEVENLABS_API_KEY is set  -> audio/mpeg
    2. Edge TTS (free, no key) if edge-tts installed -> audio/mpeg
    3. macOS `say` system voice                      -> audio/wav

  transcribe(audio_bytes, mime):
    1. An OpenAI-compatible /audio/transcriptions endpoint, configured via
       ASR_API_URL (+ optional ASR_API_KEY / ASR_MODEL).
    2. macOS Speech framework (offline, zero-config) — builds agent/asr_swift.swift.
    Returns None when everything unavailable or on failure.

Run:  python3 -m agent.voice "hello there"
      python3 -m agent.voice --listen /tmp/clip.webm
"""

import json
import os
import shutil
import ssl
import struct
import subprocess
import sys
import tempfile
import urllib.request

from . import data

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVENLABS_MODEL = "eleven_multilingual_v2"
SAY_TIMEOUT = 90  # seconds, long lines of text
EDGE_TTS_MAX_CHARS = 3000  # Edge TTS hard limit per request


# ---------------------------------------------------------------------------
# Capability probes
# ---------------------------------------------------------------------------


def speak_capability():
    """Highest available TTS backend.

    Returns 'elevenlabs' if a key is set, 'edge' if the free edge-tts
    package is installed, 'say' if the macOS voice is available, else 'none'.
    """
    if data.elevenlabs_key():
        return "elevenlabs"
    if _edge_tts_available():
        return "edge"
    if shutil.which("say"):
        return "say"
    return "none"


def asr_configured():
    """True when a remote ASR endpoint is set or the macOS Speech helper is buildable."""
    return bool(data.asr_url()) or _asr_swift_bin() is not None


def prebuild_asr():
    """Build the offline macOS Speech helper at startup (no-op when unavailable).

    Compiling once at server start avoids a multi-second delay on the first
    /api/listen request and surfaces build errors in the startup log.
    """
    if sys.platform != "darwin":
        return None
    bin_path = _asr_swift_bin()
    if bin_path:
        print(f"[voice] asr_swift ready: {bin_path}")
    else:
        print("[voice] asr_swift unavailable (swiftc or source missing)")
    return bin_path


# ---------------------------------------------------------------------------
# Speak (TTS)
# ---------------------------------------------------------------------------


def speak(text, voice_id=None):
    """Return (audio_bytes, content_type) or (None, None) on failure.

    Priority: ElevenLabs (if key set) -> Edge TTS (free) -> macOS `say`.
    """
    text = (text or "").strip()
    if not text:
        return None, None
    if data.elevenlabs_key():
        audio = _speak_elevenlabs(text, voice_id or data.elevenlabs_voice_id())
        if audio:
            return audio, "audio/mpeg"
    audio = _speak_edge(text)
    if audio:
        return audio, "audio/mpeg"
    return _speak_say(text)


def _ssl_context():
    """SSL context using certifi's CA bundle (fixes macOS Python cert issues)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _edge_tts_available():
    """True when the free edge-tts package is installed."""
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


def _speak_edge(text):
    """Free Microsoft Edge neural TTS. Returns MP3 bytes or None on failure."""
    if not _edge_tts_available():
        return None
    try:
        import asyncio
        import edge_tts

        chunks = []

        async def _stream():
            communicate = edge_tts.Communicate(text[:EDGE_TTS_MAX_CHARS], data.edge_tts_voice())
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])

        asyncio.run(_stream())
        audio = b"".join(chunks)
        if not audio:
            return None
        return audio
    except Exception as exc:
        print(f"[voice] Edge TTS failed ({exc}); falling back to 'say'")
        return None


def _speak_elevenlabs(text, voice_id):
    body = json.dumps({
        "text": text,
        "model_id": ELEVENLABS_MODEL,
    }).encode("utf-8")
    req = urllib.request.Request(
        ELEVENLABS_TTS_URL.format(voice_id=voice_id),
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
            "xi-api-key": data.elevenlabs_key(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60, context=_ssl_context()) as resp:
            return resp.read()
    except Exception as exc:
        print(f"[voice] ElevenLabs TTS failed ({exc}); falling back to 'say'")
        return None


def _speak_say(text):
    """macOS `say` -> WAV. Handles old `say` builds that only write AIFF."""
    if not shutil.which("say"):
        return None, None
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    def _run(cmd):
        try:
            subprocess.run(cmd, capture_output=True, timeout=SAY_TIMEOUT)
        except Exception:
            pass

    try:
        base = ["say", "-o", tmp_path, "--data-format=LEI16@22050"]
        if text.startswith("-"):
            base.append("--")
        _run(base + [text])
        produced = os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 44
        if not produced:
            _run(base + ["--file-format=WAVE", text])
            produced = os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 44
        if produced:
            with open(tmp_path, "rb") as f:
                return f.read(), "audio/wav"

        # Last resort: AIFF + hand-rolled conversion.
        aiff_path = tmp_path + ".aiff"
        try:
            _run(["say", "-o", aiff_path, text])
            if not os.path.exists(aiff_path):
                return None, None
            with open(aiff_path, "rb") as f:
                wav = _aiff_to_wav(f.read())
            return (wav, "audio/wav") if wav else (None, None)
        finally:
            if os.path.exists(aiff_path):
                os.unlink(aiff_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _aiff_to_wav(raw):
    """Minimal AIFF (big-endian PCM) -> WAV (little-endian PCM) converter."""
    if len(raw) < 12 or raw[:4] != b"FORM" or raw[8:12] != b"AIFF":
        return None
    channels = 1
    rate = 22050
    bits = 16
    samples = b""
    offset = 12
    while offset + 8 <= len(raw):
        cid = raw[offset:offset + 4]
        size = struct.unpack(">I", raw[offset + 4:offset + 8])[0]
        body = raw[offset + 8:offset + 8 + size]
        if cid == b"COMM" and len(body) >= 18:
            channels = struct.unpack(">h", body[0:2])[0] or 1
            bits = struct.unpack(">h", body[6:8])[0] or 16
            exp = struct.unpack(">H", body[8:10])[0]
            mant = int.from_bytes(body[10:18], "big")
            if exp:
                rate = int(mant / (2 ** 63) * (2 ** (exp - 16383)))
        elif cid == b"SSND" and len(body) >= 4:
            skip = struct.unpack(">I", body[0:4])[0]
            samples = body[4 + skip:]
        offset += 8 + size + (size % 2)
    if not samples:
        return None

    if bits == 16:
        n = len(samples) - (len(samples) % 2)
        n_samp = n // 2
        if n_samp == 0:
            return None
        pcm = struct.pack("<%dh" % n_samp, *struct.unpack(">%dh" % n_samp, samples[:n]))
    else:
        # 8-bit AIFF and WAV are both unsigned — pass through.
        pcm = samples

    byte_rate = rate * channels * bits // 8
    hdr = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    hdr += b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, rate, byte_rate, channels * bits // 8, bits)
    hdr += b"data" + struct.pack("<I", len(pcm))
    return hdr + pcm


# ---------------------------------------------------------------------------
# Listen (ASR)
# ---------------------------------------------------------------------------


def transcribe(audio_bytes, mime="audio/webm"):
    """Transcribe speech audio. Remote OpenAI-compatible endpoint first,
    then the offline macOS Speech helper. Returns the transcript string,
    or None if no backend succeeded.
    """
    text = _transcribe_remote(audio_bytes, mime)
    if text:
        return text
    return _transcribe_macos(audio_bytes, mime)


# -- Remote (OpenAI-compatible /audio/transcriptions) ------------------------


def _transcribe_remote(audio_bytes, mime="audio/webm"):
    url = data.asr_url()
    if not url:
        return None
    model = data.asr_model()
    key = data.asr_key()

    boundary = "----HeerBoundary" + os.urandom(8).hex()
    chunks = []
    chunks.append(
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="model"\r\n\r\n' +
        model.encode() + b"\r\n"
    )
    chunks.append(
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="audio"\r\n'
        b"Content-Type: " + (mime or "application/octet-stream").encode() + b"\r\n\r\n"
        + audio_bytes + b"\r\n"
    )
    chunks.append(b"--" + boundary.encode() + b"--\r\n")
    body = b"".join(chunks)

    headers = {
        "Content-Type": "multipart/form-data; boundary=" + boundary,
        "User-Agent": "heer/1.0",
    }
    if key:
        headers["Authorization"] = "Bearer " + key

    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            text = (payload.get("text") or "").strip()
            return text or None
    except Exception as exc:
        print(f"[voice] remote ASR failed: {exc}")
        return None


# -- Local (macOS Speech framework) ------------------------------------------

ASR_TMP_ROOT = os.path.join(tempfile.gettempdir(), "heer_asr")


def _asr_swift_src():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "asr_swift.swift")


def _asr_swift_plist():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "asr_swift.plist")


def _asr_swift_bin():
    """Path to the compiled asr_swift helper, building it on first use.

    The Speech framework requires NSSpeechRecognitionUsageDescription in a
    proper Info.plist. A bare command-line binary crashes (SIGABRT) inside
    SFSpeechRecognizer.requestAuthorization because TCC can't bind the plist,
    so we build a minimal .app bundle:

        heer_asr.app/Contents/MacOS/asr_swift   (the binary)
        heer_asr.app/Contents/Info.plist        (usage description)

    and ad-hoc codesign the bundle so macOS trusts it for the permission.
    """
    swiftc = shutil.which("swiftc")
    if not swiftc or not os.path.exists(_asr_swift_src()):
        return None
    try:
        os.makedirs(ASR_TMP_ROOT, exist_ok=True)
    except OSError:
        return None

    app_dir = os.path.join(ASR_TMP_ROOT, "heer_asr.app")
    macos_dir = os.path.join(app_dir, "Contents", "MacOS")
    bin_path = os.path.join(macos_dir, "asr_swift")
    plist_dst = os.path.join(app_dir, "Contents", "Info.plist")

    if os.path.exists(bin_path) and os.access(bin_path, os.X_OK):
        return bin_path

    try:
        os.makedirs(macos_dir, exist_ok=True)
        # Embed the Info.plist into the binary's __TEXT,__info_plist section.
        # TCC reads the usage description from the embedded plist even when the
        # binary is run directly from the terminal (not via LaunchServices),
        # which prevents the SIGABRT crash on SFSpeechRecognizer.requestAuthorization.
        cmd = [
            swiftc, "-O", _asr_swift_src(), "-o", bin_path,
            "-Xlinker", "-sectcreate", "-Xlinker", "__TEXT",
            "-Xlinker", "__info_plist", "-Xlinker", _asr_swift_plist(),
        ]
        subprocess.run(cmd, capture_output=True, timeout=120, check=True)

        # Copy the plist into the bundle (TCC reads it from here).
        if os.path.exists(_asr_swift_plist()):
            shutil.copyfile(_asr_swift_plist(), plist_dst)

        # Ad-hoc sign the bundle so the Speech framework trusts it.
        subprocess.run(
            ["codesign", "--force", "--sign", "-", app_dir],
            capture_output=True, timeout=60, check=True,
        )
        return bin_path
    except Exception as exc:
        print(f"[voice] could not build asr_swift: {exc}")
        return None


def _to_wav_ffmpeg(src, dst):
    """Transcode any audio to 16-bit mono PCM WAV using ffmpeg (if present)."""
    try:
        subprocess.run(
            ["ffmpeg", "-nostdin", "-y", "-i", src,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", dst],
            capture_output=True, timeout=120, check=True,
        )
        return os.path.exists(dst) and os.path.getsize(dst) > 44
    except Exception as exc:
        print(f"[voice] ffmpeg transcode failed: {exc}")
        return False


def _transcribe_macos(audio_bytes, mime="audio/webm"):
    """Offline transcription via Apple Speech framework (macOS only)."""
    if sys.platform != "darwin":
        return None
    bin_path = _asr_swift_bin()
    if not bin_path:
        return None

    with tempfile.TemporaryDirectory(prefix="heer_asr_") as tmp:
        src = os.path.join(tmp, "input" + _ext_for_mime(mime))
        with open(src, "wb") as f:
            f.write(audio_bytes)

        wav = os.path.join(tmp, "input.wav")
        # SFSpeechURLRecognitionRequest wants PCM WAV — transcode webm/ogg/mp3.
        if mime in ("audio/wav", "audio/x-wav"):
            wav = src
        elif not _to_wav_ffmpeg(src, wav):
            print("[voice] speech-to-text needs a WAV input; ffmpeg unavailable")
            return None

        # Launch via LaunchServices so TCC resolves the .app bundle as the
        # responsible process for the Speech framework permission. Running the
        # bare binary directly crashes with __TCC_CRASHING_DUE_TO_PRIVACY_VIOLATION__
        # because TCC cannot attribute the request to a bundle.
        out_json = os.path.join(tmp, "result.json")
        app_dir = os.path.join(ASR_TMP_ROOT, "heer_asr.app")
        try:
            proc = subprocess.run(
                ["open", "-W", "-n", app_dir, "--args", wav, out_json],
                capture_output=True, timeout=200,
            )
        except Exception as exc:
            print(f"[voice] asr_swift failed to launch: {exc}")
            return None

        if not os.path.exists(out_json):
            print(f"[voice] asr_swift produced no result (exit {proc.returncode})")
            return None
        try:
            with open(out_json, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            print(f"[voice] asr_swift bad output file: {out_json!r}")
            return None
        if "error" in payload:
            print(f"[voice] asr_swift: {payload['error']}")
            return None
        text = (payload.get("text") or "").strip()
        return text or None


def _ext_for_mime(mime):
    return {
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/ogg": ".ogg",
        "audio/webm": ".webm",
        "audio/flac": ".flac",
    }.get(mime, ".bin")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m agent.voice <text>  (speak)")
        print("       python3 -m agent.voice --listen <file>  (transcribe)")
        return
    if sys.argv[1] == "--listen" and len(sys.argv) >= 3:
        with open(sys.argv[2], "rb") as f:
            print(json.dumps({"text": transcribe(f.read())}, ensure_ascii=False))
        return
    audio, ctype = speak(" ".join(sys.argv[1:]))
    if audio is None:
        print("No TTS available (set ELEVENLABS_API_KEY).")
        return
    out = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
    out.write(audio)
    out.close()
    print(f"Wrote {len(audio)} bytes ({ctype}) -> {out.name}")


if __name__ == "__main__":
    main()
