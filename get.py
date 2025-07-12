import requests
import json
import time

BASE_URL = "https://portal.cghmc.com.ph/patient-data/"
START_ID = 1
END_ID = 350000
OUTPUT_FILE = "patients_data.sql"

def print_banner():
    banner = r"""
███╗   ███╗ █████╗ ██████╗  █████╗ ██████╗ ███████╗██████╗ ███████╗███████╗ ██████╗
████╗ ████║██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝██╔════╝██╔════╝
██╔████╔██║███████║██████╔╝███████║██║  ██║█████╗  ██║  ██║███████╗█████╗  ██║     
██║╚██╔╝██║██╔══██║██╔═══╝ ██╔══██║██║  ██║██╔══╝  ██║  ██║╚════██║██╔══╝  ██║     
██║ ╚═╝ ██║██║  ██║██║     ██║  ██║██████╔╝███████╗██████╔╝███████║███████╗╚██████╗
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═════╝ ╚══════╝╚══════╝ ╚═════╝
"""
    print(banner)

def is_valid_response(data):
    # Basic check for expected keys in the JSON response
    required_keys = {"userId", "id", "username", "fullName", "gender", "birthDate", "activated", "active", "age", "civilStatus", "validated"}
    return all(key in data for key in required_keys)

def sql_escape(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, (int, float)):
        return str(value)
    # Escape single quotes for SQL
    return "'" + str(value).replace("'", "''") + "'"

