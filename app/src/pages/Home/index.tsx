import { useEffect, useState, useRef } from 'preact/hooks';
import { type Chat, type Bot, getChats, sendMessage, createChat, deleteChat, queryBots, updateinstance } from '../../service';
import cs from 'classnames';
import Markdown from 'markdown-to-jsx';
import styles from './index.module.less';
const data = window.__INIT__ ?? {};

const defaultPrompt = '中文问题助手';
let ChatMap = {};
try {
  ChatMap = JSON.parse(localStorage.getItem('__chat_data__') ?? '{}');
} catch (err) {}
export function Home() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [chat, setChat] = useState<Chat>();
  const [loading, setLoading] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [chatMap, setChatMap] = useState<Record<string, { send: string; reply?: string }[]>>(ChatMap);
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [bots, setBots] = useState<Bot[]>([]);
  const [bot, setBot] = useState<string>(bots[0]?.nickname);

  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (data?.hasTokens !== false) {
      getChats().then((data) => {
        setChats(data);
      });
      queryBots({ count: 25 }).then((bots) => {
        setBots(bots);
        setBot(bots[0]?.nickname);
      });
    }
  }, []);

  const openChat = (chatId: string) => {
    const chat = chats.find((chat) => chat.chatId === chatId);
    chat && setChat(chat);
  };

  const sendMsg = () => {
    const msg = inputRef.current?.value?.trim();
    if (chat && msg) {
      const chatId = chat.chatId;
      inputRef.current && (inputRef.current.value = '');
      setLoading(true);
      chatMap[chatId] = chatMap[chatId] || [];
      chatMap[chatId].push({ send: msg });
      setChatMap({ ...chatMap });
      sendMessage({
        chatId,
        msg
      })
        .then((data) => {
          chatMap[chatId] = chatMap[chatId] || [];
          chatMap[chatId][chatMap[chatId].length - 1] = { send: data.send, reply: data.reply };
          setChatMap({ ...chatMap });
          setLoading(false);
        })
        .catch(() => {
          setLoading(false);
          if (confirm('发送消息异常稍后再试，或立即调用刷新服务')) {
            updateinstance()
          }
        });
    }
  };
  const handleAddChat = () => {
    if (!prompt || !bot) {
      alert('请输入初始Prompt和选择AI');
      return;
    }
    if (confirm('确定要添加新的聊天吗？')) {
      setCreateLoading(true);
      createChat({ bot, prompt })
        .then((data) => {
          setChats([...chats, data]);
          setChat(data);
          setCreateLoading(false);
        })
        .catch(() => {
          setCreateLoading(false);
        });
    }
  };
  const handleDeleteChat = (e: MouseEvent, bot: string, chatId: string) => {
    e.stopPropagation();
    if (confirm('确定要删除该聊天吗？')) {
      setDeleteLoading(true);
      deleteChat({ bot, chatId })
        .then(() => {
          setChats(chats.filter((chat) => chat.chatId !== chatId));
          if (chat?.chatId === chatId) {
            setChat(undefined);
          }
          setDeleteLoading(false);
        })
        .catch(() => {
          setDeleteLoading(false);
        });
    }
  };
  const clearCache = () => {
    if (!confirm('是否清除聊天记录本地缓存？')) return;
    let newChatMap = {};
    if (chat) {
      newChatMap = {
        [chat.chatId]: chatMap[chat.chatId]
      };
    }
    setChatMap(newChatMap);
    localStorage.setItem('__chat_data__', JSON.stringify(newChatMap));
  };
  useEffect(() => {
    setLoading(false);
  }, [chat?.chatId]);

  useEffect(() => {
    localStorage.setItem('__chat_data__', JSON.stringify(chatMap));
  }, [chatMap]);

  return (
    <div className={styles.container}>
      <div className={styles.chats}>
        <div className={styles.options}>
          {data?.role === 'admin' ? <a href={`/admin`}>管理</a> : null}
          <a href={`/signout`}>退出</a>
          <a href="javascript: void 0;" onClick={clearCache}>
            清除缓存
          </a>
        </div>
        <div className={styles.chatsList}>
          {chats.map(({ title, bot, chatId }) => {
            return (
              <div className={cs(styles.chat, { [styles.selected]: chat?.chatId === chatId })} onClick={() => openChat(chatId)}>
                <h3 className={styles.chatTitle}>{title ?? '[无标题]'}</h3>
                <p className={styles.chatBot}>{bot}</p>
                <a style={{ opacity: deleteLoading ? 0.5 : 1 }} onClick={(e) => !deleteLoading && handleDeleteChat(e, bot, chatId)} href="javascript: void 0;">
                  删除
                </a>
              </div>
            );
          })}
        </div>
        <div hidden={!bots?.length} className={styles.create}>
          <input
            className={styles.prompt}
            id="prompt"
            value={prompt}
            placeholder="请输入初始Prompt"
            onChange={(e) => {
              // @ts-ignore
              setPrompt(e?.target?.value ?? '');
            }}
            ref={inputRef}
          />
          <select
            className={styles.bot}
            id="bot"
            value={bot}
            onChange={(e) => {
              // @ts-ignore
              setBot(e?.target?.value);
            }}
          >
            {bots.map((bot) => {
              return (
                <option disabled={bot.isLimitedAccess} key={bot.nickname} value={bot?.nickname}>
                  {bot.displayName}({bot.nickname})
                </option>
              );
            })}
          </select>
          {!createLoading ? (
            <button className={styles.addChat} onClick={() => handleAddChat()}>
              添加聊天
            </button>
          ) : null}
        </div>
      </div>
      <div className={styles.chatView}>
        {chat ? (
          <div className={styles.chatContent}>
            <div className={styles.chatTitle}>
              <div>
                <span className={styles.chatName}>{chat.title ?? '[无标题]'}</span> - {chat.bot}
              </div>
            </div>
            <div className={styles.chatTexts}>
              {chatMap[chat.chatId]?.map(({ send, reply }, index) => {
                return (
                  <div className={styles.chatText}>
                    <div className={styles.sender}>
                      <span>{send}</span>
                    </div>
                    {(index === chatMap[chat.chatId].length - 1 && loading) || reply ? (
                      <div className={styles.replier}>
                        <span>{reply ? <Markdown>{reply}</Markdown> : '正在思考中。。。'}</span>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
            <div className={styles.send}>
              <input disabled={loading} className={styles.sendInput} ref={inputRef} type="text" onKeyPressCapture={(e) => !loading && e.key === 'Enter' && sendMsg()} />
              <button className={cs(styles.sendBtn, { [styles.disabled]: loading })} onClick={!loading ? sendMsg : void 0}>
                发送
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default Home;
