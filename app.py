# AI Resume Analyzer
# Built with Streamlit for resume parsing, analysis, and recommendations

import streamlit as st
import pandas as pd
import base64
import time
import datetime
import pymysql
import socket
import platform
import geocoder
import secrets
import io
import random
import plotly.express as px
from geopy.geocoders import Nominatim
from streamlit_tags import st_tags
from PIL import Image
import nltk
import bcrypt
import os
import getpass
from resume_parser import ResumeParser  # Import custom parser
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage

nltk.download('stopwords')

# Mock data for course recommendations
ds_course = [("Data Science 101", "https://example.com/ds101"), ("ML Basics", "https://example.com/ml")]
web_course = [("React JS", "https://example.com/react"), ("Django", "https://example.com/django")]
android_course = [("Flutter", "https://example.com/flutter"), ("Kotlin", "https://example.com/kotlin")]
ios_course = [("Swift", "https://example.com/swift"), ("Xcode", "https://example.com/xcode")]
uiux_course = [("Figma", "https://example.com/figma"), ("Adobe XD", "https://example.com/adobexd")]
resume_videos = ["https://www.youtube.com/watch?v=resume1"]
interview_videos = ["https://www.youtube.com/watch?v=interview1"]

# Utility Functions
def get_csv_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'

def pdf_reader(file_path):
    try:
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
        page_interpreter = PDFPageInterpreter(resource_manager, converter)
        with open(file_path, 'rb') as fh:
            for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
                page_interpreter.process_page(page)
            text = fake_file_handle.getvalue()
        converter.close()
        fake_file_handle.close()
        return text
    except Exception as e:
        st.error(f"Error reading PDF text: {str(e)}")
        return None

def show_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")

def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations**")
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    rec_course = []
    for c, (c_name, c_link) in enumerate(course_list, 1):
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

# Database Setup
try:
    connection = pymysql.connect(host='localhost', user='root', password='your_password', db='cv')
    cursor = connection.cursor()
except Exception as e:
    st.error(f"Database connection failed: {str(e)}")
    st.stop()

def insert_data(sec_token, ip_add, host_name, dev_user, os_name_ver, latlong, city, state, country, 
                act_name, act_mail, act_mob, name, email, res_score, timestamp, no_of_pages, 
                reco_field, cand_level, skills, recommended_skills, courses, pdf_name):
    try:
        insert_sql = """INSERT INTO user_data 
                        (sec_token, ip_add, host_name, dev_user, os_name_ver, latlong, city, state, country, 
                         act_name, act_mail, act_mob, Name, Email_ID, resume_score, Timestamp, Page_no, 
                         Predicted_Field, User_level, Actual_skills, Recommended_skills, Recommended_courses, pdf_name) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(insert_sql, (sec_token, ip_add, host_name, dev_user, os_name_ver, str(latlong), city, state, country, 
                                   act_name, act_mail, act_mob, name, email, res_score, timestamp, no_of_pages, 
                                   reco_field, cand_level, skills, recommended_skills, courses, pdf_name))
        connection.commit()
    except Exception as e:
        st.error(f"Error inserting data: {str(e)}")

def insertf_data(feed_name, feed_email, feed_score, comments, timestamp):
    try:
        insert_sql = """INSERT INTO user_feedback 
                        (feed_name, feed_email, feed_score, comments, Timestamp) 
                        VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(insert_sql, (feed_name, feed_email, feed_score, comments, timestamp))
        connection.commit()
    except Exception as e:
        st.error(f"Error inserting feedback: {str(e)}")

