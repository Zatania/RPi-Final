# RPi Server

This repository includes a setup for creating a virtual environment, installing required Python modules from a `requirements.txt` file, and running the Flask application.

## Getting Started

Follow these steps to set up your Flask project:

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

On macOS and Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 4. Install Required Python Modules

```bash
pip install -r requirements.txt
```


### 5. Initiate Database and add Admin Account
```bash
flask shell
from app import db, Admin, Beneficiary, Confirmation
from werkzeug.security import generate_password_hash
db.create_all()
new_admin = Admin(username='admin', password=generate_new_password('admin'), fullname = 'Admin Account')
db.session.add(new_admin)
db.session.commit()
exit()
```

### 6. Run the Flask Application

```bash
flask run
```

By default, the application will be available at http://127.0.0.1:5000/.

### 
