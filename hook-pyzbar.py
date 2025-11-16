from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
import os

# Collect pyzbar DLLs
datas = collect_data_files('pyzbar')
binaries = collect_dynamic_libs('pyzbar')

# Find and add libzbar DLL manually
try:
    import pyzbar
    pyzbar_path = os.path.dirname(pyzbar.__file__)
    
    # Common DLL locations
    dll_names = ['libzbar-64.dll', 'libzbar.dll', 'zbar.dll']
    for dll_name in dll_names:
        dll_path = os.path.join(pyzbar_path, dll_name)
        if os.path.exists(dll_path):
            binaries.append((dll_path, '.'))
            break
except ImportError:
    pass