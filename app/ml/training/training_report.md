# Reporte de entrenamiento ML - Riesgo de inasistencia

- Tipo de proyecto: Machine Learning tabular
- Dataset: `citas_medicas_pichanaki_junin_5000.csv`
- Algoritmo: `RandomForestClassifier`
- Librerías evidenciadas: `numpy`, `pandas`, `scikit-learn`
- Variable objetivo: `nivel_riesgo`
- Variables predictoras: `edad_paciente, genero, especialidad, prioridad, turno_cita, num_inasistencias_previas, distancia_km, dias_para_cita, minutos_espera_estimados`
- Accuracy: `0.5490`
- MSE: `0.8620`

## Classification report

```text
              precision    recall  f1-score   support

        alto       0.58      0.63      0.61       302
        bajo       0.57      0.76      0.65       390
       medio       0.40      0.21      0.27       308

    accuracy                           0.55      1000
   macro avg       0.52      0.53      0.51      1000
weighted avg       0.52      0.55      0.52      1000

```

Nota: Es un proyecto ML, no DL; por eso no requiere gráfico de red neuronal.
