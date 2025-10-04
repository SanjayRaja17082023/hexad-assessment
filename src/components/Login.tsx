import React, { useState } from 'react';
import { useAuth, AuthUser, Role } from '../context/AuthContext';

const mockUsers: AuthUser[] = [
  { id: 'u1', name: 'Alice', role: 'user' },
  { id: 'u2', name: 'Bob', role: 'admin' },
];

const Login: React.FC = () => {
  const { login } = useAuth();
  const [selectedUser, setSelectedUser] = useState<AuthUser | null>(null);
  const [provider, setProvider] = useState<'google' | 'github' | null>(null);

  const handleLogin = () => {
    if (selectedUser && provider) {
      login(selectedUser);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '2rem auto', padding: 24, border: '1px solid #ccc', borderRadius: 8 }}>
      <h2>Login</h2>
      <div>
        <label>Choose Provider:</label>
        <div>
          <button onClick={() => setProvider('google')} style={{ marginRight: 8 }}>
            Google
          </button>
          <button onClick={() => setProvider('github')}>
            GitHub
          </button>
        </div>
      </div>
      <div style={{ marginTop: 16 }}>
        <label>Choose Role:</label>
        <select
          value={selectedUser?.id || ''}
          onChange={e => {
            const user = mockUsers.find(u => u.id === e.target.value);
            setSelectedUser(user || null);
          }}
        >
          <option value="">Select User</option>
          {mockUsers.map(u => (
            <option key={u.id} value={u.id}>
              {u.name} ({u.role})
            </option>
          ))}
        </select>
      </div>
      <button
        style={{ marginTop: 24, width: '100%' }}
        disabled={!selectedUser || !provider}
        onClick={handleLogin}
      >
        Login
      </button>
    </div>
  );
};

export default Login;
