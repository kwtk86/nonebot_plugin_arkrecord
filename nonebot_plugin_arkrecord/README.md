# **nonebot_plugin_arkrecord**
欢迎使用明日方舟抽卡分析nonebot插件 beta1.0

## **插件部署说明**
本插件基于python3.9开发，主要依赖项包括：

- numpy
- matplotlib
- PIL
- pysqlite3
- XlsxWriter

本插件依赖于sqlite数据库，在Ubuntu环境下无需额外配置；在windows下，参考网络资源安装sqlite数据库后即可，无需配置数据库环境

如需修改数据库文件名称，可以修改 `ark/ark_setting.py` 中的 `arkgacha_db_path`项

当前版本不支持自动更新卡池信息及干员头像资源。如果有新增干员，可以在PRTS下载干员头像，参照`resource/profile`中的命名规则命名。如果没有可用头像，将以海猫头像代替

## **插件部署方法**
在bot.py文件夹下

`git clone https://github.com/zheuziihau/nonebot_plugin_arkrecord`

或在命令行（cmd）中

`pip install nonebot_plugin_arkrecord`

载入插件方式与载入其他插件方式相同

## **插件使用方法**
### **token设置**

每个用户第一次使用时，需要设置token。

**token获取方法**：在官网登录后，根据你的服务器，选择复制以下网址中的内容
 
官服：https://as.hypergryph.com/user/info/v1/token_by_cookie

B服：https://web-api.hypergryph.com/account/info/ak-b

***请在浏览器中获取token，避免在QQ打开的网页中获取，否则可能获取无效token***

**token设置方法**：使用插件命令`方舟抽卡token 你的token`(自动识别B服、官服token)
或`方舟寻访token 你的token`进行设置

如网页中内容为

`{"status":0,"msg":"OK","data":{"token":"example123456789"}}`

则使用命令 `方舟抽卡token example123456789`， 如果间隔超**3天**再次使用，建议重新使用上述方式设置token
### **寻访记录分析**

设置token后，直接使用`方舟抽卡分析`或`方舟寻访分析`即可

还可以使用`方舟抽卡分析 数字`，分析最近一定抽数的寻访情况

如`方舟抽卡分析 100`分析最近100抽的情况

### **更新卡池信息与干员头像**

使用`方舟卡池更新`命令，自动从PRTS更新卡池信息及干员头像文件

### **导出记录**

使用`方舟抽卡导出`命令，可以在群聊中导出你当前关联token的储存于插件数据库中的寻访记录。请注意，目前只支持在群聊中导出

### **获取帮助**
使用`方舟寻访帮助`或`方舟抽卡帮助`命令，可以获取插件帮助

### **其他功能**
使用`随机干员`命令，随机给出一张干员头像



## **未来更新计划**

- 暂无，欢迎提issue

## **参考资料**
作图代码参考于

[nonebot-plugin-gachalogs](https://github.com/monsterxcn/nonebot-plugin-gachalogs)

[nonebot_plugin_gamedraw](https://github.com/HibiKier/nonebot_plugin_gamedraw)

## **开发人员信息**
主体开发[本人](https://github.com/zheuziihau)

美术资源及需求设计 [@Alnas1](https://github.com/Alnas1)