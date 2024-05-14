import { useState } from 'preact/hooks';
import styles from './index.module.less';
import { postTokens } from '../../service';
const data = window.__INIT__ ?? {};
export function Admin() {
  const [b, setB] = useState(data.tokens?.b ?? '');
  const [lat, setLat] = useState(data.tokens?.lat ?? '');
  const handleSignIn = () => {
    postTokens({ b, lat }).then(() => {
      alert('设置成功');
    });
  };

  return (
    <div className={styles.container}>
      <h2>Admin 配置</h2>
      <div class={styles.item}>
        <div className={styles.label}>b</div>
        <input value={b} className={styles.input} id="b" onInput={(e) => setB(e.currentTarget.value)} />
      </div>
      <div class={styles.item}>
        <div className={styles.label}>lat</div>
        <input value={lat} className={styles.input} id="lat" onInput={(e) => setLat(e.currentTarget.value)} />
      </div>
      <button className={styles.button} onClick={handleSignIn}>
        设置
      </button>
    </div>
  );
}

export default Admin;
