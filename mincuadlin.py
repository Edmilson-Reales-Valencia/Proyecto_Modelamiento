def mincuadlin(tiempo_dias, consumo_diario, dias_proyeccion, tarifa_kwh):
    import numpy as np

    # Ajuste por mínimos cuadrados
    A = np.vstack([tiempo_dias, np.ones(len(tiempo_dias))]).T
    m, b = np.linalg.lstsq(A, consumo_diario, rcond=None)[0]

    # Estimar consumo futuro
    consumo_estimado = []
    for i in range(len(tiempo_dias), len(tiempo_dias) + dias_proyeccion):
        consumo_estimado.append(m * i + b)

    gasto_estimado_diario = [round(c * tarifa_kwh, 4) for c in consumo_estimado]
    gasto_proyectado_total = sum(gasto_estimado_diario)
    gasto_promedio_diario = np.mean(gasto_estimado_diario)

    # Análisis de tendencia
    direccion = "creciente" if m > 0 else "decreciente" if m < 0 else "estable"
    cambio_porcentual = ((m * len(tiempo_dias) + b) - np.mean(consumo_diario)) / np.mean(consumo_diario) * 100 if np.mean(consumo_diario) != 0 else 0


    return {
        "gastos": {
            "gasto_proyectado_diario": gasto_estimado_diario,
            "gasto_proyectado_total": round(gasto_proyectado_total, 2),
            "gasto_promedio_diario_proyectado": round(gasto_promedio_diario, 2),
            "gasto_historico_total": round(sum(consumo_diario) * tarifa_kwh, 2),
            "tarifa_kwh": tarifa_kwh
        },
        "proyeccion": {
            "dias": dias_proyeccion,
            "consumo_diario": [round(c, 2) for c in consumo_estimado],
            "consumo_promedio_proyectado": round(np.mean(consumo_estimado), 2)
        },
        "tendencia": {
            "direccion": direccion,
            "cambio_porcentual": round(cambio_porcentual, 2),
            "pendiente": round(m, 4),
            "intercepto": round(b, 4)
        },
        "resumen": {
            "ahorro_o_costo_adicional_mensual": round((gasto_promedio_diario - np.mean(consumo_diario) * tarifa_kwh) * 30, 2)
        }
    }
