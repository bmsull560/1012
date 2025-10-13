// Value Driver Pattern Library
// Systematic patterns based on Industry + Line of Business/Persona

export interface ValuePattern {
  id: string;
  name: string;
  industry: string[];
  targetPersona: string[];
  lineOfBusiness: string[];
  description: string;
  typicalSplit: {
    revenue: number;  // percentage
    cost: number;     // percentage
    risk: number;     // percentage
  };
  primaryDrivers: string[];
  secondaryDrivers: string[];
  kpis: string[];
  typicalROI: {
    min: number;
    max: number;
  };
  decisionCriteria: string[];
}

// Master pattern library based on Industry x Persona combinations
export const VALUE_PATTERNS: ValuePattern[] = [
  // ============= HEALTHCARE PROVIDER PATTERNS =============
  {
    id: 'healthcare_provider_operations',
    name: 'Healthcare Provider - Operations',
    industry: ['Healthcare Provider', 'Hospital', 'Health System'],
    targetPersona: ['COO', 'VP Operations', 'Operations Director'],
    lineOfBusiness: ['Operations', 'Supply Chain', 'Facilities'],
    description: 'Operational efficiency and cost reduction for healthcare delivery',
    typicalSplit: {
      revenue: 20,
      cost: 70,
      risk: 10
    },
    primaryDrivers: [
      'supply_chain_optimization',
      'staff_productivity',
      'patient_flow_efficiency',
      'facility_utilization'
    ],
    secondaryDrivers: [
      'inventory_reduction',
      'overtime_reduction',
      'readmission_prevention'
    ],
    kpis: [
      'Cost per patient day',
      'Length of stay',
      'Bed turnover rate',
      'Supply expense per case'
    ],
    typicalROI: { min: 300, max: 800 },
    decisionCriteria: [
      'Integration with existing systems',
      'Implementation timeline',
      'Change management requirements',
      'Regulatory compliance'
    ]
  },
  {
    id: 'healthcare_provider_clinical',
    name: 'Healthcare Provider - Clinical',
    industry: ['Healthcare Provider', 'Hospital', 'Health System'],
    targetPersona: ['CMO', 'VP Clinical', 'Medical Director'],
    lineOfBusiness: ['Clinical', 'Quality', 'Patient Care'],
    description: 'Clinical outcomes improvement and quality initiatives',
    typicalSplit: {
      revenue: 40,
      cost: 30,
      risk: 30
    },
    primaryDrivers: [
      'clinical_outcome_improvement',
      'patient_satisfaction',
      'care_coordination',
      'clinical_variation_reduction'
    ],
    secondaryDrivers: [
      'readmission_reduction',
      'infection_rate_reduction',
      'medication_error_prevention'
    ],
    kpis: [
      'HCAHPS scores',
      'Readmission rate',
      'Mortality rate',
      'Clinical quality metrics'
    ],
    typicalROI: { min: 400, max: 1200 },
    decisionCriteria: [
      'Clinical evidence',
      'Physician adoption',
      'Patient safety impact',
      'Quality score improvement'
    ]
  },
  {
    id: 'healthcare_provider_revenue_cycle',
    name: 'Healthcare Provider - Revenue Cycle',
    industry: ['Healthcare Provider', 'Hospital', 'Health System'],
    targetPersona: ['CFO', 'VP Revenue Cycle', 'Revenue Cycle Director'],
    lineOfBusiness: ['Finance', 'Revenue Cycle', 'Billing'],
    description: 'Revenue optimization and financial performance',
    typicalSplit: {
      revenue: 80,
      cost: 15,
      risk: 5
    },
    primaryDrivers: [
      'denial_reduction',
      'days_in_ar_reduction',
      'clean_claim_rate',
      'collection_rate_improvement'
    ],
    secondaryDrivers: [
      'prior_auth_automation',
      'coding_accuracy',
      'patient_payment_collection'
    ],
    kpis: [
      'Days in A/R',
      'Denial rate',
      'Clean claim rate',
      'Net collection rate'
    ],
    typicalROI: { min: 500, max: 1500 },
    decisionCriteria: [
      'ROI timeline',
      'Integration with EMR/billing systems',
      'Compliance with regulations',
      'Staff training requirements'
    ]
  },

  // ============= MEDICAL DEVICE PATTERNS =============
  {
    id: 'medical_device_sales',
    name: 'Medical Device - Sales Organization',
    industry: ['Medical Device', 'MedTech', 'Orthopedics', 'Cardiovascular'],
    targetPersona: ['VP Sales', 'Sales Director', 'Commercial Leader'],
    lineOfBusiness: ['Sales', 'Commercial', 'Business Development'],
    description: 'Sales productivity and revenue growth for device manufacturers',
    typicalSplit: {
      revenue: 70,
      cost: 25,
      risk: 5
    },
    primaryDrivers: [
      'new_surgeon_acquisition',
      'share_gain_existing',
      'asc_shift_capture',
      'sales_velocity',
      'contract_compliance'
    ],
    secondaryDrivers: [
      'rep_productivity',
      'faster_ramp',
      'reduced_bad_demos'
    ],
    kpis: [
      'New surgeon adoption rate',
      'Market share growth',
      'Sales cycle length',
      'Win rate',
      'ASP per procedure'
    ],
    typicalROI: { min: 800, max: 2000 },
    decisionCriteria: [
      'Surgeon adoption ease',
      'Clinical evidence',
      'Competitive differentiation',
      'Sales force enablement'
    ]
  },
  {
    id: 'medical_device_marketing',
    name: 'Medical Device - Marketing',
    industry: ['Medical Device', 'MedTech'],
    targetPersona: ['CMO', 'VP Marketing', 'Marketing Director'],
    lineOfBusiness: ['Marketing', 'Product Marketing', 'Market Access'],
    description: 'Market intelligence and demand generation',
    typicalSplit: {
      revenue: 60,
      cost: 30,
      risk: 10
    },
    primaryDrivers: [
      'lead_generation',
      'market_intelligence',
      'kol_engagement',
      'conference_roi'
    ],
    secondaryDrivers: [
      'brand_awareness',
      'digital_engagement',
      'content_effectiveness'
    ],
    kpis: [
      'Cost per lead',
      'Lead to opportunity conversion',
      'Marketing qualified leads',
      'Campaign ROI'
    ],
    typicalROI: { min: 400, max: 1000 },
    decisionCriteria: [
      'Marketing automation capabilities',
      'Data quality and coverage',
      'Integration with CRM',
      'Compliance with regulations'
    ]
  },
  {
    id: 'medical_device_supply_chain',
    name: 'Medical Device - Supply Chain',
    industry: ['Medical Device', 'MedTech'],
    targetPersona: ['VP Supply Chain', 'Operations Director'],
    lineOfBusiness: ['Operations', 'Supply Chain', 'Manufacturing'],
    description: 'Supply chain optimization and inventory management',
    typicalSplit: {
      revenue: 20,
      cost: 75,
      risk: 5
    },
    primaryDrivers: [
      'inventory_optimization',
      'consignment_efficiency',
      'trunk_stock_management',
      'expiry_reduction'
    ],
    secondaryDrivers: [
      'logistics_optimization',
      'demand_forecasting',
      'supplier_management'
    ],
    kpis: [
      'Inventory turns',
      'Stock-out rate',
      'Carrying cost reduction',
      'Order fulfillment rate'
    ],
    typicalROI: { min: 300, max: 700 },
    decisionCriteria: [
      'ERP integration',
      'Real-time visibility',
      'Scalability',
      'Regulatory compliance'
    ]
  },

  // ============= PHARMACEUTICAL PATTERNS =============
  {
    id: 'pharma_commercial',
    name: 'Pharmaceuticals - Commercial',
    industry: ['Pharmaceuticals', 'Biotech', 'Life Sciences'],
    targetPersona: ['VP Commercial', 'Sales Director', 'Market Access Director'],
    lineOfBusiness: ['Commercial', 'Sales', 'Market Access'],
    description: 'Commercial excellence and market access for pharma',
    typicalSplit: {
      revenue: 75,
      cost: 20,
      risk: 5
    },
    primaryDrivers: [
      'formulary_access',
      'physician_adoption',
      'patient_adherence',
      'payer_coverage'
    ],
    secondaryDrivers: [
      'sample_efficiency',
      'speaker_program_roi',
      'patient_assistance_programs'
    ],
    kpis: [
      'Prescription volume',
      'Formulary wins',
      'Market access rate',
      'Patient starts'
    ],
    typicalROI: { min: 1000, max: 3000 },
    decisionCriteria: [
      'Regulatory compliance',
      'Data privacy',
      'Payer relationships',
      'Clinical differentiation'
    ]
  },
  {
    id: 'pharma_medical_affairs',
    name: 'Pharmaceuticals - Medical Affairs',
    industry: ['Pharmaceuticals', 'Biotech'],
    targetPersona: ['VP Medical Affairs', 'Medical Director'],
    lineOfBusiness: ['Medical Affairs', 'Clinical', 'R&D'],
    description: 'Medical education and clinical evidence generation',
    typicalSplit: {
      revenue: 40,
      cost: 30,
      risk: 30
    },
    primaryDrivers: [
      'kol_engagement',
      'publication_impact',
      'medical_education',
      'real_world_evidence'
    ],
    secondaryDrivers: [
      'investigator_studies',
      'advisory_board_effectiveness',
      'medical_inquiries'
    ],
    kpis: [
      'KOL engagement score',
      'Publication citations',
      'Medical education reach',
      'Evidence generation timeline'
    ],
    typicalROI: { min: 500, max: 1500 },
    decisionCriteria: [
      'Scientific credibility',
      'KOL network',
      'Compliance capability',
      'Global reach'
    ]
  },

  // ============= PAYER PATTERNS =============
  {
    id: 'payer_operations',
    name: 'Payer - Operations',
    industry: ['Health Insurance', 'Payer', 'Managed Care'],
    targetPersona: ['COO', 'VP Operations'],
    lineOfBusiness: ['Operations', 'Claims', 'Customer Service'],
    description: 'Operational efficiency for health insurers',
    typicalSplit: {
      revenue: 30,
      cost: 65,
      risk: 5
    },
    primaryDrivers: [
      'claims_processing_efficiency',
      'prior_auth_automation',
      'member_service_productivity',
      'fraud_detection'
    ],
    secondaryDrivers: [
      'appeals_reduction',
      'auto_adjudication_rate',
      'call_center_efficiency'
    ],
    kpis: [
      'Cost per claim',
      'Auto-adjudication rate',
      'Prior auth turnaround',
      'Member satisfaction'
    ],
    typicalROI: { min: 400, max: 900 },
    decisionCriteria: [
      'System integration',
      'Regulatory compliance',
      'Member experience impact',
      'Implementation complexity'
    ]
  },
  {
    id: 'payer_clinical',
    name: 'Payer - Clinical/Quality',
    industry: ['Health Insurance', 'Payer', 'Managed Care'],
    targetPersona: ['CMO', 'VP Clinical', 'Quality Director'],
    lineOfBusiness: ['Clinical', 'Quality', 'Population Health'],
    description: 'Clinical quality and population health management',
    typicalSplit: {
      revenue: 40,
      cost: 40,
      risk: 20
    },
    primaryDrivers: [
      'care_gap_closure',
      'risk_adjustment_accuracy',
      'care_coordination',
      'preventive_care_compliance'
    ],
    secondaryDrivers: [
      'readmission_prevention',
      'chronic_care_management',
      'medication_adherence'
    ],
    kpis: [
      'HEDIS scores',
      'Star ratings',
      'Risk adjustment factor',
      'Care gap closure rate'
    ],
    typicalROI: { min: 600, max: 1800 },
    decisionCriteria: [
      'Quality score impact',
      'Provider network engagement',
      'Data integration capability',
      'Regulatory alignment'
    ]
  }
];

