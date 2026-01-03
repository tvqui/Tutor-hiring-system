import './App.css'
import { AuthProvider, useAuth } from './auth.jsx'
import Sidebar from './components/Sidebar'
import Center from './components/Center'
import Bookings from './components/Bookings'
import Login from './components/Login'
import CreatePost from './components/CreatePost'
import ProfileDetail from './components/ProfileDetail'
import Applications from './components/Applications'
import Verify from './components/Verify'
import { useState, useEffect } from 'react'

function InnerApp() {
  const { isAuthenticated } = useAuth();
  const [currentPage, setCurrentPage] = useState('center');

  useEffect(() => {
    function handleHashChange() {
      const hash = window.location.hash.slice(1);
      setCurrentPage(hash || 'center');
    }
    
    // Set initial page based on current hash
    handleHashChange();
    
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);
  
  if (!isAuthenticated) {
    return <Login />;
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'bookings':
        return <Bookings />;
      case 'applications':
        return <Applications />;
      case 'verify':
        return <Verify />;
      case 'create-post':
        return <CreatePost />;
        case 'profile':
          return <ProfileDetail />;
      default:
        return <Center />;
    }
  };
  
  return (
    <div className="app-grid">
      <Sidebar />
      <div className="main-area">
        {renderPage()}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <InnerApp />
    </AuthProvider>
  )
}
