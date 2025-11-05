import pandas as pd
import datetime as dt
import os
import cv2
import subprocess
from sqlalchemy import create_engine
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from pyzbar.pyzbar import decode as pyzbar_decode
from ultralytics import YOLO

# ====== CONFIG PATH ======
MODEL_PATH = '/opt/airflow/dags/models/best.pt'
ZXING_JAR = '/opt/airflow/dags/zxing/zxing.jar'
INPUT_DIR = '/opt/airflow/dags/data/input_images'
RAW_DIR = '/opt/airflow/dags/data/raw_images'
OUTPUT_CSV = '/opt/airflow/dags/data/decoded_results.csv'
OUTPUT_DIR = '/opt/airflow/dags/data/output'
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====== POSTGRES (optional) ======
POSTGRES_CONN = 'postgresql://airflow:airflow@postgres:5432/airflow'

# ====== EXTRACT ======
def extract_images():
    for file in os.listdir(INPUT_DIR):
        if file.endswith(('.jpg', '.png')):
            src = os.path.join(INPUT_DIR, file)
            dst = os.path.join(RAW_DIR, file)
            if not os.path.exists(dst):
                os.system(f'cp "{src}" "{dst}"')
    print("Extract complete")

# ====== TRANSFORM (DETECT + DECODE) ======
def detect_and_decode():
    model = YOLO(MODEL_PATH)
    results_list = []

    for img_name in os.listdir(RAW_DIR):
        img_path = os.path.join(RAW_DIR, img_name)
        img = cv2.imread(img_path)
        if img is None: continue

        detections = model.predict(source=img, conf=0.4, imgsz=960)
        decoded = False

        for r in detections:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                crop = img[y1:y2, x1:x2]
                pyzbar_result = pyzbar_decode(crop)
                if pyzbar_result:
                    results_list.append({
                        'filename': img_name,
                        'barcode_type': pyzbar_result[0].type,
                        'decoded_content': pyzbar_result[0].data.decode('utf-8'),
                        'decoder_used': 'pyzbar'
                    })
                    decoded = True
                    break
            if decoded: break

        if not decoded:
            try:
                zx_cmd = f'java -jar {ZXING_JAR} "{img_path}"'
                zx_output = subprocess.check_output(zx_cmd, shell=True).decode('utf-8').strip()
                if zx_output:
                    results_list.append({
                        'filename': img_name,
                        'barcode_type': 'Unknown',
                        'decoded_content': zx_output,
                        'decoder_used': 'ZXing'
                    })
                else:
                    results_list.append({
                        'filename': img_name,
                        'barcode_type': '-',
                        'decoded_content': '-',
                        'decoder_used': 'FAILED'
                    })
            except:
                results_list.append({
                    'filename': img_name,
                    'barcode_type': '-',
                    'decoded_content': '-',
                    'decoder_used': 'ZXing_FAILED'
                })

    pd.DataFrame(results_list).to_csv(OUTPUT_CSV, index=False)
    print("Transform complete: decoded_results.csv saved.")

# ====== LOAD TO POSTGRES (optional) ======
def load_to_postgres():
    df = pd.read_csv(OUTPUT_CSV)
    engine = create_engine(POSTGRES_CONN)
    df.to_sql('decoded_barcodes', engine, if_exists='replace', index=False)
    print("Loaded to PostgreSQL table 'decoded_barcodes'")

# ====== EVALUATE ======
def evaluate_decode():
    df = pd.read_csv(OUTPUT_CSV)
    total = len(df)
    success = df[df['decoder_used'] != 'FAILED']
    rate = round(len(success) / total * 100, 2)

    report = pd.DataFrame([{
        'total_images': total,
        'successful_decodes': len(success),
        'failed_decodes': total - len(success),
        'success_rate (%)': rate,
        'timestamp': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }])

    path = os.path.join(OUTPUT_DIR, f'final_report_{dt.datetime.now().strftime("%Y%m%d")}.csv')
    report.to_csv(path, index=False)
    print(f"Evaluation saved: {path}")

# ====== DAG CONFIG ======
default_args = {
    'owner': 'davon',
    'start_date': dt.datetime(2025, 11, 5),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=5)
}

with DAG('barcode_etl_dag',
         default_args=default_args,
         schedule_interval=None,
         catchup=False) as dag:

    start = BashOperator(task_id='starting', bash_command='echo "🚀 Starting barcode ETL pipeline"')

    extract_task = PythonOperator(task_id='extract_images', python_callable=extract_images)
    transform_task = PythonOperator(task_id='detect_and_decode', python_callable=detect_and_decode)
    load_task = PythonOperator(task_id='load_to_postgres', python_callable=load_to_postgres)
    evaluate_task = PythonOperator(task_id='evaluate_decode', python_callable=evaluate_decode)

    end = BashOperator(task_id='ending', bash_command='echo "🎯 Pipeline finished!"')

    # Dependencies
    start >> extract_task >> transform_task >> load_task >> evaluate_task >> end
