
## 📄 AI Resume Analyzer

### 🔍 Intelligent Resume Screening and Recommendation System

The **AI Resume Analyzer** is a Streamlit-based web application that uses Natural Language Processing (NLP) to parse resumes, extract important information, evaluate resume quality, and recommend personalized courses and skills to improve job readiness.

---

### 🚀 Features

* ✅ **PDF Resume Upload & Parsing**
* 🧠 **NLP-based Extraction**: Name, Email, Phone, Degree, Skills
* 🎯 **Skill-Based Job Field Prediction**: Data Science, Web, Android, iOS, UI/UX
* 📈 **Resume Scoring System** (out of 100)
* 🎓 **Course & Certification Recommendations**
* 📹 **Bonus Videos**: Resume Writing and Interview Tips
* 📊 **Admin Dashboard** with analytics and feedback visualization
* 🧾 **User Feedback & Registration System**
* 💾 **MySQL Database Integration** for data logging

---

### 🛠️ Tech Stack

* **Frontend**: Streamlit
* **Backend/NLP**: Python, spaCy, pdfminer, PyPDF2
* **Database**: MySQL (with pymysql)
* **Visualization**: Plotly, pandas
* **Authentication**: bcrypt (user password hashing)

---

### 📂 Project Structure

```bash
.
├── app.py                  # Main Streamlit application
├── resume_parser.py        # Core NLP resume parsing logic
├── courses.py              # Course/video recommendations dataset
├── Uploaded_Resumes/       # Folder to store user-uploaded PDFs
├── Logo/                   # Folder containing logo image
├── requirements.txt        # List of required Python libraries
└── README.md               # This file
```

---

### ⚙️ Setup Instructions

#### 1. Clone the Repository

```bash
git clone https://github.com/Deepakragavan1013/Resume-analyzer.git
cd Resume-analyzer
```

#### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Start MySQL Database

Make sure MySQL is running and a database named `cv` is created.

You can create one using:

```sql
CREATE DATABASE cv;
```

Update `app.py` with your MySQL credentials:

```python
connection = pymysql.connect(host='localhost', user='root', password='api', db='cv')
```

#### 5. Run the App

```bash
streamlit run app.py
```

---

### 📊 Admin Dashboard

* Username: `admin`
* Password: `admin123`

View resume stats, user analytics, and feedback through interactive charts.

---

### 📌 Demo Highlights

* Upload your resume (PDF only)
* Automatically extract personal and academic info
* Identify missing sections and get resume tips
* Recommended courses based on your skill set

---

### 🧪 Sample Skills Used for Field Prediction

| Field           | Sample Skills                           |
| --------------- | --------------------------------------- |
| Data Science    | TensorFlow, Scikit-learn, Deep Learning |
| Web Development | React, Node.js, Flask                   |
| Android         | Kotlin, Flutter, SQLite                 |
| iOS             | Swift, Xcode, Cocoa                     |
| UI/UX           | Figma, Adobe XD, Prototyping            |

---

### 📬 Feedback & Contributions

Feel free to:

* Raise issues
* Submit PRs
* Give feedback via the app or GitHub Issues

---

### 👨‍💻 Author

Built with ❤️ by [Deepakragavan J](http://127.0.0.1:5500/portfolio.html)

---

