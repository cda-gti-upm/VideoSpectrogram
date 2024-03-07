import sys

import pyfiglet
import subprocess
from CSIC_Seismic_Visualizator_Utils import load_config


ascii_banner = pyfiglet.figlet_format("Seismic data visualizator")
print(ascii_banner)


# Default parameters
filter_50Hz_f = 's'
formato = 'PICKLE'
location = 'LaPalma'  #  location = 'ElHierro'
min_y_fig1 = '0'
max_y_fig1 = '0'
auto_y_fig1 = 'autorange'
min_y_fig2 = '0'
max_y_fig2 = '0'
auto_y_fig2 = 'autorange'
min_y_fig3 = '0'
max_y_fig3 = '0'
auto_y_fig3 = 'autorange'

args = sys.argv
if len(args) > 1:
    file_path = f'./user_config/{args[1]}'
    params = load_config(file_path)
    if params['option'] == 1:
        params['auto_y_fig1'] = 'autorange' if params['auto_y_fig1'] == ['autorange'] else 'no'
        params['auto_y_fig2'] = 'autorange' if params['auto_y_fig2'] == ['autorange'] else 'no'
        print('Option 1 selected')
        proc = subprocess.run(
            ['python', 'CSIC_Seismic_Plot_Amplitude_RSAM.py', params['geophone'], params['channel'],
             params['start_time'], params['end_time'], params['filt_50Hz'], params['format_in'], params['location'],
             params['min_y_fig1'], params['max_y_fig1'], params['auto_y_fig1'],
             params['min_y_fig2'], params['max_y_fig2'], params['auto_y_fig2']]
        )
    elif params['option'] == 2:
        print('Option 2 selected')
        params['auto_y_fig1'] = 'autorange' if params['auto_y_fig1'] == ['autorange'] else 'no'
        params['auto_y_fig2'] = 'autorange' if params['auto_y_fig2'] == ['autorange'] else 'no'
        params['auto_y_fig3'] = 'autorange' if params['auto_y_fig3'] == ['autorange'] else 'no'
        proc = subprocess.run(
            ['python', 'CSIC_Seismic_Plot_3_Channels.py', params['geophone'],
             params['start_time'], params['end_time'], params['filt_50Hz'], params['format_in'], params['location'],
             params['min_y_fig1'], params['max_y_fig1'], params['auto_y_fig1'], params['min_y_fig2'],
             params['max_y_fig2'], params['auto_y_fig2'], params['min_y_fig3'],
             params['max_y_fig3'], params['auto_y_fig3']]
        )
    elif params['option'] == 3:
        print('Option 3 selected')
        params['auto_y_fig1'] = 'autorange' if params['auto_y_fig1'] == ['autorange'] else 'no'
        proc = subprocess.run(
            ['python', 'CSIC_Seismic_Plot_Amplitude_Spectrogram.py', params['geophone'], params['channel'],
             params['start_time'], params['end_time'], params['filt_50Hz'], params['format_in'], params['location'],
             params['min_y_fig1'], params['max_y_fig1'], params['auto_y_fig1'],
             params['min_y_fig2'], params['max_y_fig2'], params['win_length'], params['hop_length'], params['n_fft'],
             params['window'], params['s_min'], params['s_max']]
        )
    else:
        print('Option 4 selected')
        params['auto_y_fig1'] = 'autorange' if params['auto_y_fig1'] == ['autorange'] else 'no'
        proc = subprocess.run(
            ['python', 'CSIC_Seismic_Plot_RSAM_Spectrogram.py', params['geophone'], params['channel'],
             params['start_time'], params['end_time'], params['filt_50Hz'], params['format_in'], params['location'],
             params['min_y_fig1'], params['max_y_fig1'], params['auto_y_fig1'],
             params['min_y_fig2'], params['max_y_fig2'], params['win_length'], params['hop_length'], params['n_fft'],
             params['window'], params['s_min'], params['s_max']]
        )

else:
    geo = ''
    vis_type = ''
    while vis_type not in ['1', '2', '3', '4']:
        vis_type = input('¿Qué desea visualizar?\n'
                         'Opción 1: Plot + RSAM\n'
                         'Opción 2: 3 canales de un geófono\n'
                         'Opción 3: Plot + espectrograma\n'
                         'Opción 4: RSAM + espectrograma\n')

    while geo not in ['1', '2', '3', '4', '5', '6', '7', '8']:
        geo = input('Seleccione el número de geófono:\n')
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
        proc = subprocess.run(['python', 'CSIC_Seismic_Plot_Amplitude_RSAM.py', geo, channel, start, end, filter_50Hz_f,
                               formato, location, min_y_fig1, max_y_fig1, auto_y_fig1, min_y_fig2, max_y_fig2,
                               auto_y_fig2])
    elif vis_type == '2':
        proc = subprocess.run(['python', 'CSIC_Seismic_Plot_3_Channels.py', geo, start, end, filter_50Hz_f, formato,
                               location, min_y_fig1, max_y_fig1, auto_y_fig1, min_y_fig2, max_y_fig2,
                               auto_y_fig2, min_y_fig3, max_y_fig3,
                               auto_y_fig3])
    else:
        min_y_fig2 = '5'
        max_y_fig2 = '125'
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
            try:
                win_length = str(int(input('win_length: ')))
                hop_length = str(int(input('hop_length: ')))
                n_fft = str(int(input('n_fft: ')))
                window = str(int(input('window: ')))
                S_max = str(int(input('S_max: ')))
                S_min = str(int(input('S_min: ')))
            except Exception:
                print('Parámetros por defecto seleccionados.')
                win_length = '1024'
                hop_length = '256'
                n_fft = '2048'
                window = 'hann'
                S_max = '130'
                S_min = '75'

        if vis_type == '3':
            proc = subprocess.run(['python', 'CSIC_Seismic_Plot_Amplitude_Spectrogram.py', geo, channel, start, end, filter_50Hz_f, formato, location, min_y_fig1, max_y_fig1, auto_y_fig1, min_y_fig2, max_y_fig2,
                 win_length, hop_length, n_fft, window, S_min, S_max])
        else:
            proc = subprocess.run(['python', 'CSIC_Seismic_Plot_RSAM_Spectrogram.py', geo, channel, start, end, filter_50Hz_f, formato, location, min_y_fig1, max_y_fig1, auto_y_fig1, min_y_fig2, max_y_fig2,
                 win_length, hop_length, n_fft, window, S_min, S_max])
