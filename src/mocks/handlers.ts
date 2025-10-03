import { http } from 'msw';

// Mock data
const books = [
  { id: '1', title: 'Clean Code', author: 'Robert C. Martin', stock: 3 },
  { id: '2', title: 'The Pragmatic Programmer', author: 'Andrew Hunt', stock: 2 },
  { id: '3', title: 'Refactoring', author: 'Martin Fowler', stock: 0 },
];

type User = { id: string; name: string; role: string; borrowed: string[] };

const users: User[] = [
  { id: 'u1', name: 'Alice', role: 'user', borrowed: [] },
  { id: 'u2', name: 'Bob', role: 'admin', borrowed: [] },
];

export const handlers = [
  // Get books
  http.get('/api/books', ({ request }) => {
    return new Response(JSON.stringify(books), { status: 200 });
  }),

  // Get user info
  http.get('/api/user', ({ request }) => {
    const url = new URL(request.url);
    const id = url.searchParams.get('id');
    const user = users.find(u => u.id === id);
    if (!user) return new Response(JSON.stringify({ message: 'Unauthorized' }), { status: 401 });
    return new Response(JSON.stringify(user), { status: 200 });
  }),

  // Borrow book
  http.post('/api/borrow', async ({ request }) => {
    type BorrowRequestBody = { userId: string; bookId: string };
    const { userId, bookId } = await request.json() as BorrowRequestBody;
    const user = users.find(u => u.id === userId);
    const book = books.find(b => b.id === bookId);
    if (!user || !book) return new Response(JSON.stringify({ message: 'Invalid request' }), { status: 400 });
    if (book.stock <= 0) return new Response(JSON.stringify({ message: 'Not Available' }), { status: 400 });
    if (user.borrowed.length >= 2) return new Response(JSON.stringify({ message: 'Borrow limit reached' }), { status: 403 });
    book.stock -= 1;
    user.borrowed.push(bookId);
    return new Response(JSON.stringify({ message: 'Book borrowed', book, user }), { status: 200 });
  }),

  // Return book
  http.post('/api/return', async ({ request }) => {
    type ReturnRequestBody = { userId: string; bookId: string };
    const { userId, bookId } = await request.json() as ReturnRequestBody;
    const user = users.find(u => u.id === userId);
    const book = books.find(b => b.id === bookId);
    if (!user || !book) return new Response(JSON.stringify({ message: 'Invalid request' }), { status: 400 });
    if (!user.borrowed.includes(bookId)) return new Response(JSON.stringify({ message: 'Book not borrowed by user' }), { status: 400 });
    book.stock += 1;
    user.borrowed = user.borrowed.filter(id => id !== bookId);
    return new Response(JSON.stringify({ message: 'Book returned', book, user }), { status: 200 });
  }),

  // Admin: Add book
  http.post('/api/admin/add-book', async ({ request }) => {
    type AddBookRequestBody = { title: string; author: string; stock: number };
    const { title, author, stock } = await request.json() as AddBookRequestBody;
    const newBook = { id: String(books.length + 1), title, author, stock };
    books.push(newBook);
    return new Response(JSON.stringify(newBook), { status: 201 });
  }),

  // Admin: Update stock
  http.post('/api/admin/update-stock', async ({ request }) => {
    type UpdateStockRequestBody = { bookId: string; stock: number };
    const { bookId, stock } = await request.json() as UpdateStockRequestBody;
    const book = books.find(b => b.id === bookId);
    if (!book) return new Response(JSON.stringify({ message: 'Book not found' }), { status: 400 });
    book.stock = Math.max(0, stock);
    return new Response(JSON.stringify(book), { status: 200 });
  }),

  // Admin: View inventory
  http.get('/api/admin/inventory', ({ request }) => {
    return new Response(JSON.stringify(books), { status: 200 });
  }),

  // Admin: Track borrowed books
  http.get('/api/admin/borrowed', ({ request }) => {
    const borrowed = users.map(u => ({ id: u.id, name: u.name, borrowed: u.borrowed }));
    return new Response(JSON.stringify(borrowed), { status: 200 });
  }),
];
