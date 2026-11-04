import io
from googleapiclient.http import MediaIoBaseUpload
from xhtml2pdf import pisa
from fastmcp import FastMCP

from config import AppConfig
from services.v1 import GoogleDriveService

mcp = FastMCP('Google Drive Tools')

@mcp.tool
def upload_pdf_to_google_drive(html_content:str,filename:str):
    """
    Upload a pdf file to google drive. 'content' is the content of the pdf in html format,
    the conversion is made internally and 'filename' is the filename for the pdf
    """
    try:
        folder_id = AppConfig.get_config().output_folder_id
        metadata = {
            'name':filename,
            'parents':[folder_id]
        }
        pdf_bytes = io.BytesIO()
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_bytes,
            encoding='utf-8'
        )
        if pisa_status.err:
            return f'Error while generating the pdf report'
        
        pdf_bytes.seek(0)
        media = MediaIoBaseUpload(pdf_bytes,mimetype='application/pdf')
        service = GoogleDriveService.get_service()
        file_link = service.upload_file(media,metadata)
        return f'Report uploaded successfully\nurl: {file_link}'
    except Exception as ex:
        return f'Error: {ex}'