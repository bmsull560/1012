// Universal Value Pattern System
// Works for ANY B2B industry - from DevOps to Agriculture to Healthcare

export interface UniversalValuePattern {
  id: string;
  name: string;
  category: 'operational' | 'strategic' | 'transformational';
  targetFunction: string; // Which business function (Operations, Sales, Engineering, etc.)
  problemSpace: string[]; // What problems does this address
  valueThesis: string; // Core value proposition
  
  // Universal value buckets (apply to ANY industry)
  valueBuckets: {
    revenueGrowth: {
      weight: number; // 0-100
      drivers: string[];
      metrics: string[];
    };
    costReduction: {
      weight: number; // 0-100
      drivers: string[];
      metrics: string[];
    };
    riskMitigation: {
      weight: number; // 0-100
      drivers: string[];
      metrics: string[];
    };
    speedAgility: {
      weight: number; // 0-100
      drivers: string[];
      metrics: string[];
    };
    qualityImprovement: {
      weight: number; // 0-100
      drivers: string[];
      metrics: string[];
    };
  };
  
  typicalROI: {
    min: number;
    max: number;
    paybackMonths: number;
  };
  
  universalKPIs: string[];
  adoptionFactors: string[];
}

// Universal patterns that apply across ALL industries
export const UNIVERSAL_PATTERNS: UniversalValuePattern[] = [
  // ============= OPERATIONAL EFFICIENCY PATTERNS =============
  {
    id: 'operational_efficiency',
    name: 'Operational Efficiency Pattern',
    category: 'operational',
    targetFunction: 'Operations',
    problemSpace: [
      'Manual processes',
      'Resource inefficiency',
      'High operational costs',
      'Process bottlenecks'
    ],
    valueThesis: 'Streamline operations to reduce costs and improve throughput',
    valueBuckets: {
      revenueGrowth: {
        weight: 15,
        drivers: ['Increased throughput', 'Faster time to market', 'Capacity expansion'],
        metrics: ['Units per hour', 'Time to delivery', 'Capacity utilization']
      },
      costReduction: {
        weight: 50,
        drivers: ['Labor reduction', 'Resource optimization', 'Waste elimination'],
        metrics: ['Cost per unit', 'FTE reduction', 'Resource utilization']
      },
      riskMitigation: {
        weight: 10,
        drivers: ['Error reduction', 'Compliance automation', 'Audit trail'],
        metrics: ['Error rate', 'Compliance score', 'Audit findings']
      },
      speedAgility: {
        weight: 20,
        drivers: ['Process acceleration', 'Automation', 'Real-time visibility'],
        metrics: ['Cycle time', 'Process velocity', 'Response time']
      },
      qualityImprovement: {
        weight: 5,
        drivers: ['Standardization', 'Consistency', 'Best practices'],
        metrics: ['Quality score', 'Defect rate', 'Customer satisfaction']
      }
    },
    typicalROI: { min: 200, max: 600, paybackMonths: 6 },
    universalKPIs: [
      'Operational efficiency ratio',
      'Cost per transaction',
      'Process cycle time',
      'Resource utilization'
    ],
    adoptionFactors: ['Change management', 'Training requirements', 'Integration complexity']
  },
  
  {
    id: 'revenue_acceleration',
    name: 'Revenue Acceleration Pattern',
    category: 'strategic',
    targetFunction: 'Sales/Marketing/Growth',
    problemSpace: [
      'Slow growth',
      'Long sales cycles',
      'Poor conversion rates',
      'Market penetration challenges'
    ],
    valueThesis: 'Accelerate revenue growth through improved go-to-market efficiency',
    valueBuckets: {
      revenueGrowth: {
        weight: 60,
        drivers: ['New customer acquisition', 'Expansion revenue', 'Market share gain'],
        metrics: ['Customer acquisition rate', 'Revenue growth rate', 'Market share']
      },
      costReduction: {
        weight: 10,
        drivers: ['Sales efficiency', 'Marketing optimization', 'Customer acquisition cost'],
        metrics: ['CAC', 'Sales efficiency ratio', 'Marketing ROI']
      },
      riskMitigation: {
        weight: 5,
        drivers: ['Pipeline predictability', 'Forecast accuracy', 'Customer retention'],
        metrics: ['Forecast variance', 'Churn rate', 'Customer lifetime value']
      },
      speedAgility: {
        weight: 20,
        drivers: ['Sales velocity', 'Time to revenue', 'Market responsiveness'],
        metrics: ['Sales cycle length', 'Deal velocity', 'Time to first value']
      },
      qualityImprovement: {
        weight: 5,
        drivers: ['Lead quality', 'Customer fit', 'Targeting accuracy'],
        metrics: ['Lead score', 'Win rate', 'Customer success score']
      }
    },
    typicalROI: { min: 300, max: 1000, paybackMonths: 9 },
    universalKPIs: [
      'Revenue growth rate',
      'Customer acquisition cost',
      'Sales cycle length',
      'Win rate'
    ],
    adoptionFactors: ['Sales team buy-in', 'CRM integration', 'Data quality']
  },
  
  {
    id: 'digital_transformation',
    name: 'Digital Transformation Pattern',
    category: 'transformational',
    targetFunction: 'IT/Technology/Innovation',
    problemSpace: [
      'Legacy systems',
      'Digital maturity gaps',
      'Integration challenges',
      'Innovation barriers'
    ],
    valueThesis: 'Transform business capabilities through digital enablement',
    valueBuckets: {
      revenueGrowth: {
        weight: 25,
        drivers: ['New revenue streams', 'Digital channels', 'Service innovation'],
        metrics: ['Digital revenue %', 'New service adoption', 'Channel performance']
      },
      costReduction: {
        weight: 30,
        drivers: ['IT cost optimization', 'Infrastructure efficiency', 'Maintenance reduction'],
        metrics: ['IT cost ratio', 'Infrastructure costs', 'Technical debt']
      },
      riskMitigation: {
        weight: 15,
        drivers: ['Security enhancement', 'Compliance', 'Business continuity'],
        metrics: ['Security incidents', 'Compliance score', 'System uptime']
      },
      speedAgility: {
        weight: 25,
        drivers: ['Deployment velocity', 'Innovation speed', 'Market adaptability'],
        metrics: ['Release frequency', 'Time to market', 'Feature velocity']
      },
      qualityImprovement: {
        weight: 5,
        drivers: ['System reliability', 'User experience', 'Data quality'],
        metrics: ['System availability', 'User satisfaction', 'Data accuracy']
      }
    },
    typicalROI: { min: 400, max: 1500, paybackMonths: 12 },
    universalKPIs: [
      'Digital maturity score',
      'Technology ROI',
      'Innovation index',
      'Time to market'
    ],
    adoptionFactors: ['Technical readiness', 'Cultural change', 'Skills gap']
  },
  
  {
    id: 'quality_excellence',
    name: 'Quality Excellence Pattern',
    category: 'operational',
    targetFunction: 'Quality/Engineering/Production',
    problemSpace: [
      'Quality issues',
      'High defect rates',
      'Customer complaints',
      'Rework costs'
    ],
    valueThesis: 'Achieve excellence through systematic quality improvement',
    valueBuckets: {
      revenueGrowth: {
        weight: 20,
        drivers: ['Premium pricing', 'Customer retention', 'Reputation enhancement'],
        metrics: ['Price premium', 'Retention rate', 'NPS score']
      },
      costReduction: {
        weight: 35,
        drivers: ['Rework reduction', 'Warranty cost reduction', 'Scrap reduction'],
        metrics: ['Cost of quality', 'Rework rate', 'Warranty claims']
      },
      riskMitigation: {
        weight: 20,
        drivers: ['Compliance assurance', 'Liability reduction', 'Brand protection'],
        metrics: ['Compliance violations', 'Liability costs', 'Brand value']
      },
      speedAgility: {
        weight: 10,
        drivers: ['First-time-right', 'Faster inspection', 'Quick resolution'],
        metrics: ['First pass yield', 'Inspection time', 'Resolution time']
      },
      qualityImprovement: {
        weight: 15,
        drivers: ['Defect reduction', 'Process capability', 'Continuous improvement'],
        metrics: ['Defect rate', 'Cpk', 'Improvement rate']
      }
    },
    typicalROI: { min: 250, max: 800, paybackMonths: 6 },
    universalKPIs: [
      'Quality score',
      'Defect rate',
      'Customer satisfaction',
      'Cost of quality'
    ],
    adoptionFactors: ['Quality culture', 'Process maturity', 'Measurement systems']
  },
  
  {
    id: 'workforce_productivity',
    name: 'Workforce Productivity Pattern',
    category: 'strategic',
    targetFunction: 'HR/People/Workforce',
    problemSpace: [
      'Low productivity',
      'High turnover',
      'Skills gaps',
      'Employee engagement'
    ],
    valueThesis: 'Maximize human capital value through productivity enhancement',
    valueBuckets: {
      revenueGrowth: {
        weight: 30,
        drivers: ['Revenue per employee', 'Capacity expansion', 'Innovation output'],
        metrics: ['Revenue/FTE', 'Utilization rate', 'Innovation metrics']
      },
      costReduction: {
        weight: 40,
        drivers: ['Labor cost optimization', 'Turnover reduction', 'Training efficiency'],
        metrics: ['Labor cost ratio', 'Turnover rate', 'Training ROI']
      },
      riskMitigation: {
        weight: 10,
        drivers: ['Compliance', 'Knowledge retention', 'Succession planning'],
        metrics: ['Compliance rate', 'Knowledge transfer', 'Bench strength']
      },
      speedAgility: {
        weight: 15,
        drivers: ['Time to productivity', 'Skill development', 'Team velocity'],
        metrics: ['Onboarding time', 'Skill acquisition rate', 'Team performance']
      },
      qualityImprovement: {
        weight: 5,
        drivers: ['Work quality', 'Employee satisfaction', 'Culture enhancement'],
        metrics: ['Quality metrics', 'eNPS', 'Culture score']
      }
    },
    typicalROI: { min: 200, max: 500, paybackMonths: 8 },
    universalKPIs: [
      'Productivity index',
      'Employee engagement',
      'Turnover rate',
      'Revenue per employee'
    ],
    adoptionFactors: ['Change resistance', 'Training needs', 'Cultural fit']
  }
];

