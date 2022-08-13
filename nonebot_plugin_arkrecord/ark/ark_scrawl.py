import requests as req, time, json, urllib
from typing import Literal
from .ark_drawer import ArkImage
from .ark_db import *
from .ark_setting import *
from .ark_utils import *

from nonebot.log import logger

__all__ = ["url_scrawler", "user_ark_analyser"]

# def check_pool_name(pool_name):
#     """_summary_
#     检查卡池名称是否正确 目前用不到了
#     deprecated
#     """
#     if pool_name not in tot_pool_info.keys():  
#         error_info = "错误的卡池名称！现有卡池名称如下:\n"
#         pool_name_string = '\n'.join(tot_pool_info[:-1])
#         return False, error_info + pool_name_string
#     return True, ""
  
def url_scrawler(token:str, channel:Literal[1,2]):
    """_summary_
    爬取官网抽卡记录
    Args:
        token (str): _description_

    Returns:
        _type_: _description_
    """
    token = urllib.parse.quote(token)#存的是
    base_url = "https://ak.hypergryph.com/user/api/inquiry/gacha?token="+token
    params = {'channelId':channel}
    draw_info_list = []
    try:
        for i in range(1,11):
            params['page'] = str(i)
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            res_page = req.get(base_url, headers = headers, params = params)
            logger.success(res_page.url)
            res_page_text = json.loads(res_page.text)
            page_data = res_page_text['data']['list']
            if not page_data:
                break
            draw_info_list.extend(page_data)
        warning_info = "未获取到有效寻访信息。正在返回缓存信息" if not draw_info_list else ""
        return warning_info, draw_info_list
    except Exception as e:
        warning_info = "未成功访问寻访页面，token可能已经失效。正在返回缓存信息" if not draw_info_list else ""
        return warning_info, []

def user_ark_analyser(db:sq.Connection, user_info:str, max_read_count = float('inf'), pool_name = "all"):
    """_summary_
    抽卡分析主函数
    Args:
        db (pm.Connection): _description_
        user_info (str): _description_
        max_read_count (_type_, optional): _description_. Defaults to float('inf').

    Returns:
        _type_: _description_
    """
    # logger.info(user_info)
    user_name, token, user_id, channel = user_info
    # 获取官网寻访记录
    warning_info, record_info_list = url_scrawler(token, channel)
    yield warning_info
    private_tot_pool_info = get_tot_pool_info()

    if record_info_list:
        url_db_writer(db, record_info_list, user_id, private_tot_pool_info)
    # 读数据库
    db_reader = ArkDBReader(db, user_id, user_name, max_read_count, pool_name, private_tot_pool_info)
    db_reader.query_all_items()
    query_info = db_reader.query_result
    # 生成图片
    aig = ArkImage(query_info, user_id, db_reader.get_img_wh())
    aig.draw_all(user_name, db_reader.max_record_count)
    aig_save_path_desc = aig.save()  
    yield aig_save_path_desc
