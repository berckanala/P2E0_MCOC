import numpy as np
import math
import pyvista as pv
import openseespy.opensees as ops

# Limpiar y crear modelo
ops.wipe()
ops.model('basic', '-ndm', 2, '-ndf', 2)

# Definir nodos y miembros
nodes = np.array([[0, 0],
                 [0, 12],
                 [8, 7.73332],
                 [8, 12],
                 [16, 11.7333],
                 [16, 12],
                 [24, 12],
                 [30, 9.4],
                 [30, 12],
                 [36, 12],
                 [36, 4]])

members = np.array([[1, 2],  # 1
                   [1, 3],  # 2 A1
                   [2, 3],  # 3
                   [2, 4],  # 4
                   [3, 4],  # 5
                   [3, 5],  # 6 A1
                   [4, 6],  # 7
                   [4, 5],  # 8
                   [5, 6],  # 9
                   [5, 7],  # 10 A1
                   [6, 7],  # 11
                   [7, 9],  # 12
                   [7, 8],  # 13 A1
                   [8, 9],  # 14
                   [8, 10],  # 15
                   [9, 10],  # 16
                   [8, 11],  # 17 A1
                   [10, 11]])  # 18

# Parámetros del material y área
E = 210e9  # Módulo de elasticidad en Pa

D1 = 0.15  # Diámetro en m
esp1 = 0.05  # Espesor en m

D2 = 0.1  # Diámetro en m
esp2 = 0.03  # Espesor en m
A1 = math.pi * ((D1 / 2) ** 2 - ((D1 - 2 * esp1) / 2) ** 2)  # Área de la sección transversal
A2 = math.pi * ((D2 / 2) ** 2 - ((D2 - 2 * esp2) / 2) ** 2)  # Área de la sección transversal

# Definir nodos en OpenSees
for i, n in enumerate(nodes):
    ops.node(i+1, float(n[0]), float(n[1]))

# Definir el material uniaxial elástico
ops.uniaxialMaterial('Elastic', 1, E)

# Definir elementos tipo Truss
for i, mbr in enumerate(members):
    if i == 1 or i == 5 or i == 9 or i == 12 or i == 16:
        ops.element('Truss', i+1, int(mbr[0]), int(mbr[1]), A1, 1)  # Usando el área A1 y el material 1
    else:
        ops.element('Truss', i+1, int(mbr[0]), int(mbr[1]), A2, 1)  # Usando el área A2 y el material 1

# Definir condiciones de frontera
ops.fix(1, 1, 1)  # Nodo 1 empotrado
ops.fix(11, 1, 1)  # Nodo 11 empotrado

# Definir cargas en los nodos
ops.timeSeries('Constant', 1)
ops.pattern('Plain', 1, 1)
ops.load(2, 0.0, -15000.0)
ops.load(4, 0.0, -30000.0)
ops.load(6, 0.0, -30000.0)
ops.load(7, 0.0, -30000.0)
ops.load(9, 0.0, -30000.0)
ops.load(10, 0.0, -15000.0)

# Configuración del análisis estático
ops.system('BandSPD')
ops.numberer('RCM')
ops.constraints('Plain')
ops.integrator('LoadControl', 1.0)
ops.algorithm('Linear')
ops.analysis('Static')

# Ejecutar análisis
if ops.analyze(1) != 0:
    print("Error en el análisis estático")
else:
    print("Análisis estático exitoso")

# Crear una malla de líneas para visualizar la estructura
plotter = pv.Plotter(off_screen=True)  # Habilitar el modo off_screen para renderizar sin mostrar

# Factor de escala para los desplazamientos
xfact = 500  # Ajusta este valor según sea necesario

# Lista para almacenar las magnitudes de desplazamiento en los miembros
desplazamientos_magnitud = []

# Dibujar estructura deformada y no deformada
for mbr in members:
    node_i = int(mbr[0])
    node_j = int(mbr[1])

    # Coordenadas originales
    ix, iy = nodes[node_i-1, :]
    jx, jy = nodes[node_j-1, :]

    # Desplazamientos escalados
    ux_i = ops.nodeDisp(node_i, 1) * xfact
    uy_i = ops.nodeDisp(node_i, 2) * xfact
    ux_j = ops.nodeDisp(node_j, 1) * xfact
    uy_j = ops.nodeDisp(node_j, 2) * xfact

    # Magnitud del desplazamiento en el miembro
    desplazamiento_mag = math.sqrt((ux_j - ux_i)**2 + (uy_j - uy_i)**2)
    desplazamientos_magnitud.append(desplazamiento_mag)

    # Línea sin deformación
    line_original = pv.Line([ix, iy, 0], [jx, jy, 0])
    plotter.add_mesh(line_original, color='grey', line_width=1, label="Estructura sin deformación")

    # Línea deformada
    line_deformada = pv.Line([ix + ux_i, iy + uy_i, 0], [jx + ux_j, jy + uy_j, 0])
    # Asignar el desplazamiento como un valor escalar

    plotter.add_mesh(line_deformada, scalars=[desplazamiento_mag], cmap="inferno", line_width=2,multi_colors=True, label="Estructura deformada")



# Mostrar los límites y añadir etiquetas a los ejes
# Mostrar los límites y añadir títulos a los ejes usando xtitle, ytitle, ztitle
plotter.show_bounds(
    grid='back',             # Muestra la cuadrícula en el fondo
    location='outer',        # Coloca las etiquetas fuera de la ventana gráfica
    xtitle='Distancia X (m)', # Título para el eje X
    ytitle='Distancia Y (m)'
)

plotter.view_xy()
plotter.show_axes()
# Añadir un título a la visualización
plotter.add_text("Estructura Deformada y no deformada", position="upper_edge", font_size=12, color="black")

# Guardar la visualización como una imagen
plotter.screenshot("E0_pyvista_heatmap.png")
plotter.close()
