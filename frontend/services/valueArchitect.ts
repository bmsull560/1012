// Value Architect Agent Service
// This service handles the conversation flow for building value models

import { VALUE_DRIVERS, calculateTotalValue, generateScenarios, calculateNPV, calculatePayback, INDUSTRY_BENCHMARKS, calculateAdoptionFactor, ValueDriver } from '@/utils/valueDrivers';
import { companyResearch, CompanyData } from './companyResearch';
import { recommendValueDrivers, findMatchingPatterns, aggregateOrganizationalPatterns, VALUE_PATTERNS } from './valueDriverPatterns';
import { generateUniversalValueModel, matchUniversalPattern, UNIVERSAL_PATTERNS } from './universalValuePatterns';
import { valueModelsAPI, agentAPI, AgentMessage } from './api';

export type WorkflowStage = 
  | 'idle'
  | 'company_research' 
  | 'commercial_footprint'
  | 'driver_selection'
  | 'data_collection'
  | 'calculation'
  | 'refinement'
  | 'report_generation';

export interface CompanyInfo {
  name: string;
  industry: string;
  size: string;
  analysisType: string;
  website?: string;
  description?: string;
}

export interface ValueModelContext {
  stage: WorkflowStage;
  company?: CompanyInfo;
  selectedDrivers: string[];
  inputs: Map<string, number>;
  currentDriverIndex: number;
  currentInputIndex: number;
  calculations?: {
    totalBenefits: number;
    totalCosts: number;
    netBenefit: number;
    npv: number;
    payback: number;
    scenarios: {
      conservative: number;
      base: number;
      optimistic: number;
    };
    byDriver: Map<string, number>;
    byCategory: Map<string, number>;
  };
}

// Company database (in production, this would be an API call)
const COMPANY_DATABASE: { [key: string]: CompanyInfo } = {
  'anika therapeutics': {
    name: 'Anika Therapeutics',
    industry: 'Orthopedics - IDN/ASC Framework',
    size: '$2.8B Market Cap',
    analysisType: 'Joint Preservation Division',
    description: 'Leading provider of hyaluronic acid-based joint preservation therapies'
  },
  'rush university': {
    name: 'Rush University System for Health',
    industry: 'Healthcare - Integrated Delivery Network',
    size: '$2.8B Revenue',
    analysisType: 'Orthopedics Department',
    description: 'Academic medical center with strong orthopedics program'
  },
  'zimmer biomet': {
    name: 'Zimmer Biomet',
    industry: 'Medical Device - Orthopedics',
    size: '$7.8B Revenue',
    analysisType: 'Hip & Knee Implants',
    description: 'Global leader in musculoskeletal healthcare'
  }
};

export class ValueArchitectAgent {
  private context: ValueModelContext = {
    stage: 'idle',
    selectedDrivers: [],
    inputs: new Map(),
    currentDriverIndex: 0,
    currentInputIndex: 0
  };
  private modelId: string | null = null;
  private userId: string | null = null;
  private autoSaveTimer: NodeJS.Timeout | null = null;
  private agentMessageHandler: ((message: AgentMessage) => void) | null = null;

  // Process user message and return agent response
  async processMessage(message: string): Promise<{
    response: string;
    stage: WorkflowStage;
    progress: number;
    context: ValueModelContext;
    showReport?: boolean;
  }> {
    const lowerMessage = message.toLowerCase();
    
    // Send message to backend agent if connected
    if (this.userId) {
      agentAPI.sendMessage('value_architect', message, {
        stage: this.context.stage,
        company: this.context.company,
        selectedDrivers: this.context.selectedDrivers,
        inputs: Object.fromEntries(this.context.inputs)
      });
    }

    // Check for value model initiation
    if (lowerMessage.includes('build') && lowerMessage.includes('value model')) {
      return this.initiateValueModel(message);
    }

    // Route based on current stage
    switch (this.context.stage) {
      case 'company_research':
        return this.handleCompanyResearch(message);
      case 'commercial_footprint':
        return this.handleCommercialFootprint(message);
      case 'driver_selection':
        return this.handleDriverSelection(message);
      case 'data_collection':
        return this.handleDataCollection(message);
      case 'calculation':
        return this.handleCalculation(message);
      case 'refinement':
        return this.handleRefinement(message);
      default:
        return this.handleDefault(message);
    }
  }

