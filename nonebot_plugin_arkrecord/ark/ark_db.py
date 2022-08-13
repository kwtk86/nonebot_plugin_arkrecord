import json, time, requests as req, sqlite3 as sq, csv
import xlsxwriter as xlw, urllib
from math import ceil
from .ark_setting import *
from nonebot.log import logger

""" 
读写数据库
"""
__all__ = ["get_user_uid", "write_token2db", "read_token_from_db", "export_record2file", "url_db_writer", "ArkDBReader"]

def get_user_uid(token:str):
    """_summary_
    根据token从官网获取uid和昵称
    Args:
        token (str): _description_
    Returns:
        _type_: _description_
    """
    #两个服务器的请求头不一样
    base_url = 'https://as.hypergryph.com/u8/user/info/v1/basic'
    user_info = {}
    #官服

    payload = '''
        {{
            "appId":1,
            "channelMasterId":1,
            "channelToken":{{
                "token":"{}"
            }}
        }}'''.format(token)
    content = req.post(base_url, payload).content#访问官服
    page_content = json.loads(content)
    try:
        if page_content['status']!=0:#b服
            token = urllib.parse.unquote(token)
            payload = {'token':token}
            content = req.post(base_url, payload).content
            page_content = json.loads(content)
            assert page_content['status'] == 0, "无效token"
        user_info_source = page_content.get('data')
        user_info['uid'] = user_info_source.get('uid')
        user_info['name'] = user_info_source.get('nickName')
        user_info['channelMasterId'] = user_info_source.get('channelMasterId')
    except:
        raise RuntimeError("无效token")
    return user_info

def write_token2db(db:sq.Connection, qq_id:str, token:str):
    """_summary_
    向表中写入用户token
    """

    response = get_user_uid(token)
    try:
        cursor = db.cursor()
        sql = f"replace into {qq_user_table}\
            ({qq_id_field}, {user_id_field}, {user_name_field}, {ark_token_field}, {channel_field}) \
            values \
            (\'{qq_id}\', \'{response['uid']}\', \'{response['name']}\', \'{token}\', {response['channelMasterId']});"
        cursor.execute(sql)
        db.commit()
        return
    except:
        raise RuntimeError("保存token失败")
    # except Exception as e:
    #     logger.warning(e)
    #     return "保存token失败"

def write2xlsx(file_path:str, headers:list, info:list):
    wb = xlw.Workbook(file_path)
    ws = wb.add_worksheet()
    #写第一行
    row, col = 0, 0
    ws.write_row(0, 0, headers)
    row+=1
    for item in info:
        ws.write_row(row, 0, item)
        row+=1
    wb.close()

def export_record2file(db:sq.Connection, info:list, qq_id:str, private_tot_pool_info:dict):
    try:
        db_reader = ArkDBReader(db, info[2], info[0], float('inf'), 'all', private_tot_pool_info)
        res = db_reader.export_query()
        headers = ['寻访编号', 'uid', '卡池', '干员', '星级',
                '是否为新干员','寻访时间','限定类型']
        out_file_name = f'ark_record_{qq_id}_{info[0]}.xlsx'
        out_file_path = os.path.join(output_csv_dir, out_file_name)
        write2xlsx(out_file_path, headers, res)
        return out_file_path
    except Exception as e:
        raise RuntimeError("获取/导出记录失败 " + str(e))          
    
