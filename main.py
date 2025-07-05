import asyncio
import datetime
import os
import pyautogui
import easyocr
import re
import time
import AliyunVoiceService

base_path = r"E:\tmp\screenshot"
image_queue = asyncio.Queue()

def AutoCGSnapshot(base_path):
    cleaned = False
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.lower().endswith(".png"):
                os.remove(os.path.join(root, f))
                cleaned = True
    if not cleaned:
        print("Nothing to clean")

async def SnapShot():
    while True:
        now = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        fp = os.path.join(base_path, f"screenshot{now}.png")
        try:
            img = pyautogui.screenshot()
            img.save(fp)
            await image_queue.put(fp)
            print(f"[Producer] added {fp}")
        except OSError as e:
            print(f"[Producer] Screenshot failed: {e}")
        await asyncio.sleep(1)

async def Process(worker_id):
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
    loop = asyncio.get_running_loop()
    while True:
        fp = await image_queue.get()
        print(f"[Consumer{worker_id}] processing {fp}")
        result = await loop.run_in_executor(None, lambda: reader.readtext(fp, detail=0))
        s = str(result)
        os.remove(fp)
        print(f"[Consumer{worker_id}] deleted file {fp}")
        if re.search(r"下单成功.*?支付", s):
            print("匹配成功！准备拨打电话")
            AliyunVoiceService.VoiceService.main("")  # 填手机号
            AutoCGSnapshot(base_path)
            break
        else:
            print("还没匹配到", s)
        image_queue.task_done()

async def main():
    AutoCGSnapshot(base_path)
    producer = asyncio.create_task(SnapShot())
    consumers = [asyncio.create_task(Process(i)) for i in range(2)]
    await asyncio.gather(producer, *consumers)

if __name__ == "__main__":
    print("确保抢票程序在前台，无其他干扰")
    asyncio.run(main())
