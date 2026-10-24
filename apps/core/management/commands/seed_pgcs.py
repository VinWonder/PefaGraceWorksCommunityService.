"""
Load all content from the PEFA GraceWorks organisation profile into the database.

    python manage.py seed_pgcs            # safe to run again: updates instead of duplicating
    python manage.py seed_pgcs --demo     # also adds sample events, a blog post and demo records
"""
from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.core.models import FAQ, CoreValue, HeroSlide, ImpactStat, Milestone, Partner, Person, SiteSettings
from apps.programs.models import FocusArea, FocusAreaItem, ImplementationStage, Indicator, IndicatorMeasurement, Project, ServiceStandard

ABOUT = """PEFA GraceWorks Community Services is a registered Community-Based Organization (CBO) founded under the auspices of the Pentecostal Evangelistic Fellowship of Africa (PEFA) Church. Rooted in Christian faith and guided by biblical principles of compassion, stewardship, and service, the organization was established to extend the Church's mission beyond the pulpit and into the heart of the community. Our journey began with a shared vision among believers who sought to address the pressing social and economic challenges faced by vulnerable families within Kolwa Central Ward and the larger Kisumu East Sub-County.

Since its inception, PEFA GraceWorks Community Services has remained steadfast in promoting holistic transformation, empowering individuals spiritually, socially, and economically. Our faith-inspired approach acknowledges that true development occurs when both the soul and society thrive. Through community outreach, mentorship, education, and economic empowerment programs, we strive to restore dignity, hope, and self-reliance among the most marginalized members of our community.

Our formation was born out of a growing awareness that sustainable community change requires a coordinated, faith-driven response. The founding members, drawn from various professional and ministry backgrounds, recognized the need to bridge the gap between spiritual growth and everyday wellbeing. This conviction gave rise to a structured community arm of the church that actively partners with stakeholders, local authorities, and development actors to deliver impactful interventions.

Today, PEFA GraceWorks Community Services stands as a beacon of hope and transformation in Kisumu County. Our commitment to service is anchored on the belief that faith without works is incomplete, and that God's grace compels us to act. We continue to nurture a community where every person can flourish, spiritually empowered, socially connected, and economically sustained."""

LEGAL = """PEFA GraceWorks Community Services operates as a duly registered Community-Based Organization (CBO) under the Ministry of Labour and Social Protection, pursuant to the Community Group Registration Act (No. 3 of 2022). The organization received its Certificate of Registration No. DSD/42/238/02/115935 on 22nd July 2025, issued by the Directorate of Social Development.

The organization's area of jurisdiction covers Kolwa Central Ward, located within Kisumu East Sub-County, Kisumu East Constituency, in Kisumu County. From this base, we coordinate programs and partnerships to reach both urban and peri-urban communities.

While faith remains our foundation, the CBO operates autonomously, with its own constitution, governance structures, and management systems to promote transparency, accountability, and inclusivity. We submit annual returns to the Department of Social Development and follow sound financial management practices in line with our constitution and the Public Benefit Organizations (PBO) framework."""

CHURCH = """As the outreach arm of the Pentecostal Evangelistic Fellowship of Africa (PEFA), we draw moral guidance, legitimacy and logistical support from the Church's well-established network. The Church provides a strong foundation for community mobilisation, volunteer engagement and spiritual mentorship.

Through joint missions, discipleship programs and social outreach, our interventions stay grounded in Christian values while addressing practical community needs: faith without works is incomplete, and God's grace compels us to act."""

VALUES = [
    ("Faith and Integrity", "shield-check", "We are guided by unwavering faith in God and a commitment to uphold honesty, transparency, and accountability in all our actions. Our decisions and relationships are built on biblical truth and moral integrity."),
    ("Compassion and Service", "heart", "We believe that love and empathy are the foundation of true service. Our work is inspired by Christ's compassion, reaching out to the most vulnerable with care, respect, and dignity."),
    ("Empowerment and Self-Reliance", "tools", "We are dedicated to equipping individuals and communities with knowledge, skills, and resources that enable them to realize their full potential and lead self-sustaining lives."),
    ("Collaboration and Partnership", "people", "We value teamwork and strategic alliances with like-minded organizations, government agencies, and community stakeholders to amplify our impact and share resources for greater good."),
    ("Excellence and Stewardship", "award", "We pursue excellence in all our initiatives, ensuring that every resource entrusted to us is managed prudently and used effectively to bring lasting transformation."),
    ("Inclusivity and Equity", "universal-access", "We uphold the dignity of every person regardless of gender, age, ability, or social background, promoting fairness, equality, and respect for diversity in all our programs and interactions."),
]

