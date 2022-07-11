
from nonebot.log import logger
from nonebot.plugin import on_keyword
from nonebot.adapters.onebot.v11 import Bot, Event, PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from .ark_db import *
from .ark_scrawl import *
from .ark_setting import *

user_token_event = on_keyword(['方舟抽卡token', '方舟寻访token'],priority=50)
@user_token_event.handle()
async def user_token_handle(bot: Bot, event: Event):
    qq_id = event.get_user_id()
    user_token = str(event.get_message()).split(' ')[1].strip()
    try:
        write_token2db(arkgacha_db, qq_id, user_token)
    except Exception as e:
        logger.error(str(e))
        await user_analysis_event.finish(\
            Message(\
                '[CQ:at,qq={}]{}'.format(event.get_user_id(), str(e))\
                )
            )    
    await user_token_event.finish(\
        Message(\
            f'[CQ:at,qq={qq_id}] {"成功保存token"}'\
            )
        )

user_export_event = on_keyword(['方舟抽卡导出', '方舟寻访导出'],priority=50)
@user_export_event.handle()
async def user_export_handle(bot: Bot, event: Event):
    qq_id = event.get_user_id()
    if isinstance(event, PrivateMessageEvent):#gocq不支持私聊传文件
        await user_analysis_event.finish(\
            Message(\
                f'[CQ:at,qq={qq_id}]暂不支持私聊传文件，可以创建单人群聊后使用命令'\
                )
            )
    try:
        user_info = read_token_from_db(arkgacha_db, qq_id)
        response = export_record2file(arkgacha_db, user_info, qq_id)
    except Exception as e:
        logger.error(e)
        await user_analysis_event.finish(\
            Message(\
                f'[CQ:at,qq={qq_id}]{str(e)}'\
                )
            )
    await bot.upload_group_file(
        group_id = event.group_id,
        file =  response,
        name = response.split(os.sep)[-1],
    )  




user_analysis_event = on_keyword(['方舟抽卡分析','方舟寻访分析'],priority=50)
@user_analysis_event.handle()
async def user_analysis_handle(bot: Bot, event: Event):
    qq_id = event.get_user_id()    
    try:
        user_info = read_token_from_db(arkgacha_db, qq_id)
        max_record_count = parse_message(event.get_message())
        ana_gnrt = user_ark_analyser(arkgacha_db, user_info, max_record_count)
        warning_info = next(ana_gnrt)
        if warning_info:
            await user_analysis_event.send(\
                Message(\
                    '[CQ:at,qq={}]{}'.format(event.get_user_id(), warning_info)\
                    )
                )
        img_path = next(ana_gnrt)

        image_file_path = "file:///" + img_path
        message_CQ = Message(f'[CQ:at,qq={event.get_user_id()}]')
        message_img = MessageSegment.image(image_file_path),
    except Exception as e:
        logger.warning(str(e))#这个warning会蜜汁报错 还没解决这个问题
        await user_analysis_event.finish(\
            Message(\
                '[CQ:at,qq={}]{}'.format(event.get_user_id(), str(e))\
                )
            )
    await user_analysis_event.finish(message_CQ + message_img)


ark_help_event = on_keyword(['方舟抽卡帮助','方舟寻访帮助'],priority=50)
@ark_help_event.handle()
async def ark_help_handle(bot: Bot, event: Event):
    image_file_path = "file:///" + help_img_path
    logger.info(image_file_path)
    message_CQ = Message(
        f'[CQ:at,qq={event.get_user_id()}]\n欢迎使用明日方舟寻访分析插件！\
                \n帮助请参看以下图片。图片中涉及的网址为:\
                \n官网：https://ak.hypergryph.com/\
                \n官服token获取地址：https://as.hypergryph.com/user/info/v1/token_by_cookie\
                \nB服token获取地址：https://web-api.hypergryph.com/account/info/ak-b\n'
    )
    try:
        message_img = MessageSegment.image(image_file_path),
        msg = message_CQ + message_img
    except:
        msg = message_CQ + Message('获取抽卡帮助资源出错！')
    await user_analysis_event.finish(msg)

def parse_message(message:str):#todo:修改为正则匹配
    """_summary_
    解析抽卡分析的输入参数
    Args:
        message (str): _description_

    Returns:
        _type_: _description_
    """
    m_lst = str(message).split()
    if len(m_lst) == 1:
        return float('inf')
    elif len(m_lst) == 2:
        #如果长度为2 则必须
        item1, item2 = m_lst
        assert item1.isdigit() + item2.isdigit() == 1, "参数不合法"
        return int(item2 if item2.isdigit() else item1)
    raise RuntimeError("参数过多！")