// Industry-specific overlays (extend universal patterns)
export interface IndustryOverlay {
  industry: string;
  specificDrivers: { [patternId: string]: string[] };
  industryMetrics: string[];
  regulatoryFactors: string[];
  competitiveDynamics: string;
}

export const INDUSTRY_OVERLAYS: IndustryOverlay[] = [
  {
    industry: 'Software/SaaS/DevOps',
    specificDrivers: {
      'operational_efficiency': ['CI/CD automation', 'Infrastructure as code', 'DevOps practices'],
      'digital_transformation': ['Cloud migration', 'Microservices', 'API-first architecture'],
      'quality_excellence': ['Code quality', 'Test coverage', 'Security scanning']
    },
    industryMetrics: ['Deployment frequency', 'MTTR', 'Lead time', 'Change failure rate'],
    regulatoryFactors: ['SOC2', 'ISO 27001', 'GDPR', 'HIPAA'],
    competitiveDynamics: 'Speed to market and developer productivity are key differentiators'
  },
  {
    industry: 'Agriculture/AgTech',
    specificDrivers: {
      'operational_efficiency': ['Precision farming', 'Drone automation', 'IoT sensors'],
      'revenue_acceleration': ['Yield optimization', 'Market timing', 'Supply chain integration'],
      'quality_excellence': ['Crop quality', 'Sustainability metrics', 'Traceability']
    },
    industryMetrics: ['Yield per acre', 'Resource efficiency', 'Crop quality score', 'Sustainability index'],
    regulatoryFactors: ['FDA', 'USDA', 'Organic certification', 'Environmental compliance'],
    competitiveDynamics: 'Sustainability and yield optimization drive competitive advantage'
  },
  {
    industry: 'Manufacturing/Industry 4.0',
    specificDrivers: {
      'operational_efficiency': ['Smart factory', 'Predictive maintenance', 'Digital twin'],
      'quality_excellence': ['Six Sigma', 'Zero defects', 'Statistical process control'],
      'digital_transformation': ['IIoT', 'MES integration', 'Real-time analytics']
    },
    industryMetrics: ['OEE', 'First pass yield', 'Cycle time', 'Inventory turns'],
    regulatoryFactors: ['ISO 9001', 'Industry-specific standards', 'Safety regulations'],
    competitiveDynamics: 'Efficiency and quality at scale determine market leadership'
  },
  {
    industry: 'Financial Services/FinTech',
    specificDrivers: {
      'operational_efficiency': ['Transaction processing', 'Straight-through processing', 'RPA'],
      'digital_transformation': ['Open banking', 'API economy', 'Blockchain'],
      'risk_mitigation': ['Fraud detection', 'AML/KYC', 'Credit risk modeling']
    },
    industryMetrics: ['Processing cost', 'Transaction speed', 'Error rate', 'Compliance score'],
    regulatoryFactors: ['Basel III', 'PSD2', 'AML regulations', 'Data privacy'],
    competitiveDynamics: 'Regulatory compliance and customer experience drive differentiation'
  },
  {
    industry: 'Retail/E-commerce',
    specificDrivers: {
      'revenue_acceleration': ['Personalization', 'Omnichannel', 'Dynamic pricing'],
      'operational_efficiency': ['Inventory optimization', 'Supply chain automation', 'Fulfillment'],
      'digital_transformation': ['Digital commerce', 'Mobile experience', 'Analytics']
    },
    industryMetrics: ['Conversion rate', 'AOV', 'Customer lifetime value', 'Inventory turnover'],
    regulatoryFactors: ['Consumer protection', 'Data privacy', 'PCI compliance'],
    competitiveDynamics: 'Customer experience and operational efficiency determine winners'
  },
  {
    industry: 'Energy/Utilities',
    specificDrivers: {
      'operational_efficiency': ['Grid optimization', 'Predictive maintenance', 'Smart metering'],
      'digital_transformation': ['Smart grid', 'Renewable integration', 'Energy storage'],
      'risk_mitigation': ['Reliability', 'Safety systems', 'Environmental compliance']
    },
    industryMetrics: ['Uptime', 'Efficiency ratio', 'Safety incidents', 'Carbon footprint'],
    regulatoryFactors: ['Environmental regulations', 'Safety standards', 'Grid codes'],
    competitiveDynamics: 'Sustainability and reliability are becoming key differentiators'
  },
  {
    industry: 'Logistics/Supply Chain',
    specificDrivers: {
      'operational_efficiency': ['Route optimization', 'Warehouse automation', 'Last-mile delivery'],
      'digital_transformation': ['Track and trace', 'Digital freight', 'Blockchain'],
      'quality_excellence': ['On-time delivery', 'Damage reduction', 'Service reliability']
    },
    industryMetrics: ['On-time delivery', 'Cost per mile', 'Utilization rate', 'Perfect order rate'],
    regulatoryFactors: ['Transportation regulations', 'Customs', 'Environmental standards'],
    competitiveDynamics: 'Speed, reliability, and cost efficiency drive competitive advantage'
  }
];

