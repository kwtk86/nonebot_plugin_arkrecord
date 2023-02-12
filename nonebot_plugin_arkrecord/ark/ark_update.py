import os, sys, json
import requests as req
from .ark_setting import operator_profile_dir, tot_pool_info_file, get_tot_pool_info, tot_pool_info, arkgacha_db, write_log2file
from .ark_db import rewrite_db
from nonebot.log import logger
from nonebot.plugin import on_keyword, on_command
from nonebot.adapters.onebot.v11 import Bot, Event, PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from bs4 import BeautifulSoup as bs
from collections import defaultdict as ddict

__all__ = ['ark_update_handle', 'ark_manual_update_handle', 'ark_db_rewrite_handle']

def get_prts_pool_info(pinfo:dict):
    """获取prts中的卡池信息"""
    prts_url = "https://prts.wiki/w/%E5%8D%A1%E6%B1%A0%E4%B8%80%E8%A7%88/%E9%99%90%E6%97%B6%E5%AF%BB%E8%AE%BF"
    prts_res = req.get(prts_url)
    prts_content = prts_res.content
    prts_soup = bs(prts_content, 'lxml') 
    #限定
    group_type_divs = prts_soup.find_all('table', class_ = 'wikitable mw-collapsible fullline logo')
    group_types = [1, 0]#is_exclusive
    for g_type, type_div in zip(group_types, group_type_divs):
        trs = type_div.find_all('tr')
        for tr in trs[1:]:
            try:
                td0 = tr.find_all('td')[0]
                #不知道为什么prts在卡池名称前面加上了 寻访模拟/
                pname = td0.find('a').attrs['title'].strip().strip("寻访模拟/")
                pinfo[pname] = {'is_exclusive':True if g_type else False}#判断是否为限定
            except:
                continue
    return pinfo

def update_pool_info():
    """更新卡池信息"""
    with open(tot_pool_info_file, 'r', encoding='utf-8') as fj:
        try:
            pool_info = json.load(fj)
        except:#防止出bug为空
            pool_info = {}
    #从prts获取卡池信息
    pool_info = get_prts_pool_info(pool_info)
    with open(tot_pool_info_file, 'w', encoding='utf-8') as fj:
        json.dump(pool_info, fj, ensure_ascii=False)
    
def read_cur_profiles():
    """获取已有头像对应的干员名称"""
    pro_names = ddict(int, {p.split('.')[0].split('_')[1]:1 for p in os.listdir(operator_profile_dir)})
    return pro_names

def update_by_prts_profile_info(names):
    """对比prts中的干员头像和已有头像，进行更新"""
    base_url = r'https://prts.wiki/w/PRTS:%E6%96%87%E4%BB%B6%E4%B8%80%E8%A7%88/%E5%B9%B2%E5%91%98%E7%B2%BE%E8%8B%B10%E5%A4%B4%E5%83%8F'
    updated = [False,[]]
    prts_info = req.get(base_url).content
    prts_soup = bs(prts_info, 'lxml')
    ops = prts_soup.findAll('div', class_='mw-parser-output')
    for op in ops[0].find_all('a', class_='image'):
        op_name = op.find('img').attrs['alt'].split(' ')[1].split('.')[0]
        if not names[op_name]:#如果没有这个头像
            img_info_page = 'https://prts.wiki/' + op.attrs['href']
            img_info = req.get(img_info_page).content
            img_soup = bs(img_info, 'lxml')
            img_div = img_soup.find('div', class_ = 'fullImageLink')
            img_name = 'profile_' + img_soup.find('h1', class_ = 'firstHeading').string.split(' ')[1].strip()
            img_page = 'https://prts.wiki/' + img_div.contents[0].attrs['href']
            img = req.get(img_page).content
            with open(operator_profile_dir +"/" + img_name, 'wb') as fp:
                fp.write(img)
            logger.info("保存" + img_name)
            updated[0] = True
            updated[1].append(op_name)
    return updated

def update_profile():
    #更新干员头像信息
    pronames = read_cur_profiles()
    updated = update_by_prts_profile_info(pronames)
    return updated

