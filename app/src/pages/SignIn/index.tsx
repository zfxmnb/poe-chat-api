import { useState } from 'preact/hooks';
import styles from './index.module.less';
import { postSignIn } from '../../service';
export function SignIn() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const handleSignIn = () => {
    if (username.trim() === '' || password.trim() === '') {
      alert('用户名或密码不能为空');
      return;
    }
    postSignIn({ username, password }).then(() => {
      window.location.href = '/';
    });
  };

  return (
    <div className={styles.container}>
      <h2>用户登录</h2>
      <div class={styles.item}>
        <div className={styles.label}>用户</div>
        <input value={username} className={styles.input} id="username" onInput={(e) => setUsername(e.currentTarget.value)} />
      </div>
      <div class={styles.item}>
        <div className={styles.label}>密码</div>
        <input value={password} className={styles.input} type={'password'} id="password" onInput={(e) => setPassword(e.currentTarget.value)} />
      </div>
      <button className={styles.button} onClick={handleSignIn}>
        登录
      </button>
    </div>
  );
}

export default SignIn;