// Function to match pattern to any industry/use case
export function matchUniversalPattern(
  industry: string,
  problemDescription: string,
  targetFunction?: string
): {
  pattern: UniversalValuePattern;
  industryContext?: IndustryOverlay;
  confidence: number;
} {
  // Analyze problem description for keywords
  const problemLower = problemDescription.toLowerCase();
  
  // Score each pattern based on problem match
  const scores = UNIVERSAL_PATTERNS.map(pattern => {
    let score = 0;
    
    // Check problem space match
    pattern.problemSpace.forEach(problem => {
      if (problemLower.includes(problem.toLowerCase())) {
        score += 25;
      }
    });
    
    // Check target function match
    if (targetFunction && pattern.targetFunction.toLowerCase().includes(targetFunction.toLowerCase())) {
      score += 30;
    }
    
    // Check for value driver keywords
    const allDrivers = [
      ...pattern.valueBuckets.revenueGrowth.drivers,
      ...pattern.valueBuckets.costReduction.drivers,
      ...pattern.valueBuckets.speedAgility.drivers
    ];
    
    allDrivers.forEach(driver => {
      const driverWords = driver.toLowerCase().split(' ');
      driverWords.forEach(word => {
        if (word.length > 4 && problemLower.includes(word)) {
          score += 10;
        }
      });
    });
    
    return { pattern, score };
  });
  
  // Find best matching pattern
  const bestMatch = scores.sort((a, b) => b.score - a.score)[0];
  
  // Find industry overlay if exists
  const industryContext = INDUSTRY_OVERLAYS.find(overlay =>
    industry.toLowerCase().includes(overlay.industry.toLowerCase()) ||
    overlay.industry.toLowerCase().includes(industry.toLowerCase())
  );
  
  return {
    pattern: bestMatch.pattern,
    industryContext,
    confidence: Math.min(bestMatch.score, 100) / 100
  };
}

