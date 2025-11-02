'''
===========================================================

Script ini digunakan untuk menghapus semua file .xml yang mungkin masih tersisa di dalam folder labels/train, labels/val, dan labels/test. Biasanya dilakukan setelah proses konversi label ke format .txt (YOLO).

===========================================================
'''


import os
import glob

# List folder target
label_dirs = ["labels/train", "labels/val", "labels/test"]

for folder in label_dirs:
    xml_files = glob.glob(os.path.join(folder, "*.xml"))
    for file_path in xml_files:
        os.remove(file_path)
        print(f"Dihapus: {file_path}")

print("Semua file .xml di dalam folder labels/* berhasil dihapus.")