ark_update_event = on_keyword(['方舟卡池更新'], priority = 50)
@ark_update_event.handle()
async def ark_update_handle(bot: Bot, event: Event):
    try:
        update_pool_info()
        updated = update_profile()
        if updated[0]:
            op_names = ' '.join(updated[1])
            info = f"更新成功！获取到干员 {op_names} 的头像及新卡池信息"
        else:
            info = "成功尝试了更新，但是没有获取到新的头像（虽然可能获取到了新的卡池，但是作者太懒，懒得写判断了）"
    except Exception as e:
        write_log2file('warning', f"{e}, 更新卡池失败")
        logger.error(str(e) + "获取更新失败！")
        await ark_update_event.finish(\
            Message(\
                f'[CQ:at,qq={event.get_user_id()}]{str(e) + "获取更新失败！"}'\
                )
            )
    await ark_update_event.finish(\
        Message(\
            f'[CQ:at,qq={event.get_user_id()}]{info}'\
            )
        )

"""手动更新卡池系列"""
def manual_update_pool(pool_name:str, is_exclusive:bool):
    """_summary_
    获取已有卡池
    Args:
        pool_name (sq.Connection): 卡池名称
        is_exclusive (bool): 是否为限定卡池
    """
    pool_info = None
    with open(tot_pool_info_file, 'r', encoding='utf-8') as fjread:
        try:
            pool_info = json.load(fjread)
        except: # 防止出bug为空
            pool_info = {}
    pool_info[pool_name] = {'is_exclusive': is_exclusive}
    # 写回
    with open(tot_pool_info_file, 'w', encoding='utf-8') as fjwrite:
        json.dump(pool_info, fjwrite, ensure_ascii=False)
    

ark_manual_update_event = on_keyword(["手动添加卡池"], priority = 80)
@ark_manual_update_event.handle()
async def ark_manual_update_handle(bot: Bot, event: Event):
    message_split = str(event.get_message()).strip().split('|')
    if len(message_split) != 4:
        await ark_manual_update_event.finish('指令不符合格式，请重新输入')
    """检查指令是否可用"""
    # 指令是否合法
    if message_split[0] != '手动添加卡池':
        await ark_manual_update_event.finish('指令不符合格式，请重新输入')
    # 限定术语是否合法
    if message_split[2] not in ['限定', '非限定']:
        await ark_manual_update_event.finish('限定类型错误，请重新输入')
    else:
        message_split[2] = True if message_split[2] == "限定" else False
    # 是否加入确认
    if not message_split[3].isnumeric() or int(message_split[3]) != int(event.get_user_id()) :
        await ark_manual_update_event.finish('最终确认有误，请重新输入')
    # 获取已有卡池
    try:
        manual_update_pool(message_split[1], message_split[2])
    except Exception as e:
        write_log2file('warning', f"{e}, 添加卡池失败")
        logger.error(str(e) + "添加卡池失败！")
        await ark_update_event.finish(\
            Message(\
                f'[CQ:at,qq={event.get_user_id()}]{str(e) + "添加卡池失败！"}'\
                )
            )
    await ark_update_event.finish(\
        Message(\
            f'[CQ:at,qq={event.get_user_id()}]{"添加卡池成功！"}'\
            )
        )   

"""
为避免限定类型出错，添加数据库卡池信息重置功能
-------------------
REWRITE OF DATABASE
SPONSORED BY KANBE KOTORI
-------------------
"""
ark_db_rewrite_event = on_keyword(["方舟数据库刷新"], priority = 80)
@ark_db_rewrite_event.handle()
async def ark_db_rewrite_handle(bot: Bot, event: Event):
    tot_pool_info
    try:
        with open(tot_pool_info_file, 'r', encoding='utf-8') as fj:
            pool_info = json.load(fj)
            rewrite_db(arkgacha_db, pool_info)
    except:
        pass
    await ark_update_event.finish(\
    Message(\
        f'[CQ:at,qq={event.get_user_id()}]{"数据库刷新成功！"}'\
        )
    )   