import React, { useEffect, useState } from 'react';
import { Book } from './BookList';

interface User {
  id: string;
  name: string;
  role: string;
  borrowed: string[];
}

const MOCK_USER_ID = 'u1'; // Simulate logged-in user

const BorrowReturn: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch('/api/books').then(res => res.json()),
      fetch(`/api/user?id=${MOCK_USER_ID}`).then(res => res.json()),
    ])
      .then(([booksData, userData]) => {
        setBooks(booksData);
        setUser(userData);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load data');
        setLoading(false);
      });
  }, []);

  const handleBorrow = async (bookId: string) => {
    setActionMsg(null);
    try {
      const res = await fetch('/api/borrow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: MOCK_USER_ID, bookId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message);
      setBooks(books => books.map(b => b.id === bookId ? { ...b, stock: b.stock - 1 } : b));
      setUser(u => u ? { ...u, borrowed: [...u.borrowed, bookId] } : u);
      setActionMsg('Book borrowed successfully!');
    } catch (err: any) {
      setActionMsg(err.message);
    }
  };

  const handleReturn = async (bookId: string) => {
    setActionMsg(null);
    try {
      const res = await fetch('/api/return', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: MOCK_USER_ID, bookId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message);
      setBooks(books => books.map(b => b.id === bookId ? { ...b, stock: b.stock + 1 } : b));
      setUser(u => u ? { ...u, borrowed: u.borrowed.filter(id => id !== bookId) } : u);
      setActionMsg('Book returned successfully!');
    } catch (err: any) {
      setActionMsg(err.message);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!user) return <div>No user found.</div>;

  return (
    <div>
      <h2>Borrow & Return Books</h2>
      {actionMsg && <div style={{ color: actionMsg.includes('success') ? 'green' : 'red' }}>{actionMsg}</div>}
      <h3>Available Books</h3>
      <ul>
        {books.map(book => (
          <li key={book.id}>
            <b>{book.title}</b> by {book.author} —
            <span style={{ color: book.stock === 0 ? 'red' : 'black' }}>
              {book.stock === 0 ? ' Not Available' : ` Stock: ${book.stock}`}
            </span>
            <button
              disabled={book.stock === 0 || user.borrowed.length >= 2 || user.borrowed.includes(book.id)}
              onClick={() => handleBorrow(book.id)}
              style={{ marginLeft: 8 }}
            >
              Borrow
            </button>
          </li>
        ))}
      </ul>
      <h3>Borrowed Books</h3>
      <ul>
        {user.borrowed.length === 0 ? <li>None</li> : user.borrowed.map(bookId => {
          const book = books.find(b => b.id === bookId);
          return (
            <li key={bookId}>
              <b>{book?.title || 'Unknown Book'}</b> by {book?.author || 'Unknown'}
              <button onClick={() => handleReturn(bookId)} style={{ marginLeft: 8 }}>
                Return
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default BorrowReturn;
