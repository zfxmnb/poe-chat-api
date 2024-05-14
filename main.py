import sys
import os
import string
import random
import re
import json
import time
import hashlib
from threading import Thread
from flask import Flask, render_template, url_for, redirect, request, make_response
from poe_api_wrapper import PoeApi

# 获取环境变量的值
CACHE_DIR = os.environ.get('PEO_CACHE_DIR')
if CACHE_DIR is None:
    CACHE_DIR = '.data'
PORT = os.environ.get('PEO_PORT')
if PORT is None:
    PORT = 5000
COOKIE_KEY='s_t'
listens = {}
loginExpires = time.time() + 60 * 60 * 24 * 15
usersPath = f'{CACHE_DIR}/users.json'
poePath=f'{CACHE_DIR}/poe.json'
# 缺少配置文件直接退出
if os.path.exists(poePath) is False or os.path.exists(usersPath) is False:
    print(f'[{CACHE_DIR}/]目录下缺少poe.json或users.json配置文件')
    sys.exit(0)

# 基础方法
## 生成随机字符串
def gen_hash(s = ''):
    letters = string.ascii_letters
    k = f"{''.join(random.choice(letters) for _ in range(32))}_{s}"
    return hashlib.md5(str(k).encode('utf-8')).hexdigest()
## 文件变动监听进程
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
        time.sleep(5)
## 文件变动监听
def watch_file(file_path, callback): 
    p = Thread(target=watch_fork, args=(file_path, callback))
    p.setDaemon(True)
    p.start()
def hasValidProperty(obj: dict, key: str, allowEmpty=False):
    if key not in obj:
        return False
    if allowEmpty is False and (obj.get(key) is None or obj.get(key) == '' ):
        return False
    return True
def hasValidProperties(obj: dict, keys: list=[], allowEmpty=False):
    for key in keys:
        if not hasValidProperty(obj, key, allowEmpty):
            return False
    return True
    
# 用户相关方法
users = []
userMap = {}
## 获取所有用户
def getUsers():
    global users
    global userMap
    users = json.load(open(usersPath,'r'))
    for i in range(0, len(users)):
        user = users[i]
        userMap[user['username']] = i
    print(f'getUsers success')
    return users
getUsers()
## 获取指定用户
def getUser(name):
    if len(users) == 0:
        getUsers()
    if len(users) == 0:
        return None
    return users[userMap[name]]
## 设置指定用户session
def setUserSession(user, session):
    user['session'] = session
    with open(usersPath, "w") as file:
        file.write(json.dumps(users, indent=2))
    return True
## 移除指定用户session
def removeUserSession(name):
    user = users[userMap[name]]
    if user is None:
        return False
    del user['session']
    with open(usersPath, "w") as file:
        file.write(json.dumps(users, indent=2))
    return True
## 用户登录设置session
def userSignIn (name, pwd):
    user = getUser(name)
    if user is None or pwd != user['password']:
        return None
    k = str(pwd).encode('utf-8')
    d = hashlib.md5(k).hexdigest()
    t = gen_hash(d)
    user['session'] = t
    setUserSession(user, t)
    return t
## 通过session匹配用户有效
def matchUserBySession(session):
    if session is None:
        return None
    for i in range(0, len(users)):
        if 'session' in users[i] and users[i]['session'] == session:
            return users[i]
            break
    return None
## 通过session匹配用户有效
def validUserBySession(session, admin=False):
    user = matchUserBySession(session)
    if user is None:
        return False
    if admin is True and user['role'] != 'admin':
        return False
    return True
## 登出
def userSignOut(session):
    user = matchUserBySession(session)
    if user is None:
        return False
    del user['session']
    with open(usersPath, "w") as file:
        file.write(json.dumps(users, indent=2))
    return True

# token方法
tokens = { 'b': '', 'lat': '' }
def getTokens():
    global tokens
    if os.path.exists(poePath):
        poeConfig = json.load(open(poePath, 'r'))
        if hasValidProperty(tokens, 'b'):
            tokens['b'] = poeConfig['b']
        if hasValidProperty(tokens, 'lat'):
            tokens['lat'] = poeConfig['lat']
        print(f'getTokens success: {tokens}')
getTokens()
def setTokens(b, lat):
    global tokens
    tokens['b'] = b
    tokens['lat'] = lat
    with open(poePath, "w") as file:
        file.write(json.dumps(tokens, indent=2))
    
# 获取入口html
html = {'content': ''}
html_path = 'static/index.html'
def getHTML():
    global html
    if os.path.exists(html_path):
        with open(html_path, 'r') as file:
            html['content'] = file.read()
        print('getHTML success')
getHTML()

# peo
print(f'tokens:{tokens}')
poeApi = { 'client': None, 'chats': [], 'chatMap': {} }
def clientInit():
    global poeApi
    poeApi['client'] = PoeApi(cookie=tokens)
def clientCheck():
    global poeApi
    if 'chats' not in poeApi or poeApi['client'] is None:
        clientInit()
def tokensUpdate():
    global poeApi
    getTokens()
    clientInit()
# 获取聊天记录
def getChats():
    clientCheck()
    history = poeApi['client'].get_chat_history()['data']
    poeApi['chats'] = []

    for key, value in history.items():
        for i in range(0, len(value)):
            chat = value[i]
            chat['bot'] = key
            poeApi['chats'].append(chat)
            poeApi['chatMap'][str(chat['chatId'])] = chat
    return poeApi['chats']
