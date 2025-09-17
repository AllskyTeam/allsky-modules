import json
import time
import os
import tempfile
import requests
import gzip
import shutil
from pathlib import Path


class ALLSKYBUILDADSBDATABASES:
    def __init__(self):
        self._adsb_data_url = 'https://downloads.adsbexchange.com/downloads/basic-ac-db.json.gz'
        self._raw_data_file = 'basic-ac-db.json'
        script_path = Path(__file__).resolve()
        self._adsb_db_dir = os.path.join(script_path.parent.parent, 'adsb_data')

    def _download_adsb_data(self):
        print(f'Downloading raw data file from {self._adsb_data_url}')
        temp_file_name = None
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_name = temp_file.name

            response = requests.get(self._adsb_data_url)

            if response.status_code == 200:
                temp_file.write(response.content)
                print(f'Downloaded content to {temp_file_name}')
                print('Decompressing file')
                with gzip.open(temp_file_name, 'rb') as f_in:
                    with open(self._raw_data_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                print(f'Decompressed file to {self._raw_data_file}')
            else:
                print('Failed to download file.')

        if temp_file_name is not None:
            try:
                os.remove(temp_file_name)
            except OSError as e:
                print(f'Error removing temporary file: {e}')

    def _parse_adsb_data(self):
        ac_data = {}
        print('Parsing raw data')
        with open(self._raw_data_file, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file, start=1):
                data = json.loads(line)
                if data['ownop'] != 'CANCELLED/NOT ASSIGNED':
                    db_file_key = data['icao'][:2]
                    if db_file_key not in ac_data:
                        ac_data[db_file_key] = {}
                    ac_data[db_file_key][data['icao']] = {
                        'i': str(data['icao']),
                        'r': data['reg'],
                        'it': data['icaotype'],
                        'y': data['year'],
                        'm': data['manufacturer'],
                        'mo': data['model'],
                        'o': data['ownop'],
                        'st': data['short_type'],
                        'ml': data['mil']
                    }

                if i % 1000 == 0:
                    print('.', end='', flush=True)
        print('')
        print('Creating json files')
        total_aircraft = 0
        for icao_key in ac_data:
            icao_file = f'{icao_key}.json'
            file_path = os.path.join(self._adsb_db_dir, icao_file)
            aircraft_in_file = len(ac_data[icao_key])
            total_aircraft = total_aircraft + aircraft_in_file
            print(f'{icao_file} Aircraft written = {aircraft_in_file:,}')
            with open(file_path, 'w') as file:
                json.dump(ac_data[icao_key], file, indent=2)
        print(f'Total Aircraft written {total_aircraft:,}')

        try:
            os.remove(self._raw_data_file)
        except OSError as e:
            print(f'Error removing {self._raw_data_file} file: {e}')
                
    def run(self):
        self._download_adsb_data()
        self._parse_adsb_data()


if __name__ == '__main__':
    start_time = time.time()
    builder = ALLSKYBUILDADSBDATABASES()
    builder.run()
    end_time = time.time()
    execution_time = end_time - start_time
    print(f'Execution time: {execution_time} seconds')
    exit(0)
