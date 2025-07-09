import logging
import os
import time
import json
import colorlog
import requests
import AliyunVoiceService

from qrclogin.main import qrcmain
logger = logging.getLogger()


def order_brief(_order) -> str:
    return "{}({})\t{}, {}\t{},{}".format(
        _order["shop_name"], _order["status_name"],
        _order["rows"][0]["name"], _order["rows"][0]["extra_data"]["skuSpec"],
        _order["total_desc"], _order["pay_money"] / 100
    )


def GetCookie():
    path = r'./cookie.json'
    if os.path.exists(path):
        logger.info("登陆成功，或者检测到本地有可用的cookie")
    else:
        logger.info("登陆失败或本地没有可用cookie，拉起登录")
        qrcmain()
    logger.info("获取cookie中")
    with open(path, 'r',encoding="utf-8") as f:
        cookie = json.load(f)
        return cookie


def init_logger(log_level: int = logging.INFO) -> None:
    stream = logging.StreamHandler()
    stream.setLevel(logging.DEBUG)
    stream.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)8s [%(asctime)s]%(reset)s "
        "%(blue)s%(message)s ",
        reset=True,
        datefmt="%H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))
    logging.basicConfig(level=log_level, handlers=[stream])

def format_cookie(cookie_dict):
    return "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

#作为计划任务执行
def check_cookies(_cookies):
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cookie': _cookies,
        'dnt': '1',
        'origin': 'https://www.bilibili.com',
        'priority': 'u=1, i',
        'referer': 'https://www.bilibili.com/',
        'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 '
                      'Safari/537.36'
    }
    response = None
    try:
        logger.info("正在验证 cookies 是否可用")
        response = requests.get("https://api.bilibili.com/x/web-interface/nav", headers=headers, timeout=3)
        response.raise_for_status()
        response_body = response.json()
        if response_body["code"] != 0:
            logger.info(response_body)
            logger.error("cookies 无效。")
            return False
        else:
            logger.info(f"cookies 验证成功。欢迎 {response_body['data']['uname']}")
            return True
    except requests.exceptions.RequestException as e:
        logger.error(f"验证登录失败: {e}")
        print(f"验证登录失败: {e}")
        if response is not None:
            logger.debug(response.text)


def get_order_list(_cookies):
    try:
        response = requests.get(
            "https://show.bilibili.com/api/ticket/ordercenter/list?"
            f"pageNum=0&pageSize=20&customer=0&platform=h5&build=0&v={int(time.time() * 1000)}&order_type",
            headers={
                'accept': '*/*',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/x-www-form-urlencoded',
                'dnt': '1',
                'origin': 'https://mall.bilibili.com',
                'priority': 'u=1, i',
                'referer': 'https://mall.bilibili.com/',
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/137.0.0.0 Safari/537.36',
                'cookie': _cookies
            }, timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as _e:
        logger.error(f"请求失败: {_e}")
        return None

def get_valid_cookie():
    dict_cookie = GetCookie()
    cookies = format_cookie(dict_cookie)
    if check_cookies(cookies) == False:
        os.remove('./cookie.json')
        logger.info("删除了本地存储的错误的 cookie")
        dict_cookie = GetCookie()
        cookies = format_cookie(dict_cookie)
        return cookies
    else:
        return cookies


def main():
    init_logger(logging.INFO)
    cookies = get_valid_cookie()
    logger.debug(f"获取到的cookie是{cookies}")
    is_lock_ticket = False
    while is_lock_ticket is False:
        try:
            order_list = get_order_list(cookies)
            if order_list is not None:
                if len(order_list["data"]["list"]) != 0:
                    logger.debug(order_brief(order_list["data"]["list"][0]))
                    #print(order_brief(order_list["data"]["list"][0]))
                for order in order_list["data"]["list"]:
                    # logger.debug(order_brief(order))
                    if order['pay_time_limit'] != 0 and order['order_status'] == 1:
                        logger.info(order)
                        logger.info(order_brief(order_list["data"]["list"][0]))
                        is_lock_ticket = True
                        break
                if is_lock_ticket:
                    break
                else:
                    logger.info("无事发生喵~")
                    time.sleep(20)  # 没有获取到就停止10s
            else:
                logger.error("未能获取订单数据喵~")
        except KeyError as e:
            logger.error(f"呜~响应结构错误：{e}")
        except KeyboardInterrupt:
            logger.critical("Ctrl-C：终止程序了喵！")
            break
        except Exception as e:
            logger.error(f"出现了未知错误，但仍将继续运行{e}")

    if is_lock_ticket:
        logger.info("喵呜！有被锁定的票喵！")
        logger.info("要给你打电话了喵!")
        AliyunVoiceService.VoiceService.main("15901758049") #加你的电话号码
    else:
        logger.info("呜~本次运行没有发现未付款的票票")


if __name__ == '__main__':
    main()
