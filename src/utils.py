"""
DELIBERATELY VULNERABLE UTILITY FUNCTIONS - FOR EDUCATIONAL PURPOSES ONLY

This module demonstrates various security vulnerabilities in utility functions.
"""

import os
import subprocess
import hashlib
import pickle
import requests
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XMLParser
from . import config


def hash_password(password):
    """
    CWE-327: Use of a Broken or Risky Cryptographic Algorithm

    MD5 is cryptographically broken and should NEVER be used for passwords.
    Use bcrypt, argon2, or scrypt instead.
    """
    # VULNERABILITY: MD5 is not suitable for password hashing
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """Verify password against MD5 hash."""
    return hash_password(password) == password_hash


def run_system_command(command):
    """
    CWE-78: OS Command Injection

    Executes system commands without sanitization.
    NEVER use shell=True with user input!
    """
    # VULNERABILITY: shell=True with unsanitized input allows command injection
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode('utf-8')}"


def get_file_content(filename):
    """
    CWE-22: Path Traversal

    Reads file without path validation.
    Allows reading arbitrary files using ../ sequences.
    """
    # VULNERABILITY: No path validation allows path traversal
    try:
        file_path = os.path.join(config.UPLOAD_FOLDER, filename)
        with open(file_path, "r") as f:
            return f.read()
    except Exception:
        return None


def save_uploaded_file(file_data, filename):
    """
    CWE-434: Unrestricted Upload of File with Dangerous Type

    Saves file without validation of file type or content.
    Accepts either a Flask FileStorage object or raw bytes.
    """
    # VULNERABILITY: No file type validation
    # VULNERABILITY: No filename sanitization
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if hasattr(file_data, "save"):
        # Flask FileStorage object
        file_data.save(file_path)
    else:
        with open(file_path, "wb") as f:
            f.write(file_data)
    return {"success": True, "filepath": file_path}


def serialize_session(session_data):
    """
    CWE-502: Deserialization of Untrusted Data

    Uses pickle for serialization which can execute arbitrary code.
    NEVER use pickle with untrusted data!
    """
    # VULNERABILITY: pickle can execute arbitrary code during deserialization
    return pickle.dumps(session_data)


def deserialize_session(serialized_data):
    """
    CWE-502: Deserialization of Untrusted Data

    Deserializes pickle data which can execute arbitrary code.
    """
    # VULNERABILITY: Unpickling untrusted data is extremely dangerous
    try:
        return pickle.loads(serialized_data)
    except Exception:
        return None


def fetch_url(url):
    """
    CWE-918: Server-Side Request Forgery (SSRF)

    Fetches URL without validation.
    Allows attacker to scan internal network or access internal services.
    Returns a dict with 'success', 'content', and optional 'status_code'/'error' keys.
    """
    # VULNERABILITY: No URL validation allows SSRF attacks
    # VULNERABILITY: SSL verification disabled
    try:
        response = requests.get(url, verify=False, timeout=5)
        return {
            "success": True,
            "content": response.text,
            "status_code": response.status_code,
        }
    except Exception as e:
        return {"success": False, "error": f"Error fetching URL: {str(e)}"}


def parse_xml(xml_string):
    """
    CWE-611: Improper Restriction of XML External Entity Reference (XXE)

    Parses XML without disabling external entities.
    Allows reading arbitrary files and SSRF via XXE injection.
    """
    # VULNERABILITY: XMLParser with default settings is vulnerable to XXE
    try:
        # This parser allows external entities by default
        parser = XMLParser()
        root = ET.fromstring(xml_string, parser=parser)
        return root
    except Exception as e:
        return f"Error parsing XML: {str(e)}"


def parse_xml_file(filepath):
    """
    CWE-611: XXE via file parsing
    """
    # VULNERABILITY: Parsing XML files without disabling external entities
    try:
        tree = ET.parse(filepath)
        return tree.getroot()
    except Exception as e:
        return f"Error parsing XML file: {str(e)}"


def generate_session_token(user_id):
    """
    CWE-330: Use of Insufficiently Random Values

    Generates predictable session tokens.
    Should use cryptographically secure random generator.
    """
    # VULNERABILITY: Predictable token generation using MD5 of user_id
    import time

    token_string = f"{user_id}_{time.time()}"
    return hashlib.md5(token_string.encode()).hexdigest()


def check_file_checksum(filename, checksum_type="md5"):
    """
    Calculate file checksum.
    Uses MD5 by default (weak).
    """
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)

    # VULNERABILITY: Using MD5 for integrity checking (weak)
    if checksum_type == "md5":
        hasher = hashlib.md5()
    else:
        hasher = hashlib.sha1()  # SHA1 also deprecated

    try:
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    except Exception:
        return None


def is_admin_user(username):
    """
    CWE-863: Incorrect Authorization

    Weak admin check that could be bypassed.
    """
    # VULNERABILITY: Simple string comparison, no cryptographic verification
    return username == "admin" or username.lower() == "administrator"


def get_file_checksum(filename, checksum_type="md5"):
    """
    Alias for check_file_checksum for API consistency.

    Parameters:
    filename (str): The name of the file to checksum.
    checksum_type (str): The checksum algorithm to use (default: 'md5').

    Returns:
    str: The hex digest of the checksum, or None if the file cannot be read.
    """
    return check_file_checksum(filename, checksum_type)
