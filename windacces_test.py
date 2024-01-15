## Imports
import sys
import urllib.request
import json
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt
import subprocess
import configparser
import webbrowser
import os
from urllib.parse import quote


# Load Windchill configuration from windchill.config
config = configparser.ConfigParser()
config.read('windchill.config')

BASE_URL = config['Windchill']['base_url']
USERNAME = config['Windchill']['username']
PASSWORD = config['Windchill']['password']
creo_view_agent = config['Windchill']['creo_view_agent']

# Mapping MIME types to icon filenames
mime_type_to_icon = {
    'image/vnd.dwg': 'dwg_icon.png',
    'image/vnd.dxf': 'dxf_icon.png',
    'application/pdf': 'pdf_icon.png',
    'x-unknown/x-unknown': 'unknown_icon.png',
    # Add other mappings as needed
}

## URL Definitions and Data Fetching

# Define the URLs
search_url = "http://eccdemo03.eccellent.com/Windchill/servlet/odata/v3/CADDocumentMgmt/CADDocuments?$filter=Number eq 'pogo_pin_probe_2.prt' or Name eq 'pogo_pin_probe_2.prt'&ptc.search.latestversion=true"
representations_endpoint = "http://eccdemo03.eccellent.com/Windchill/servlet/odata/v3/CADDocumentMgmt/CADDocuments('OR:wt.epm.EPMDocument:196404')/Representations"

# URL encoding
search_url = quote(search_url, safe=':/?=&')
representations_endpoint = quote(representations_endpoint, safe=':/?=&')

# Create a password manager
password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

# Add the username and password
password_mgr.add_password(None, BASE_URL, USERNAME, PASSWORD)

handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

# Create an opener that will use the handler
opener = urllib.request.build_opener(handler)

# Use the opener to open the URL
with opener.open(search_url) as url:
    search_data = json.loads(url.read().decode())

with opener.open(representations_endpoint) as url:
    representations_data = json.loads(url.read().decode())

# Extract the necessary data from the JSON
search_results = search_data['value']
representations = representations_data['value']

# GUI Creation and Event Handling

# Create a QTableWidget and set its row and column count
app = QApplication(sys.argv)
table = QTableWidget()
table.setRowCount(len(search_results))  # Assuming search_results is populated from the API response
table.setColumnCount(6)  # 6 columns: Thumbnail, Number, Name, Version, State, Download Files

# For each row in the table, create a QLabel for the thumbnail, a QTableWidgetItem for the number, name, version, and state, and a QWidget with QPushButtons for the download files
# Thumbnail and other columns handling
for i, result in enumerate(search_results):
    print(f"Processing result {result}")
    # Thumbnail
    thumbnail_label = QLabel()
    # Find the corresponding representation for this result
    representation = next((rep for rep in representations if rep['ID'] == result['ID']), None)
    if representation:
        thumbnail_file_path = representation.get('TwoDThumbnailURL', {}).get('URL', '')
        print(f"Thumbnail file path: {thumbnail_file_path}")  # Print the file path
        if thumbnail_file_path:
            try:
                if not os.path.isfile(thumbnail_file_path):
                    print(f"File does not exist: {thumbnail_file_path}")
                    continue
                pixmap = QPixmap(thumbnail_file_path)  # Load the QPixmap from the file
                if pixmap.isNull():
                    print(f"Failed to load image: {thumbnail_file_path}")
                    continue
                pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio)  # Scale the pixmap
                thumbnail_label.setPixmap(pixmap)
            except Exception as e:
                print(f"Error loading thumbnail from {thumbnail_file_path}: {e}")

    table.setCellWidget(i, 0, thumbnail_label)

    # Number, Name, Version, State
    number_item = QTableWidgetItem(result.get('Number', 'No Number'))
    name_item = QTableWidgetItem(result.get('Name', 'No Name'))
    version_item = QTableWidgetItem(result.get('Version', 'No Version'))
    state_item = QTableWidgetItem(result.get('State', {}).get('Display', 'No State'))

    table.setItem(i, 1, number_item)
    table.setItem(i, 2, name_item)
    table.setItem(i, 3, version_item)
    table.setItem(i, 4, state_item)

    # Download Files
    download_files_widget = QWidget()
    download_files_layout = QHBoxLayout(download_files_widget)

    additional_files = representations[0].get('AdditionalFiles', [])
    print(f"Additional files: {additional_files}")
    if additional_files:
        for file in additional_files:
            file_url = file.get('URL', '')
            mime_type = file.get('MimeType', '')
            icon_file_name = mime_type_to_icon.get(mime_type, 'default_icon.png')
            icon_file_path = f'static/images/{icon_file_name}'
            print(icon_file_path)

            if os.path.exists(icon_file_path):
                button = QPushButton()
                button.setIcon(QIcon(icon_file_path))
                button.setIconSize(QSize(64, 64))
                button.clicked.connect(lambda _, url=file_url: webbrowser.open(url))
                download_files_layout.addWidget(button)
            else:
                print(f"Icon file not found for MIME type {mime_type}: {icon_file_path}")

    table.setCellWidget(i, 5, download_files_widget)

# Connect the clicked signal of the QTableWidget to a function that opens the `creo_view_url` if the thumbnail is clicked or the corresponding file if a download button is clicked
def on_click(row, column):
    if column == 0:
        thumbnail_label = table.cellWidget(row, column)
        creo_view_command = f"\"{creo_view_agent}\\pvagent.exe\" {thumbnail_label.property('creo_view_url')}"
        subprocess.run(creo_view_command, shell=True)

table.cellClicked.connect(on_click)

# Display the table
table.show()
sys.exit(app.exec_())