FOCUS = [
    {
        "title": "Faith and Outreach", "slug": "faith-and-outreach", "icon": "book",
        "summary": "Hope, healing and spiritual support through missions, chaplaincy and counselling in hospitals, prisons and neighbourhoods.",
        "description": "<p>Faith is at the core of our identity and service. Through our Faith and Outreach programs, we extend the message of hope, healing, and salvation to individuals and communities. Our teams engage in evangelistic missions, chaplaincy, and counseling within hospitals, prisons, and marginalized neighborhoods.</p><p>We also conduct discipleship sessions, community fellowships, and prayer outreaches aimed at nurturing spiritual growth and moral transformation. By integrating faith with action, we seek to restore dignity and remind every individual that they are valued and loved by God.</p>",
        "goal": "To spread the Gospel of Christ and restore hope among individuals and communities through faith-based engagement and compassionate service.",
        "activities": ["Organizing evangelism missions and community fellowships.", "Conducting hospital and prison visitations for counseling and spiritual support.", "Training volunteers and church leaders in pastoral care and outreach.", "Supporting vulnerable families through prayer and material assistance."],
        "outcomes": ["Strengthened spiritual and moral values in the community.", "Increased participation in faith-based activities and fellowships.", "Renewed hope and psychosocial wellbeing among marginalized groups."],
        "charter": ("Missionary outreach, hospital and prison ministry, counseling, and community evangelism.", "To extend hope, compassion, and spiritual support to all without discrimination.", "Outreach programs conducted quarterly and spiritual support available on request throughout the year."),
    },
    {
        "title": "Health", "slug": "health", "icon": "heart-pulse",
        "summary": "Community wellness, medical camps, maternal and child health, mental health support and trained community health volunteers.",
        "description": "<p>Our health initiatives are centered on the conviction that physical wellbeing is integral to holistic development. We aim to promote access to promotive, preventive, and curative health services through community wellness programs and partnerships with health facilities.</p><p>Activities include health education, medical camps, maternal and child health awareness, mental health support, and training of community health volunteers. By fostering healthy lifestyles and improving access to essential care, we empower communities to live productive and fulfilling lives.</p>",
        "goal": "To promote healthy living and improve access to quality health services for community members.",
        "activities": ["Conducting community medical camps and health awareness campaigns.", "Facilitating nutrition and hygiene education in schools and households.", "Partnering with health facilities to enhance service delivery.", "Supporting mental health awareness and counseling services."],
        "outcomes": ["Improved community health-seeking behavior.", "Reduced prevalence of preventable diseases.", "Strengthened community capacity for health promotion and disease prevention."],
        "charter": ("Community wellness programs, preventive health education, and development of a community clinic.", "To promote access to quality, affordable, and inclusive health services.", "Regular community health forums, annual medical camps, and prompt service at our wellness centre."),
    },
    {
        "title": "Water and Sanitation", "slug": "water-and-sanitation", "icon": "droplet",
        "summary": "Boreholes, water purification and hygiene education so every household and school has safe, reliable water.",
        "description": "<p>Clean water and adequate sanitation are fundamental human rights and key determinants of community health. PEFA GraceWorks Community Services is committed to improving water access and hygiene standards across Kolwa Central and neighboring areas.</p><p>We undertake initiatives such as drilling boreholes, installing water purification systems, and promoting household-level hygiene practices. Our goal is to ensure that communities, schools, and households have safe, reliable water sources that reduce disease burden and improve quality of life.</p>",
        "goal": "To ensure reliable access to clean and safe water while promoting good sanitation and hygiene practices.",
        "activities": ["Drilling and maintaining community boreholes.", "Installing water purification and storage systems.", "Promoting household sanitation through community-led hygiene education.", "Partnering with schools to enhance water and sanitation facilities."],
        "outcomes": ["Increased access to clean and safe drinking water.", "Improved hygiene and sanitation practices in households and institutions.", "Reduction in water-borne diseases and related health risks."],
        "charter": ("Borehole drilling, installation of water purification systems, and sanitation education.", "To ensure every household and school in our service area has access to clean, safe water.", "Minimum of one new water access project per year; periodic maintenance and monitoring of existing systems."),
    },
    {
        "title": "Education Support", "slug": "education", "icon": "mortarboard",
        "summary": "Bursaries, learning materials, mentorship and sanitary towels so no child drops out of school for lack of means.",
        "description": "<p>Education remains a cornerstone of empowerment and long-term poverty reduction. We mobilize resources to support needy learners through bursaries, provision of learning materials, and mentorship programs.</p><p>Recognizing the challenges faced by adolescent girls, we also supply sanitary towels and promote menstrual health education to ensure uninterrupted school attendance. By working with schools, parents, and local leaders, we create an enabling environment where every child can access quality education and pursue their dreams.</p>",
        "goal": "To enhance access to education and support equitable learning opportunities for children and youth from vulnerable backgrounds.",
        "activities": ["Providing bursaries and educational materials to needy learners.", "Distributing sanitary towels and offering menstrual health education to adolescent girls.", "Mentorship and life-skills training for students.", "Collaborating with schools, parents, and faith institutions to promote retention and performance."],
        "outcomes": ["Improved school attendance and retention, particularly for girls.", "Enhanced academic performance among supported learners.", "Strengthened partnerships between schools, families, and faith institutions."],
        "charter": ("Provision of bursaries, mentorship, sanitary towels, and other learning support materials.", "To promote educational equity for needy and vulnerable learners.", "Timely disbursement of bursaries each academic year and continuous support to beneficiaries."),
    },
    {
        "title": "Economic Empowerment", "slug": "economic-empowerment", "icon": "briefcase",
        "summary": "Vocational skills, entrepreneurship and financial literacy for youth, women and single mothers.",
        "description": "<p>Economic stability is critical to sustaining community transformation. Our Economic Empowerment programs focus on equipping youth, women, and single mothers with vocational and entrepreneurial skills to enhance their livelihoods.</p><p>We provide training in technical trades, small business management, and financial literacy, and we plan to establish a fully equipped vocational training center to expand opportunities. Through these initiatives, we aim to break cycles of dependency, promote self-reliance, and nurture a generation that contributes meaningfully to the economy.</p>",
        "goal": "To promote self-reliance and income generation among youth, women, and marginalized groups through vocational training and enterprise development.",
        "activities": ["Offering skills development in trades such as tailoring, mechanics, and ICT.", "Providing entrepreneurship and financial literacy training.", "Supporting start-up initiatives and small enterprises with tools and equipment.", "Establishing a vocational training center to serve as a hub for skill-building."],
        "outcomes": ["Increased employment and income opportunities for youth and women.", "Growth of small-scale enterprises and household economic stability.", "Strengthened local capacity for innovation and self-employment."],
        "charter": ("Vocational skills training, micro-enterprise support, and establishment of a community resource center.", "To strengthen self-reliance through skills development and enterprise growth.", "At least two empowerment training sessions annually and ongoing mentorship for graduates."),
    },
]