  private async initiateValueModel(message: string): Promise<any> {
    // Extract company name or website from message
    const companyMatch = message.match(/for\s+([^\.]+)/i);
    const companyName = companyMatch ? companyMatch[1].trim() : '';
    
    // Check if they're describing a solution type (CI/CD, farming drone, etc.)
    const lowerMessage = message.toLowerCase();
    let industryContext = '';
    let solutionType = '';
    
    // Detect industry/solution patterns
    if (lowerMessage.includes('ci/cd') || lowerMessage.includes('cicd') || lowerMessage.includes('devops')) {
      industryContext = 'DevOps/Software';
      solutionType = 'CI/CD Platform';
    } else if (lowerMessage.includes('farming') || lowerMessage.includes('agriculture') || lowerMessage.includes('drone')) {
      industryContext = 'Agriculture/AgTech';
      solutionType = 'Farming Automation';
    } else if (lowerMessage.includes('construction') || lowerMessage.includes('building')) {
      industryContext = 'Construction';
      solutionType = 'Project Management';
    } else if (lowerMessage.includes('fintech') || lowerMessage.includes('banking')) {
      industryContext = 'Financial Services';
      solutionType = 'Financial Technology';
    } else if (lowerMessage.includes('logistics') || lowerMessage.includes('supply chain')) {
      industryContext = 'Logistics/Supply Chain';
      solutionType = 'Supply Chain Optimization';
    } else if (lowerMessage.includes('retail') || lowerMessage.includes('ecommerce')) {
      industryContext = 'Retail/E-commerce';
      solutionType = 'Commerce Platform';
    } else if (lowerMessage.includes('manufacturing') || lowerMessage.includes('factory')) {
      industryContext = 'Manufacturing';
      solutionType = 'Manufacturing Optimization';
    }
    
    // Check if it's a website
    const isWebsite = companyName.includes('.com') || companyName.includes('.org') || 
                      companyName.includes('.edu') || companyName.includes('http');
    
    let companyData: CompanyData;
    
    if (isWebsite) {
      // Normalize URL
      const url = companyName.startsWith('http') ? companyName : `https://${companyName}`;
      const scraped = await companyResearch.scrapeWebsite(url);
      companyData = await companyResearch.enrichCompanyData(scraped.name || companyName, url);
    } else {
      // Search for company
      companyData = await companyResearch.enrichCompanyData(companyName);
    }
    
    // Analyze for value model using patterns
    const analysis = await companyResearch.analyzeForValueModel(companyData);
    
    // Determine if we should use universal patterns (non-healthcare) or healthcare patterns
    let valueModelData: any;
    
    if (industryContext && !companyData.industry.toLowerCase().includes('health')) {
      // Use universal patterns for non-healthcare industries
      const problemDescription = `Improving operational efficiency and ${solutionType.toLowerCase()} capabilities`;
      
      valueModelData = generateUniversalValueModel(
        industryContext,
        solutionType,
        problemDescription,
        'Operations' // Default to operations buyer
      );
      
      // Store the industry context as encoded values
      this.context.inputs.set('industry_type', industryContext === 'DevOps/Software' ? 1 : 
                                               industryContext === 'Agriculture/AgTech' ? 2 : 
                                               industryContext === 'Manufacturing' ? 3 : 0);
      this.context.inputs.set('solution_category', solutionType.includes('CI/CD') ? 1 : 
                                                   solutionType.includes('Farming') ? 2 : 
                                                   solutionType.includes('Manufacturing') ? 3 : 0);
    } else {
      // Use healthcare-specific patterns
      valueModelData = recommendValueDrivers(
        companyData.industry,
        undefined,
        undefined
      );
    }
    
    const companyInfo: CompanyInfo = {
      name: companyData.name,
      industry: companyData.industry,
      size: companyData.size,
      analysisType: companyData.subIndustry || companyData.industry,
      website: companyData.website,
      description: companyData.description
    };

    this.context = {
      stage: 'company_research',
      company: companyInfo,
      selectedDrivers: [],
      inputs: new Map(),
      currentDriverIndex: 0,
      currentInputIndex: 0
    };

    // Store typical deal size and other analysis results
    this.context.inputs.set('annual_subscription', analysis.typicalDealSize);
    this.context.inputs.set('onboarding_cost', analysis.typicalDealSize * 0.15);
    
    const response = `🔍 **Researching ${companyInfo.name}**

I found the following information:
• **Industry**: ${companyInfo.industry}
• **Size**: ${companyInfo.size}
• **Analysis Focus**: ${companyInfo.analysisType}
${companyInfo.website ? `• **Website**: ${companyInfo.website}` : ''}
${companyInfo.description ? `• **Profile**: ${companyInfo.description}` : ''}

${analysis.industryContext}

**Industry Pattern Analysis**:
Based on ${industryContext || companyInfo.industry} patterns, value typically splits:
${industryContext ? 
  Object.entries(valueModelData.valueSplit)
    .filter(([_, weight]) => (weight as number) > 0)
    .map(([key, weight]) => {
      const labels: any = {
        'revenueGrowth': 'Revenue Growth',
        'costReduction': 'Cost Reduction',
        'riskMitigation': 'Risk Mitigation',
        'speedAgility': 'Speed & Agility',
        'qualityImprovement': 'Quality Improvement'
      };
      return `• **${labels[key] || key}**: ${weight}% of value`;
    }).join('\n')
  : 
  `• **Revenue Growth**: ${valueModelData.valueSplit?.revenue || 50}% of value
• **Cost Reduction**: ${valueModelData.valueSplit?.cost || 40}% of value
• **Risk Mitigation**: ${valueModelData.valueSplit?.risk || 10}% of value`
}

${valueModelData.valueMessage || valueModelData.insights?.valueMessage || 'Drive operational excellence and business growth'}

**Key Opportunities**:
${analysis.keyOpportunities.map(opp => `• ${opp}`).join('\n')}

**Target Departments & Personas**:
${industryContext ? 
  `• **Operations Leadership**: Process optimization and efficiency gains
• **Technology/IT**: Digital transformation and innovation
• **Finance**: ROI and cost management
• **Executive Team**: Strategic value and competitive advantage` :
  (valueModelData.patterns?.length > 0 ? 
    valueModelData.patterns.slice(0, 3).map((p: any) => 
      `• **${p.targetPersona[0]}** (${p.lineOfBusiness[0]}): ${p.description}`
    ).join('\n') : 
    '• **Sales Leadership**: Revenue growth and market expansion\n• **Operations**: Cost reduction and efficiency\n• **Clinical/Quality**: Outcomes and compliance'
  )
}

**Critical Success Metrics**:
${(valueModelData.kpis || valueModelData.universalKPIs || []).slice(0, 4).map((kpi: string) => `• ${kpi}`).join('\n')}

**Typical Deal Profile**:
• Deal Size: ${this.formatCurrency(analysis.typicalDealSize)} annual
• Sales Cycle: ${analysis.salesCycle} days
• Expected ROI: ${valueModelData.expectedROI?.min || 200}%-${valueModelData.expectedROI?.max || 1000}%
• Payback Period: ${valueModelData.expectedROI?.paybackMonths || 9} months
• Key Success Factors: ${(valueModelData.industrySpecificFactors || valueModelData.insights?.competitiveFactors || ['Integration', 'Training', 'Change Management']).slice(0, 3).join(', ')}

Which department or buyer persona are you targeting${companyInfo.name ? ` at ${companyInfo.name}` : ''}?`;
    
    // Pre-select recommended drivers based on patterns
    this.context.selectedDrivers = valueModelData.recommendedDrivers?.length > 0 ? 
      valueModelData.recommendedDrivers : 
      (valueModelData.primaryDrivers?.length > 0 ? 
        this.mapUniversalDriversToValueDrivers(valueModelData.primaryDrivers) : 
        analysis.recommendedDrivers);
    
    // Store pattern insights for later use
    if (valueModelData.valueSplit) {
      const splits = valueModelData.valueSplit;
      this.context.inputs.set('pattern_revenue_split', splits.revenueGrowth || splits.revenue || 50);
      this.context.inputs.set('pattern_cost_split', splits.costReduction || splits.cost || 40);
      this.context.inputs.set('pattern_risk_split', splits.riskMitigation || splits.risk || 10);
    }
    this.context.inputs.set('expected_roi_min', valueModelData.expectedROI?.min || 200);
    this.context.inputs.set('expected_roi_max', valueModelData.expectedROI?.max || 1000);

    this.context.stage = 'commercial_footprint';

    return {
      response,
      stage: this.context.stage,
      progress: 15,
      context: this.context
    };
  }

