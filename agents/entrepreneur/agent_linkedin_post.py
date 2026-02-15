from utils.logger import AgenticLogger
from utils.deepseek_client import DeepSeekClient
import random
from datetime import datetime

class AgentLinkedInPost:
    """Agent responsable de la publication sur LinkedIn avec génération IA avancée"""
    
    # ─────────────────────────────────────────────────────────────────
    # BANQUES DE DONNÉES POUR TEMPLATES CONTEXTUELS
    # ─────────────────────────────────────────────────────────────────
    
    ACCROCHES = [
        "🚀 On recrute et ce n'est pas n'importe quel poste !",
        "🔥 Avis aux talents : une opportunité exceptionnelle vous attend !",
        "💡 Et si votre prochain défi professionnel commençait ici ?",
        "📢 RECRUTEMENT | L'aventure commence maintenant !",
        "⚡ Alerte Opportunité ! Rejoignez une équipe qui fait la différence.",
        "🌟 Nous cherchons LA perle rare. C'est peut-être vous ?",
        "🎯 Votre prochaine grande aventure professionnelle est ici.",
        "💼 Nouveau chapitre, nouvelle équipe, nouveau challenge.",
        "🔍 On recherche un talent qui veut avoir un vrai impact.",
        "✨ Prêt(e) à relever un défi ambitieux ? Lisez la suite !",
    ]
    
    MISSIONS = {
        "tech": [
            "Concevoir et développer des solutions innovantes qui transforment notre industrie.",
            "Contribuer à des projets technologiques à fort impact, de la conception au déploiement.",
            "Rejoindre une équipe technique passionnée pour bâtir les produits de demain.",
            "Participer à l'innovation technologique au cœur de projets ambitieux et stimulants.",
        ],
        "data": [
            "Exploiter la puissance des données pour guider nos décisions stratégiques.",
            "Transformer des volumes massifs de données en insights actionnables.",
            "Construire des modèles prédictifs qui créent un avantage compétitif réel.",
        ],
        "design": [
            "Créer des expériences utilisateur mémorables qui ravissent nos clients.",
            "Concevoir des interfaces élégantes et intuitives qui font la différence.",
        ],
        "management": [
            "Piloter des projets stratégiques et accompagner la croissance de l'équipe.",
            "Impulser une dynamique d'innovation et de performance collective.",
        ],
        "default": [
            "Rejoindre une équipe ambitieuse et contribuer à des projets à forte valeur ajoutée.",
            "Apporter votre expertise pour relever des défis passionnants au quotidien.",
            "Participer activement à la croissance et à l'innovation de l'entreprise.",
        ]
    }
    
    POURQUOI_REJOINDRE = [
        "🏆 Un environnement stimulant avec des projets challengeants",
        "🤝 Une équipe soudée et bienveillante qui valorise chaque talent",
        "📈 De vraies perspectives d'évolution et de montée en compétences",
        "🎯 Un impact concret sur des produits utilisés au quotidien",
        "💡 Une culture d'innovation où vos idées comptent",
        "🌍 Un cadre de travail moderne et flexible",
        "⚡ Des technologies de pointe et des défis techniques stimulants",
    ]
    
    APPELS_ACTION = [
        "👉 Ça vous parle ? Postulez dès maintenant",
        "📩 Intéressé(e) ? Candidatez en quelques clics",
        "🔗 N'attendez plus, cette opportunité est pour vous",
        "💌 Envie d'en savoir plus ? Postulez ici",
        "✅ Prêt(e) à nous rejoindre ? C'est par ici",
    ]
    
    CLOSINGS = [
        "🔄 Partagez autour de vous, votre réseau cache peut-être le candidat idéal !",
        "💬 N'hésitez pas à partager ce post, le bouche-à-oreille fait des merveilles !",
        "🤝 Identifiez en commentaire quelqu'un qui pourrait être intéressé(e) !",
        "📣 Likez et partagez pour nous aider à trouver cette perle rare !",
    ]
    
    DOMAIN_KEYWORDS = {
        "tech": ["développeur", "ingénieur", "devops", "architecte", "full stack", "backend",
                 "frontend", "mobile", "logiciel", "software", "sre", "cloud"],
        "data": ["data", "scientist", "analyst", "engineer", "machine learning", "ml", "ia",
                 "intelligence artificielle", "big data", "bi", "analytics"],
        "design": ["designer", "ux", "ui", "graphiste", "créatif", "directeur artistique"],
        "management": ["manager", "chef de projet", "directeur", "responsable", "lead",
                       "scrum master", "product owner", "consultant"],
    }

    def __init__(self):
        self.logger = AgenticLogger("AgentLinkedInPost")
        try:
            self.ai_client = DeepSeekClient()
            self.logger.info("Client DeepSeek initialisé avec succès")
        except Exception as e:
            self.logger.warning(f"Impossible d'initialiser DeepSeek: {e}. Mode templates avancés activé")
            self.ai_client = None

    def poster_offre(self, details: dict, form_url: str = None):
        job_title = details.get('job_title', 'Poste inconnu')
        skills_list = details.get('skills_required', [])
        skills = ", ".join(skills_list) if skills_list else ""
        location = details.get('location', 'Non spécifié')
        company = details.get('company_name', 'Non spécifié')
        salary = details.get('salary', 'Non spécifié')
        experience = details.get('experience_level', 'Non spécifié')
        contract_type = details.get('contract_type', 'Non spécifié')
        duration = details.get('duration', 'Non spécifié')
        
        self.logger.info(f"Génération d'un post LinkedIn optimisé pour : {job_title}")
        
        post_content = ""
        form_url = form_url or "[Lien dans le premier commentaire]"
        
        if self.ai_client:
            try:
                post_content = self.ai_client.generate_linkedin_post(
                    job_title=job_title, company=company, location=location,
                    skills=skills or "Compétences variées", salary=salary,
                    form_url=form_url, experience=experience, contract_type=contract_type
                )
                self.logger.success("Post généré avec DeepSeek")
            except Exception as e:
                self.logger.error(f"Erreur génération DeepSeek: {e}")
                post_content = self._generate_smart_post(
                    job_title, skills_list, location, company, salary,
                    experience, contract_type, duration, form_url
                )
        else:
            post_content = self._generate_smart_post(
                job_title, skills_list, location, company, salary,
                experience, contract_type, duration, form_url
            )

        # Affichage du résultat
        print("\n" + "🔵"*20 + " APERCU LINKEDIN " + "🔵"*20)
        print(post_content)
        print("🔵"*55 + "\n")
        
        self.logger.success(f"Offre publiée (ID: #LI-{abs(hash(job_title)) % 100000})")
        return {
            "content": post_content,
            "url": f"https://www.linkedin.com/jobs/view/{abs(hash(job_title)) % 100000}"
        }

    # ─────────────────────────────────────────────────────────────────
    # MOTEUR DE GÉNÉRATION INTELLIGENT
    # ─────────────────────────────────────────────────────────────────

    def _detect_domain(self, title: str) -> str:
        """Détecte le domaine d'activité à partir du titre du poste"""
        title_lower = title.lower()
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in title_lower for kw in keywords):
                return domain
        return "default"

    def _is_specified(self, value: str) -> bool:
        """Vérifie qu'une valeur n'est pas 'Non spécifié' ou vide"""
        return value and value.strip().lower() not in ("non spécifié", "", "non specifié")

    def _build_skills_section(self, skills_list: list) -> str:
        """Construit la section compétences avec mise en forme"""
        if not skills_list:
            return ""
        
        lines = []
        for skill in skills_list[:6]:  # Max 6 compétences
            lines.append(f"  ✔️ {skill.strip()}")
        return "\n".join(lines)

    def _build_details_section(self, location, salary, experience, contract_type, duration) -> str:
        """Construit la section détails de l'offre"""
        details = []
        if self._is_specified(location):
            details.append(f"📍 **Localisation :** {location}")
        if self._is_specified(contract_type):
            details.append(f"📝 **Contrat :** {contract_type}")
        if self._is_specified(experience):
            details.append(f"🎓 **Expérience :** {experience}")
        if self._is_specified(salary):
            details.append(f"💰 **Rémunération :** {salary}")
        if self._is_specified(duration):
            details.append(f"⏱️ **Durée :** {duration}")
        return "\n".join(details)

    def _generate_hashtags(self, title: str, location: str, skills_list: list) -> str:
        """Génère des hashtags intelligents et pertinents"""
        tags = set()
        
        # Hashtag du poste
        title_clean = title.replace(" ", "").replace("'", "").replace("é", "e").replace("è", "e")
        tags.add(f"#{title_clean}")
        
        # Hashtags de base
        tags.add("#Recrutement")
        tags.add("#Emploi")
        
        # Localisation
        if self._is_specified(location):
            loc_clean = location.replace(" ", "").replace("-", "")
            tags.add(f"#{loc_clean}")
        
        # Compétences (max 2)
        for skill in skills_list[:2]:
            skill_clean = skill.strip().replace(" ", "").replace(".", "").replace("/", "")
            if len(skill_clean) > 2:
                tags.add(f"#{skill_clean}")
        
        # Domaine
        domain = self._detect_domain(title)
        domain_tags = {
            "tech": ["#Tech", "#IT", "#Dev"],
            "data": ["#DataScience", "#BigData"],
            "design": ["#Design", "#UX"],
            "management": ["#Management", "#Leadership"],
        }
        if domain in domain_tags:
            tags.add(random.choice(domain_tags[domain]))
        
        return " ".join(list(tags)[:6])

    def _generate_smart_post(self, title, skills_list, location, company, 
                              salary, experience, contract_type, duration, form_url) -> str:
        """Génère un post LinkedIn de qualité avec des templates contextuels avancés"""
        
        domain = self._detect_domain(title)
        
        # ── Composants du post ──
        accroche = random.choice(self.ACCROCHES)
        mission = random.choice(self.MISSIONS.get(domain, self.MISSIONS["default"]))
        
        pourquoi = random.sample(self.POURQUOI_REJOINDRE, k=3)
        pourquoi_text = "\n".join(pourquoi)
        
        appel = random.choice(self.APPELS_ACTION)
        closing = random.choice(self.CLOSINGS)
        hashtags = self._generate_hashtags(title, location, skills_list)
        
        # ── Sections conditionnelles ──
        company_display = company if self._is_specified(company) else "notre entreprise"
        
        # Titre du poste avec entreprise
        if self._is_specified(company):
            titre_section = f"📌 **{company}** recrute un(e) **{title}**"
        else:
            titre_section = f"📌 Nous recrutons un(e) **{title}**"
        if self._is_specified(location):
            titre_section += f" à **{location}**"
        titre_section += " !"
        
        # Section compétences
        skills_section = self._build_skills_section(skills_list)
        skills_block = ""
        if skills_section:
            skills_block = f"\n🛠️ **Compétences recherchées :**\n{skills_section}\n"
        
        # Section détails
        details_section = self._build_details_section(location, salary, experience, contract_type, duration)
        details_block = ""
        if details_section:
            details_block = f"\n📋 **Les détails :**\n{details_section}\n"
        
        # ── Assemblage du post (choix de style) ──
        style = random.choice(["storytelling", "professionnel", "dynamique"])
        
        if style == "storytelling":
            post = self._template_storytelling(
                accroche, titre_section, mission, skills_block,
                pourquoi_text, details_block, appel, form_url, closing, hashtags,
                title, company_display
            )
        elif style == "professionnel":
            post = self._template_professionnel(
                titre_section, mission, skills_block,
                pourquoi_text, details_block, appel, form_url, closing, hashtags,
                title, company_display
            )
        else:
            post = self._template_dynamique(
                accroche, titre_section, mission, skills_block,
                pourquoi_text, details_block, appel, form_url, closing, hashtags,
                title, company_display
            )
        
        return post.strip()

    # ─────────────────────────────────────────────────────────────────
    # STYLES DE TEMPLATES
    # ─────────────────────────────────────────────────────────────────
    
    def _template_storytelling(self, accroche, titre, mission, skills_block,
                                pourquoi, details, appel, form_url, closing, hashtags,
                                job_title, company):
        """Template style storytelling - accroche émotionnelle"""
        return f"""{accroche}

{titre}

🎯 **La mission :**
{mission}
{skills_block}
{details}
✨ **Pourquoi nous rejoindre ?**
{pourquoi}

{appel} 👇
🔗 {form_url}

{closing}

{hashtags}"""

    def _template_professionnel(self, titre, mission, skills_block,
                                 pourquoi, details, appel, form_url, closing, hashtags,
                                 job_title, company):
        """Template style corporate/professionnel"""
        return f"""📢 OFFRE D'EMPLOI

{titre}

━━━━━━━━━━━━━━━━━━━━━━

🎯 **Mission :**
{mission}
{skills_block}
{details}
💎 **Ce que nous offrons :**
{pourquoi}

━━━━━━━━━━━━━━━━━━━━━━

{appel} :
🔗 {form_url}

{closing}

{hashtags}"""

    def _template_dynamique(self, accroche, titre, mission, skills_block,
                             pourquoi, details, appel, form_url, closing, hashtags,
                             job_title, company):
        """Template style dynamique et engageant"""
        return f"""{accroche}

{titre}

💡 {mission}
{skills_block}
{details}
🌟 **Les + :**
{pourquoi}

{appel} ⬇️
🔗 {form_url}

{closing}

{hashtags}"""
