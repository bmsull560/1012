# 📊 Value Model Analysis - What This Excel Teaches Us

**Source**: AcuityMD Value Model Framework (MedTech)  
**Analysis Date**: October 13, 2025

---

## 🎯 What This Model Does

This Excel framework helps **MedTech sales reps** quantify the ROI of selling AcuityMD (sales analytics platform) to hospitals/surgical centers like Rush University.

**The Problem It Solves**:
- Sales rep needs to justify $450K annual subscription
- CFO wants to see 3-year NPV and payback period
- Multiple stakeholders need different sensitivity scenarios

**Time to Build Manually**: 2-3 days of Excel work  
**Complexity**: 4 sheets, 60+ inputs, 15+ formulas  
**Output**: Business case with $3M+ ROI projection

---

## 📋 The Complete Workflow (What ValueVerse Should Automate)

### **Stage 1: Input Collection** (Currently: Manual Excel)

**Global Settings**:
- Discount rate (12%)
- Benefit realization ramp (25% → 50% → 75% → 100% over Q1-Q4)
- Analysis horizon (3 years)

**Commercial Footprint**:
- Number of sales reps (20)
- Fully loaded rep cost ($90/hour)
- Working weeks per year (48)

**Economics** (per procedure):
- Average selling price per case ($4,500)
- Gross margin (70%)
- Baseline market share (12%)
- Targeted annual procedures (12,000 cases)

**Targeting & Adoption**:
- New surgeons acquired per rep (3.0)
- Cases per new surgeon (18)
- Share gain in existing accounts (+2.0 pp)
- ASC shift capture (+1.5 pp)
- Sales cycle time reduction (25%)
- Pipeline win rate lift (+2.0 pp)
- Rep adoption rate (80%)

**Contracts & Pricing**:
- On-contract eligible revenue ($12M)
- Contract compliance uplift (+5.0 pp)
- Price realization improvement (+0.75%)

**Productivity**:
- Research hours saved per rep/week (6 hours)
- New rep ramp reduction (2 months)
- Quota per rep ($1.8M/year)
- Bad demos avoided (25/year @ $600 each)
- 3rd party data spend reduced ($100K/year)

**Costs**:
- Annual subscription ($450K)
- One-time onboarding ($75K)

---

## 💡 The Value Calculation Logic

### **Revenue Uplift Components**:

1. **New Surgeon Acquisition**:
   ```
   = Reps × Adoption Rate × New Surgeons/Rep × Cases/Surgeon × ASP
   = 20 × 80% × 3.0 × 18 × $4,500
   = $3.89M additional revenue
   ```

2. **Share Gain in Existing Accounts**:
   ```
   = Target Cases × Share Gain (pp) × ASP
   = 12,000 × 2.0% × $4,500
   = $1.08M additional revenue
   ```

3. **ASC Shift Capture** (outpatient procedures):
   ```
   = Target Cases × ASP × ASC Mix (40%) × ASC Gain (pp)
   = 12,000 × $4,500 × 40% × 1.5%
   = $324K additional revenue
   ```

4. **Faster Sales Cycles & Win Rate**:
   ```
   = Target Cases × Baseline Share × (Cycle Reduction × Win Lift) × ASP
   = 12,000 × 12% × (25% × 2.0%) × $4,500
   = $162K additional revenue
   ```

5. **Contract Pull-Through**:
   ```
   = On-Contract Revenue × Compliance Uplift
   = $12M × 5.0%
   = $600K additional revenue
   ```

**Total Revenue Uplift**: $6.06M

---

### **Cost Savings Components**:

1. **Rep Time Saved**:
   ```
   = Reps × Hours Saved/Week × Rep Rate × Weeks × Adoption
   = 20 × 6 × $90 × 48 × 80%
   = $414K savings
   ```

2. **Faster New-Rep Ramp**:
   ```
   = (Months Saved / 12) × Quota × Margin × Rep Count
   = (2 / 12) × $1.8M × 70% × 20
   = $420K value from faster productivity
   ```

3. **Fewer Bad Demos**:
   ```
   = Bad Demos Avoided × Cost per Demo
   = 25 × $600
   = $15K savings
   ```

4. **Reduced Data Spend**:
   ```
   = List/Data Spend Reduced
   = $100K savings
   ```

**Total Cost Savings**: $949K

---

### **Total Benefits vs Costs**:

**Year 1** (with ramp factor of 62.5% average):
- Total Benefits: $7.01M (full run-rate)
- Total Costs: $525K (subscription + onboarding)
- Net Benefit (full run-rate): $6.48M
- **Realized Net Benefit Y1**: $4.05M (after adoption ramp)

**Steady-State Years** (Years 2-3):
- Annual Benefits: $7.01M
- Annual Costs: $450K (subscription only)
- **Net Benefit**: $6.56M/year

**3-Year NPV** (12% discount rate):
- Year 1: $4.05M / 1.12 = $3.62M
- Year 2: $6.56M / 1.25 = $5.24M
- Year 3: $6.56M / 1.40 = $4.68M
- **Total NPV**: $13.54M

**Payback Period**: ~1.6 months

---

## 🎯 What ValueVerse Should Do Differently