  private async handleCompanyResearch(message: string): Promise<any> {
    const lowerMessage = message.toLowerCase();
    
    // Check if they're specifying a department/persona
    let targetPersona = '';
    let lineOfBusiness = '';
    
    const personaKeywords = {
      'sales': ['Sales', 'Commercial'],
      'operations': ['Operations', 'Supply Chain'],
      'clinical': ['Clinical', 'Quality'],
      'finance': ['Finance', 'Revenue Cycle'],
      'it': ['IT', 'Technology'],
      'marketing': ['Marketing', 'Product']
    };
    
    Object.entries(personaKeywords).forEach(([key, values]) => {
      if (lowerMessage.includes(key)) {
        lineOfBusiness = values[0];
        targetPersona = `VP ${values[0]}`;
      }
    });
    
    // Also check for specific titles
    if (lowerMessage.includes('coo') || lowerMessage.includes('chief operating')) {
      targetPersona = 'COO';
      lineOfBusiness = 'Operations';
    } else if (lowerMessage.includes('cfo') || lowerMessage.includes('chief financial')) {
      targetPersona = 'CFO';
      lineOfBusiness = 'Finance';
    } else if (lowerMessage.includes('cmo') || lowerMessage.includes('chief medical')) {
      targetPersona = 'CMO';
      lineOfBusiness = 'Clinical';
    }
    
    if (targetPersona || lineOfBusiness) {
      // Get more specific pattern recommendations
      const specificPatterns = recommendValueDrivers(
        this.context.company?.industry || 'Healthcare',
        targetPersona,
        lineOfBusiness
      );
      
      // Update selected drivers based on specific pattern
      if (specificPatterns.recommendedDrivers.length > 0) {
        this.context.selectedDrivers = specificPatterns.recommendedDrivers;
      }
      
      // Store the target persona for context as encoded values
      this.context.inputs.set('persona_type', targetPersona.includes('COO') ? 1 : 
                                              targetPersona.includes('CFO') ? 2 : 
                                              targetPersona.includes('CMO') ? 3 : 0);
      this.context.inputs.set('lob_type', lineOfBusiness === 'Operations' ? 1 : 
                                          lineOfBusiness === 'Finance' ? 2 : 
                                          lineOfBusiness === 'Clinical' ? 3 : 0);
      
      this.context.stage = 'commercial_footprint';
      
      return {
        response: `Excellent! Targeting **${targetPersona || lineOfBusiness}** at ${this.context.company?.name}.

${specificPatterns.patterns.length > 0 ? 
  `**Pattern Match Found**: ${specificPatterns.patterns[0].name}\n${specificPatterns.patterns[0].description}\n\n` : ''
}

**Value Focus for ${lineOfBusiness}**:
• Primary: ${specificPatterns.insights.valueMessage}
• Expected ROI: ${specificPatterns.expectedROI.min}%-${specificPatterns.expectedROI.max}%
• Key Metrics: ${specificPatterns.kpis.slice(0, 3).join(', ')}

Now, tell me about your commercial footprint:
• How many sales reps cover accounts like ${this.context.company?.name}?
• What's your typical deal size (annual contract value)?`,
        stage: this.context.stage,
        progress: 25,
        context: this.context
      };
    }
    
    // Default response if no persona specified
    if (lowerMessage.includes('yes') || lowerMessage.includes('correct') || lowerMessage.includes('all')) {
      this.context.stage = 'commercial_footprint';
      
      return {
        response: `Great! Let's build your value model.

**First, tell me about your commercial footprint:**
• How many sales reps cover accounts like ${this.context.company?.name}?
• What's your typical deal size (annual contract value)?`,
        stage: this.context.stage,
        progress: 20,
        context: this.context
      };
    }

    return {
      response: 'Which department or buyer persona are you targeting? (e.g., "Sales", "Operations", "Clinical", "CFO")',
      stage: this.context.stage,
      progress: 18,
      context: this.context
    };
  }

