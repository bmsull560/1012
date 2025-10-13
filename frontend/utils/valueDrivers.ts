// Value Driver Library - Based on AcuityMD Model

export interface ValueDriver {
  id: string;
  name: string;
  category: 'revenue_uplift' | 'cost_savings' | 'risk_mitigation';
  formula: string;
  inputs: InputParameter[];
  description: string;
  typicalImpact: number; // As percentage of total value
  confidenceLevel: number; // 0-1
  applicableIndustries: string[];
  productModules?: string[];
}

export interface InputParameter {
  id: string;
  name: string;
  type: 'number' | 'percentage' | 'currency';
  defaultValue: number;
  lowValue: number;
  highValue: number;
  unit?: string;
  description: string;
  source?: string; // Benchmark source
}

// Based on the AcuityMD Excel model
export const VALUE_DRIVERS: ValueDriver[] = [
  {
    id: 'new_surgeon_acquisition',
    name: 'New Surgeon Acquisition',
    category: 'revenue_uplift',
    formula: 'reps * adoption_rate * new_surgeons_per_rep * cases_per_surgeon * asp',
    description: 'Revenue from acquiring new surgeons through better targeting and peer networks',
    typicalImpact: 0.30,
    confidenceLevel: 0.85,
    applicableIndustries: ['MedTech', 'Medical Device', 'Orthopedics', 'Healthcare'],
    productModules: ['Targeting', 'Care Journeys'],
    inputs: [
      {
        id: 'reps',
        name: 'Number of Sales Reps',
        type: 'number',
        defaultValue: 20,
        lowValue: 10,
        highValue: 50,
        description: 'Total sales representatives in the territory'
      },
      {
        id: 'adoption_rate',
        name: 'Rep Adoption Rate',
        type: 'percentage',
        defaultValue: 0.80,
        lowValue: 0.60,
        highValue: 0.95,
        description: 'Percentage of reps actively using the system'
      },
      {
        id: 'new_surgeons_per_rep',
        name: 'New Surgeons per Rep per Year',
        type: 'number',
        defaultValue: 3.0,
        lowValue: 1.5,
        highValue: 5.0,
        description: 'Average new surgeon relationships developed annually'
      },
      {
        id: 'cases_per_surgeon',
        name: 'Cases per New Surgeon',
        type: 'number',
        defaultValue: 18,
        lowValue: 10,
        highValue: 30,
        description: 'Average procedures per new surgeon in first year'
      },
      {
        id: 'asp',
        name: 'Average Selling Price per Case',
        type: 'currency',
        defaultValue: 4500,
        lowValue: 3000,
        highValue: 7000,
        description: 'Revenue per surgical procedure'
      }
    ]
  },
  {
    id: 'share_gain_existing',
    name: 'Share Gain in Existing Accounts',
    category: 'revenue_uplift',
    formula: 'target_procedures * share_gain_pp * asp',
    description: 'Increased market share within current accounts through better intelligence',
    typicalImpact: 0.15,
    confidenceLevel: 0.75,
    applicableIndustries: ['MedTech', 'Medical Device', 'Healthcare'],
    productModules: ['Markets', 'Targeting'],
    inputs: [
      {
        id: 'target_procedures',
        name: 'Total Addressable Procedures',
        type: 'number',
        defaultValue: 12000,
        lowValue: 5000,
        highValue: 25000,
        description: 'Annual procedures in target accounts'
      },
      {
        id: 'share_gain_pp',
        name: 'Share Gain (percentage points)',
        type: 'percentage',
        defaultValue: 0.02,
        lowValue: 0.01,
        highValue: 0.04,
        description: 'Incremental market share capture'
      }
    ]
  },
  {
    id: 'asc_shift_capture',
    name: 'ASC Shift Capture',
    category: 'revenue_uplift',
    formula: 'target_procedures * asc_mix * asc_share_gain * asp',
    description: 'Capturing procedures shifting to ambulatory surgery centers',
    typicalImpact: 0.10,
    confidenceLevel: 0.70,
    applicableIndustries: ['Orthopedics', 'Surgery Centers'],
    productModules: ['Care Journeys'],
    inputs: [
      {
        id: 'asc_mix',
        name: 'ASC Mix of Procedures',
        type: 'percentage',
        defaultValue: 0.40,
        lowValue: 0.25,
        highValue: 0.60,
        description: 'Percentage of procedures in ASCs'
      },
      {
        id: 'asc_share_gain',
        name: 'ASC Share Gain',
        type: 'percentage',
        defaultValue: 0.015,
        lowValue: 0.005,
        highValue: 0.03,
        description: 'Additional share in ASC procedures'
      }
    ]
  },
  {
    id: 'sales_velocity',
    name: 'Sales Cycle Acceleration',
    category: 'revenue_uplift',
    formula: 'baseline_revenue * cycle_reduction * win_rate_lift',
    description: 'Faster deal velocity and improved win rates through better pipeline management',
    typicalImpact: 0.08,
    confidenceLevel: 0.65,
    applicableIndustries: ['All B2B'],
    productModules: ['Pipeline'],
    inputs: [
      {
        id: 'baseline_revenue',
        name: 'Current Annual Revenue',
        type: 'currency',
        defaultValue: 10000000,
        lowValue: 5000000,
        highValue: 50000000,
        description: 'Existing revenue base'
      },
      {
        id: 'cycle_reduction',
        name: 'Sales Cycle Reduction',
        type: 'percentage',
        defaultValue: 0.25,
        lowValue: 0.15,
        highValue: 0.40,
        description: 'Reduction in average sales cycle time'
      },
      {
        id: 'win_rate_lift',
        name: 'Win Rate Improvement',
        type: 'percentage',
        defaultValue: 0.02,
        lowValue: 0.01,
        highValue: 0.05,
        description: 'Increase in deal win rate'
      }
    ]
  },
  {
    id: 'contract_compliance',
    name: 'Contract Pull-Through',
    category: 'revenue_uplift',
    formula: 'on_contract_revenue * compliance_uplift',
    description: 'Improved contract compliance and reduced revenue leakage',
    typicalImpact: 0.12,
    confidenceLevel: 0.80,
    applicableIndustries: ['MedTech', 'Healthcare', 'Enterprise'],
    productModules: ['Contracts'],
    inputs: [
      {
        id: 'on_contract_revenue',
        name: 'On-Contract Eligible Revenue',
        type: 'currency',
        defaultValue: 12000000,
        lowValue: 5000000,
        highValue: 25000000,
        description: 'Revenue covered by contracts'
      },
      {
        id: 'compliance_uplift',
        name: 'Compliance Improvement',
        type: 'percentage',
        defaultValue: 0.05,
        lowValue: 0.02,
        highValue: 0.10,
        description: 'Increase in on-contract purchasing'
      }
    ]
  },
  {
    id: 'rep_productivity',
    name: 'Rep Time Savings',
    category: 'cost_savings',
    formula: 'reps * hours_saved_per_week * rep_hourly_rate * weeks_per_year * adoption_rate',
    description: 'Sales rep productivity gains from reduced admin and research time',
    typicalImpact: 0.15,
    confidenceLevel: 0.90,
    applicableIndustries: ['All B2B'],
    productModules: ['Targeting', 'Mobile', 'Integrations'],
    inputs: [
      {
        id: 'hours_saved_per_week',
        name: 'Hours Saved per Rep per Week',
        type: 'number',
        defaultValue: 6,
        lowValue: 3,
        highValue: 10,
        description: 'Admin and research time eliminated'
      },
      {
        id: 'rep_hourly_rate',
        name: 'Fully Loaded Rep Cost ($/hour)',
        type: 'currency',
        defaultValue: 90,
        lowValue: 60,
        highValue: 150,
        description: 'Total cost per rep hour including benefits'
      },
      {
        id: 'weeks_per_year',
        name: 'Working Weeks per Year',
        type: 'number',
        defaultValue: 48,
        lowValue: 46,
        highValue: 50,
        description: 'Annual working weeks'
      }
    ]
  },
  {
    id: 'faster_ramp',
    name: 'New Rep Ramp Acceleration',
    category: 'cost_savings',
    formula: '(months_saved / 12) * quota_per_rep * gross_margin * new_reps_per_year',
    description: 'Faster time to productivity for new sales hires',
    typicalImpact: 0.20,
    confidenceLevel: 0.75,
    applicableIndustries: ['All B2B'],
    productModules: ['Onboarding', 'Training', 'Targeting'],
    inputs: [
      {
        id: 'months_saved',
        name: 'Ramp Time Reduction (months)',
        type: 'number',
        defaultValue: 2,
        lowValue: 1,
        highValue: 4,
        description: 'Months saved in reaching full productivity'
      },
      {
        id: 'quota_per_rep',
        name: 'Annual Quota per Rep',
        type: 'currency',
        defaultValue: 1800000,
        lowValue: 1000000,
        highValue: 3000000,
        description: 'Annual sales target per rep'
      },
      {
        id: 'gross_margin',
        name: 'Gross Margin',
        type: 'percentage',
        defaultValue: 0.70,
        lowValue: 0.50,
        highValue: 0.85,
        description: 'Product gross margin percentage'
      },
      {
        id: 'new_reps_per_year',
        name: 'New Reps Hired Annually',
        type: 'number',
        defaultValue: 5,
        lowValue: 2,
        highValue: 15,
        description: 'Annual new hire count'
      }
    ]
  },
  {
    id: 'reduced_bad_demos',
    name: 'Fewer Bad Demos/Evaluations',
    category: 'cost_savings',
    formula: 'bad_demos_avoided * cost_per_bad_demo',
    description: 'Better qualification reduces wasted demos and evaluations',
    typicalImpact: 0.05,
    confidenceLevel: 0.70,
    applicableIndustries: ['MedTech', 'Enterprise Software'],
    productModules: ['Targeting', 'Care Journeys'],
    inputs: [
      {
        id: 'bad_demos_avoided',
        name: 'Bad Demos Avoided per Year',
        type: 'number',
        defaultValue: 25,
        lowValue: 10,
        highValue: 50,
        description: 'Unqualified demos eliminated'
      },
      {
        id: 'cost_per_bad_demo',
        name: 'Cost per Bad Demo',
        type: 'currency',
        defaultValue: 600,
        lowValue: 300,
        highValue: 1500,
        description: 'Total cost of wasted demo/eval'
      }
    ]
  },
  {
    id: 'data_spend_reduction',
    name: 'Reduced 3rd-Party Data Spend',
    category: 'cost_savings',
    formula: 'annual_data_spend_reduced',
    description: 'Elimination of external data and list purchases',
    typicalImpact: 0.08,
    confidenceLevel: 0.85,
    applicableIndustries: ['All B2B'],
    productModules: ['Markets', 'Targeting'],
    inputs: [
      {
        id: 'annual_data_spend_reduced',
        name: 'Annual Data Spend Reduction',
        type: 'currency',
        defaultValue: 100000,
        lowValue: 25000,
        highValue: 250000,
        description: 'Third-party data costs eliminated'
      }
    ]
  },
  {
    id: 'price_realization',
    name: 'Price Realization Improvement',
    category: 'revenue_uplift',
    formula: 'total_revenue * price_improvement_rate',
    description: 'Better pricing discipline and reduced discounting',
    typicalImpact: 0.05,
    confidenceLevel: 0.60,
    applicableIndustries: ['All B2B'],
    productModules: ['Contracts', 'Analytics'],
    inputs: [
      {
        id: 'total_revenue',
        name: 'Total Annual Revenue',
        type: 'currency',
        defaultValue: 20000000,
        lowValue: 5000000,
        highValue: 100000000,
        description: 'Total revenue base'
      },
      {
        id: 'price_improvement_rate',
        name: 'Price Realization Improvement',
        type: 'percentage',
        defaultValue: 0.0075,
        lowValue: 0.0025,
        highValue: 0.02,
        description: 'Reduction in unnecessary discounting'
      }
    ]
  }
];