# 发送消息
def sendMsg(bot, message, chatId):
    # print(bot, chatId, message)
    clientCheck()
    for chunk in poeApi['client'].send_message(bot, message, chatId):
        pass
    s = chunk['text']
    return s

# Flask
app = Flask(__name__)
# app.config['STATIC_FOLDER'] = 'static'
app.config['JSON_AS_ASCII'] = False
app.json.ensure_ascii = False
app.config['PORT'] = PORT

# 鉴权
def auth(admin=False):
    t = request.cookies.get(COOKIE_KEY)
    if t is None or validUserBySession(t, admin) is False:
        return False
    return True
# 重定向登录
def loginRedirect():
    t = request.cookies.get(COOKIE_KEY)
    if t is not None:
        userSignOut(t)
    resp = make_response(redirect('/signin'))
    resp.delete_cookie(COOKIE_KEY)
    return resp
def poeValid(chatId):
    if hasValidProperties(poeApi, ['chatMap']) is False:
        return False
    if chatId is None or hasValidProperties(poeApi['chatMap'], [chatId]) is False:
        return False
    return True
# 发送聊天信息
@app.route('/api/chats/<chatId>/send', methods=['GET', 'POST'])
def sendMessage(chatId):
    if auth() is False:
        return { 'status': False, 'code': -1, 'data': 'error' }
    if poeValid(chatId) is False:
        poeApi['chats'] = getChats()
    if poeValid(chatId) is False:
        return { 'status': False, 'code': 1, 'data': 'poe error' }
    if request.method == 'POST':
        if hasValidProperties(request.json, ['msg']) is False:
            return { 'status': False, 'code': 2, 'data': 'properties error' }
        message = request.json['msg']
    else:
        if hasValidProperties(request.json, ['msg']) is False:
            return { 'status': False, 'code': 2, 'data': 'properties error' }
        message = request.args['msg']
    if message is None or message == '':
        return { 'status': False, 'code': 2, 'data': 'msg is empty' }
    reply=sendMsg(poeApi['chatMap'].get(chatId)['bot'], message, chatId)
    return {'status': True, 'code': 0, 'data': { 'send': message, 'reply': reply }}
# 获取单个信息
@app.route('/api/chats/<chatId>/info', methods=['GET'])
def queryChat(chatId):
    if auth() is False:
        return { 'status': False, 'code': -1, 'data': 'role error' }
    if poeValid(chatId) is False:
        poeApi['chats'] = getChats()
    if poeValid(chatId) is False:
        return { 'status': False, 'code': 1, 'data': 'poe error' }
    return {'status': True, 'code': 0, 'data': poeApi['chatMap'].get(chatId)}
# 获取所有聊天
@app.route('/api/chats', methods=['GET'])
def queryChats():
    if auth() is False:
        return { 'status': False, 'code': -1, 'data': 'role error' }
    poeApi['chats'] = getChats()
    if poeValid() is False:
        return { 'status': False, 'code': 1, 'data': 'poe error' }
    return {'status': True, 'code': 0, 'data': poeApi['chats']}
# 登出接口
@app.route('/api/signout', methods=['GET', 'POST'])
def sign_out():
    resp = make_response({'status': True, 'code': -1, 'data': 'role error'})
    resp.delete_cookie(COOKIE_KEY)
    return resp
# 登录接口
@app.route('/api/signin', methods=['POST'])
def sign_in():
    if getValidProperties(request.json, ['username', 'password']) is False:
        return { 'status': False, 'code': 2, 'data': 'properties error' }
    t = userSignIn(request.json['username'], request.json['password'])
    if t is not None:
        resp = make_response({ 'status': True, 'code': 0, 'data': '' })
        resp.set_cookie(COOKIE_KEY, t, httponly=True, expires=loginExpires)
        return resp
    return {'status': False, 'code': 3, 'data': 'password invalid'}
# 设置token接口
@app.route('/api/tokens', methods=['POST'])
def post_tokens():
    if auth('admin') is False:
        return { 'status': False, 'code': -1, 'data': 'role error' }
    if hasValidProperties(request.json, ['b', 'lat']) is False:
        return { 'status': False, 'code': 2, 'data': 'properties error' }
    b = request.json['b']
    lat = request.json['lat']
    setTokens(b, lat)
    resp = make_response({ 'status': True, 'code': 0, 'data': '' })
    return resp
# 管理页
@app.route('/admin', methods=['GET'])
def admin():
    if auth() is False:
        return loginRedirect()
    if auth('admin') is False:
        return redirect(url_for('index'))
    return render_template('index.html', data={ 'currentPage': 'Admin', 'tokens': tokens }, content=html['content'])
# 登出页
@app.route('/signout', methods=['GET'])
def logout():
    return loginRedirect()
# 登录页
@app.route('/signin', methods=['GET'])
def login():
    if auth() is True:
        return redirect(url_for('index'))
    global tokens
    return render_template('index.html', data={ 'currentPage': 'Signin' }, content=html['content'])
# 首页
@app.route('/', methods=['GET'])
def index():
    if auth() is False:
        return loginRedirect()
    return render_template('index.html', data={ 'currentPage': 'Home' }, content=html['content'])
# 定义当出现 404 错误时的处理函数
@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('index'))

def main ():
    watch_file(usersPath, getUsers)
    watch_file(poePath, tokensUpdate)
    watch_file(html_path, getHTML)
    app.run(port=PORT)
if __name__ == '__main__':
    main()