PROJECTS = [
    ("Community Health Clinic", "community-health-clinic", "health", "fundraising", True,
     "Our flagship project: an accessible, affordable clinic in Kolwa Central offering promotive, preventive and basic curative care.",
     "<p>The organization's foremost infrastructure goal is the construction of a Community Health Clinic to address the growing need for accessible, affordable, and quality healthcare services in Kolwa Central Ward and the wider Kisumu East Sub-County.</p><p>The facility will provide promotive, preventive, and basic curative services, with a special focus on maternal and child health, non-communicable diseases, and community health education. It will also integrate spiritual care and counselling, host periodic medical camps, and serve as a referral and outreach centre for faith-based and public health initiatives.</p><h3>Expected outcomes</h3><ul><li>Improved access to primary healthcare services for underserved households.</li><li>Reduced maternal, infant, and preventable disease morbidity rates.</li><li>Strengthened linkage between faith-based health promotion and public health systems.</li></ul>",
     "Accessible, affordable healthcare for at least 5,000 residents annually."),
    ("Community Hall and Resource Centre", "community-resource-centre", "economic-empowerment", "fundraising", False,
     "A multipurpose hub for vocational training, youth mentorship, digital literacy, community meetings and worship.",
     "<p>PGCS aims to establish a Community Hall and Resource Center that will serve as a dynamic hub for learning, social interaction, and empowerment. The multipurpose facility will host vocational training programs, youth mentorship workshops, digital literacy sessions, and entrepreneurship clinics, as well as community meetings, cultural events, and spiritual gatherings.</p><p>The resource center will feature a modest digital lab, a library corner, and training spaces adaptable for group activities. In the long term, it will grow into a Community Empowerment Hub that promotes collaboration among local organizations, government agencies, and development partners.</p><h3>Expected outcomes</h3><ul><li>Enhanced access to skills development and knowledge-sharing opportunities.</li><li>Increased community cohesion through inclusive spaces for engagement.</li><li>Strengthened institutional capacity for program delivery and community partnerships.</li></ul>",
     "Increased community access to information, skills training, and social empowerment opportunities."),
    ("Education Support Expansion: 300 Learners", "education-300-learners", "education", "ongoing", False,
     "Scaling bursaries and mentorship from about 100 to at least 300 learners by 2028, with a focus on girls.",
     "<p>Building on the success of supporting nearly 100 learners, PGCS aims to scale up its bursary and mentorship program to reach at least 300 learners by 2028. We will strengthen partnerships with schools, churches, and sponsors to sustain scholarship funding, and continue supplying sanitary towels and mentorship for adolescent girls.</p>",
     "Improved school retention and performance among vulnerable children, especially girls."),
    ("Boreholes and Water Purification (WASH)", "wash-boreholes", "water-and-sanitation", "planned", False,
     "Borehole drilling and purification systems for schools and homesteads facing acute water shortages in Kisumu East.",
     "<p>The organization plans to implement borehole drilling and water purification projects targeting underserved areas within Kisumu East. Consultations with stakeholders are under way and feasibility studies will be conducted at identified priority sites. The projects will be complemented by hygiene promotion campaigns in schools and communities.</p>",
     "Enhanced access to clean, safe water for learning institutions and households, reducing water-borne diseases."),
    ("Vocational Skills and Livelihoods", "vocational-skills", "economic-empowerment", "planned", False,
     "Tailoring, hairdressing, carpentry, mechanics and entrepreneurship training, with business incubation and microfinance links.",
     "<p>PGCS intends to establish a vocational training and skills development program for youth, women, and single mothers. Planned courses include tailoring, hairdressing, carpentry, mechanics, and entrepreneurship. The organization also seeks to initiate small business incubation support and link trainees to microfinance institutions.</p>",
     "At least 200 beneficiaries gain employable skills and sustainable livelihoods by 2028."),
]

