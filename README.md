[README.md](https://github.com/user-attachments/files/24866787/README.md)
# Digital Twin–Based Smart Reefer Container with Early Fault Detection

This repository contains the complete implementation of a **digital twin simulation of a smart reefer container**, developed for **Transtech 2026**.  
The system integrates **physics-based modeling**, **interactive fault injection**, **cargo risk assessment**, and **machine learning–based early fault detection** within a single real-time platform.

---

## Key Features

- Real-time **digital twin** of a reefer container  
- Physics-based **temperature and humidity models**  
- Interactive **fault injection** (power failure, door opening, cooling failure)  
- **Cargo spoilage risk assessment**  
- **Machine learning–based early fault detection**  
- Live **dashboard with gauges, plots, and indicators**  
- ML-ready **time-series dataset generation**  
- Full-screen **exhibition / demo mode**

---

## System Overview

The digital twin continuously simulates the internal environment of a reefer container and mirrors its operational state.  
A trained **Random Forest classifier** analyzes recent sensor trends to predict whether a fault is likely to occur within the next few minutes, enabling **predictive monitoring** rather than reactive alarm-based systems.

---

## Repository Structure

```
Transtech_2026_Reefer_Digital_Twin/reefer_sim/
├── digital_twin_app.py
├── data_logger.py
├── thermal_model.py
├── humidity_model.py
├── risk_model.py
├── alarm_logic.py
├── reefer_state.py
├── train_early_fault_rf.py
├── early_fault_random_forest.pkl
├── logs/
│   └── reefer_dataset.csv
├── README.md
└── requirements.txt
```

---

## Dependencies

Python 3.9+

- numpy
- pandas
- matplotlib
- scikit-learn
- joblib
- PyQt5

---

## Running the Digital Twin

```bash
python digital_twin_app.py
```

Press **ESC** to exit full-screen mode.

---

## Citation

```
P. A. Prasad, “Digital Twin–Based Smart Reefer Container with Early Fault Detection,” GitHub repository, 2026.
Available: https://github.com/pranavprasad9973/Reefer_Digital_Twin
```

---

## Author

**Pranav Amit Prasad** - 
**Indian Maritime University, Kolkata**