Instead of manually building this Excel:

### **Conversational Flow**:

```
User: "Build value model for Rush University orthopedics"

Agent: "I found Rush University System for Health - they're a 
        $2.8B integrated delivery network with strong orthopedics. 
        I'll help you build a business case for [Your Product].
        
        First, tell me about your sales footprint:
        - How many reps sell into accounts like Rush?
        - What's the average deal size for your product?"

User: "We have 20 reps, typical deal is around $450K annual"

Agent: "Got it. For orthopedic implants at $450K/year, I'm seeing
        similar customers realize value through:
        
        1. Revenue Growth (66% of value)
           • New surgeon acquisition via better targeting
           • Share expansion in existing accounts
           • ASC shift capture (outpatient procedures)
           • Faster sales cycles
           • Contract compliance improvement
        
        2. Cost Reduction (34% of value)
           • Rep productivity gains
           • Faster new rep ramp time
           • Better qualification = fewer wasted demos
           • Reduced 3rd-party data costs
        
        Sound about right for Rush, or should I adjust?"

User: "Yes, especially the new surgeon acquisition"

Agent: "Perfect. Let me ask a few questions to size the opportunity..."

[Guided conversation continues]

Agent: "Based on your inputs, here's what I'm projecting for Rush:

        📊 3-Year Business Case:
        • Total Benefits: $7.0M/year (steady-state)
        • Investment: $525K (Year 1 including onboarding)
        • Net Year 1: $4.0M (after 62% ramp)
        • 3-Year NPV: $13.5M
        • Payback: ~2 months
        • ROI: 25.8x over 3 years
        
        The biggest value driver is new surgeon acquisition
        ($3.9M), followed by share gains ($1.1M).
        
        Want to stress-test any assumptions?"

User: "What if we only get 1.5 new surgeons per rep instead of 3?"

Agent: [Recalculates instantly]
        "In that scenario:
        • New surgeon value drops to $1.9M
        • Total Y1 benefit: $5.1M
        • 3-Year NPV: $11.2M
        • Still strong ROI of 21.3x
        
        The business case holds even in conservative scenarios."

User: "Generate the executive summary for the CFO meeting"

Agent: "Done! I've created:
        • 1-page executive summary (PDF)
        • 8-slide PowerPoint deck
        • Detailed Excel model (like the one you saw)
        • All with Rush-specific data and your branding
        
        Ready to download."
```

---

## 🏗️ Technical Implementation Needed

### **1. Value Driver Library**:

Create structured database of value drivers:

```typescript
interface ValueDriver {
  id: string;
  name: string;
  category: 'revenue' | 'cost' | 'risk';
  formula: string;
  inputs: InputParameter[];
  benchmarks: IndustryBenchmark[];
  confidenceLevel: number;
  applicableIndustries: string[];
  moduleMapping: string[]; // which product modules deliver this
}
```

Example drivers from this model:
- New surgeon acquisition (revenue)
- Share gain in existing accounts (revenue)
- ASC shift capture (revenue)
- Sales cycle reduction (revenue)
- Contract compliance (revenue)
- Rep time savings (cost)
- Ramp time reduction (cost)

### **2. Calculation Engine**:

Build formula evaluation system:

```typescript
class ROICalculator {
  evaluate(driver: ValueDriver, inputs: InputValues): number {
    // Parse formula
    // Substitute values
    // Apply industry benchmarks
    // Return calculated value
  }
  
  calculateSensitivity(driver: ValueDriver, range: number): ScenarioResults {
    // Low/base/high scenarios
  }
  
  aggregateMultipleDrivers(drivers: ValueDriver[]): TotalROI {
    // Sum across all drivers
    // Apply ramp factors
    // Calculate NPV
  }
}
```

### **3. Conversational Data Collection**:

Agent guides user through structured questions:

```typescript
interface ConversationFlow {
  stages: [
    {
      name: 'Company Research';
      questions: ['What company?', 'Confirm industry/size?'];
      outputs: CompanyProfile;
    },
    {
      name: 'Product Scoping';
      questions: ['Deal size?', 'Number of reps?', 'Current share?'];
      outputs: CommercialFootprint;
    },
    {
      name: 'Driver Selection';
      questions: ['Which value drivers apply?', 'Priority ranking?'];
      outputs: SelectedDrivers[];
    },
    {
      name: 'Data Collection';
      questions: dynamicQuestions(selectedDrivers);
      outputs: ModelInputs;
    },
    {
      name: 'Calculation';
      questions: ['Validate assumptions?'];
      outputs: ROIResults;
    },
    {
      name: 'Refinement';
      questions: ['What-if scenarios?'];
      outputs: Scenarios[];
    },
    {
      name: 'Output';
      questions: ['Which format?'];
      outputs: Documents[];
    }
  ];
}
```

### **4. Visual Output (Not Just Graph)**:

Build actual business case visualizer:

