import { useState } from "react";
import { Brain, Layers, BarChart3, AlertCircle, CheckCircle2 } from "lucide-react";
import modelData from "./model_data.json";

const COLORS = {
  input: { fill: "#3b82f6", stroke: "#1e3a5f", label: "Capa de Entrada (Embedding)" },
  lstm: { fill: "#10b981", stroke: "#065f46", label: "Capa Oculta (BiLSTM)" },
  dense: { fill: "#10b981", stroke: "#065f46", label: "Capa Oculta (Dense + ReLU)" },
  output: { fill: "#3b82f6", stroke: "#1e3a5f", label: "Capa de Salida (Softmax)" },
};

function getColorForLayer(type) {
  if (type === "embedding" || type === "input") return COLORS.input;
  if (type === "lstm") return COLORS.lstm;
  if (type === "dense") return COLORS.dense;
  if (type === "output") return COLORS.output;
  return COLORS.dense;
}

function getActivationLabel(layer) {
  if (layer.activation) return layer.activation.toUpperCase();
  if (layer.type === "dropout") return `DROPOUT ${layer.rate}`;
  return "—";
}

function getLayerSummary(layer) {
  const units = typeof layer.units === "number" ? layer.units : (layer.neurons || "?");
  return `${units} neuronas`;
}

