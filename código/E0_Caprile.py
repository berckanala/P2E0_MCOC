import numpy as np
import math
import matplotlib.pyplot as plt
import openseespy.opensees as ops

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

members = np.array([[1, 2],#1
                   [1, 3], #2 A1
                   [2, 3], #3
                   [2, 4], #4
                   [3, 4], #5
                   [3, 5], #6 A1
                   [4, 6], #7
                   [4, 5], #8
                   [5, 6], #9
                   [5, 7], #10 A1
                   [6, 7], #11
                   [7, 9], #12
                   [7, 8], #13 A1
                   [8, 9], #14
                   [8, 10], #15
                   [9, 10], #16
                   [8, 11], #17 A1
                   [10, 11]]) #18

# Parámetros del material y área
E = 210e9  # Módulo de elasticidad en Pa

D1 = 0.15  # Diámetro en m
esp1 = 0.05  # Espesor en m

D2 = 0.1 # Diámetro en m
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
    if i==1 or i== 5 or i == 9 or i == 12 or i == 16:
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


print("Fuerzas en los elementos")
mbr_forces = np.array([])
for i, mbr in enumerate(members):
    axial_force = round(ops.basicForce(i+1)[0]/1000,3)
    mbr_forces = np.append(mbr_forces, axial_force)
    print(f"Member {i+1}: axial force= {axial_force} kN")
print("--------------------")
print("")


# Imprimir desplazamientos en los nodos
print("Desplazamientos")
for i, n in enumerate(nodes):
    try:
        ux = round(ops.nodeDisp(i+1, 1)*1000,3)
        uy = round(ops.nodeDisp(i+1, 2)*1000,3)
        print(f"Node {i+1}: ux= {ux} mm, uy= {uy}mm")
    except Exception as e:
        print(f"Error al obtener desplazamientos del nodo {i+1}: {e}")

# Factor de escala para los desplazamientos
xfact = 500  # Ajusta este valor según sea necesario

# Visualización de la estructura
fig, axes = plt.subplots(figsize=(8, 4))

dibujado_sin_deformar = False
dibujado_deformado = False

# Dibujar la estructura original (sin deformación)
for mbr in members:
    node_i = int(mbr[0])
    node_j = int(mbr[1])

    ix = nodes[node_i-1,0]
    iy = nodes[node_i-1,1]
    jx = nodes[node_j-1,0]
    jy = nodes[node_j-1,1]

    # Estructura sin deformación
    if not dibujado_sin_deformar:
        axes.plot([ix, jx], [iy, jy], 'grey', lw=0.75, label = "Estructura sin deformación" )
        dibujado_sin_deformar = True
    axes.plot([ix, jx], [iy, jy], 'grey', lw=0.75)
    # Dibujar la estructura deformada
    
    ux_i = ops.nodeDisp(node_i, 1) *xfact
    uy_i = ops.nodeDisp(node_i, 2) *xfact
    ux_j = ops.nodeDisp(node_j, 1) *xfact
    uy_j = ops.nodeDisp(node_j, 2) *xfact

    if not dibujado_deformado:
        axes.plot([ix+ux_i, jx+ux_j], [iy+uy_i, jy+uy_j], "red", lw=1, label = "Estructura deformada" )
        dibujado_deformado = True
    axes.plot([ix+ux_i, jx+ux_j], [iy+uy_i, jy+uy_j], "red", lw=1)

axes.set_xlabel('Distancia (m)')
axes.set_ylabel('Distancia (m)')
plt.title('Estructura sin deformar y deformada')

plt.grid(True)
plt.legend()
plt.savefig('E0_matplotlib.png')