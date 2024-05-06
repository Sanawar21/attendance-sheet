from simple_salesforce import SalesforceLogin, SFType


class AttendanceClient(SFType):

    def __init__(self, username, password, security_token):
        session_id, instance = SalesforceLogin(
            username=username,
            domain="test",
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
            'Code': 'dnf-fkqv-twc'
        }
        """
        data = {
            "Course_Offering__c": None,  # TODO: Connect with google meet
            "Duration__c": raw_data["Duration"],
            "Email__c": raw_data["Email"],
            "First_Name__c": raw_data["First name"],
            "Last_Name__c": raw_data["Last name"],
            "Time_Exited__c": raw_data["Time exited"],
            "Time__c": raw_data["Time joined"],
            "hed__Contact__c": None,
            "hed__Date__c": raw_data["Date"],
        }

        return self.create(data)