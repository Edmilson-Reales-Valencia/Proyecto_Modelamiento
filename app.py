from flask import Flask, request, render_template, jsonify
import pandas as pd
import numpy as np
from PoliLagrange import interpolation
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        data = pd.read_csv(file)
        
        if 'Hora' not in data.columns or 'Consumo' not in data.columns:
            return jsonify({"error": "El archivo debe contener columnas 'Hora' y 'Consumo'."}), 400
        
        # Convertir horas a un formato numérico
        X = [int(h.split(':')[0]) + int(h.split(':')[1]) / 60.0 for h in data['Hora'].tolist()]
        Y = data['Consumo'].tolist()  # Suponiendo consumo ya es numérico
        
        instants = []
        
        for i in range(len(X) - 1):
            start_hour, start_minute = map(int, data['Hora'].iloc[i].split(':'))
            for j in range(4):
                minute = start_minute + j * 15
                if minute >= 60:
                    minute -= 60
                    start_hour += 1
                instants.append(start_hour + minute / 60.0)  # Convertir a formato decimal

        interpolated_values = []
        for instant in instants:
            try:
                # Llamar a interpolation con valores numéricos
                result = interpolation(instant, X, Y)
                interpolated_values.append(float(result))
            except Exception as e:
                return jsonify({"error": f"Error en el cálculo de interpolación: {str(e)}"}), 400

        return jsonify(instants=instants, values=interpolated_values)

if __name__ == '__main__':
    app.run(debug=True)