STAGES = [
    ("Community Needs Assessment", "Systematic identification of pressing social, health, and economic challenges through participatory appraisals, household surveys, and local consultations."),
    ("Planning and Design", "Translating needs into practical projects and interventions that align with our five thematic pillars and available resources."),
    ("Resource Mobilization", "Leveraging internal contributions, church support, government linkages, and external donor partnerships to finance activities."),
    ("Program Execution", "Implementing projects through trained volunteers, technical experts, and local committees while ensuring inclusivity and accountability."),
    ("Monitoring and Evaluation", "Continuous assessment of progress using verifiable indicators to measure efficiency, effectiveness, and community impact."),
    ("Sustainability and Scale-Up", "Strengthening local capacity, institutionalizing successful initiatives, and replicating effective models in other communities."),
]

BOARD = [
    ("Chairperson", "Provides overall leadership and ensures adherence to governance principles."),
    ("Vice Chairperson", "Assists the chair and provides leadership continuity."),
    ("Secretary", "Oversees documentation, communication, and organizational records."),
    ("Treasurer", "Manages financial oversight and ensures prudent resource use."),
    ("Program Representative", "Provides technical guidance and linkages to the community."),
    ("Program Representative", "Provides technical guidance and linkages to the community."),
    ("Church Liaison Officer", "Ensures spiritual alignment and partnership with the PEFA Church network."),
]
MANAGEMENT = [
    ("Program Coordinator", "Links governance and implementation: strategic execution, partnerships and staff supervision."),
    ("Health Lead", "Leads community wellness, medical camps and the clinic project."),
    ("Education Lead", "Runs bursaries, mentorship and the sanitary towel program."),
    ("Economic Empowerment Lead", "Runs vocational training, enterprise and financial literacy."),
    ("Water & Sanitation Lead", "Leads borehole, purification and hygiene projects."),
    ("Faith & Outreach Lead", "Coordinates missions, chaplaincy and counselling."),
]

