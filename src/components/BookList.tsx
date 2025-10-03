import React, { useEffect, useState } from 'react';

export type Book = {
  id: string;
  title: string;
  author: string;
  stock: number;
};

const BookList: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/books')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch books');
        return res.json();
      })
      .then((data) => {
        setBooks(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading books...</div>;
  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;

  return (
    <div>
      <h2>Book Inventory</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid #ccc', padding: '8px' }}>Title</th>
            <th style={{ border: '1px solid #ccc', padding: '8px' }}>Author</th>
            <th style={{ border: '1px solid #ccc', padding: '8px' }}>Stock</th>
          </tr>
        </thead>
        <tbody>
          {books.map((book) => (
            <tr key={book.id}>
              <td style={{ border: '1px solid #ccc', padding: '8px' }}>{book.title}</td>
              <td style={{ border: '1px solid #ccc', padding: '8px' }}>{book.author}</td>
              <td style={{ border: '1px solid #ccc', padding: '8px', color: book.stock === 0 ? 'red' : 'black' }}>
                {book.stock === 0 ? 'Not Available' : book.stock}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default BookList;