// Calculation functions
export function calculateDriverValue(driver: ValueDriver, inputs: Map<string, number>): number {
  // Parse the formula and calculate
  // This is simplified - in production would use a proper expression parser
  let formula = driver.formula;
  
  driver.inputs.forEach(input => {
    const value = inputs.get(input.id) || input.defaultValue;
    formula = formula.replace(new RegExp(input.id, 'g'), value.toString());
  });
  
  // Use Function constructor to evaluate the formula
  try {
    // Add Math functions to the context
    const func = new Function('Math', `return ${formula}`);
    return func(Math);
  } catch (error) {
    console.error(`Error calculating ${driver.name}:`, error);
    return 0;
  }
}

export function calculateTotalValue(drivers: ValueDriver[], inputs: Map<string, number>): {
  totalBenefits: number;
  byCategory: Map<string, number>;
  byDriver: Map<string, number>;
} {
  const byCategory = new Map<string, number>();
  const byDriver = new Map<string, number>();
  let totalBenefits = 0;
  
  drivers.forEach(driver => {
    const value = calculateDriverValue(driver, inputs);
    byDriver.set(driver.id, value);
    
    const currentCategory = byCategory.get(driver.category) || 0;
    byCategory.set(driver.category, currentCategory + value);
    
    totalBenefits += value;
  });
  
  return { totalBenefits, byCategory, byDriver };
}

