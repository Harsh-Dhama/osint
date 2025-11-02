"""
Tracker Module PDF Report Generator
Generates professional PDF reports for Number/Email searches with branding and disclaimers
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import qrcode
from io import BytesIO
import json

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable, KeepTogether
)
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)


class TrackerReportGenerator:
    """Generate professional PDF reports for tracker searches"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Colors
        self.primary_color = HexColor('#1e3a8a')  # Dark blue
        self.secondary_color = HexColor('#3b82f6')  # Blue
        self.danger_color = HexColor('#dc2626')  # Red
        self.success_color = HexColor('#16a34a')  # Green
        self.warning_color = HexColor('#ea580c')  # Orange
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        # Confidential watermark style
        self.styles.add(ParagraphStyle(
            name='Confidential',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Disclaimer style
        self.styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_JUSTIFY,
            leading=10
        ))
    
    def generate_report(
        self,
        search_data: Dict[str, Any],
        case_info: Dict[str, Any],
        user_info: Dict[str, Any],
        output_path: str
    ) -> bool:
        """
        Generate complete PDF report for tracker search
        
        Args:
            search_data: Complete search results with all modules
            case_info: Case details (number, title, etc.)
            user_info: Officer details (name, badge, department)
            output_path: Path to save PDF file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[TrackerReport] Generating PDF report: {output_path}")
            
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build content
            story = []
            
            # Add header
            story.extend(self._build_header())
            
            # Add confidential notice
            story.extend(self._build_confidential_notice())
            
            # Add case information
            story.extend(self._build_case_info(case_info, user_info))
            
            # Add search details
            story.extend(self._build_search_details(search_data))
            
            # Add results summary
            story.extend(self._build_results_summary(search_data))
            
            # Add detailed module results
            story.extend(self._build_module_results(search_data))
            
            # Add disclaimer
            story.extend(self._build_disclaimer())
            
            # Add footer with QR code
            story.extend(self._build_footer(search_data, case_info))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"[TrackerReport] ✓ PDF report generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"[TrackerReport] Failed to generate PDF: {e}")
            return False
    
    def _build_header(self) -> List:
        """Build report header"""
        elements = []
        
        # Agency logo placeholder (add actual logo if available)
        elements.append(Spacer(1, 0.2*inch))
        
        # Title
        title = Paragraph("OSINT PLATFORM", self.styles['CustomTitle'])
        elements.append(title)
        
        subtitle = Paragraph(
            "Number/Email Search Tracker - Intelligence Report",
            self.styles['CustomHeading']
        )
        elements.append(subtitle)
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_confidential_notice(self) -> List:
        """Build confidential watermark"""
        elements = []
        
        confidential_text = """
        <para align="center" fontName="Helvetica-Bold" fontSize="12" textColor="red">
        ⚠️ CONFIDENTIAL - LAW ENFORCEMENT USE ONLY ⚠️<br/>
        This document contains sensitive information obtained through authorized channels.<br/>
        Unauthorized disclosure is a criminal offense.
        </para>
        """
        
        elements.append(Paragraph(confidential_text, self.styles['Normal']))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.red))
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_case_info(self, case_info: Dict, user_info: Dict) -> List:
        """Build case information section"""
        elements = []
        
        elements.append(Paragraph("Case Information", self.styles['CustomHeading']))
        
        # Case details table
        case_data = [
            ['Case Number:', case_info.get('case_number', 'N/A')],
            ['Case Title:', case_info.get('title', 'N/A')],
            ['Investigating Officer:', user_info.get('full_name', 'N/A')],
            ['Badge Number:', user_info.get('badge_number', 'N/A')],
            ['Department:', user_info.get('department', 'N/A')],
            ['Report Generated:', datetime.now().strftime('%d %b %Y, %H:%M IST')]
        ]
        
        case_table = Table(case_data, colWidths=[2*inch, 4*inch])
        case_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(case_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_search_details(self, search_data: Dict) -> List:
        """Build search details section"""
        elements = []
        
        elements.append(Paragraph("Search Details", self.styles['CustomHeading']))
        
        search_details = [
            ['Search Type:', search_data.get('search_type', 'N/A').upper()],
            ['Search Value:', search_data.get('search_value', 'N/A')],
            ['Modules Queried:', ', '.join(search_data.get('modules_requested', []))],
            ['Total Modules:', str(len(search_data.get('module_results', [])))],
            ['Credits Used:', str(search_data.get('credits_used', 0))],
            ['Search Date:', search_data.get('searched_at', 'N/A')],
            ['Search Status:', search_data.get('status', 'N/A').upper()],
        ]
        
        search_table = Table(search_details, colWidths=[2*inch, 4*inch])
        search_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(search_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_results_summary(self, search_data: Dict) -> List:
        """Build results summary section"""
        elements = []
        
        elements.append(Paragraph("Results Summary", self.styles['CustomHeading']))
        
        summary = search_data.get('summary', {})
        
        # Identity section
        if summary.get('identity'):
            identity = summary['identity']
            elements.append(Paragraph("✓ Identity Information", self.styles['CustomSubheading']))
            
            if identity.get('primary_name'):
                elements.append(Paragraph(
                    f"<b>Primary Name:</b> {identity['primary_name']}",
                    self.styles['Normal']
                ))
            
            if identity.get('names') and len(identity['names']) > 1:
                elements.append(Paragraph(
                    f"<b>Also Known As:</b> {', '.join(identity['names'][1:])}",
                    self.styles['Normal']
                ))
            
            elements.append(Spacer(1, 0.1*inch))
        
        # Contact information
        if summary.get('contact'):
            contact = summary['contact']
            elements.append(Paragraph("✓ Contact Information", self.styles['CustomSubheading']))
            
            if contact.get('emails'):
                elements.append(Paragraph(
                    f"<b>Email Addresses:</b> {', '.join(contact['emails'][:5])}",
                    self.styles['Normal']
                ))
            
            if contact.get('phone_numbers'):
                elements.append(Paragraph(
                    f"<b>Phone Numbers:</b> {', '.join(contact['phone_numbers'][:5])}",
                    self.styles['Normal']
                ))
            
            if contact.get('social_profiles'):
                platforms = [p['platform'] for p in contact['social_profiles']]
                elements.append(Paragraph(
                    f"<b>Social Media:</b> {', '.join(platforms)}",
                    self.styles['Normal']
                ))
            
            elements.append(Spacer(1, 0.1*inch))
        
        # Financial information
        if summary.get('financial'):
            financial = summary['financial']
            if financial.get('upi_ids') or financial.get('banks'):
                elements.append(Paragraph("✓ Financial Data", self.styles['CustomSubheading']))
                
                if financial.get('upi_ids'):
                    elements.append(Paragraph(
                        f"<b>UPI IDs:</b> {', '.join(financial['upi_ids'])}",
                        self.styles['Normal']
                    ))
                
                if financial.get('banks'):
                    elements.append(Paragraph(
                        f"<b>Banks:</b> {', '.join(financial['banks'])}",
                        self.styles['Normal']
                    ))
                
                elements.append(Spacer(1, 0.1*inch))
        
        # Verification flags
        if summary.get('verification'):
            verification = summary['verification']
            elements.append(Paragraph("⚠️ Sensitive Data Access Log", self.styles['CustomSubheading']))
            
            if verification.get('aadhaar_linked'):
                elements.append(Paragraph(
                    "<b>Aadhaar Verification:</b> <font color='green'>LINKED</font>",
                    self.styles['Normal']
                ))
            
            if verification.get('vehicle_registered'):
                elements.append(Paragraph(
                    "<b>Vehicle Registration:</b> <font color='green'>FOUND</font>",
                    self.styles['Normal']
                ))
            
            elements.append(Spacer(1, 0.1*inch))
        
        # Data breaches
        if summary.get('data_leaks'):
            leaks = summary['data_leaks']
            if leaks.get('breaches_found', 0) > 0:
                elements.append(Paragraph(
                    f"<font color='red'>⚠️ Data Breach Alert: {leaks['breaches_found']} breach(es) found</font>",
                    self.styles['CustomSubheading']
                ))
                
                if leaks.get('exposed_data'):
                    elements.append(Paragraph(
                        f"<b>Exposed Data Types:</b> {', '.join(leaks['exposed_data'])}",
                        self.styles['Normal']
                    ))
                
                elements.append(Spacer(1, 0.1*inch))
        
        # Confidence assessment
        confidence = summary.get('confidence_assessment', 'medium').upper()
        confidence_color = {
            'HIGH': 'green',
            'MEDIUM': 'orange',
            'LOW': 'red'
        }.get(confidence, 'black')
        
        elements.append(Paragraph(
            f"<b>Overall Confidence Level:</b> <font color='{confidence_color}'>{confidence}</font>",
            self.styles['Normal']
        ))
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(PageBreak())
        
        return elements
    
    def _build_module_results(self, search_data: Dict) -> List:
        """Build detailed module results"""
        elements = []
        
        elements.append(Paragraph("Detailed Module Results", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        module_results = search_data.get('module_results', [])
        
        for idx, result in enumerate(module_results, 1):
            module_name = result.get('module', 'Unknown').replace('_', ' ').title()
            confidence = result.get('confidence', 'medium').upper()
            source = result.get('source', 'N/A')
            data = result.get('data', {})
            
            # Module header
            elements.append(Paragraph(
                f"[{idx}] {module_name}",
                self.styles['CustomSubheading']
            ))
            
            # Metadata
            meta_text = f"<b>Source:</b> {source} | <b>Confidence:</b> "
            confidence_color = {
                'HIGH': 'green',
                'MEDIUM': 'orange',
                'LOW': 'red'
            }.get(confidence, 'black')
            meta_text += f"<font color='{confidence_color}'>{confidence}</font>"
            
            elements.append(Paragraph(meta_text, self.styles['Normal']))
            elements.append(Spacer(1, 0.05*inch))
            
            # Module data
            if data:
                data_items = []
                for key, value in data.items():
                    if value and value != {} and value != []:
                        # Format key nicely
                        display_key = key.replace('_', ' ').title()
                        
                        # Format value
                        if isinstance(value, list):
                            display_value = ', '.join(str(v) for v in value[:10])
                            if len(value) > 10:
                                display_value += f" ... (+{len(value) - 10} more)"
                        elif isinstance(value, dict):
                            display_value = json.dumps(value, indent=2)
                        else:
                            display_value = str(value)
                        
                        data_items.append([display_key + ':', display_value])
                
                if data_items:
                    data_table = Table(data_items, colWidths=[1.5*inch, 4.5*inch])
                    data_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ]))
                    
                    elements.append(data_table)
            else:
                elements.append(Paragraph("<i>No data available</i>", self.styles['Normal']))
            
            elements.append(Spacer(1, 0.2*inch))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_disclaimer(self) -> List:
        """Build legal disclaimer"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Legal Disclaimer", self.styles['CustomHeading']))
        
        disclaimer_text = """
        This report contains <b>SENSITIVE PERSONAL INFORMATION</b> obtained through authorized 
        law enforcement intelligence gathering channels. The data has been collected in compliance 
        with applicable laws including the Information Technology Act, 2000, and related provisions.
        <br/><br/>
        <b>Legal Requirements:</b>
        <br/>
        • This information must only be used for legitimate investigative purposes
        <br/>
        • Access is restricted to authorized law enforcement personnel
        <br/>
        • Unauthorized disclosure constitutes a criminal offense
        <br/>
        • Data must be handled in accordance with privacy protection regulations
        <br/><br/>
        <b>Data Sources:</b>
        <br/>
        Information in this report has been aggregated from multiple third-party intelligence sources. 
        While efforts have been made to verify accuracy, the platform does not guarantee the 
        completeness or absolute accuracy of all data points. Investigators should corroborate 
        critical information through additional sources.
        <br/><br/>
        <b>Retention & Security:</b>
        <br/>
        • All searches are logged and audited
        <br/>
        • Data is stored locally with encryption
        <br/>
        • Reports must be securely stored as part of case files
        <br/>
        • Destruction must follow departmental data retention policies
        <br/><br/>
        <font color="red"><b>⚠️ HANDLE WITH UTMOST CONFIDENTIALITY</b></font>
        """
        
        elements.append(Paragraph(disclaimer_text, self.styles['Disclaimer']))
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_footer(self, search_data: Dict, case_info: Dict) -> List:
        """Build report footer with QR code"""
        elements = []
        
        elements.append(HRFlowable(width="100%", thickness=2, color=self.primary_color))
        elements.append(Spacer(1, 0.2*inch))
        
        # Generate QR code for report verification
        report_id = f"TRK-{case_info.get('case_number', 'UNKNOWN')}-{search_data.get('search_id', 0)}"
        qr_data = f"OSINT_TRACKER_REPORT:{report_id}:{datetime.now().isoformat()}"
        
        try:
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Create QR code image
            qr_image = Image(qr_buffer, width=1*inch, height=1*inch)
            
            # Footer table with QR code and info
            footer_data = [
                [
                    qr_image,
                    Paragraph(
                        f"""
                        <b>Report ID:</b> {report_id}<br/>
                        <b>Generated:</b> {datetime.now().strftime('%d %b %Y, %H:%M:%S IST')}<br/>
                        <b>Platform:</b> OSINT Platform v1.0<br/>
                        <b>Module:</b> Number/Email Tracker
                        """,
                        self.styles['Normal']
                    )
                ]
            ]
            
            footer_table = Table(footer_data, colWidths=[1.5*inch, 4.5*inch])
            footer_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ]))
            
            elements.append(footer_table)
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            elements.append(Paragraph(
                f"<b>Report ID:</b> {report_id}",
                self.styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.1*inch))
        
        # Final confidentiality notice
        elements.append(Paragraph(
            "<para align='center'><font color='red' size='8'>"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>"
            "CONFIDENTIAL - FOR LAW ENFORCEMENT USE ONLY<br/>"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            "</font></para>",
            self.styles['Normal']
        ))
        
        return elements


