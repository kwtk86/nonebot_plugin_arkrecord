import requests as req, time, json, urllib
from typing import Literal
from .ark_setting import *
from .ark_utils import *
from .ark_db import *

from nonebot.log import logger

__all__ = ['download_file']

def download_file(url):
    # 直链下载群文件中的抽卡记录
    f = req.get(url)
    fpath = ""
    with open(fpath, "wb") as code:
        logger.info(f.content)
        code.write(f.content)
    return fpath

def top_csv2db(fpath, user_id):
    pass