# cs348-project
**Coffee Ordering System for CS348 Project**

Coffee Café is a full-stack web application built using **Flask** and **MySQL**, designed to allow customers to view a menu, place and manage orders, generate reports, and manage their profiles. The app includes secure authentication, a user-friendly interface, and dynamically updated order and customer data.

<img width="1501" alt="Screenshot 2025-05-01 at 3 02 43 PM" src="https://github.com/user-attachments/assets/9db0f094-e079-4e0c-89c1-bffadd8a2212" />

---

## Features

- **Customer Registration & Login**
  - Password hashing with Flask-Login and Werkzeug
  - Session-based authentication
- **Menu Display**
  - Menu items categorized for easy navigation
- **Place Orders**
  - Users can select multiple items
  - Automatically calculates total price
- **Order History**
  - Users can view, edit, or delete past orders
- **Generate Reports**
  - Filter by date range, customer ID, or item
  - View statistics like total revenue, average order value, and most popular items
- **Customer Profile Management**
  - Edit or delete your account

---

## Technologies Used

- Flask (Web Framework)
- Flask-WTF (Form handling and validation)
- Flask-Login (User authentication)
- SQLAlchemy (ORM for database interaction)
- MySQL (Database)
- HTML/CSS for UI

