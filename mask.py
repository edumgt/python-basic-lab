import os
import cv2
import pytesseract
import re
import sys

# 현재 실행 파일 기준 경로 계산
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
TESSERACT_EXE = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")
TESSDATA_DIR = os.path.join(BASE_DIR, "tesseract", "tessdata")

pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

def mask_jumin_number(image_path, output_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, lang='kor', output_type=pytesseract.Output.DICT)

    found = False
    for i, text in enumerate(data['text']):
        match = re.match(r'(\d{6})[- ]?(\d{7})', text)
        if match:
            found = True
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            front_width = int(w * 6 / 13)
            mask_x = x + front_width + 5
            mask_w = w - front_width - 5
            cv2.rectangle(image, (mask_x, y), (mask_x + mask_w, y + h), (0, 0, 0), -1)

    if found:
        cv2.imwrite(output_path, image)
        print(f"[✅] 마스킹 저장: {output_path}")
    else:
        print(f"[ℹ️] 주민번호 미검출 → 생략: {os.path.basename(image_path)}")

def process_folder(org_folder="org", upd_folder="upd"):
    os.makedirs(upd_folder, exist_ok=True)

    for filename in os.listdir(org_folder):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        org_path = os.path.join(org_folder, filename)
        upd_path = os.path.join(upd_folder, filename)

        if not os.path.exists(upd_path):
            print(f"[🔍] 새 파일 감지: {filename}")
            mask_jumin_number(org_path, upd_path)
        else:
            print(f"[⏩] 이미 처리됨: {filename}")

if __name__ == "__main__":
    process_folder()
