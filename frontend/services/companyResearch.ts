// Company Research Service
// Fetches real company data from various sources

export interface CompanyData {
  name: string;
  website?: string;
  industry: string;
  subIndustry?: string;
  size: string;
  revenue?: number;
  employees?: number;
  description: string;
  headquarters?: string;
  founded?: number;
  publiclyTraded?: boolean;
  ticker?: string;
  marketCap?: number;
  products?: string[];
  competitors?: string[];
  recentNews?: string[];
  keyMetrics?: {
    annualRevenue?: number;
    revenueGrowth?: number;
    grossMargin?: number;
    operatingMargin?: number;
    customerCount?: number;
    marketShare?: number;
  };
}

// Mock API service - in production, this would call real APIs
class CompanyResearchService {
  // Scrape company website for basic information
  async scrapeWebsite(url: string): Promise<Partial<CompanyData>> {
    // In production, this would use a scraping service or API
    // For now, we'll parse the URL and return relevant mock data
    
    const domain = new URL(url).hostname.replace('www.', '');
    
    // Mock implementation - would actually scrape in production
    const mockData: { [key: string]: Partial<CompanyData> } = {
      'anikatx.com': {
        name: 'Anika Therapeutics',
        industry: 'Medical Device',
        subIndustry: 'Orthopedics - Joint Preservation',
        size: 'Mid-Cap',
        revenue: 160000000, // $160M
        employees: 150,
        description: 'Anika Therapeutics is a global joint preservation company that develops, manufactures, and commercializes therapeutic products based on hyaluronic acid.',
        headquarters: 'Bedford, MA',
        founded: 1992,
        publiclyTraded: true,
        ticker: 'ANIK',
        marketCap: 450000000,
        products: ['Monovisc', 'Orthovisc', 'Cingal', 'Hyalofast'],
        keyMetrics: {
          annualRevenue: 160000000,
          revenueGrowth: 0.12,
          grossMargin: 0.68,
          operatingMargin: 0.15,
          customerCount: 500,
          marketShare: 0.08
        }
      },
      'rush.edu': {
        name: 'Rush University Medical Center',
        industry: 'Healthcare Provider',
        subIndustry: 'Academic Medical Center',
        size: 'Large Enterprise',
        revenue: 2800000000, // $2.8B
        employees: 12000,
        description: 'Rush University Medical Center is a leading academic medical center comprising Rush University Medical Center, Rush University, Rush Oak Park Hospital and Rush Health.',
        headquarters: 'Chicago, IL',
        founded: 1837,
        publiclyTraded: false,
        products: ['Orthopedic Surgery', 'Neurosurgery', 'Cancer Care', 'Heart Care'],
        keyMetrics: {
          annualRevenue: 2800000000,
          revenueGrowth: 0.08,
          customerCount: 750000, // patients
          marketShare: 0.12 // Chicago market
        }
      },
      'zimmerbiomet.com': {
        name: 'Zimmer Biomet',
        industry: 'Medical Device',
        subIndustry: 'Orthopedic Implants',
        size: 'Large Cap',
        revenue: 7800000000, // $7.8B
        employees: 20000,
        description: 'Zimmer Biomet is a global leader in musculoskeletal healthcare, offering a comprehensive portfolio of products for joint reconstruction, sports medicine, spine, dental, and trauma.',
        headquarters: 'Warsaw, IN',
        founded: 1927,
        publiclyTraded: true,
        ticker: 'ZBH',
        marketCap: 25000000000,
        products: ['Knee Implants', 'Hip Implants', 'S.E.T.', 'Rosa Robotics'],
        keyMetrics: {
          annualRevenue: 7800000000,
          revenueGrowth: 0.06,
          grossMargin: 0.71,
          operatingMargin: 0.18,
          customerCount: 12000, // hospitals
          marketShare: 0.27
        }
      }
    };
    
    return mockData[domain] || {
      name: this.extractCompanyName(domain),
      website: url,
      industry: 'Healthcare',
      description: `Leading healthcare organization focused on delivering innovative solutions.`
    };
  }
  
