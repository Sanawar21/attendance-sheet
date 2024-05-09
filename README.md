# Attendance Sheet Automation

Automate the process of recording attendance for college classes conducted on Google Meet and managing them on Salesforce.

## Overview

This project automates the attendance recording process for colleges that conduct classes on Google Meet and record attendance on Salesforce. It scans emails from Google Meet sent by meetings-noreply@google.com, extracts attendance links, and connects them to corresponding courses using the Google Classroom API. The attendance sheets are then uploaded to respective courses on Salesforce.

## Features

- **Email Parsing:** Utilizes the Gmail API to extract attendance links from emails.
- **Attendance Sheet Download:** Leverages the Google Sheets API to download attendance sheets.
- **Course Details Extraction:** Develops a web scraper using Browser Automation Studio to retrieve course details from Google Classroom.
- **Salesforce Integration:** Integrates the Salesforce API to upload attendance sheets to respective courses.

## Technologies Used

- Python
- Gmail API
- Google Sheets API
- Google Classroom API
- Salesforce API
- Browser Automation Studio

## Usage

1. Clone the repository:

    ```bash
    git clone https://github.com/Sanawar21/attendance-sheet.git
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the main script:

    ```bash
    python main.py
    ```

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License.

## Acknowledgments

Special thanks to Sanawar21 for developing this project.
