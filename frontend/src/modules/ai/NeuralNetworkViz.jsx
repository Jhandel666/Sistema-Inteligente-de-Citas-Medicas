import { useState } from "react";
import { Brain, Layers, BarChart3, AlertCircle, CheckCircle2 } from "lucide-react";
import modelData from "./model_data.json";

const LAYER_COLORS = {
  embedding: { bar: "#bfdbfe", border: "#3b82f6", text: "#1e3a5f", neuron: "#3b82f6", label: "Entrada" },
  lstm: { bar: "#e9d5ff", border: "#9333ea", text: "#581c87", neuron: "#9333ea", label: "Oculta" },
  dropout: { bar: "#fde68a", border: "#d97706", text: "#78350f", neuron: "#d97706", label: "Regularización" },
  dense: { bar: "#a7f3d0", border: "#10b981", text: "#064e3b", neuron: "#10b981", label: "Oculta" },
  output: { bar: "#fecaca", border: "#ef4444", text: "#7f1d1d", neuron: "#ef4444", label: "Salida" },
};

function NeuronDots({ count, max, cx, cy, r, color }) {
  const shown = Math.min(count, max);
  const spacing = Math.min(16, Math.floor(480 / shown));
  const startX = cx - (shown * spacing) / 2;
  const dots = [];
  for (let i = 0; i < shown; i++) {
    dots.push(
      <circle key={i} cx={startX + i * spacing + 8} cy={cy} r={r} fill={color} opacity={0.9} />
    );
  }
  if (count > max) {
    dots.push(
      <text key="more" x={startX + shown * spacing + 12} y={cy + 4} fontSize={11} fill="#6b7280">
        +{count - max} más
      </text>
    );
  }
  return <g>{dots}</g>;
}

