import subprocess
import dmidecode


def fetch_dmi_data():
    dmi_output = subprocess.run("dmidecode", cwd="dmi/", shell=True, capture_output=True).stdout.decode()
    parsed_dmi = dmidecode.parse_dmi(dmi_output)

    data = {}
    for (subject, subject_data) in parsed_dmi:
        if subject not in data:
            data[subject] = [subject_data]
        else:
            data[subject].append(subject_data)
        
    return data


DMI_DATA = fetch_dmi_data()
