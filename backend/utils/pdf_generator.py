"""
WhatsApp Profile PDF Report Generator
Generates professional PDF reports matching the WAProfiler format
"""
from reportlab.lib import colors
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


class WhatsAppProfilePDFGenerator:
    """Generate professional PDF reports for WhatsApp profile data"""
    
    def __init__(self):
        self.page_width = A4[0]
        self.page_height = A4[1]
        self.margin = 0.75 * inch
        
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
        """Create summary overview table (top of page 2)"""
        # Convert values to strings to handle numpy types
        phone = str(profile_data.get("phone_number", "N/A"))
        display_name = str(profile_data.get("display_name", "Not Available")) if profile_data.get("display_name") else "Not Available"
        about = str(profile_data.get("about", "Not Available")) if profile_data.get("about") else "Not Available"
        last_seen = str(profile_data.get("last_seen", "N/A")) if profile_data.get("last_seen") else "N/A"
        scraped_at = str(profile_data.get("scraped_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        data = [
            ["Summary Overview", ""],
            ["Phone Number", phone],
            ["Display Name", display_name],
            ["About/Bio", about],
            ["Last Seen", last_seen],
            ["WhatsApp Status", "Registered" if profile_data.get("is_available") else "Not Registered"],
            ["Extraction Time", scraped_at],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            # Header row (first row)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('SPAN', (0, 0), (-1, 0)),  # Merge header cells
            
            # Data rows
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#E8F4F8')),  # Left column light blue
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            ('BACKGROUND', (1, 1), (1, -1), colors.white),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (1, 1), (1, -1), 10),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
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
        Page 1: Professional intro/cover page with summary
        Page 2+: Detailed table with profile pictures
        
        Args:
            profiles: List of profile dictionaries
            case_id: Case identifier
            officer_name: Name of the officer/investigator
            output_dir: Directory to save the PDF
            
        Returns:
            str: Path to the generated PDF file
        """
        logger.info(f"Generating single consolidated PDF report for {len(profiles)} profiles")
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"WAProfiler_Report_{case_id}_{timestamp}.pdf"
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
        
        story = []
        styles = getSampleStyleSheet()
        
        # ============================================================
        # PAGE 1: PROFESSIONAL INTRO/COVER PAGE
        # ============================================================
        
        # Title with large font
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=colors.HexColor('#1C3D5A'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=34
        )
        
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("WhatsApp Profiling Report", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#4A90E2'),
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=10
        )
        story.append(Paragraph("Comprehensive Profile Analysis", subtitle_style))
        story.append(Spacer(1, 0.8*inch))
        
        # Case information box
        case_info_style = ParagraphStyle(
            'CaseInfoBox',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT,
            fontName='Helvetica',
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
        
        story.append(Spacer(1, 0.8*inch))
        
        # Summary statistics in a clean box
        total = len(profiles)
        registered = sum(1 for p in profiles if p.get("is_available"))
        success = sum(1 for p in profiles if p.get("status") == "success")
        not_registered = total - registered
        
        summary_style = ParagraphStyle(
            'SummaryHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1C3D5A'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=15
        )
        story.append(Paragraph("Summary Statistics", summary_style))
        
        stats_data = [
            ["Metric", "Count", "Percentage"],
            ["Total Numbers Analyzed", str(total), "100%"],
            ["Successfully Extracted", str(success), f"{(success/total*100):.1f}%" if total > 0 else "0%"],
            ["Registered on WhatsApp", str(registered), f"{(registered/total*100):.1f}%" if total > 0 else "0%"],
            ["Not Registered/Unavailable", str(not_registered), f"{(not_registered/total*100):.1f}%" if total > 0 else "0%"],
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1C3D5A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            
            # Grid and padding
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F9F9F9'), colors.white]),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 1*inch))
        
        # Footer on cover page
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        story.append(Paragraph("This report contains confidential information", footer_style))
        story.append(Paragraph("For authorized investigative personnel only", footer_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Generated by WAProfiler - OSINT Intelligence Platform", footer_style))
        
        # Page break to start detailed data on new page
        story.append(PageBreak())
        
        # ============================================================
        # PAGE 2+: DETAILED DATA TABLE WITH PROFILE PICTURES
        # ============================================================
        
        # Section header for detailed profiles
        detail_header_style = ParagraphStyle(
            'DetailHeader',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1C3D5A'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=20,
            spaceBefore=10
        )
        story.append(Paragraph("Detailed Profile Information", detail_header_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Build table data with profile pictures
        table_data = [["#", "Phone Number", "Name", "Profile Picture", "About/Bio"]]
        
        for idx, profile in enumerate(profiles, 1):
            phone = str(profile.get("phone_number", "N/A"))
            name = str(profile.get("display_name") or "Not Available")
            about = str(profile.get("about") or "Not Available")
            
            # Clean bio - remove HTML artifacts
            if about and about != "Not Available":
                import re
                # Remove block-* CSS classes
                about = re.sub(r'block-\w+\s+', '', about)
                about = re.sub(r'favorite-\w+', '', about)
                # Remove extra phone numbers that match the contact's phone
                clean_phone_digits = "".join([c for c in phone if c.isdigit()])
                if clean_phone_digits in about.replace(" ", "").replace("+", ""):
                    # If bio is just the phone number, mark as not available
                    about = "Not Available"
                about = about.strip()
            
            # Truncate long bio
            if len(about) > 120:
                about = about[:117] + "..."
            
            # Handle profile picture
            profile_pic_path = profile.get("profile_picture") or profile.get("profile_picture_path")
            
            if profile_pic_path and os.path.exists(profile_pic_path):
                try:
                    # Create clear, larger thumbnail (1.2 inch square for better visibility)
                    img = Image(profile_pic_path, width=1.2*inch, height=1.2*inch)
                    img.hAlign = 'CENTER'
                    pic_cell = img
                except Exception as e:
                    logger.warning(f"Could not load image {profile_pic_path}: {e}")
                    pic_cell = Paragraph("<i>Image error</i>", styles['Normal'])
            else:
                # Create placeholder for no image
                no_img_style = ParagraphStyle(
                    'NoImage',
                    parent=styles['Normal'],
                    fontSize=8,
                    textColor=colors.grey,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Oblique'
                )
                pic_cell = Paragraph("<i>No Image<br/>Available</i>", no_img_style)
            
            # Style for table cells
            cell_style = ParagraphStyle(
                'CellText',
                parent=styles['Normal'],
                fontSize=9,
                leading=12,
                fontName='Helvetica'
            )
            
            name_style = ParagraphStyle(
                'NameText',
                parent=cell_style,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#1C3D5A')
            )
            
            # Add row
            table_data.append([
                Paragraph(f"<b>{idx}</b>", cell_style),
                Paragraph(phone, cell_style),
                Paragraph(name, name_style),
                pic_cell,
                Paragraph(about, cell_style)
            ])
        
        # Create table with appropriate column widths for clarity
        col_widths = [0.4*inch, 1.3*inch, 1.4*inch, 1.4*inch, 2.4*inch]
        results_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Professional table styling
        table_style = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1C3D5A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows styling
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # # column centered
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Picture column centered
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            
            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#CCCCCC')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1C3D5A')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1C3D5A')),
            
            # Padding for readability
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ]
        
        # Alternating row colors for better readability
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F9F9F9')))
            else:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
        
        results_table.setStyle(TableStyle(table_style))
        
        story.append(results_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Footer on last page
        footer_style = ParagraphStyle(
            'FooterText',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
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
        
        # Build PDF - no custom page handler needed, just build it
        doc.build(story)
        
        logger.info(f"Single consolidated PDF report generated: {filepath}")
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
