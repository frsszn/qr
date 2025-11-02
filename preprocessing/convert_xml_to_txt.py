'''
===========================================================

Script ini dipakai untuk mengubah file label .xml menjadi file .txt dengan format yang sesuai untuk YOLO, untuk dua jenis objek: barcode dan qr.

Fitur utama:
- Mengubah koordinat bounding box ke format YOLO (x_center, y_center, width, height).
- Menyimpan hasil konversi ke dalam folder labels/train, labels/val, labels/test sesuai struktur data hasil split sebelumnya.
- Mendukung dua kelas yaitu 'barcode' : 0, 'qr' : 1.

Script ini penting untuk mempersiapkan dataset sebelum melakukan pelatihan YOLOv8.

Catatan:
- File XML yang tidak ditemukan akan dilewati.
- Bounding box akan diubah relatif terhadap ukuran gambar.

===========================================================
'''

import os
import xml.etree.ElementTree as ET

# Path folder gambar setelah split
image_root = "images"
label_root = "labels"

# Buat folder labels/train, val, test 
for split in ["train", "val", "test"]:
    os.makedirs(os.path.join(label_root, split), exist_ok=True)

# Path folder XML asli 
xml_folder = "dataset"

# Fungsi konversi koordinat ke format YOLO
def convert_to_yolo(size, box):
    dw = 1. / size[0]
    dh = 1. / size[1]
    x_center = (box[0] + box[1]) / 2.0
    y_center = (box[2] + box[3]) / 2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    return (x_center * dw, y_center * dh, w * dw, h * dh)

# Mapping nama class ke ID
class_map = {"barcode": 0, "qr": 1}

# Loop setiap split folder
for split in ["train", "val", "test"]:
    image_dir = os.path.join(image_root, split)
    label_dir = os.path.join(label_root, split)

    image_files = [f for f in os.listdir(image_dir) if f.endswith(".jpg")]
    image_names = [os.path.splitext(f)[0] for f in image_files]

    for name in image_names:
        xml_path = os.path.join(xml_folder, name + ".xml")
        if not os.path.exists(xml_path):
            print(f"⚠️ File XML untuk gambar {name} tidak ditemukan, dilewati.")
            continue

        tree = ET.parse(xml_path)
        root = tree.getroot()

        image_width = int(root.find("size/width").text)
        image_height = int(root.find("size/height").text)

        txt_path = os.path.join(label_dir, name + ".txt")
        with open(txt_path, "w") as f:
            for obj in root.findall("object"):
                class_name = obj.find("name").text.strip().lower()
                if class_name not in class_map:
                    continue 

                class_id = class_map[class_name]
                xml_box = obj.find("bndbox")
                xmin = int(xml_box.find("xmin").text)
                xmax = int(xml_box.find("xmax").text)
                ymin = int(xml_box.find("ymin").text)
                ymax = int(xml_box.find("ymax").text)

                yolo_box = convert_to_yolo((image_width, image_height), (xmin, xmax, ymin, ymax))
                yolo_box = [str(round(x, 6)) for x in yolo_box]
                f.write(f"{class_id} " + " ".join(yolo_box) + "\n")

print("Semua XML berhasil dikonversi ke YOLO format (2 class: barcode, qr) dan dibagi ke labels/train-val-test.")