function NeuralNetworkV2() {
  const [tab, setTab] = useState("network");
  const data = modelData.arquitectura;
  const weightsData = modelData.pesos;

  if (!data) return null;

  const layers = data.layers.filter((l) => l.type !== "dropout");
  const realLayers = data.layers;

  const inputCount = 5;
  const lstmCount = 6;
  const denseCount = 5;
  const outputCount = 9;

  const layerXPositions = [80, 280, 480, 680];
  const layerYStart = 60;
  const neuronRadius = 22;
  const verticalSpacing = 60;

  const inputY = layerYStart + 0;
  const lstmY = layerYStart + 0;
  const denseY = layerYStart + Math.max(0, (lstmCount - denseCount) * verticalSpacing / 2);
  const outputY = layerYStart + Math.max(0, (lstmCount - outputCount) * verticalSpacing / 2);

  const inputPositions = Array.from({ length: inputCount }, (_, i) => ({
    x: layerXPositions[0],
    y: inputY + i * verticalSpacing,
  }));
  const lstmPositions = Array.from({ length: lstmCount }, (_, i) => ({
    x: layerXPositions[1],
    y: lstmY + i * verticalSpacing,
  }));
  const densePositions = Array.from({ length: denseCount }, (_, i) => ({
    x: layerXPositions[2],
    y: denseY + i * verticalSpacing,
  }));
  const outputPositions = Array.from({ length: outputCount }, (_, i) => ({
    x: layerXPositions[3],
    y: outputY + i * verticalSpacing,
  }));

  const allLayers = [
    { positions: inputPositions, count: inputCount, info: realLayers[0], color: COLORS.input, actualNeurons: 128 },
    { positions: lstmPositions, count: lstmCount, info: realLayers[1], color: COLORS.lstm, actualNeurons: 256 },
    { positions: densePositions, count: denseCount, info: realLayers[3], color: COLORS.dense, actualNeurons: 64 },
    { positions: outputPositions, count: outputCount, info: realLayers[5], color: COLORS.output, actualNeurons: 9 },
  ];

  const svgWidth = 800;
  const svgHeight = Math.max(
    inputPositions[inputPositions.length - 1]?.y || 0,
    lstmPositions[lstmPositions.length - 1]?.y || 0,
    densePositions[densePositions.length - 1]?.y || 0,
    outputPositions[outputPositions.length - 1]?.y || 0
  ) + 100;

  const getWeightBiasForLayer = (layerIndex) => {
    return weightsData?.pesos_por_capa?.find((c) => c.layer_index === layerIndex) || null;
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-xl shadow overflow-hidden">
        <div className="p-5 border-b border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                <Brain size={24} className="text-blue-600" />
                Red Neuronal Profunda (Deep Neural Network)
              </h3>
              <p className="text-gray-500 mt-1">
                {data.modelo} — {data.framework}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setTab("network")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  tab === "network"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <Layers size={16} />
                Diagrama
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

        {tab === "network" && (
          <div className="p-5">
            <div className="mb-3 text-sm text-gray-600 flex items-center gap-2">
              <span className="font-semibold">Arquitectura:</span>
              <span>Embedding (128) → BiLSTM (256) → Dropout → Dense+ReLU (64) → Dropout → Dense+Softmax (9)</span>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 overflow-x-auto">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-auto"
                style={{ minWidth: 750 }}
              >
                <defs>
                  <marker
                    id="arrow"
                    markerWidth="8"
                    markerHeight="8"
                    refX="6"
                    refY="4"
                    orient="auto"
                  >
                    <path d="M0,0 L0,8 L8,4 z" fill="#94a3b8" />
                  </marker>
                </defs>

                {/* Connections between layers with weight labels */}
                {allLayers.slice(0, -1).map((layer, layerIdx) => {
                  const nextLayer = allLayers[layerIdx + 1];
                  const weightInfo = getWeightBiasForLayer(layer.info.index);
                  const numWeights = weightInfo?.weights?.[0];
                  const numBiases = weightInfo?.biases?.[0];
                  const totalConn = layer.positions.length * nextLayer.positions.length;
                  
                  return (
                    <g key={`conn-${layerIdx}`}>
                      {layer.positions.map((p1, i) =>
                        nextLayer.positions.map((p2, j) => (
                          <line
                            key={`line-${layerIdx}-${i}-${j}`}
                            x1={p1.x + neuronRadius}
                            y1={p1.y}
                            x2={p2.x - neuronRadius}
                            y2={p2.y}
                            stroke="#94a3b8"
                            strokeWidth={0.8}
                            opacity={0.5}
                          />
                        ))
                      )}
                      {/* Weight label between layers */}
                      <text
                        x={(layer.positions[0].x + nextLayer.positions[0].x) / 2}
                        y={-5}
                        fontSize={11}
                        fontWeight="bold"
                        fill="#1e40af"
                        textAnchor="middle"
                      >
                        W{layerIdx + 1}: {numWeights ? JSON.stringify(numWeights.shape) : "?"}
                      </text>
                      <text
                        x={(layer.positions[0].x + nextLayer.positions[0].x) / 2}
                        y={8}
                        fontSize={9}
                        fill="#6b7280"
                        textAnchor="middle"
                      >
                        ({totalConn} conexiones)
                      </text>
                    </g>
                  );
                })}

                {/* Neurons with bias labels */}
                {allLayers.map((layer, layerIdx) => {
                  const biasInfo = getWeightBiasForLayer(layer.info.index);
                  const biases = biasInfo?.biases?.[0]?.sample_values || [];
                  
                  return (
                    <g key={`layer-${layerIdx}`}>
                      {/* Layer label at top */}
                      <text
                        x={layer.positions[0].x}
                        y={-20}
                        fontSize={12}
                        fontWeight="bold"
                        fill={layer.color.stroke}
                        textAnchor="middle"
                      >
                        {layer.color.label}
                      </text>
                      <text
                        x={layer.positions[0].x}
                        y={-7}
                        fontSize={10}
                        fill="#6b7280"
                        textAnchor="middle"
                      >
                        {getActivationLabel(layer.info)} · {layer.actualNeurons} neuronas
                      </text>

                      {/* Neurons */}
                      {layer.positions.map((pos, i) => {
                        const biasVal = biases[i] !== undefined ? biases[i].toFixed(3) : null;
                        return (
                          <g key={`n-${layerIdx}-${i}`}>
                            <circle
                              cx={pos.x}
                              cy={pos.y}
                              r={neuronRadius}
                              fill={layer.color.fill}
                              stroke={layer.color.stroke}
                              strokeWidth={2}
                            />
                            <text
                              x={pos.x}
                              y={pos.y + 4}
                              fontSize={9}
                              fill="white"
                              textAnchor="middle"
                              fontWeight="bold"
                            >
                              n{i + 1}
                            </text>
                            {/* Bias label */}
                            {biasVal !== null && (
                              <text
                                x={pos.x}
                                y={pos.y + neuronRadius + 14}
                                fontSize={8}
                                fill="#7c3aed"
                                textAnchor="middle"
                                fontFamily="monospace"
                              >
                                b={biasVal}
                              </text>
                            )}
                          </g>
                        );
                      })}
                    </g>
                  );
                })}

                {/* Output class labels */}
                {outputPositions.map((pos, i) => {
                  const clase = data.clases?.[i] || `clase_${i}`;
                  return (
                    <text
                      key={`out-label-${i}`}
                      x={pos.x + neuronRadius + 8}
                      y={pos.y + 4}
                      fontSize={9}
                      fill="#1e40af"
                      fontWeight="bold"
                    >
                      {clase}
                    </text>
                  );
                })}
              </svg>
            </div>

            {/* Legend */}
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-blue-500 border-2 border-blue-800" />
                <span className="text-xs text-gray-700">Capa Entrada/Salida</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-green-500 border-2 border-green-800" />
                <span className="text-xs text-gray-700">Capas Ocultas</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-1 h-4 bg-gray-400" />
                <span className="text-xs text-gray-700">Pesos (W)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-purple-700">b=0.xxx</span>
                <span className="text-xs text-gray-700">Sesgos (b)</span>
              </div>
            </div>

            {/* Summary stats */}
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

export default NeuralNetworkV2;
