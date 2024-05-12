import os
import time
from threading import Thread
from flask import Flask, render_template, url_for, redirect, request, make_response
import random
import string
import hashlib
import re
# 获取环境变量的值
CACHE_DIR = os.environ.get('PEO_CACHE_DIR')
if CACHE_DIR is None:
    CACHE_DIR = '.cache'
PORT = os.environ.get('PEO_PORT')
if PORT is None:
    PORT = 5000
COOKIE_KEY='t_token'
# Using poe.com tokens
tokens = {
    'b': '',
    'lat': '',
    'pwd': '',
    'sessionToken': '',
}
listens = {}

def watch_fork(file_path, callback):
    if os.path.exists(file_path):
        listens[file_path] = os.path.getmtime(file_path)
    else: 
        listens[file_path] = 0
    while True:
        if os.path.exists(file_path):
            current_time = os.path.getmtime(file_path)
        else: 
            current_time = 0
        if current_time > listens[file_path]:
            callback()
            listens[file_path] = current_time
        time.sleep(15)

def watch_file(file_path, callback): 
    p = Thread(target=watch_fork, args=(file_path, callback))
    p.setDaemon(True)
    p.start()

b_path = f'{CACHE_DIR}/b'
lat_path = f'{CACHE_DIR}/lat'
def getTokens():
    global tokens
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
    global tokens
    if os.path.exists(pwd_path):
        with open(pwd_path, 'r') as file:
            tokens['pwd'] = file.read()
        print(f'getPwd success: {tokens}')
getPwd()

if tokens['pwd'] != '':
    k = str(tokens['pwd']).encode('utf-8')
    sessionToken_path = f'{CACHE_DIR}/sessions/{hashlib.md5(k).hexdigest()}'
def getSessionToken():
    global tokens
    global sessionToken_path
    if os.path.exists(sessionToken_path) is False:
        return
    k = str(tokens['pwd']).encode('utf-8')
    sessionToken_path = f'{CACHE_DIR}/sessions/{hashlib.md5(k).hexdigest()}'
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
    global html
    if os.path.exists(html_path):
        with open(html_path, 'r') as file:
            html['content'] = file.read()
        print('getHTML success')
getHTML()

from poe_api_wrapper import PoeApi
cookie={'b': tokens['b'], 'lat': tokens['lat']}
print(f'cookie:{cookie}')
poeApi = { 'client': None }
def clientInit():
    poeApi['client'] = PoeApi(cookie=tokens)

def clientCheck():
    if poeApi['client'] is None:
        clientInit()
def updateTokens():
    global poeApi
    getTokens()
    if poeApi['client'] is not None:
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

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'
app.config['TEMPLATES_FOLDER'] = 'static'
app.config['JSON_AS_ASCII'] = False
app.json.ensure_ascii = False
app.config['PORT'] = PORT

# 生成随机字符串
def gen_hash(s = ''):
    letters = string.ascii_letters
    k = f"{''.join(random.choice(letters) for _ in range(32))}_{s}"
    return hashlib.md5(str(k).encode('utf-8')).hexdigest()

def auth():
    t = request.cookies.get(COOKIE_KEY)
    if t is None:
        return False
    k = str(tokens['pwd']).encode('utf-8')
    path = f'{CACHE_DIR}/sessions/{hashlib.md5(k).hexdigest()}'
    print(t, k, path)
    if os.path.exists(path) is False:
        return False
    with open(path, 'r') as file:
        tokensText = file.read()
    print(t, tokensText)
    if tokensText is None or re.search(t, tokensText) is None:
        return False
    return True

def loginRedirect():
    resp = make_response(redirect('/login', code=302))
    resp.delete_cookie(COOKIE_KEY)
    return resp

# 发送聊天信息
@app.route('/api/chats/<chatId>/<message>', methods=['GET'])
def sendMessage(chatId, message):
    if auth() is False:
        return { 'status': False, 'code': -1, 'data': 'error' }
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
        return { 'status': False, 'code': -1, 'data': 'error' }
    if chatMap.get(chatId) is None:
        chatsRef['chats'] = getChats()
    if chatMap.get(chatId) is None:
        return { 'status': False, 'code': 1, 'data': 'error' }
    return {'status': True, 'code': 0, 'data': chatMap.get(chatId)}
# 获取所有聊天
@app.route('/api/chats', methods=['GET'])
def queryChats():
    if auth() is False:
        return { 'status': False, 'code': -1, 'data': 'error' }
    chatsRef['chats'] = getChats()
    if chatsRef['chats'] is None:
        return { 'status': False, 'code': 1, 'data': 'error' }
    return {'status': True, 'code': 0, 'data': chatsRef['chats']}
# 登出接口
@app.route('/api/signout', methods=['GET', 'POST'])
def signout():
    resp = make_response({'status': True, 'code': -1, 'data': ''})
    resp.delete_cookie(COOKIE_KEY)
    return resp
# 登录接口
@app.route('/api/signin', methods=['POST'])
def signin():
    if tokens['pwd'] and tokens['pwd'] == request.json['password']:
        k = str(request.json['password']).encode('utf-8')
        d = hashlib.md5(k).hexdigest()
        t = gen_hash(d)
        path = f'{CACHE_DIR}/sessions/{d}'
        if os.path.exists(path):
            with open(path, "r+") as file:
                file.write(f'{t}\n')
        else:
            with open(path, "a") as file:
                file.write(t)
                file.close()
        resp = make_response({ 'status': True, 'code': 0, 'data': '' })
        resp.set_cookie(COOKIE_KEY, t)
        return resp
    return {'status': False, 'code': 1, 'data': 'password invalid'}
# 登出
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    return loginRedirect()
# 登录页
@app.route('/login', methods=['GET'])
def login():
    if auth() is True:
        return redirect(url_for('index'), code=302)
    global tokens
    return render_template('index.html', data={ 'page': 'login', 'chats': [], 'tokens': tokens }, content=html['content'])
# 首页
@app.route('/', methods=['GET'])
def index():
    if auth() is False:
        return loginRedirect()
    return render_template('index.html', data={ 'page': 'login', 'chats': chatsRef['chats'] }, content=html['content'])
# 定义当出现 404 错误时的处理函数
@app.errorhandler(404)
def page_not_found(error):
    if auth() is False:
        return
    return redirect(url_for('index'))

def main ():
    watch_file(b_path, updateTokens)
    watch_file(lat_path, updateTokens)
    watch_file(pwd_path, getPwd)
    watch_file(sessionToken_path, getSessionToken)
    watch_file(html_path, getHTML)
    app.run(port=PORT)
if __name__ == '__main__':
    main()
