# AI Retail Demand Intelligence Platform

A high-performance retail analytics suite with glassmorphic UI, dynamic ETL pipelines, and AI-driven demand forecasting.

## 🚀 How to Run in VS Code

To run this project locally with the full AI inference engine, follow these steps:

### 1. Open the Project
Open the **`C:\AI RETAIL`** folder directly in VS Code.

### 2. Select the Python Interpreter (Crucial)
1. Press `Ctrl + Shift + P` to open the Command Palette.
2. Type **`Python: Select Interpreter`** and press Enter.
3. Choose the interpreter located in the **`venv`** folder (e.g., `.\venv\Scripts\python.exe`).

### 3. Run the Application
I have already pre-configured the **`launch.json`** for you:
1. Click the **Run and Debug** icon in the sidebar (or press `Ctrl + Shift + D`).
2. At the top of the sidebar, select **"Python: Flask"** from the dropdown.
3. Press the **Green Play Button** (or press `F5`).

### 4. Access the Dashboard
Once the server starts, open your browser and go to:
**[http://localhost:5000](http://localhost:5000)**

---

## 🛠 Features
- **Dynamic ETL**: Automatically infers database schemas from uploaded CSV/Excel files.
- **AI Forecasting**: Uses Holt-Winters Exponential Smoothing for 90-day demand predictions.
- **Demand Intelligence**: Live KPI tracking and category-level drill-downs.
- **Modern UI**: Full glassmorphism theme with dark mode support.

## 📦 Deployment
This project is pre-configured for **Render.com** via the included `render.yaml` blueprint.
