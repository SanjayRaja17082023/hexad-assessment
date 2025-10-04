import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Book } from './BookList';

const AdminPanel: React.FC = () => {
  const { user } = useAuth();
  const [books, setBooks] = useState<Book[]>([]);
  const [borrowed, setBorrowed] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);
  const [newBook, setNewBook] = useState({ title: '', author: '', stock: 1 });

  useEffect(() => {
    Promise.all([
      fetch('/api/admin/inventory').then(async res => {
        if (!res.ok) throw new Error('Error loading inventory');
        return res.json();
      }),
      fetch('/api/admin/borrowed').then(async res => {
        if (!res.ok) throw new Error('Error loading borrowed books');
        return res.json();
      }),
    ]).then(([booksData, borrowedData]) => {
      setBooks(booksData);
      setBorrowed(borrowedData);
      setLoading(false);
    }).catch(err => {
      setMsg(err.message || 'Failed to load admin data');
      setLoading(false);
    });
  }, [msg]);

  const handleAddBook = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    try {
      const res = await fetch('/api/admin/add-book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newBook),
      });
      if (!res.ok) {
        const data = await res.json();
        setMsg(data.message || 'Failed to add book');
        return;
      }
      setMsg('Book added!');
      setNewBook({ title: '', author: '', stock: 1 });
    } catch (err: any) {
      setMsg(err.message || 'Failed to add book');
    }
  };

  const handleUpdateStock = async (bookId: string, stock: number) => {
    setMsg(null);
    try {
      const res = await fetch('/api/admin/update-stock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bookId, stock }),
      });
      if (!res.ok) {
        const data = await res.json();
        setMsg(data.message || 'Failed to update stock');
        return;
      }
      setMsg('Stock updated!');
    } catch (err: any) {
      setMsg(err.message || 'Failed to update stock');
    }
  };

  if (!user || user.role !== 'admin') return null;
  if (loading) return <div>Loading admin panel...</div>;

  return (
    <div style={{ marginTop: 32, padding: 24, border: '1px solid #ccc', borderRadius: 8 }}>
      <h2>Admin Panel</h2>
      {msg && <div style={{ color: msg.includes('!') ? 'green' : 'red' }}>{msg}</div>}
      <h3>Add New Book</h3>
      <form onSubmit={handleAddBook} style={{ marginBottom: 16 }}>
        <input
          type="text"
          placeholder="Title"
          value={newBook.title}
          onChange={e => setNewBook(b => ({ ...b, title: e.target.value }))}
          required
        />
        <input
          type="text"
          placeholder="Author"
          value={newBook.author}
          onChange={e => setNewBook(b => ({ ...b, author: e.target.value }))}
          required
        />
        <input
          type="number"
          min={0}
          placeholder="Stock"
          value={newBook.stock}
          onChange={e => setNewBook(b => ({ ...b, stock: Number(e.target.value) }))}
          required
        />
        <button type="submit">Add Book</button>
      </form>
      <h3>Inventory</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Title</th>
            <th>Author</th>
            <th>Stock</th>
            <th>Update Stock</th>
          </tr>
        </thead>
        <tbody>
          {books.map(book => (
            <tr key={book.id}>
              <td>{book.title}</td>
              <td>{book.author}</td>
              <td>{book.stock === 0 ? 'Not Available' : book.stock}</td>
              <td>
                <input
                  type="number"
                  min={0}
                  defaultValue={book.stock}
                  onBlur={e => handleUpdateStock(book.id, Number(e.target.value))}
                  style={{ width: 60 }}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Borrowed Books</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>User</th>
            <th>Borrowed Book IDs</th>
          </tr>
        </thead>
        <tbody>
          {borrowed.map(u => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td>{u.borrowed.length === 0 ? 'None' : u.borrowed.join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AdminPanel;
