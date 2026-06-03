import tempfile
from pathlib import Path


class STTService:
    _model = None
    _model_name = "base"

    def _get_model(self):
        if STTService._model is None:
            from faster_whisper import WhisperModel
            model_path = str(Path(__file__).resolve().parent.parent / "models" / "whisper")
            STTService._model = WhisperModel(
                self._model_name,
                device="cpu",
                compute_type="int8",
                download_root=model_path,
            )
        return STTService._model

    def transcribe(self, audio_bytes: bytes, suffix: str = ".webm", lang: str = "es") -> str:
        model = self._get_model()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            segments, info = model.transcribe(tmp_path, language=lang, beam_size=5)
            parts = []
            for seg in segments:
                if seg.avg_logprob > -1.0 and seg.no_speech_prob < 0.6:
                    parts.append(seg.text.strip())
            result = " ".join(parts) if parts else ""
            return result
        finally:
            Path(tmp_path).unlink(missing_ok=True)
