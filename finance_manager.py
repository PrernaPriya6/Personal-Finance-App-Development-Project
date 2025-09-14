import sqlite3
import hashlib
import datetime
import getpass
import json
import os
from typing import List, Dict, Tuple, Optional

class PersonalFinanceManager:
    def __init__(self, db_name: str = "finance.db"):
        self.db_name = db_name
        self.current_user = None
        self.setup_database()
        
    def setup_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, category, month, year)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str) -> bool:
        """Register a new user"""
        if not username or not password:
            print("Username and password cannot be empty.")
            return False
            
        hashed_password = self.hash_password(password)
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            print("Registration successful!")
            return True
        except sqlite3.IntegrityError:
            print("Username already exists. Please choose a different one.")
            return False
        finally:
            conn.close()
    
    def login(self, username: str, password: str) -> bool:
        """Authenticate user"""
        hashed_password = self.hash_password(password)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.current_user = user[0]
            print(f"Welcome, {username}!")
            return True
        else:
            print("Invalid username or password.")
            return False
    
    def add_transaction(self, transaction_type: str, amount: float, category: str, description: str = "") -> bool:
        """Add a new transaction (income or expense)"""
        if not self.current_user:
            print("Please log in first.")
            return False
            
        if transaction_type not in ['income', 'expense']:
            print("Transaction type must be 'income' or 'expense'.")
            return False
            
        if amount <= 0:
            print("Amount must be positive.")
            return False
            
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (user_id, type, amount, category, description, date) VALUES (?, ?, ?, ?, ?, ?)",
                (self.current_user, transaction_type, amount, category, description, date)
            )
            conn.commit()
            print("Transaction added successfully!")
            
            # Check if budget is exceeded
            self.check_budget(category, amount)
            
            return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False
        finally:
            conn.close()
    
    def update_transaction(self, transaction_id: int, amount: float = None, category: str = None, description: str = None) -> bool:
        """Update an existing transaction"""
        if not self.current_user:
            print("Please log in first.")
            return False
            
        # Build the update query dynamically based on provided parameters
        updates = []
        params = []
        
        if amount is not None:
            if amount <= 0:
                print("Amount must be positive.")
                return False
            updates.append("amount = ?")
            params.append(amount)
            
        if category is not None:
            updates.append("category = ?")
            params.append(category)
            
        if description is not None:
            updates.append("description = ?")
            params.append(description)
            
        if not updates:
            print("No updates provided.")
            return False
            
        params.append(transaction_id)
        params.append(self.current_user)
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE transactions SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
                params
            )
            
            if cursor.rowcount == 0:
                print("Transaction not found or you don't have permission to update it.")
                return False
                
            conn.commit()
            print("Transaction updated successfully!")
            return True
        except Exception as e:
            print(f"Error updating transaction: {e}")
            return False
        finally:
            conn.close()
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        if not self.current_user:
            print("Please log in first.")
            return False
            
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM transactions WHERE id = ? AND user_id = ?",
                (transaction_id, self.current_user)
            )
            
            if cursor.rowcount == 0:
                print("Transaction not found or you don't have permission to delete it.")
                return False
                
            conn.commit()
            print("Transaction deleted successfully!")
            return True
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return False
        finally:
            conn.close()
    
    def get_transactions(self, start_date: str = None, end_date: str = None, category: str = None, transaction_type: str = None) -> List[Dict]:
        """Retrieve transactions with optional filters"""
        if not self.current_user:
            print("Please log in first.")
            return []
            
        query = "SELECT id, type, amount, category, description, date FROM transactions WHERE user_id = ?"
        params = [self.current_user]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        if category:
            query += " AND category = ?"
            params.append(category)
            
        if transaction_type:
            query += " AND type = ?"
            params.append(transaction_type)
            
        query += " ORDER BY date DESC"
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(query, params)
            transactions = cursor.fetchall()
            
            result = []
            for trans in transactions:
                result.append({
                    'id': trans[0],
                    'type': trans[1],
                    'amount': trans[2],
                    'category': trans[3],
                    'description': trans[4],
                    'date': trans[5]
                })
                
            return result
        except Exception as e:
            print(f"Error retrieving transactions: {e}")
            return []
        finally:
            conn.close()
    
    def generate_report(self, period: str = "monthly") -> Dict:
        """Generate financial report for the specified period"""
        if not self.current_user:
            print("Please log in first.")
            return {}
            
        now = datetime.datetime.now()
        
        if period == "monthly":
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        elif period == "yearly":
            start_date = now.replace(month=1, day=1).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        else:
            print("Invalid period. Use 'monthly' or 'yearly'.")
            return {}
            
        transactions = self.get_transactions(start_date, end_date)
        
        total_income = 0
        total_expenses = 0
        category_expenses = {}
        
        for trans in transactions:
            if trans['type'] == 'income':
                total_income += trans['amount']
            else:
                total_expenses += trans['amount']
                category_expenses[trans['category']] = category_expenses.get(trans['category'], 0) + trans['amount']
        
        savings = total_income - total_expenses
        
        return {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'savings': savings,
            'category_expenses': category_expenses
        }
    
    def set_budget(self, category: str, amount: float) -> bool:
        """Set monthly budget for a category"""
        if not self.current_user:
            print("Please log in first.")
            return False
            
        if amount <= 0:
            print("Budget amount must be positive.")
            return False
            
        now = datetime.datetime.now()
        month = now.month
        year = now.year
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO budgets (user_id, category, amount, month, year) VALUES (?, ?, ?, ?, ?)",
                (self.current_user, category, amount, month, year)
            )
            conn.commit()
            print(f"Budget for {category} set to ${amount:.2f} for {now.strftime('%B %Y')}.")
            return True
        except Exception as e:
            print(f"Error setting budget: {e}")
            return False
        finally:
            conn.close()
    
    def check_budget(self, category: str, amount: float) -> bool:
        """Check if a transaction exceeds the budget for its category"""
        if not self.current_user:
            return False
            
        now = datetime.datetime.now()
        month = now.month
        year = now.year
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT amount FROM budgets WHERE user_id = ? AND category = ? AND month = ? AND year = ?",
                (self.current_user, category, month, year)
            )
            budget = cursor.fetchone()
            
            if not budget:
                return False
                
            budget_amount = budget[0]
            
            # Calculate total expenses for this category in the current month
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            
            expenses = self.get_transactions(start_date, end_date, category, 'expense')
            total_spent = sum(trans['amount'] for trans in expenses)
            
            if total_spent > budget_amount:
                print(f"Warning: You have exceeded your budget for {category}!")
                print(f"Budget: ${budget_amount:.2f}, Spent: ${total_spent:.2f}")
                return True
                
        except Exception as e:
            print(f"Error checking budget: {e}")
            return False
        finally:
            conn.close()
            
        return False
    
    def get_budgets(self) -> List[Dict]:
        """Get all budgets for the current user"""
        if not self.current_user:
            print("Please log in first.")
            return []
            
        now = datetime.datetime.now()
        month = now.month
        year = now.year
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category, amount FROM budgets WHERE user_id = ? AND month = ? AND year = ?",
                (self.current_user, month, year)
            )
            budgets = cursor.fetchall()
            
            result = []
            for budget in budgets:
                result.append({
                    'category': budget[0],
                    'amount': budget[1]
                })
                
            return result
        except Exception as e:
            print(f"Error retrieving budgets: {e}")
            return []
        finally:
            conn.close()
    
    def backup_data(self, backup_file: str) -> bool:
        """Backup user data to a JSON file"""
        if not self.current_user:
            print("Please log in first.")
            return False
            
        try:
            # Get transactions
            transactions = self.get_transactions()
            
            # Get budgets
            budgets = self.get_budgets()
            
            # Create backup data structure
            backup_data = {
                'user_id': self.current_user,
                'backup_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'transactions': transactions,
                'budgets': budgets
            }
            
            # Write to file
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=4)
                
            print(f"Backup created successfully: {backup_file}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_data(self, backup_file: str) -> bool:
        """Restore user data from a JSON file"""
        if not self.current_user:
            print("Please log in first.")
            return False
            
        try:
            # Read backup file
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
                
            # Verify user ID matches
            if backup_data['user_id'] != self.current_user:
                print("Backup file does not belong to the current user.")
                return False
                
            # Clear existing data
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (self.current_user,))
            cursor.execute("DELETE FROM budgets WHERE user_id = ?", (self.current_user,))
            
            # Restore transactions
            for trans in backup_data['transactions']:
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, category, description, date) VALUES (?, ?, ?, ?, ?, ?)",
                    (self.current_user, trans['type'], trans['amount'], trans['category'], trans['description'], trans['date'])
                )
                
            # Restore budgets
            now = datetime.datetime.now()
            for budget in backup_data['budgets']:
                cursor.execute(
                    "INSERT INTO budgets (user_id, category, amount, month, year) VALUES (?, ?, ?, ?, ?)",
                    (self.current_user, budget['category'], budget['amount'], now.month, now.year)
                )
                
            conn.commit()
            conn.close()
            
            print("Data restored successfully!")
            return True
        except Exception as e:
            print(f"Error restoring data: {e}")
            return False

