from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLabel, QComboBox, QLineEdit, QPushButton, QHBoxLayout, QHeaderView, QTreeView, QListWidget, QListWidgetItem, QStyledItemDelegate, QApplication 
from PyQt5.QtGui import QImage, QPixmap, QDesktopServices, QIcon, QStandardItemModel, QStandardItem, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QUrl, QSize
import sys
import requests
import os
import json
import base64
from requests.auth import HTTPBasicAuth
import configparser
from urllib.parse import urlparse, unquote, parse_qs
from xml.etree import ElementTree as ET
import subprocess
from functools import partial
import webbrowser

# Load Windchill configuration from windchill.config
config = configparser.ConfigParser()
config.read('windchill.config')

BASE_URL = config['Windchill']['base_url']
USERNAME = config['Windchill']['username']
PASSWORD = config['Windchill']['password']

# Create a session object
session = requests.Session()
session.auth = (USERNAME, PASSWORD)

# Initialize the application
app = QApplication(sys.argv)

# Create the main window
window = QMainWindow()
window.setWindowTitle("WindAccess - Windchill Simple Search App")
window.setMinimumSize(1250, 400)

# Create the main widget and layout
main_widget = QWidget()
window.setCentralWidget(main_widget)
layout = QVBoxLayout(main_widget)

# Create the top layout
top_layout = QHBoxLayout()
layout.addLayout(top_layout)

# Add the logo label
logo_label = QLabel()
pixmap = QPixmap("static/images/WINDACCESS.png")
logo_label.setPixmap(pixmap)
top_layout.addWidget(logo_label)

# Get the directory of the current script file
script_dir = os.path.dirname(os.path.realpath(__file__))

# Define a mapping from MimeTypes to icon files
mime_type_to_icon = {
    'image/vnd.dwg': 'dwg_icon.png',
    'image/vnd.dxf': 'dxf_icon.png',
    'x-unknown/x-unknown': 'unknown_icon.png',
    'application/pdf': 'pdf_icon.png',
    # Add more mappings as needed
}

# Add the document type label and dropdown
document_type_label = QLabel("Select Document Type:")
top_layout.addWidget(document_type_label)
document_type_dropdown = QComboBox()
document_type_dropdown.addItems(["Part", "CAD Document", "Document"])
top_layout.addWidget(document_type_dropdown)

# Add the search keyword label and entry
search_keyword_label = QLabel("Search:")
top_layout.addWidget(search_keyword_label)
search_keyword_entry = QLineEdit()
top_layout.addWidget(search_keyword_entry)

# Add the search button
search_button = QPushButton("Search")
top_layout.addWidget(search_button)

# Add the search results table
search_results_table = QTableWidget(0, 6)
search_results_table.setHorizontalHeaderLabels(["Thumbnail", "Number", "Name", "Version", "State", "Download Files"])
layout.addWidget(search_results_table)

# Set the resize mode of the horizontal header
header = search_results_table.horizontalHeader()

# Set the resize mode of each column
for i in range(search_results_table.columnCount()):
    if i == search_results_table.columnCount() - 1:  # The last column ("Download Files")
        header.setSectionResizeMode(i, QHeaderView.Stretch)
    else:
        header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
def create_icon_label(url, icon_path):
    label = QLabel()
    pixmap = QPixmap(icon_path).scaled(20, 20, Qt.KeepAspectRatio)
    label.setPixmap(pixmap)
    label.setToolTip(url)

    # Use a QEvent to handle the click event
    label.mousePressEvent = lambda event: QDesktopServices.openUrl(QUrl(url))
    return label

def openUrl(event, url):
    QDesktopServices.openUrl(QUrl(url))   
class FileIconView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.header().hide()  # Hide the header
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.setMaximumHeight(70)  # Adjust height as needed
# Custom model for displaying icons
class IconModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(IconModel, self).__init__(parent)

