import { useState } from "react";
import { ChevronDown, ChevronUp, Eye } from "lucide-react";
import PageCard from "../components/ui/PageCard";
import AiIntentForm from "../modules/ai/AiIntentForm";
import NeuralNetworkViz from "../modules/ai/NeuralNetworkViz";

function AiVoicePage() {
  const [showViz, setShowViz] = useState(false);

  return (
    <div className="space-y-6">
      <PageCard title="Asistente IA por Voz">
        <AiIntentForm />
      </PageCard>

      <div className="bg-white border border-gray-200 rounded-xl shadow overflow-hidden">
        <button
          onClick={() => setShowViz(!showViz)}
          className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Eye size={22} className="text-purple-600" />
            <div className="text-left">
              <h3 className="font-bold text-gray-800">Visualización de la Red Neuronal (Deep Learning)</h3>
              <p className="text-sm text-gray-500">
                Arquitectura LSTM — capas, neuronas, activaciones, pesos y sesgos
              </p>
            </div>
          </div>
          {showViz ? <ChevronUp size={22} className="text-gray-400" /> : <ChevronDown size={22} className="text-gray-400" />}
        </button>

        {showViz && (
          <div className="border-t border-gray-200">
            <NeuralNetworkViz />
          </div>
        )}
      </div>
    </div>
  );
}

export default AiVoicePage;