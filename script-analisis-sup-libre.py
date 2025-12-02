#%%
import os
import pandas as pd

def txts_a_excel_por_separado(carpeta):
    archivos_txt = [f for f in os.listdir(carpeta) if f.lower().endswith('.txt')]

    for archivo in archivos_txt:
        ruta_txt = os.path.join(carpeta, archivo)
        nombre_base = os.path.splitext(archivo)[0]
        ruta_excel = os.path.join(carpeta, nombre_base + '.xlsx')

        try:
            # Leer a partir de la línea 6 (índice 5), ignorando cabeceras u otras líneas corruptas
            df = pd.read_csv(
                ruta_txt,
                delimiter='\t',
                header=None,
                skiprows=5,  # Cambia este número si tus datos empiezan más arriba o más abajo
                encoding='latin1'
            )

            # Validar si tiene las dimensiones correctas
            if df.shape != (205, 101):
                print(f'⚠️  {archivo}: dimensiones inesperadas {df.shape}')
            
            df.to_excel(ruta_excel, index=False, header=False)
            print(f'✅ Convertido: {archivo} → {nombre_base}.xlsx')

        except Exception as e:
            print(f'❌ Error al procesar {archivo}: {e}')

# USO
carpeta = input("Introduce la ruta de la carpeta con los .txt: ").strip()
txts_a_excel_por_separado(carpeta)

#%%

import os
import pandas as pd

def consolidar_excels(carpeta):
    archivos_excel = [f for f in os.listdir(carpeta) if f.lower().endswith('.xlsx') and not f.startswith('~$')]

    ruta_excel_salida = os.path.join(carpeta, "raw-transformed.xlsx")
    writer = pd.ExcelWriter(ruta_excel_salida, engine='openpyxl')

    for archivo in archivos_excel:
        ruta_excel = os.path.join(carpeta, archivo)
        nombre_hoja = os.path.splitext(archivo)[0]

        try:
            # Leer el Excel
            df = pd.read_excel(ruta_excel, header=None)

            # Eliminar primera fila y primera columna
            df = df.iloc[1:, 1:]

            # Escribir en una nueva hoja del Excel general
            df.to_excel(writer, sheet_name=nombre_hoja[:31], index=False, header=False)
            print(f'✅ Añadido: {archivo} → hoja "{nombre_hoja}"')

        except Exception as e:
            print(f'❌ Error al procesar {archivo}: {e}')

    writer.close()
    print(f'\n📁 Consolidado generado en: {ruta_excel_salida}')

# USO
carpeta = input("Introduce la ruta de la carpeta con los .xlsx: ").strip()
consolidar_excels(carpeta)

#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import pandas as pd

# Parámetros de la malla, espaciado calculado en excel...
dx = 0.421214  # Espaciado longitudinal (popa → proa), en metros
dy = 0.340375  # Espaciado transversal (crujía → babor), en metros

# === Ruta del archivo Excel - cambiar solo el número de carpeta H - XX - X
archivo_excel = "ruta-de-tu-archivo/raw-transformed.xlsx"
xls = pd.ExcelFile(archivo_excel)

# === Función para extraer valor numérico del nombre de hoja (Fn o velocidad) ===
def extraer_valor(hoja):
    match = re.search(r'[\d.]+', hoja)
    return float(match.group()) if match else None

# === Procesamiento ===
resultados = []

for hoja in xls.sheet_names:
    df = xls.parse(hoja, header=None)
    Z_mitad = df.values

    # cambiar calados para cada carena...
    calado = 0.231  # en metros, por ejemplo: 1.8   
    Z = df.to_numpy()
    Z -= calado

    # Reflejar respecto a crujía
    Z_completa = np.hstack((np.flip(Z_mitad, axis=1), Z_mitad))

    # Calcular integrales
    integral_abs = np.sum(np.abs(Z_completa)) * dx * dy
    integral_cuadrada = np.sum(Z_completa**2) * dx * dy
    max_altura = np.max(Z_completa)
    min_altura = np.min(Z_completa)
    rango = max_altura - min_altura

    resultados.append({
        'Ensayo': hoja,
        'X_label': extraer_valor(hoja),
        'Z': Z_completa,
        'Integral_Abs': integral_abs,
        'Integral_Cuadrada': integral_cuadrada,
        'Max_Altura': max_altura,
        'Min_Altura': min_altura,
        'Rango_Alturas': rango
    })
       
    # Visualización
    fig, ax = plt.subplots(figsize=(10, 6))
    c = ax.imshow(Z_completa, cmap='coolwarm', origin='lower',
                  extent=[-dy*Z_mitad.shape[1], dy*Z_mitad.shape[1], 0, dx*Z_mitad.shape[0]])
    ax.set_title(f"Superficie libre completa – {hoja}")
    ax.set_xlabel("Distancia transversal (m)")
    ax.set_ylabel("Distancia longitudinal (m)")
    fig.colorbar(c, label='Altura (m)')
    plt.tight_layout()
    plt.show()

# === Ordenar resultados por X_label (por ejemplo, Froude o velocidad) ===
resultados = sorted(resultados, key=lambda x: x['X_label'] if x['X_label'] is not None else 0)

# === Panel combinado con 4 gráficos ===
x_vals = [r['X_label'] for r in resultados]
int_quad = [r['Integral_Cuadrada'] for r in resultados]
int_abs = [r['Integral_Abs'] for r in resultados]
z_max = [r['Max_Altura'] for r in resultados]
z_min = [r['Min_Altura'] for r in resultados]
z_range = [r['Rango_Alturas'] for r in resultados]

fig, axs = plt.subplots(2, 2, figsize=(12, 8))

# Integral cuadrática
axs[0, 0].plot(x_vals, int_quad, marker='o', color='navy')
axs[0, 0].set_title("∫ ζ² dxdy (Energía de ola)")
axs[0, 0].set_xlabel("Froude / Velocidad")
axs[0, 0].set_ylabel("Integral cuadrática (m²·m)")
axs[0, 0].grid(True)

# Integral de valor absoluto
axs[0, 1].plot(x_vals, int_abs, marker='s', color='darkorange')
axs[0, 1].set_title("∫ |ζ| dxdy (Magnitud total de ola)")
axs[0, 1].set_xlabel("Froude / Velocidad")
axs[0, 1].set_ylabel("Integral de módulo (m²)")
axs[0, 1].grid(True)

# Máximos y mínimos
axs[1, 0].plot(x_vals, z_max, marker='^', label='Máx ζ', color='darkgreen')
axs[1, 0].plot(x_vals, z_min, marker='v', label='Mín ζ', color='crimson')
axs[1, 0].set_title("Alturas extremas de ζ")
axs[1, 0].set_xlabel("Froude / Velocidad")
axs[1, 0].set_ylabel("Altura (m)")
axs[1, 0].legend()
axs[1, 0].grid(True)

# Rango
axs[1, 1].plot(x_vals, z_range, marker='D', linestyle='--', color='purple')
axs[1, 1].set_title("Rango de alturas: Máx - Mín")
axs[1, 1].set_xlabel("Froude / Velocidad")
axs[1, 1].set_ylabel("Rango ζ (m)")
axs[1, 1].grid(True)

plt.suptitle("Indicadores hidrodinámicos de superficie libre", fontsize=14, fontweight='bold')
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

# Crear un DataFrame a partir de la lista de resultados
df_resultados = pd.DataFrame(resultados)

# Guardar en un archivo Excel - cambiar solo el número de carpeta H - XX - X
df_resultados.to_excel("ruta-de-exportacion/out-transformed", index=False)

print("Resultados exportados a 'out-transformed.xlsx'")
