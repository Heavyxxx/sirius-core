import pandas as pd
from flask import Flask, render_template, jsonify, request, send_file
import requests
import hashlib
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = Flask(__name__)

# Base de datos completa: 32 estados de México
ESTADOS_MEXICO = [
    {"n": "Aguascalientes", "lat": 21.8853, "lon": -102.2916}, 
    {"n": "Baja California", "lat": 30.8406, "lon": -115.2838},
    {"n": "Baja California Sur", "lat": 25.7617, "lon": -111.4604},
    {"n": "Campeche", "lat": 19.8301, "lon": -90.5349},
    {"n": "Chiapas", "lat": 16.7569, "lon": -93.1292}, 
    {"n": "Chihuahua", "lat": 28.6330, "lon": -106.0691},
    {"n": "Ciudad de México", "lat": 19.4326, "lon": -99.1332}, 
    {"n": "Coahuila", "lat": 27.0587, "lon": -101.7068},
    {"n": "Colima", "lat": 19.2381, "lon": -104.6866},
    {"n": "Durango", "lat": 24.0277, "lon": -104.6532},
    {"n": "Estado de México", "lat": 19.3502, "lon": -99.6449}, 
    {"n": "Guanajuato", "lat": 20.9167, "lon": -101.4833},
    {"n": "Guerrero", "lat": 17.4392, "lon": -99.5451},
    {"n": "Hidalgo", "lat": 20.1105, "lon": -98.7600},
    {"n": "Jalisco", "lat": 20.6595, "lon": -103.3494},
    {"n": "Michoacán", "lat": 19.5665, "lon": -101.7068},
    {"n": "Morelos", "lat": 18.6813, "lon": -99.1013}, 
    {"n": "Nayarit", "lat": 21.7514, "lon": -105.2517},
    {"n": "Nuevo León", "lat": 25.6866, "lon": -100.3161},
    {"n": "Oaxaca", "lat": 17.0732, "lon": -96.7266},
    {"n": "Puebla", "lat": 19.0414, "lon": -98.2063}, 
    {"n": "Querétaro", "lat": 20.5888, "lon": -100.3899},
    {"n": "Quintana Roo", "lat": 19.1823, "lon": -87.3247},
    {"n": "San Luis Potosí", "lat": 22.1597, "lon": -100.9855},
    {"n": "Sinaloa", "lat": 24.7964, "lon": -107.3964},
    {"n": "Sonora", "lat": 29.0729, "lon": -110.9559},
    {"n": "Tabasco", "lat": 17.8409, "lon": -92.2623},
    {"n": "Tamaulipas", "lat": 23.7345, "lon": -98.1592},
    {"n": "Tlaxcala", "lat": 19.3130, "lon": -98.2349},
    {"n": "Veracruz", "lat": 19.1738, "lon": -96.1342},
    {"n": "Yucatán", "lat": 20.8449, "lon": -87.7277},
    {"n": "Zacatecas", "lat": 22.7709, "lon": -102.5832}
]

def obtener_data_climatica(lat, lon):
    try:
        r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m&timezone=auto", timeout=5)
        return r.json()['current']
    except:
        return {'temperature_2m': 20, 'relative_humidity_2m': 50, 'wind_speed_10m': 10}

def calcular_bioclimatologia(clima):
    temp = clima.get('temperature_2m', 20)
    hum = clima.get('relative_humidity_2m', 50)
    ith = (0.8 * temp) + ((hum / 100) * (temp - 14.4)) + 46.4
    riesgo = "BAJO" if ith < 72 else ("MEDIO" if ith < 78 else "ALTO")
    impacto = (ith - 72) * 12500 if ith > 72 else 0
    colors_map = {"BAJO": "#2ecc71", "MEDIO": "#f1c40f", "ALTO": "#e74c3c"}
    return {"ith": round(ith, 2), "riesgo": riesgo, "impacto": impacto, "temp": temp, "hum": hum, "color": colors_map[riesgo], "viento": f"{clima.get('wind_speed_10m')} km/h"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/operacion_sirius', methods=['POST'])
def operacion_sirius():
    data = request.json
    nombre, lat, lon = data.get('nombre'), data.get('lat'), data.get('lon')
    clima = obtener_data_climatica(lat, lon)
    res = calcular_bioclimatologia(clima)
    hash_id = hashlib.sha256(f"{nombre}{datetime.now()}".encode()).hexdigest()
    
    return jsonify({"status": "active", "payload": {
        "nombre": nombre, "lat": lat, "lon": lon, "temp": f"{res['temp']}°C", 
        "hum": f"{res['hum']}%", "viento": res['viento'], "ith": res['ith'],
        "riesgo": res['riesgo'], "agua": max(0, res['hum'] - 5), "forraje": "ESTABLE" if res['ith'] < 75 else "ALERTA",
        "finanzas": f"${res['impacto']:,.2f} MXN", "color": res['color'], "logistica": "FLUJO NORMAL", "hash": hash_id[:16]
    }})

@app.route('/export/csv')
def export_csv():
    data_total = []
    for edo in ESTADOS_MEXICO:
        clima = obtener_data_climatica(edo['lat'], edo['lon'])
        res = calcular_bioclimatologia(clima)
        data_total.append({"Estado": edo['n'], "ITH": res['ith'], "Riesgo": res['riesgo'], "Temp_C": res['temp'], "Impacto_MXN": res['impacto']})
    df = pd.DataFrame(data_total)
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name="Sirius_Reporte_Nacional.csv")