def insert_student_user(username, password, name, email):
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        insert_sql = """INSERT INTO student_users (username, password, name, email) 
                        VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_sql, (username, hashed_password, name, email))
        connection.commit()
        return True
    except pymysql.err.IntegrityError:
        return False  # Username already exists
    except Exception as e:
        st.error(f"Error registering user: {str(e)}")
        return False

def verify_student_user(username, password):
    try:
        cursor.execute("SELECT password, name, email FROM student_users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result:
            stored_password, name, email = result
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                return True, name, email
        return False, None, None
    except Exception as e:
        st.error(f"Error verifying user: {str(e)}")
        return False, None, None

# Streamlit Configuration
st.set_page_config(page_title="AI Resume Analyzer", page_icon=":page_facing_up:")

def run():
    # Create Uploaded_Resumes directory if it doesn't exist
    os.makedirs("./Uploaded_Resumes", exist_ok=True)

    # UI Setup
    img = Image.open('./Logo/RESUM1.png')
    st.image(img, caption="Resume Analyzer Logo",width=600)
    st.sidebar.markdown("# Navigation")
    activities = ["User", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Select Option:", activities)
    st.sidebar.markdown("Built by [Deepakragavan J](http://127.0.0.1:5500/portfolio.html)", unsafe_allow_html=True)

    # Database Initialization
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS cv")
        cursor.execute("""CREATE TABLE IF NOT EXISTS user_data (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            sec_token VARCHAR(20),
            ip_add VARCHAR(50),
            host_name VARCHAR(50),
            dev_user VARCHAR(50),
            os_name_ver VARCHAR(50),
            latlong VARCHAR(50),
            city VARCHAR(50),
            state VARCHAR(50),
            country VARCHAR(50),
            act_name VARCHAR(50),
            act_mail VARCHAR(50),
            act_mob VARCHAR(20),
            Name VARCHAR(500),
            Email_ID VARCHAR(500),
            resume_score VARCHAR(8),
            Timestamp VARCHAR(50),
            Page_no VARCHAR(5),
            Predicted_Field BLOB,
            User_level BLOB,
            Actual_skills BLOB,
            Recommended_skills BLOB,
            Recommended_courses BLOB,
            pdf_name VARCHAR(50)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS user_feedback (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            feed_name VARCHAR(50),
            feed_email VARCHAR(50),
            feed_score VARCHAR(5),
            comments VARCHAR(100),
            Timestamp VARCHAR(50)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS student_users (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(100),
            name VARCHAR(50),
            email VARCHAR(50)
        )""")
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        st.stop()

    # User Section
    if choice == "User":
        st.markdown("### Student Login")
        action = st.radio("Select Action:", ("Login", "Register"))

        if action == "Register":
            with st.form("register_form"):
                st.write("Register New Student Account")
                reg_username = st.text_input("Username*")
                reg_password = st.text_input("Password*", type="password")
                reg_name = st.text_input("Full Name*")
                reg_email = st.text_input("Email*")
                submitted = st.form_submit_button("Register")
                if submitted:
                    if reg_username and reg_password and reg_name and reg_email:
                        if insert_student_user(reg_username, reg_password, reg_name, reg_email):
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Username already exists.")
                    else:
                        st.error("All fields are required.")

        elif action == "Login":
            with st.form("login_form"):
                st.write("Login to Your Account")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                if submitted:
                    success, name, email = verify_student_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.name = name
                        st.session_state.email = email
                        st.success(f"Welcome, {name}!")
                    else:
                        st.error("Invalid username or password.")

        if st.session_state.get("logged_in", False):
            act_name = st.session_state.name
            act_mail = st.session_state.email
            act_mob = st.text_input("Mobile Number*")
            sec_token = secrets.token_urlsafe(12)
            host_name = socket.gethostname()
            ip_add = socket.gethostbyname(host_name)
            dev_user = getpass.getuser()
            os_name_ver = f"{platform.system()} {platform.release()}"
            g = geocoder.ip('me')
            latlong = g.latlng
            geolocator = Nominatim(user_agent="resume_analyzer")
            location = geolocator.reverse(latlong, language='en') if latlong else None
            address = location.raw['address'] if location else {}
            city = address.get('city', '')
            state = address.get('state', '')
            country = address.get('country', '')

            st.markdown("### Upload Your Resume")
            pdf_file = st.file_uploader("Choose a PDF resume", type=["pdf"], key="resume_uploader")
            if pdf_file:
                try:
                    with st.spinner("Analyzing resume..."):
                        # Save uploaded file
                        save_path = f"./Uploaded_Resumes/{pdf_file.name}"
                        with open(save_path, "wb") as f:
                            f.write(pdf_file.getbuffer())
                        st.success("Resume uploaded successfully!")

                        # Display PDF
                        show_pdf(save_path)

                        # Parse resume using custom ResumeParser
                        resume_data = ResumeParser(pdf_file).get_extracted_data()
                        resume_text = pdf_reader(save_path)

                        if 'error' in resume_data:
                            st.error(f"Resume parsing failed: {resume_data['error']}")
                        elif resume_data and resume_text:
                            st.header("Resume Analysis")
                            st.success(f"Hello {resume_data.get('name', 'User')}")
                            st.subheader("Basic Info")
                            st.text(f"Name: {resume_data.get('name', 'N/A')}")
                            st.text(f"Email: {resume_data.get('email', 'N/A')}")
                            st.text(f"Contact: {resume_data.get('mobile_number', 'N/A')}")
                            st.text(f"Degree: {resume_data.get('degree', 'N/A')}")
                            st.text(f"Resume Pages: {resume_data.get('no_of_pages', 'N/A')}")

                            # Experience Level
                            cand_level = "Fresher"
                            if resume_data.get('no_of_pages', 0) < 1:
                                st.markdown("**Fresher Level**", unsafe_allow_html=True)
                            elif resume_text and any(x in resume_text.upper() for x in ["INTERNSHIP", "INTERNSHIPS"]):
                                cand_level = "Intermediate"
                                st.markdown("**Intermediate Level**", unsafe_allow_html=True)
                            elif resume_text and any(x in resume_text.upper() for x in ["EXPERIENCE", "WORK EXPERIENCE"]):
                                cand_level = "Experienced"
                                st.markdown("**Experienced Level**", unsafe_allow_html=True)

                            # Skills Analysis
                            st.subheader("Skills Recommendation")
                            skills = resume_data.get('skills', [])
                            keywords = st_tags(label="Current Skills", value=skills, key="skills")
                            ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                            web_keyword = ['react', 'django', 'node js', 'php', 'laravel', 'wordpress', 'javascript', 'flask']
                            android_keyword = ['android', 'flutter', 'kotlin', 'xml']
                            ios_keyword = ['ios', 'swift', 'cocoa', 'xcode']
                            uiux_keyword = ['ux', 'adobe xd', 'figma', 'ui', 'prototyping', 'wireframes', 'photoshop']
                            n_any = ['english', 'communication', 'microsoft office']

                            recommended_skills = []
                            reco_field = ""
                            rec_course = ""
                            for skill in skills:
                                skill_lower = skill.lower()
                                if skill_lower in ds_keyword:
                                    reco_field = "Data Science"
                                    recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Data Mining', 'Scikit-learn', 'Tensorflow']
                                    st.success("Looking for Data Science Jobs")
                                    st_tags(label="Recommended Skills", value=recommended_skills, key="ds_skills")
                                    rec_course = course_recommender(ds_course)
                                    break
                                elif skill_lower in web_keyword:
                                    reco_field = "Web Development"
                                    recommended_skills = ['React', 'Django', 'Node JS', 'PHP', 'Flask']
                                    st.success("Looking for Web Development Jobs")
                                    st_tags(label="Recommended Skills", value=recommended_skills, key="web_skills")
                                    rec_course = course_recommender(web_course)
                                    break
                                elif skill_lower in android_keyword:
                                    reco_field = "Android Development"
                                    recommended_skills = ['Flutter', 'Kotlin', 'XML', 'Java', 'SQLite']
                                    st.success("Looking for Android Development Jobs")
                                    st_tags(label="Recommended Skills", value=recommended_skills, key="android_skills")
                                    rec_course = course_recommender(android_course)
                                    break
                                elif skill_lower in ios_keyword:
                                    reco_field = "IOS Development"
                                    recommended_skills = ['Swift', 'Cocoa Touch', 'Xcode', 'Objective-C']
                                    st.success("Looking for IOS Development Jobs")
                                    st_tags(label="Recommended Skills", value=recommended_skills, key="ios_skills")
                                    rec_course = course_recommender(ios_course)
                                    break
                                elif skill_lower in uiux_keyword:
                                    reco_field = "UI-UX Development"
                                    recommended_skills = ['Figma', 'Adobe XD', 'Prototyping', 'Wireframes']
                                    st.success("Looking for UI-UX Development Jobs")
                                    st_tags(label="Recommended Skills", value=recommended_skills, key="uiux_skills")
                                    rec_course = course_recommender(uiux_course)
                                    break
                                elif skill_lower in n_any:
                                    reco_field = "NA"
                                    recommended_skills = ['No Recommendations']
                                    st.warning("Only Data Science, Web, Android, IOS, and UI/UX supported")
                                    st_tags(label="Recommended Skills", value=recommended_skills, key="na_skills")
                                    rec_course = "Not Available"
                                    break

                            # Resume Scoring
                            st.subheader("Resume Tips")
                            resume_score = 0
                            sections = [
                                ("Objective or Summary", ["OBJECTIVE", "SUMMARY"], 6),
                                ("Education", ["EDUCATION", "SCHOOL", "COLLEGE"], 12),
                                ("Experience", ["EXPERIENCE", "WORK EXPERIENCE"], 16),
                                ("Internships", ["INTERNSHIP", "INTERNSHIPS"], 6),
                                ("Skills", ["SKILL", "SKILLS"], 7),
                                ("Hobbies", ["HOBBIES"], 4),
                                ("Interests", ["INTERESTS"], 5),
                                ("Achievements", ["ACHIEVEMENTS"], 13),
                                ("Certifications", ["CERTIFICATION", "CERTIFICATIONS"], 12),
                                ("Projects", ["PROJECT", "PROJECTS"], 19)
                            ]
                            for section_name, keywords, score in sections:
                                if resume_text and any(k in resume_text.upper() for k in keywords):
                                    resume_score += score
                                    st.markdown(f"[+] Added {section_name}", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"[-] Add {section_name} to improve your resume", unsafe_allow_html=True)

                            st.subheader("Resume Score")
                            st.progress(resume_score)
                            st.success(f"Your Resume Score: {resume_score}/100")
                            st.warning("Score based on resume content")

                            # Store Data
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                            insert_data(sec_token, ip_add, host_name, dev_user, os_name_ver, latlong, city, state, country, 
                                        act_name, act_mail, act_mob, resume_data.get('name', 'N/A'), resume_data.get('email', 'N/A'), 
                                        str(resume_score), timestamp, str(resume_data.get('no_of_pages', 'N/A')), 
                                        reco_field, cand_level, str(skills), str(recommended_skills), 
                                        str(rec_course), pdf_file.name)

                            # Bonus Videos
                            st.header("Resume Writing Tips")
                            st.video(random.choice(resume_videos))
                            st.header("Interview Tips")
                            st.video(random.choice(interview_videos))
                            st.balloons()
                        else:
                            st.error("Failed to parse resume. Please ensure the PDF is valid and contains extractable text.")
                except Exception as e:
                    st.error(f"Error processing resume: {str(e)}")
            else:
                st.info("Please upload a PDF resume to proceed.")

    # Feedback Section
    elif choice == "Feedback":
        with st.form("feedback_form"):
            st.write("Feedback Form")
            feed_name = st.text_input("Name")
            feed_email = st.text_input("Email")
            feed_score = st.slider("Rate Us (1-5)", 1, 5)
            comments = st.text_input("Comments")
            submitted = st.form_submit_button("Submit")
            if submitted:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                insertf_data(feed_name, feed_email, str(feed_score), comments, timestamp)
                st.success("Feedback Submitted!")
                st.balloons()

        query = "SELECT * FROM user_feedback"
        try:
            feedback_data = pd.read_sql(query, connection)
            st.subheader("User Ratings")
            fig = px.pie(values=feedback_data['feed_score'].value_counts(), 
                         names=feedback_data['feed_score'].unique(), 
                         title="User Rating Distribution")
            st.plotly_chart(fig)

            st.subheader("User Comments")
            st.dataframe(feedback_data[['feed_name', 'comments']], width=1000)
        except Exception as e:
            st.error(f"Error retrieving feedback: {str(e)}")

    # About Section
    elif choice == "About":
        st.subheader("About AI Resume Analyzer")
        st.markdown("""
            This tool uses NLP to parse resumes, extract keywords, and provide tailored recommendations for skills and courses.
            
            **How to Use:**
            - **User**: Register or login, then upload a PDF resume to get analysis and recommendations.
            - **Feedback**: Share your thoughts about the tool.
            - **Admin**: Login with username `admin` and password `admin123` to view analytics.
            
           
        """, unsafe_allow_html=True)

    # Admin Section
    elif choice == "Admin":
        st.success("Admin Dashboard")
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type="password")
        if st.button("Login"):
            if ad_user == "admin" and ad_password == "admin123":
                try:
                    # Fetch data for visualization
                    cursor.execute("SELECT ID, ip_add, resume_score, Predicted_Field, User_level, city, state, country FROM user_data")
                    data = cursor.fetchall()
                    df = pd.DataFrame(data, columns=['ID', 'IP', 'Resume Score', 'Predicted Field', 'User Level', 'City', 'State', 'Country'])
                    st.success(f"Total Users: {len(df)}")
                    
                    # Display full user data
                    st.header("User Data")
                    cursor.execute("SELECT * FROM user_data")
                    user_data = cursor.fetchall()
                    user_df = pd.DataFrame(user_data, columns=[
                                'id', 'sec_token', 'ip_add', 'host_name', 'dev_user', 'os_name_ver', 'latlong',
                                'city', 'state', 'country', 'act_name', 'act_mail', 'act_mobile', 'Name', 'Email_ID',
                                'resume_score', 'Timestamp', 'Page_no', 'Predicted_Field', 'User_level',
                                'Actual_skills', 'Recommended_skills', 'Recommended_courses', 'pdf_name'
                            ])

                    st.dataframe(user_df)
                    st.markdown(get_csv_download_link(user_df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)

                    # Display feedback data
                    st.header("Feedback Data")
                    cursor.execute("SELECT * FROM user_feedback")
                    feedback_data = cursor.fetchall()
                    feedback_df = pd.DataFrame(feedback_data, columns=['ID', 'Name', 'Email', 'Score', 'Comments', 'Timestamp'])
                    st.dataframe(feedback_df)

                    # Visualization charts
                    if not df.empty:
                        for column, title in [
                            ('Predicted Field', 'Predicted Field Distribution'),
                            ('User Level', 'User Experience Levels'),
                            ('Resume Score', 'Resume Scores'),
                            ('IP', 'Usage by IP'),
                            ('City', 'Usage by City'),
                            ('State', 'Usage by State'),
                            ('Country', 'Usage by Country')
                        ]:
                            if column in df.columns and not df[column].isna().all():
                                st.subheader(f"**{title}**")
                                fig = px.pie(values=df[column].value_counts(), names=df[column].unique(), title=title)
                                st.plotly_chart(fig)
                            else:
                                st.warning(f"No data available for {title}")
                    else:
                        st.warning("No user data available for visualization.")
                except Exception as e:
                    st.error(f"Error retrieving admin data: {str(e)}")
            else:
                st.error("Invalid Credentials")

if __name__ == "__main__":
    run()