def read_token_from_db(db:sq.Connection, qq_id:str):
    """_summary_
    获取用户的token
    Args:
        user_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        cursor = db.cursor()
        sql = f"select * from {qq_user_table} \
            where {qq_id_field} = \'{qq_id}\';"
        cursor.execute(sql)
        #user_name token user_id channel
        res = cursor.fetchone()[1:]
    except:
        raise RuntimeError("获取已储存的token失败")
    assert res, '请先使用 方舟抽卡帮助 查看帮助或使用 方舟抽卡token + 你的token 进行设置'
    return res

def url_db_writer(db:sq.Connection, draw_info_list:list, user_id:str, private_tot_pool_info:dict):
    """_summary_
    将单次爬取到的寻访记录写入数据库
    Args:
        db (sq.Connection): _description_
        draw_info_list (list): _description_
        user_id (str): _description_
    """
    # logger.info(tot_pool_info)
    try:
        base_sql = f'replace into {ark_record_table} \
            ({record_id_field}, {timestamp_field}, {user_id_field}, \
                {pool_name_field}, {char_name_field}, {star_field}, {is_new_field}, {exclusive_field}) values '
        for draw in draw_info_list:
            base_draw_id = draw['ts']
            draw_pool = draw['pool']
            char_info = draw['chars']
            try:
                
                exclusive_name =  draw_pool if private_tot_pool_info[draw_pool]['is_exclusive'] else exclusive_common_name
            except:
                raise RuntimeError("pool" + draw_pool)
            for i, character in enumerate(char_info):              #为方便排序，这里是的id反着存的
                draw_id = "{}_{}".format(base_draw_id, i)#
                time_local = time.localtime(base_draw_id)
                dt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)      
                value_sql = f"(\'{draw_id}\', \'{dt}\', \'{user_id}\', \'{draw_pool}\', \
                    \'{character['name']}\', {character['rarity']+1}, {character['isNew']}, \'{exclusive_name}\'),"
                base_sql += value_sql
        base_sql = base_sql[:-1]+';'
        cursor = db.cursor()
        cursor.execute(base_sql)
        db.commit()
    except Exception as e:
        logger.error(e)
        if 'pool' in str(e):
            raise RuntimeError("寻访记录中有未知的卡池,请使用 方舟卡池更新 命令尝试更新卡池", )
        raise RuntimeError("数据库写入失败")    
    
class ArkDBReader():
    """
    数据库读取类
    """
    def __init__(self, db:sq.Connection, 
                 user_id:str,
                 user_name:str,
                 max_record_count:str,
                 target_pool_name:str,
                 private_tot_pool_info:dict) -> None:
        self.db = db 
        self.user_id = user_id 
        self.user_name = user_name
        self.max_record_count = max_record_count
        self.target_pool_name = target_pool_name
        self.private_tot_pool_info = private_tot_pool_info
        #查询用cursor
        self.cursor = self.db.cursor()
        #记录次数
        self.max_record_count = max_record_count
        if self.max_record_count == float('inf'):
            self.max_record_count = self.get_record_count()
        #视图管理
        self.view_name =  'v{}'.format(self.user_id)
        self.check_view()
        self.create_view()
        #查询结果
        self.pool_in_view = self.get_pool_in_view()
        self.query_result = {}
        
    def get_pool_in_view(self):
        "获取视图中包含的卡池"
        base_sql = f"select distinct {exclusive_field} from {self.view_name}"
        self.cursor.execute(base_sql)
        tmp = [item[0] for item in self.cursor.fetchall()]
        return tmp
        
    def get_record_count(self):
        """_summary_
        获取有效记录数量
        Returns:
            _type_: _description_
        """
        count_sql = f"select count(*) from {ark_record_table} where {user_id_field} = {self.user_id}" 
        self.cursor.execute(count_sql)
        return self.cursor.fetchone()[0] 
    
    def check_view(self):
        """_summary_
        处理完成后删除视图
        Args:
            cursor (_type_): _description_
            view_name (_type_): _description_
            check_type (_type_): _description_
        """
        drop_view_sql = "drop view if exists {}".format(self.view_name)
        self.cursor.execute(drop_view_sql)
        
    def create_view(self):
        """_summary_
        创建查询视图
        """
        #查询所有卡池情况
        if self.target_pool_name=="all":
            create_view_sql = f"create view {self.view_name} as \
                                select *\
                                from {ark_record_table} \
                                where {user_id_field} = \'{self.user_id}\' order by {timestamp_field} desc \
                                limit {self.max_record_count};\
                                "
            # logger.info(create_view_sql)
        else:#旧版单卡池查询用
            create_view_sql = f"create view {self.view_name} as \
                                select *\
                                from {ark_record_table} \
                                where {user_id_field} = \'{self.user_id}\' and {pool_name_field} = \'{self.target_pool_name}\'\
                                    limit {self.max_record_count};"
        self.cursor.execute(create_view_sql)
    
    
    def export_query(self):
        sql = f"select * from {self.view_name}"
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        self.finish()
        return res
    
    def query_all_items(self):
        def filter_star6char(info):#判断是否为六星
            return info[2]==6
        def filter_newchar(info):#判断是否为新角色
            return info[3]
        
        star6char_query_param = {
            'op_type':'六星干员',
            'result_name':'star6char_info',
            'filter_func':filter_star6char,
            'cost_statis':True,
        }
        
        newchar_query_param = {
            'op_type':'新干员',
            'result_name':'newchar_info',
            'filter_func':filter_newchar,
            'cost_statis':False,
        }
        
        self.pool_query()
        self.star_query()
        self.shuiwei_query()
        self.char_query(newchar_query_param)
        self.char_query(star6char_query_param)

        self.frequent_query()
        self.finish()
           
    def pool_query(self):
        #查询卡池信息
        if self.target_pool_name == 'all':
            pool_name_sql = f"select {pool_name_field}, count(*) from \
                {self.view_name}\
                group by {pool_name_field} \
                order by count(*) desc"
            self.cursor.execute(pool_name_sql)
            pool_info = list(self.cursor.fetchall())[:max_pool_count][::-1]
            tmp_lst = {'desc':[], 'count':[], 'text':""}
            for pool in pool_info:
                tmp_lst['desc'].append(f"{pool[0].split(' ')[0].strip()}")#把复刻和常规算作一个，不然放不下了 todo:自适应图片宽度
                tmp_lst['count'].append(pool[1])
                tmp_lst['text'] += f"{pool[0]}:{pool[1]}抽\n\n"
            self.query_result['pool_info'] = tmp_lst
        else:
            self.query_result['pool_info'] = {'desc':[self.target_pool_name],'count':[self.max_record_count]}
    

    def star_query(self):
        """查询星级分布"""
        star_sql = f"select {star_field}, count(*) from \
            {self.view_name} group by {star_field}"
        self.cursor.execute(star_sql)
        star_info = list(self.cursor.fetchall())
        star_info.sort()
        tmp_lst = {'desc':[], 
                   'count':[], 
                   'avg':[],
                   'text':f'',
                   'title':f'星级分布'}
        for star in star_info:
            tmp_lst['desc'].append(f"{star[0]}星")
            tmp_lst['count'].append(star[1])
            avg = self.max_record_count/star[1]
            tmp_lst['avg'].append(avg)
            star_desc = f"{star[1]}个{star[0]}星"
            tmp_lst['text'] += f"{star_desc:8}{avg:.1f}抽/个\n\n"
        self.query_result['star_info'] = tmp_lst
    
    def char_query(self, query_params:dict):
        """获取获得的新角色或六星角色信息"""
        #首先获取所有卡池
        tmp_info = {'chars':[], 'count':0}
        #遍历普通池和每个限定池
        for pool in self.pool_in_view:
            char_sql = f"select {char_name_field}, {timestamp_field}, {star_field}, {is_new_field}, {pool_name_field}, {record_id_field} \
                from {self.view_name} \
                where {exclusive_field} = \'{pool}\'    \
                order by {record_id_field} desc"
            self.cursor.execute(char_sql)
            char_info_lst = list(self.cursor.fetchall())
            last_mark_idx = 1e20#上一次获得六星时的序号
            char_info_lst = char_info_lst[::-1]
            for idx, char_info in enumerate(char_info_lst):#反过来遍历，以统计抽数
                if query_params['filter_func'](char_info):#如果是新角色或者六星角色
                    indi_info = {}
                    #年月日
                    ymd = char_info[1].split(' ')[0].strip().split('-')
                    year, month, day  = ymd[0], ymd[1], ymd[2]
                    indi_info['date'] = char_info[1]
                    indi_info['desc'] = f"于{year}年{month}月{day}日\n{char_info[4]}/{pool}\n"
                    indi_info['name'] = f"{char_info[0]}"
                    indi_info['star'] = char_info[2]
                    indi_info['pool'] = char_info[4]
                    indi_info['record_id'] = char_info[5]
                    # indi_info['date'] = idx#用于排序十连
                    if query_params['cost_statis']:
                        #统计于最近第几抽获得
                        if idx-last_mark_idx<0:
                            indi_info['desc'] += f"花费至少 {idx + 1} 抽获得"
                        else:
                            indi_info['desc'] += f"花费 {idx - last_mark_idx} 抽获得"
                        last_mark_idx = idx    
                    else:
                        #如果不统计花费的抽数，就统计最近几抽           
                        indi_info['desc'] += f"该类池最近第{len(char_info_lst)-idx}抽获得"
                    tmp_info['chars'].append(indi_info)                          
                    tmp_info['count'] += 1
                                   
        if not tmp_info['chars']:
            tmp_info['describe'] = f"没有获得{query_params['op_type']}\n"
        else:
            tmp_info['chars'].sort(key = lambda item:item['record_id'], reverse = True)
            tmp_info['chars'] = tmp_info['chars'][:max_char_count]
            tmp_info['describe'] = f"获得了{len(tmp_info['chars'])}个{query_params['op_type']}\n"
        self.query_result[query_params['result_name']] = tmp_info

    def shuiwei_query(self):
        """查询卡池水位情况"""
        tmp_info = {'text':'', 'title':f"卡池水位情况"}
        for pool in self.pool_in_view:
            char_sql = f"select {char_name_field}, {timestamp_field}, {star_field}, {record_id_field} \
                from {self.view_name} \
                where {exclusive_field} = \'{pool}\'    \
                order by {record_id_field} desc"
            self.cursor.execute(char_sql)
            char_info_lst = list(self.cursor.fetchall())
            for i, char in enumerate(char_info_lst):
                if char[2] == 6:#是六星
                    tmp_info['text'] += f"{pool}：{i+1}抽\n\n"
                    break
            else:
                tmp_info['text'] += f"{pool}：至少{len(char_info_lst)}抽\n\n"
        self.query_result['shuiwei_info'] = tmp_info

    def frequent_query(self, limit = 5):
        """_summary_
        预留 查询获得次数最多的干员情况
        Args:
            limit (int, optional): _description_. Defaults to 5.
        """
        frequent_sql = f"select {char_name_field}, count(*) from\
            {self.view_name} \
            group by {char_name_field}\
            order by count(*)\
            desc\
            limit {limit}"
        self.cursor.execute(frequent_sql)
        fre_info = self.cursor.fetchall()
        tmp_lst = []
        for fre_char in fre_info:
            desc = f"抽到了{fre_char[1]}次{fre_char[0]}"#这边格式要优化
            tmp_lst.append(desc)
        self.query_result['frequent'] = tmp_lst
    
    
    
    
    def finish(self):
        """查询完成后删除视图"""
        self.check_view()
        
    def get_img_wh(self, 
                   base_h = base_img_h,
                   base_w = base_img_w):
        #根据六星及新干员数量计算输出的图像的高度
        mmax = max(self.query_result['star6char_info']['count'],
                   self.query_result['newchar_info']['count'])
        char_line_cnt = ceil(mmax/2)#可以排列几行
        base_h += int(1.2*char_title_p['fsize'])
        base_h += get_char_drawer_h(char_line_cnt)
        base_h += int(bottom_img_p['h'])
        base_h += int(base_img_h*0.03)
        char_drawer_p['h_int'] = char_drawer_p['h'](char_line_cnt)
        return (base_w, base_h), char_line_cnt
    
  