// Generate value model for ANY industry
export function generateUniversalValueModel(
  industry: string,
  solution: string,
  problemDescription: string,
  targetBuyer?: string
): {
  valueSplit: { [key: string]: number };
  primaryDrivers: string[];
  kpis: string[];
  expectedROI: { min: number; max: number; paybackMonths: number };
  valueMessage: string;
  industrySpecificFactors: string[];
} {
  const { pattern, industryContext, confidence } = matchUniversalPattern(
    industry,
    problemDescription,
    targetBuyer
  );
  
  // Build value split from pattern
  const valueSplit: { [key: string]: number } = {};
  Object.entries(pattern.valueBuckets).forEach(([key, bucket]) => {
    if (bucket.weight > 0) {
      valueSplit[key] = bucket.weight;
    }
  });
  
  // Collect all drivers
  const primaryDrivers: string[] = [];
  Object.values(pattern.valueBuckets).forEach(bucket => {
    if (bucket.weight >= 20) {
      primaryDrivers.push(...bucket.drivers);
    }
  });
  
  // Add industry-specific drivers if available
  if (industryContext && industryContext.specificDrivers[pattern.id]) {
    primaryDrivers.push(...industryContext.specificDrivers[pattern.id]);
  }
  
  // Combine KPIs
  const kpis = [...pattern.universalKPIs];
  if (industryContext) {
    kpis.push(...industryContext.industryMetrics.slice(0, 3));
  }
  
  // Generate value message
  let valueMessage = pattern.valueThesis;
  if (industryContext) {
    valueMessage += `. ${industryContext.competitiveDynamics}`;
  }
  
  // Industry-specific factors
  const industrySpecificFactors = industryContext ? [
    ...industryContext.regulatoryFactors.slice(0, 3),
    ...pattern.adoptionFactors
  ] : pattern.adoptionFactors;
  
  return {
    valueSplit,
    primaryDrivers: primaryDrivers.slice(0, 8), // Top 8 drivers
    kpis: kpis.slice(0, 6), // Top 6 KPIs
    expectedROI: pattern.typicalROI,
    valueMessage,
    industrySpecificFactors
  };
}

