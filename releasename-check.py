#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import urllib.request
import re

def _rename_file(movie_info, check_mode):
    old_file = os.path.join(movie_info['dir_name'], movie_info['file_name'])
    new_file = os.path.join(movie_info['dir_name'], movie_info['release_name_srrdb'] + movie_info['release_name_file_ext'])
    old_crc_file = os.path.join(movie_info['dir_name'], movie_info['crc_name'])
    new_crc_file = os.path.join(movie_info['dir_name'], movie_info['release_name_srrdb'] + '.crc')

    if os.path.isfile(old_file) and not os.path.isfile(new_file):
        if not check_mode:
            pass
            os.rename(old_file, new_file)
            os.rename(old_crc_file, new_crc_file)
            if os.path.isfile(new_file):
                print(f'Old File: {old_file}')
                print(f'New File: {new_file}')
                return True
            else:
                print(f'Something goes wrong with file: {new_file}')
                print(f'This program will stop, please fix the problem first.')
                exit()
    return True
  
def _get_releasename_of_srrdb(movie_info):
    full_url = "https://www.srrdb.com/api/search/archive-crc:" + movie_info['crc_hash']
    with urllib.request.urlopen(full_url) as url:
        data = json.loads(url.read().decode())
    for i in data['results']:
        if i.get('release'):
            return i['release']    
    return None

def _crc_create(movie_info, check_mode):
    if not check_mode:
        with open(movie_info['full_crc_path'], 'w+') as f:
            f.write(movie_info['crc_hash'])

        return True if os.path.isfile(movie_info['full_crc_path']) else False
    else:
        return True

def _crc_generate(movie_info):
    # Checkmode maken.
    result_raw = subprocess.check_output(['cksfv', '-c', movie_info['full_path']], text=True)
    # Test
    # result_raw = subprocess.check_output(['cksfv', '-c', '/home/bram/Downloads/config'], text=True)
    crc_hash = result_raw.rstrip('\n')[-8:]
    crc_okey = re.search("[A-Z0-9]{8}$", crc_hash)
    if crc_okey:
        print(f'CRC Generated: {crc_hash}')
        return crc_hash
    else:
        return None

def _find_movies(fpath):
    movies = {}
    i = 1
    # r=dirpath, d=dirnames, f = files
    for r, d, f in os.walk(fpath):
        for file in f:
            if '.mkv' in file:
                movies[i] = {}
                movies[i]['release_name'] = file[:-4]
                movies[i]['release_name_file_ext'] = file[-4:]
                movies[i]['release_name_srrdb'] = None
                movies[i]['file_name'] = file
                movies[i]['dir_name'] = r
                movies[i]['full_path'] = r + '/' + file
                movies[i]['full_crc_path'] = r + '/' + movies[i]['release_name'] + '.crc'
                movies[i]['crc_hash'] = _crc_file_exist(movies[i]['full_crc_path'], movies[i]['file_name'])
                movies[i]['crc_name'] = movies[i]['release_name'] + '.crc'
                
                i = i + 1
    return movies

def _crc_file_exist(crc_path, crc_name):
    isFile = os.path.isfile(crc_path)
    if isFile:
        with open(crc_path, 'r') as file:
            data = file.read().replace('\n', '')
        return data
    return None

def _check_valid_path(fpath):
    isDirectory = os.path.isdir(fpath)
    return isDirectory
    

def _startup_aggr(aggruments):
    aggr = {}
    for i, j in enumerate(aggruments):	
        if ('--path' in j) or ('-p' in j):	
            aggr['isDirectory'] = aggruments[i+1]	
            if not _check_valid_path(aggr['isDirectory']):	
                print(f"Wrong directory {aggr['isDirectory']}")	
                exit()	
        if '--check-only' in j:
            aggr['check_mode'] = True
    if not aggr.get('check_mode'):
        aggr['check_mode'] = False

    print(f'This program wil start with the following arrguments.')
    print(f"Scan Dir:   {aggr['isDirectory']}")
    print(f"Check mode: {aggr['check_mode']}\n\n")
    
    return aggr

def _main():	
    # Check if aggruments are correct.	
    aggr = _startup_aggr(sys.argv)

    # Collect movies information into a json.
    movies =  _find_movies(aggr['isDirectory'])
    

    for id in movies:
    
        # Create / Check CRC 
        if not movies[id].get('crc_hash'):
            print(f"File: {movies[id]['file_name']}")
            movies[id]['crc_hash'] = _crc_generate(movies[id])
            if _crc_create(movies[id], aggr['check_mode']):
                print(f"CRC saved: {movies[id].get('crc_name')}")

        # Check release_name srrdb
        if not movies[id].get('release_name_srrdb'):
            if movies[id].get('crc_hash'):
                movies[id]['release_name_srrdb'] = _get_releasename_of_srrdb(movies[id])
    
        # Rewrite movie based on match release_name and srrdb
        if movies[id]['release_name'] != movies[id]['release_name_srrdb']:
            if movies[id]['release_name_srrdb']:
                if _rename_file(movies[id], aggr['check_mode']):
                    print(f'Rename file: Done')
            else:
                print(f'No match found on srrdb')
        
        print(f'-------------------------')
    
    
if __name__ == '__main__':
     _main()
    # https://www.srrdb.com/api/search/archive-crc:445CF107
    # if str1.startswith('"') and str1.endswith('"'):