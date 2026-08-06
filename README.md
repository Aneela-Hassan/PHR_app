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
5.  5. Run: `python app.py`
  
## Docker
This app can also be run using Docker:
`bash
docker build -t phr-app .
docker run -p 5001:5000 --env-file .env phr-app

Then visit `http://localhost:5001`

## Note
This is a learning/portfolio project — not intended to store real patient data, as it lacks full production-grade security compliance (e.g. email verification is currently format-only, not OTP/link-based).