  private async handleCommercialFootprint(message: string): Promise<any> {
    // Parse rep count and deal size
    const numbers = message.match(/\d+/g);
    const repCount = numbers ? parseInt(numbers[0]) : 20;
    
    // Look for dollar amounts
    const dollarMatch = message.match(/\$?([\d,]+)k?m?/i);
    let dealSize = 450000; // default
    if (dollarMatch) {
      const value = parseInt(dollarMatch[1].replace(/,/g, ''));
      if (message.toLowerCase().includes('m')) {
        dealSize = value * 1000000;
      } else if (message.toLowerCase().includes('k')) {
        dealSize = value * 1000;
      } else {
        dealSize = value;
      }
    }

    // Store inputs
    this.context.inputs.set('reps', repCount);
    this.context.inputs.set('annual_subscription', dealSize);
    this.context.inputs.set('onboarding_cost', dealSize * 0.15); // 15% of annual for onboarding

    // Move to driver selection
    this.context.stage = 'driver_selection';

    const response = `📊 **Commercial Profile Captured**
• Sales Reps: **${repCount}**
• Typical Deal Size: **${this.formatCurrency(dealSize)}** annual

Now, let me tailor the value drivers for your solution.

**Which value drivers apply to your offering?** (Reply with numbers or "all")

**Revenue Drivers:**
1️⃣ **New Surgeon Acquisition** - Find and convert new physicians through better targeting
2️⃣ **Share Gain in Existing Accounts** - Expand within current customers
3️⃣ **ASC Shift Capture** - Win procedures moving to outpatient settings
4️⃣ **Sales Velocity** - Faster cycles and better win rates
5️⃣ **Contract Compliance** - Improve on-contract purchasing

**Cost Savings:**
6️⃣ **Rep Time Savings** - Reduce admin/research time by 6+ hrs/week
7️⃣ **Faster New Rep Ramp** - Get reps productive 2-3 months faster
8️⃣ **Fewer Bad Demos** - Better qualification saves wasted effort
9️⃣ **Reduced Data Spend** - Eliminate third-party data costs

Select the drivers that best match your value proposition (e.g., "1, 2, 6, 7" or "all")`;

    return {
      response,
      stage: this.context.stage,
      progress: 35,
      context: this.context
    };
  }

  private async handleDriverSelection(message: string): Promise<any> {
    const lowerMessage = message.toLowerCase();
    
    // Select drivers based on user input
    let selectedDrivers: string[] = [];
    
    if (lowerMessage.includes('all')) {
      selectedDrivers = [
        'new_surgeon_acquisition',
        'share_gain_existing',
        'asc_shift_capture',
        'sales_velocity',
        'contract_compliance',
        'rep_productivity',
        'faster_ramp',
        'reduced_bad_demos',
        'data_spend_reduction'
      ];
    } else {
      // Parse numbers from message
      const numbers = message.match(/\d+/g);
      if (numbers) {
        const driverMap: { [key: string]: string } = {
          '1': 'new_surgeon_acquisition',
          '2': 'share_gain_existing',
          '3': 'asc_shift_capture',
          '4': 'sales_velocity',
          '5': 'contract_compliance',
          '6': 'rep_productivity',
          '7': 'faster_ramp',
          '8': 'reduced_bad_demos',
          '9': 'data_spend_reduction'
        };
        
        numbers.forEach(num => {
          if (driverMap[num]) {
            selectedDrivers.push(driverMap[num]);
          }
        });
      }
    }

    // If no valid selection, default to top drivers
    if (selectedDrivers.length === 0) {
      selectedDrivers = [
        'new_surgeon_acquisition',
        'share_gain_existing',
        'rep_productivity',
        'faster_ramp'
      ];
    }

    this.context.selectedDrivers = selectedDrivers;
    this.context.stage = 'data_collection';
    this.context.currentDriverIndex = 0;
    this.context.currentInputIndex = 0;

    // Start data collection for first driver
    const firstDriver = VALUE_DRIVERS.find(d => d.id === selectedDrivers[0]);
    
    const response = `✅ **Selected ${selectedDrivers.length} Value Drivers**

Now I need to gather some key data points to calculate your ROI. I'll use industry benchmarks where possible to speed this up.

**Let's start with ${firstDriver?.name}:**

${this.getNextQuestion()}`;

    return {
      response,
      stage: this.context.stage,
      progress: 50,
      context: this.context
    };
  }

