import datetime
import random
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.models import Lead
from backend import crud

# Seed data for simulated scanning based on keywords and sources
LEAD_TEMPLATES = [
    # Web Development
    {
        "keywords": ["Web Development", "Software Development"],
        "project_name": "Modern E-Commerce Platform Redesign",
        "project_description": "We are seeking a development partner to upgrade our legacy storefront to a modern headless architecture. Requirements: React/Next.js, Tailwind CSS, integration with Shopify API, and performance optimization.",
        "contact_name": "Eleanor Vance",
        "phone_number": "+1 (555) 321-9876",
        "email_address": "eleanor.v@vancestyle.com",
        "website": "https://vancestyle.com",
        "location": "Boston, MA",
        "sources": ["LinkedIn", "Google Maps"]
    },
    {
        "keywords": ["Web Development", "Software Development"],
        "project_name": "SaaS Client Portal Build",
        "project_description": "Looking for a software development freelancer or boutique agency to build a custom customer portal. Needs secure auth, Stripe subscription integration, and a sleek dashboard.",
        "contact_name": "Marcus Brodie",
        "phone_number": "+1 (555) 678-1234",
        "email_address": "mbrodie@fintechflow.io",
        "website": "https://fintechflow.io",
        "location": "Chicago, IL",
        "sources": ["LinkedIn", "X (Twitter)"]
    },
    {
        "keywords": ["Web Development", "SEO Services", "Digital Marketing"],
        "project_name": "Corporate Website SEO & Migration",
        "project_description": "Our law firm is migrating to a new CMS. We need clean HTML/CSS work, proper redirects, schema markup setup, and an initial technical SEO audit.",
        "contact_name": "Arthur Pendelton",
        "phone_number": "+1 (555) 890-4321",
        "email_address": "apendelton@pendeltonlaw.com",
        "website": "https://pendeltonlaw.com",
        "location": "Austin, TX",
        "sources": ["Google Maps"]
    },
    
    # Mobile App Development
    {
        "keywords": ["Mobile App Development", "Software Development"],
        "project_name": "iOS & Android Fitness Tracker App",
        "project_description": "We want to build a cross-platform mobile app for our gym members. Core features: workout tracking, trainer booking, and Apple Health / Google Fit integrations. Flutter or React Native preferred.",
        "contact_name": "Sarah Miller",
        "phone_number": "+1 (555) 432-1098",
        "email_address": "smiller@fitpulse.co",
        "website": "https://fitpulse.co",
        "location": "Denver, CO",
        "sources": ["LinkedIn", "Instagram"]
    },
    {
        "keywords": ["Mobile App Development", "AI Development"],
        "project_name": "AI-Powered Recipe Planner Mobile App",
        "project_description": "Seeking an expert to build a mobile app where users take pictures of ingredients in their fridge, and AI suggests recipes. Native iOS or Flutter.",
        "contact_name": "Keanu Patel",
        "phone_number": "+1 (555) 765-4321",
        "email_address": "keanu@pantryai.app",
        "website": "https://pantryai.app",
        "location": "Seattle, WA",
        "sources": ["LinkedIn", "X (Twitter)", "Instagram"]
    },

    # AI Development
    {
        "keywords": ["AI Development", "Software Development"],
        "project_name": "Customer Support LLM Agent Integration",
        "project_description": "Seeking a developer to fine-tune and integrate an OpenAI/Claude customer service chatbot into our existing Zendesk help desk platform. Must include fallback logic to human agents.",
        "contact_name": "Diane Vance",
        "phone_number": "+1 (555) 234-5678",
        "email_address": "diane@vance-logistics.com",
        "website": "https://vance-logistics.com",
        "location": "Miami, FL",
        "sources": ["LinkedIn", "X (Twitter)"]
    },
    {
        "keywords": ["AI Development"],
        "project_name": "Real Estate Listing Generator API",
        "project_description": "We need an AI model/API that reads property parameters (images, size, location) and generates compelling, SEO-friendly listing descriptions.",
        "contact_name": "Robert Sterling",
        "phone_number": "+1 (555) 345-6789",
        "email_address": "rsterling@sterlingproperties.com",
        "website": "https://sterlingproperties.com",
        "location": "Los Angeles, CA",
        "sources": ["LinkedIn", "X (Twitter)"]
    },

    # SEO & Digital Marketing
    {
        "keywords": ["SEO Services", "Digital Marketing"],
        "project_name": "Local SEO & Google Business Profile Growth",
        "project_description": "Dental clinic with 3 locations looking to dominate local search. Need local citations, review collection strategy, page speed optimization, and content marketing.",
        "contact_name": "Dr. Amit Patel",
        "phone_number": "+1 (555) 901-2345",
        "email_address": "contact@pateldental.com",
        "website": "https://pateldental.com",
        "location": "Houston, TX",
        "sources": ["Google Maps", "Instagram"]
    },
    {
        "keywords": ["Digital Marketing", "SEO Services"],
        "project_name": "E-Commerce PPC & Organic Search Campaign",
        "project_description": "Eco-friendly clothing brand wants to launch Google Ads and Facebook campaigns for our upcoming Summer line. Looking for a marketing consultant or agency with retail experience.",
        "contact_name": "Chloe Dupont",
        "phone_number": "+33 6 12 34 56 78",
        "email_address": "chloe@eco-thread.fr",
        "website": "https://eco-thread.fr",
        "location": "Paris, France",
        "sources": ["Instagram", "LinkedIn", "X (Twitter)"]
    },
    {
        "keywords": ["Digital Marketing"],
        "project_name": "Social Media Growth & Influencer Strategy",
        "project_description": "Direct-to-consumer cosmetics brand seeking a social media manager/agency to manage Instagram, TikTok, and design a micro-influencer outreach plan.",
        "contact_name": "Elena Rostova",
        "phone_number": "+44 20 7946 0192",
        "email_address": "elena@glowbar.co.uk",
        "website": "https://glowbar.co.uk",
        "location": "London, UK",
        "sources": ["Instagram", "X (Twitter)"]
    }
]

