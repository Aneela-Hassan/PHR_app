# Personal Health Record (PHR) App

A patient-owned health record web application. Patients can log their doctor visits, upload test reports, and generate a secure, shareable QR code so any doctor can view their medical history without needing to log in.

## Features
- Secure signup/login (hashed passwords, session-based auth)
- Add visit records: diagnosis, medicines, advice, doctor name, date
- Upload test reports (PDF/image) via Cloudinary
- Shareable QR code + link for read-only, doctor-facing access
- Searchable visit timeline (filter by doctor, condition, date)
- Patient profile: allergies, current medicines, date of birth

## Tech Stack
- **Backend:** Flask (Python)
- **Database:** MongoDB Atlas
- **File Storage:** Cloudinary
- **Frontend:** HTML, CSS (no frameworks)
- **Auth:** Flask sessions, Werkzeug password hashing

## Setup
1. Clone this repo
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with:
