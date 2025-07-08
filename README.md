# DWEE_Website

This project was developed during a one-month full-stack web development internship at **DWEE**, from May 26 to June 26, 2025, by **Nour Yaakoub**, **Ikram Kalkoul**, and **Eya ben Ismail**. The project aimed to digitize and optimize internal business processes related to D-KIT management, user registration, maintenance scheduling, and client support.

## 🛠 Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Database**: MySQL

---

## 📋 Project Overview

The platform consists of two main interfaces:

1. **Client Interface**
2. **Super Admin Interface**

Each section contains several submodules described below.

---

## 👤 Client Interface

### 1. Authentication (Login/Register)
- Users can register and select their country and province (API integration for countries).
- Password reset via email with secure update to the database.
- Known Issues:
  - Province API not working.
  - Some messages not translated into French.

### 2. Dashboard
- Shows quick actions like booking maintenance or accessing support.
- If no D-KIT is assigned, sections appear empty (expected behavior).

### 3. Mes D-KITs
- Users can request multiple D-KIT additions.
- After admin validation, device appears with a 1-year warranty.
- Known Issues:
  - Hardcoded data (e.g. maintenance dates).
  - Refresh required to update views.

### 4. Maintenance Requests
- Users can request emergency maintenance.
- Maintenance goes through several statuses: scheduled → confirmed.
- Known Issues:
  - No form prefill on edit.
  - Past dates and weekends are selectable.

### 5. Profile Management
- Users can update basic info.
- Known Issues:
  - Country and province not editable.

### 6. Support Chatbot
- Integrated with [DocsBot AI](https://docsbot.ai)
- Handles:
  - After-sale contact
  - Product settings
  - Feedback collection
  - Warranty/usage guidance

### 7. Become a Commercial Partner
- Available for companies to register as resellers.
- Frontend ready; backend incomplete.

---

## 🛡️ Super Admin Interface

### 1. Authentication
- Admins log in with special credentials.
- Passwords are manageable via MySQL directly.

### 2. Dashboard
- Displays:
  - Number of clients, D-KITs added
  - D-KITs active/inactive ratio
  - Upcoming appointments
- Known Issues:
  - Some stats not working due to recent code changes.

### 3. User Management
- Add/Edit/Delete clients
- Filter users by D-KIT assignment
- Known Issues:
  - Modify/Delete buttons broken
  - Missing search bar

### 4. Maintenance Management
- Confirm/Reject appointments
- Support for urgent and regular (annual) maintenance
- Known Issues:
  - Button color feedback missing
  - Rejected requests not properly handled

### 5. Device Management

#### a. Stock Management
- Add D-KIT to stock
- Known Issues:
  - Wrong DB table used (should be `stock`, not `devices`)
  - Modify/Delete not functional
  - Missing fields: manufacturing date, battery type, etc.

#### b. Assignment to Clients
- D-KITs can be assigned manually or via user requests.
- Validated devices appear in user dashboards.
- Known Issues:
  - Auto-complete missing
  - Warranty and model sometimes not saved

#### c. Regular Maintenance
- Auto-scheduled 1 year after D-KIT assignment.
- Visible in both admin and user calendars.

---

## 🚧 Known Issues & Improvements

- Dynamic updates (avoid hardcoded values)
- French translation of all UI text
- Improve UX with auto-suggestions and pre-filled forms
- Strengthen data consistency across `stock`, `devices`, and `users` tables
- Complete the backend logic for the commercial partner module

---

## 🙏 Acknowledgments

Special thanks to **Mr. Amine Rkhis** and **Mrs. Neirouz Rawen** for their continuous guidance and support throughout this internship experience.

---

## 📌 Future Work

This platform is still under active development. Planned next steps include:
- Finalizing backend features
- Enhancing database schemas
- Deploying the application to a production environment

---

## 🔒 Admin Credentials (for testing only)
> **⚠️ For development/testing purposes only. Do not use in production.**
see database
