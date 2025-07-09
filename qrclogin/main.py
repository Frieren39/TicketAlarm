from qrclogin import login
from qrclogin import utils


def qrcmain():
    utils.save_json_file(path="./cookie.json", data=login.get_cookie())