  private async handleDataCollection(message: string): Promise<any> {
    // Parse the user's input
    const value = this.parseValue(message);
    
    // Store the input
    const currentDriver = VALUE_DRIVERS.find(d => d.id === this.context.selectedDrivers[this.context.currentDriverIndex]);
    if (currentDriver && this.context.currentInputIndex < currentDriver.inputs.length) {
      const input = currentDriver.inputs[this.context.currentInputIndex];
      this.context.inputs.set(input.id, value);
      this.context.currentInputIndex++;
    }

    // Check if we need more inputs for this driver
    if (currentDriver && this.context.currentInputIndex < currentDriver.inputs.length) {
      return {
        response: this.getNextQuestion(),
        stage: this.context.stage,
        progress: 50 + (this.context.currentDriverIndex / this.context.selectedDrivers.length) * 30,
        context: this.context
      };
    }

    // Move to next driver
    this.context.currentDriverIndex++;
    this.context.currentInputIndex = 0;

    // Check if we have more drivers
    if (this.context.currentDriverIndex < this.context.selectedDrivers.length) {
      const nextDriver = VALUE_DRIVERS.find(d => d.id === this.context.selectedDrivers[this.context.currentDriverIndex]);
      return {
        response: `✅ Got it!

**Next driver: ${nextDriver?.name}**

${this.getNextQuestion()}`,
        stage: this.context.stage,
        progress: 50 + (this.context.currentDriverIndex / this.context.selectedDrivers.length) * 30,
        context: this.context
      };
    }

    // All data collected, move to calculation
    this.context.stage = 'calculation';
    return this.handleCalculation(message);
  }

  private async handleCalculation(message: string): Promise<any> {
    // Apply default values for any missing inputs
    this.applyDefaults();

    // Calculate value for selected drivers
    const selectedDriverObjects = VALUE_DRIVERS.filter(d => 
      this.context.selectedDrivers.includes(d.id)
    );

    const results = calculateTotalValue(selectedDriverObjects, this.context.inputs);
    
    // Get costs
    const annualCost = this.context.inputs.get('annual_subscription') || 450000;
    const onboardingCost = this.context.inputs.get('onboarding_cost') || 75000;
    const totalCostsY1 = annualCost + onboardingCost;
    
    // Apply adoption ramp
    const adoptionFactor = calculateAdoptionFactor('standard'); // 62.5%
    const realizedBenefitY1 = results.totalBenefits * adoptionFactor;
    const netBenefitY1 = realizedBenefitY1 - totalCostsY1;
    
    // Calculate steady state (Year 2+)
    const netBenefitSteadyState = results.totalBenefits - annualCost;
    
    // Calculate 3-year NPV (12% discount rate)
    const npv = calculateNPV(
      [realizedBenefitY1, netBenefitSteadyState, netBenefitSteadyState],
      [totalCostsY1, annualCost, annualCost],
      0.12
    );
    
    // Calculate payback
    const monthlyBenefit = netBenefitY1 / 12;
    const payback = calculatePayback(totalCostsY1, monthlyBenefit);

    // Generate scenarios
    const scenarios = generateScenarios(selectedDriverObjects, this.context.inputs);

    // Store calculations
    this.context.calculations = {
      totalBenefits: results.totalBenefits,
      totalCosts: totalCostsY1,
      netBenefit: netBenefitY1,
      npv: npv,
      payback: payback,
      scenarios: scenarios,
      byDriver: results.byDriver,
      byCategory: results.byCategory
    };

    this.context.stage = 'refinement';

    const response = `🎯 **Value Model Complete!**

Based on your inputs, here's what I'm projecting for ${this.context.company?.name}:

**📊 Executive Summary:**
• **Total Benefits (Year 1)**: ${this.formatCurrency(results.totalBenefits)} (full run-rate)
• **Investment**: ${this.formatCurrency(totalCostsY1)} (including one-time setup)
• **Net Benefit (Year 1)**: ${this.formatCurrency(netBenefitY1)} (after ${Math.round(adoptionFactor * 100)}% adoption ramp)
• **3-Year NPV**: ${this.formatCurrency(npv)}
• **Payback Period**: ${payback.toFixed(1)} months
• **ROI (Year 1)**: ${Math.round((netBenefitY1 / totalCostsY1) * 100)}%

**💰 Value Breakdown:**
${this.getValueBreakdown(results)}

**📈 Scenario Analysis:**
• Conservative: ${this.formatCurrency(scenarios.conservative)} NPV
• Base Case: ${this.formatCurrency(npv)} NPV
• Optimistic: ${this.formatCurrency(scenarios.optimistic)} NPV

The business case is strong with a ${payback.toFixed(1)}-month payback and ${Math.round((netBenefitY1 / totalCostsY1) * 100)}% first-year ROI.

Would you like to:
1. **Adjust assumptions** (type "what if...")
2. **See detailed report** (type "show report")
3. **Export to PowerPoint** (type "export")`;

    return {
      response,
      stage: this.context.stage,
      progress: 90,
      context: this.context,
      showReport: false
    };
  }

