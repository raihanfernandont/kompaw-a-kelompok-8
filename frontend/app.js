const API_URL = "/api";

function getToken() {
    return localStorage.getItem("token");
}

function setLoginInfo() {
    const user = JSON.parse(localStorage.getItem("user") || "null");
    const info = document.getElementById("loginInfo");

    if (user) {
        info.innerText = `Login sebagai: ${user.name} (${user.role})`;
    } else {
        info.innerText = "Belum login";
    }
}

async function register() {
    const data = {
        name: document.getElementById("regName").value,
        email: document.getElementById("regEmail").value,
        password: document.getElementById("regPassword").value,
        phone: document.getElementById("regPhone").value,
        address: document.getElementById("regAddress").value
    };

    const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    const result = await res.json();
    showMessage(result);
}

async function login() {
    const data = {
        email: document.getElementById("loginEmail").value,
        password: document.getElementById("loginPassword").value
    };

    const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    const result = await res.json();

    if (result.success) {
        localStorage.setItem("token", result.token);
        localStorage.setItem("user", JSON.stringify(result.user));
        showMessage(result );
        setLoginInfo();
    } else {
        showMessage(result);
    }
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setLoginInfo();
    alert("Logout berhasil");
}

async function loadBooks() {
    const res = await fetch(`${API_URL}/books`);
    const result = await res.json();

    const container = document.getElementById("books");
    container.innerHTML = "";

    result.books.forEach(book => {
        container.innerHTML += `
            <div class="book-item">
                <h3>${book.title}</h3>
                <p><b>Penulis:</b> ${book.author}</p>
                <p><b>Kategori:</b> ${book.category_name || "-"}</p>
                <p><b>Stok:</b> ${book.available_stock}/${book.total_stock}</p>
                <p>${book.description || ""}</p>
                <button onclick="borrowBook(${book.id})">Pinjam</button>
            </div>
        `;
    });
}

async function searchBooks() {
    const q = document.getElementById("searchInput").value;

    if (!q) {
        alert("Masukkan kata kunci pencarian");
        return;
    }

    const res = await fetch(`${API_URL}/books/search?q=${encodeURIComponent(q)}`);
    const result = await res.json();

    const container = document.getElementById("books");
    container.innerHTML = "";

    result.books.forEach(book => {
        container.innerHTML += `
            <div class="book-item">
                <h3>${book.title}</h3>
                <p><b>Penulis:</b> ${book.author}</p>
                <p><b>Kategori:</b> ${book.category_name || "-"}</p>
                <p><b>Stok:</b> ${book.available_stock}/${book.total_stock}</p>
                <button onclick="borrowBook(${book.id})">Pinjam</button>
            </div>
        `;
    });
}

async function borrowBook(bookId) {
    const token = getToken();

    if (!token) {
        alert("Login dulu sebagai member");
        return;
    }

    const res = await fetch(`${API_URL}/loans`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({book_id: bookId})
    });

    const result = await res.json();
    showMessage(result);
}

async function loadMyLoans() {
    const token = getToken();

    if (!token) {
        alert("Login dulu");
        return;
    }

    const res = await fetch(`${API_URL}/loans/my`, {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const result = await res.json();

    const container = document.getElementById("myLoans");
    container.innerHTML = "";

    result.loans.forEach(loan => {
        container.innerHTML += `
            <div class="loan-item">
                <p><b>Buku:</b> ${loan.book_title}</p>
                <p><b>Status:</b> ${loan.status}</p>
                <p><b>Tanggal Pinjam:</b> ${loan.loan_date || "-"}</p>
                <p><b>Jatuh Tempo:</b> ${loan.due_date || "-"}</p>
                <p><b>Denda:</b> Rp ${loan.fine_amount}</p>
            </div>
        `;
    });
}

async function loadAllLoans() {
    const token = getToken();

    if (!token) {
        alert("Login dulu sebagai admin");
        return;
    }

    const res = await fetch(`${API_URL}/loans`, {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const result = await res.json();

    if (!result.success) {
        alert(result.detail || "Gagal mengambil data");
        return;
    }

    const container = document.getElementById("allLoans");
    container.innerHTML = "";

    result.loans.forEach(loan => {
        container.innerHTML += `
            <div class="loan-item">
                <p><b>Member:</b> ${loan.user_name}</p>
                <p><b>Buku:</b> ${loan.book_title}</p>
                <p><b>Status:</b> ${loan.status}</p>
                <p><b>Due Date:</b> ${loan.due_date || "-"}</p>
                <p><b>Denda:</b> Rp ${loan.fine_amount}</p>
                <button onclick="approveLoan(${loan.id})">Approve</button>
                <button onclick="returnLoan(${loan.id})">Return</button>
            </div>
        `;
    });
}

async function approveLoan(loanId) {
    const token = getToken();

    const res = await fetch(`${API_URL}/loans/${loanId}/approve`, {
        method: "PUT",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const result = await res.json();
    showMessage(result);
    loadAllLoans();
}

async function returnLoan(loanId) {
    const token = getToken();

    const res = await fetch(`${API_URL}/loans/${loanId}/return`, {
        method: "PUT",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const result = await res.json();
    showMessage(result);
    loadAllLoans();
}

async function addBook() {
    const token = getToken();

    const stock = Number(document.getElementById("bookStock").value || 1);

    const data = {
        title: document.getElementById("bookTitle").value,
        author: document.getElementById("bookAuthor").value,
        isbn: document.getElementById("bookIsbn").value,
        category_id: Number(document.getElementById("bookCategory").value || 1),
        publisher: document.getElementById("bookPublisher").value,
        year: Number(document.getElementById("bookYear").value || 2024),
        description: document.getElementById("bookDescription").value,
        cover_url: "",
        total_stock: stock,
        available_stock: stock
    };

    const res = await fetch(`${API_URL}/books`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(data)
    });

    const result = await res.json();
    showMessage(result);
    loadBooks();
}

async function loadStats() {
    const token = getToken();

    const res = await fetch(`${API_URL}/reports/stats`, {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const result = await res.json();

    if (!result.success) {
        alert(result.detail || "Gagal mengambil statistik");
        return;
    }

    const s = result.stats;

    document.getElementById("stats").innerHTML = `
        <p><b>Total Buku:</b> ${s.total_books}</p>
        <p><b>Stok Tersedia:</b> ${s.available_books}</p>
        <p><b>Total Member:</b> ${s.total_members}</p>
        <p><b>Peminjaman Aktif:</b> ${s.active_loans}</p>
        <p><b>Total Denda:</b> Rp ${s.total_fines}</p>
    `;
}

function showMessage(result) {
    if (result.message) {
        alert(result.message);
    } else if (typeof result.detail === "string") {
        alert(result.detail);
    } else if (result.detail) {
        alert(JSON.stringify(result.detail, null, 2));
    } else {
        alert(JSON.stringify(result, null, 2));
    }
}

setLoginInfo();
loadBooks();