// Function to find matching patterns
export function findMatchingPatterns(
  industry: string,
  targetPersona?: string,
  lineOfBusiness?: string
): ValuePattern[] {
  return VALUE_PATTERNS.filter(pattern => {
    // Check industry match (fuzzy matching)
    const industryMatch = pattern.industry.some(ind => 
      industry.toLowerCase().includes(ind.toLowerCase()) ||
      ind.toLowerCase().includes(industry.toLowerCase())
    );
    
    if (!industryMatch) return false;
    
    // If persona specified, check match
    if (targetPersona) {
      const personaMatch = pattern.targetPersona.some(persona =>
        targetPersona.toLowerCase().includes(persona.toLowerCase()) ||
        persona.toLowerCase().includes(targetPersona.toLowerCase())
      );
      if (!personaMatch) return false;
    }
    
    // If line of business specified, check match
    if (lineOfBusiness) {
      const lobMatch = pattern.lineOfBusiness.some(lob =>
        lineOfBusiness.toLowerCase().includes(lob.toLowerCase()) ||
        lob.toLowerCase().includes(lineOfBusiness.toLowerCase())
      );
      if (!lobMatch) return false;
    }
    
    return true;
  });
}

// Function to aggregate patterns across an organization
export function aggregateOrganizationalPatterns(
  industry: string,
  departments: string[] = ['Operations', 'Clinical', 'Finance', 'Sales']
): {
  totalValue: { revenue: number; cost: number; risk: number };
  primaryDrivers: string[];
  kpis: string[];
  typicalROI: { min: number; max: number };
} {
  const patterns = departments.flatMap(dept => 
    findMatchingPatterns(industry, undefined, dept)
  );
  
  if (patterns.length === 0) {
    return {
      totalValue: { revenue: 50, cost: 40, risk: 10 },
      primaryDrivers: [],
      kpis: [],
      typicalROI: { min: 300, max: 1000 }
    };
  }
  
  // Aggregate the patterns
  const avgSplit = patterns.reduce((acc, pattern) => ({
    revenue: acc.revenue + pattern.typicalSplit.revenue / patterns.length,
    cost: acc.cost + pattern.typicalSplit.cost / patterns.length,
    risk: acc.risk + pattern.typicalSplit.risk / patterns.length
  }), { revenue: 0, cost: 0, risk: 0 });
  
  // Collect unique drivers and KPIs
  const allDrivers = new Set<string>();
  const allKPIs = new Set<string>();
  
  patterns.forEach(pattern => {
    pattern.primaryDrivers.forEach(driver => allDrivers.add(driver));
    pattern.kpis.forEach(kpi => allKPIs.add(kpi));
  });
  
  // Calculate ROI range
  const minROI = Math.min(...patterns.map(p => p.typicalROI.min));
  const maxROI = Math.max(...patterns.map(p => p.typicalROI.max));
  
  return {
    totalValue: avgSplit,
    primaryDrivers: Array.from(allDrivers),
    kpis: Array.from(allKPIs),
    typicalROI: { min: minROI, max: maxROI }
  };
}

