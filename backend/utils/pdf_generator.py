"""
WhatsApp Profile PDF Report Generator
Generates professional PDF reports matching the WAProfiler format
"""
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.pdfgen import canvas
from datetime import datetime
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

FONT_PATH = "D:/osint/fonts/NotoSansDevanagari-VariableFont_wdth,wght.ttf"
class WhatsAppProfilePDFGenerator:
    """Generate professional PDF reports for WhatsApp profile data"""
    
    def __init__(self):
        self.page_width = A4[0]
        self.page_height = A4[1]
        self.margin = 0.75 * inch
        pdfmetrics.registerFont(TTFont("NotoDev", FONT_PATH))
        
    def _create_cover_page(self, canvas_obj, case_id: str, officer_name: str = "John Doe"):
        """
        Create the cover page matching WAProfiler format
        Page 1: Title, Logo, Case Info, Confidentiality Notice
        """
        # Set background color - dark blue/navy
        canvas_obj.setFillColorRGB(0.11, 0.18, 0.29)  # Dark blue background
        canvas_obj.rect(0, 0, self.page_width, self.page_height, fill=True, stroke=False)
        
        # Logo placeholder (green checkmark circle)
        # Draw circle
        canvas_obj.setFillColorRGB(0.2, 0.8, 0.4)  # Green color
        circle_center_x = self.page_width / 2
        circle_center_y = self.page_height - 150
        circle_radius = 50
        canvas_obj.circle(circle_center_x, circle_center_y, circle_radius, fill=True, stroke=False)
        
        # Draw checkmark (simplified)
        canvas_obj.setStrokeColorRGB(1, 1, 1)  # White checkmark
        canvas_obj.setLineWidth(5)
        canvas_obj.line(circle_center_x - 15, circle_center_y, 
                       circle_center_x - 5, circle_center_y - 15)
        canvas_obj.line(circle_center_x - 5, circle_center_y - 15, 
                       circle_center_x + 20, circle_center_y + 20)
        
        # Title - WAProfiler
        canvas_obj.setFillColorRGB(1, 1, 1)  # White text
        canvas_obj.setFont("Helvetica-Bold", 36)
        canvas_obj.drawCentredString(self.page_width / 2, circle_center_y - 100, "WAProfiler")
        
        # Subtitle
        canvas_obj.setFont("Helvetica", 16)
        canvas_obj.setFillColorRGB(0.4, 0.7, 1)  # Light blue
        canvas_obj.drawCentredString(self.page_width / 2, circle_center_y - 130, 
                                     "WhatsApp Profiling Intelligence Report")
        
        # Generation timestamp and case info
        canvas_obj.setFont("Helvetica", 12)
        canvas_obj.setFillColorRGB(0.8, 0.8, 0.8)  # Light gray
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        canvas_obj.drawCentredString(self.page_width / 2, circle_center_y - 200, 
                                     f"Generated on: {timestamp}")
        canvas_obj.drawCentredString(self.page_width / 2, circle_center_y - 220, 
                                     f"Officer: {officer_name}  |  Case ID: {case_id}")
        
        # Confidentiality notice (bottom of page)
        canvas_obj.setFont("Helvetica-Oblique", 9)
        canvas_obj.setFillColorRGB(0.6, 0.6, 0.6)  # Medium gray
        notice_y = 80
        notice_text = [
            "This report is confidential and intended solely for the use of authorized personnel in investigative roles.",
            "Do not share, reproduce, or distribute without appropriate clearance and compliance with applicable laws."
        ]
        for i, line in enumerate(notice_text):
            canvas_obj.drawCentredString(self.page_width / 2, notice_y - (i * 12), line)
        
    def _create_summary_table(self, profile_data: dict) -> Table:
            phone = str(profile_data.get("phone_number", "N/A"))
            display_name = str(profile_data.get("display_name", "Not Available")) if profile_data.get("display_name") else "Not Available"
            about = str(profile_data.get("about", "Not Available")) if profile_data.get("about") else "Not Available"
            last_seen = str(profile_data.get("last_seen", "N/A")) if profile_data.get("last_seen") else "N/A"
            scraped_at = str(profile_data.get("scraped_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            # UPDATED style for every cell/Paragraph
            unicode_style = ParagraphStyle(
                name='UnicodeCell',
                fontName='NotoDev',
                fontSize=11,
                leading=15,
                alignment=TA_LEFT
            )

            data = [
                ["Summary Overview", ""],
                ["Phone Number", phone],
                ["Display Name", Paragraph(display_name.replace('\n', '<br/>'), unicode_style)],
                ["About/Bio", Paragraph(about.replace('\n', '<br/>'), unicode_style)],
                ["Last Seen", last_seen],
                ["WhatsApp Status", "Registered" if profile_data.get("is_available") else "Not Registered"],
                ["Extraction Time", scraped_at],
            ]
            table = Table(data, colWidths=[2.5*inch, 4*inch])
            table.setStyle(TableStyle([
                # [table styles are unchanged except font]
                ('FONTNAME', (0, 0), (-1, -1), 'NotoDev'),
                # other styles ...
            ]))
            return table
    
    def _add_profile_picture(self, profile_pic_path: str) -> Image:
        """Add profile picture to report"""
        if profile_pic_path and os.path.exists(profile_pic_path):
            try:
                img = Image(profile_pic_path, width=2*inch, height=2*inch)
                return img
            except Exception as e:
                logger.warning(f"Could not load profile picture: {e}")
        
        # Return placeholder if image not available
        return None
    
    def generate_single_profile_report(
        self, 
        profile_data: dict, 
        case_id: str,
        officer_name: str = "John Doe",
        output_dir: str = "reports/whatsapp"
    ) -> str:
        """
        Generate a complete PDF report for a single WhatsApp profile
        
        Args:
            profile_data: Dictionary containing profile information
            case_id: Case identifier
            officer_name: Name of the officer/investigator
            output_dir: Directory to save the PDF
            
        Returns:
            str: Path to the generated PDF file
        """
        logger.info(f"Generating PDF report for {profile_data.get('phone_number', 'Unknown')}")
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename - convert phone to string first
        phone = str(profile_data.get("phone_number", "unknown")).replace("+", "").replace(" ", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"WAProfiler_{phone}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build document content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1C3D5A'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Page 2: Profile Details
        # Title
        story.append(Paragraph("WhatsApp Profiling Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Case info header
        case_info_style = ParagraphStyle(
            'CaseInfo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", case_info_style))
        story.append(Paragraph(f"Officer: {officer_name} | Case ID: {case_id}", case_info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Logo placeholder (small version for header)
        # You can add a small logo here if needed
        
        # Summary Table
        summary_table = self._create_summary_table(profile_data)
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Profile Picture Section
        story.append(Paragraph("Profile Picture", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        profile_pic_path = profile_data.get("profile_picture") or profile_data.get("profile_picture_path")
        if profile_pic_path and os.path.exists(profile_pic_path):
            try:
                # Center the image
                img = Image(profile_pic_path, width=2*inch, height=2*inch)
                img.hAlign = 'CENTER'
                story.append(img)
            except Exception as e:
                logger.warning(f"Could not add profile picture to PDF: {e}")
                story.append(Paragraph("<i>Profile picture not available</i>", styles['Normal']))
        else:
            story.append(Paragraph("<i>Profile picture not available</i>", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Detailed Information Section
        story.append(Paragraph("Detailed Information", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        details_data = [
            ["Field", "Value"],
            ["Phone Number", profile_data.get("phone_number", "N/A")],
            ["Display Name", profile_data.get("display_name", "Not Available")],
            ["About/Bio", profile_data.get("about", "Not Available")],
            ["Account Status", "Active" if profile_data.get("is_available") else "Inactive"],
            ["Last Seen", profile_data.get("last_seen", "N/A")],
            ["Data Extraction Method", profile_data.get("method", "auto_navigate")],
            ["Extraction Status", profile_data.get("status", "success")],
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 4.5*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F0F0F0')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Footer disclaimer
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=10
        )
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            "<i>This report is confidential and intended for authorized investigative personnel only.</i>",
            disclaimer_style
        ))
        story.append(Paragraph(
            "<i>Generated by WAProfiler - OSINT Intelligence Platform</i>",
            disclaimer_style
        ))
        
        # Build PDF with cover page
        def add_cover_page(canvas_obj, doc):
            canvas_obj.saveState()
            if doc.page == 1:
                self._create_cover_page(canvas_obj, case_id, officer_name)
            canvas_obj.restoreState()
        
        # Build document
        doc.build(story, onFirstPage=add_cover_page, onLaterPages=lambda c, d: None)
        
        logger.info(f"PDF report generated: {filepath}")
        return filepath
    
    def generate_bulk_report(
        self, 
        profiles: list, 
        case_id: str,
        officer_name: str = "John Doe",
        output_dir: str = "reports/whatsapp"
    ) -> str:
        """
        Generate a single PDF report with all profiles in a clean table format.
        Supports Unicode (Hindi/emoji) in all cells using NotoSansDevanagari.
        """
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"WAProfiler_Report_{case_id}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Register the Unicode font
        pdfmetrics.registerFont(TTFont("NotoDev", FONT_PATH))

        unicode_style = ParagraphStyle(
            'UnicodeNormal',
            fontName='NotoDev',
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
        )
        name_style = ParagraphStyle('NameUnicode', parent=unicode_style, fontName='NotoDev', fontSize=11, textColor=colors.HexColor('#1C3D5A'))
        cell_style = ParagraphStyle('CellUnicode', parent=unicode_style, fontSize=10, leading=13)

        story = []
        # Large title/cover section (as before, you can keep or simplify)
        title_style = ParagraphStyle(
            'CoverTitle',
            fontName='NotoDev',
            fontSize=28,
            textColor=colors.HexColor('#1C3D5A'),
            alignment=TA_CENTER,
            spaceAfter=30,
            leading=34
        )
        story.append(Spacer(1, 1.1 * inch))
        story.append(Paragraph("WhatsApp Profiling Report", title_style))
        story.append(Spacer(1, 0.5 * inch))
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontName='NotoDev',
            fontSize=14,
            textColor=colors.HexColor('#4A90E2'),
            alignment=TA_CENTER,
            spaceAfter=10,
        )
        story.append(Paragraph("Comprehensive Profile Analysis", subtitle_style))
        story.append(Spacer(1, 0.8 * inch))

        # Case and officer info
        case_info_style = ParagraphStyle(
            'CaseInfoBox',
            fontName='NotoDev',
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT,
            leading=18,
            leftIndent=30,
            spaceAfter=8
        )
        case_info = [
            f"<b>Case ID:</b> {case_id}",
            f"<b>Investigating Officer:</b> {officer_name}",
            f"<b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}",
            f"<b>Report Time:</b> {datetime.now().strftime('%I:%M %p')}",
        ]
        for info in case_info:
            story.append(Paragraph(info, case_info_style))
        story.append(Spacer(1, 0.8 * inch))

        # Table header
        table_data = [["#", "Phone Number", "Name", "Profile Picture", "About/Bio"]]
        for idx, profile in enumerate(profiles, 1):
            phone = str(profile.get("phone_number", "N/A"))
            name = str(profile.get("display_name") or "Not Available")
            about = str(profile.get("about") or "Not Available")
            if len(about) > 250:
                about = about[:247] + "..."
            profile_pic_path = profile.get("profile_picture") or profile.get("profile_picture_path")
            # Ensure line breaks are preserved
            name_cell = Paragraph(name.replace('\n', '<br/>'), name_style)
            about_cell = Paragraph(about.replace('\n', '<br/>'), unicode_style)
            if profile_pic_path and os.path.exists(profile_pic_path):
                try:
                    img = Image(profile_pic_path, width=1.1 * inch, height=1.1 * inch)
                    img.hAlign = 'CENTER'
                    pic_cell = img
                except Exception:
                    pic_cell = Paragraph("<i>Image error</i>", cell_style)
            else:
                pic_cell = Paragraph("<i>No Image<br/>Available</i>", cell_style)

            table_data.append([
                Paragraph(f"<b>{idx}</b>", unicode_style),
                Paragraph(phone, unicode_style),
                name_cell,
                pic_cell,
                about_cell
            ])

        col_widths = [0.4 * inch, 1.3 * inch, 1.4 * inch, 1.4 * inch, 2.4 * inch]
        results_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        results_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'NotoDev'),
            # Table header styles
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1C3D5A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'NotoDev'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            # Data rows
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#CCCCCC')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1C3D5A')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1C3D5A')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ]))
        # Alternating row colors
        for i in range(1, len(table_data)):
            results_table.setStyle([
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F9F9F9') if i % 2 == 0 else colors.white)
            ])
        story.append(results_table)
        story.append(Spacer(1, 0.5 * inch))
        # Footer
        footer_style = ParagraphStyle(
            'FooterText',
            fontName='NotoDev',
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=5
        )
        story.append(Paragraph(
            "<i>This report is confidential and intended for authorized investigative personnel only.</i>",
            footer_style
        ))
        story.append(Paragraph(
            "<i>Generated by WAProfiler - OSINT Intelligence Platform</i>",
            footer_style
        ))

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        doc.build(story)
        return filepath
# Convenience functions
def generate_whatsapp_profile_pdf(
    profile_data: dict, 
    case_id: str,
    officer_name: str = "John Doe",
    output_dir: str = "reports/whatsapp"
) -> str:
    """Generate a PDF report for a single WhatsApp profile"""
    generator = WhatsAppProfilePDFGenerator()
    return generator.generate_single_profile_report(profile_data, case_id, officer_name, output_dir)


def generate_whatsapp_bulk_pdf(
    profiles: list, 
    case_id: str,
    officer_name: str = "John Doe",
    output_dir: str = "reports/whatsapp"
) -> str:
    """Generate a PDF report for multiple WhatsApp profiles"""
    generator = WhatsAppProfilePDFGenerator()
    return generator.generate_bulk_report(profiles, case_id, officer_name, output_dir)
