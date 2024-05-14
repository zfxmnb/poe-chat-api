import { useEffect, useState, useRef } from 'preact/hooks';
import { type Chat, getChats, sendMessage, createChat, deleteChat } from '../../service';
import cs from 'classnames';
import Markdown from 'markdown-to-jsx';
import styles from './index.module.less';
const data = window.__INIT__ ?? {};
// 免费bot
const bots = [
  'claude_2_1_bamboo',
  'a2',
  'capybara',
  'chinchilla',
  'gpt3_5',
  'chinchilla_instruct',
  'acouchy',
  'llama_2_7b_chat',
  'llama_2_13b_chat',
  'llama_2_70b_chat',
  'code_llama_7b_instruct',
  'code_llama_13b_instruct',
  'code_llama_34b_instruct',
  'upstage_solar_0_70b_16bit',
  'claude_3_haiku',
  'claude_3_haiku_200k'
];
const defaultPrompt = '中文问题助手';
let ChatMap = {};
try {
  ChatMap = JSON.parse(localStorage.getItem('__chat_data__') ?? '{}');
} catch (err) {}
export function Home() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [chat, setChat] = useState<Chat>();
  const [loading, setLoading] = useState(false);
  const [chatMap, setChatMap] = useState<Record<string, { send: string; reply?: string }[]>>(ChatMap);
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [bot, setBot] = useState(bots[0]);

  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    getChats().then((data) => {
      setChats(data);
    });
  }, []);

  const openChat = (chatId: string) => {
    const chat = chats.find((chat) => chat.chatId === chatId);
    chat && setChat(chat);
  };

  const sendMsg = () => {
    const msg = inputRef.current?.value?.trim();
    if (chat && msg) {
      inputRef.current && (inputRef.current.value = '');
      setLoading(true);
      chatMap[chat.chatId] = chatMap[chat.chatId] || [];
      chatMap[chat.chatId].push({ send: msg });
      setChatMap({ ...chatMap });
      sendMessage({
        chatId: chat.chatId,
        msg
      })
        .then((data) => {
          chatMap[chat.chatId] = chatMap[chat.chatId] || [];
          chatMap[chat.chatId][chatMap[chat.chatId].length - 1] = { send: data.send, reply: data.reply };
          setChatMap({ ...chatMap });
          setLoading(false);
        })
        .catch(() => {
          setLoading(false);
        });
    }
  };
  const handleAddChat = () => {
    if (!prompt) {
      alert('请输入初始prompt');
      return;
    }
    confirm('确定要添加新的聊天吗？') &&
      createChat({ bot, prompt }).then((data) => {
        setChats([...chats, data]);
        setChat(data);
      });
  };
  const handleDeleteChat = (e: MouseEvent, bot: string, chatId: string) => {
    e.stopPropagation();
    if (confirm('确定要删除该聊天吗？')) {
      deleteChat({ bot, chatId }).then(() => {
        setChats(chats.filter((chat) => chat.chatId !== chatId));
        if (chat?.chatId === chatId) {
          setChat(undefined);
        }
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
                <a onClick={(e) => handleDeleteChat(e, bot, chatId)} href="javascript: void 0;">
                  删除
                </a>
              </div>
            );
          })}
        </div>
        <div className={styles.create}>
          <input
            className={styles.prompt}
            id="prompt"
            value={prompt}
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
              return <option value={bot}>{bot}</option>;
            })}
          </select>
          <button className={styles.addChat} onClick={() => handleAddChat()}>
            添加聊天
          </button>
        </div>
      </div>
      <div className={styles.chatView}>
        {chat ? (
          <div className={styles.chatContent}>
            <div className={styles.chatTitle}>
              <div>
                <span className={styles.chatName}>{chat.title}</span> - {chat.bot}
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