PARTNERS = [
    ("Pentecostal Evangelistic Fellowship of Africa (PEFA) Church", "faith", "Moral guidance, legitimacy, volunteers and logistical support through the Church network."),
    ("Department of Social Development", "government", "Registration, compliance, and capacity building of CBOs."),
    ("County Department of Health, Kisumu", "government", "Health promotion programs, community health clinic development, and joint outreach initiatives."),
    ("County Department of Water and Environment", "government", "Water, sanitation, and environmental conservation projects."),
    ("Department of Education and Vocational Training", "government", "Mentorship, education support, and youth empowerment."),
    ("Local schools, churches and community leaders", "community", "Community dialogues, needs assessments and participatory evaluations."),
]

MILESTONES = [
    ("Registered as a Community-Based Organization", "Certificate No. DSD/42/238/02/115935 issued by the Directorate of Social Development.", date(2025, 7, 22), "patch-check", None),
    ("School fees paid for nearly 100 learners", "Learners from vulnerable households in primary and secondary school continued their education uninterrupted. We also provided uniforms and stationery to selected beneficiaries.", None, "mortarboard", "education"),
    ("Sanitary towels and mentorship for girls", "Adolescent girls received sanitary towels and mentorship sessions to reduce absenteeism, and parents joined forums on faith-based child nurturing.", None, "gender-female", "education"),
    ("Hospital and prison outreach", "With the PEFA Church network we held hospital visits, fellowship sessions in correctional facilities and ministry among vulnerable groups, giving spiritual and material support.", None, "book", "faith-and-outreach"),
    ("Health education campaigns", "Awareness campaigns with local clinics on hygiene, nutrition and preventive care, and initial groundwork for the Community Health Clinic.", None, "heart-pulse", "health"),
    ("Water project consultations", "Consultations with stakeholders on water access and purification for schools and homesteads; feasibility studies for borehole drilling are being prepared.", None, "droplet", "water-and-sanitation"),
    ("Strategic plan and governance in place", "A strategic plan aligned with county and national priorities, a governance structure with clear accountability, and working relations with faith-based and government stakeholders.", None, "diagram-3", None),
]

INDICATORS = [
    ("education", "Learners supported with school fees / bursaries", "learners", 0, 300, 98),
    ("health", "Residents reached by clinic services each year", "residents", 0, 5000, 0),
    ("economic-empowerment", "Beneficiaries trained in employable skills", "people", 0, 200, 0),
    ("water-and-sanitation", "New water access projects completed", "projects", 0, 3, 0),
    ("faith-and-outreach", "Outreach missions held", "missions", 0, 12, 2),
]

FAQS = [
    ("Who can ask PEFA GraceWorks for help?", "Anyone living in Kolwa Central Ward and the wider Kisumu East Sub-County, whatever their faith, gender, age or ability. Use the Request help form or visit us at the PEFA Church compound."),
    ("How do you decide who gets help first?", "Every request gets a vulnerability score based on income, household size, children, disability, age of the household head and urgency. Our team reviews the highest scores first, and households helped recently move down the list so support is spread fairly."),
    ("Is my donation safe?", "M-Pesa gifts go straight to our registered Paybill and you receive an M-Pesa receipt plus our own reference. We publish progress on every project and submit annual returns to the Department of Social Development."),
    ("Do I need to be a member of PEFA Church to volunteer?", "No. We welcome volunteers of good character from every background who share our heart for service."),
    ("How long until my complaint is answered?", "Our service charter promises acknowledgement within 48 hours and a resolution within 14 working days. You can track progress with your reference number."),
]


