import { useCallback, useRef, useState } from "react";

const WAKE_WORDS = [
  "ey eva",
  "hey eva",
  "eva salud",
  "asistente eva",
  "la ia",
  "asistente la ia",
  "ey la ia",
  "hey la ia",
];

function isWake(text = "") {
  const t = String(text || "").toLowerCase();
  return WAKE_WORDS.some((word) => t.includes(word));
}

function getSpeechRecognition() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function safeStop(recognition) {
  if (!recognition) return;
  try {
    recognition.onresult = null;
    recognition.onend = null;
    recognition.onerror = null;
    recognition.stop();
  } catch (_) {
    try { recognition.abort?.(); } catch (_) {}
  }
}

export function useLaIAVoice({
  log,
  onCommand,
  ttsEnabled = true,
  disabledRef,
  setView,
  setResponse,
  setBrowserError,
  onReactivate,
}) {
  const [state, setState] = useState("idle");

  const wakeRecognitionRef = useRef(null);
  const commandRecognitionRef = useRef(null);
  const voiceRef = useRef(null);
  const mountedRef = useRef(true);
  const fullRef = useRef(false);
  const wokeRef = useRef(false);
  const wakeCountRef = useRef(0);
  const warnShownRef = useRef(false);
  const wakeRestartTimerRef = useRef(null);
  const commandSilenceTimerRef = useRef(null);
  const startingWakeRef = useRef(false);

  const clearTimers = useCallback(() => {
    clearTimeout(wakeRestartTimerRef.current);
    clearTimeout(commandSilenceTimerRef.current);
    wakeRestartTimerRef.current = null;
    commandSilenceTimerRef.current = null;
  }, []);

  const stopWake = useCallback(() => {
    clearTimeout(wakeRestartTimerRef.current);
    wakeRestartTimerRef.current = null;
    safeStop(wakeRecognitionRef.current);
    wakeRecognitionRef.current = null;
    startingWakeRef.current = false;
  }, []);

  const stopCommand = useCallback(() => {
    clearTimeout(commandSilenceTimerRef.current);
    commandSilenceTimerRef.current = null;
    safeStop(commandRecognitionRef.current);
    commandRecognitionRef.current = null;
  }, []);

  const stopAll = useCallback(() => {
    clearTimers();
    stopWake();
    stopCommand();
    window.speechSynthesis?.cancel();
    setState("idle");
  }, [clearTimers, stopCommand, stopWake]);

  const speak = useCallback((text, onDone) => {
    if (!ttsEnabled || disabledRef?.current) {
      setTimeout(() => onDone?.(), 100);
      return;
    }

    const clean = String(text || "")
      .replace(/\*+/g, "")
      .replace(/\n/g, ". ")
      .replace(/\s+/g, " ")
      .trim();

    window.speechSynthesis?.cancel();

    if (!clean) {
      setTimeout(() => onDone?.(), 100);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = "es-PE";
    utterance.rate = 1.1;
    utterance.pitch = 1.0;
    if (voiceRef.current) utterance.voice = voiceRef.current;

    utterance.onstart = () => {
      log?.("tts");
      setState("speaking");
    };

    utterance.onend = () => {
      log?.("tts end");
      setState("idle");
      setTimeout(() => onDone?.(), 250);
    };

    utterance.onerror = () => {
      setState("idle");
      setTimeout(() => onDone?.(), 100);
    };

    window.speechSynthesis?.speak(utterance);
  }, [disabledRef, log, ttsEnabled]);

  const setVoiceGender = useCallback((gender) => {
    const select = () => {
      const voices = window.speechSynthesis?.getVoices?.() || [];
      if (!voices.length) {
        window.speechSynthesis?.addEventListener?.("voiceschanged", select, { once: true });
        return;
      }

      if (gender === "female") {
        voiceRef.current = voices.find((v) => /helena|sabina|zira|google español/i.test(v.name))
          || voices.find((v) => /female|mujer/i.test(v.name))
          || voices.find((v) => String(v.lang || "").startsWith("es"))
          || null;
        log?.(`voz femenina: ${voiceRef.current?.name || "ninguna disponible"}`);
      } else {
        voiceRef.current = null;
        log?.("voz masculina/default");
      }
    };

    select();
  }, [log]);

  const startWake = useCallback(() => {
    mountedRef.current = true;

    if (!mountedRef.current || startingWakeRef.current) return;
    if (wakeRecognitionRef.current) return;
    if (fullRef.current) return;

    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) {
      log?.("SpeechRecognition NO disponible");
      if (!warnShownRef.current) {
        warnShownRef.current = true;
        setBrowserError?.("Tu navegador no soporta reconocimiento de voz. Usa Chrome.");
      }
      return;
    }

    startingWakeRef.current = true;
    const recognition = new SpeechRecognition();
    recognition.lang = "es-PE";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript.toLowerCase().trim();
        log?.(`oyó: "${text}"`);

        if (disabledRef?.current) {
          if (isWake(text) && !wokeRef.current) {
            wokeRef.current = true;
            stopWake();
            onReactivate?.();
            wakeRestartTimerRef.current = setTimeout(() => {
              wokeRef.current = false;
              startWake();
            }, 700);
          }
          continue;
        }

        if (isWake(text) && !wokeRef.current) {
          wokeRef.current = true;
          wakeCountRef.current += 1;
          fullRef.current = true;
          log?.(`WAKE #${wakeCountRef.current}: "${text}"`);
          stopWake();

          setView?.("mini");
          setState("greeting");
          const msg = "¡Hola Admin! Soy La IA. ¿En qué puedo ayudarte?";
          setResponse?.(msg);
          speak(msg, () => startCommandListen());
          return;
        }
      }
    };

    recognition.onend = () => {
      const shouldRestart = mountedRef.current && !fullRef.current && !disabledRef?.current;
      wakeRecognitionRef.current = null;
      startingWakeRef.current = false;
      if (shouldRestart) {
        wakeRestartTimerRef.current = setTimeout(() => startWake(), 900);
      }
    };

    recognition.onerror = (event) => {
      wakeRecognitionRef.current = null;
      startingWakeRef.current = false;
      const err = event?.error || "desconocido";
      log?.(`wake error: ${err}`);
      if (mountedRef.current && !fullRef.current && !disabledRef?.current && err !== "aborted") {
        wakeRestartTimerRef.current = setTimeout(() => startWake(), 1200);
      }
    };

    wakeRecognitionRef.current = recognition;
    try {
      recognition.start();
      log?.("wake iniciado");
    } catch (e) {
      wakeRecognitionRef.current = null;
      startingWakeRef.current = false;
      log?.(`wake start err: ${e.message}`);
    }
  }, [disabledRef, log, onReactivate, setBrowserError, setResponse, setView, speak, stopWake]);

  const startCommandListen = useCallback(() => {
    mountedRef.current = true;
    if (!mountedRef.current || disabledRef?.current) return;
    if (commandRecognitionRef.current) return;

    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) return;

    stopWake();
    setState("listening");

    const recognition = new SpeechRecognition();
    recognition.lang = "es-PE";
    recognition.continuous = true;
    recognition.interimResults = true;

    let accumulated = "";
    const SILENCE_MS = 1400;

    recognition.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          accumulated += ` ${event.results[i][0].transcript.trim()}`;
        }
      }

      clearTimeout(commandSilenceTimerRef.current);
      commandSilenceTimerRef.current = setTimeout(() => {
        try { recognition.stop(); } catch (_) {}
      }, SILENCE_MS);
    };

    recognition.onend = () => {
      clearTimeout(commandSilenceTimerRef.current);
      commandSilenceTimerRef.current = null;
      commandRecognitionRef.current = null;

      const text = accumulated.trim();
      accumulated = "";

      if (text) {
        log?.(`cmd: "${text.slice(0, 80)}" (${text.length} chars)`);
        onCommand?.(text);
      } else {
        setState("idle");
        if (fullRef.current && mountedRef.current && !disabledRef?.current) {
          commandSilenceTimerRef.current = setTimeout(() => startCommandListen(), 500);
        }
      }
    };

    recognition.onerror = (event) => {
      commandRecognitionRef.current = null;
      const err = event?.error || "desconocido";
      log?.(`cmd error: ${err}`);
      setState("idle");
    };

    commandRecognitionRef.current = recognition;
    try {
      recognition.start();
    } catch (e) {
      commandRecognitionRef.current = null;
      log?.(`cmd start err: ${e.message}`);
      setState("idle");
    }
  }, [disabledRef, log, onCommand, startWake, stopWake]);

  const resetWakeState = useCallback(() => {
    fullRef.current = false;
    wokeRef.current = false;
  }, []);

  const destroy = useCallback(() => {
    mountedRef.current = false;
    stopAll();
  }, [stopAll]);

  return {
    state,
    setState,
    speak,
    setVoiceGender,
    startWake,
    startCommandListen,
    stopAll,
    resetWakeState,
    destroy,
    fullRef,
    wokeRef,
    wakeRecognitionRef,
    commandRecognitionRef,
    voiceRef,
  };
}
