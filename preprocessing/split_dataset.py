'''
===========================================================

Script ini digunakan untuk membagi dataset gambar dan file label XML menjadi tiga bagian: train (80%), validation (10%), dan test (10%).

Fitur utama:
- Mengacak urutan file sebelum membagi agar distribusinya merata.
- Membuat struktur folder otomatis: images/train, images/val, images/test, serta labels/train, labels/val, labels/test.
- Menyalin file gambar .jpg dan label .xml ke dalam folder yang sesuai.

===========================================================
'''

import os
import random
import shutil
from pathlib import Path

# Set seed for reproducibility
random.seed(42)

# Folder awal berisi .jpg dan .xml
source_folder = Path("dataset")

# Buat folder target
for group in ['train', 'val', 'test']:
    os.makedirs(f"images/{group}", exist_ok=True)
    os.makedirs(f"labels/{group}", exist_ok=True)

# Ambil semua nama file gambar
filenames = [f.stem for f in source_folder.glob("*.jpg")]
random.shuffle(filenames)

# Split
total = len(filenames)
train_end = int(0.8 * total)
val_end = int(0.9 * total)

splits = {
    'train': filenames[:train_end],
    'val': filenames[train_end:val_end],
    'test': filenames[val_end:]
}

# Copy file .jpg dan .xml ke folder masing masing
for split, files in splits.items():
    for name in files:
        # copy image
        shutil.copy2(source_folder / f"{name}.jpg", f"images/{split}/{name}.jpg")
        # copy label
        shutil.copy2(source_folder / f"{name}.xml", f"labels/{split}/{name}.xml")

print("Dataset split berhasil.")
