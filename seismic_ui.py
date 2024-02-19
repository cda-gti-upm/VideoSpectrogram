import pyfiglet
import subprocess


ascii_banner = pyfiglet.figlet_format("Seismic data visualizator")
print(ascii_banner)
# Default parameters
filter_50Hz_f = 'n'
formato = 'PICKLE'
location = 'ElHierro'  #  location = 'ElHierro'
geo = ''
vis_type = ''
while vis_type not in ['1', '2', '3', '4']:
    vis_type = input('¿Qué desea visualizar?\n'
                     'Opción 1: Plot + RSAM\n'
                     'Opción 2: 3 canales de un geófono\n'
                     'Opción 3: Plot + espectrograma\n'
                     'Opción 4: RSAM + espectrograma\n')

while geo not in ['1', '2', '3', '4', '5', '6', '7', '8']:
    geo = input('Seleccione el número de geófono\n')
geo = 'Geophone' + geo
channel = ''
if vis_type in ['1', '3', '4']:
    while channel not in ['X', 'Y', 'Z']:
        channel = input('Seleccione un canal: (X, Y, Z) \n')
        channel = str.upper(channel)

start = input('Seleccione instante inicial:  formato yyyy-mm-dd hh:mm:ss o dejar vacío para ver todo\n')
end = input('Seleccione instante final:  formato yyyy-mm-dd hh:mm:ss o dejar vacío para ver todo\n')
# filter_50Hz_f = input('¿Desea filtrar la señal de 50 Hz? (s ó n)\n')
# formato = input('Formato de los datos: \n')

if vis_type == '1':
    proc = subprocess.run(['python', 'Dash_Seismic_Plot_RSAM.py', geo, channel, start, end, filter_50Hz_f, formato, location])
elif vis_type == '2':
    proc = subprocess.run(['python', 'Dash_Seismic_Plot_3_Channels.py', geo, start, end, filter_50Hz_f, formato, location])
else:
    win_length = '1024'
    hop_length = '256'
    n_fft = '2048'
    window = 'hann'
    S_max = '130'
    S_min = '75'
    print(f'Parámetros por defecto:\n'
          f'win_length: {win_length}\n'
          f'hop_length: {hop_length}\n'
          f'n_fft: {n_fft}\n'
          f'window: {window}\n'
          f'S_max: {S_max}\n'
          f'S_min: {S_min}\n')
    mod = input('¿Desea modificar los parámetros del espectrograma(s ó n)?\n')
    if mod == 's':
        win_length = input('win_length: ')
        hop_length = input('hop_length: ')
        n_fft = input('n_fft: ')
        window = input('window: ')
        S_max = input('S_max: ')
        S_min = input('S_min: ')
    if vis_type == '3':
        proc = subprocess.run(['python', 'Dash_Seismic_Plot_Spectrogram.py', geo, channel, start, end, filter_50Hz_f, formato, location,
                               win_length, hop_length, n_fft, window, S_max, S_min])
    else:
        proc = subprocess.run(
            ['python', 'Dash_Seismic_RSAM_Spectrogram.py', geo, channel, start, end, filter_50Hz_f, formato, location,
             win_length, hop_length, n_fft, window, S_max, S_min])