// Examples of usage
export const EXAMPLE_APPLICATIONS = [
  {
    industry: 'DevOps/CI-CD',
    solution: 'Continuous Integration Platform',
    problem: 'Slow deployment cycles and frequent production issues',
    expectedPattern: 'operational_efficiency',
    typicalValue: 'Reduce deployment time by 80%, reduce failures by 60%'
  },
  {
    industry: 'Agriculture',
    solution: 'Farming Drone System',
    problem: 'Inefficient crop monitoring and resource waste',
    expectedPattern: 'operational_efficiency',
    typicalValue: 'Increase yield by 20%, reduce water usage by 30%'
  },
  {
    industry: 'Construction',
    solution: 'Project Management Platform',
    problem: 'Project delays and cost overruns',
    expectedPattern: 'operational_efficiency',
    typicalValue: 'Reduce project delays by 40%, improve resource utilization by 25%'
  },
  {
    industry: 'Education',
    solution: 'Learning Management System',
    problem: 'Low student engagement and poor learning outcomes',
    expectedPattern: 'quality_excellence',
    typicalValue: 'Improve learning outcomes by 35%, increase engagement by 50%'
  },
  {
    industry: 'Legal',
    solution: 'Contract Automation Platform',
    problem: 'Manual contract review and high legal costs',
    expectedPattern: 'operational_efficiency',
    typicalValue: 'Reduce contract review time by 70%, cut legal costs by 40%'
  }
];
