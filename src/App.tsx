import React from 'react';
import './App.css';
import BookList from './components/BookList';
import BorrowReturn from './components/BorrowReturn';
import Login from './components/Login';
import { useAuth } from './context/AuthContext';

function App() {
  const { user, logout } = useAuth();

  return (
    <div className="App">
      <header className="App-header">
        <h1>Hexad Book Borrowing System</h1>
        {user ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <span>Logged in as <b>{user.name}</b> ({user.role})</span>
              <button style={{ marginLeft: 16 }} onClick={logout}>Logout</button>
            </div>
            <BookList />
            <BorrowReturn />
            {/* Admin panel will be added for admin role */}
          </>
        ) : (
          <Login />
        )}
      </header>
    </div>
  );
}

export default App;