  private async handleRefinement(message: string): Promise<any> {
    const lowerMessage = message.toLowerCase();

    if (lowerMessage.includes('show report') || lowerMessage.includes('detailed')) {
      this.context.stage = 'report_generation';
      return {
        response: 'Generating detailed report...',
        stage: this.context.stage,
        progress: 100,
        context: this.context,
        showReport: true
      };
    }

    if (lowerMessage.includes('what if')) {
      // Handle what-if scenarios
      return {
        response: `**What-if Analysis**

You can adjust any assumption. For example:
• "What if we only get 10 reps instead of 20?"
• "What if adoption is 60% instead of 80%?"
• "What if we achieve 5 new surgeons per rep?"

What would you like to test?`,
        stage: this.context.stage,
        progress: 95,
        context: this.context
      };
    }

    if (lowerMessage.includes('export')) {
      return {
        response: `📥 **Export Options:**

I can generate:
• **PowerPoint deck** - 8-slide executive presentation
• **PDF report** - Detailed business case document
• **Excel model** - Full calculation workbook

Which format would you like?`,
        stage: this.context.stage,
        progress: 95,
        context: this.context
      };
    }

    // Default: show report
    this.context.stage = 'report_generation';
    return {
      response: 'Generating detailed report...',
      stage: this.context.stage,
      progress: 100,
      context: this.context,
      showReport: true
    };
  }

  private async handleDefault(message: string): Promise<any> {
    return {
      response: `I'm your Value Architect agent. I help build ROI models for enterprise deals.

**Try saying:**
• "Build a value model for [Company Name]"
• "Create ROI analysis for Anika Therapeutics"
• "Help me build a business case"

What company would you like to analyze?`,
      stage: 'idle',
      progress: 0,
      context: this.context
    };
  }

  // Helper methods
  private getNextQuestion(): string {
    const currentDriver = VALUE_DRIVERS.find(d => d.id === this.context.selectedDrivers[this.context.currentDriverIndex]);
    if (!currentDriver) return '';

    const input = currentDriver.inputs[this.context.currentInputIndex];
    if (!input) return '';

    // Check if we already have this input (shared across drivers)
    if (this.context.inputs.has(input.id)) {
      this.context.currentInputIndex++;
      if (this.context.currentInputIndex < currentDriver.inputs.length) {
        return this.getNextQuestion();
      }
      return '';
    }

    let question = `**${input.name}**\n`;
    question += `${input.description}\n\n`;
    question += `Industry benchmark: **${this.formatValue(input.defaultValue, input.type)}**`;
    if (input.lowValue && input.highValue) {
      question += ` (typically ${this.formatValue(input.lowValue, input.type)} - ${this.formatValue(input.highValue, input.type)})`;
    }
    question += `\n\nYour value? (or press Enter to use benchmark)`;

    return question;
  }

  private parseValue(message: string): number {
    // Remove commas and dollar signs
    const cleaned = message.replace(/[$,]/g, '');
    
    // Check for percentages
    if (message.includes('%')) {
      return parseFloat(cleaned) / 100;
    }
    
    // Check for millions
    if (message.toLowerCase().includes('m')) {
      return parseFloat(cleaned) * 1000000;
    }
    
    // Check for thousands
    if (message.toLowerCase().includes('k')) {
      return parseFloat(cleaned) * 1000;
    }
    
    // Default: parse as number
    const parsed = parseFloat(cleaned);
    return isNaN(parsed) ? 0 : parsed;
  }

  private applyDefaults(): void {
    // Apply default values for all selected drivers
    this.context.selectedDrivers.forEach(driverId => {
      const driver = VALUE_DRIVERS.find(d => d.id === driverId);
      if (driver) {
        driver.inputs.forEach(input => {
          if (!this.context.inputs.has(input.id)) {
            this.context.inputs.set(input.id, input.defaultValue);
          }
        });
      }
    });

    // Ensure we have common values
    if (!this.context.inputs.has('adoption_rate')) {
      this.context.inputs.set('adoption_rate', 0.80);
    }
    if (!this.context.inputs.has('gross_margin')) {
      this.context.inputs.set('gross_margin', 0.70);
    }
    if (!this.context.inputs.has('weeks_per_year')) {
      this.context.inputs.set('weeks_per_year', 48);
    }
  }

  private formatCurrency(value: number): string {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  }

  private formatValue(value: number, type: string): string {
    switch (type) {
      case 'currency':
        return this.formatCurrency(value);
      case 'percentage':
        return `${(value * 100).toFixed(0)}%`;
      default:
        return value.toString();
    }
  }

  private getValueBreakdown(results: any): string {
    let breakdown = '';
    
    // Group by category
    const revenueTotal = results.byCategory.get('revenue_uplift') || 0;
    const costTotal = results.byCategory.get('cost_savings') || 0;
    
    if (revenueTotal > 0) {
      breakdown += `**Revenue Growth**: ${this.formatCurrency(revenueTotal)}\n`;
      this.context.selectedDrivers.forEach(driverId => {
        const driver = VALUE_DRIVERS.find(d => d.id === driverId);
        if (driver && driver.category === 'revenue_uplift') {
          const value = results.byDriver.get(driverId) || 0;
          if (value > 0) {
            breakdown += `  • ${driver.name}: ${this.formatCurrency(value)}\n`;
          }
        }
      });
    }
    
    if (costTotal > 0) {
      breakdown += `\n**Cost Savings**: ${this.formatCurrency(costTotal)}\n`;
      this.context.selectedDrivers.forEach(driverId => {
        const driver = VALUE_DRIVERS.find(d => d.id === driverId);
        if (driver && driver.category === 'cost_savings') {
          const value = results.byDriver.get(driverId) || 0;
          if (value > 0) {
            breakdown += `  • ${driver.name}: ${this.formatCurrency(value)}\n`;
          }
        }
      });
    }
    
    return breakdown;
  }

