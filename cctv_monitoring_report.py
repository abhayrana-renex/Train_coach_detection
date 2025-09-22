#!/usr/bin/env python3
"""
CCTV Railway Station Monitoring Report Generator
Generates reports specifically for CCTV monitoring requirements.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class CCTVMonitoringReport:
    """Generates CCTV-specific monitoring reports for railway stations."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for CCTV reports."""
        if not REPORTLAB_AVAILABLE:
            return
        
        # CCTV Header style
        self.styles.add(ParagraphStyle(
            name='CCTVHeader',
            parent=self.styles['Title'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkred,
            backColor=colors.lightgrey
        ))
        
        # CCTV Subheader style
        self.styles.add(ParagraphStyle(
            name='CCTVSubheader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=colors.darkblue
        ))
    
    def generate_cctv_report(self, processed_dir: str) -> str:
        """
        Generate CCTV monitoring report from processed video data.
        
        Args:
            processed_dir: Directory containing processed video data
            
        Returns:
            Path to generated CCTV report
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_text_report(processed_dir)
        
        # Collect CCTV data
        cctv_data = self._collect_cctv_data(processed_dir)
        
        # Generate PDF report
        report_path = Path(processed_dir) / "CCTV_Monitoring_Report.pdf"
        doc = SimpleDocTemplate(str(report_path), pagesize=A4)
        story = []
        
        # Cover page
        story.extend(self._create_cctv_cover_page(cctv_data))
        story.append(PageBreak())
        
        # CCTV Summary
        story.extend(self._create_cctv_summary(cctv_data))
        story.append(PageBreak())
        
        # Per-train CCTV analysis
        for train_data in cctv_data['trains']:
            story.extend(self._create_train_cctv_analysis(train_data))
            story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        return str(report_path)
    
    def _collect_cctv_data(self, processed_dir: str) -> Dict[str, Any]:
        """Collect CCTV monitoring data from processed results."""
        processed_path = Path(processed_dir)
        cctv_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_trains': 0,
            'total_coaches': 0,
            'total_doors_open': 0,
            'total_doors_closed': 0,
            'trains': []
        }
        
        # Find all train folders
        train_folders = [f for f in processed_path.iterdir() if f.is_dir() and '_' in f.name]
        
        for train_folder in train_folders:
            train_number = train_folder.name.split('_')[0]
            coach_number = train_folder.name.split('_')[1]
            
            # Load component data
            component_file = train_folder / f"{train_number}_{coach_number}_components.json"
            if component_file.exists():
                with open(component_file, 'r') as f:
                    component_data = json.load(f)
                
                # Add to train data
                train_data = {
                    'train_number': train_number,
                    'coach_number': int(coach_number),
                    'doors_open': component_data.get('doors_open', 0),
                    'doors_closed': component_data.get('doors_closed', 0),
                    'engines': len(component_data.get('engines', [])),
                    'wagons': len(component_data.get('wagons', []))
                }
                
                cctv_data['trains'].append(train_data)
                cctv_data['total_doors_open'] += train_data['doors_open']
                cctv_data['total_doors_closed'] += train_data['doors_closed']
        
        # Group by train
        train_groups = {}
        for train_data in cctv_data['trains']:
            train_num = train_data['train_number']
            if train_num not in train_groups:
                train_groups[train_num] = []
            train_groups[train_num].append(train_data)
        
        cctv_data['train_groups'] = train_groups
        cctv_data['total_trains'] = len(train_groups)
        cctv_data['total_coaches'] = len(cctv_data['trains'])
        
        return cctv_data
    
    def _create_cctv_cover_page(self, cctv_data: Dict[str, Any]) -> List:
        """Create CCTV cover page."""
        story = []
        
        # CCTV Header
        header = Paragraph("CCTV RAILWAY STATION MONITORING REPORT", self.styles['CCTVHeader'])
        story.append(header)
        story.append(Spacer(1, 20))
        
        # Timestamp
        timestamp = Paragraph(f"Generated: {cctv_data['timestamp']}", self.styles['Normal'])
        story.append(timestamp)
        story.append(Spacer(1, 30))
        
        # CCTV Summary Table
        summary_data = [
            ['CCTV Monitoring Metric', 'Count'],
            ['Total Trains Monitored', str(cctv_data['total_trains'])],
            ['Total Coaches Analyzed', str(cctv_data['total_coaches'])],
            ['Total Doors Open', str(cctv_data['total_doors_open'])],
            ['Total Doors Closed', str(cctv_data['total_doors_closed'])],
            ['Open Door Percentage', f"{(cctv_data['total_doors_open'] / max(1, cctv_data['total_doors_open'] + cctv_data['total_doors_closed']) * 100):.1f}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        return story
    
    def _create_cctv_summary(self, cctv_data: Dict[str, Any]) -> List:
        """Create CCTV summary section."""
        story = []
        
        # Section header
        header = Paragraph("CCTV MONITORING SUMMARY", self.styles['CCTVSubheader'])
        story.append(header)
        
        # Per-train summary table
        train_summary_data = [['Train Number', 'Coaches', 'Doors Open', 'Doors Closed', 'Open %']]
        
        for train_num, train_group in cctv_data['train_groups'].items():
            total_doors_open = sum(t['doors_open'] for t in train_group)
            total_doors_closed = sum(t['doors_closed'] for t in train_group)
            total_doors = total_doors_open + total_doors_closed
            open_percentage = (total_doors_open / max(1, total_doors) * 100) if total_doors > 0 else 0
            
            train_summary_data.append([
                train_num,
                str(len(train_group)),
                str(total_doors_open),
                str(total_doors_closed),
                f"{open_percentage:.1f}%"
            ])
        
        train_table = Table(train_summary_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1.5*inch, 1*inch])
        train_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(train_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_train_cctv_analysis(self, train_data: Dict[str, Any]) -> List:
        """Create detailed CCTV analysis for a train."""
        story = []
        
        # Train header
        header = Paragraph(f"TRAIN {train_data['train_number']} - CCTV ANALYSIS", self.styles['CCTVSubheader'])
        story.append(header)
        
        # Coach-by-coach analysis
        coach_data = [['Coach #', 'Doors Open', 'Doors Closed', 'Status']]
        
        for coach in train_data.get('coaches', []):
            coach_num = coach.get('coach_number', 'Unknown')
            doors_open = coach.get('doors_open', 0)
            doors_closed = coach.get('doors_closed', 0)
            
            # Determine status based on your requirements
            if doors_open > 0:
                status = "DOORS OPEN - ATTENTION REQUIRED"
            else:
                status = "ALL DOORS CLOSED - NORMAL"
            
            coach_data.append([
                str(coach_num),
                str(doors_open),
                str(doors_closed),
                status
            ])
        
        coach_table = Table(coach_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 2.5*inch])
        coach_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(coach_table)
        return story
    
    def _generate_text_report(self, processed_dir: str) -> str:
        """Generate text-based CCTV report."""
        cctv_data = self._collect_cctv_data(processed_dir)
        report_path = Path(processed_dir) / "CCTV_Monitoring_Report.txt"
        
        with open(report_path, 'w') as f:
            f.write("CCTV RAILWAY STATION MONITORING REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {cctv_data['timestamp']}\n\n")
            
            # Summary
            f.write("CCTV MONITORING SUMMARY\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total Trains Monitored: {cctv_data['total_trains']}\n")
            f.write(f"Total Coaches Analyzed: {cctv_data['total_coaches']}\n")
            f.write(f"Total Doors Open: {cctv_data['total_doors_open']}\n")
            f.write(f"Total Doors Closed: {cctv_data['total_doors_closed']}\n\n")
            
            # Per-train analysis
            for train_num, train_group in cctv_data['train_groups'].items():
                f.write(f"TRAIN {train_num} ANALYSIS\n")
                f.write("-" * 20 + "\n")
                
                total_doors_open = sum(t['doors_open'] for t in train_group)
                total_doors_closed = sum(t['doors_closed'] for t in train_group)
                
                f.write(f"Coaches: {len(train_group)}\n")
                f.write(f"Doors Open: {total_doors_open}\n")
                f.write(f"Doors Closed: {total_doors_closed}\n")
                
                if total_doors_open > 0:
                    f.write("STATUS: ATTENTION REQUIRED - DOORS OPEN\n")
                else:
                    f.write("STATUS: NORMAL - ALL DOORS CLOSED\n")
                f.write("\n")
        
        return str(report_path)

def main():
    """Generate CCTV monitoring report."""
    processed_dir = "Processed_Video"
    
    if not os.path.exists(processed_dir):
        print(f"❌ Processed directory '{processed_dir}' not found!")
        return
    
    print("📹 Generating CCTV Railway Station Monitoring Report...")
    
    reporter = CCTVMonitoringReport()
    report_path = reporter.generate_cctv_report(processed_dir)
    
    print(f"✅ CCTV Report generated: {report_path}")

if __name__ == "__main__":
    main()
