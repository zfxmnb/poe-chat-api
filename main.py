import os
import time
import asyncio
# 获取环境变量的值
CACHE_DIR = os.environ.get('PEO_CACHE_DIR')
if CACHE_DIR is None:
    CACHE_DIR = '.cache'
PORT = os.environ.get('PEO_PORT')
if PORT is None:
    PORT = 5000
# Using poe.com tokens

tokens = {
    'b': '',
    'lat': '',
    'pwd': '',
    'sessionToken': '',
}
listens = {}
async def watch_file(file_path, callback):
    listens[file_path] = os.path.getmtime(file_path)
    print(file_path)
    while True:
        current_time = os.path.getmtime(file_path)
        if current_time > listens[file_path]:
            callback()
            listens[file_path] = current_time
        await asyncio.sleep(1)

b_path = f'{CACHE_DIR}/b'
lat_path = f'{CACHE_DIR}/lat'   
def getTokens():
    if os.path.exists(b_path) | os.path.exists(lat_path):
        with open(b_path, 'r') as file:
            b = file.read()
        with open(lat_path, 'r') as file:
            lat = file.read()
        tokens['b'] = b
        tokens['lat'] = lat
        print(f'getTokens success: {tokens}')
getTokens()

pwd_path = f'{CACHE_DIR}/pwd'
def getPwd():
    if os.path.exists(pwd_path):
        with open(pwd_path, 'r') as file:
            tokens['pwd'] = file.read()
        print(tokens['pwd'])
        print(f'getPwd success: {tokens}')
getPwd()

sessionToken_path = f'{CACHE_DIR}/{hash(tokens['pwd'])}'
def getSessionToken():
    sessionToken_path = f'{CACHE_DIR}/{hash(tokens['pwd'])}'
    if os.path.exists(sessionToken_path):
        with open(sessionToken_path, 'r') as file:
            tokens['sessionToken'] = file.read()
        print(f'getSessionToken success: {tokens}')
getSessionToken()

html = {
    'content': ''
}
html_path = 'static/index.html'
def getHTML():
    if os.path.exists(html_path):
        with open(html_path, 'r') as file:
            html['content'] = file.read()
        print('getHTML success')
getHTML()

from poe_api_wrapper import PoeApi
cookie={'b': tokens['b'], 'lat': tokens['lat']}
print(f'cookie:{cookie}')
poeApi = {}
def clientInit():
    poeApi['client'] = PoeApi(cookie=tokens)

def clientCheck():
    if poeApi['client'] is None:
        clientInit()

chatsRef = { 'chats': [] }
chatMap = {}
# 获取聊天记录
def getChats() :
    clientCheck()
    history = poeApi['client'].get_chat_history()['data']
    chatsRef['chats'] = []

    for key, value in history.items():
        for i in range(0, len(value)):
            chat = value[i]
            chat['bot'] = key
            chatsRef['chats'].append(chat)
            chatMap[str(chat['chatId'])] = chat
    return chatsRef['chats']
# 发送消息
def sendMsg(bot, message, chatId):
    # print(bot, chatId, message)
    clientCheck()
    for chunk in poeApi['client'].send_message(bot, message, chatId):
        pass
    s = chunk['text']
    return s


from flask import Flask, render_template, url_for, redirect, request, make_response
import random
import string

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'
app.config['TEMPLATES_FOLDER'] = 'static'
app.config['JSON_AS_ASCII'] = False
app.json.ensure_ascii = False
app.config['PORT'] = PORT

# 生成随机字符串
def gen_hash(str = ''):
    letters = string.ascii_letters
    return hash(f"{''.join(random.choice(letters) for _ in range(32))}_{str}")

def auth():
    t = request.cookies.get('t_token')
    if t is None:
        return False
    with open(f'${CACHE_DIR}/{hash(tokens['pwd'])}', 'r') as file:
        tokensText = file.read()
    match = re.search(t, tokensText)
    if tokensText is None or re.search(t, tokensText) is None:
        return False
    return True


# 发送聊天信息
@app.route('/api/chats/<chatId>/<message>', methods=['GET'])
def sendMessage(chatId, message):
    if auth() is False:
        return redirect('/login')
    if chatMap.get(chatId) is None:
        chatsRef['chats'] = getChats()
    if chatMap.get(chatId) is None:
        return { 'status': False, 'code': 1, 'data': 'error' }
    reply=sendMsg(chatMap.get(chatId)['bot'], message, chatId)
    return {'status': True, 'code': 0, 'data': { 'send': message, 'reply': reply }}
# 获取单个信息
@app.route('/api/chats/<chatId>', methods=['GET'])
def queryChat(chatId):
    if auth() is False:
        return redirect('/login')
    if chatMap.get(chatId) is None:
        chatsRef['chats'] = getChats()
    if chatMap.get(chatId) is None:
        return { 'status': False, 'code': 1, 'data': 'error' }
    return {'status': True, 'code': 0, 'data': chatMap.get(chatId)}
# 获取所有聊天
@app.route('/api/chats', methods=['GET'])
def queryChats():
    if auth() is False:
        return redirect('/login')
    chatsRef['chats'] = getChats()
    if chatsRef['chats'] is None:
        return { 'status': False, 'code': 1, 'data': 'error' }
    return {'status': True, 'code': 0, 'data': chatsRef['chats']}
# 登录接口
@app.route('/api/sign', methods=['POST'])
def sign():
    if tokens['pwd'] == request.json['password']:
        with open(sessionToken_path, "r+") as file:
            content = file.read()
            file.write(f'{gen_hash(tokens['pwd'])}\n{content}')
        return { 'status': True, 'code': 0, 'data': '' }
    return {'status': False, 'code': 1, 'data': 'password invalid'}
# 首页
@app.route('/login', methods=['GET'])
def login():
    if auth() is True:
        return redirect(url_for('index'))
    return render_template('index.html', data={ 'page': 'login', 'chats': [] }, content=html['content'])
# 首页
@app.route('/', methods=['GET'])
def index():
    if auth() is False:
        return redirect('/login')
    return render_template('index.html', data={ 'page': 'login', 'chats': chatsRef['chats'] }, content=html['content'])
# 定义当出现 404 错误时的处理函数
@app.errorhandler(404)
def page_not_found(error):
    if auth() is False:
        return
    return redirect(url_for('index'))

async def updateTokens():
    getTokens()
    if poeApi['client'] is not None:
        clientInit()
  
async def main ():
    asyncio.create_task(watch_file(b_path, updateTokens))
    asyncio.create_task(watch_file(lat_path, updateTokens))
    asyncio.create_task(watch_file(pwd_path, getPwd))
    asyncio.create_task(watch_file(sessionToken_path, getSessionToken))
    asyncio.create_task(watch_file(html_path, getHTML))
    await asyncio.sleep(1)
    app.run(port=PORT)
asyncio.run(main())
