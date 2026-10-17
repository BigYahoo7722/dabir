import os, subprocess, sys, tempfile, numpy as np
sys.path.insert(0, ".")
import process as p
d = tempfile.mkdtemp()
t = np.linspace(0, 3, 3 * 44100, endpoint=False)
sig = (0.3 * np.sin(2 * np.pi * 220 * t) * (np.sin(2 * np.pi * 3 * t) > 0) + 0.05 * np.random.randn(len(t))).astype("float32")
import soundfile as sf; sf.write(d + "/a.wav", sig, 44100)
for ext, codec in (("mp3", "libmp3lame"), ("m4a", "aac"), ("ogg", "libvorbis"), ("flac", "flac")):
    f = f"{d}/audio.{ext}"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", d + "/a.wav", "-c:a", codec, f], check=True)
    dur = p.decode(f, f"{d}/o_{ext}.wav"); assert 2.5 < dur < 3.6, (ext, dur); print("decode ok", ext, round(dur, 2))
w = []; p.denoise(f"{d}/o_mp3.wav", w); assert not w, w; print("denoise ok")
os.rename(f"{d}/audio.mp3", f"{d}/audio.bin"); assert p.decode(f"{d}/audio.bin", d + "/x.wav") > 2; print("wrong-extension ok")
open(d + "/bad.mp3", "wb").write(b"xx" * 500)
try: p.decode(d + "/bad.mp3", d + "/y.wav"); raise SystemExit("bad file accepted")
except ValueError as e: print("corrupt rejected ok")
assert p.fmt(p.clean([{"text": " a", "speaker": 1}, {"text": "b", "speaker": 1}, {"text": "c", "speaker": 2}])) == "[گوینده 1] a b\n[گوینده 2] c"
print("ALL OK")
