"""
Username Search Report Generator

Generates professional PDF reports for username search results across social media
platforms and online services. Reports include platform icons, profile links,
discovery dates, case metadata, and officer information.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import qrcode
import io
from sqlalchemy.orm import Session
from backend.database.models import UsernameSearch, UsernameResult

import logging
logger = logging.getLogger(__name__)


class UsernameReportGenerator:
    """Generate professional PDF reports for username searches"""
    
    def __init__(self, search_id: int, db: Session, output_path: Optional[str] = None):
        """
        Initialize report generator
        
        Args:
            search_id: ID of the username search
            db: Database session
            output_path: Optional custom output path
        """
        self.search_id = search_id
        self.db = db
        self.output_path = output_path
        
        # Load search data
        self.search = db.query(UsernameSearch).filter(
            UsernameSearch.id == search_id
        ).first()
        
        if not self.search:
            raise ValueError(f"Username search {search_id} not found")
        
        # Load results
        self.results = db.query(UsernameResult).filter(
            UsernameResult.search_id == search_id
        ).order_by(UsernameResult.confidence_score.desc()).all()
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
        # Colors
        self.primary_color = colors.HexColor('#1e3a8a')  # Dark blue
        self.secondary_color = colors.HexColor('#3b82f6')  # Blue
        self.success_color = colors.HexColor('#10b981')  # Green
        self.warning_color = colors.HexColor('#f59e0b')  # Orange
        self.danger_color = colors.HexColor('#ef4444')  # Red
        self.gray_color = colors.HexColor('#6b7280')  # Gray
        
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        
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
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=10,
            spaceBefore=16,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=colors.HexColor('#3b82f6'),
            borderPadding=5,
            backColor=colors.HexColor('#eff6ff')
        ))
        
        # Confidential notice
        self.styles.add(ParagraphStyle(
            name='Confidential',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.gray_color,
            alignment=TA_CENTER
        ))
    
    def generate(self) -> str:
        """
        Generate the PDF report
        
        Returns:
            Path to generated PDF file
        """
        # Determine output path
        if not self.output_path:
            reports_dir = Path("reports/username")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            case_ref = f"case_{self.search.case_id}" if self.search.case_id else "no_case"
            filename = f"username_{case_ref}_{self.search_id}_{timestamp}.pdf"
            self.output_path = str(reports_dir / filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build content
        story = []
        story.extend(self._build_header())
        story.append(Spacer(1, 0.2*inch))
        story.extend(self._build_confidential_notice())
        story.append(Spacer(1, 0.3*inch))
        story.extend(self._build_search_info())
        story.append(Spacer(1, 0.3*inch))
        story.extend(self._build_summary())
        story.append(Spacer(1, 0.3*inch))
        story.extend(self._build_platform_results())
        story.append(Spacer(1, 0.3*inch))
        story.extend(self._build_disclaimer())
        story.append(Spacer(1, 0.3*inch))
        story.extend(self._build_footer())
        
        # Generate PDF
        doc.build(story)
        
        logger.info(f"Username search report generated: {self.output_path}")
        return self.output_path
    
    def _build_header(self) -> List:
        """Build report header"""
        elements = []
        
        # Title
        title = Paragraph(
            "USERNAME SEARCH REPORT",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Report metadata
        report_info = f"""
        <para align=center>
        <b>Report ID:</b> USR-{self.search_id:06d} | 
        <b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}
        </para>
        """
        elements.append(Paragraph(report_info, self.styles['Normal']))
        
        return elements
    
    def _build_confidential_notice(self) -> List:
        """Build confidential notice banner"""
        elements = []
        
        notice = Paragraph(
            "⚠️ CONFIDENTIAL - FOR OFFICIAL USE ONLY ⚠️",
            self.styles['Confidential']
        )
        elements.append(notice)
        
        return elements
    
    def _build_search_info(self) -> List:
        """Build search information section"""
        elements = []
        
        # Section header
        header = Paragraph("Search Information", self.styles['SectionHeader'])
        elements.append(header)
        
        # Search details table
        data = [
            ['Username Searched', self.search.username],
            ['Search Date', self.search.searched_at.strftime('%B %d, %Y at %H:%M:%S')],
            ['Case ID', str(self.search.case_id) if self.search.case_id else 'N/A'],
            ['Officer Name', self.search.officer_name or 'N/A'],
            ['Search Status', self.search.status.upper()],
            ['Cache Key', self.search.cache_key or 'N/A']
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_color),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, self.gray_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_summary(self) -> List:
        """Build results summary section"""
        elements = []
        
        # Section header
        header = Paragraph("Results Summary", self.styles['SectionHeader'])
        elements.append(header)
        
        # Summary statistics
        total_checked = self.search.platforms_checked or 0
        total_found = self.search.platforms_found or 0
        success_rate = (total_found / total_checked * 100) if total_checked > 0 else 0
        
        # High confidence results
        high_confidence = sum(1 for r in self.results if r.confidence_score >= 0.8)
        medium_confidence = sum(1 for r in self.results if 0.5 <= r.confidence_score < 0.8)
        low_confidence = sum(1 for r in self.results if r.confidence_score < 0.5)
        
        summary_data = [
            ['Platforms Checked', str(total_checked)],
            ['Platforms Found', f'{total_found} ({success_rate:.1f}%)'],
            ['High Confidence', f'{high_confidence} (≥80%)'],
            ['Medium Confidence', f'{medium_confidence} (50-79%)'],
            ['Low Confidence', f'{low_confidence} (<50%)']
        ]
        
        table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_color),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, self.gray_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_platform_results(self) -> List:
        """Build detailed platform results"""
        elements = []
        
        # Section header
        header = Paragraph("Detected Platforms", self.styles['SectionHeader'])
        elements.append(header)
        
        if not self.results:
            elements.append(Paragraph(
                "No platforms detected for this username.",
                self.styles['Normal']
            ))
            return elements
        
        # Platform results table
        table_data = [['#', 'Platform', 'Confidence', 'Profile URL', 'Discovered']]
        
        for idx, result in enumerate(self.results, 1):
            # Confidence badge color
            if result.confidence_score >= 0.8:
                conf_color = self.success_color
                conf_text = f"{result.confidence_score*100:.0f}% ✓"
            elif result.confidence_score >= 0.5:
                conf_color = self.warning_color
                conf_text = f"{result.confidence_score*100:.0f}% ~"
            else:
                conf_color = self.danger_color
                conf_text = f"{result.confidence_score*100:.0f}% ?"
            
            # Format URL for display
            url = result.platform_url or "N/A"
            if len(url) > 40:
                display_url = url[:37] + "..."
            else:
                display_url = url
            
            # Format discovery date
            discovered = result.discovered_at.strftime('%Y-%m-%d %H:%M') if result.discovered_at else 'N/A'
            
            table_data.append([
                str(idx),
                result.platform_name,
                conf_text,
                display_url,
                discovered
            ])
        
        # Create table
        table = Table(table_data, colWidths=[0.4*inch, 1.5*inch, 1*inch, 2.3*inch, 1.3*inch])
        
        # Base style
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, self.gray_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        
        # Alternate row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb')))
        
        # Color code confidence scores
        for idx, result in enumerate(self.results, 1):
            if result.confidence_score >= 0.8:
                conf_color = colors.HexColor('#d1fae5')
            elif result.confidence_score >= 0.5:
                conf_color = colors.HexColor('#fed7aa')
            else:
                conf_color = colors.HexColor('#fecaca')
            
            table_style.append(('BACKGROUND', (2, idx), (2, idx), conf_color))
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        
        # Add note about URLs
        elements.append(Spacer(1, 0.2*inch))
        note = Paragraph(
            "<i>Note: URLs are clickable in digital version. Confidence: ✓=High (≥80%), ~=Medium (50-79%), ?=Low (&lt;50%)</i>",
            self.styles['Normal']
        )
        elements.append(note)
        
        return elements
    
    def _build_disclaimer(self) -> List:
        """Build legal disclaimer section"""
        elements = []
        
        # Section header
        header = Paragraph("Legal Disclaimer", self.styles['SectionHeader'])
        elements.append(header)
        
        disclaimer_text = """
        <para alignment="justify">
        This report is generated for official law enforcement purposes only. The information 
        contained herein is based on publicly available data and automated platform checks. 
        While reasonable efforts have been made to ensure accuracy, this report should not 
        be solely relied upon for critical decisions.
        <br/><br/>
        <b>Important Considerations:</b>
        </para>
        """
        elements.append(Paragraph(disclaimer_text, self.styles['Normal']))
        
        disclaimer_points = [
            "Username presence does not confirm identity - verification required",
            "Confidence scores are algorithmic estimates, not guarantees",
            "Some platforms may have privacy restrictions or rate limiting",
            "Results are cached for 7 days - platforms may change",
            "This report must be handled in accordance with data protection laws",
            "Chain of custody must be maintained for evidentiary use"
        ]
        
        for point in disclaimer_points:
            elements.append(Paragraph(f"• {point}", self.styles['Normal']))
        
        return elements
    
    def _build_footer(self) -> List:
        """Build report footer with QR code"""
        elements = []
        
        # Generate QR code for report verification
        qr_data = f"USERNAME_REPORT:{self.search_id}:{datetime.now().isoformat()}"
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Convert QR code to image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Create footer table with QR code and metadata
        footer_data = [[
            Paragraph(
                f"""
                <para align=left fontSize=8>
                <b>Report Verification</b><br/>
                Scan QR code to verify authenticity<br/>
                Report ID: USR-{self.search_id:06d}<br/>
                Generated by OSINT Platform
                </para>
                """,
                self.styles['Footer']
            ),
            Image(buffer, width=0.8*inch, height=0.8*inch)
        ]]
        
        footer_table = Table(footer_data, colWidths=[5*inch, 1*inch])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        elements.append(footer_table)
        
        return elements


def generate_username_report(search_id: int, db: Session, output_path: Optional[str] = None) -> str:
    """
    Convenience function to generate username search report
    
    Args:
        search_id: ID of the username search
        db: Database session
        output_path: Optional custom output path
        
    Returns:
        Path to generated PDF file
    """
    generator = UsernameReportGenerator(search_id, db, output_path)
    return generator.generate()