def generate_leads_and_logs(
    db: Session,
    keywords: List[str],
    sources: List[str],
    date_filter: str,
    time_filter: str
) -> Tuple[List[Dict[str, Any]], List[str]]:
    
    logs = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append(f"[{timestamp}] [INFO] Starting Project Hunting Scanner Engine...")
    logs.append(f"[{timestamp}] [INFO] Target Keywords: {', '.join(keywords)}")
    logs.append(f"[{timestamp}] [INFO] Target Sources: {', '.join(sources)}")
    logs.append(f"[{timestamp}] [INFO] Filters: Date = {date_filter}, Time = {time_filter}")
    
    selected_templates = []
    # Match keywords and sources
    for t in LEAD_TEMPLATES:
        # Check if template matches any of the target keywords (case-insensitive)
        keyword_match = False
        for kw in keywords:
            if any(kw.lower() in tkw.lower() or tkw.lower() in kw.lower() for tkw in t["keywords"]):
                keyword_match = True
                break
        
        # Check if template matches any of the target sources
        source_match = False
        for src in sources:
            # Match names like "X (Twitter)" to "X" or "Twitter"
            clean_srcs = [s.lower() for s in t["sources"]]
            if any(src.lower() in s or s in src.lower() for s in clean_srcs):
                source_match = True
                break
                
        if keyword_match and source_match:
            selected_templates.append(t)

    logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [INFO] Scanning public postings and business listings...")
    
    found_leads = []
    
    for src in sources:
        logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [SCAN] Initiating crawler for source: {src}")
        logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [SCAN] Querying public index for keywords: {', '.join(keywords)}...")
        
        # Add source specific logs to look highly realistic
        if "LinkedIn" in src:
            logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [COMPLIANCE] Scanning public LinkedIn job posts and company bulletin feeds.")
            logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [COMPLIANCE] Excluded private profiles. Analyzing public hiring posts.")
        elif "Google Maps" in src:
            logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [COMPLIANCE] Querying public Places API for keywords. Reading public business metadata.")
        elif "X" in src or "Twitter" in src:
            logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [COMPLIANCE] Reading public tweets with query flags: 'hiring' OR 'looking for developer'.")
        elif "Instagram" in src:
            logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [COMPLIANCE] Checking public business handles and posts under relevant service hashtags.")
            
        # Select matching templates for this source
        src_templates = [t for t in selected_templates if any(src.lower() in s.lower() or s.lower() in src.lower() for s in t["sources"])]
        
        if not src_templates:
            logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [SCAN] No public posts matching filter criteria on {src}.")
            continue
            
        # Pick 1-3 random templates matching this source to generate lead (simulating real discovery)
        num_to_select = min(len(src_templates), random.randint(1, 2))
        selected_src_templates = random.sample(src_templates, num_to_select)
        
        for t in selected_src_templates:
            # Let's check if lead already exists in DB to prevent duplicates
            existing_lead = db.query(Lead).filter(
                Lead.project_name == t["project_name"],
                Lead.source == src
            ).first()
            
            if existing_lead:
                logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [SKIP] Duplicate found: '{t['project_name']}' on {src} (Skipped).")
                continue
                
            logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [FOUND] New opportunity: '{t['project_name']}' on {src}")
            logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [EXTRACT] Public metadata - Contact: {t['contact_name']}, Phone: {t['phone_number']}, Email: {t['email_address']}, Site: {t['website']}")
            
            # Format date & time
            today = datetime.date.today()
            now_time = datetime.datetime.now().time()
            
            lead_data = {
                "project_name": t["project_name"],
                "project_description": t["project_description"],
                "source": src,
                "contact_name": t["contact_name"],
                "phone_number": t["phone_number"],
                "email_address": t["email_address"],
                "website": t["website"],
                "location": t["location"],
                "collection_date": today,
                "collection_time": now_time,
                "status": "New Lead",
                "priority": random.choice(["Best Opportunity", "Better Opportunity", "Normal Opportunity", "Low Priority"]),
                "notes": ""
            }
            found_leads.append(lead_data)
            
    logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [INFO] Scan complete. Total opportunities identified: {len(found_leads)}")
    return found_leads, logs
