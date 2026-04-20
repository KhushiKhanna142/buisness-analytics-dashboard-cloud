# 📊 Data Analytics Dashboard on AWS

A cloud-based data analytics dashboard built as part of a Cloud Computing course project. The application leverages **Amazon S3** for storage and **Amazon EC2** for compute, demonstrating a real-world cloud data pipeline from file upload to insights.

---

## 🏗️ Architecture
| Service | Role |
|--------|------|
| Amazon S3 | Stores raw CSV/JSON files and processed reports |
| Amazon EC2 | Hosts the web app and runs data analysis scripts |
| IAM Role | Grants EC2 secure access to S3 without hardcoded credentials |
| boto3 | Python SDK used to connect EC2 and S3 |
| pandas | Data processing and statistical analysis |
| Dash | Interactive web dashboard framework |

---

## ⚙️ How It Works

1. User uploads a CSV file through the dashboard or directly to S3
2. EC2 fetches the file from the `raw-data/` folder in S3 using boto3
3. pandas loads and analyzes the data — row count, column stats, numeric summaries
4. Results are saved back to the `reports/` folder in S3 as JSON
5. Dashboard displays the analysis output and lists all saved reports

## 🗂️ Project Structure

```
analytics-dashboard-cloud/
├── app.py
├── analyze.py
├── requirements.txt
├── sample_data/
│   └── sample.csv
├── .gitignore
└── README.md
```
## 🛠️ Tech Stack

- **Cloud**: AWS EC2 (Ubuntu 22.04), AWS S3
- **Language**: Python 3.12
- **Libraries**: boto3, pandas, Dash, Plotly, Flask
- **Security**: IAM Role-based access (no hardcoded credentials)

---

## 🚀 Setup & Deployment

### Prerequisites
- AWS account with EC2 and S3 access
- EC2 instance with IAM role attached (AmazonS3FullAccess)
- Port 8050 open in EC2 security group

### Installation

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@<ec2-public-ip>

# Clone the repository
git clone https://github.com/yourusername/analytics-dashboard-cloud.git
cd analytics-dashboard-cloud

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install boto3 pandas dash plotly flask

# Set your bucket name in both files
nano app.py       # update BUCKET_NAME
nano analyze.py   # update BUCKET_NAME

# Run the app
python3 app.py
```

### Access the Dashboard
Open your browser and go to:
http://<ec2-public-ip>:8050
---

## 📁 S3 Bucket Structure
analytics-dashboard-cc-project/
├── raw-data/
│   └── sample.csv          # Uploaded input files
└── reports/
└── sample_results.json # Processed analysis output
---

## 📸 Screenshots

<img width="1458" height="805" alt="image" src="https://github.com/user-attachments/assets/5dca1056-4f0a-4e6d-9c9f-ed3a02977075" />


<img width="1458" height="441" alt="image" src="https://github.com/user-attachments/assets/5dc7894f-8a74-4faf-b636-77604e15c52d" />


<img width="976" height="827" alt="image" src="https://github.com/user-attachments/assets/2177a807-4b8e-461c-9eca-b43b5f967d7f" />


---

## 📄 Sample Data

The project includes a sample e-commerce dataset with 10 orders covering product name, category, quantity, price, city, and date — used to demonstrate the full pipeline end to end.

---

