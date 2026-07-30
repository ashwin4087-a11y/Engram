# Monocular Face Distance Estimator — Backend

> **HackTronix 2.0 · Track B (AI Qualifier) · Task 2**

Estimates a person's **distance from the camera** and **horizontal viewing angle** using a single webcam and the **pinhole camera model**.

---

## Quick Start

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

Edit `.env` if needed:

```
CAMERA_INDEX=0
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 3. Start the server

```bash
python run.py
```

### 4. Verify

Open your browser:

- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