  // Search for company using various APIs
  async searchCompany(query: string): Promise<CompanyData[]> {
    // This would integrate with multiple APIs in production:
    // - Clearbit API
    // - LinkedIn API
    // - Crunchbase API
    // - Google Knowledge Graph
    // - SEC EDGAR (for public companies)
    
    const searchResults: CompanyData[] = [
      {
        name: 'Anika Therapeutics, Inc.',
        website: 'https://www.anikatx.com',
        industry: 'Medical Device',
        subIndustry: 'Orthopedics - Joint Preservation',
        size: '$450M Market Cap',
        revenue: 160000000,
        employees: 150,
        description: 'Global joint preservation company developing HA-based therapeutic products for orthopedics.',
        headquarters: 'Bedford, MA',
        founded: 1992,
        publiclyTraded: true,
        ticker: 'ANIK',
        marketCap: 450000000,
        products: ['Monovisc', 'Orthovisc', 'Cingal'],
        competitors: ['Sanofi', 'Ferring', 'Bioventus'],
        keyMetrics: {
          annualRevenue: 160000000,
          revenueGrowth: 0.12,
          grossMargin: 0.68,
          operatingMargin: 0.15,
          customerCount: 500,
          marketShare: 0.08
        }
      },
      {
        name: 'Rush University System for Health',
        website: 'https://www.rush.edu',
        industry: 'Healthcare Provider',
        subIndustry: 'Integrated Delivery Network',
        size: '$2.8B Revenue',
        revenue: 2800000000,
        employees: 12000,
        description: 'Leading academic medical center with strong orthopedics and neurosurgery programs.',
        headquarters: 'Chicago, IL',
        founded: 1837,
        publiclyTraded: false,
        products: ['Orthopedic Surgery', 'Neurosurgery', 'Cancer Care'],
        competitors: ['Northwestern Medicine', 'UChicago Medicine', 'Advocate Aurora'],
        keyMetrics: {
          annualRevenue: 2800000000,
          revenueGrowth: 0.08,
          customerCount: 750000,
          marketShare: 0.12
        }
      }
    ];
    
    // Filter based on query
    const lowerQuery = query.toLowerCase();
    return searchResults.filter(company => 
      company.name.toLowerCase().includes(lowerQuery) ||
      company.description.toLowerCase().includes(lowerQuery)
    );
  }
  
  // Get industry-specific metrics and benchmarks
  async getIndustryBenchmarks(industry: string): Promise<any> {
    const benchmarks: { [key: string]: any } = {
      'Medical Device': {
        averageGrossMargin: 0.70,
        averageSalesGrowth: 0.08,
        averageRepQuota: 2000000,
        averageDealSize: 500000,
        salesCycleDays: 180,
        winRate: 0.25,
        customerRetention: 0.92,
        typicalBudgetCycle: 'Annual',
        decisionMakers: 5,
        competitorsPerDeal: 3
      },
      'Healthcare Provider': {
        averageOperatingMargin: 0.03,
        averageRevenue: 500000000,
        averagePatientVolume: 100000,
        averageLengthOfStay: 4.5,
        readmissionRate: 0.15,
        patientSatisfaction: 4.2,
        physicianCount: 500,
        bedCount: 400,
        typicalBudgetCycle: 'Annual',
        decisionMakers: 8
      },
      'Pharmaceuticals': {
        averageGrossMargin: 0.80,
        rdAsPercentOfSales: 0.18,
        averageDrugDevelopmentCost: 1000000000,
        averageTimeToMarket: 10,
        patentLife: 20,
        genericPenetration: 0.90,
        averageSalesForce: 1000,
        typicalBudgetCycle: 'Quarterly',
        decisionMakers: 7
      }
    };
    
    return benchmarks[industry] || benchmarks['Medical Device'];
  }
  
