
import os, sqlite3 as sq
# # from nonebot_plugin_arkrecord.ark.ark_db import export_record2file, get_user_uid
# # get_user_uid("G0fXSprvkrrebaHDyd7kQbv2xPfK4UEMrseZwEDdpqsN6bw2AMDDrEBqU9%2BQBR6AW9eHm31NZRhbeL9MVdoTtXEg%2B5WkFNXEzRzs9si7SN9lhzxZlK3QlFL54UMN0Y50D%2BwNN40OJfNZWh7WA1JDInTHmNhpulfchks566opjGUBy6GUurYIX5Yvq7fUrVdEL8w2XRhdO0Dq")
from nonebot_plugin_arkrecord.ark.ark_scrawl import user_ark_analyser
resource_dir = "./nonebot_plugin_arkrecord/resource/"
ssyh_db_path = os.path.join(resource_dir, "arkgacha_record.db")
ssyh_db = sq.connect(ssyh_db_path)
gnrt = user_ark_analyser(ssyh_db, ['vivi#7527','TCJ0EfYh/Pm2mz8GDYLVnPw8', "594209837", 1], float('inf'), 'all')
# gnrt = user_ark_analyser(ssyh_db, ['画风奇特的日哥#','G0fXSprvkrrebaHDyd7kQbv2xPfK4UEMrseZwEDdpqsN6bw2AMDDrEBqU9+QBR6AW9eHm31NZRhbeL9MVdoTtXEg+5WkFNXEzRzs9si7SN9lhzxZlK3QlFL54UMN0Y50D+wNN40OJfNZWh7WA1JDInTHmNhpulfchks566opjGUBy6GUurYIX5Yvq7fUrVdEL8w2XRhdO0Dq','5177032', 2], 9999, 'all')
# gnrt = user_ark_analyser(ssyh_db, ['陈睿#','G0fXSprvkrrebaHDyd7kQbv2xPfK4UEMrseZwEDdpqsN6bw2AMDDrEBqU9+QBR6AW9eHm31NZRhbeL9MVdoTtXEg+5WkFNXEzRzs9si7SN9lhzxZlK3QlFL54UMN0Y50D+wNN40OJfNZWh7WA1JDInTHmNhpulfchks566opjGUBy6GUurYIX5Yvq7fUrVdEL8w2XRhdO0Dq','5177032', 2], 9999, 'all')
next(gnrt)
next(gnrt)
print('ok1')