// Function to get pattern insights
export function getPatternInsights(pattern: ValuePattern): {
  primaryValue: 'revenue' | 'cost' | 'risk';
  focusArea: string;
  typicalBuyer: string;
  valueMessage: string;
  competitiveFactors: string[];
} {
  // Determine primary value type
  const { revenue, cost, risk } = pattern.typicalSplit;
  let primaryValue: 'revenue' | 'cost' | 'risk';
  
  if (revenue >= cost && revenue >= risk) {
    primaryValue = 'revenue';
  } else if (cost >= revenue && cost >= risk) {
    primaryValue = 'cost';
  } else {
    primaryValue = 'risk';
  }
  
  // Generate insights
  const insights = {
    primaryValue,
    focusArea: pattern.lineOfBusiness[0],
    typicalBuyer: pattern.targetPersona[0],
    valueMessage: '',
    competitiveFactors: pattern.decisionCriteria.slice(0, 3)
  };
  
  // Generate value message based on pattern
  switch (primaryValue) {
    case 'revenue':
      insights.valueMessage = `Drive ${pattern.typicalROI.min}-${pattern.typicalROI.max}% ROI through revenue growth and market expansion`;
      break;
    case 'cost':
      insights.valueMessage = `Achieve ${pattern.typicalROI.min}-${pattern.typicalROI.max}% ROI through operational efficiency and cost reduction`;
      break;
    case 'risk':
      insights.valueMessage = `Reduce risk while delivering ${pattern.typicalROI.min}-${pattern.typicalROI.max}% ROI through compliance and quality improvements`;
      break;
  }
  
  return insights;
}

