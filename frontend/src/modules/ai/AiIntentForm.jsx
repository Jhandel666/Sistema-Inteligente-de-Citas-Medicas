import { useState } from "react";
import { Brain, Mic, Volume2 } from "lucide-react";
import { classifyIntent } from "./aiService";

function AiIntentForm() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);

  const clasificar = async () => {
    if (!text.trim()) {
      alert("Primero escribe o dicta una solicitud.");
      return;
    }

    try {
      setLoading(true);
      const response = await classifyIntent(text);
      setResult(response);
    } catch (error) {
      alert(
        JSON.stringify(
          error.response?.data || "Error desconocido",
          null,
          2
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const escucharVoz = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Tu navegador no soporta reconocimiento de voz. Usa Google Chrome.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "es-PE";
    recognition.continuous = false;
    recognition.interimResults = false;

    setListening(true);
    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setText(transcript);
      setListening(false);
    };

    recognition.onerror = () => {
      setListening(false);
      alert("No se pudo reconocer la voz. Intenta nuevamente.");
    };

    recognition.onend = () => {
      setListening(false);
    };
  };

  const hablarResultado = () => {
    if (!result) return;

    const mensaje = `La intención detectada es ${result.intent} usando el modelo ${result.model}, con confianza ${result.confidence}`;
    const speech = new SpeechSynthesisUtterance(mensaje);
    speech.lang = "es-PE";
    window.speechSynthesis.speak(speech);
  };

  const modelLabel =
    result?.model === "lstm_deep_learning"
      ? "Deep Learning LSTM"
      : "Reglas de respaldo";

  return (
    <div className="space-y-5">
      <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
        <h4 className="font-bold text-blue-900 flex items-center gap-2">
          <Brain size={20} />
          Asistente inteligente con Machine Learning y Deep Learning
        </h4>

        <p className="text-sm text-blue-800 mt-2">
          Este módulo captura voz, convierte la frase a texto y clasifica la
          intención médica usando un modelo LSTM entrenado con 5000 registros
          sintéticos basados en Pichanaki, Junín.
        </p>
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="w-full border rounded-lg p-3"
        rows="5"
        placeholder="Ejemplo: quiero reservar una cita médica"
      />

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={escucharVoz}
          className={`flex items-center gap-2 px-5 py-3 rounded-lg text-white ${
            listening ? "bg-red-600" : "bg-purple-700"
          }`}
        >
          <Mic size={20} />
          {listening ? "Escuchando..." : "Hablar"}
        </button>

        <button
          type="button"
          onClick={clasificar}
          disabled={loading}
          className="flex items-center gap-2 bg-blue-700 text-white px-5 py-3 rounded-lg"
        >
          <Brain size={20} />
          {loading ? "Clasificando..." : "Clasificar intención"}
        </button>

        {result && (
          <button
            type="button"
            onClick={hablarResultado}
            className="flex items-center gap-2 bg-green-700 text-white px-5 py-3 rounded-lg"
          >
            <Volume2 size={20} />
            Leer resultado
          </button>
        )}
      </div>

      {result && (
        <div className="mt-4 bg-white border border-gray-200 p-5 rounded-xl shadow">
          <h4 className="font-bold text-gray-800 mb-3">
            Resultado del modelo inteligente
          </h4>

          <p>
            <strong>Texto analizado:</strong> {text}
          </p>

          <p>
            <strong>Intención detectada:</strong> {result.intent}
          </p>

          <p>
            <strong>Confianza:</strong> {result.confidence}
          </p>

          <p>
            <strong>Modelo usado:</strong>{" "}
            <span
              className={`font-bold ${
                result.model === "lstm_deep_learning"
                  ? "text-green-700"
                  : "text-orange-600"
              }`}
            >
              {modelLabel}
            </span>
          </p>

          <div className="mt-4 h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-700"
              style={{
                width: `${Number(result.confidence) * 100}%`,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default AiIntentForm;