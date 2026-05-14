CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    role VARCHAR(10) DEFAULT 'member' CHECK (role IN ('admin','member')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    publisher VARCHAR(100),
    year INT,
    description TEXT,
    cover_url TEXT,
    total_stock INT DEFAULT 1 CHECK (total_stock >= 0),
    available_stock INT DEFAULT 1 CHECK (available_stock >= 0),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending','approved','returned','overdue')),
    loan_date DATE,
    due_date DATE,
    return_date DATE,
    fine_amount INT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO categories (name, description) VALUES
('Fiksi', 'Buku cerita fiksi'),
('Non-Fiksi', 'Buku pengetahuan umum'),
('Sains & Teknologi', 'Buku sains dan teknologi'),
('Sejarah', 'Buku sejarah'),
('Biografi', 'Buku biografi tokoh'),
('Pendidikan', 'Buku pendidikan')
ON CONFLICT (name) DO NOTHING;

INSERT INTO users (name, email, password_hash, role)
VALUES (
    'Administrator',
    'admin@perpustakaan.com',
    '$2b$12$qQmDuTE98O9yPOU3S6Wl7.K9OzCmHAfcjHsHS85BoVfETXuAfOQv.',
    'admin'
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO books 
(title, author, isbn, category_id, publisher, year, description, cover_url, total_stock, available_stock)
VALUES
('Laskar Pelangi', 'Andrea Hirata', '9789793062792', 1, 'Bentang Pustaka', 2005, 'Novel tentang perjuangan anak-anak Belitung dalam pendidikan.', '', 5, 5),
('Bumi Manusia', 'Pramoedya Ananta Toer', '9789799731234', 1, 'Hasta Mitra', 1980, 'Novel sejarah Indonesia pada masa kolonial.', '', 4, 4),
('Clean Code', 'Robert C. Martin', '9780132350884', 3, 'Prentice Hall', 2008, 'Panduan menulis kode yang bersih dan mudah dirawat.', '', 3, 3),
('Atomic Habits', 'James Clear', '9780735211292', 2, 'Avery', 2018, 'Buku tentang membangun kebiasaan kecil yang berdampak besar.', '', 6, 6),
('Sejarah Indonesia Modern', 'M.C. Ricklefs', '9789790241152', 4, 'Serambi', 2008, 'Pembahasan sejarah Indonesia modern.', '', 2, 2)
ON CONFLICT (isbn) DO NOTHING;



--Email    : admin@perpustakaan.com
--Password : admin123