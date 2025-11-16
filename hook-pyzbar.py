from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules
import os

# Collect all pyzbar files
datas = collect_data_files('pyzbar')
binaries = collect_dynamic_libs('pyzbar')
hiddenimports = collect_submodules('pyzbar')

# Find and add all DLLs in pyzbar directory
try:
    import pyzbar
    pyzbar_path = os.path.dirname(pyzbar.__file__)
    
    # Add all DLL files found in pyzbar directory
    for file in os.listdir(pyzbar_path):
        if file.endswith('.dll'):
            dll_path = os.path.join(pyzbar_path, file)
            # Add to both root and pyzbar subdirectory
            binaries.extend([
                (dll_path, '.'),
                (dll_path, 'pyzbar')
            ])
            
except ImportError:
    pass