// Scenario generation
export function generateScenarios(drivers: ValueDriver[], baseInputs: Map<string, number>): {
  conservative: number;
  base: number;
  optimistic: number;
} {
  // Conservative: Use low values
  const conservativeInputs = new Map(baseInputs);
  drivers.forEach(driver => {
    driver.inputs.forEach(input => {
      conservativeInputs.set(input.id, input.lowValue);
    });
  });
  
  // Optimistic: Use high values
  const optimisticInputs = new Map(baseInputs);
  drivers.forEach(driver => {
    driver.inputs.forEach(input => {
      optimisticInputs.set(input.id, input.highValue);
    });
  });
  
  return {
    conservative: calculateTotalValue(drivers, conservativeInputs).totalBenefits,
    base: calculateTotalValue(drivers, baseInputs).totalBenefits,
    optimistic: calculateTotalValue(drivers, optimisticInputs).totalBenefits
  };
}

// NPV calculation
export function calculateNPV(
  yearlyBenefits: number[],
  yearlyC: number[],
  discountRate: number
): number {
  let npv = 0;
  
  for (let year = 0; year < yearlyBenefits.length; year++) {
    const netBenefit = yearlyBenefits[year] - yearlyC[year];
    const discountFactor = Math.pow(1 + discountRate, year + 1);
    npv += netBenefit / discountFactor;
  }
  
  return npv;
}

