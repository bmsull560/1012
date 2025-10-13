// Export Service for generating PDF, PowerPoint, and Excel files
// Uses browser-based libraries for client-side generation

import { ValueModelData } from '@/components/value-model/ValueModelReport';

interface ExportOptions {
  format: 'pdf' | 'ppt' | 'excel';
  data: ValueModelData;
  filename?: string;
}

class ExportService {
  // Generate PDF Report
  async exportToPDF(data: ValueModelData, filename?: string): Promise<void> {
    // In production, use libraries like jsPDF or react-pdf
    // For now, we'll use browser print functionality
    
    const printContent = this.generateHTMLReport(data);
    const printWindow = window.open('', '_blank');
    
    if (!printWindow) {
      alert('Please allow pop-ups to export PDF');
      return;
    }
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${data.company.name} Value Model</title>
          <style>
            @media print {
              @page { margin: 1cm; size: letter; }
            }
            body { 
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
              line-height: 1.6;
              color: #333;
              max-width: 800px;
              margin: 0 auto;
              padding: 20px;
            }
            .header {
              border-bottom: 3px solid #2563eb;
              padding-bottom: 20px;
              margin-bottom: 30px;
            }
            h1 { 
              color: #1e40af;
              margin: 0 0 10px 0;
            }
            .subtitle {
              color: #64748b;
              font-size: 14px;
            }
            .kpi-grid {
              display: grid;
              grid-template-columns: repeat(4, 1fr);
              gap: 15px;
              margin: 30px 0;
            }
            .kpi-card {
              background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
              color: white;
              padding: 20px;
              border-radius: 8px;
            }
            .kpi-title {
              font-size: 12px;
              opacity: 0.9;
              margin-bottom: 5px;
            }
            .kpi-value {
              font-size: 24px;
              font-weight: bold;
            }
            .kpi-subtitle {
              font-size: 11px;
              opacity: 0.8;
              margin-top: 5px;
            }
            .section {
              margin: 30px 0;
            }
            .section-title {
              font-size: 18px;
              font-weight: 600;
              color: #1e40af;
              margin-bottom: 15px;
              padding-bottom: 5px;
              border-bottom: 1px solid #e5e7eb;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 15px 0;
            }
            th, td {
              text-align: left;
              padding: 10px;
              border-bottom: 1px solid #e5e7eb;
            }
            th {
              background: #f8fafc;
              font-weight: 600;
            }
            .metric-row {
              display: flex;
              justify-content: space-between;
              padding: 8px 0;
              border-bottom: 1px solid #f1f5f9;
            }
            .footer {
              margin-top: 40px;
              padding-top: 20px;
              border-top: 1px solid #e5e7eb;
              font-size: 12px;
              color: #64748b;
            }
            @media print {
              .kpi-card { 
                break-inside: avoid;
                background: #f0f9ff !important;
                color: #1e40af !important;
                border: 1px solid #2563eb;
              }
            }
          </style>
        </head>
        <body>
          ${printContent}
        </body>
      </html>
    `);
    
    printWindow.document.close();
    
    // Wait for content to render then trigger print
    setTimeout(() => {
      printWindow.print();
      // printWindow.close(); // Uncomment if you want to auto-close
    }, 500);
  }
  
  // Generate PowerPoint Presentation
  async exportToPowerPoint(data: ValueModelData, filename?: string): Promise<void> {
    // In production, use a library like PptxGenJS
    // For MVP, we'll generate a structured text format that can be copied to PowerPoint
    
    const pptContent = this.generatePowerPointContent(data);
    const blob = new Blob([pptContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `${data.company.name.replace(/\s+/g, '_')}_Value_Model.txt`;
    link.click();
    URL.revokeObjectURL(url);
    
    alert('PowerPoint outline generated! Copy the content into PowerPoint or use it as speaker notes.');
  }
  
  // Generate Excel Workbook
  async exportToExcel(data: ValueModelData, filename?: string): Promise<void> {
    // Generate CSV format that Excel can open
    const csvContent = this.generateExcelContent(data);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `${data.company.name.replace(/\s+/g, '_')}_Value_Model.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }
  
  // Generate HTML content for PDF
  private generateHTMLReport(data: ValueModelData): string {
    const formatCurrency = (value: number) => {
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      } else if (value >= 1000) {
        return `$${(value / 1000).toFixed(0)}K`;
      }
      return `$${value.toFixed(0)}`;
    };
    
