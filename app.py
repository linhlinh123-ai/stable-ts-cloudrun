from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import PlainTextResponse, JSONResponse
import os, tempfile, torch

# Giới hạn thread CPU cho Cloud Run
torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))

MODEL_NAME = os.getenv("WHISPER_MODEL", "small")  # small | medium
LANG_DEFAULT = os.getenv("LANG_DEFAULT", "vi")

app = FastAPI()

# ---- Lazy load stable-ts model ----
model = None
def get_model():
    global model
    if model is None:
        import stable_whisper as whisper
        model = whisper.load_model(MODEL_NAME)
    return model
# -----------------------------------

def segments_to_words(result):
    words = []
    for seg in result.segments:
        if getattr(seg, "words", None):
            for w in seg.words or []:
                if not w or not getattr(w, "word", None):
                    continue
                words.append({
                    "text": (w.word or "").strip(),
                    "start": float(getattr(w, "start", seg.start)),
                    "end": float(getattr(w, "end", seg.end)),
                })
        else:
            words.append({
                "text": (seg.text or "").strip(),
                "start": float(seg.start),
                "end": float(seg.end),
            })
    return words

def to_srt(segs):
    def fmt(t):
        ms = round((t - int(t)) * 1000)
        s = int(t) % 60
        m = (int(t) // 60) % 60
        h = int(t) // 3600
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    out = []
    for i, s in enumerate(segs, 1):
        out += [str(i), f"{fmt(s['start'])} --> {fmt(s['end'])}", s["text"], ""]
    return "\n".join(out)

@app.get("/healthz")
def health():
    # Không đụng tới model để server trả lời nhanh
    return {"ok": True, "model_env": MODEL_NAME}

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form(LANG_DEFAULT),
    use_vad: int = Form(1),
    word_timestamps: int = Form(1),
    output: str = Form("words")  # words | segments | srt
):
    # Lúc này mới load model nếu chưa có
    whisper_model = get_model()

    # Lưu file upload vào /tmp
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        path = tmp.name

    # Gọi stable-ts
    result = whisper_model.transcribe(
        path,
        language=language,
        vad=bool(use_vad),
        word_timestamps=bool(word_timestamps),
    )

    if output == "segments":
        segs = [{
            "text": (s.text or "").strip(),
            "start": float(s.start),
            "end": float(s.end),
        } for s in result.segments]
        return JSONResponse({"segments": segs})

    if output == "srt":
        segs = [{
            "text": (s.text or "").strip(),
            "start": float(s.start),
            "end": float(s.end),
        } for s in result.segments]
        return PlainTextResponse(to_srt(segs), media_type="text/plain")

    # Mặc định trả word-level
    return JSONResponse({"words": segments_to_words(result)})
