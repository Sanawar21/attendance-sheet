from simple_salesforce import SalesforceLogin, SFType


class AttendanceClient(SFType):

    def __init__(self, username, password, security_token):
        session_id, instance = SalesforceLogin(
            username=username,
            domain="login",
            password=password,
            security_token=security_token
        )

        super().__init__("hed__Attendance_Event__c", session_id, instance)

    def upload(self, raw_data: dict):
        """
        Uploads an attendance record containing data in the following
        format:
        {
            'First name': 'Sanawar', 
            'Last name': 'Saeed', 
            'Email': 'test@g.com', 
            'Duration': '56 min', 
            'Time joined': '10:30\u202fPM', 
            'Time exited': '11:25\u202fPM', 
            'Date': '2024-05-4T23:26:18+05:00Z', 
            'Code': 'dnf-fkqv-twc',
            'Course': 'Course 1'
        }
        """

        data = {
            "Course_Offering_ID__c": raw_data.get("Course"),
            "Duration__c": raw_data.get("Duration"),
            "Email__c": raw_data.get("Email"),
            "First_Name__c": raw_data.get("First name"),
            "Last_Name__c": raw_data.get("Last name"),
            "Time_Exited__c": raw_data.get("Time exited"),
            "Time__c": raw_data.get("Time joined"),
            "hed__Contact__c": raw_data.get("HED Contact"),  # always None
            "hed__Date__c": raw_data.get("Date"),
        }

        return self.create(data)