class Command(BaseCommand):
    help = "Load PEFA GraceWorks profile content (safe to re-run)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Also create sample events and a blog post")
        parser.add_argument("--if-empty", action="store_true",
                            help="Only seed a fresh database, so deploys never overwrite content edited in the admin")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["if_empty"] and FocusArea.objects.exists():
            self.stdout.write("Content already loaded; skipping seed.")
            return
        s = SiteSettings.load()
        s.org_name = "PEFA GraceWorks Community Services"
        s.short_name = "PGCS"
        s.tagline = "Empowered by Faith, Serving with Grace"
        s.closing_statement = "Together, we build thriving, holistic communities."
        s.vision = "To see thriving, holistic communities that are spiritually empowered, socially connected, and economically sustained."
        s.mission = "To nurture a holistic community empowered in the Word, sound in health, and enabled with diverse opportunities for sustainable growth and transformation."
        s.about_short = ("A faith-based Community-Based Organization of the PEFA Church, serving vulnerable families in Kolwa Central Ward "
                         "and Kisumu East through outreach, health, clean water, education and economic empowerment.")
        s.about_long = ABOUT
        s.legal_status = LEGAL
        s.church_block_text = CHURCH
        s.registration_number = "DSD/42/238/02/115935"
        s.registration_date = date(2025, 7, 22)
        s.registered_under = "Directorate of Social Development, Ministry of Labour and Social Protection"
        s.affiliation = "Pentecostal Evangelistic Fellowship of Africa (PEFA) Church"
        s.phone = "+254 728 565 413"
        s.whatsapp = "254728565413"
        s.email = s.email or "info@pefagraceworks.org"
        s.address = "Kolwa Central Ward, Kisumu East Sub-County, Kisumu County, Kenya"
        s.physical_location = "Within the PEFA Church compound, Kisumu East"
        s.save()

        for i, (title, icon, desc) in enumerate(VALUES):
            CoreValue.objects.update_or_create(title=title, defaults={"icon": icon, "description": desc, "order": i})

        areas = {}
        for i, f in enumerate(FOCUS):
            area, _ = FocusArea.objects.update_or_create(slug=f["slug"], defaults={
                "title": f["title"], "icon": f["icon"], "summary": f["summary"], "description": f["description"],
                "goal": f["goal"], "order": i})
            area.items.all().delete()
            for j, t in enumerate(f["activities"]):
                FocusAreaItem.objects.create(focus_area=area, kind="activity", text=t, order=j)
            for j, t in enumerate(f["outcomes"]):
                FocusAreaItem.objects.create(focus_area=area, kind="outcome", text=t, order=j)
            ServiceStandard.objects.update_or_create(focus_area=area, defaults=dict(zip(
                ["services_offered", "commitment", "standard"], f["charter"])))
            areas[f["slug"]] = area

        for i, (title, slug, area, status, featured, summary, desc, target) in enumerate(PROJECTS):
            Project.objects.update_or_create(slug=slug, defaults={
                "title": title, "focus_area": areas[area], "status": status, "is_featured": featured, "summary": summary,
                "description": desc, "target_outcome": target, "order": i, "location": "Kisumu East",
                "start_date": date(2025, 8, 1), "end_date": date(2028, 12, 31)})

        for i, (title, desc) in enumerate(STAGES):
            ImplementationStage.objects.update_or_create(title=title, defaults={"description": desc, "order": i})

        if not Person.objects.filter(group="board").exists():
            for i, (role, desc) in enumerate(BOARD):
                Person.objects.create(role=role, role_description=desc, group="board", order=i)
        if not Person.objects.filter(group="management").exists():
            for i, (role, desc) in enumerate(MANAGEMENT):
                Person.objects.create(role=role, role_description=desc, group="management", order=i)

        for i, (name, cat, desc) in enumerate(PARTNERS):
            Partner.objects.update_or_create(name=name, defaults={"category": cat, "description": desc, "order": i})

        for i, (title, desc, d, icon, area) in enumerate(MILESTONES):
            Milestone.objects.update_or_create(title=title, defaults={
                "description": desc, "date": d, "icon": icon, "order": i, "focus_area": areas.get(area)})

        for i, (area, name, unit, base, target, current) in enumerate(INDICATORS):
            ind, _ = Indicator.objects.update_or_create(name=name, defaults={
                "focus_area": areas[area], "unit": unit, "baseline": base, "target": target, "target_year": 2028, "order": i})
            if current:
                IndicatorMeasurement.objects.update_or_create(indicator=ind, period_end=date(2025, 9, 30), defaults={
                    "value": current, "source": "Organisation profile 2025"})

        stats = [("Learners supported", "learners", 98, "+"), ("Focus areas", "manual", 5, ""),
                 ("Residents the clinic will serve yearly", "manual", 5000, "+"), ("Learners targeted by 2028", "manual", 300, "")]
        for i, (label, source, value, suffix) in enumerate(stats):
            ImpactStat.objects.update_or_create(label=label, defaults={
                "source": source, "manual_value": value, "minimum_value": value if source != "manual" else 0,
                "suffix": suffix, "order": i})

        for i, (q, a) in enumerate(FAQS):
            FAQ.objects.update_or_create(question=q, defaults={"answer": a, "order": i})

        slides = [
            ("Empowered by faith, serving with grace", "A community arm of the PEFA Church serving vulnerable families in Kolwa Central and Kisumu East.", "Who we are", "/about/"),
            ("Keeping every child in school", "Nearly 100 learners have had their school fees paid. Help us reach 300 by 2028.", "Sponsor a learner", "/donate/?project=education-300-learners"),
            ("A clinic for 5,000 neighbours", "We are raising funds to build an affordable Community Health Clinic in Kolwa Central.", "Support the clinic", "/projects/community-health-clinic/"),
            ("Clean water for schools and homes", "Boreholes and purification systems for households facing acute water shortages.", "See the water project", "/projects/wash-boreholes/"),
        ]
        for i, (t, sub, btn, url) in enumerate(slides):
            HeroSlide.objects.update_or_create(title=t, defaults={"subtitle": sub, "button_text": btn, "button_url": url, "order": i})

        if opts["demo"]:
            self._demo(areas)
        self.stdout.write(self.style.SUCCESS("PEFA GraceWorks content loaded."))

    def _demo(self, areas):
        from apps.events.models import Event
        from apps.news.models import Category, Post

        tz = timezone.get_current_timezone()
        base = timezone.localdate()
        demo_events = [
            ("Community medical camp", "medical_camp", "health", 21, "PEFA Church compound, Kolwa Central"),
            ("Quarterly hospital outreach", "outreach", "faith-and-outreach", 35, "Jaramogi Oginga Odinga Teaching & Referral Hospital"),
            ("Girls' mentorship & sanitary towel drive", "training", "education", 49, "PEFA Church compound, Kolwa Central"),
        ]
        for title, kind, area, days, venue in demo_events:
            start = datetime.combine(base + timedelta(days=days), datetime.min.time()).replace(hour=9, tzinfo=tz)
            Event.objects.update_or_create(slug=title.lower().replace(" ", "-").replace("'", "").replace("&", "and"), defaults={
                "title": title, "kind": kind, "focus_area": areas[area], "start": start, "end": start + timedelta(hours=6),
                "venue": venue, "summary": "Sample event — edit or delete it in the admin.", "registration_open": True, "capacity": 150})
        cat, _ = Category.objects.get_or_create(slug="news", defaults={"name": "News"})
        Post.objects.update_or_create(slug="we-are-officially-registered", defaults={
            "title": "We are officially registered", "category": cat, "status": "published",
            "published_at": timezone.make_aware(datetime(2025, 7, 22, 10, 0)),
            "excerpt": "PEFA GraceWorks Community Services received its Certificate of Registration from the Directorate of Social Development.",
            "body": "<p>On 22 July 2025, PEFA GraceWorks Community Services received Certificate of Registration No. DSD/42/238/02/115935 from the Directorate of Social Development under the Community Group Registration Act (No. 3 of 2022).</p><p>This recognition lets us partner formally with county departments, development partners and donors as we work toward the Community Health Clinic, the Resource Centre and 300 supported learners by 2028.</p>"})