```typescript
<BusinessCaseCanvas>
  <ExecutiveSummary>
    <ValueProp>$13.5M NPV over 3 years</ValueProp>
    <KeyMetrics>
      <Metric label="Year 1 ROI" value="7.7x" />
      <Metric label="Payback" value="1.6 months" />
      <Metric label="Risk Level" value="Low" />
    </KeyMetrics>
  </ExecutiveSummary>
  
  <ValueWaterfallChart>
    <Bar label="Revenue Uplift" value={6.06M} breakdown={revComponents} />
    <Bar label="Cost Savings" value={0.95M} breakdown={costComponents} />
    <Bar label="Investment" value={-0.525M} />
    <Bar label="Net Benefit" value={6.48M} />
  </ValueWaterfallChart>
  
  <AssumptionsTable>
    {inputs.map(input => 
      <Row>
        <Input>{input.name}</Input>
        <Value editable>{input.value}</Value>
        <Benchmark>{input.industryAvg}</Benchmark>
        <Confidence>{input.confidence}</Confidence>
      </Row>
    )}
  </AssumptionsTable>
  
  <SensitivityChart>
    <TornadoDiagram drivers={topDrivers} />
  </SensitivityChart>
</BusinessCaseCanvas>
```

### **5. Document Generation**:

Export to multiple formats:

```typescript
class DocumentGenerator {
  async generateExecutiveSummary(model: ValueModel): Promise<PDF> {
    // 1-page summary with key metrics
  }
  
  async generatePowerPoint(model: ValueModel): Promise<PPTX> {
    // 8-12 slide deck with charts
  }
  
  async generateDetailedExcel(model: ValueModel): Promise<XLSX> {
    // Full model like the one you showed me
  }
  
  async generateQBRReport(model: ValueModel): Promise<PDF> {
    // Quarterly business review format
  }
}
```

---

## 🎯 The MVP Implementation Plan

### **Week 1: Value Driver Foundation**
- Build value driver database (start with 20 common drivers from this Excel)
- Implement ROI calculation engine
- Create formula parser and evaluator

### **Week 2: Conversational Collection**
- Build conversation state machine
- Implement Value Architect agent with question sequences
- Add input validation and industry benchmarking

### **Week 3: Visual Business Case**
- Create business case canvas component (NOT just a graph)
- Build value waterfall chart
- Add assumptions table with inline editing
- Real-time recalculation on changes

### **Week 4: Scenarios & Sensitivity**
- Implement what-if slider controls
- Build scenario comparison view
- Add tornado/sensitivity charts
- Lock and save multiple scenarios

### **Week 5: Document Export**
- PDF executive summary generator
- PowerPoint deck builder
- Excel detailed model export
- User testing with sales reps

---

## 📊 Success Criteria

**User can complete this workflow in 15 minutes**:

1. ✅ Type "Build value model for [Company]"
2. ✅ Agent researches company, suggests relevant drivers
3. ✅ Answer 8-10 guided questions
4. ✅ See live business case building in canvas
5. ✅ Use sliders to test 3-5 scenarios
6. ✅ Generate professional documents
7. ✅ Export in 3 formats (PDF, PPT, Excel)

**Output quality matches manually-built Excel**:
- Same level of financial rigor
- Industry-benchmarked assumptions
- Professional formatting
- Audit trail of calculations

**Time savings**:
- Manual: 2-3 days
- ValueVerse: 15 minutes
- **90% time reduction**

---

## 🔑 Key Insights from This Excel

1. **Value models are STRUCTURED** - not free-form
   - Fixed categories (revenue, cost, risk)
   - Known driver types
   - Standard formulas
   - Industry benchmarks

2. **Users need GUIDED input collection**
   - 60+ inputs is overwhelming
   - Need smart defaults and benchmarks
   - Validation prevents errors
   - Progressive disclosure of complexity

3. **Visual output is a BUSINESS CASE, not a graph**
   - Waterfall charts show value buildup
   - Tables show assumptions
   - Sensitivity shows risk
   - Multiple scenario comparison

4. **Scenarios are CRITICAL**
   - Low/base/high for every input
   - What-if analysis is how deals get sold
   - Conservative cases build credibility
   - Side-by-side comparison drives decisions

5. **Export is NON-NEGOTIABLE**
   - CFOs want Excel to validate formulas
   - Execs want PowerPoint for boards
   - Compliance wants PDF for audit trail
   - All must look professional

---

## 💡 This Changes Everything

The Excel you showed me proves that:

1. **The problem is REAL** - sales reps DO build these manually
2. **The logic is KNOWABLE** - formulas are deterministic, not magic
3. **The workflow is STRUCTURED** - not arbitrary
4. **The value is MASSIVE** - 90% time savings is transformative
5. **The output is SPECIFIC** - not "show a graph" but "generate business case"

This is what ValueVerse should do - turn 2-3 days of Excel work into a 15-minute conversation.

---

**Next Step**: Build ONE complete driver with full workflow, then replicate for others.

**Start with**: "New Surgeon Acquisition" driver
- Why: Largest value component ($3.9M of $7M)
- Formula: Clear and testable
- Inputs: Well-defined (reps, adoption, surgeons, cases, ASP)
- Benchmarks: Available from industry data
- Output: Single number that can be verified

Once this ONE driver works end-to-end (conversation → calculation → visualization → export), replicate the pattern for the other 14 drivers.