  // Get report data for the ValueModelReport component
  getReportData(): any {
    if (!this.context.calculations || !this.context.company) {
      return null;
    }

    const calc = this.context.calculations;
    const adoptionRamp = calculateAdoptionFactor('standard');
    
    // Build value drivers array for report
    const valueDrivers = this.context.selectedDrivers.map(driverId => {
      const driver = VALUE_DRIVERS.find(d => d.id === driverId);
      const value = calc.byDriver.get(driverId) || 0;
      return {
        name: driver?.name || '',
        value: value,
        percentOfTotal: value / calc.totalBenefits,
        confidence: driver?.confidenceLevel || 0.75,
        category: driver?.category === 'revenue_uplift' ? 'revenue' : 'cost'
      };
    }).sort((a, b) => b.value - a.value);

    return {
      company: this.context.company,
      keyMetrics: {
        totalBenefitsY1: calc.totalBenefits,
        netBenefitY1: calc.netBenefit,
        npv3Year: calc.npv,
        paybackMonths: calc.payback,
        adoptionRamp: adoptionRamp
      },
      executiveSummary: {
        roiYear1: (calc.netBenefit / calc.totalCosts) * 100,
        paybackPeriod: calc.payback,
        roi3Year: (calc.npv / (calc.totalCosts * 3)) * 100,
        keyRecommendation: calc.payback < 6 ? 
          'Exceptional ROI - Strong business case for immediate investment' :
          'Solid ROI - Recommended investment with proper planning'
      },
      valueDrivers: valueDrivers,
      financialDetails: {
        totalBenefitsY1: calc.totalBenefits,
        totalCostsY1: calc.totalCosts,
        netBenefitRealized: calc.netBenefit,
        netBenefitSteadyState: calc.totalBenefits - (this.context.inputs.get('annual_subscription') || 450000),
        npv3Year: calc.npv,
        discountRate: 0.12
      },
      assumptions: {
        salesReps: this.context.inputs.get('reps') || 20,
        aspPerCase: this.context.inputs.get('asp') || 4500,
        grossMargin: this.context.inputs.get('gross_margin') || 0.70,
        annualProcedures: this.context.inputs.get('target_procedures') || 12000,
        adoptionRate: this.context.inputs.get('adoption_rate') || 0.80,
        criticalFactor: `Rep adoption rate of ${((this.context.inputs.get('adoption_rate') || 0.80) * 100).toFixed(0)}% drives majority of value realization`
      },
      scenarios: calc.scenarios,
      implementationNotes: [
        'Focus initial rollout on high-volume accounts',
        'Integrate with existing CRM to track outcomes',
        'Monitor adoption metrics weekly during first quarter',
        'Establish executive sponsor at target account',
        'Schedule quarterly business reviews to track progress'
      ],
      keySuccessFactors: [
        `Achieve ${((this.context.inputs.get('adoption_rate') || 0.80) * 100).toFixed(0)}% rep adoption within 6 months`,
        'Focus on top 3 reps for pilot program',
        'Track value metrics from day one',
        'Maintain executive alignment throughout'
      ]
    };
  }

  // Recalculate with new inputs (for what-if analysis)
  recalculateWithInputs(newInputs: Map<string, number>): any {
    if (!this.context.company || this.context.selectedDrivers.length === 0) {
      return null;
    }

    // Update context with new inputs
    this.context.inputs = newInputs;

    // Recalculate everything
    const selectedDriverObjects = VALUE_DRIVERS.filter(d => 
      this.context.selectedDrivers.includes(d.id)
    );

    const results = calculateTotalValue(selectedDriverObjects, newInputs);
    
    // Get costs
    const annualCost = newInputs.get('annual_subscription') || 450000;
    const onboardingCost = newInputs.get('onboarding_cost') || 75000;
    const totalCostsY1 = annualCost + onboardingCost;
    
    // Apply adoption ramp
    const adoptionFactor = calculateAdoptionFactor('standard');
    const realizedBenefitY1 = results.totalBenefits * adoptionFactor;
    const netBenefitY1 = realizedBenefitY1 - totalCostsY1;
    
    // Calculate steady state
    const netBenefitSteadyState = results.totalBenefits - annualCost;
    
    // Calculate 3-year NPV
    const npv = calculateNPV(
      [realizedBenefitY1, netBenefitSteadyState, netBenefitSteadyState],
      [totalCostsY1, annualCost, annualCost],
      0.12
    );
    
    // Calculate payback
    const monthlyBenefit = netBenefitY1 / 12;
    const payback = calculatePayback(totalCostsY1, monthlyBenefit);

    // Generate scenarios with new inputs
    const scenarios = generateScenarios(selectedDriverObjects, newInputs);

    // Update calculations in context
    this.context.calculations = {
      totalBenefits: results.totalBenefits,
      totalCosts: totalCostsY1,
      netBenefit: netBenefitY1,
      npv: npv,
      payback: payback,
      scenarios: scenarios,
      byDriver: results.byDriver,
      byCategory: results.byCategory
    };

    // Return updated report data
    return this.getReportData();
  }

