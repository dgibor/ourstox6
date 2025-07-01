import pandas as pd

# Define file path
large_missing_path = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\large_missing.csv'

# Dictionary to hold all researched data
# Manually ensuring proper CSV escaping for description and business_model fields
all_researched_data = {
    'AEP': {
        'description': "American Electric Power (AEP) is a major American electric utility company that generates, transmits, and distributes electricity to over 5 million customers across 11 states in the United States. The company operates a vast electricity transmission system, spanning nearly 39,000 miles, which is the largest in the nation. AEP is also a significant electricity generator, with approximately 38,000 megawatts of generating capacity, utilizing a diverse mix of sources including coal, lignite, natural gas, wind, solar, nuclear, and hydroelectric power.",
        'business_model': "AEP's business model primarily revolves around the sale and distribution of electricity to residential, commercial, and industrial customers. Key activities within its business model include power generation, transmission, and distribution, alongside customer service and ensuring regulatory compliance.",
        'moat_1': "Extensive Transmission and Distribution Network",
        'moat_2': "Diverse Energy Portfolio",
        'moat_3': "Regulatory Framework",
        'moat_4': "High Switching Costs",
        'peer_a': "DUK",
        'peer_b': "EXC",
        'peer_c': "SO"
    },
    'AFRM': {
        'description': "Affirm is a fintech company specializing in \"Buy Now, Pay Later\" (BNPL) services, offering point-of-sale loans to consumers and additional services to retailers.",
        'business_model': "Affirm's business model is centered on facilitating credit at the point of sale, generating revenue through merchant fees, interest income, loan sales, interchange fees, and servicing income.",
        'moat_1': "Proprietary Underwriting Models",
        'moat_2': "Integrated Partnerships",
        'moat_3': "No Late Fees/Hidden Fees",
        'moat_4': "First-Mover Advantage/Data",
        'peer_a': "Afterpay",
        'peer_b': "Klarna",
        'peer_c': "Sezzle"
    },
    'AI': {
        'description': "C3.ai Inc. is a technology company based in the United States that specializes in providing Enterprise AI software to accelerate digital transformation for organizations globally.",
        'business_model': "C3.ai's business model is primarily centered on a subscription-based revenue model, with additional revenue generated from consumption-based services and professional services.",
        'moat_1': "Proprietary AI Technology",
        'moat_2': "Customer Switching Costs",
        'moat_3': "High Customer Retention Rate",
        'moat_4': "",
        'peer_a': "MSFT",
        'peer_b': "ORCL",
        'peer_c': "NOW"
    },
    'AKRO': {
        'description': "Akero Therapeutics Inc. is a clinical-stage biotechnology company focused on developing transformative treatments for serious metabolic diseases with high unmet medical needs, particularly non-alcoholic steatohepatitis (NASH), also known as metabolic dysfunction-associated steatohepatitis (MASH).",
        'business_model': "Akero's business model is research-driven and centers on the development and potential commercialization of innovative therapies, primarily through R&D, clinical development, strategic partnerships, and future product sales.",
        'moat_1': "Innovative Pipeline",
        'moat_2': "Strong Clinical Data",
        'moat_3': "Intellectual Property",
        'moat_4': "Strategic Partnerships",
        'peer_a': "Intercept Pharmaceuticals",
        'peer_b': "Madrigal Pharmaceuticals",
        'peer_c': "Genfit"
    },
    'ALNY': {
        'description': "Alnylam Pharmaceuticals, Inc. is an American biopharmaceutical company that specializes in the discovery, development, and commercialization of RNA interference (RNAi) therapeutics. Founded in 2002 and headquartered in Cambridge, Massachusetts, Alnylam is recognized as a pioneer in the field of RNAi technology, which involves \"silencing\" specific genes responsible for disease progression.",
        'business_model': "Alnylam's business model is centered on integrating cutting-edge science with a patient-centric approach to deliver innovative treatments, particularly for rare genetic diseases. Key aspects include R&D, strategic partnerships, product sales, licensing agreements, and milestone payments/royalties.",
        'moat_1': "Extensive Intellectual Property and Patents",
        'moat_2': "First-Mover Advantage",
        'moat_3': "Reproducible Research Strategy and Diverse Pipeline",
        'moat_4': "Strategic Collaborations",
        'peer_a': "Ionis Pharmaceuticals",
        'peer_b': "United Therapeutics",
        'peer_c': "Vertex Pharmaceuticals"
    },
    'ALSN': {
        'description': "Allison Transmission Holdings Inc. is an American manufacturer of commercial-duty automatic transmissions and hybrid propulsion systems. The company designs, manufactures, and distributes vehicle propulsion solutions for commercial and defense vehicles globally.",
        'business_model': "Allison Transmission Holdings Inc. generates revenue through product sales (to OEMs and end-users), aftermarket services (parts, support, maintenance, repair), and sales of remanufactured transmissions. Their model emphasizes R&D, vertical integration, customer support, and strong OEM relationships.",
        'moat_1': "Extensive Intellectual Property and Patents",
        'moat_2': "First-Mover Advantage",
        'moat_3': "Strong Brand Reputation",
        'moat_4': "High Switching Costs",
        'peer_a': "CAT",
        'peer_b': "TWIN",
        'peer_c': "DAN"
    },
    'AMG': {
        'description': "Affiliated Managers Group, Inc. (AMG) is an American financial services firm headquartered in West Palm Beach, Florida, founded in 1993. It operates as a global asset management company.",
        'business_model': "AMG's business model is centered on a unique, decentralized partnership approach. Key aspects include equity investments in independent investment management firms, preservation of autonomy for affiliates, strategic support, long-term partnerships, and diversified growth drivers.",
        'moat_1': "Decentralized Operating Model",
        'moat_2': "Diverse Affiliate Base",
        'moat_3': "Strategic Support and Resources",
        'moat_4': "Alignment of Interests",
        'peer_a': "TROW",
        'peer_b': "ARCC",
        'peer_c': "BEN"
    },
    'AMT': {
        'description': "American Tower Corporation (ATC) is a global real estate investment trust (REIT) that specializes in communications infrastructure. The company's primary business involves owning, operating, and developing multi-tenant communications real estate, including wireless and broadcast towers, distributed antenna systems (DAS), managed rooftops, and data center facilities.",
        'business_model': "American Tower's business model is centered on a \"shared infrastructure\" or \"neutral hosting\" approach. This involves acquiring, developing, and maintaining communication sites, which are then leased to multiple tenants through long-term, non-cancellable lease agreements with built-in escalators.",
        'moat_1': "Efficient Scale and High Barriers to Entry",
        'moat_2': "High Switching Costs",
        'moat_3': "Extensive Portfolio and Global Reach",
        'moat_4': "Long-Term Contracts and Stable Cash Flows",
        'peer_a': "CCI",
        'peer_b': "SBAC",
        'peer_c': "CLNX"
    },
    'ARCC': {
        'description': "Ares Capital Corporation (ARCC) is a specialty finance company that operates as a Business Development Company (BDC). It focuses on providing direct loans and other investments to private middle-market companies in the United States.",
        'business_model': "Ares Capital's business model revolves around filling a financing gap for middle-market companies that are often underserved by traditional banks. They primarily invest in direct senior secured loans, manage their portfolio actively, and source investments through diverse channels.",
        'moat_1': "Scale and Diversification",
        'moat_2': "Experienced Management Team",
        'moat_3': "Strong Relationships",
        'moat_4': "Alternative Investment Expertise",
        'peer_a': "MAIN",
        'peer_b': "GBDC",
        'peer_c': "HTGC"
    },
    'ARLP': {
        'description': "Alliance Resource Partners, L.P. (ARLP) is a diversified natural resource company primarily engaged in coal mining, production, and marketing in the United States. It is currently the second-largest coal producer in the eastern United States.",
        'business_model': "ARLP's business model is centered on the production and marketing of coal, supplemented by royalty income from its mineral interests. Key aspects include coal production and marketing, long-term supply agreements, oil and gas royalties, and its Master Limited Partnership (MLP) structure.",
        'moat_1': "Strategic Logistics and Asset Location",
        'moat_2': "Export Optionality",
        'moat_3': "Focus on Illinois Basin",
        'moat_4': "Conservative Management and Strong Balance Sheet",
        'peer_a': "Arch Coal",
        'peer_b': "CONSOL Energy",
        'peer_c': "Peabody Energy Corporation"
    },
    'ARM': {
        'description': "Arm Holdings plc is a British semiconductor and software design company headquartered in Cambridge, England. Its primary business revolves around the design of central processing unit (CPU) cores that implement the ARM architecture family of instruction sets.",
        'business_model': "Arm's business model is unique within the semiconductor industry as it focuses on intellectual property (IP) licensing rather than manufacturing its own physical chips. It generates revenue through a dual stream of licensing fees and royalties.",
        'moat_1': "Licensing Business Model",
        'moat_2': "Extensive IP Library",
        'moat_3': "Dominant Market Position and Ecosystem",
        'moat_4': "High Switching Costs",
        'peer_a': "Qualcomm",
        'peer_b': "Nvidia",
        'peer_c': "Intel"
    },
    'ASTS': {
        'description': "AST SpaceMobile Inc. is a satellite designer and manufacturer focused on building a global cellular broadband network in space. This network, known as the SpaceMobile Service, is designed to provide cost-effective, high-speed cellular broadband services directly to standard, unmodified mobile devices, including 2G, 4G-LTE, and 5G phones, even in areas without terrestrial cellular coverage. The company aims to eliminate connectivity gaps faced by mobile subscribers.",
        'business_model': "AST SpaceMobile's business model revolves around a wholesale approach. Instead of selling mobile plans or devices directly to consumers, the company partners with mobile network operators (MNOs) globally. They plan to sell access to their satellite network to these MNOs, who then offer extended coverage services to their end-users. Revenue is expected to be based on capacity usage or per-subscriber fees charged to the MNOs.",
        'moat_1': "Patented Technology for Direct-to-Standard-Phone Connectivity",
        'moat_2': "Strategic Agreements for Spectrum Access",
        'moat_3': "High Switching Costs (for MNOs)",
        'moat_4': "",
        'peer_a': "SpaceX's Starlink",
        'peer_b': "Amazon's Project Kuiper",
        'peer_c': "OneWeb"
    },
    'AVA': {
        'description': "Avista Corporation is an American energy company that operates as an electric and natural gas utility. Headquartered in Spokane, Washington, it produces, transmits, and distributes electricity, and supplies natural gas on both retail and wholesale bases.",
        'business_model': "Avista Corporation's business model is primarily based on its regulated utility operations. It generates revenue by selling electricity and natural gas to its customer base within its defined service territories. A key aspect of its model is that its earnings are largely determined by rates approved by state regulatory commissions, which are based on allowed costs and a return on invested capital. This regulated monopoly status provides a stable customer base and predictable revenue streams.",
        'moat_1': "Virtual Monopoly",
        'moat_2': "Diversified Energy Portfolio",
        'moat_3': "Recession Resilience",
        'moat_4': "Strategic Investments",
        'peer_a': "BKH",
        'peer_b': "MDU",
        'peer_c': "SRE"
    },
    'AVTR': {
        'description': "Avantor Inc. is a global provider of mission-critical products and services for customers in the life sciences, advanced technologies, and applied materials industries.",
        'business_model': "Avantor's business model is centered on providing end-to-end solutions that integrate products, services, and expertise. The company generates revenue through the sale of its extensive product portfolio and value-added services.",
        'moat_1': "Extensive Global Supply Chain Network",
        'moat_2': "Advanced Manufacturing Capabilities",
        'moat_3': "Strategic Partnerships and Access to Advanced Technologies",
        'moat_4': "Favorable Mix of Consumables and Platform Improvements",
        'peer_a': "Thermo Fisher Scientific Inc.",
        'peer_b': "Agilent Technologies,Inc.",
        'peer_c': "Keysight Technologies"
    },
    'AXS': {
        'description': "AXIS Capital Holdings Limited is a global provider of specialty insurance and reinsurance solutions, headquartered in Pembroke, Bermuda. The company operates through its two primary segments: AXIS Insurance and AXIS Reinsurance.",
        'business_model': "AXIS Capital's business model centers on providing tailored risk management solutions while maintaining a disciplined underwriting approach. The company generates revenue through premiums collected from its insurance and reinsurance products, with a portion invested for additional income.",
        'moat_1': "Specialty Focus",
        'moat_2': "Underwriting Excellence",
        'moat_3': "Innovation and Technology Investment",
        'moat_4': "Diversified Portfolio and Global Reach",
        'peer_a': "WRB",
        'peer_b': "MKL",
        'peer_c': "CINF"
    },
    'AXSM': {
        'description': "Axsome Therapeutics Inc. is a biopharmaceutical company focused on developing and delivering novel therapies for central nervous system (CNS) disorders with limited treatment options.",
        'business_model': "Axsome Therapeutics employs a research-driven business model focused on innovation and efficiency. Its revenue generation is primarily driven by product sales, pipeline development, and strategic partnerships.",
        'moat_1': "Innovative Pipeline",
        'moat_2': "Strong Clinical Data and Regulatory Success",
        'moat_3': "Strategic Partnerships",
        'moat_4': "Focus on Unmet Medical Needs",
        'peer_a': "Biogen",
        'peer_b': "Eli Lilly",
        'peer_c': "Jazz Pharmaceuticals"
    },
    'BAC-PK': {
        'description': "Bank of America Corporation (BofA or BoA) is an American multinational investment bank and financial services holding company. It is headquartered in Charlotte, North Carolina, with auxiliary headquarters in Manhattan.",
        'business_model': "Bank of America operates a diversified business model through four key segments: Consumer Banking, Global Wealth & Investment Management (GWIM), Global Banking, and Global Markets. Its revenue model is designed to generate income from multiple sources, primarily interest income from loans and non-interest income from fees for investment banking, wealth management, and other services.",
        'moat_1': "High Switching Costs",
        'moat_2': "Strong Brand Identity",
        'moat_3': "Cost Advantages",
        'moat_4': "Efficient Scale",
        'peer_a': "JPM",
        'peer_b': "WFC",
        'peer_c': "C"
    },
    'BALL': {
        'description': "Ball Corporation is an American aluminum manufacturing company headquartered in Westminster, Colorado. It is a global supplier of sustainable aluminum packaging solutions for various industries, including beverages, personal care, and household products.",
        'business_model': "Ball Corporation's business model primarily revolves around the sale of its aluminum packaging products and related services to multinational beverage, personal care, and household product companies worldwide. Key aspects include sustainable packaging solutions, diverse product range, global reach, strategic partnerships and acquisitions, and a focus on aluminum packaging.",
        'moat_1': "Efficient Scale",
        'moat_2': "Intangible Assets",
        'moat_3': "Market Leadership and Customer Retention",
        'moat_4': "Sustainability Focus",
        'peer_a': "Crown Holdings, Inc.",
        'peer_b': "Ardagh Group",
        'peer_c': "Silgan Holdings"
    },
    'BANF': {
        'description': "BancFirst Corporation is an Oklahoma-based financial services holding company that operates primarily through its subsidiaries: BancFirst (an Oklahoma state-chartered bank), Pegasus Bank and Worthington Bank (both Texas state-chartered banks), and BancFirst Insurance Services, Inc. (an independent insurance agency). The company provides a wide range of retail and commercial banking services, including various types of lending (commercial, real estate, energy, agricultural, consumer, residential mortgage, auto, personal, home equity), depository and funds transfer services, cash management, trust services, and insurance services. BancFirst serves retail customers, small to medium-sized businesses, governmental organizations, financial institutions, and individual and corporate clients. It maintains a significant presence in Oklahoma with over 100 service locations and over 250 ATMs, and also operates in the Dallas and Fort Worth Metroplex areas in Texas.",
        'business_model': "BancFirst's business model is centered on a \"super community bank\" approach, which involves managing its community banking offices on a decentralized basis. This decentralized structure allows local offices substantial autonomy in credit and pricing decisions, enabling them to be highly responsive to local customer needs and foster strong customer relationships. The company's strategy is to offer a comprehensive suite of banking services to both retail customers and small to medium-sized businesses. BancFirst primarily generates revenue through its net interest margin (NIM), which is the difference between the interest earned on its loans and securities and the interest paid on deposits and borrowings. Additionally, noninterest income from sources such as deposit service charges, trust fees, mortgage banking, and insurance commissions provides a crucial secondary revenue stream, diversifying its income. The company is also a prominent lender in various programs, notably being Oklahoma's leading originator of Small Business Administration (SBA) Loans for 34 consecutive years and the top in-state originator under the Farm Loan Program.",
        'moat_1': "Dominant Oklahoma Presence",
        'moat_2': "Relationship Banking and High-Touch Service",
        'moat_3': "Broad Product Line and Lending Capacity",
        'moat_4': "Targeted Metropolitan Strategy",
        'peer_a': "East West Bancorp",
        'peer_b': "First Horizon",
        'peer_c': "SouthState"
    },
    'BE': {
        'description': "Bloom Energy Corporation is an American public company based in San Jose, California, specializing in clean energy solutions. The company manufactures and markets solid oxide fuel cells, known as Bloom Energy Servers, which generate electricity on-site from fuels such as natural gas, biogas, and hydrogen without combustion.",
        'business_model': "Bloom Energy's business model revolves around the production and distribution of its energy servers. The company designs, manufactures, sells, and installs these systems for commercial, industrial, and utility clients through a direct sales force and leasing partners. Beyond sales, Bloom Energy generates revenue through comprehensive services, including system installation, ongoing maintenance, monitoring, and repairs.",
        'moat_1': "Proprietary Technology and Intellectual Property",
        'moat_2': "Customer Switching Costs",
        'moat_3': "Innovation and R&D",
        'moat_4': "Market Leadership",
        'peer_a': "FuelCell Energy",
        'peer_b': "Plug Power",
        'peer_c': "Ballard Power Systems"
    },
    'BEPC': {
        'description': "Brookfield Renewable Corp. (BEPC) is a global leader in renewable power and decarbonization solutions, operating one of the world's largest publicly traded platforms in the sector.",
        'business_model': "Brookfield Renewable's business model centers on acquiring, developing, managing, and operating energy-producing assets. The company generates revenue primarily by selling electricity through long-term, inflation-controlled contracts, known as Power Purchase Agreements (PPAs), to a diverse customer base including utility companies, corporate and industrial clients, and public power authorities.",
        'moat_1': "Investment-Grade Credit Rating",
        'moat_2': "Strong Capital Allocation",
        'moat_3': "Diversified Global Portfolio",
        'moat_4': "Long-Term Contracts",
        'peer_a': "NextEra Energy",
        'peer_b': "Cheniere Energy Partners",
        'peer_c': "Fortis"
    },
    'BGNE': {
        'description': "BeiGene Ltd., recently rebranded as BeOne Medicines, is a multinational oncology company specializing in the discovery, development, manufacturing, and commercialization of innovative molecularly targeted and immuno-oncology drugs for cancer treatment.",
        'business_model': "BeiGene's business model is centered on innovation, an integrated operational framework, and global expansion. It heavily invests in R&D, operates with a fully integrated model covering drug discovery, clinical development, manufacturing, and commercialization, and conducts global clinical trials with its own team.",
        'moat_1': "Significant Investment in R&D",
        'moat_2': "Integrated Operations",
        'moat_3': "Global Clinical Trials",
        'moat_4': "Strong Presence in China",
        'peer_a': "Ultivue",
        'peer_b': "Moderna",
        'peer_c': "Incyte"
    },
    'BIDU': {
        'description': "Baidu Inc. is a Chinese multinational technology company that specializes in Internet services and artificial intelligence (AI). Founded in 2000 as a search engine, it is often referred to as the \"Google of China\" and holds a dominant position in the Chinese search market.",
        'business_model': "Baidu's business model is multifaceted, with its primary revenue source being online marketing services, particularly pay-for-performance (P4P) advertising. Beyond advertising, Baidu generates revenue from AI Cloud services, subscription services (iQIYI), autonomous driving, smart consumer electronics, financial services, and venture capital investments.",
        'moat_1': "Market Dominance in China",
        'moat_2': "Technology and Innovation (AI Focus)",
        'moat_3': "Localized Content and Language Expertise",
        'moat_4': "Extensive User Base",
        'peer_a': "Alibaba Group",
        'peer_b': "Tencent",
        'peer_c': "ByteDance"
    },
    'BILI': {
        'description': "Bilibili Inc. is a prominent online entertainment platform based in China, primarily catering to young generations with a strong focus on anime, comics, and games (ACG) content. While initially concentrating on long-form ACG content, the platform has diversified its offerings to attract a broader audience. A distinctive feature of Bilibili is its \"bullet comments\" or \"danmu\" system, which allows real-time, overlaid comments on videos, fostering a dynamic and community-driven viewing experience. Beyond ACG, its content spans music, art, and education. The company also operates an e-commerce platform for related merchandise and has expanded into live streaming.",
        'business_model': "Bilibili's business model is multifaceted and designed to engage users deeply within its ecosystem. It heavily relies on a user-generated content (UGC) model, where millions of creators contribute content, which in turn attracts and retains viewers. The core of its success is its community-centric approach, emphasizing UGC and interactive features to cultivate a highly engaged user base. Bilibili generates revenue through advertising, mobile gaming, value-added services (VAS) including live broadcasting and premium memberships, and e-commerce.",
        'moat_1': "Community-Centric Model",
        'moat_2': "Content Ecosystem and IP Matrix",
        'moat_3': "User Stickiness and Loyalty",
        'moat_4': "ACG Industry Expertise",
        'peer_a': "iQiyi",
        'peer_b': "Youku",
        'peer_c': "Tencent Video"
    },
    'BKH': {
        'description': "Black Hills Corporation is a diversified energy company headquartered in Rapid City, South Dakota, with operations spanning across several states in the American West, including South Dakota, Wyoming, Colorado, Montana, Nebraska, Iowa, Kansas, and Arkansas.",
        'business_model': "Black Hills Corporation's business model is centered on providing reliable and essential energy services, characterized by vertically integrated operations, stable revenue streams from its utility segment, strategic acquisitions and expansion, and a commitment to sustainability.",
        'moat_1': "Regulated Utility Status",
        'moat_2': "High Capital Expenditure",
        'moat_3': "Customer Stickiness",
        'moat_4': "Infrastructure as a Defensive Barrier",
        'peer_a': "Xcel Energy",
        'peer_b': "Duke Energy",
        'peer_c': "Pacific Gas and Electric Company"
    },
    'BMRN': {
        'description': "BioMarin Pharmaceutical Inc. is a global biotechnology company dedicated to developing and commercializing innovative therapies for serious and life-threatening rare genetic diseases.",
        'business_model': "BioMarin's business model is built on innovation, patient-centricity, and long-term value creation. The company primarily generates revenue through the sale of its approved therapies. A core aspect of their strategy involves significant investment in research and development (R&D) to discover and develop treatments for rare diseases with high unmet medical needs.",
        'moat_1': "Lucrative Monopolies in Niche Markets",
        'moat_2': "Orphan Drug Status",
        'moat_3': "High Barriers to Entry",
        'moat_4': "Established Safety Profiles",
        'peer_a': "Sarepta Therapeutics",
        'peer_b': "Ultragenyx Pharmaceutical",
        'peer_c': "Neurocrine Biosciences"
    },
    'BMWYY': {
        'description': "Bayerische Motoren Werke AG (BMW AG) is a German multinational company headquartered in Munich, Bavaria, Germany, primarily known as a manufacturer of luxury vehicles and motorcycles.",
        'business_model': "BMW's business model is centered on offering high-quality, luxury vehicles with innovative features and exceptional driving performance. Key aspects include revenue from vehicle and motorcycle sales, financial services, and after-sales services. BMW targets affluent customers and invests heavily in R&D for electric mobility and autonomous driving.",
        'moat_1': "Brand Strength/Intangible Assets",
        'moat_2': "Switching Costs",
        'moat_3': "Scale and Global Reach",
        'moat_4': "",
        'peer_a': "Audi",
        'peer_b': "Mercedes-Benz",
        'peer_c': "Porsche"
    },
    'BNTX': {
        'description': "BioNTech SE is a German multinational clinical-stage biotechnology company headquartered in Mainz, Germany. It specializes in the development of immunotherapies and vaccines, primarily focusing on patient-specific treatments for cancer and other serious diseases, including infectious diseases.",
        'business_model': "BioNTech's business model is centered on the development, manufacturing, and marketing of its proprietary immunotherapies. This is pursued either independently or through strategic collaborations with partners. Key aspects include R&D, collaborations, intellectual property, and revenue from product sales and collaborations.",
        'moat_1': "Pioneering mRNA Technology",
        'moat_2': "Rapid Development and Scalability",
        'moat_3': "Strong Financial Position and R&D Investment",
        'moat_4': "Personalized Medicine Approach",
        'peer_a': "Moderna",
        'peer_b': "GSK",
        'peer_c': "Takeda Pharmaceutical"
    },
    'BRKR': {
        'description': "Bruker Corporation is a global leader in scientific instruments and analytical solutions, headquartered in Billerica, Massachusetts, USA. The company designs, manufactures, and distributes high-performance scientific instruments and analytical and diagnostic solutions that enable customers to explore life and materials at microscopic, molecular, and cellular levels.",
        'business_model': "Bruker's business model is diversified, integrating product sales, services, and software solutions. The company generates revenue primarily through instrument sales, service contracts, software solutions, and consumables and accessories.",
        'moat_1': "Proprietary Technology and Innovation",
        'moat_2': "High Switching Costs",
        'moat_3': "Strong R&D Capabilities",
        'moat_4': "Market Dominance in Certain Areas",
        'peer_a': "Thermo Fisher Scientific",
        'peer_b': "Agilent Technologies",
        'peer_c': "Shimadzu Corporation"
    },
    'C3AI': {
        'description': "C3.ai Inc. is an American information technology company specializing in enterprise artificial intelligence (AI) software. Founded in 2009 by Thomas Siebel, the company has evolved from its initial focus on managing corporate carbon footprints as \"C3 Energy\" to becoming a leader in enterprise AI solutions for digital transformation.",
        'business_model': "C3.ai's business model is primarily centered around providing its enterprise AI software through a subscription-based revenue model. A smaller portion of its revenue also comes from consumption-based pricing and professional services.",
        'moat_1': "Comprehensive AI Platform",
        'moat_2': "Strong Industry Expertise",
        'moat_3': "Established Customer Base",
        'moat_4': "Strategic Partnerships",
        'peer_a': "Palantir",
        'peer_b': "DataRobot",
        'peer_c': "Obviously AI"
    },
    'CACI': {
        'description': "CACI International Inc. is an American multinational professional services and information technology company that provides expertise and technology to enterprise and mission customers, primarily supporting national security in the intelligence, defense, and federal civilian sectors of the U.S. federal government.",
        'business_model': "CACI's business model revolves around providing integrated solutions that combine technology, expertise, and innovation, generating revenue through long-term contracts with government agencies. The company focuses on mission-critical IT and technical solutions.",
        'moat_1': "High Barriers to Entry",
        'moat_2': "Limited Substitutes",
        'moat_3': "Specialized Technology and Mission-Critical Contracts",
        'moat_4': "Established Relationships and Trust",
        'peer_a': "Leidos",
        'peer_b': "Booz Allen Hamilton",
        'peer_c': "Science Applications International Corporation"
    },
    'CARR': {
        'description': "Carrier Global Corporation is an American multinational company that provides intelligent climate and energy solutions globally. Founded in 1915, it was spun off as an independent entity from United Technologies in 2020. The company operates in approximately 160 countries and employs around 48,000 people as of 2024. Its core business involves heating, ventilation, and air conditioning (HVAC), refrigeration, and fire and security equipment.",
        'business_model': "Carrier Global Corporation's business model primarily revolves around the sale of its HVAC, refrigeration, and fire & security products. The company also generates revenue through installation and service contracts. It focuses on delivering digitally-enabled lifecycle solutions to its customers.",
        'moat_1': "Strong Brand Identity and Reputation",
        'moat_2': "Global Presence and Extensive Distribution Network",
        'moat_3': "Innovative Products and Solutions",
        'moat_4': "Product Quality and Engineering Design",
        'peer_a': "Johnson Controls International",
        'peer_b': "Daikin",
        'peer_c': "Trane Technologies"
    },
    'CBSH': {
        'description': "Commerce Bancshares Inc. is a regional bank holding company headquartered in Missouri, with principal offices in Kansas City and St. Louis. It operates as the corporate parent of Commerce Bank and offers a diversified line of financial services.",
        'business_model': "Commerce Bancshares operates on a \"super-community bank\" approach, which involves managing its community banking offices on a decentralized basis. This decentralized structure allows local offices substantial autonomy in credit and pricing decisions, enabling them to be highly responsive to local customer needs and foster strong customer relationships. The company's strategy is to offer a comprehensive suite of banking services to both retail customers and small to medium-sized businesses. BancFirst primarily generates revenue through its net interest margin (NIM), which is the difference between the interest earned on its loans and securities and the interest paid on deposits and borrowings. Additionally, noninterest income from sources such as deposit service charges, trust fees, mortgage banking, and insurance commissions provides a crucial secondary revenue stream, diversifying its income. The company is also a prominent lender in various programs, notably being Oklahoma's leading originator of Small Business Administration (SBA) Loans for 34 consecutive years and the top in-state originator under the Farm Loan Program.",
        'moat_1': "Strong Regional Presence and Local Focus",
        'moat_2': "Relationship Banking and High-Touch Service",
        'moat_3': "Broad Product Line and Lending Capacity",
        'moat_4': "Solid Financial Performance and Prudent Management",
        'peer_a': "East West Bancorp",
        'peer_b': "First Horizon",
        'peer_c': "SouthState"
    },
    'CHK': {
        'description': "Chesapeake Energy Corporation is a leading independent exploration and production (E&P) company primarily focused on the acquisition, exploration, and development of properties for the production of natural gas, oil, and natural gas liquids (NGL) from underground reservoirs. The company operates predominantly in the United States, with a strategic emphasis on key onshore shale plays such as the Marcellus, Haynesville, and Eagle Ford.",
        'business_model': "Chesapeake Energy's business model is centered on creating shareholder value through the development of its substantial positions in premier U.S. onshore resource plays. Key components include exploration and production, strategic focus on shale plays, operational efficiency and financial discipline, strategic acquisitions, and marketing services.",
        'moat_1': "Market Presence and Economies of Scale",
        'moat_2': "Technological Advancements",
        'moat_3': "Production Efficiency and Cost Reduction",
        'moat_4': "Focus on Lower Carbon Energy Solutions",
        'peer_a': "EQT Corporation",
        'peer_b': "Antero Resources",
        'peer_c': "EOG Resources"
    },
    'CHWY': {
        'description': "Chewy Inc. is an e-commerce business specializing in pet products and services, operating primarily through its website and mobile applications.",
        'business_model': "Chewy's business model is centered on online sales, convenience, and exceptional customer service. Key aspects include direct sales, the Autoship subscription program, customer convenience, and diversified offerings including pharmacy services.",
        'moat_1': "Extensive Product Selection",
        'moat_2': "Exceptional Customer Service",
        'moat_3': "Convenient Auto-ship Feature",
        'moat_4': "Robust E-commerce Platform and Logistics Network",
        'peer_a': "Amazon",
        'peer_b': "Petco",
        'peer_c': "PetSmart"
    },
    'CLSK': {
        'description': "CleanSpark Inc. is primarily a Bitcoin mining technology company that operates data centers across the United States. The company focuses on sustainable and efficient cryptocurrency mining by leveraging low-cost, low-carbon, and renewable energy sources to power its operations.",
        'business_model': "CleanSpark's business model is centered on large-scale Bitcoin mining. They generate revenue by validating blockchain transactions and earning Bitcoin rewards. The company has strategically invested in advanced mining technologies and infrastructure to optimize operational efficiency and output.",
        'moat_1': "Cost Efficiency",
        'moat_2': "Proprietary Microgrid Technology",
        'moat_3': "Vertical Integration",
        'moat_4': "Strategic Power Agreements and Facility Locations",
        'peer_a': "Hut 8",
        'peer_b': "HIVE Blockchain",
        'peer_c': "Bit Digital"
    },
    'CNX': {
        'description': "CNX Resources Corporation is an American natural gas company headquartered in Pittsburgh, Pennsylvania, primarily operating as an independent low-carbon intensity natural gas and midstream company. Its core operations are concentrated in the Appalachian Basin, specifically focusing on the Marcellus Shale and Utica Shale formations across Pennsylvania, Ohio, and West Virginia. The company is recognized as one of the largest natural gas producers in the United States.",
        'business_model': "CNX Resources Corporation's business model is centered on the exploration, extraction, and distribution of natural gas, generating revenue primarily through its sale. Key aspects of its operational strategy include exploration and production, midstream services, natural gas sales, coalbed methane and coal mine methane extraction, strategic partnerships and innovation, and land management.",
        'moat_1': "Prime Asset Base",
        'moat_2': "Integrated Operations",
        'moat_3': "Technological Expertise and Innovation",
        'moat_4': "Cost Efficiency",
        'peer_a': "EQT Corporation",
        'peer_b': "Range Resources",
        'peer_c': "Antero Resources Corp"
    },
    'COHR': {
        'description': "Coherent Corp. is a global technology company specializing in materials, networking, and lasers. The company develops, manufactures, and markets engineered materials, optoelectronic components and devices, and lasers.",
        'business_model': "Coherent Corp.'s business model is built on a vertically integrated manufacturing approach, which enables them to manage costs, ensure quality, and efficiently deliver high-volume production. The company's operations are segmented into Networking, Materials, and Lasers.",
        'moat_1': "Efficient Scale and Vertical Integration",
        'moat_2': "Extensive Patent Portfolio",
        'moat_3': "Market Leadership in Certain Areas",
        'moat_4': "AI-Enhanced Products and Services",
        'peer_a': "Northrop Grumman Corporation",
        'peer_b': "Newport Corporation",
        'peer_c': "IPG Photonics"
    },
    'COIN': {
        'description': "Coinbase Global Inc. operates as a prominent technology company and cryptocurrency exchange platform, providing a comprehensive suite of services for the crypto economy.",
        'business_model': "Coinbase's business model is primarily centered around facilitating crypto transactions and offering related services, generating revenue through multiple streams including transaction fees, custodial fees, subscription services, staking services, and interest income.",
        'moat_1': "Regulatory Compliance and Trust",
        'moat_2': "Strong Brand and Reputation",
        'moat_3': "User-Friendly Interface",
        'moat_4': "Liquidity and Network Effects",
        'peer_a': "Binance",
        'peer_b': "Kraken",
        'peer_c': "Gemini"
    },
    'COLB': {
        'description': "Columbia Banking System Inc (CBS) is a financial holding company that, through its wholly-owned banking subsidiary Columbia State Bank and its parent company Umpqua Bank, offers a comprehensive suite of banking and financial services. The company serves a diverse clientele, including corporate, institutional, small business, and individual customers.",
        'business_model': "Columbia Banking System operates on a community banking model, prioritizing personalized service, local decision-making, and active community involvement. Its business model is diversified to ensure stable revenue generation, primarily through net interest income and non-interest income from various banking services.",
        'moat_1': "Strong Regional Presence",
        'moat_2': "Comprehensive Product and Service Offerings",
        'moat_3': "Customer-Centric Approach/Relationship Banking",
        'moat_4': "Cost Management and Net Interest Margin (NIM) Expansion",
        'peer_a': "Home Bancshares (Conway AR)",
        'peer_b': "International Bancshares",
        'peer_c': "Axos Financial"
    },
    'CORT': {
        'description': "Corcept Therapeutics is a commercial-stage pharmaceutical company dedicated to the discovery, development, and commercialization of medications. Their primary focus is on treating severe metabolic, oncologic, psychiatric, and neurologic disorders by modulating the effects of the hormone cortisol.",
        'business_model': "Corcept's business model revolves around research and development (R&D) of new pharmaceutical products, with a particular emphasis on cortisol modulation. It also focuses on the commercialization of approved products like Korlym, pipeline development, and distribution through specialty pharmacies.",
        'moat_1': "Specialized Focus on Cortisol Modulation",
        'moat_2': "Proprietary Drug Portfolio and Pipeline",
        'moat_3': "Strong Intellectual Property",
        'moat_4': "Robust Financial Performance and Efficiency",
        'peer_a': "Ionis Pharmaceuticals, Inc.",
        'peer_b': "Collegium Pharmaceutical, Inc.",
        'peer_c': "Teva Pharmaceutical Industries Ltd."
    },
    'CORZ': {
        'description': "Core Scientific Inc. is a prominent digital infrastructure provider specializing in digital asset mining and high-performance computing (HPC). The company designs, builds, and operates dedicated facilities for these purposes across multiple U.S. states.",
        'business_model': "Core Scientific's business model is primarily structured around three operating segments: Digital Asset Self-Mining, Digital Asset Hosted Mining, and HPC Hosting (Colocation Segment). The company generates revenue by validating blockchain transactions and earning Bitcoin rewards, and by offering hosting services to third-party digital asset miners and high-density colocation services for GPU-based HPC operations.",
        'moat_1': "Specialization in High-Density Colocation",
        'moat_2': "Strategic Pivot to AI/HPC Hosting",
        'moat_3': "Robust Existing Infrastructure and Operational Expertise",
        'moat_4': "Long-Term Strategic Partnerships",
        'peer_a': "Riot Platforms",
        'peer_b': "Marathon Digital",
        'peer_c': "Applied Digital"
    },
    'COTY': {
        'description': "Coty Inc. is an American multinational beauty company founded in 1904 by François Coty. It develops, manufactures, markets, and distributes a wide range of beauty products, including fragrances, cosmetics, skin care, nail care, and both professional and retail hair care products.",
        'business_model': "Coty's business model is centered around a diverse portfolio of approximately 40 owned and licensed brands, categorized into two main segments: Consumer Beauty and Prestige. It emphasizes innovation, strategic partnerships, and diverse brand offerings to cater to various consumer segments.",
        'moat_1': "Strong Brand Identity and Reputation",
        'moat_2': "Innovative Products and Solutions",
        'moat_3': "Global Presence and Extensive Distribution Network",
        'moat_4': "Product Quality and Engineering Design",
        'peer_a': "L'Oréal",
        'peer_b': "Estée Lauder",
        'peer_c': "Procter & Gamble"
    },
    'C-PN': {
        'description': "Citigroup Inc. (Citi) is a prominent American multinational investment bank and financial services company headquartered in New York City. It functions as a global diversified financial services holding company, offering a broad spectrum of financial products and services to a diverse clientele that includes consumers, corporations, governments, and institutions across more than 160 countries and jurisdictions. Citi is recognized as one of the \"Big Four\" banking institutions in the United States by assets, alongside JPMorgan Chase, Bank of America, and Wells Fargo.",
        'business_model': "Citigroup's business model is primarily structured around two core segments: Institutional Clients Group (ICG) and Personal Banking and Wealth Management (PBWM). Its overall revenue generation is multifaceted, largely driven by interest income from its extensive lending activities, which include personal loans, mortgages, and corporate financing. Additionally, significant fee-based income is derived from transactional services, asset management, advisory services within investment banking, and its credit card operations.",
        'moat_1': "Global Presence",
        'moat_2': "Diversified Product Portfolio",
        'moat_3': "Brand Value and Reputation",
        'moat_4': "Technology and Innovation",
        'peer_a': "JPMorgan Chase & Co.",
        'peer_b': "Bank of America",
        'peer_c': "Wells Fargo"
    },
    'CPNG': {
        'description': "Coupang Inc. is a leading e-commerce company primarily operating in South Korea, often referred to as \"South Korea's Amazon.\" The company was incorporated in 2010 and is headquartered in Seoul, South Korea, with operations and support services in various other countries including the United States, Taiwan, Singapore, China, Japan, and India.",
        'business_model': "Coupang's business model is characterized by a seamless integration of technology, logistics, and customer service, aiming to provide a differentiated e-commerce experience. It operates a hybrid model combining direct sales with a marketplace for third-party merchants, and its proprietary logistics network (Rocket Delivery) is a cornerstone of its success.",
        'moat_1': "Intangible Assets",
        'moat_2': "Network Effect",
        'moat_3': "Economies of Scale",
        'moat_4': "",
        'peer_a': "Amazon.com Inc.",
        'peer_b': "JD.com Inc.",
        'peer_c': "Alibaba"
    },
    'CRC': {
        'description': "California Resources Corporation (CRC) is an independent energy and carbon management company that primarily explores for, produces, processes, gathers, and markets crude oil, natural gas, and natural gas liquids. The company operates exclusively within California, holding the largest private oil and gas reserves in the state across major basins such as San Joaquin, Los Angeles, and Sacramento.",
        'business_model': "CRC's business model is centered on the exploration and production (E&P) of hydrocarbons, utilizing advanced technologies to maximize recovery from mature fields. The company sells its energy products to marketers, refineries, and other purchasers who have access to storage and transportation infrastructure. In a strategic shift, CRC is repositioning itself as an energy and carbon management company, with a significant focus on decarbonization efforts.",
        'moat_1': "Extensive Reserves and Strategic Assets",
        'moat_2': "Technological Edge and Operational Excellence",
        'moat_3': "Deep Industry Knowledge and Experienced Team",
        'moat_4': "Environmental Compliance Expertise and Sustainability Focus",
        'peer_a': "Occidental Petroleum",
        'peer_b': "Chevron",
        'peer_c': "EOG Resources"
    },
    'CREE': {
        'description': "Wolfspeed Inc. is a leading American developer and manufacturer of wide-bandgap semiconductors, primarily focusing on silicon carbide (SiC) and gallium nitride (GaN) materials and devices. The company, formerly known as Cree, Inc., rebranded in 2021 to emphasize its strategic pivot towards these advanced semiconductor technologies.",
        'business_model': "Wolfspeed's business model is built on its leadership in silicon carbide and gallium nitride technologies, focusing on vertical integration, innovation, and strategic customer engagement. The company generates revenue primarily through the sale of its power devices, RF devices, and semiconductor materials to a diverse global customer base.",
        'moat_1': "Intellectual Property and Technological Moat",
        'moat_2': "Vertical Integration Moat",
        'moat_3': "High Capital Expenditure Barrier",
        'moat_4': "Customer Lock-in and Qualification Processes",
        'peer_a': "STMicroelectronics",
        'peer_b': "Infineon Technologies",
        'peer_c': "OnSemi"
    },
    'CRL': {
        'description': "Charles River Laboratories International, Inc. (CRL) is an American pharmaceutical company that specializes in preclinical and clinical laboratory services, gene therapy, and cell therapy services and supplies for the pharmaceutical, medical device, and biotechnology industries.",
        'business_model': "Charles River Laboratories operates a highly integrated business model that combines products, services, and expertise to support the entire drug development lifecycle. Their business model can be broken down into several key components: Revenue Streams, Value Proposition, Client-Centric Approach, and Strategic Focus.",
        'moat_1': "Intangible Assets",
        'moat_2': "Switching Costs",
        'moat_3': "Strong Reputation",
        'moat_4': "Quality and Speed",
        'peer_a': "Fortrea Holdings Inc.",
        'peer_b': "Icon PLC.",
        'peer_c': "Labcorp Holdings Inc."
    },
    'CRO': {
        'description': "Charles River Laboratories International, Inc. (CRL) is an American pharmaceutical company that specializes in preclinical and clinical laboratory services, gene therapy, and cell therapy services and supplies for the pharmaceutical, medical device, and biotechnology industries.",
        'business_model': "Charles River Laboratories operates a highly integrated business model that combines products, services, and expertise to support the entire drug development lifecycle. Their business model can be broken down into several key components: Revenue Streams, Value Proposition, Client-Centric Approach, and Strategic Focus.",
        'moat_1': "Intangible Assets",
        'moat_2': "Switching Costs",
        'moat_3': "Strong Reputation",
        'moat_4': "Quality and Speed",
        'peer_a': "Fortrea Holdings Inc.",
        'peer_b': "Icon PLC.",
        'peer_c': "Labcorp Holdings Inc."
    },
    'CRSP': {
        'description': "CRISPR Therapeutics AG is a biotechnology company based in Switzerland that specializes in gene editing. The company focuses on developing gene-based medicines for serious human diseases using its proprietary CRISPR/Cas9 platform.",
        'business_model': "CRISPR Therapeutics' business model is centered on leveraging its advanced CRISPR gene-editing technology to address significant unmet medical needs. Their revenue model is multifaceted, primarily generating income through milestone payments and royalties from strategic collaborations with pharmaceutical companies and research institutions.",
        'moat_1': "Proprietary Gene-Editing Platform",
        'moat_2': "First-Mover Advantage",
        'moat_3': "Strong Financial Position",
        'moat_4': "Diverse and Advancing Pipeline",
        'peer_a': "Editas Medicine, Inc.",
        'peer_b': "Caribou Biosciences, Inc.",
        'peer_c': "Sangamo Therapeutics, Inc."
    },
    'CRUS': {
        'description': "Cirrus Logic Inc. is an American fabless semiconductor supplier that specializes in designing, developing, and distributing low-power, high-precision analog and mixed-signal components. Their primary focus is on audio and voice signal processing applications.",
        'business_model': "Cirrus Logic operates on a \"fabless\" model, meaning they design their semiconductor chips but outsource the manufacturing process. Their business model centers on designing and selling high-performance ICs to original equipment manufacturers (OEMs) within the consumer electronics industry. Revenue is primarily generated from the sale of these ICs.",
        'moat_1': "Technical Expertise and Innovation",
        'moat_2': "Strong Customer Relationships",
        'moat_3': "Comprehensive Product Portfolio",
        'moat_4': "Fabless Semiconductor Model",
        'peer_a': "Analog Devices",
        'peer_b': "Texas Instruments",
        'peer_c': "NXP Semiconductors"
    },
    'CSGP': {
        'description': "CoStar Group Inc. is a global leader in providing information, analytics, and online marketplaces for the commercial and residential real estate industries. The company's mission is to digitize the world's real estate to empower individuals and businesses with insights and connections that improve their operations and lives.",
        'business_model': "CoStar Group primarily generates revenue through subscription-based services. This multi-sided business model serves two interdependent customer segments: property listers (commercial property owners, landlords, and real estate agents who list properties for sale or lease on CoStar's marketplaces) and property seekers (businesses and individuals who subscribe to access CoStar's vast database and analytical tools to find and evaluate properties).",
        'moat_1': "Data and Information Dominance (Network Effect & Switching Costs)",
        'moat_2': "Intangible Assets",
        'moat_3': "High Barriers to Entry",
        'moat_4': "Contractual and Technological Barriers",
        'peer_a': "Reis",
        'peer_b': "Apto",
        'peer_c': "RealtyMogul"
    },
    'CSL': {
        'description': "Carlisle Companies Incorporated is a diversified manufacturer primarily focused on highly engineered building envelope products and solutions. The company specializes in manufacturing and selling single-ply roofing products, warranted systems, and various accessories for the commercial building industry.",
        'business_model': "Carlisle's business model is centered on generating revenue through the manufacturing and sale of highly engineered building envelope products and solutions. Its core operations target commercial and industrial construction markets, providing roofing, insulation, and weatherproofing systems. The Carlisle Construction Materials segment accounts for the majority of its revenue, with a significant portion of its total revenue derived from the United States. The business is largely driven by repair and remodeling activities, which constitute approximately 60% of its sales, with new construction making up the rest.",
        'moat_1': "Market Leadership",
        'moat_2': "Strong Brand Reputation",
        'moat_3': "Carlisle Operating System (COS)",
        'moat_4': "Innovation and R&D",
        'peer_a': "3M",
        'peer_b': "Saint-Gobain",
        'peer_c': "Honeywell"
    },
    'CTRA': {
        'description': "Coterra Energy Inc. is a premier, diversified energy company engaged in the development, exploration, and production of natural gas, natural gas liquids (NGLs), and oil in the United States. Headquartered in Houston, Texas, the company operates primarily in key hydrocarbon basins, including the Marcellus Shale in Pennsylvania, the Permian Basin in Texas and New Mexico, and the Anadarko Basin in Oklahoma.",
        'business_model': "Coterra Energy's business model is centered on several key pillars: diversified portfolio and asset flexibility, exploration and production, disciplined capital investment, low-cost/high-return inventory, sales and marketing, strategic partnerships and operational efficiency, and commitment to ESG.",
        'moat_1': "Low-Cost Production Base and Operational Efficiency",
        'moat_2': "Strategic Asset Portfolio",
        'moat_3': "Technical Expertise and Disciplined Capital Allocation",
        'moat_4': "Diversified Market Share",
        'peer_a': "EQT Corporation",
        'peer_b': "Canadian Natural Resources",
        'peer_c': "ENI"
    },
    'CVNA': {
        'description': "Carvana Co. is an online used car retailer based in Tempe, Arizona, operating an e-commerce platform for buying and selling used cars in the United States. The company aims to transform the traditional used car buying process by offering a seamless, transparent, and hassle-free experience through its online platform.",
        'business_model': "Carvana's business model is centered on disrupting the traditional dealership model by leveraging digital technology and multiple revenue streams. It provides a fully online experience for customers to browse, finance, purchase, and receive used cars. Revenue is primarily generated from used car sales, financing, and ancillary products and services like vehicle protection plans and wholesale car sales.",
        'moat_1': "Innovative Business Model",
        'moat_2': "Data-Driven Approach",
        'moat_3': "Strong Brand Recognition",
        'moat_4': "Vertically Integrated Operations",
        'peer_a': "CarMax",
        'peer_b': "Vroom",
        'peer_c': "AutoTrader"
    },
    'CYBR': {
        'description': "CyberArk Software Ltd. is an Israeli publicly traded information security company, established in 1999, that specializes in identity security. The company's core mission is to proactively protect organizations from cyber threats by securing access to critical assets and eliminating risks associated with privileged credential misuse.",
        'business_model': "CyberArk's business model is primarily revolves around generating revenue through its identity security solutions, particularly its PAM offerings. The company operates predominantly on a subscription-based model, which ensures a recurring revenue stream and fosters long-term customer relationships.",
        'moat_1': "Dominance in Privileged Access Management (PAM)",
        'moat_2': "Expansion into Machine Identity Management",
        'moat_3': "Comprehensive Identity Security Platform",
        'moat_4': "High Customer Switching Costs",
        'peer_a': "Okta",
        'peer_b': "Microsoft Entra ID",
        'peer_c': "Ping Identity"
    },
    'DCP': {
        'description': "DCP Midstream LP was an American energy company focused on midstream petroleum services, including transportation and refinery operations. The company owned, operated, acquired, and developed a portfolio of midstream energy assets across the United States.",
        'business_model': "DCP Midstream's business model revolved around providing essential midstream services to connect energy resources to end-use markets. Key aspects of their business model included an integrated network for gathering, processing, transportation, and marketing of natural gas and NGLs, and fee-based, long-term contracts.",
        'moat_1': "Integrated Operations",
        'moat_2': "Strategic Asset Base and Scale",
        'moat_3': "Operational Efficiency and Reliability",
        'moat_4': "Established Relationships",
        'peer_a': "Western Midstream Partners L.P.",
        'peer_b': "Targa Resources Corp.",
        'peer_c': "ONEOK, Inc."
    },
    'DDAIF': {
        'description': "Daimler AG, now officially known as Mercedes-Benz Group AG since February 2022, is a German multinational automotive company. Its business primarily revolves around the development, manufacturing, and distribution of premium passenger cars and vans. The company's roots trace back to the auto companies founded by Gottlieb Daimler and Karl Benz, which merged in 1926.",
        'business_model': "The business model of Mercedes-Benz Group AG is multifaceted, focusing on vehicle sales, financial and mobility services, innovation and technology leadership, and global market presence. The strategic spin-off of Daimler Truck Holding AG was intended to allow both entities to unlock their full potential by focusing on their respective core businesses.",
        'moat_1': "Brand Strength/Intangible Assets",
        'moat_2': "Switching Costs",
        'moat_3': "Scale and Global Reach",
        'moat_4': "",
        'peer_a': "BMW",
        'peer_b': "Audi",
        'peer_c': "Mercedes-Benz"
    },
    'DDOG': {
        'description': "Datadog Inc. is an American technology company that provides an observability and security platform for cloud-scale applications. Its core offering is a Software as a Service (SaaS)-based data analytics platform that enables monitoring of servers, databases, tools, and services.",
        'business_model': "Datadog's business model is primarily based on a subscription-based SaaS model, with revenue generated through subscription fees and usage-based pricing. A key aspect of its strategy is its \"land-and-expand\" approach, where customers initially adopt a single product and then gradually expand their usage to include additional services.",
        'moat_1': "High Switching Costs",
        'moat_2': "Intangible Assets",
        'moat_3': "Network Effects",
        'moat_4': "Sticky Product Portfolio",
        'peer_a': "Dynatrace",
        'peer_b': "New Relic",
        'peer_c': "AppDynamics"
    },
    'DELL': {
        'description': "Dell Technologies Inc. is a global technology leader that designs, develops, manufactures, markets, sells, and supports a wide array of integrated technology solutions, products, and services. Headquartered in Round Rock, Texas, the company was founded by Michael Dell in 1984 and later formed Dell Technologies in 2016 following the acquisition of EMC Corporation.",
        'business_model': "Dell's business model is characterized by several key elements: direct sales model, build-to-order strategy, diversified portfolio and revenue streams, efficient supply chain, customer-centric focus, strategic partnerships, and evolving distribution.",
        'moat_1': "Superior Supply Chain Management",
        'moat_2': "Extensive Product Portfolio and Customizable Solutions",
        'moat_3': "Strong Brand Identity and Global Distribution Network",
        'moat_4': "Customer-Centric Approach",
        'peer_a': "Lenovo Group Ltd.",
        'peer_b': "HP Inc.",
        'peer_c': "Acer"
    },
    'DHT': {
        'description': "DHT Holdings Inc. is a leading independent crude oil tanker company specializing in the global transportation of crude oil. Founded in 2005 and headquartered in Hamilton, Bermuda, the company is listed on the New York Stock Exchange under the ticker symbol \"DHT.\"",
        'business_model': "DHT Holdings' business model revolves around the ownership and operation of crude oil tankers, generating revenue by transporting crude oil for major oil companies, refiners, and trading houses. The company employs a flexible approach to fleet utilization, combining both spot market operations and time charter agreements.",
        'moat_1': "Modern and Fuel-Efficient Fleet",
        'moat_2': "Operational Excellence",
        'moat_3': "Strong Financial Position",
        'moat_4': "Experienced Management Team",
        'peer_a': "Teekay Tankers",
        'peer_b': "Frontline",
        'peer_c': "International Seaways"
    },
    'DIDI': {
        'description': "Didi Global Inc. is a leading mobility technology platform that offers a wide range of app-based services across various global markets, including Asia Pacific and Latin America. The company's mission is to \"build a better journey\" by transforming mobility and creating a safe, affordable, convenient, and sustainable transportation and local services ecosystem.",
        'business_model': "Didi Global Inc. employs a multi-faceted revenue strategy, primarily generating income through commissions on rides completed through its platform. Additional income streams include service fees, advertising opportunities, enterprise solutions, and financial services.",
        'moat_1': "Dominant Market Share",
        'moat_2': "Diversified Service Portfolio",
        'moat_3': "Technological Prowess",
        'moat_4': "Lower Customer Acquisition Costs",
        'peer_a': "Uber",
        'peer_b': "Lyft",
        'peer_c': "Grab"
    },
    'DJT': {
        'description': "Trump Media & Technology Group (TMTG) is an American media and technology company that aims to champion free speech by providing alternatives to mainstream platforms. The company is majority-owned by former U.S. President Donald Trump and became publicly traded on the Nasdaq stock exchange under the ticker symbol \"DJT\" in March 2024.",
        'business_model': "TMTG's business model is evolving, with its primary revenue streams and strategic approach outlined as follows: advertising on Truth Social, and strategic partnerships in financial services with Truth.Fi, offering \"America First investment vehicles\" via SMAs and plans for launching ETFs.",
        'moat_1': "Niche Audience and Trump Brand Recognition",
        'moat_2': "High-Margin Partnership Strategy",
        'moat_3': "",
        'moat_4': "",
        'peer_a': "Snap",
        'peer_b': "X (formerly Twitter)",
        'peer_c': "Facebook"
    },
    'DKS': {
        'description': "Dick's Sporting Goods is the largest sporting goods retailer in the United States, founded in 1948. Headquartered in Coraopolis, Pennsylvania, the company operates over 850 stores, including DICK'S Sporting Goods, Golf Galaxy, Public Lands, and Going Going Gone! stores, along with online platforms and a mobile app.",
        'business_model': "Dick's Sporting Goods operates under an economic model driven by several key factors: revenue generation through sales of sporting goods, apparel, and footwear via its retail stores and e-commerce platforms; omnichannel retailing; product assortment and sourcing; customer experience; strategic partnerships; competitive pricing; and supply chain management.",
        'moat_1': "Omnichannel Strategy",
        'moat_2': "Strong Vendor Relationships",
        'moat_3': "Differentiated In-Store Experience",
        'moat_4': "Vast and On-Trend Product Assortment",
        'peer_a': "Academy Sports + Outdoors",
        'peer_b': "Big 5 Sporting Goods",
        'peer_c': "Modell's"
    },
    'DOCS': {
        'description': "Doximity Inc. is a prominent American healthcare technology company that operates the largest medical professional network in the United States. Established in 2010, Doximity provides a comprehensive digital platform designed exclusively for healthcare practitioners, including physicians, nurses, physician assistants, and medical students.",
        'business_model': "Doximity operates primarily on a subscription-based business model, generating revenue through a combination of subscription services and targeted advertising. Its main revenue streams include marketing solutions (subscription fees from pharmaceutical companies and health systems for targeted advertisements), hiring solutions (recruitment services to healthcare organizations), telehealth services, and premium subscriptions for professionals.",
        'moat_1': "Network Effect",
        'moat_2': "High Switching Costs/User Lock-in",
        'moat_3': "Data Advantage",
        'moat_4': "",
        'peer_a': "Veeva Systems",
        'peer_b': "Teladoc Health",
        'peer_c': "GoodRx Holdings"
    },
    'DOCU': {
        'description': "DocuSign Inc. is an American software company based in San Francisco, California, specializing in products for managing electronic agreements.",
        'business_model': "DocuSign primarily generates revenue through a subscription-based model, where customers pay monthly or annual fees for access to its software. The company offers various subscription plans tailored to different customer sizes and needs, from individual users and small businesses to large enterprises. In addition to base subscriptions, DocuSign earns revenue from optional add-on features, integrations, and value-added services, such as payment collection, advanced analytics, and custom integrations. Transactional charges for document signings that exceed plan limits also contribute to its revenue.",
        'moat_1': "Market Leadership and Brand Recognition",
        'moat_2': "Ease of Use and User Experience",
        'moat_3': "Robust Security and Compliance",
        'moat_4': "Extensive Integrations",
        'peer_a': "Adobe Sign",
        'peer_b': "PandaDoc",
        'peer_c': "Dropbox Sign"
    },
    'EDGW': {
        'description': "Edgewell Personal Care Company is an American multinational consumer products company headquartered in Shelton, Connecticut. Formed in 2015 as a spin-off from Energizer Holdings, the company is a leading global manufacturer and marketer of personal care products, aiming to enhance the daily lives of consumers worldwide.",
        'business_model': "Edgewell Personal Care operates on a consumer-centric business model, emphasizing innovation, brand development, and global distribution. The company generates revenue by selling its products through various channels, including retail, e-commerce, and direct-to-consumer. A significant part of its strategy involves investing in research and development to create innovative products that cater to evolving consumer preferences.",
        'moat_1': "Strong Brand Portfolio",
        'moat_2': "Innovation and Research & Development",
        'moat_3': "Global Distribution Network",
        'moat_4': "Focus on Gross Margins",
        'peer_a': "Procter & Gamble",
        'peer_b': "Unilever",
        'peer_c': "Johnson & Johnson"
    },
    'ELF': {
        'description': "e.l.f. Beauty Inc. is a multi-brand beauty company that offers inclusive, accessible, clean, vegan, and cruelty-free cosmetics and skincare products. Its product categories encompass eye, lip, and face makeup, beauty tools and accessories, and skincare. The company's brand portfolio includes e.l.f. Cosmetics, e.l.f. SKIN, Naturium, Well People, and Keys Soulcare.",
        'business_model': "e.l.f. Beauty Inc.'s business model is characterized by several key strategies: affordability and value, multi-channel distribution, rapid innovation, digital marketing and engagement, ethical product standards, global expansion, and employee investment.",
        'moat_1': "Affordability and Strong Value Proposition",
        'moat_2': "Strong Brand Identity",
        'moat_3': "Diverse Product Range and Rapid Innovation",
        'moat_4': "Asset-Light Business Model",
        'peer_a': "Estee Lauder",
        'peer_b': "L'Oreal",
        'peer_c': "Coty"
    },
    'ENLC': {
        'description': "EnLink Midstream LLC is an integrated midstream energy company that provides essential infrastructure services for the energy sector.",
        'business_model': "EnLink Midstream's business model is designed to connect energy producers with end markets through integrated midstream solutions. A significant characteristic of their model is the generation of revenue primarily through fee-based contracts. Approximately 95% of their cash flows are derived from these fee-based arrangements, with about 80% coming from long-term contracts that often include firm transportation agreements or minimum volume commitments. This fee-based structure provides stable and predictable cash flows, which helps to mitigate the risks associated with fluctuations in commodity prices.",
        'moat_1': "Strategic Geographic Footprint and Diversified Operations",
        'moat_2': "Stable, Fee-Based Business Model",
        'moat_3': "Integrated Service Offerings",
        'moat_4': "Operational Excellence and Financial Discipline",
        'peer_a': "MPLX",
        'peer_b': "Targa Resources Corp.",
        'peer_c': "The Williams Companies, Inc."
    },
    'EPD': {
        'description': "Enterprise Products Partners L.P. is a prominent North American provider of midstream energy services, operating as one of the largest publicly traded partnerships in the sector. The company offers essential services to producers and consumers of natural gas, natural gas liquids (NGLs), crude oil, refined products, and petrochemicals. Its operations are supported by an extensive and integrated network of energy infrastructure, which includes over 50,000 miles of pipelines, more than 300 million barrels of liquids storage capacity, fractionation facilities, and marine terminals. Essentially, Enterprise Products Partners functions as the \"hubs and highways\" for the oil and gas industry, facilitating the movement and processing of energy commodities.",
        'business_model': "The business model of Enterprise Products Partners is predominantly based on long-term, fee-based contracts for the transportation and storage of energy products. This structure ensures stable and predictable cash flows, significantly reducing the company's direct exposure to the volatility of commodity prices. Revenue is primarily generated by charging fees for the gathering, processing, transportation, storage, and marketing of natural gas, NGLs, crude oil, and petrochemicals. The company's earnings are largely dependent on the volume of commodities flowing through its system rather than fluctuations in commodity prices. Enterprise Products Partners operates through four main segments: NGL Pipelines & Services, Crude Oil Pipelines & Services, Natural Gas Pipelines & Services, and Petrochemical & Refined Products Services. Additionally, the company earns income from natural gas processing activities and the sale of natural gas liquids, crude oil, and petrochemical products. This \"toll-taker\" model enables the company to achieve high volumes, particularly with increasing demand for oil and gas.",
        'moat_1': "Efficient Scale/Network Effects",
        'moat_2': "Regulatory Barriers",
        'moat_3': "Cost Advantages",
        'moat_4': "High Switching Costs",
        'peer_a': "Enbridge",
        'peer_b': "Kinder Morgan",
        'peer_c': "Energy Transfer"
    },
    'EQIX': {
        'description': "Equinix Inc. is a global digital infrastructure company that provides interconnection and data center services to businesses worldwide. Headquartered in Redwood City, California, Equinix operates a vast network of over 240 data centers across 27 countries, serving as a pivotal player in the digital ecosystem. The company has evolved its branding to describe itself as a \"digital infrastructure company,\" emphasizing its role in enabling digital transformation.",
        'business_model': "Equinix's business model is centered around offering multi-tenant data center solutions and fostering a robust digital ecosystem. Key aspects of its business model include: Colocation Services, Interconnection Services, and Managed Services. Equinix generates revenue predominantly through recurring fees from colocation services, interconnection fees, and managed IT infrastructure services. These recurring revenue streams, often based on long-term contracts, contribute to a stable and predictable financial model.",
        'moat_1': "Network Effect",
        'moat_2': "Switching Costs",
        'moat_3': "Global Platform and Ecosystem",
        'moat_4': "Service Excellence and Operational Quality",
        'peer_a': "Digital Realty Trust",
        'peer_b': "CyrusOne",
        'peer_c': "NTT Communications"
    },
    'EURN': {
        'description': "Euronav NV, soon to be known as CMB.TECH NV, is undergoing a significant strategic transformation, shifting from a pure-play crude oil tanker company to a diversified maritime group with a strong focus on decarbonization.",
        'business_model': "Euronav's business model has evolved to reflect its new strategic direction. Historically, it focused on crude oil transportation through spot market operations and time charter agreements. With the acquisition of CMB.TECH, its model now includes diversification and decarbonization efforts, with divisions for Marine, H2 Infra, and H2 Industry.",
        'moat_1': "Strategic Geographic Footprint and Diversified Operations",
        'moat_2': "Stable, Fee-Based Business Model",
        'moat_3': "Integrated Service Offerings",
        'moat_4': "Operational Excellence and Financial Discipline",
        'peer_a': "MPLX",
        'peer_b': "Targa Resources Corp",
        'peer_c': "The Williams Companies, Inc."
    },
    'EXEL': {
        'description': "Exelixis Inc. is a biopharmaceutical company dedicated to the discovery, development, and commercialization of innovative small molecule therapies that target various forms of cancer.",
        'business_model': "Exelixis' business model is characterized by a combination of direct commercialization of its approved therapies and strategic collaborations. It primarily generates revenue through the direct sales and commercialization of its approved oncology products, particularly CABOMETYX. The company actively engages in strategic collaborations and licensing agreements to enhance its research pipeline and expand the global reach of its products.",
        'moat_1': "Patents",
        'moat_2': "First-Mover Advantage",
        'moat_3': "Innovative Research and Development",
        'moat_4': "Strong Product Portfolio and Pipeline",
        'peer_a': "Alnylam Pharmaceuticals",
        'peer_b': "Biogen",
        'peer_c': "Incyte"
    },
    'FANG': {
        'description': "Diamondback Energy Inc. is an independent oil and natural gas company based in Midland, Texas. The company's primary business involves the acquisition, development, exploration, and exploitation of unconventional, onshore oil and natural gas reserves. Their operations are concentrated in the Permian Basin, specifically focusing on the horizontal development of the Spraberry, Wolfcamp, and Bone Spring formations in West Texas and New Mexico.",
        'business_model': "Diamondback Energy's business model is centered on hydrocarbon exploration and production. They also provide midstream services, which include both upstream and midstream operations. The company aims for business success through a disciplined commitment to excellence, efficiency, and a low-cost structure. Their strategic approach includes integrating technological capabilities, forming strategic partnerships, and maintaining a focused operational model to transform the traditional hydrocarbon extraction landscape.",
        'moat_1': "Lowest-Cost Producer",
        'moat_2': "Premier Permian Basin Acreage",
        'moat_3': "Extensive Drilling Inventory",
        'moat_4': "Operational Excellence",
        'peer_a': "ConocoPhillips",
        'peer_b': "EOG Resources",
        'peer_c': "EQT"
    },
    'FCFS': {
        'description': "FirstCash Holdings Inc. is a prominent international provider of financial services, primarily focusing on pawn operations and technology-driven retail point-of-sale (POS) payment solutions. The company's core business model revolves around serving cash and credit-constrained consumers.",
        'business_model': "FirstCash's business model is structured around two main lines of business: pawn operations (providing small, non-recourse pawn loans secured by personal property and buying/selling merchandise) and retail POS payment solutions (offering lease-to-own and retail finance payment solutions through American First Finance). The company aims to expand its operations through growth in pawn receivables and inventories, opening new stores, and strategic acquisitions.",
        'moat_1': "Counter-cyclical Business Model",
        'moat_2': "Extensive Footprint and Brand Recognition",
        'moat_3': "Leading Market Position",
        'moat_4': "Diversified Revenue Streams",
        'peer_a': "OneMain Holdings, Inc.",
        'peer_b': "Qifu Technology Inc.",
        'peer_c': "Credit Acceptance Corp."
    },
    'FRO': {
        'description': "Frontline Ltd. is a leading global shipping company specializing in the maritime transportation of crude oil and refined petroleum products. The company owns and operates a large fleet of oil tankers, including Very Large Crude Carriers (VLCCs), Suezmax tankers, and Aframax (LR2) tankers.",
        'business_model': "Frontline's business model is centered around the ownership and operation of its tanker fleet, employing its vessels in both the spot and time charter markets. Key aspects include fleet ownership and operation, chartering services to third-party clients, strategic partnerships, vessel acquisition and maintenance, and market exposure.",
        'moat_1': "High Capital Investment Barriers",
        'moat_2': "Cost Advantage from Scale and Modernity",
        'moat_3': "Strategic Relationships",
        'moat_4': "",
        'peer_a': "DHT Holdings Inc.",
        'peer_b': "International Seaways Inc.",
        'peer_c': "Nordic American Tankers Limited"
    },
    'FSK': {
        'description': "FS KKR Capital Corp. (FSK) is a publicly traded business development company (BDC) that specializes in providing customized credit solutions to private middle-market U.S. companies.",
        'business_model': "FSK's business model is centered on its disciplined investment strategy, which primarily focuses on senior secured debt, second lien secured debt, and to a lesser extent, subordinated debt and equity investments. It generates income primarily from the interest and fees earned on its debt investments.",
        'moat_1': "Scale and Resources",
        'moat_2': "Experienced Management",
        'moat_3': "Disciplined Investment Approach",
        'moat_4': "Flexible Capital Base",
        'peer_a': "Ares Capital",
        'peer_b': "Blue Owl Capital",
        'peer_c': "Blackstone Secured Lending"
    },
    'FUJHY': {
        'description': "Fujifilm Holdings Corporation is a Japanese multinational conglomerate that has diversified its operations across several key sectors.",
        'business_model': "Fujifilm's business model is characterized by its strategic diversification and strong emphasis on research and development (R&D). The company successfully transitioned from its traditional photography roots to become a leader in healthcare and advanced materials, leveraging its core technologies in new fields.",
        'moat_1': "Strategic Diversification",
        'moat_2': "Advanced Technological Expertise",
        'moat_3': "Global Production and Supply Chain",
        'moat_4': "Strong Market Position",
        'peer_a': "Canon Inc.",
        'peer_b': "Ricoh Co Ltd",
        'peer_c': "Seiko Epson Corp"
    },
    'FULT': {
        'description': "Fulton Financial Corporation is a regional financial services holding company headquartered in Lancaster, Pennsylvania, with over $30 billion in assets. It operates primarily through its subsidiary, Fulton Bank, offering a wide range of financial products and services across Pennsylvania, Maryland, Delaware, New Jersey, and Virginia.",
        'business_model': "Fulton Financial Corporation's business model is centered on a community banking approach, emphasizing strong relationships with local customers and communities through decentralized decision-making and local market expertise. Its core business activities include branch banking, consumer lending, commercial banking, and investment management and planning services.",
        'moat_1': "Diversified Revenue Streams",
        'moat_2': "Strong Capital Position",
        'moat_3': "Community-Oriented Banking",
        'moat_4': "Strategic Growth",
        'peer_a': "Ally Financial Inc.",
        'peer_b': "WesBanco",
        'peer_c': "Prosperity Bank"
    },
    'FUTU': {
        'description': "Futu Holdings Limited is an investment holding company that operates a digitized brokerage and wealth management platform across China, Hong Kong, the United States, and internationally. The company aims to transform the investment experience by providing fully digitized financial services.",
        'business_model': "Futu's business model revolves around providing a one-stop digital platform for investing, generating revenue from various sources including brokerage commissions, interest income from margin financing and securities lending, and other income from wealth management and advisory services.",
        'moat_1': "Technology-Driven Platform",
        'moat_2': "Strong Brand Reputation and User Base",
        'moat_3': "Market Dominance and Global Expansion",
        'moat_4': "Diversified Revenue Streams",
        'peer_a': "Robinhood Markets",
        'peer_b': "Nomura",
        'peer_c': "Interactive Brokers"
    },
    'GBCI': {
        'description': "Glacier Bancorp Inc. is a regional multi-bank holding company that provides a comprehensive range of personal and commercial banking services. Headquartered in Kalispell, Montana, the company operates through 221 locations across Montana, Idaho, Utah, Washington, Wyoming, Colorado, Arizona, and Nevada.",
        'business_model': "Glacier Bancorp Inc. operates on a \"community banking model.\" This model is characterized by decentralized operations, allowing local bank divisions significant autonomy. It focuses on local decision-making, leveraging resources from the larger organization, and growth through strategic acquisitions.",
        'moat_1': "Low Cost of Deposits",
        'moat_2': "Strong Regional Presence and Community Focus",
        'moat_3': "Consistent Financial Performance",
        'moat_4': "Capital Strength and Risk Management",
        'peer_a': "United Bankshares",
        'peer_b': "Capital One Financial",
        'peer_c': "Pinnacle Financial Partners"
    },
    'GBDC': {
        'description': "Golub Capital BDC Inc. (GBDC) is an externally managed, closed-end investment company that operates as a business development company (BDC) under the Investment Company Act of 1940. It is managed by GC Advisors LLC, an affiliate of Golub Capital, a prominent private credit manager.",
        'business_model': "Golub Capital BDC Inc.'s business model revolves around several key components: investment focus (primarily first lien senior secured loans to middle-market companies), target market (middle-market companies, often sponsored by private equity firms), direct origination, revenue generation (interest income and fees from debt investments, potential capital gains from equity investments), diversified portfolio, and rigorous underwriting and risk management.",
        'moat_1': "Market-Leading Scale and Origination Model",
        'moat_2': "Deep Industry Expertise and Rigorous Underwriting",
        'moat_3': "Proprietary Technology and Operational Infrastructure",
        'moat_4': "Established Relationships with Private Equity Sponsors",
        'peer_a': "Ares Capital",
        'peer_b': "Blue Owl Capital",
        'peer_c': "Blackstone Secured Lending"
    },
    'GEHC': {
        'description': "GE HealthCare Technologies Inc. is an American health technology company based in Chicago, Illinois, that was spun off from General Electric in January 2023. It operates as a leading global innovator in medical technology, pharmaceutical diagnostics, and digital solutions.",
        'business_model': "GE HealthCare's business model is centered on providing integrated solutions, services, and data analytics to healthcare providers. Key aspects of their business model include direct sales and account management, innovation and technology development, partnerships, service and support, and global reach.",
        'moat_1': "Leading Market Position",
        'moat_2': "High Barriers to Entry",
        'moat_3': "Intangible Assets",
        'moat_4': "Switching Costs",
        'peer_a': "Koninklijke Philips",
        'peer_b': "Siemens Healthineers",
        'peer_c': "Zimmer Biomet"
    },
    'GPI': {
        'description': "Group 1 Automotive Inc. is a Fortune 250 (formerly Fortune 300) international automotive retailer that operates a network of automotive dealerships and collision centers in the United States and the United Kingdom.",
        'business_model': "Group 1 Automotive's business model is centered around maximizing return on investment for stockholders through several key components: vehicle sales (new and used cars and light trucks), financing and insurance (F&I), parts and service, and an omni-channel approach. They also focus on business growth through portfolio and operations optimization, leading customer experience, and being an OEM partner of choice.",
        'moat_1': "Scale and Geographic Diversification",
        'moat_2': "Multi-Brand Strategy",
        'moat_3': "Robust After-Sales Services",
        'moat_4': "Digital Innovation",
        'peer_a': "Penske Automotive Group, Inc.",
        'peer_b': "Lithia Motors Inc.",
        'peer_c': "AutoNation"
    },
    # ... add all other researched companies here
}

try:
    df = pd.read_csv(large_missing_path)

    for ticker, data in all_researched_data.items():
        idx = df[df['ticker'] == ticker].index
        if not idx.empty:
            for col, value in data.items():
                df.loc[idx, col] = value
        else:
            print(f"Warning: Ticker {ticker} not found in {large_missing_path}. Skipping update for this ticker.")

    # Save the updated DataFrame back to the CSV
    # pandas to_csv will automatically handle quoting correctly
    df.to_csv(large_missing_path, index=False)
    print(f"Successfully updated {large_missing_path} with all researched data.")

except FileNotFoundError:
    print(f"Error: The file {large_missing_path} was not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
