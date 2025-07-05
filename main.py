import pyautogui
import time
import datetime
import easyocr
import re
import os
import AliyunVoiceService
import logging

def GetSnapshot():
        path = r"E:\tmp\screenshot"
        screenshot = pyautogui.screenshot()
        now = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        now_str = str(now)
        screenshot.save(f"{path}\\screenshot{now_str}.png")
        file_path = f"{path}\\screenshot{now_str}.png"
        print(f"要保存的路径是{file_path}")
        return file_path

def OCRSnapshot(file_path):
    reader = easyocr.Reader(['ch_sim', 'en'])
    result = reader.readtext(file_path,detail=0)
    return result

def AutoCGSnapshot(base_path):
    Clean_Status = False
    for root_dir, _, files in os.walk(base_path):
        for fname in files:
            if not fname.lower().endswith((".png")):
                continue
            full_path = os.path.join(root_dir, fname)
            os.remove(full_path)
            print(f"删掉了{full_path}")
            Clean_Status = True
    if Clean_Status == False:
        print("Nothing to clean")


if __name__ == "__main__":
    print("请保证抢票程序在前台，并确保前台干净，无其他程序干扰OCR！")
    base_path = r"E:\tmp\screenshot"
    AutoCGSnapshot(base_path)  # 初始化文件夹，删掉上一次使用的内容
    while True:
        file_path = GetSnapshot() #测试时注释
        #file_path = r"E:\tmp\screenshot\2.png" #1是失败案例，2是成功案例
        result = OCRSnapshot(file_path)
        str_result = str(result)
        print(result) #调试用
        logging.info(str_result) #调试用
        match = re.search(r"下单成功.*?支付",str_result)
        if match:
            print("抢到了喵，要开始给你打电话了喵",match.group())
            DialNumber="15901758049"
            # 要被拨打电话的号码，如果有多个建议用List，然后自己改一下VoiceService的main方法
            # 调用语音通知服务
            str_DialNumber = str(DialNumber)
            result = AliyunVoiceService.VoiceService.main(str_DialNumber)
            print(result)
            AutoCGSnapshot(base_path)
            break
        else:
            # 觉得烦人可以注释掉
            print("还没有喵，请耐心等待喵")
            print(str_result)