  // Map universal driver names to existing value driver IDs
  private mapUniversalDriversToValueDrivers(universalDrivers: string[]): string[] {
    const mappings: { [key: string]: string } = {
      // Revenue drivers
      'New customer acquisition': 'new_surgeon_acquisition',
      'Expansion revenue': 'share_gain_existing',
      'Market share gain': 'share_gain_existing',
      'Sales velocity': 'sales_velocity',
      'Increased throughput': 'sales_velocity',
      
      // Cost drivers
      'Labor reduction': 'rep_productivity',
      'Resource optimization': 'rep_productivity',
      'Process acceleration': 'rep_productivity',
      'Automation': 'rep_productivity',
      
      // Supply chain
      'Inventory optimization': 'data_spend_reduction',
      'Supply chain efficiency': 'data_spend_reduction',
      
      // Quality
      'Error reduction': 'reduced_bad_demos',
      'Defect reduction': 'reduced_bad_demos',
      'Quality improvement': 'reduced_bad_demos',
      
      // Speed
      'Deployment velocity': 'sales_velocity',
      'Time to market': 'faster_ramp',
      'Cycle time': 'sales_velocity'
    };
    
    const mappedDrivers: string[] = [];
    const defaultDrivers = ['sales_velocity', 'rep_productivity', 'contract_compliance', 'faster_ramp'];
    
    universalDrivers.forEach(driver => {
      const mapped = mappings[driver];
      if (mapped && !mappedDrivers.includes(mapped)) {
        mappedDrivers.push(mapped);
      }
    });
    
    // If no mappings found, use defaults
    return mappedDrivers.length > 0 ? mappedDrivers : defaultDrivers;
  }
  
  // Save current model to backend
  async saveModel(): Promise<string | null> {
    if (!this.userId) {
      console.warn('No user ID, cannot save model');
      return null;
    }

    try {
      const modelData = {
        name: `Value Model - ${this.context.company?.name || 'Unknown'}`,
        description: `${this.context.stage} stage value model for ${this.context.company?.industry || 'Unknown'} industry`,
        target_value: this.context.calculations?.totalBenefits,
        hypothesis: {
          company_name: this.context.company?.name || 'Unknown',
          industry: this.context.company?.industry || 'Unknown',
          inputs: Object.fromEntries(this.context.inputs),
          selectedDrivers: this.context.selectedDrivers,
          calculations: this.context.calculations,
          stage: this.context.stage
        }
      };

      if (this.modelId) {
        // Update existing model
        const updated = await valueModelsAPI.update(this.modelId, modelData);
        return updated.id;
      } else {
        // Create new model
        const created = await valueModelsAPI.create(modelData);
        this.modelId = created.id;
        return created.id;
      }
    } catch (error) {
      console.error('Failed to save model:', error);
      return null;
    }
  }

  // Load a model from backend
  async loadModel(modelId: string): Promise<boolean> {
    try {
      const model = await valueModelsAPI.get(modelId);
      if (!model) return false;

      this.modelId = model.id;
      
      // Parse hypothesis data to restore context
      const hypothesis = model.hypothesis || {};
      
      this.context = {
        stage: hypothesis.stage as WorkflowStage || 'idle',
        company: {
          name: hypothesis.company_name || model.name,
          industry: hypothesis.industry || 'Unknown',
          size: 'Unknown',
          analysisType: hypothesis.industry || 'Unknown'
        },
        selectedDrivers: hypothesis.selectedDrivers || [],
        inputs: new Map(Object.entries(hypothesis.inputs || {})),
        currentDriverIndex: 0,
        currentInputIndex: 0,
        calculations: hypothesis.calculations
      };

      return true;
    } catch (error) {
      console.error('Failed to load model:', error);
      return false;
    }
  }

  // Set user for saving
  setUser(userId: string): void {
    this.userId = userId;
    this.startAutoSave();
    
    // Subscribe to agent messages from backend
    if (this.agentMessageHandler) {
      // Unsubscribe previous handler
      this.agentMessageHandler = null;
    }
    
    this.agentMessageHandler = (message: AgentMessage) => {
      if (message.agent === 'value_architect' && message.type === 'agent:response') {
        // Handle agent response from backend
        console.log('Received agent response:', message);
        // TODO: Process and update context based on backend response
      }
    };
    
    agentAPI.onMessage(this.agentMessageHandler);
  }

  // Start auto-save timer
  private startAutoSave(): void {
    this.stopAutoSave();
    this.autoSaveTimer = setInterval(async () => {
      if (this.context.stage !== 'idle' && this.userId) {
        await this.saveModel();
      }
    }, 30000); // Save every 30 seconds
  }

  // Stop auto-save timer
  private stopAutoSave(): void {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
      this.autoSaveTimer = null;
    }
  }

  // Get all saved models for current user
  async getMyModels(): Promise<any[]> {
    try {
      return await valueModelsAPI.list();
    } catch (error) {
      console.error('Failed to get models:', error);
      return [];
    }
  }
  
  // Export model in various formats
  async exportModel(format: 'pdf' | 'ppt' | 'excel'): Promise<Blob | null> {
    if (!this.modelId) {
      console.warn('No model to export');
      return null;
    }
    
    try {
      return await valueModelsAPI.export(this.modelId, format);
    } catch (error) {
      console.error('Failed to export model:', error);
      return null;
    }
  }
  
  // Reset the agent to start over
  reset(): void {
    this.context = {
      stage: 'idle',
      selectedDrivers: [],
      inputs: new Map(),
      currentDriverIndex: 0,
      currentInputIndex: 0
    };
    this.modelId = null;
    this.stopAutoSave();
    this.agentMessageHandler = null;
  }
}

// Export singleton instance
export const valueArchitect = new ValueArchitectAgent();