class DownloadFilesWidget(QWidget):
    def __init__(self, files, parent=None):
        super(DownloadFilesWidget, self).__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for file in files:
            mime_type = file['MimeType']
            icon_file_name = mime_type_to_icon.get(mime_type, 'default_icon.png')
            icon_file_path = os.path.join(script_dir, 'static', 'images', icon_file_name)

            if os.path.exists(icon_file_path):
                button = QPushButton()
                button.setIcon(QIcon(icon_file_path))
                button.setIconSize(QSize(20, 20))  # Adjust the icon size as needed
                button.setFixedSize(24, 24)  # Adjust the button size as needed
                button.clicked.connect(lambda _, url=file['URL']: QDesktopServices.openUrl(QUrl(url)))
                layout.addWidget(button)
            else:
                layout.addWidget(QLabel("Icon not found"))

        self.setLayout(layout)

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)

    def mousePressEvent(self, event):
        QDesktopServices.openUrl(QUrl(self.toolTip()))
class IconWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

    def add_icon(self, icon_path):
        button = QPushButton()
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(20, 20))
        self.layout.addWidget(button)

class FileIconWidget(QWidget):
    def __init__(self, files, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for file in files:
            mime_type = file['MimeType']
            url = file['URL']
            icon_file = mime_type_to_icon.get(mime_type, 'default_icon.png')
            icon_file_path = os.path.join(script_dir, 'static', 'images', icon_file)

            if os.path.exists(icon_file_path):
                icon_label = QLabel()
                icon_pixmap = QPixmap(icon_file_path).scaled(20, 20, Qt.KeepAspectRatio)
                icon_label.setPixmap(icon_pixmap)
                icon_label.setCursor(Qt.PointingHandCursor)
                icon_label.setToolTip(f"Open: {file['FileName']}")

                # Connect the label click event
                icon_label.mousePressEvent = lambda event, url=url: self.openUrl(url)

                layout.addWidget(icon_label)

    def openUrl(self, url):
        QDesktopServices.openUrl(QUrl(url))

class IconDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(IconDelegate, self).__init__(parent)
        # Initialize any necessary variables, e.g., icon size

    def paint(self, painter, option, index):
        # Extract the data (list of icon paths) from the model
        icon_paths = index.model().data(index, Qt.UserRole)
        
        # Check if icon_paths is valid
        if not icon_paths:
            super(IconDelegate, self).paint(painter, option, index)
            return

        # Painter code to draw icons
        x = option.rect.left()
        y = option.rect.top()
        for icon_path in icon_paths:
            pixmap = QPixmap(icon_path)
            painter.drawPixmap(x, y, pixmap.scaled(20, 20, Qt.KeepAspectRatio))
            x += 24  # Move to the right for the next icon
# Define the perform_search function
def perform_search():
    creo_view_urls = []  # Initialize an empty list to store the URLs
    print("perform_search called")  # Debug print
    try:
        document_type = document_type_dropdown.currentText()
        search_keyword = search_keyword_entry.text()

        endpoint_mapping = {
            'Part': 'servlet/odata/v5/ProdMgmt/Parts',
            'CAD Document': 'servlet/odata/v3/CADDocumentMgmt/CADDocuments',
            'Document': 'servlet/odata/v5/DocMgmt/Documents'
        }

        # Construct the filter parameter based on the search keyword
        filter_param = ''
        if search_keyword:
            if search_keyword.startswith('*') and search_keyword.endswith('*'):
                keyword = search_keyword.strip('*')
                filter_param = f"$filter=contains(Number, '{keyword}') or contains(Name, '{keyword}')"
            elif search_keyword.startswith('*'):
                keyword = search_keyword.strip('*')
                filter_param = f"$filter=endswith(Number, '{keyword}') or endswith(Name, '{keyword}')"
            elif search_keyword.endswith('*'):
                keyword = search_keyword.strip('*')
                filter_param = f"$filter=startswith(Number, '{keyword}') or startswith(Name, '{keyword}')"
            else:
                filter_param = f"$filter=Number eq '{search_keyword}' or Name eq '{search_keyword}'"

        # Add the option to only show the latest version
        additional_params = '&ptc.search.latestversion=true' 
        search_url = f"{BASE_URL}/{endpoint_mapping.get(document_type, '')}?{filter_param}{additional_params}"
        print(f"search_url: {search_url}")
        response = session.get(search_url)
        print(f"response: {response}") 

        if response.status_code == 200:
            try:
                # Clear previous search results from the table
                search_results = response.json().get('value', [])
            except requests.exceptions.JSONDecodeError:
                print("Received an empty response from the API")
                search_results = []

            # Clear the previous search results
            search_results_table.setRowCount(0)

            # Insert new search results into the table
            for index, result in enumerate(search_results):
                state_display = result.get('State', {}).get('Display', '')
                document_id = result.get('ID', '')
                additional_files = result.get('AdditionalFiles', [])
                THUMBNAIL_COLUMN_INDEX = 0

                # Add Thumbnail column with image or "No Image"
                thumbnail_label = QLabel()
                thumbnail_label.setAlignment(Qt.AlignCenter)  # Ensure alignment
                thumbnail_image = None 

                creo_view_url = None  # Initialize creo_view_url here
                
                # Initialize an empty list to hold the URLs
                #urls = []

                if document_id:
                    try:
                        representations_endpoint = f"{BASE_URL}/{endpoint_mapping[document_type]}('{document_id}')/Representations"
                        print(f"representations_endpoint: {representations_endpoint}")
                        representations_response = session.get(representations_endpoint)
                        download_files_widget = QWidget()
                        download_files_layout = QHBoxLayout(download_files_widget)
                        if representations_response.status_code == 200:
                            data = representations_response.json()  # Simplified JSON parsing

                            additional_files = data.get('value', [{}])[0].get('AdditionalFiles', [])
                            thumbnail_url = data.get('value', [{}])[0].get('TwoDThumbnailURL', {}).get('URL', '')
                            creo_view_url = data.get('value', [{}])[0].get('CreoViewURL', {}).get('URL', '')

                            DOWNLOAD_FILES_COLUMN_INDEX = 5  # Adjust as per your table's structure
                           
                            if additional_files:
                                for file in additional_files:
                                    file_url = file.get('URL', '')
                                    print(f"THIS IS THE FILE URL: {file_url}")
                                    mime_type = file.get('MimeType', '')
                                    print(f"THIS IS THE MIME TYPE: {mime_type}")
                                    icon_file_name = mime_type_to_icon.get(mime_type, 'default_icon.png')
                                    icon_file_path = f'static/images/{icon_file_name}'
                                    print(icon_file_path)

                                    if os.path.exists(icon_file_path):
                                        button = QPushButton()
                                        button.setIcon(QIcon(icon_file_path))
                                        button.setIconSize(QSize(10, 10))
                                        button.clicked.connect(lambda _, url=file_url: webbrowser.open(url))
                                        download_files_layout.addWidget(button)
                                    else:
                                        print(f"Icon file not found for MIME type {mime_type}: {icon_file_path}")

                                # Add the cell widget to the table
                                search_results_table.setCellWidget(index, DOWNLOAD_FILES_COLUMN_INDEX, download_files_widget)
                            else:
                                search_results_table.setItem(index, DOWNLOAD_FILES_COLUMN_INDEX, QTableWidgetItem("No Downloads"))
    

                            # Store the creo_view_url in the UserRole of the Thumbnail column's QTableWidgetItem
                            search_results_table.update()
                            thumbnail_url_item = QTableWidgetItem()
                            thumbnail_url_item.setData(Qt.UserRole, creo_view_url)
                            #search_results_table.setItem(index, THUMBNAIL_COLUMN_INDEX, thumbnail_url_item)

                            # Create a QLabel to hold the image
                            thumbnail_label = QLabel()
                            thumbnail_label.setAlignment(Qt.AlignCenter)

                            THUMBNAIL_COLUMN_INDEX = 0  # Adjust as per your table's structure  

                            if thumbnail_url:
                                image_response = requests.get(thumbnail_url, stream=True, auth=(USERNAME, PASSWORD))
                                if image_response.status_code == 200:
                                    thumbnail_image = QImage()
                                    thumbnail_image.loadFromData(image_response.content)
                                    thumbnail_label.setPixmap(QPixmap.fromImage(thumbnail_image).scaled(200, 200, Qt.KeepAspectRatio))
                            else:
                                thumbnail_label.setText("No Image")

                            # Add the QLabel to the QTableWidget
                            search_results_table.setCellWidget(index, THUMBNAIL_COLUMN_INDEX, thumbnail_label)

                    except Exception as e:
                        print(f"Error loading representations: {e}")


                # Add the QWidget to the QTableWidget
                #search_results_table.setCellWidget(index, DOWNLOAD_FILES_COLUMN_INDEX, button_holder)
                # Populate the table with the new search results
                search_results_table.insertRow(index)
                search_results_table.setCellWidget(index, 0, thumbnail_label)

                # Extract the values from the result dictionary
                number = result.get('Number', '')
                name = result.get('Name', '')
                version = result.get('Version', '')

                # Set the table items to the extracted values
                item = QTableWidgetItem(number)
                item.setData(Qt.UserRole, creo_view_url)  # Store the URL in the QTableWidgetItem

                # Set the table items to the extracted values
                search_results_table.setItem(index, 1, item)
                search_results_table.setItem(index, 2, QTableWidgetItem(name))
                search_results_table.setItem(index, 3, QTableWidgetItem(version))

                search_results_table.setItem(index, 4, QTableWidgetItem(state_display))

                # Create a QTableWidgetItem to hold the creo_view_url
                creo_view_url_item = QTableWidgetItem()
                creo_view_url_item.setData(Qt.UserRole, creo_view_url)
                search_results_table.setItem(index, THUMBNAIL_COLUMN_INDEX, creo_view_url_item)
            
                # Define the open_url function
                def open_url(row, column):
                    if column == THUMBNAIL_COLUMN_INDEX:  # Only react when a cell in the Thumbnail column is clicked
                        item = search_results_table.item(row, column)
                        if item is not None:
                            creo_view_url = item.data(Qt.UserRole)  # Extract the URL from the QTableWidgetItem
                            print(f"THIS IS THE creo_view_url -line 274: {creo_view_url}")
                            if creo_view_url is not None:
                                try:
                                    # Construct the command to launch Creo View
                                    creo_view_agent = config['Windchill']['creo_view_agent']
                                    creo_view_command = f"\"{creo_view_agent}\\pvagent.exe\" {creo_view_url}"
                                    print(f"Launching Creo View with command: {creo_view_command}")
                                    
                                    # Use subprocess.Popen instead of os.system
                                    subprocess.Popen(creo_view_command, shell=True)
                                except Exception as e:
                                    print(f"An error occurred while launching Creo View: {e}")
                            else:
                                print("No creo_view_url found for this row.")

            # Process the search results
            for index, data in enumerate(search_results):
                search_results_table.insertRow(index)
                # Append the URL to the list
                creo_view_urls.append(creo_view_url)
                # Set the table items to the extracted values
                item = QTableWidgetItem(state_display)
                item.setData(Qt.UserRole, creo_view_url)  # Store the URL in the QTableWidgetItem
                search_results_table.setItem(index, 0, item)  # Set the item in the Thumbnail column
            else:
                print(f"Error fetching representations data for document {document_id}")

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, creo_view_url)
                #search_results_table.setItem(index, THUMBNAIL_COLUMN_INDEX, item)

            # Connect the open_url function to the cellClicked signal
            search_results_table.cellClicked.connect(open_url)


            # Resize columns and rows to fit their content
            search_results_table.resizeColumnsToContents()
            search_results_table.resizeRowsToContents()
            search_results_table.setSortingEnabled(True)
            # Enable alternating row colors
            search_results_table.setAlternatingRowColors(True)

            # Set the stylesheet to specify the colors
            search_results_table.setStyleSheet("""
                QTableWidget {
                    alternate-background-color: lightgray;
                }
            """)
    except Exception as e:
        print(f"An error occurred: {e}")

# Connect the perform_search function to the search button click event
search_button.clicked.connect(perform_search)

# Show the main window
window.show()

# Run the application
sys.exit(app.exec_())

## End Improved Code Snippet ##