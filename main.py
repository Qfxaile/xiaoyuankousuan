import os
import subprocess
from PIL import Image
import pytesseract
import time
import threading

current_directory = os.path.dirname(os.path.abspath(__file__))
screenshot_dir = os.path.join(current_directory, "screenshots")


def init():
    """初始化截图目录"""
    if not os.path.exists(screenshot_dir):
        os.mkdir(screenshot_dir)


def take_screenshot(path: str):
    """获取手机截屏,保存到path"""
    screenshot_path = "/sdcard/Qfxaile/screenshot.png"
    subprocess.run(["adb", "shell", "screencap", "-p", screenshot_path])
    subprocess.run(["adb", "pull", screenshot_path, path])
    subprocess.run(["adb", "shell", "rm", screenshot_path])
    print(f"截图保存至 {path}")


def preprocess_image(image):
    """预处理图像，转换为灰度并二值化"""
    img = image.convert("L")  # 转换为灰度图
    img = img.point(lambda x: 0 if x < 128 else 255, "1")  # 二值化处理
    return img
    
    
def crop_image(image_path: str, crop_areas: list):
    """裁剪图像并保存"""
    with Image.open(image_path) as img:
        cropped_images = []
        for idx, area in enumerate(crop_areas):
            cropped_img = img.crop(area)
            cropped_img_path = os.path.join(
                screenshot_dir, f"cropped_area_{idx + 1}.png"
            )
            cropped_img.save(cropped_img_path)
            print(f"裁剪区域 {idx + 1} 的图片保存至 {cropped_img_path}")
            cropped_images.append(cropped_img_path)
        return cropped_images


def recognize_numbers(image_path: str):
    """使用pytesseract识别图片中的数字"""
    if os.path.exists(image_path):
        img = Image.open(image_path)
        img = preprocess_image(img)  # 预处理图像
        # 使用 pytesseract 进行 OCR 识别
        ocr_result = pytesseract.image_to_string(
            img, config="--psm 6 digits"
        )  # 仅识别数字
        print(f"OCR识别结果: {ocr_result}")  # 打印详细的OCR识别结果

        # 提取识别出的数字
        numbers = "".join(filter(str.isdigit, ocr_result))
        if numbers:
            return int(numbers)
    else:
        print(f"图像文件不存在: {image_path}")
    return None


def compare_numbers(x, y):
    """比较两个数字并在屏幕上画出相应的符号。"""
    try:
        x_int, y_int = int(x), int(y)
        if x_int > y_int:
            print(f"{x} > {y}")
            # 画大于号 ">"
            os.system("adb shell input swipe 400 800 600 1000 50")  # 右上斜线
            os.system("adb shell input swipe 600 1000 400 1200 50")  # 右下斜线
        elif x_int < y_int:
            print(f"{x} < {y}")
            # 画小于号 "<"
            os.system("adb shell input swipe 600 800 400 1000 50")  # 左上斜线
            os.system("adb shell input swipe 400 1000 600 1200 50")  # 左下斜线
        else:
            print(f"{x} = {y}")
            # 画等号 "="
            os.system("adb shell input swipe 400 900 600 900 50")  # 上横线
            os.system("adb shell input swipe 400 1100 600 1100 50")  # 下横线
    except ValueError:
        print("数字格式无效。")


def recognize_numbers_in_thread(image_path: str, results: list, index: int):
    """在多线程中执行OCR识别并将结果存储到指定位置"""
    number = recognize_numbers(image_path)
    results[index] = number


if __name__ == "__main__":
    init()
    while True:
        time.sleep(0.3)
        # 获取截图
        screenshot_path = f"{screenshot_dir}/screenshot.png"
        take_screenshot(screenshot_path)

        # 裁剪图像的两个区域，定义区域的坐标 (left, upper, right, lower)
        crop_areas = [
            (250, 520, 450, 720),  # 第一个区域
            (630, 520, 830, 720),  # 第二个区域
        ]

        # 裁剪图像
        cropped_images = crop_image(screenshot_path, crop_areas)

        # 对裁剪后的图片进行数字识别并比较大小
        if len(cropped_images) >= 2:
            # 用于存储识别结果
            ocr_results = [None, None]
            threads = []

            # 创建线程来并发识别每个裁剪区域的图像
            for i, image in enumerate(cropped_images):
                thread = threading.Thread(
                    target=recognize_numbers_in_thread, args=(image, ocr_results, i)
                )
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            number1, number2 = ocr_results

            if number1 is not None and number2 is not None:
                print(f"裁剪区域 1 中识别出的数字: {number1}")
                print(f"裁剪区域 2 中识别出的数字: {number2}")
                compare_numbers(number1, number2)
            else:
                print("无法识别两个数字中的一个或多个。")
