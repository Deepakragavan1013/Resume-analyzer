import os
import io
import spacy
from spacy.matcher import Matcher
import re
import PyPDF2
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter

# Placeholder utils module
class utils:
    @staticmethod
    def extract_text(file, ext):
        try:
            resource_manager = PDFResourceManager()
            fake_file_handle = io.StringIO()
            converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
            page_interpreter = PDFPageInterpreter(resource_manager, converter)

            if isinstance(file, io.BytesIO):
                file.seek(0)
                file_obj = file
            else:
                file_obj = open(file, 'rb')

            for page in PDFPage.get_pages(file_obj, caching=True, check_extractable=True):
                page_interpreter.process_page(page)
            text = fake_file_handle.getvalue()

            converter.close()
            fake_file_handle.close()
            if not isinstance(file, io.BytesIO):
                file_obj.close()

            return text
        except Exception as e:
            raise Exception(f"Error extracting text: {str(e)}")

    @staticmethod
    def extract_entities_with_custom_model(doc):
        entities = {'Name': [], 'Degree': []}
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['Name'].append(ent.text)
            elif ent.label_ == 'DEGREE':
                entities['Degree'].append(ent.text)
        return entities

    @staticmethod
    def extract_name(doc, text=None):
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) <= 0:
                return ent.text.strip()

        if text:
            lines = text.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                if 1 <= len(first_line.split()) <= 2:
                    return first_line

        possible_names = re.findall(r"^[A-Z]+(?:\s[A-Z]+){1,2}", text or "", re.MULTILINE)
        if possible_names:
            return possible_names[0]

        return "Name Not Found"

    @staticmethod
    def extract_email(text):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None

    @staticmethod
    def extract_mobile_number(text, custom_regex=None):
        if custom_regex:
            pattern = custom_regex
        else:
            pattern = r'(\+\d{1,3}\s?)?(\d{10}|\(\d{3}\)\s?\d{3}-\d{4}|\d{3}-\d{3}-\d{4})'
        numbers = re.findall(pattern, text)
        return numbers[0][-1] if numbers else None

    @staticmethod
    def extract_skills(doc, noun_chunks, skills_file=None):
        if skills_file and os.path.exists(skills_file):
            with open(skills_file, 'r') as f:
                skills_list = [line.strip().lower() for line in f if line.strip()]
        else:
            skills_list = ['python', 'java', 'javascript', 'sql', 'machine learning', 'tensorflow', 'react', 'django', 'flutter', 'swift', 'figma']

        skills = []
        for token in doc:
            if token.text.lower() in skills_list:
                skills.append(token.text)
        for chunk in noun_chunks:
            if chunk.text.lower() in skills_list:
                skills.append(chunk.text)
        return list(set(skills))

    @staticmethod
    def get_number_of_pages(file):
        try:
            if isinstance(file, io.BytesIO):
                file.seek(0)
                pdf = PyPDF2.PdfReader(file)
            else:
                pdf = PyPDF2.PdfReader(file)
            return len(pdf.pages)
        except Exception as e:
            return None

    @staticmethod
    def extract_degrees(text):
        degree_keywords = [
            "Bachelor", "B.Tech", "BE", "BSc", "BCA",
            "Master", "M.Tech", "ME", "MSc", "MCA",
            "PhD", "Doctorate", "Diploma", "BA", "MA"
        ]
        found = [deg for deg in degree_keywords if deg.lower() in text.lower()]
        return list(set(found))


class ResumeParser:
    def __init__(self, resume, skills_file=None, custom_regex=None):
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except Exception as e:
            raise Exception(f"Error loading spacy model: {str(e)}")

        self.custom_nlp = None
        try:
            custom_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'custom_nlp_model')
            if os.path.exists(custom_model_path):
                self.custom_nlp = spacy.load(custom_model_path)
        except Exception as e:
            print(f"Warning: Could not load custom NLP model: {str(e)}")

        self.matcher = Matcher(self.nlp.vocab)
        self.skills_file = skills_file
        self.custom_regex = custom_regex
        self.resume = resume

        self.details = {
            'name': None,
            'email': None,
            'mobile_number': None,
            'skills': None,
            'degree': None,
            'no_of_pages': None,
        }

        if not isinstance(resume, io.BytesIO):
            self.ext = os.path.splitext(resume)[1].lstrip('.').lower()
        else:
            self.ext = resume.name.split('.')[-1].lower() if hasattr(resume, 'name') else 'pdf'

        if self.ext not in ['pdf']:
            raise ValueError(f"Unsupported file format: {self.ext}. Only PDF is supported.")

        try:
            self.text_raw = utils.extract_text(self.resume, f'.{self.ext}')
            self.text = ' '.join(self.text_raw.split())
        except Exception as e:
            raise Exception(f"Failed to extract text from resume: {str(e)}")

        self.doc = self.nlp(self.text)
        self.custom_doc = self.custom_nlp(self.text_raw) if self.custom_nlp else self.doc
        self.noun_chunks = list(self.doc.noun_chunks)
        self._extract_basic_details()

    def get_extracted_data(self):
        return self.details

    def _extract_basic_details(self):
        try:
            custom_entities = utils.extract_entities_with_custom_model(self.custom_doc)
            name = utils.extract_name(self.doc, text=self.text_raw)
            try:
                self.details['name'] = custom_entities['Name'][0] if custom_entities['Name'] else name
            except (KeyError, IndexError):
                self.details['name'] = name

            self.details['email'] = utils.extract_email(self.text)
            self.details['mobile_number'] = utils.extract_mobile_number(self.text, self.custom_regex)
            self.details['skills'] = utils.extract_skills(self.doc, self.noun_chunks, self.skills_file)
            self.details['no_of_pages'] = utils.get_number_of_pages(self.resume)

            try:
                if custom_entities['Degree']:
                    self.details['degree'] = custom_entities['Degree']
                else:
                    self.details['degree'] = utils.extract_degrees(self.text)
            except KeyError:
                self.details['degree'] = utils.extract_degrees(self.text)
        except Exception as e:
            raise Exception(f"Error extracting details: {str(e)}")


def parse_resume(resume):
    try:
        parser = ResumeParser(resume)
        return parser.get_extracted_data()
    except Exception as e:
        return {'error': str(e)}