def extract_patient_data(data):
    # Basic fields
    userId = data.get("userId")
    patient_id = data.get("id")
    username = data.get("username")
    fullName = data.get("fullName")
    gender = data.get("gender")
    birthDate = data.get("birthDate")
    activated = data.get("activated")
    active = data.get("active")
    age = data.get("age")
    civilStatus = data.get("civilStatus")
    validated = data.get("validated")
    bloodType = data.get("bloodType")
    occupation = data.get("occupation")
    location = data.get("location")
    address = data.get("address")
    secondaryEmail = data.get("secondaryEmail")
    secondaryMobile = data.get("secondaryMobile")
    pin = data.get("pin")
    patientIds = json.dumps(data.get("patientIds")) if data.get("patientIds") is not None else None
    parent = json.dumps(data.get("parent")) if data.get("parent") is not None else None
    parentUserId = data.get("parentUserId")
    dependents = json.dumps(data.get("dependents")) if data.get("dependents") is not None else None
    dependent = data.get("dependent")
    relationship = data.get("relationship")
    deleted = data.get("deleted")
    position = data.get("position")
    personalAndSocialHistory = json.dumps(data.get("personalAndSocialHistory")) if data.get("personalAndSocialHistory") is not None else None
    deficiencyRemarks = data.get("deficiencyRemarks")
    hmos = json.dumps(data.get("hmos")) if data.get("hmos") is not None else None
    hmosDetail = json.dumps(data.get("hmosDetail")) if data.get("hmosDetail") is not None else None
    historyOfFamilyIllnesses = json.dumps(data.get("historyOfFamilyIllnesses")) if data.get("historyOfFamilyIllnesses") is not None else None
    illnesses = json.dumps(data.get("illnesses")) if data.get("illnesses") is not None else None
    allergies = json.dumps(data.get("allergies")) if data.get("allergies") is not None else None
    medications = json.dumps(data.get("medications")) if data.get("medications") is not None else None
    password = data.get("password")
    encryptedPin = data.get("encryptedPin")
    parentName = data.get("parentName")
    parentEmail = data.get("parentEmail")

    # Flattened name object
    name_obj = data.get("name", {})
    familyName = name_obj.get("familyName")
    givenName = name_obj.get("givenName")
    middleName = name_obj.get("middleName")
    suffix = name_obj.get("suffix")
    prefix = name_obj.get("prefix")
    degree = name_obj.get("degree")
    givenNameSuffixFormat = name_obj.get("givenNameSuffixFormat")
    fullNameFamilyNameSuffixFormat = name_obj.get("fullNameFamilyNameSuffixFormat")
    fullNameGivenNameSuffixFormat = name_obj.get("fullNameGivenNameSuffixFormat")

    # Permanent address fields
    perm_addr = data.get("permanentAddress", {})
    perm_street = perm_addr.get("street")
    perm_barangay = perm_addr.get("barangay")
    perm_municipality = perm_addr.get("municipality")
    perm_province = perm_addr.get("province")
    perm_countryId = perm_addr.get("countryId")
    perm_region = perm_addr.get("region")
    perm_village = perm_addr.get("village")
    perm_houseNo = perm_addr.get("houseNo")
    perm_zipCode = perm_addr.get("zipCode")

    # Current address fields
    curr_addr = data.get("currentAddress", {})
    curr_street = curr_addr.get("street")
    curr_barangay = curr_addr.get("barangay")
    curr_municipality = curr_addr.get("municipality")
    curr_province = curr_addr.get("province")
    curr_countryId = curr_addr.get("countryId")
    curr_region = curr_addr.get("region")
    curr_village = curr_addr.get("village")
    curr_houseNo = curr_addr.get("houseNo")
    curr_zipCode = curr_addr.get("zipCode")

    # Contact info (take first mobile if exists)
    contactInfos = data.get("contactInfos", [])
    mobile = None
    for c in contactInfos:
        if c.get("type") == "MOBILE":
            mobile = c.get("value")
            break

    # Nationality code
    nationality = data.get("nationality", {})
    nationality_code = nationality.get("code")
    nationality_description = nationality.get("description")

    sql = f"""INSERT INTO patients (
        userId, patient_id, username, fullName, gender, birthDate, activated, active, age, civilStatus, validated,
        bloodType, occupation, location, address, secondaryEmail, secondaryMobile, pin, patientIds, parent, parentUserId, dependents, dependent, relationship, deleted, position, personalAndSocialHistory, deficiencyRemarks, hmos, hmosDetail, historyOfFamilyIllnesses, illnesses, allergies, medications, password, encryptedPin, parentName, parentEmail,
        familyName, givenName, middleName, suffix, prefix, degree, givenNameSuffixFormat, fullNameFamilyNameSuffixFormat, fullNameGivenNameSuffixFormat,
        perm_street, perm_barangay, perm_municipality, perm_province, perm_countryId, perm_region, perm_village, perm_houseNo, perm_zipCode,
        curr_street, curr_barangay, curr_municipality, curr_province, curr_countryId, curr_region, curr_village, curr_houseNo, curr_zipCode,
        mobile, nationality_code, nationality_description
    ) VALUES (
        {sql_escape(userId)}, {sql_escape(patient_id)}, {sql_escape(username)}, {sql_escape(fullName)}, {sql_escape(gender)}, {sql_escape(birthDate)}, {sql_escape(activated)}, {sql_escape(active)}, {sql_escape(age)}, {sql_escape(civilStatus)}, {sql_escape(validated)},
        {sql_escape(bloodType)}, {sql_escape(occupation)}, {sql_escape(location)}, {sql_escape(address)}, {sql_escape(secondaryEmail)}, {sql_escape(secondaryMobile)}, {sql_escape(pin)}, {sql_escape(patientIds)}, {sql_escape(parent)}, {sql_escape(parentUserId)}, {sql_escape(dependents)}, {sql_escape(dependent)}, {sql_escape(relationship)}, {sql_escape(deleted)}, {sql_escape(position)}, {sql_escape(personalAndSocialHistory)}, {sql_escape(deficiencyRemarks)}, {sql_escape(hmos)}, {sql_escape(hmosDetail)}, {sql_escape(historyOfFamilyIllnesses)}, {sql_escape(illnesses)}, {sql_escape(allergies)}, {sql_escape(medications)}, {sql_escape(password)}, {sql_escape(encryptedPin)}, {sql_escape(parentName)}, {sql_escape(parentEmail)},
        {sql_escape(familyName)}, {sql_escape(givenName)}, {sql_escape(middleName)}, {sql_escape(suffix)}, {sql_escape(prefix)}, {sql_escape(degree)}, {sql_escape(givenNameSuffixFormat)}, {sql_escape(fullNameFamilyNameSuffixFormat)}, {sql_escape(fullNameGivenNameSuffixFormat)},
        {sql_escape(perm_street)}, {sql_escape(perm_barangay)}, {sql_escape(perm_municipality)}, {sql_escape(perm_province)}, {sql_escape(perm_countryId)}, {sql_escape(perm_region)}, {sql_escape(perm_village)}, {sql_escape(perm_houseNo)}, {sql_escape(perm_zipCode)},
        {sql_escape(curr_street)}, {sql_escape(curr_barangay)}, {sql_escape(curr_municipality)}, {sql_escape(curr_province)}, {sql_escape(curr_countryId)}, {sql_escape(curr_region)}, {sql_escape(curr_village)}, {sql_escape(curr_houseNo)}, {sql_escape(curr_zipCode)},
        {sql_escape(mobile)}, {sql_escape(nationality_code)}, {sql_escape(nationality_description)}
    );"""
    return sql

def main():
    print_banner()
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://portal.cghmc.com.ph/",
    "Cookie": "JSESSIONID=1hmeucvpjietp1p1mqqt8ajf78"
}
    max_retries = 3
    failed_ids = []
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f, open("failed_patients.txt", "w", encoding="utf-8") as fail_log:
        for patient_id in range(START_ID, END_ID + 1):
            url = f"{BASE_URL}{patient_id}"
            success = False
            for attempt in range(1, max_retries + 1):
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if is_valid_response(data):
                            sql = extract_patient_data(data)
                            f.write(sql + "\n")
                        success = True
                        break
                    else:
                        # Non-200 response, treat as failure
                        pass
                except (requests.RequestException, json.JSONDecodeError):
                    # Suppress error output, just retry
                    time.sleep(0.5)  # Short delay before retry
            # Print status/loading message (no error details)
            print(f"\r[STATUS] Collecting patient ID {patient_id}...", end="", flush=True)
            if not success:
                failed_ids.append(patient_id)
                fail_log.write(f"{patient_id}\n")
        print(f"\nDone. Data written to {OUTPUT_FILE}")
        if failed_ids:
            print(f"{len(failed_ids)} patient IDs failed. See failed_patients.txt.")

if __name__ == "__main__":
    main()