// Map traditional value drivers to pattern categories
export const DRIVER_TO_PATTERN_MAP: { [key: string]: string[] } = {
  // Revenue drivers
  'new_surgeon_acquisition': ['medical_device_sales'],
  'share_gain_existing': ['medical_device_sales'],
  'asc_shift_capture': ['medical_device_sales'],
  'sales_velocity': ['medical_device_sales', 'pharma_commercial'],
  'contract_compliance': ['medical_device_sales', 'healthcare_provider_revenue_cycle'],
  'formulary_access': ['pharma_commercial'],
  'physician_adoption': ['pharma_commercial', 'medical_device_sales'],
  'denial_reduction': ['healthcare_provider_revenue_cycle', 'payer_operations'],
  
  // Cost drivers
  'rep_productivity': ['medical_device_sales', 'pharma_commercial'],
  'supply_chain_optimization': ['healthcare_provider_operations', 'medical_device_supply_chain'],
  'staff_productivity': ['healthcare_provider_operations', 'payer_operations'],
  'inventory_optimization': ['medical_device_supply_chain', 'healthcare_provider_operations'],
  'claims_processing_efficiency': ['payer_operations', 'healthcare_provider_revenue_cycle'],
  
  // Clinical/Quality drivers  
  'clinical_outcome_improvement': ['healthcare_provider_clinical'],
  'patient_satisfaction': ['healthcare_provider_clinical'],
  'care_coordination': ['healthcare_provider_clinical', 'payer_clinical'],
  'readmission_reduction': ['healthcare_provider_clinical', 'payer_clinical'],
  'care_gap_closure': ['payer_clinical'],
  
  // Risk/Compliance drivers
  'fraud_detection': ['payer_operations'],
  'risk_adjustment_accuracy': ['payer_clinical'],
  'compliance_improvement': ['healthcare_provider_operations', 'pharma_commercial']
};

