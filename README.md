# Intelligent Fleet & Route Booking Platform

*A full-stack Django architecture designed to handle dynamic vehicle inventory, route management, and seamless booking workflows.*

## 📖 Project Overview
This platform is a comprehensive fleet management system built to handle real-world booking complexities. It provides distinct interfaces and permission levels for standard users to book vehicles/routes, and an administrative backbone to control pricing, inventory, and travel routes. 

This project demonstrates scalable database design, containerized development, and robust MVC architecture.

## 🚀 Core Features

### 1. User/Customer Portal
* **Dedicated Dashboard:** Users can view their active, past, and pending bookings.
* **Booking Engine:** Users can select vehicles, pick specific travel routes, and lock in dates.
* **Status Tracking:** Real-time visibility into whether a booking is pending, approved, or completed.

### 2. Administrative Control Center
* **Dynamic Pricing:** Admins can adjust the daily rates of vehicles or specific route prices on the fly.
* **Route Management:** Admins can upload, create, and assign specific operational routes for the fleet.
* **Inventory Management:** Update vehicle statuses (Available, In Maintenance, Unavailable) to prevent booking conflicts.
* **Approval Workflow:** Review and approve or reject user booking requests.

## 🛠 Technical Stack
* **Backend Framework:** Python / Django 4.2+
* **Database:** PostgreSQL 15
* **Frontend:** Django Templates (HTML/CSS)
* **Infrastructure:** Docker & Docker Compose
* **Development Environment:** Linux (Arch / Ubuntu)

## 🗺 System Architecture & Data Flow
1. **The Route & Vehicle Setup:** Admins define the available `Vehicles` and the available `Routes` in the database.
2. **The Booking Transaction:** A user selects a combination of Vehicle + Route + Dates. The system calculates the total price based on admin-set parameters.
3. **The Lock:** Once booked, the system's availability engine prevents any other user from booking that specific vehicle for those overlapping dates.

## 📅 Development Roadmap (Phases)

### Phase 1: Core Backend & Database Design (Current)
- [ ] Initialize Docker & PostgreSQL environment.
- [ ] Build core Django Models (`Vehicle`, `Route`, `Booking`).
- [ ] Utilize Django's built-in Admin panel to securely manage data, set prices, and upload routes.

### Phase 2: User Experience
- [ ] Build Django Templates for the User Dashboard.
- [ ] Implement user registration, login, and authentication.
- [ ] Create the frontend booking form and confirmation flow.

### Phase 3: Custom Admin Dashboard (Future)
- [ ] Bypass the default Django admin to build a fully custom, branded Admin Dashboard using HTML/CSS.
- [ ] Implement advanced revenue analytics and route-tracking visualizations.

---
*Developed by Okemwa Brian Nyang'wara*