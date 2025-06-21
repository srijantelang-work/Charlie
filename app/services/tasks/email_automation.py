"""
Email Automation Service
Handles email sending and reading operations
"""

import smtplib
import imaplib
import email
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailAutomation:
    """Email automation service for sending and reading emails"""
    
    def __init__(self):
        # Configuration - these would be loaded from environment variables
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.imap_server = getattr(settings, 'IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = getattr(settings, 'IMAP_PORT', 993)
        
        # These should be securely stored and retrieved
        self.email_address = getattr(settings, 'EMAIL_ADDRESS', None)
        self.email_password = getattr(settings, 'EMAIL_PASSWORD', None)
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        is_html: bool = False
    ) -> Dict[str, Any]:
        """Send an email with optional attachments"""
        
        try:
            if not self.email_address or not self.email_password:
                return {
                    'success': False,
                    'error': 'Email credentials not configured'
                }
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {Path(file_path).name}'
                            )
                            msg.attach(part)
                    else:
                        logger.warning(f"Attachment not found: {file_path}")
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                text = msg.as_string()
                server.sendmail(self.email_address, to, text)
            
            return {
                'success': True,
                'message': f'Email sent successfully to {to}',
                'to': to,
                'subject': subject
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def read_emails(
        self,
        limit: int = 10,
        unread_only: bool = True,
        folder: str = 'INBOX'
    ) -> Dict[str, Any]:
        """Read emails from the mailbox"""
        
        try:
            if not self.email_address or not self.email_password:
                return {
                    'success': False,
                    'error': 'Email credentials not configured'
                }
            
            # Connect to IMAP server
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.email_address, self.email_password)
                mail.select(folder)
                
                # Search for emails
                search_criteria = '(UNSEEN)' if unread_only else 'ALL'
                status, messages = mail.search(None, search_criteria)
                
                if status != 'OK':
                    return {
                        'success': False,
                        'error': 'Failed to search emails'
                    }
                
                # Get message IDs
                message_ids = messages[0].split()
                message_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
                
                emails = []
                for msg_id in reversed(message_ids):  # Most recent first
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    
                    if status == 'OK':
                        email_message = email.message_from_bytes(msg_data[0][1])
                        
                        # Extract email content
                        subject = email_message.get('Subject', '')
                        sender = email_message.get('From', '')
                        date = email_message.get('Date', '')
                        
                        # Get email body
                        body = self._extract_email_body(email_message)
                        
                        emails.append({
                            'id': msg_id.decode(),
                            'subject': subject,
                            'from': sender,
                            'date': date,
                            'body': body[:500] + '...' if len(body) > 500 else body,
                            'full_body': body
                        })
            
            return {
                'success': True,
                'emails': emails,
                'count': len(emails),
                'folder': folder
            }
            
        except Exception as e:
            logger.error(f"Failed to read emails: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_email_body(self, email_message) -> str:
        """Extract plain text body from email message"""
        
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode()
            except:
                body = str(email_message.get_payload())
        
        return body
    
    def mark_as_read(self, message_id: str, folder: str = 'INBOX') -> Dict[str, Any]:
        """Mark an email as read"""
        
        try:
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.email_address, self.email_password)
                mail.select(folder)
                
                mail.store(message_id, '+FLAGS', '\\Seen')
                
                return {
                    'success': True,
                    'message': f'Email {message_id} marked as read'
                }
                
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_email(self, message_id: str, folder: str = 'INBOX') -> Dict[str, Any]:
        """Delete an email"""
        
        try:
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.email_address, self.email_password)
                mail.select(folder)
                
                mail.store(message_id, '+FLAGS', '\\Deleted')
                mail.expunge()
                
                return {
                    'success': True,
                    'message': f'Email {message_id} deleted'
                }
                
        except Exception as e:
            logger.error(f"Failed to delete email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_folders(self) -> Dict[str, Any]:
        """Get list of email folders"""
        
        try:
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.email_address, self.email_password)
                
                status, folders = mail.list()
                
                if status == 'OK':
                    folder_list = []
                    for folder in folders:
                        folder_name = folder.decode().split('"')[-2]
                        folder_list.append(folder_name)
                    
                    return {
                        'success': True,
                        'folders': folder_list
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to get folders'
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get folders: {e}")
            return {
                'success': False,
                'error': str(e)
            } 