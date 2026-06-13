import { ChatArea } from './components/ChatArea/ChatArea';
import { ErrorBannerPortal } from './components/ErrorBanner/ErrorBanner';
import { Header } from './components/Header/Header';
import { MessageInput } from './components/MessageInput/MessageInput';
import { ChatProvider } from './context/ChatContext';
import styles from './App.module.css';

export default function App() {
  return (
    <ChatProvider>
      <div className={styles.app}>
        <Header />
        <ChatArea />
        <ErrorBannerPortal />
        <MessageInput />
      </div>
    </ChatProvider>
  );
}
