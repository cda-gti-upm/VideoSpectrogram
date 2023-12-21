import pyfiglet

ascii_banner = pyfiglet.figlet_format("Seismic data visualizator")
print(ascii_banner)

vis_type = input('¿Qué desea visualizar?\n'
                 'Opción 1: Plot + RSAM\n'
                 'Opción 2: 3 canales de un geófono\n'
                 'Opción 3: Plot + espectrograma\n')
if vis_type == '1':
    geo = input('Seleccione el número de geófono\n')
    geo = 'Geophone' + geo
    channel = input('Seleccione un canal: (X, Y, Z) \n')
    channel = str.upper(channel)
    start = input('Seleccione instante inicial:  formato yyyy-mm-dd hh:mm:ss o dejar vacío para ver todo\n')
    end = input('Seleccione instante inicial:  formato yyyy-mm-dd hh:mm:ss o dejar vacío para ver todo\n')
    filter_50Hz_f = input('Desea filtrar la señal de 50 Hz (s ó n)\n')
    formato = input('Formato de los datos: (PICKLE)\n')
    formato = 'PICKLE'