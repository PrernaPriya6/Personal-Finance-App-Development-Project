# Personal-Finance-App-Development-Project

* What the project does
* How to install/run it
* Features (income, expense, budget, backup, restore, reports)
* Example usage with screenshots 

# 📊 Personal Finance Manager (CLI)

A simple **command-line application** to manage your personal finances.
Track **income & expenses**, set **budgets**, and generate **financial reports** directly from the terminal.

---

## 🚀 Features

* 👤 User registration & login (with password hashing for security)
* 💰 Add income & expense transactions
* ✏️ Update or delete transactions
* 📜 View transactions with filters (date, category, type)
* 📊 Generate **monthly/yearly financial reports**
* 🎯 Set category-based budgets with alerts when exceeded
* 💾 Backup & restore data in JSON format
* 🔐 SQLite database for persistent storage

---

## ⚙️ Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/personal-finance-manager.git
   cd personal-finance-manager
   ```

2. Make sure you have **Python 3.8+** installed.
   Check with:

   ```bash
   python --version
   ```

3. Install required dependencies (only standard Python libraries are used, so no extra installation needed).

---

## ▶️ Usage

Run the program from the terminal:

```bash
python finance_manager.py
```

You’ll see:

```
=== Personal Finance Manager ===
1. Register
2. Login
3. Add Income
4. Add Expense
5. View Transactions
6. Update Transaction
7. Delete Transaction
8. Generate Report
9. Set Budget
10. View Budgets
11. Backup Data
12. Restore Data
13. Exit
================================
Enter your choice (1-13):
```

---

## 📝 Example Flow

1. **Register a new user**

   ```
   Enter username: prerna
   Enter password:
   Registration successful!
   ```

2. **Login**

   ```
   Enter username: prerna
   Enter password:
   Welcome, prerna!
   ```

3. **Add an expense**

   ```
   Enter expense amount: 200
   Enter category: Food
   Enter description (optional): Lunch
   Transaction added successfully!
   ```

4. **Generate a monthly report**

   ```
   --- Financial Report (monthly) ---
   Period: 2025-09-01 to 2025-09-14
   Total Income: $5000.00
   Total Expenses: $1200.00
   Savings: $3800.00

   Expenses by Category:
     Food: $600.00
     Travel: $300.00
     Entertainment: $300.00
   ```

---

## 📂 Project Structure

```
personal-finance-manager/
│
├── finance_manager.py   # Main CLI application
├── finance.db           # Auto-created SQLite database
├── README.md            # Documentation
└── backups/             # JSON backup files (optional)
```

---

## 🤝 Contributing

Pull requests are welcome!
For major changes, please open an issue first to discuss what you’d like to change.

---

## 📜 License

This project is licensed under the MIT License.

