###### Packages Used ######
import streamlit as st # core package used in this project
import pandas as pd
import base64, random
import time
import io,random
from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from nltk.stem import PorterStemmer
from PIL import Image
# pre stored data for prediction purposes
from Courses import resume_videos,interview_videos
from Skills import data_science, web_development,android_development,ios_development
import nltk
from nltk.corpus import wordnet
nltk.download('stopwords')
import google.generativeai as genai



###### Preprocessing functions ######

genai.configure(api_key="AIzaSyAN8urrdcCj8U10gtRGI7nW5rgGmZTekAE")
# OpenAI API configuration

def get_gemini_response(input):
    model=genai.GenerativeModel('gemini-1.0-pro-latest')
    response=model.generate_content(input)
    return response.text


# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 
def get_csv_download_link(df,filename,text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py
st.set_page_config(
   page_title="CVGuru",
   page_icon='./Logo/recommend.png',
)

###### Main function run() ######

def run():
        

        main_heading = "<h1 style='text-align: center; color: #cce7ff; margin-bottom: 0; margin-top:-50px'>CVGuru</h1>"
        tagline = "<h4 style='text-align: center; color: #cce7ff; margin-top: -25px;'>AI Resume Review Assistant</h4>"
        header_content = main_heading + tagline
        st.markdown(header_content, unsafe_allow_html=True)

        st.markdown('''<p align='justify';>
            A tool which parses information from a resume using natural language processing and finds the keywords, 
                    cluster them onto sectors based on their keywords and lastly show recommendations, 
                    generated by Gemini text model(gemini-1.0-pro-latest).
        </p>''',unsafe_allow_html=True)  

        st.markdown('<hr>', unsafe_allow_html=True)

        # Upload Resume
        st.markdown(''' <br>
                    <h3 style='text-align: left; color: #cce7ff;'> Upload Your Resume, And Get Smart Recommendations</h3>'''
                    ,unsafe_allow_html=True)
        
        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(0.5)
        
            ## saving the uploaded resume to folder
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                
                ## Get the whole resume data into resume_text
                resume_text = pdf_reader(save_image_path)


                st.markdown('<hr>', unsafe_allow_html=True)

                ## Showing Analyzed data from (resume_data)
                st.header(" Resume Analysis")
                st.subheader("Your Basic info!")
                for field, label in [
                    ("name", "Name"),
                    ("email", "Email"),
                    ("mobile_number", "Contact"),
                    ("degree", "Degree"),
                    ("total_experience", "Total Experience")
                ]:
                    if resume_data.get(field):
                        if field == "degree":
                            st.text(f'{label}: {resume_data[field][0]}')
                        else:
                            st.text(f'{label}: {resume_data[field]}')
                ## Predicting Candidate Experience Level 

                # Using total experience to predict experience level
                experience_grades = ['Fresher', 'Intermediate', 'Experienced']
                experience_bounds = [0, 2, 5, 10]
                experience_count = resume_data['total_experience']
                colors = ['#FF9999', '#B2FFFC', '#AEFFAE']  # bold pink, mint, bold green
                for i, grade in enumerate(experience_grades):
                    if experience_bounds[i] <= experience_count < experience_bounds[i+1]:
                        msg = f'<h6 style="display: inline;"> You are at <span style="color:{colors[i]};">{grade}</span> level!</h6>'
                        st.markdown(msg, unsafe_allow_html=True)
                        break
                else:
                    cand_level = 'Experienced'  # assign default level outside of the loop

                st.markdown('<hr>', unsafe_allow_html=True)

                ## Skills Analyzing and Recommendation
                st.header("Skills Recommendation 💡")
                
                ### Current Analyzed Skills
                keywords = st_tags(label='##### Current Analyzed Skills💹:',text='See our skills recommendation below',
                                   value=resume_data['skills'],key = '1')

                ### Predicting Field Based on Keywords
                # Load NLTK stopwords
                stop_words = set(nltk.corpus.stopwords.words('english'))
                words = [word.lower() for word in resume_data['skills'] if word.lower() not in stop_words]
                resume_skills = " ".join(words)
                
                # Use NLTK to predict field
                field_grades = {
                    'Data Science': 'data_science',
                    'Web Development': 'web_development',
                    'Android Development': 'android_development',
                    'IOS Development': 'ios_development'
                }
                field_count = {}
                for grade in field_grades:
                    count = 0
                    for synonym in wordnet.synonyms(grade):
                        count += resume_skills.lower().count(synonym.name())
                    if count == 0:
                        count = resume_skills.lower().count(grade)
                    field_count[grade] = count
                if all(count == 0 for count in field_count.values()):
                    field_count = {'Data Science': 1}
                max_field = max(field_count.values())
                for grade in field_grades:
                    if field_count[grade] == max_field:
                        reco_field = grade
                        break


                ### Skill Recommendations based on predicted field
                # prompt = f"Provide a list of 20 skills required for '{reco_field}' in a comma-separated format without any extra text."
                # recommended_skills = get_gemini_response(prompt)
                # recommended_skills = [skill.lower() for skill in recommended_skills.split(',')]

                recommended_skills = field_grades[reco_field]
                
                if reco_field == 'Data Science':
                    recommended_skills = data_science
                elif reco_field == 'Web Development':
                    recommended_skills = web_development
                elif reco_field == 'Android Development':
                    recommended_skills = android_development
                elif reco_field == 'IOS Development':
                    recommended_skills = ios_development

                ps = PorterStemmer()

                already_have_skills = [ps.stem(skill.lower()) for skill in resume_data['skills']]
                recommended_skills_stem = [ps.stem(skill.lower()) for skill in recommended_skills]

                recommended_skills_list = []
                for skill in recommended_skills_stem:
                    if not any(syn.name().lower() in already_have_skills for syn in wordnet.synsets(skill)):
                        recommended_skills_list.append(skill)

                keywords = st_tags(label=f' ##### Recommended skills for you ({reco_field})📚📚:',
                                               text='Recommended skills generated by System.',
                                               value=recommended_skills_list, #Changed value to list
                                               key='2') # Added list to display skills in box
                
                st.markdown('<hr>', unsafe_allow_html=True)

                ## Resume Scorer & Resume Writing Tips
                st.header("**Resume Tips & Ideas 🥂**")
                resume_score = 0
                
                ### Using NLP to Predicting Whether these key points are added to the resume
                def similar_words(word):
                    synonyms = set()
                    for syn in wordnet.synsets(word):
                        for l in syn.lemmas():
                            synonyms.add(l.name())
                    return synonyms

                keywords_to_find = ['Summary','Education','EXPERIENCE','INTERNSHIPS','SKILLS','HOBBIES',
                                'INTERESTS','ACHIEVEMENTS','CERTIFICATIONS','PROJECTS']
                keywords = {"match":0, "mismatch": 0}
                match_sections = []
                for keyword in keywords_to_find:
                    keyword_syn = similar_words(keyword.lower())
                    for syn in keyword_syn:
                        if syn.lower() in resume_text.lower():
                            keywords["match"] = keywords.get("match") + 1
                            match_sections.append(syn.lower())
                            msg = f'''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added {syn.lower()}</h4>'''
                            st.markdown(msg, unsafe_allow_html=True)
                            break
                    else:
                        keywords["mismatch"] = keywords.get("mismatch") + 1
                        msg = f'''<h5 style='text-align: left; color: #ff6b6b;'>[-] Please add {keyword.lower()}.</h4>'''
                        st.markdown(msg, unsafe_allow_html=True)
               
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )

                ### Calculate Resume Score using NLP
                st.subheader("Resume Score 📝")
                
                for field in ["name","email","mobile_number","degree"]:
                    if resume_data.get(field):
                        resume_score += 5

                skills_required, skills_present = len(recommended_skills_list), len(already_have_skills)
                years_of_exp = resume_data['total_experience']
                skill_score = (skills_present) / (skills_required + skills_present) * 50
                exp_score = min(years_of_exp / 10, 1) * 30
                keyword_match = keywords["match"] / (keywords["match"] + keywords["mismatch"]) * 50
                resume_score = int(skill_score + exp_score + keyword_match)

                ### Score Bar
                my_bar = st.progress(0)
                # my_bar.progress(resume_score)
                for percent_complete in range(0, resume_score + 1):
                    my_bar.progress(percent_complete)
                    time.sleep(0.01)  #

                st.error(f'Your Resume Writing Score: {resume_score}')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")


                st.markdown('<hr>', unsafe_allow_html=True)

                # Create a list of Improvement
                options = []
                for option in ["summary", "education", "experience", "internship", "projects"]:
                    option_variations = [option] + [syn.lower() for syn in similar_words(option)]
                    for variant in option_variations:
                        if variant.lower() in match_sections:
                            options.append(option.capitalize())
                            break
                if "Summary" not in options:
                    options.append("Summary")
                # Create a dropdown menu with a label and the options list
                st.markdown('''<h2>Areas of Improvement ✍🏻:  </h2>''',unsafe_allow_html=True)

                selected_option = st.selectbox('',options,index=None ,placeholder="Choose a section to Improvement")
                if selected_option:
                    with st.spinner('Hang On While We Cook Magic For You...'):
                        prompt = f"Based on the following resume text can you please improve {selected_option}? \n\n Resume text: {resume_text}"
                        response = get_gemini_response(prompt)
                        st.write(response)


                st.markdown('<hr>', unsafe_allow_html=True)

                ## Recommending Resume Writing Video
                st.header("**Bonus Video for Resume Writing Tips💡**")

                # getting recommneded videos from Gemini
                prompt="Provide a list of 2 videos for resume writing tips: Title: link"
                recommended_videos = get_gemini_response(prompt)
                st.write(recommended_videos)
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## Recommending Interview Preparation Video
                st.header("**Bonus Video for Interview Tips💡**")
                prompt="Provide a list of 2 videos for interview prepration tips: Title: link"
                recommended_videos = get_gemini_response(prompt)
                st.write(recommended_videos)
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                ## On Successful Result 
                custom_style = """
                            <style>
                            .centered-text {
                                font-size: 24px;  /* Adjust the font size as desired */
                                text-align: center;  /* Center align the text */
                            }
                            </style>
                        """

                # Apply the custom CSS styles
                st.markdown(custom_style, unsafe_allow_html=True)

                # Display the text with the custom class to apply the styles
                st.markdown('<p class="centered-text">Thank you for using CVGuru. 🙏</p>', unsafe_allow_html=True)
                
            else:
                st.error('Something went wrong..')      

# Calling the main (run()) function to make the whole process run
run()