function NeuralNetworkViz() {
  const [tab, setTab] = useState("arch");

  const data = modelData.arquitectura;
  const weightsData = modelData.pesos;
  if (!data) return null;

  const layers = data.layers || [];
  const svgWidth = 860;
  const layerHeight = 65;
  const gap = 18;
  const svgHeight = layers.length * (layerHeight + gap) + gap;
  const neuronCenterX = 380;
  const neuronR = 5;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-xl shadow overflow-hidden">
        <div className="p-5 border-b border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                <Brain size={24} className="text-blue-600" />
                Arquitectura del Modelo de Deep Learning
              </h3>
              <p className="text-gray-500 mt-1">
                {data.modelo} — {data.framework}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setTab("arch")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  tab === "arch"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <Layers size={16} />
                Arquitectura
              </button>
              <button
                onClick={() => setTab("weights")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  tab === "weights"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <BarChart3 size={16} />
                Pesos y Sesgos
              </button>
            </div>
          </div>
        </div>

        {tab === "arch" && (
          <div className="p-5">
            <svg
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full h-auto"
              style={{ maxHeight: 600 }}
            >
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af" />
                </marker>
              </defs>

              {layers.map((layer, i) => {
                const y = gap + i * (layerHeight + gap);
                const colors = LAYER_COLORS[layer.type] || LAYER_COLORS.dense;
                const layerMiddleY = y + layerHeight / 2;
                const neuronCount = typeof layer.neurons === "number" ? layer.neurons : 8;

                return (
                  <g key={i}>
                    {i > 0 && (
                      <line
                        x1={neuronCenterX}
                        y1={gap + (i - 1) * (layerHeight + gap) + layerHeight}
                        x2={neuronCenterX}
                        y2={y}
                        stroke="#9ca3af"
                        strokeWidth={2}
                        strokeDasharray="5,3"
                        markerEnd="url(#arrowhead)"
                      />
                    )}

                    <rect
                      x={40}
                      y={y}
                      width={580}
                      height={layerHeight}
                      rx={10}
                      fill={colors.bar}
                      stroke={colors.border}
                      strokeWidth={1.5}
                      opacity={0.7}
                    />

                    <NeuronDots
                      count={neuronCount}
                      max={28}
                      cx={neuronCenterX}
                      cy={layerMiddleY}
                      r={neuronR}
                      color={colors.neuron}
                    />

                    <text
                      x={640}
                      y={layerMiddleY + 4}
                      fontSize={13}
                      fontWeight="bold"
                      fill={colors.text}
                    >
                      {layer.name}
                    </text>

                    <text
                      x={640}
                      y={layerMiddleY + 20}
                      fontSize={11}
                      fill="#6b7280"
                    >
                      {layer.units} {layer.activation ? `· ${layer.activation.toUpperCase()}` : ""}
                    </text>

                    <text x={16} y={layerMiddleY + 4} fontSize={10} fill="#6b7280" textAnchor="end">
                      {colors.label}
                    </text>
                  </g>
                );
              })}

              {data.modelo_cargado && (
                <text x={svgWidth - 10} y={svgHeight - 6} fontSize={10} fill="#22c55e" textAnchor="end">
                  ● Modelo entrenado — {data.num_clases} clases
                </text>
              )}
            </svg>

            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-3 py-2 font-semibold text-gray-700">#</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-700">Capa</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-700">Tipo</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-700">Neuronas / Unidades</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-700">Activación</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-700">Params entrenables</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-700">Descripción</th>
                  </tr>
                </thead>
                <tbody>
                  {layers.map((layer, i) => {
                    const colors = LAYER_COLORS[layer.type] || LAYER_COLORS.dense;
                    return (
                      <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-3 py-2 text-gray-500">{i + 1}</td>
                        <td className="px-3 py-2 font-medium text-gray-800">{layer.name}</td>
                        <td className="px-3 py-2">
                          <span
                            className="inline-block px-2 py-0.5 rounded text-xs font-semibold"
                            style={{ backgroundColor: colors.bar, color: colors.text }}
                          >
                            {layer.type}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-gray-700">{layer.units}</td>
                        <td className="px-3 py-2 text-gray-700">{layer.activation || "—"}</td>
                        <td className="px-3 py-2 text-gray-700 font-mono text-xs">{layer.params}</td>
                        <td className="px-3 py-2 text-gray-500 text-xs max-w-xs">{layer.description}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-gray-50 rounded-lg px-4 py-3">
                <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider">Optimizador</p>
                <p className="text-lg font-bold text-gray-800 mt-1">{data.optimizador}</p>
              </div>
              <div className="bg-gray-50 rounded-lg px-4 py-3">
                <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider">Función de pérdida</p>
                <p className="text-lg font-bold text-gray-800 mt-1">{data.loss}</p>
              </div>
              <div className="bg-gray-50 rounded-lg px-4 py-3">
                <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider">Params totales</p>
                <p className="text-lg font-bold text-gray-800 mt-1">{data.total_params_estimados}</p>
              </div>
              <div className="bg-gray-50 rounded-lg px-4 py-3">
                <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider">Clases de salida</p>
                <p className="text-lg font-bold text-gray-800 mt-1">{data.num_clases}</p>
              </div>
            </div>

            {data.clases?.length > 0 && (
              <div className="mt-4 bg-gray-50 rounded-lg px-4 py-3">
                <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider mb-2">Clases entrenadas</p>
                <div className="flex flex-wrap gap-2">
                  {data.clases.map((clase) => (
                    <span
                      key={clase}
                      className="inline-flex items-center gap-1 bg-white border border-green-200 text-green-800 px-2.5 py-1 rounded-full text-xs font-medium"
                    >
                      <CheckCircle2 size={12} />
                      {clase}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "weights" && (
          <div className="p-5">
            {weightsData?.modelo_cargado ? (
              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-gray-50 rounded-lg px-4 py-3">
                    <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider">Params entrenables</p>
                    <p className="text-2xl font-bold text-gray-800 mt-1">
                      {weightsData.total_parametros_entrenables?.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg px-4 py-3">
                    <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider">Total Pesos</p>
                    <p className="text-2xl font-bold text-blue-700 mt-1">
                      {weightsData.resumen?.total_pesos?.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg px-4 py-3">
                    <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider">Total Sesgos</p>
                    <p className="text-2xl font-bold text-purple-700 mt-1">
                      {weightsData.resumen?.total_sesgos?.toLocaleString()}
                    </p>
                  </div>
                </div>

                {(weightsData.pesos_por_capa || []).map((capa, ci) => (
                  <div key={ci} className="border border-gray-200 rounded-xl overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <h5 className="font-bold text-gray-800">
                        Capa {capa.layer_index + 1}: {capa.layer_name}
                      </h5>
                    </div>
                    <div className="p-4 space-y-4">
                      {capa.weights.length > 0 && (
                        <div>
                          <h6 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-2">
                            <span className="w-2 h-2 bg-blue-500 rounded-full" />
                            Pesos
                          </h6>
                          <div className="grid gap-3">
                            {capa.weights.map((w, wi) => (
                              <div key={wi} className="bg-blue-50 rounded-lg p-3 text-sm">
                                <div className="flex flex-wrap gap-x-6 gap-y-1 mb-2">
                                  <span className="text-gray-600">
                                    Shape: <span className="font-mono font-bold text-gray-800">{JSON.stringify(w.shape)}</span>
                                  </span>
                                  <span className="text-gray-600">
                                    Elementos: <span className="font-bold text-gray-800">{w.size?.toLocaleString()}</span>
                                  </span>
                                </div>
                                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                                  <span>Media: <span className="font-mono font-bold">{w.mean}</span></span>
                                  <span>Std: <span className="font-mono font-bold">{w.std}</span></span>
                                  <span>Min: <span className="font-mono font-bold">{w.min}</span></span>
                                  <span>Max: <span className="font-mono font-bold">{w.max}</span></span>
                                </div>
                                {w.sample_values && (
                                  <div className="mt-2">
                                    <span className="text-xs text-gray-500">Muestra (3×3):</span>
                                    <div className="mt-1 font-mono text-xs text-gray-700 bg-white rounded p-2 inline-block border border-blue-200">
                                      {w.sample_values.map((row, ri) => (
                                        <div key={ri}>[{row.join(", ")}]</div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {capa.biases.length > 0 && (
                        <div>
                          <h6 className="text-sm font-semibold text-purple-800 mb-2 flex items-center gap-2">
                            <span className="w-2 h-2 bg-purple-500 rounded-full" />
                            Sesgos
                          </h6>
                          <div className="grid gap-3">
                            {capa.biases.map((b, bi) => (
                              <div key={bi} className="bg-purple-50 rounded-lg p-3 text-sm">
                                <div className="flex flex-wrap gap-x-6 gap-y-1 mb-2">
                                  <span className="text-gray-600">
                                    Shape: <span className="font-mono font-bold text-gray-800">{JSON.stringify(b.shape)}</span>
                                  </span>
                                  <span className="text-gray-600">
                                    Elementos: <span className="font-bold text-gray-800">{b.size}</span>
                                  </span>
                                </div>
                                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                                  <span>Media: <span className="font-mono font-bold">{b.mean}</span></span>
                                  <span>Std: <span className="font-mono font-bold">{b.std}</span></span>
                                  <span>Min: <span className="font-mono font-bold">{b.min}</span></span>
                                  <span>Max: <span className="font-mono font-bold">{b.max}</span></span>
                                </div>
                                {b.sample_values && (
                                  <div className="mt-2">
                                    <span className="text-xs text-gray-500">Muestra (primeros 5):</span>
                                    <div className="mt-1 font-mono text-xs text-gray-700 bg-white rounded p-2 inline-block border border-purple-200">
                                      [{b.sample_values.join(", ")}]
                                    </div>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {capa.weights.length === 0 && capa.biases.length === 0 && (
                        <p className="text-sm text-gray-500 italic">Capa sin parámetros entrenables (Dropout)</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
                <AlertCircle size={40} className="mx-auto text-amber-500 mb-3" />
                <h4 className="font-bold text-amber-800 text-lg">Datos de pesos no disponibles</h4>
                <p className="text-amber-700 mt-2 max-w-lg mx-auto text-sm">
                  {weightsData?.mensaje || "Los pesos y sesgos no están disponibles en esta compilación."}
                </p>
                {weightsData?.diagnostico && (
                  <div className="mt-3 max-w-lg mx-auto bg-amber-100/70 rounded-lg px-4 py-2 text-xs text-left font-mono text-amber-900 whitespace-pre-wrap break-all">
                    {weightsData.diagnostico}
                  </div>
                )}
                <div className="mt-4 inline-block bg-amber-100 text-amber-800 px-4 py-2 rounded-lg text-sm font-mono">
                  python app/ml/training/rnn_intent_training_template.py
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default NeuralNetworkViz;
