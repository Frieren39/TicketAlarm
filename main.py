import asyncio
import datetime
import os
import pyautogui
import easyocr
import re
import AliyunVoiceService
import psutil

base_path = r"E:\tmp\screenshot"
image_queue = asyncio.Queue()

def AutoCGSnapshot(base_path):
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.lower().endswith(".png"):
                os.remove(os.path.join(root, f))
    print("Nothing to clean")

def KillMSPrint():
    target = "mspaint.exe"
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == target:
                print(f"检测到 MS Paint，进程 PID={proc.pid}，正在关闭...")
                proc.kill()
                print("MS Paint 已关闭")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

async def WatchAndKillMspaint(interval=2):
    while True:
        await asyncio.sleep(interval)
        KillMSPrint()

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
        await asyncio.sleep(10)

async def Process(worker_id):
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
    loop = asyncio.get_running_loop()
    pattern = re.compile(r"(锁票成功|锁票中|下单成功.*?支付|下单成功|锁票|支付)")
    while True:
        fp = await image_queue.get()
        print(f"[Consumer{worker_id}] processing {fp}")
        result = await loop.run_in_executor(None, lambda: reader.readtext(fp, detail=0))
        s = str(result)
        os.remove(fp)
        print(f"[Consumer{worker_id}] deleted file {fp}")
        if pattern.search(s):
            print("匹配成功！准备拨打电话")
            AliyunVoiceService.VoiceService.main("15901758049")
            AutoCGSnapshot(base_path)
            break
        else:
            print("还没匹配到", s)
        image_queue.task_done()

async def main():
    AutoCGSnapshot(base_path)
    tasks = [
        asyncio.create_task(SnapShot()),
        asyncio.create_task(Process(0)),
        asyncio.create_task(Process(1)),
        asyncio.create_task(WatchAndKillMspaint(2))
    ]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for t in tasks:
        if not t.done():
            t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    print("确保抢票程序在前台，无其他干扰")
    asyncio.run(main())