@app.route('/export/pdf')
def export_pdf():
    buffer = io.BytesIO()
    data_total = []
    ith_values = []
    
    for edo in ESTADOS_MEXICO:
        clima = obtener_data_climatica(edo['lat'], edo['lon'])
        res = calcular_bioclimatologia(clima)
        data_total.append({
            "estado": edo['n'], 
            "ith": res['ith'], 
            "riesgo": res['riesgo'],
            "temp": f"{res['temp']}°C",
            "hum": f"{res['hum']}%",
            "impacto": f"${res['impacto']:,.0f} MXN"
        })
        ith_values.append(res['ith'])
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.3*inch, bottomMargin=0.3*inch)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#2d2d2d'), alignment=0)
    text_style = ParagraphStyle('TextStyle', parent=styles['Normal'], fontSize=9, spaceAfter=6)

    # --- SECCIÓN ENCABEZADO (Título + Logo) ---
    logo_path = os.path.join('static', 'img', 'image.jpg')
    header_content = [Paragraph("<b>SIRIUS CORE</b><br/><font size=12>REPORTE NACIONAL BIOCLIMÁTICO</font>", title_style)]
    
    # Intentar cargar imagen
    header_data = [header_content]
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=0.8*inch, height=0.8*inch)
        header_data = [[header_content[0], logo_img]]
    
    header_table = Table(header_data, colWidths=[5.5*inch, 1.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15)
    ]))
    story.append(header_table)

    # --- TABLA DE DATOS ---
    table_data = [["ESTADO", "ITH", "RIESGO", "TEMP", "HUMEDAD", "IMPACTO"]]
    for item in data_total:
        table_data.append([item["estado"], f"{item['ith']:.2f}", item["riesgo"], item["temp"], item["hum"], item["impacto"]])
    
    data_table = Table(table_data, colWidths=[1.8*inch, 0.7*inch, 0.9*inch, 0.7*inch, 0.9*inch, 1.3*inch], repeatRows=1)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.gold),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(data_table)
    story.append(Spacer(1, 0.2*inch))
    
    # --- DIAGNÓSTICO GLOBAL ---
    promedio_ith = sum(ith_values) / len(ith_values)
    estables = len([v for v in ith_values if v < 72])
    alertas = len([v for v in ith_values if 72 <= v < 78])
    criticos = len([v for v in ith_values if v >= 78])
    
    diag_box_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1c40f')),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('PADDING', (0,0), (-1,-1), 10)
    ])

    diag_text = f"""
    <b>CONCLUSIONES DEL MOTOR SIRIUS AI</b><br/>
    Análisis sobre {len(ESTADOS_MEXICO)} entidades: El promedio nacional se ubica en <b>{promedio_ith:.2f} ITH</b>.<br/>
    Distribución: {estables} Óptimos, {alertas} en Alerta y {criticos} en estado Crítico.<br/>
    <i>Recomendación estratégica: Implementar protocolos de mitigación inmediata en regiones con ITH > 78.</i>
    """
    
    diag_table = Table([[Paragraph(diag_text, text_style)]], colWidths=[7.3*inch])
    diag_table.setStyle(diag_box_style)
    story.append(diag_table)
    
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name="Sirius_Reporte_Nacional.pdf")

if __name__ == '__main__':
    app.run(debug=True, port=5000)