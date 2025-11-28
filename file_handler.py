import os
import streamlit as st
from pypdf import PdfReader
from pypdf.errors import PdfReadError

def safe_file_type(uploaded_file):
    try:
        t = getattr(uploaded_file, "type", None)
        if t:
            return t
        name = getattr(uploaded_file, "name", "")
        ext = os.path.splitext(name)[1].lower()
        if ext == ".txt":
            return "text/plain"
        if ext == ".pdf":
            return "application/pdf"
        return None
    except Exception:
        return None

@st.cache_data
def read_uploaded_file(uploaded_file):
    try:
        ftype = safe_file_type(uploaded_file)
        if ftype == "text/plain":
            raw = uploaded_file.read()
            if isinstance(raw, bytes):
                return raw.decode("utf-8", errors="ignore")
            return str(raw)
        elif ftype == "application/pdf":
            reader = PdfReader(uploaded_file)
            if reader.is_encrypted:
                st.warning(f"PDF '{uploaded_file.name}' is encrypted. Skipping.")
                return None
            if not reader.pages:
                st.warning(f"PDF '{uploaded_file.name}' contains no readable pages.")
                return None
            text = ""
            for page in reader.pages:
                try:
                    pt = page.extract_text() or ""
                except Exception:
                    pt = ""
                text += pt + "\n"
            return text.strip()
        else:
            raw = uploaded_file.read()
            if isinstance(raw, bytes):
                return raw.decode("utf-8", errors="ignore")
            return str(raw)
    except PdfReadError as e:
        st.error(f"PDF read error '{uploaded_file.name}': {e}")
        return None
    except Exception as e:
        st.error(f"Error reading file '{getattr(uploaded_file,'name', '')}': {e}")
        return None