def generate_tracker_report(
    search_id: int,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to generate tracker report
    
    Args:
        search_id: ID of the tracker search
        output_path: Optional output path, auto-generated if not provided
        
    Returns:
        Path to generated PDF file, or None if failed
    """
    from backend.database.database import SessionLocal
    from backend.database.models import NumberEmailSearch, Case, User
    from backend.modules.tracker_service import TrackerService
    
    db = SessionLocal()
    
    try:
        # Get search data
        service = TrackerService(db)
        search_data = service.get_search_results(search_id)
        
        if not search_data:
            logger.error(f"Search {search_id} not found")
            return None
        
        # Get search object
        search = db.query(NumberEmailSearch).filter(
            NumberEmailSearch.id == search_id
        ).first()
        
        if not search:
            return None
        
        # Get case info
        case = db.query(Case).filter(Case.id == search.case_id).first()
        case_info = {
            'case_number': case.case_number if case else 'N/A',
            'title': case.title if case else 'N/A',
        }
        
        # Get user info
        user = db.query(User).filter(User.id == search.user_id).first()
        user_info = {
            'full_name': user.full_name if user else 'N/A',
            'badge_number': user.badge_number if user else 'N/A',
            'department': user.department if user else 'N/A',
        }
        
        # Generate output path if not provided
        if not output_path:
            reports_dir = Path('reports/tracker')
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tracker_{case.case_number}_{search_id}_{timestamp}.pdf"
            output_path = str(reports_dir / filename)
        
        # Generate report
        generator = TrackerReportGenerator()
        success = generator.generate_report(
            search_data=search_data,
            case_info=case_info,
            user_info=user_info,
            output_path=output_path
        )
        
        if success:
            logger.info(f"[TrackerReport] Report saved to: {output_path}")
            return output_path
        else:
            return None
            
    except Exception as e:
        logger.error(f"Failed to generate tracker report: {e}")
        return None
        
    finally:
        db.close()