    const formatPercent = (value: number) => `${(value * 100).toFixed(0)}%`;
    
    return `
      <div class="header">
        <h1>${data.company.name} Value Model</h1>
        <div class="subtitle">${data.company.industry} • ${data.company.analysisType}</div>
        <div class="subtitle">Generated: ${new Date().toLocaleDateString()}</div>
      </div>
      
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-title">Total Benefits (Y1)</div>
          <div class="kpi-value">${formatCurrency(data.keyMetrics.totalBenefitsY1)}</div>
          <div class="kpi-subtitle">Revenue + Cost Savings</div>
        </div>
        <div class="kpi-card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
          <div class="kpi-title">Net Benefit (Y1)</div>
          <div class="kpi-value">${formatCurrency(data.keyMetrics.netBenefitY1)}</div>
          <div class="kpi-subtitle">After ${formatPercent(data.keyMetrics.adoptionRamp)} Ramp</div>
        </div>
        <div class="kpi-card" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
          <div class="kpi-title">3-Year NPV</div>
          <div class="kpi-value">${formatCurrency(data.keyMetrics.npv3Year)}</div>
          <div class="kpi-subtitle">at ${formatPercent(data.financialDetails.discountRate)} Discount</div>
        </div>
        <div class="kpi-card" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);">
          <div class="kpi-title">Payback</div>
          <div class="kpi-value">${data.keyMetrics.paybackMonths.toFixed(1)} Mo</div>
          <div class="kpi-subtitle">Fast Recovery</div>
        </div>
      </div>
      
      <div class="section">
        <h2 class="section-title">Executive Summary</h2>
        <table>
          <tr>
            <td><strong>ROI (Year 1)</strong></td>
            <td>${formatPercent(data.executiveSummary.roiYear1 / 100)}</td>
          </tr>
          <tr>
            <td><strong>Payback Period</strong></td>
            <td>${data.executiveSummary.paybackPeriod.toFixed(1)} months</td>
          </tr>
          <tr>
            <td><strong>3-Year ROI</strong></td>
            <td>${formatPercent(data.executiveSummary.roi3Year / 100)}</td>
          </tr>
          <tr>
            <td><strong>Recommendation</strong></td>
            <td>${data.executiveSummary.keyRecommendation}</td>
          </tr>
        </table>
      </div>
      
      <div class="section">
        <h2 class="section-title">Value Drivers</h2>
        ${data.valueDrivers.map(driver => `
          <div class="metric-row">
            <span>${driver.name}</span>
            <strong>${formatCurrency(driver.value)}</strong>
          </div>
        `).join('')}
      </div>
      
      <div class="section">
        <h2 class="section-title">Financial Overview</h2>
        <table>
          <tr>
            <td>Total Benefits (Year 1)</td>
            <td style="text-align: right;"><strong>${formatCurrency(data.financialDetails.totalBenefitsY1)}</strong></td>
          </tr>
          <tr>
            <td>Total Costs (Year 1)</td>
            <td style="text-align: right;"><strong>${formatCurrency(data.financialDetails.totalCostsY1)}</strong></td>
          </tr>
          <tr style="background: #f0f9ff;">
            <td><strong>Net Benefit (Year 1 Realized)</strong></td>
            <td style="text-align: right;"><strong>${formatCurrency(data.financialDetails.netBenefitRealized)}</strong></td>
          </tr>
          <tr>
            <td>Net Benefit (Steady State)</td>
            <td style="text-align: right;"><strong>${formatCurrency(data.financialDetails.netBenefitSteadyState)}</strong></td>
          </tr>
          <tr style="background: #eff6ff;">
            <td><strong>3-Year NPV</strong></td>
            <td style="text-align: right;"><strong>${formatCurrency(data.financialDetails.npv3Year)}</strong></td>
          </tr>
        </table>
      </div>
      
      ${data.implementationNotes ? `
        <div class="section">
          <h2 class="section-title">Implementation Notes</h2>
          <ul>
            ${data.implementationNotes.map(note => `<li>${note}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      
      <div class="footer">
        <p>This value model was generated by ValueVerse AI. All calculations are based on industry benchmarks and provided inputs.</p>
        <p>Confidential - ${data.company.name}</p>
      </div>
    `;
  }
  
  // Generate PowerPoint content
  private generatePowerPointContent(data: ValueModelData): string {
    const formatCurrency = (value: number) => {
      if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
      else if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
      return `$${value.toFixed(0)}`;
    };
    
    const formatPercent = (value: number) => `${(value * 100).toFixed(0)}%`;
    
    return `
POWERPOINT PRESENTATION OUTLINE
${data.company.name} Value Model
${new Date().toLocaleDateString()}

=====================================
SLIDE 1: Title Slide
=====================================
${data.company.name} Value Model
${data.company.industry}
Prepared by: [Your Name]
Date: ${new Date().toLocaleDateString()}

=====================================
SLIDE 2: Executive Summary
=====================================
KEY METRICS:
• Total Benefits (Year 1): ${formatCurrency(data.keyMetrics.totalBenefitsY1)}
• Net Benefit (Year 1): ${formatCurrency(data.keyMetrics.netBenefitY1)}
• 3-Year NPV: ${formatCurrency(data.keyMetrics.npv3Year)}
• Payback Period: ${data.keyMetrics.paybackMonths.toFixed(1)} months
• ROI (Year 1): ${formatPercent(data.executiveSummary.roiYear1 / 100)}

RECOMMENDATION:
${data.executiveSummary.keyRecommendation}

=====================================
SLIDE 3: Value Drivers - Revenue
=====================================
REVENUE GROWTH OPPORTUNITIES:
${data.valueDrivers
  .filter(d => d.category === 'revenue')
  .map(d => `• ${d.name}: ${formatCurrency(d.value)} (${formatPercent(d.percentOfTotal)} of total)`)
  .join('\n')}

Total Revenue Impact: ${formatCurrency(
  data.valueDrivers.filter(d => d.category === 'revenue').reduce((sum, d) => sum + d.value, 0)
)}

=====================================
SLIDE 4: Value Drivers - Cost Savings
=====================================
OPERATIONAL EFFICIENCY GAINS:
${data.valueDrivers
  .filter(d => d.category === 'cost')
  .map(d => `• ${d.name}: ${formatCurrency(d.value)} (${formatPercent(d.percentOfTotal)} of total)`)
  .join('\n')}

Total Cost Savings: ${formatCurrency(
  data.valueDrivers.filter(d => d.category === 'cost').reduce((sum, d) => sum + d.value, 0)
)}

=====================================
SLIDE 5: Financial Analysis
=====================================
YEAR 1 ANALYSIS:
• Total Benefits: ${formatCurrency(data.financialDetails.totalBenefitsY1)}
• Total Investment: ${formatCurrency(data.financialDetails.totalCostsY1)}
• Net Benefit (Realized): ${formatCurrency(data.financialDetails.netBenefitRealized)}
• Adoption Ramp: ${formatPercent(data.keyMetrics.adoptionRamp)}

STEADY STATE (YEARS 2-3):
• Annual Net Benefit: ${formatCurrency(data.financialDetails.netBenefitSteadyState)}

3-YEAR OUTLOOK:
• NPV @ ${formatPercent(data.financialDetails.discountRate)}: ${formatCurrency(data.financialDetails.npv3Year)}
• Total ROI: ${formatPercent(data.executiveSummary.roi3Year / 100)}

=====================================
SLIDE 6: Key Assumptions
=====================================
COMMERCIAL FOOTPRINT:
• Sales Reps: ${data.assumptions.salesReps}
• Rep Adoption Rate: ${formatPercent(data.assumptions.adoptionRate)}

MARKET METRICS:
• ASP per Case: ${formatCurrency(data.assumptions.aspPerCase)}
• Gross Margin: ${formatPercent(data.assumptions.grossMargin)}
• Annual Procedures: ${data.assumptions.annualProcedures.toLocaleString()}

CRITICAL SUCCESS FACTOR:
${data.assumptions.criticalFactor}

=====================================
SLIDE 7: Implementation Roadmap
=====================================
KEY SUCCESS FACTORS:
${data.keySuccessFactors?.map(factor => `• ${factor}`).join('\n') || '• Focus on rapid adoption\n• Track value metrics from day one\n• Maintain executive alignment'}

NEXT STEPS:
${data.implementationNotes?.slice(0, 3).map(note => `• ${note}`).join('\n') || '• Finalize contract terms\n• Identify pilot users\n• Establish success metrics'}

=====================================
SLIDE 8: Questions & Discussion
=====================================
CONTACT:
[Your Name]
[Your Email]
[Your Phone]

APPENDIX AVAILABLE:
• Detailed calculations
• Sensitivity analysis
• Industry benchmarks
• Risk assessment
    `;
  }
  
  // Generate Excel CSV content
  private generateExcelContent(data: ValueModelData): string {
    const rows: string[][] = [];
    
    // Header
    rows.push(['Value Model Report', data.company.name]);
    rows.push(['Generated', new Date().toLocaleDateString()]);
    rows.push([]);
    
    // Key Metrics
    rows.push(['KEY METRICS']);
    rows.push(['Metric', 'Value', 'Notes']);
    rows.push(['Total Benefits (Y1)', data.keyMetrics.totalBenefitsY1.toString(), 'Revenue + Cost Savings']);
    rows.push(['Net Benefit (Y1)', data.keyMetrics.netBenefitY1.toString(), `After ${(data.keyMetrics.adoptionRamp * 100).toFixed(0)}% adoption ramp`]);
    rows.push(['3-Year NPV', data.keyMetrics.npv3Year.toString(), `at ${(data.financialDetails.discountRate * 100).toFixed(0)}% discount rate`]);
    rows.push(['Payback (months)', data.keyMetrics.paybackMonths.toFixed(1), 'Fast recovery']);
    rows.push([]);
    
    // Executive Summary
    rows.push(['EXECUTIVE SUMMARY']);
    rows.push(['ROI Year 1', `${(data.executiveSummary.roiYear1).toFixed(0)}%`]);
    rows.push(['Payback Period', `${data.executiveSummary.paybackPeriod.toFixed(1)} months`]);
    rows.push(['3-Year ROI', `${(data.executiveSummary.roi3Year).toFixed(0)}%`]);
    rows.push([]);
    
    // Value Drivers
    rows.push(['VALUE DRIVERS']);
    rows.push(['Driver', 'Category', 'Value', 'Percent of Total', 'Confidence']);
    data.valueDrivers.forEach(driver => {
      rows.push([
        driver.name,
        driver.category,
        driver.value.toString(),
        `${(driver.percentOfTotal * 100).toFixed(1)}%`,
        `${(driver.confidence * 100).toFixed(0)}%`
      ]);
    });
    rows.push([]);
    
    // Financial Details
    rows.push(['FINANCIAL OVERVIEW']);
    rows.push(['Item', 'Amount']);
    rows.push(['Total Benefits Y1', data.financialDetails.totalBenefitsY1.toString()]);
    rows.push(['Total Costs Y1', data.financialDetails.totalCostsY1.toString()]);
    rows.push(['Net Benefit Realized', data.financialDetails.netBenefitRealized.toString()]);
    rows.push(['Net Benefit Steady State', data.financialDetails.netBenefitSteadyState.toString()]);
    rows.push(['3-Year NPV', data.financialDetails.npv3Year.toString()]);
    rows.push(['Discount Rate', `${(data.financialDetails.discountRate * 100).toFixed(0)}%`]);
    rows.push([]);
    
    // Assumptions
    rows.push(['KEY ASSUMPTIONS']);
    rows.push(['Parameter', 'Value']);
    rows.push(['Sales Reps', data.assumptions.salesReps.toString()]);
    rows.push(['ASP per Case', data.assumptions.aspPerCase.toString()]);
    rows.push(['Gross Margin', `${(data.assumptions.grossMargin * 100).toFixed(0)}%`]);
    rows.push(['Annual Procedures', data.assumptions.annualProcedures.toString()]);
    rows.push(['Adoption Rate', `${(data.assumptions.adoptionRate * 100).toFixed(0)}%`]);
    rows.push([]);
    
    // Scenarios
    rows.push(['SCENARIO ANALYSIS']);
    rows.push(['Scenario', '3-Year NPV']);
    rows.push(['Conservative', data.scenarios.conservative.toString()]);
    rows.push(['Base', data.scenarios.base.toString()]);
    rows.push(['Optimistic', data.scenarios.optimistic.toString()]);
    
    // Convert to CSV
    return rows.map(row => row.map(cell => {
      // Escape cells containing commas or quotes
      const cellStr = cell.toString();
      if (cellStr.includes(',') || cellStr.includes('"')) {
        return `"${cellStr.replace(/"/g, '""')}"`;
      }
      return cellStr;
    }).join(',')).join('\n');
  }
}

export const exportService = new ExportService();
