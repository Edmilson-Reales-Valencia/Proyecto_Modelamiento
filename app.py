from flask import Flask, request, jsonify, render_template, send_from_directory
import pandas as pd
import os
import numpy as np
from mincuadlin import mincuadlin
from PoliLagrange import interpolation

app = Flask(__name__)

# Crear la carpeta templates si no existe
if not os.path.exists('templates'):
    os.makedirs('templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    try:
        df = pd.read_csv(file)
        if 'Tiempo' not in df.columns or 'Consumo' not in df.columns:
            return jsonify({"error": "CSV debe contener columnas 'Tiempo' y 'Consumo'"}), 400
        
        df['Tiempo'] = pd.to_datetime(df['Tiempo'])
        df_15min = df.set_index('Tiempo').resample('15T').mean().interpolate()
        df_horario = df_15min.resample('H').mean()
        df_diario = df_15min.resample('D').sum()
        df_interpolado_diario = df_diario.interpolate().rolling(window=3, min_periods=1).mean()

        dias_proyeccion = int(request.form.get('dias_proyeccion', 30))
        tarifa_kwh = float(request.form.get('tarifa_kwh', 0.15))

        # Preparar datos para interpolación de Lagrange
        tiempo_dias = list(range(len(df_interpolado_diario)))
        consumo_diario = df_interpolado_diario['Consumo'].values

        # Usar mínimos cuadrados para estimación de gastos
        estimacion_gastos = mincuadlin(
            tiempo_dias, 
            consumo_diario, 
            dias_proyeccion, 
            tarifa_kwh
        )

        # Aplicar interpolación de Lagrange para suavizar los datos
        # Tomar puntos de muestra para la interpolación (evitar sobreajuste con muchos puntos)
        n_puntos = min(10, len(tiempo_dias))  # Máximo 10 puntos para evitar oscilaciones
        indices_muestra = np.linspace(0, len(tiempo_dias)-1, n_puntos, dtype=int)
        
        X_lagrange = [tiempo_dias[i] for i in indices_muestra]
        Y_lagrange = [consumo_diario[i] for i in indices_muestra]
        
        # Generar valores interpolados con Lagrange
        valores_lagrange = []
        for x in tiempo_dias:
            valor_interpolado = interpolation(x, X_lagrange, Y_lagrange)
            valores_lagrange.append(valor_interpolado)

        # Proyección futura usando Lagrange
        proyeccion_lagrange = []
        for dia_futuro in range(len(tiempo_dias), len(tiempo_dias) + dias_proyeccion):
            valor_proyectado = interpolation(dia_futuro, X_lagrange, Y_lagrange)
            # Evitar valores negativos
            valor_proyectado = max(0, valor_proyectado)
            proyeccion_lagrange.append(valor_proyectado)

        # Calcular estadísticas de la proyección con Lagrange
        consumo_proyectado_total = sum(proyeccion_lagrange)
        gasto_proyectado = consumo_proyectado_total * tarifa_kwh
        
        response = {
            "nivel_15min": {
                "tiempos": df_15min.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                "valores": df_15min['Consumo'].round(4).tolist()
            },
            "nivel_horario": {
                "tiempos": df_horario.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                "valores": df_horario['Consumo'].round(4).tolist()
            },
            "nivel_diario": {
                "tiempos": df_diario.index.strftime('%Y-%m-%d').tolist(),
                "valores": df_diario['Consumo'].round(4).tolist()
            },
            "nivel_interpolado_diario": {
                "tiempos": df_interpolado_diario.index.strftime('%Y-%m-%d').tolist(),
                "valores": df_interpolado_diario['Consumo'].round(4).tolist()
            },
            "interpolacion_lagrange": {
                "tiempos": df_interpolado_diario.index.strftime('%Y-%m-%d').tolist(),
                "valores": [round(v, 4) for v in valores_lagrange],
                "puntos_base": {
                    "indices": X_lagrange,
                    "valores": [round(v, 4) for v in Y_lagrange]
                }
            },
            "proyeccion_lagrange": {
                "dias": list(range(len(tiempo_dias) + 1, len(tiempo_dias) + dias_proyeccion + 1)),
                "valores": [round(v, 4) for v in proyeccion_lagrange],
                "consumo_total_proyectado": round(consumo_proyectado_total, 4),
                "gasto_proyectado": round(gasto_proyectado, 2)
            },
            "estadisticas": {
                "puntos_15min": len(df_15min),
                "promedio_horario": round(df_horario['Consumo'].mean(), 4),
                "consumo_total": round(df_diario['Consumo'].sum(), 4),
                "dias_analizados": len(df_diario),
                "consumo_max_diario": round(df_diario['Consumo'].max(), 4),
                "puntos_lagrange": n_puntos
            },
            "estimacion_gastos": estimacion_gastos,
            "comparacion_metodos": {
                "mincuadlin_vs_lagrange": {
                    "diferencia_consumo": round(abs(estimacion_gastos.get('consumo_proyectado', 0) - consumo_proyectado_total), 4),
                    "diferencia_gasto": round(abs(estimacion_gastos.get('gasto_proyectado', 0) - gasto_proyectado), 2)
                }
            }
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)