def display_menu():
    """Display the main menu"""
    print("\n=== Personal Finance Manager ===")
    print("1. Register")
    print("2. Login")
    print("3. Add Income")
    print("4. Add Expense")
    print("5. View Transactions")
    print("6. Update Transaction")
    print("7. Delete Transaction")
    print("8. Generate Report")
    print("9. Set Budget")
    print("10. View Budgets")
    print("11. Backup Data")
    print("12. Restore Data")
    print("13. Exit")
    print("================================")

def main():
    """Main function to run the application"""
    manager = PersonalFinanceManager()
    
    while True:
        display_menu()
        choice = input("Enter your choice (1-13): ").strip()
        
        if choice == '1':
            username = input("Enter username: ").strip()
            password = getpass.getpass("Enter password: ")
            manager.register_user(username, password)
            
        elif choice == '2':
            username = input("Enter username: ").strip()
            password = getpass.getpass("Enter password: ")
            manager.login(username, password)
            
        elif choice == '3':
            try:
                amount = float(input("Enter income amount: "))
                category = input("Enter category: ").strip()
                description = input("Enter description (optional): ").strip()
                manager.add_transaction('income', amount, category, description)
            except ValueError:
                print("Invalid amount. Please enter a number.")
                
        elif choice == '4':
            try:
                amount = float(input("Enter expense amount: "))
                category = input("Enter category: ").strip()
                description = input("Enter description (optional): ").strip()
                manager.add_transaction('expense', amount, category, description)
            except ValueError:
                print("Invalid amount. Please enter a number.")
                
        elif choice == '5':
            print("\nFilter options:")
            print("1. All transactions")
            print("2. By date range")
            print("3. By category")
            print("4. By type (income/expense)")
            filter_choice = input("Enter your choice (1-4): ").strip()
            
            start_date = None
            end_date = None
            category = None
            trans_type = None
            
            if filter_choice == '2':
                start_date = input("Enter start date (YYYY-MM-DD): ").strip()
                end_date = input("Enter end date (YYYY-MM-DD): ").strip()
            elif filter_choice == '3':
                category = input("Enter category: ").strip()
            elif filter_choice == '4':
                trans_type = input("Enter type (income/expense): ").strip().lower()
                
            transactions = manager.get_transactions(start_date, end_date, category, trans_type)
            
            if not transactions:
                print("No transactions found.")
            else:
                print("\nTransactions:")
                print("-" * 80)
                for trans in transactions:
                    print(f"ID: {trans['id']} | {trans['date']} | {trans['type'].upper()} | "
                          f"${trans['amount']:.2f} | {trans['category']} | {trans['description']}")
                print("-" * 80)
                total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
                total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
                print(f"Total Income: ${total_income:.2f} | Total Expense: ${total_expense:.2f} | "
                      f"Net: ${(total_income - total_expense):.2f}")
                
        elif choice == '6':
            try:
                trans_id = int(input("Enter transaction ID to update: "))
                print("Leave field blank to keep current value:")
                amount_str = input("Enter new amount: ").strip()
                amount = float(amount_str) if amount_str else None
                category = input("Enter new category: ").strip()
                if not category:
                    category = None
                description = input("Enter new description: ").strip()
                if not description:
                    description = None
                    
                manager.update_transaction(trans_id, amount, category, description)
            except ValueError:
                print("Invalid transaction ID or amount.")
                
        elif choice == '7':
            try:
                trans_id = int(input("Enter transaction ID to delete: "))
                manager.delete_transaction(trans_id)
            except ValueError:
                print("Invalid transaction ID.")
                
        elif choice == '8':
            period = input("Enter period (monthly/yearly): ").strip().lower()
            report = manager.generate_report(period)
            
            if report:
                print(f"\n--- Financial Report ({report['period']}) ---")
                print(f"Period: {report['start_date']} to {report['end_date']}")
                print(f"Total Income: ${report['total_income']:.2f}")
                print(f"Total Expenses: ${report['total_expenses']:.2f}")
                print(f"Savings: ${report['savings']:.2f}")
                
                if report['category_expenses']:
                    print("\nExpenses by Category:")
                    for category, amount in report['category_expenses'].items():
                        print(f"  {category}: ${amount:.2f}")
                        
        elif choice == '9':
            category = input("Enter category: ").strip()
            try:
                amount = float(input("Enter budget amount: "))
                manager.set_budget(category, amount)
            except ValueError:
                print("Invalid amount. Please enter a number.")
                
        elif choice == '10':
            budgets = manager.get_budgets()
            
            if not budgets:
                print("No budgets set for this month.")
            else:
                print("\nCurrent Budgets:")
                print("-" * 40)
                for budget in budgets:
                    print(f"{budget['category']}: ${budget['amount']:.2f}")
                print("-" * 40)
                
        elif choice == '11':
            backup_file = input("Enter backup filename: ").strip()
            if not backup_file:
                backup_file = f"finance_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            manager.backup_data(backup_file)
            
        elif choice == '12':
            backup_file = input("Enter backup filename: ").strip()
            if os.path.exists(backup_file):
                manager.restore_data(backup_file)
            else:
                print("Backup file not found.")
                
        elif choice == '13':
            print("Thank you for using Personal Finance Manager!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()