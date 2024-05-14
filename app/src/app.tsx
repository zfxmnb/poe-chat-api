// import { useState } from 'preact/hooks'
import Home from './pages/Home';
import SignIn from './pages/SignIn';
import Admin from './pages/Admin';
import './app.css';
const data = window.__INIT__ ?? { currentPage: 'Home' };
export function App() {
  // const [count, setCount] = useState(0)
  return (
    <>
      {data.currentPage === 'Home' ? <Home /> : null}
      {data.currentPage === 'Signin' ? <SignIn /> : null}
      {data.currentPage === 'Admin' ? <Admin /> : null}
    </>
  );
}
