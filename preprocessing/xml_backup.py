'''
===========================================================

Script ini memindahkan semua file .xml dari folder dataset ke folder xml_backup. Folder backup akan dibuat secara otomatis jika belum ada. Digunakan untuk merapikan folder dataset setelah file format XML selesai diubah ke format baru untuk training model.

===========================================================
'''


import os
import shutil

# Lokasi folder asal file .xml
xml_folder = "dataset"
backup_folder = "xml_backup"

# Folder backup jika belum ada
os.makedirs(backup_folder, exist_ok=True)

# Loop semua file di folder XML
for filename in os.listdir(xml_folder):
    if filename.endswith(".xml"):
        src_path = os.path.join(xml_folder, filename)
        dst_path = os.path.join(backup_folder, filename)
        shutil.move(src_path, dst_path)
        print(f"{filename} dipindahkan ke {backup_folder}/")

print("Semua file .xml berhasil dipindahkan ke folder backup.")
