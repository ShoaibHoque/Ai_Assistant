import pandas as pd

# DataFrame simulating a database for requests
db_columns = ["Employee", "Module", "Intent", "Project ID", "Project Name", "Amount", "Reason", "Status", "Language"]

class ERPData:
    def __init__(self):
        self.erp_modules = {
            "Human Resources": [],
            "Financial Management": ["request_money"],
            "Supply Chain Management": [],
            "Project Management": [],
            "Customer Relationship Management (CRM)": []
        }

    def add_request(self, employee, intent_data, lang="en"):
        new_entry = {
            "Employee": employee,
            "Module": "Financial Management",  # Example module
            "Intent": intent_data["intent"],
            "Project ID": intent_data["entities"].get("PROJECT_ID", ""),
            "Project Name": intent_data["entities"].get("PROJECT_NAME", ""),
            "Amount": intent_data["entities"].get("AMOUNT", ""),
            "Reason": intent_data["entities"].get("REASON", ""),
            "Status": "Pending Verification",
            "Language": lang
        }

        # Append new entry to CSV file
        new_df = pd.DataFrame([new_entry])
        try:
            existing_df = pd.read_csv("requests_db.csv")  # Read existing data
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        except FileNotFoundError:
            updated_df = new_df  # If file doesn't exist, start with the new data

        updated_df.to_csv("requests_db.csv", index=False)
        return "Request added successfully."
