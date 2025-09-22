"""
Report generation utilities for creating PDF reports.
"""

import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. PDF reports will not be generated.")

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates PDF reports for train video processing results."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for the report."""
        if not REPORTLAB_AVAILABLE:
            return
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkgreen
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
    
    def generate_master_report(self, all_results: Dict[str, Any], output_dir: Path) -> str:
        """
        Generate master report for all processed videos.
        
        Args:
            all_results: Results from all processed videos
            output_dir: Output directory
            
        Returns:
            Path to generated report
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. Cannot generate PDF report.")
            return ""
        
        report_path = output_dir / "Final_Report.pdf"
        
        doc = SimpleDocTemplate(str(report_path), pagesize=A4)
        story = []
        
        # Cover page
        story.extend(self._create_cover_page(all_results))
        story.append(PageBreak())
        
        # Summary section
        story.extend(self._create_summary_section(all_results))
        story.append(PageBreak())
        
        # Per-train sections
        for train_number, train_data in all_results.items():
            story.extend(self._create_train_section(train_number, train_data))
            story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        logger.info(f"Generated master report: {report_path}")
        return str(report_path)
    
    def _create_cover_page(self, all_results: Dict[str, Any]) -> List:
        """Create cover page content."""
        story = []
        
        # Title
        title = Paragraph("Train Video Processing Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Processing date
        date_str = datetime.now().strftime("%B %d, %Y")
        date_para = Paragraph(f"Generated on: {date_str}", self.styles['CustomSubtitle'])
        story.append(date_para)
        story.append(Spacer(1, 30))
        
        # Summary statistics
        total_trains = len(all_results)
        total_coaches = sum(len(data.get('coaches', [])) for data in all_results.values())
        total_engines = sum(data.get('total_engines', 0) for data in all_results.values())
        total_wagons = sum(data.get('total_wagons', 0) for data in all_results.values())
        
        summary_data = [
            ['Metric', 'Count'],
            ['Total Trains Processed', str(total_trains)],
            ['Total Coaches', str(total_coaches)],
            ['Total Engines', str(total_engines)],
            ['Total Wagons', str(total_wagons)]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        
        return story
    
    def _create_summary_section(self, all_results: Dict[str, Any]) -> List:
        """Create summary section."""
        story = []
        
        # Section header
        header = Paragraph("Processing Summary", self.styles['SectionHeader'])
        story.append(header)
        
        # Create summary table
        summary_data = [['Train Number', 'Total Coaches', 'Engines', 'Wagons', 'Doors Open', 'Doors Closed']]
        
        for train_number, train_data in all_results.items():
            coaches = train_data.get('coaches', [])
            total_doors_open = sum(coach.get('doors_open', 0) for coach in coaches)
            total_doors_closed = sum(coach.get('doors_closed', 0) for coach in coaches)
            
            summary_data.append([
                train_number,
                str(len(coaches)),
                str(sum(1 for coach in coaches if coach.get('coach_type') == 'engine')),
                str(sum(1 for coach in coaches if coach.get('coach_type') == 'wagon')),
                str(total_doors_open),
                str(total_doors_closed)
            ])
        
        summary_table = Table(summary_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_train_section(self, train_number: str, train_data: Dict[str, Any]) -> List:
        """Create section for a specific train."""
        story = []
        
        # Train header
        header = Paragraph(f"Train {train_number} Analysis", self.styles['SectionHeader'])
        story.append(header)
        
        coaches = train_data.get('coaches', [])
        
        # Train summary
        summary_text = f"Total Coaches: {len(coaches)}"
        summary_para = Paragraph(summary_text, self.styles['Normal'])
        story.append(summary_para)
        story.append(Spacer(1, 12))
        
        # Per-coach details
        for coach in coaches:
            coach_number = coach.get('coach_number', 'Unknown')
            coach_type = coach.get('coach_type', 'Unknown')
            frame_count = coach.get('frame_count', 0)
            doors_open = coach.get('doors_open', 0)
            doors_closed = coach.get('doors_closed', 0)
            
            # Coach header
            coach_header = Paragraph(f"Coach {coach_number} ({coach_type})", self.styles['Heading3'])
            story.append(coach_header)
            
            # Coach details
            details_text = f"Frames extracted: {frame_count}, Doors open: {doors_open}, Doors closed: {doors_closed}"
            details_para = Paragraph(details_text, self.styles['Normal'])
            story.append(details_para)
            story.append(Spacer(1, 8))
        
        return story
    
    def generate_train_report(self, train_number: str, train_data: Dict[str, Any], 
                            output_dir: Path) -> str:
        """
        Generate report for a single train.
        
        Args:
            train_number: Train number
            train_data: Train processing data
            output_dir: Output directory
            
        Returns:
            Path to generated report
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. Cannot generate PDF report.")
            return ""
        
        report_path = output_dir / f"Train_{train_number}_Report.pdf"
        
        doc = SimpleDocTemplate(str(report_path), pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(f"Train {train_number} Processing Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Train details
        coaches = train_data.get('coaches', [])
        total_coaches = len(coaches)
        
        details_text = f"Total Coaches Processed: {total_coaches}"
        details_para = Paragraph(details_text, self.styles['CustomSubtitle'])
        story.append(details_para)
        story.append(Spacer(1, 20))
        
        # Coach table
        coach_data = [['Coach #', 'Type', 'Frames', 'Doors Open', 'Doors Closed']]
        
        for coach in coaches:
            coach_data.append([
                str(coach.get('coach_number', 'Unknown')),
                coach.get('coach_type', 'Unknown'),
                str(coach.get('frame_count', 0)),
                str(coach.get('doors_open', 0)),
                str(coach.get('doors_closed', 0))
            ])
        
        coach_table = Table(coach_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
        coach_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(coach_table)
        
        # Build PDF
        doc.build(story)
        logger.info(f"Generated train report: {report_path}")
        return str(report_path)
    
    def generate_simple_report(self, all_results: Dict[str, Any], output_dir: Path) -> str:
        """
        Generate a simple text report if ReportLab is not available.
        
        Args:
            all_results: Processing results
            output_dir: Output directory
            
        Returns:
            Path to generated report
        """
        report_path = output_dir / "Final_Report.txt"
        
        with open(report_path, 'w') as f:
            f.write("TRAIN VIDEO PROCESSING REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            total_trains = len(all_results)
            total_coaches = sum(len(data.get('coaches', [])) for data in all_results.values())
            
            f.write("SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Trains Processed: {total_trains}\n")
            f.write(f"Total Coaches: {total_coaches}\n\n")
            
            # Per-train details
            for train_number, train_data in all_results.items():
                f.write(f"TRAIN {train_number}\n")
                f.write("-" * 20 + "\n")
                
                coaches = train_data.get('coaches', [])
                f.write(f"Total Coaches: {len(coaches)}\n")
                
                for coach in coaches:
                    coach_number = coach.get('coach_number', 'Unknown')
                    coach_type = coach.get('coach_type', 'Unknown')
                    doors_open = coach.get('doors_open', 0)
                    doors_closed = coach.get('doors_closed', 0)
                    
                    f.write(f"  Coach {coach_number} ({coach_type}): ")
                    f.write(f"Open doors: {doors_open}, Closed doors: {doors_closed}\n")
                
                f.write("\n")
        
        logger.info(f"Generated simple report: {report_path}")
        return str(report_path)
