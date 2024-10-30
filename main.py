import os
import subprocess
from PIL import Image
import pytesseract
import time
import keyboard
import sys
import cv2
import re
import numpy as np


current_directory = os.path.dirname(os.path.abspath(__file__))
screenshot_dir = os.path.join(current_directory, "screenshots")


def init():
    """初始化截图目录"""
    if not os.path.exists(screenshot_dir):
        os.mkdir(screenshot_dir)


def take_screenshot(path: str):
    """获取手机截屏,保存到path"""
    screenshot_path = "/sdcard/screenshot.png"
    subprocess.run(["adb", "shell", "screencap", "-p", screenshot_path])
    subprocess.run(["adb", "pull", screenshot_path, path])
    subprocess.run(["adb", "shell", "rm", screenshot_path])
    print(f"截图保存至 {path}")


def preprocess_image(image_path):
    """使用OpenCV预处理图像，转换为灰度并二值化"""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
    # 增强黑色部分
    # 进行形态学操作以增强黑色区域
    kernel = np.ones((3, 3), np.uint8)  # 创建结构元素
    enhanced = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)  # 闭运算
    processed_img = Image.fromarray(enhanced)
    return processed_img


def crop_image(image_path: str, crop_area: tuple):
    """裁剪图像并返回裁剪后的图像"""
    with Image.open(image_path) as img:
        cropped_img = img.crop(crop_area)
        cropped_img_path = os.path.join(screenshot_dir, "cropped_area.png")
        cropped_img.save(cropped_img_path)
        print(f"裁剪区域的图片保存至 {cropped_img_path}")
        return cropped_img_path


def recognize_numbers(image_path: str):
    """使用pytesseract识别图片中的数字"""
    if os.path.exists(image_path):
        # 预处理图像
        img = preprocess_image(image_path)

        # 使用 pytesseract 进行 OCR 识别
        ocr_result = pytesseract.image_to_string(img, config="--psm 6")
        print(f"OCR识别结果: {ocr_result}")

        # 识别出以 `?` 分隔的两个数字
        # numbers = ocr_result.split("?")
        # 使用正则表达式匹配数字
        numbers = re.findall(r'\d+', ocr_result)  # 匹配所有数字
        if len(numbers) == 2:
            num1 = numbers[0]  # 第一个数字
            num2 = numbers[1]  # 第二个数字
            return num1, num2
        else:
            print("无法识别两个有效的数字")
            return None, None
    else:
        print(f"图像文件不存在: {image_path}")
    return None, None


def compare_numbers(num1, num2):
    """比较两个数字并打印结果"""
    try:
        x_int, y_int = int(num1), int(num2)
        if x_int > y_int:
            print(f"{num1} > {num2}")
            # ADB 画大于号 ">"
            os.system("adb shell input swipe 400 800 600 1000 50")  # 右上斜线
            os.system("adb shell input swipe 600 1000 400 1200 50")  # 右下斜线
        elif x_int < y_int:
            print(f"{num1} < {num2}")
            # ADB 画小于号 "<"
            os.system("adb shell input swipe 600 800 400 1000 50")  # 左上斜线
            os.system("adb shell input swipe 400 1000 600 1200 50")  # 左下斜线
        else:
            print(f"{num1} = {num2}")
            # ADB 画等号 "="
            os.system("adb shell input swipe 400 900 600 900 50")  # 上横线
            os.system("adb shell input swipe 400 1100 600 1100 50")  # 下横线
    except ValueError:
        print("识别的数字格式无效，无法比较")


if __name__ == "__main__":
    init()
    while True:
        if keyboard.is_pressed("esc"):
            sys.exit()

        time.sleep(0.3)
        # 获取截图
        screenshot_path = os.path.join(screenshot_dir, "screenshot.png")
        take_screenshot(screenshot_path)

        # 定义裁剪区域的坐标 (left, upper, right, lower)
        crop_area = (250, 570, 870, 750)

        # 裁剪图像
        cropped_image_path = crop_image(screenshot_path, crop_area)

        # 识别裁剪区域中的数字并比较
        num1, num2 = recognize_numbers(cropped_image_path)

        if num1 is not None and num2 is not None:
            print(f"识别出的数字: {num1}, {num2}")
            compare_numbers(num1, num2)
        else:
            print("无法识别到两个有效的数字。")