// Export pattern-based recommendations
export function recommendValueDrivers(
  industry: string,
  targetPersona?: string,
  lineOfBusiness?: string
): {
  patterns: ValuePattern[];
  recommendedDrivers: string[];
  valueSplit: { revenue: number; cost: number; risk: number };
  kpis: string[];
  expectedROI: { min: number; max: number };
  insights: any;
} {
  const patterns = findMatchingPatterns(industry, targetPersona, lineOfBusiness);
  
  if (patterns.length === 0) {
    // Return generic pattern
    return {
      patterns: [],
      recommendedDrivers: ['sales_velocity', 'rep_productivity', 'cost_reduction'],
      valueSplit: { revenue: 50, cost: 40, risk: 10 },
      kpis: ['ROI', 'Payback Period', 'NPV'],
      expectedROI: { min: 300, max: 1000 },
      insights: {
        primaryValue: 'revenue',
        focusArea: 'General',
        typicalBuyer: 'Executive',
        valueMessage: 'Drive operational excellence and revenue growth',
        competitiveFactors: ['ROI', 'Integration', 'Support']
      }
    };
  }
  
  // Aggregate recommendations from matching patterns
  const allDrivers = new Set<string>();
  const allKPIs = new Set<string>();
  let totalRevenue = 0, totalCost = 0, totalRisk = 0;
  let minROI = Infinity, maxROI = 0;
  
  patterns.forEach(pattern => {
    pattern.primaryDrivers.forEach(driver => allDrivers.add(driver));
    pattern.kpis.forEach(kpi => allKPIs.add(kpi));
    
    totalRevenue += pattern.typicalSplit.revenue;
    totalCost += pattern.typicalSplit.cost;
    totalRisk += pattern.typicalSplit.risk;
    
    minROI = Math.min(minROI, pattern.typicalROI.min);
    maxROI = Math.max(maxROI, pattern.typicalROI.max);
  });
  
  const count = patterns.length;
  const valueSplit = {
    revenue: Math.round(totalRevenue / count),
    cost: Math.round(totalCost / count),
    risk: Math.round(totalRisk / count)
  };
  
  // Get insights from primary pattern
  const primaryPattern = patterns[0];
  const insights = getPatternInsights(primaryPattern);
  
  return {
    patterns,
    recommendedDrivers: Array.from(allDrivers),
    valueSplit,
    kpis: Array.from(allKPIs).slice(0, 6), // Top 6 KPIs
    expectedROI: { min: minROI, max: maxROI },
    insights
  };
}
