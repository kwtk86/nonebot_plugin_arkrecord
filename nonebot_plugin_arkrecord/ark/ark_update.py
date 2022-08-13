import os,sys,json
import requests as req
from .ark_setting import operator_profile_dir, tot_pool_info_file, get_tot_pool_info, tot_pool_info
from nonebot.log import logger
from nonebot.plugin import on_keyword
from nonebot.adapters.onebot.v11 import Bot, Event, PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from bs4 import BeautifulSoup as bs
from collections import defaultdict as ddict

__all__ = ['ark_update_handle', 'ark_update_handle']

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
                pname = td0.find('a').attrs['title'].strip()
                pinfo[pname] = {'is_exclusive':True if g_type else False}
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
    pool_info = get_prts_pool_info(pool_info)
    with open(tot_pool_info_file, 'w', encoding='utf-8') as fj:
        json.dump(pool_info, fj, ensure_ascii=False)
    # get_tot_pool_info(tot_pool_info_file)
    
    
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

ark_update_event = on_keyword(['方舟卡池更新'],priority=50)
@ark_update_event.handle()
async def ark_update_handle(bot: Bot, event: Event):
    try:
        update_pool_info()
        updated = update_profile()
        if updated[0]:
            op_names = ' '.join(updated[1])
            info = f"更新成功！获取到干员 {op_names} 的头像及新卡池信息"
        else:
            info = "成功尝试更新，但是没有获取到新的头像"
    except Exception as e:
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