// Payback period
export function calculatePayback(
  initialCost: number,
  monthlyBenefit: number
): number {
  if (monthlyBenefit <= 0) return Infinity;
  return initialCost / monthlyBenefit;
}

// Industry benchmarks
export const INDUSTRY_BENCHMARKS = {
  'MedTech': {
    grossMargin: 0.70,
    salesCycle: 127,
    winRate: 0.23,
    repQuota: 1800000,
    adoptionRate: 0.80
  },
  'Healthcare': {
    grossMargin: 0.65,
    salesCycle: 145,
    winRate: 0.20,
    repQuota: 1500000,
    adoptionRate: 0.75
  },
  'Enterprise Software': {
    grossMargin: 0.85,
    salesCycle: 90,
    winRate: 0.28,
    repQuota: 2000000,
    adoptionRate: 0.85
  }
};

// Adoption ramp schedules
export const ADOPTION_RAMPS = {
  'conservative': [0.20, 0.40, 0.60, 0.80], // Q1-Q4
  'standard': [0.25, 0.50, 0.75, 1.00],
  'aggressive': [0.30, 0.60, 0.85, 1.00]
};

export function calculateAdoptionFactor(rampType: keyof typeof ADOPTION_RAMPS): number {
  const ramp = ADOPTION_RAMPS[rampType];
  return ramp.reduce((sum, val) => sum + val, 0) / ramp.length;
}