  // Enrich company data with additional sources
  async enrichCompanyData(companyName: string, website?: string): Promise<CompanyData> {
    // Start with search results
    const searchResults = await this.searchCompany(companyName);
    let companyData = searchResults[0] || {
      name: companyName,
      industry: 'Healthcare',
      size: 'Unknown',
      description: 'Company information not available',
      website: website
    };
    
    // If we have a website, scrape it for additional info
    if (website) {
      const scrapedData = await this.scrapeWebsite(website);
      companyData = { ...companyData, ...scrapedData };
    }
    
    // Get industry benchmarks
    const benchmarks = await this.getIndustryBenchmarks(companyData.industry);
    
    // Estimate missing metrics based on industry benchmarks
    if (!companyData.keyMetrics) {
      companyData.keyMetrics = {};
    }
    
    if (!companyData.keyMetrics.grossMargin && benchmarks.averageGrossMargin) {
      companyData.keyMetrics.grossMargin = benchmarks.averageGrossMargin;
    }
    
    if (!companyData.keyMetrics.revenueGrowth && benchmarks.averageSalesGrowth) {
      companyData.keyMetrics.revenueGrowth = benchmarks.averageSalesGrowth;
    }
    
    return companyData;
  }
  
  // Extract company name from domain
  private extractCompanyName(domain: string): string {
    // Remove common TLDs and clean up
    const name = domain
      .replace(/\.(com|org|edu|net|io|ai|co|biz|info).*$/, '')
      .replace(/-/g, ' ')
      .replace(/_/g, ' ');
    
    // Capitalize words
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
  
  // Analyze company for value model recommendations
  async analyzeForValueModel(company: CompanyData): Promise<{
    recommendedDrivers: string[];
    industryContext: string;
    keyOpportunities: string[];
    typicalDealSize: number;
    salesCycle: number;
  }> {
    // Analyze based on company characteristics
    const analysis = {
      recommendedDrivers: [] as string[],
      industryContext: '',
      keyOpportunities: [] as string[],
      typicalDealSize: 500000,
      salesCycle: 180
    };
    
    // Industry-specific recommendations
    if (company.industry === 'Medical Device') {
      analysis.recommendedDrivers = [
        'new_surgeon_acquisition',
        'share_gain_existing',
        'asc_shift_capture',
        'contract_compliance',
        'rep_productivity'
      ];
      analysis.industryContext = 'Medical device companies typically see 60-70% value from revenue growth (new accounts, share gain) and 30-40% from operational efficiency.';
      analysis.keyOpportunities = [
        'ASC migration capturing 40% of procedures',
        'Surgeon adoption through KOL targeting',
        'Contract compliance improvement of 5-8%',
        'Rep productivity gains of 15-20%'
      ];
      analysis.typicalDealSize = 750000;
      analysis.salesCycle = 180;
    } else if (company.industry === 'Healthcare Provider') {
      analysis.recommendedDrivers = [
        'rep_productivity',
        'contract_compliance',
        'faster_ramp',
        'data_spend_reduction'
      ];
      analysis.industryContext = 'Healthcare providers focus on operational efficiency (60%) and cost reduction (40%) given margin pressures.';
      analysis.keyOpportunities = [
        'Supply chain optimization saving 2-3%',
        'Clinical workflow efficiency gains',
        'Reduced readmissions through better care coordination',
        'Physician preference item standardization'
      ];
      analysis.typicalDealSize = 1500000;
      analysis.salesCycle = 240;
    } else {
      // Generic healthcare
      analysis.recommendedDrivers = [
        'new_surgeon_acquisition',
        'rep_productivity',
        'sales_velocity',
        'contract_compliance'
      ];
      analysis.industryContext = 'Healthcare organizations typically balance growth initiatives (50%) with efficiency improvements (50%).';
      analysis.keyOpportunities = [
        'Digital transformation opportunities',
        'Market expansion into adjacent segments',
        'Operational excellence initiatives',
        'Value-based care transitions'
      ];
    }
    
    // Adjust based on company size
    if (company.revenue && company.revenue > 1000000000) {
      analysis.typicalDealSize *= 2; // Larger companies, bigger deals
      analysis.salesCycle *= 1.5; // Longer sales cycles
    } else if (company.revenue && company.revenue < 100000000) {
      analysis.typicalDealSize *= 0.5; // Smaller deals
      analysis.salesCycle *= 0.75; // Faster decisions
    }
    
    return analysis;
  }
}

// Export singleton instance
export const companyResearch = new CompanyResearchService();
