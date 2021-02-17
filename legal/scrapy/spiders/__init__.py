from datetime import datetime
def get_graduation_info(education_info, search_key, data_key):
    graduated_date, university_name = None, []
    for education in education_info:
        try:
            current_graduated_date = datetime.strptime(education.get(search_key, ''), '%Y-%m-%d %H:%M:%S')
            if graduated_date and current_graduated_date > graduated_date:
                graduated_date = current_graduated_date
                university_name = [education.get(data_key, '')]
            elif graduated_date and current_graduated_date == graduated_date:
                university_name.append(education.get(data_key, ''))
            elif not graduated_date:
                graduated_date = current_graduated_date
                university_name = [education.get(data_key, '')]
        except:
            pass
    return (graduated_date, ', '.join(university_name))

def generate_graduation_info(education_data):
    education_info = education_data.get('educationInfo', [])
    graduate_medical_info = education_data.get('medicalEducationInfo', [])
    if education_info:
        graduated_date, university_name = get_graduation_info(education_info, 'graduated', 'schoolName')
        if not graduated_date:
            to_date, university_name = get_graduation_info(education_info, 'toDate', 'schoolName')
    else:
        graduated_date, university_name = get_graduation_info(graduate_medical_info, 'graduated', 'hospitalName')
        if not graduated_date:
            to_date, university_name = get_graduation_info(graduate_medical_info, 'toDate', 'hospitalName')
    graduated_year = None
    if graduated_date:
        graduated_year = graduated_date.year
    education_data.pop('educationInfo')
    education_data.pop('medicalEducationInfo')
    education_data['graduationYearfromCollege'] = graduated_year
    education_data['universityName'] = university_name
    return education_data
