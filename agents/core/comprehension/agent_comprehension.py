

from models.schemas import UserType, ComprehensionOutput
from utils.logger import HackathonLogger
import re

class AgentComprehension:
    """
    Version simplifiée de l'agent qui utilise des règles (pas d'API)
    """
    
    def __init__(self):
        self.logger = HackathonLogger("AgentComprehension")
        
        # Dictionnaires de mots-clés
        self.mots_entrepreneur = {
            'recruter', 'recrutement', 'embauche', 'poste', 'emploi',
            'ingénieur', 'développeur', 'data', 'scientist', 'full-stack',
            'cdi', 'cdd', 'freelance', 'contrat', 'salaire',
            'compétences', 'profil', 'candidat', 'équipe',
            'cherche', 'recherche', 'besoin', 'mission', 'entreprise', 'société'
        }
        
        self.mots_etudiant = {
            'stage', 'alternance', 'apprentissage', 'étudiant',
            'cv', 'candidature', 'postuler', 'école', 'université',
            'master', 'licence', 'formation', 'gratuit'
        }
        

    
    def process(self, texte: str) -> ComprehensionOutput:
        """
        Analyse le texte par mots-clés
        """
        self.logger.info(f"Analyse du texte: {texte[:100]}...")
        
        # Nettoyer le texte
        texte_propre = texte.lower()
        mots = set(re.findall(r'\b\w+\b', texte_propre))
        
        # Compter les occurrences par catégorie
        score_entrepreneur = len(mots.intersection(self.mots_entrepreneur))
        score_etudiant = len(mots.intersection(self.mots_etudiant))

        
        # Déterminer le type
        scores = [
            (UserType.ENTREPRENEUR, score_entrepreneur),
            (UserType.ETUDIANT, score_etudiant)
        ]
        
        # Trier par score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if scores[0][1] > 0:
            type_user = scores[0][0]
            # Calculer une confiance (max 0.95)
            confiance = min(0.95, 0.5 + (scores[0][1] * 0.1))
        else:
            type_user = UserType.AUTRE
            confiance = 0.3
        
        self.logger.success(f"Type détecté: {type_user.value} (confiance: {confiance:.2f})")
        
        # Extraire les données selon le type
        if type_user == UserType.ENTREPRENEUR:
            donnees = self._extraire_recrutement(texte)
        elif type_user == UserType.ETUDIANT:
            donnees = self._extraire_stage(texte)
        else:
            donnees = {"texte_original": texte[:200]}
        
        return ComprehensionOutput(
            type_utilisateur=type_user,
            confiance=confiance,
            donnees_extraites=donnees,
            texte_original=texte
        )
    
    def _convertir_nombre(self, texte: str) -> int:
        """Convertit un nombre en texte français vers un entier"""
        nombres_fr = {
            'un': 1, 'une': 1, 'deux': 2, 'trois': 3, 'quatre': 4,
            'cinq': 5, 'six': 6, 'sept': 7, 'huit': 8, 'neuf': 9,
            'dix': 10, 'onze': 11, 'douze': 12, 'treize': 13,
            'quatorze': 14, 'quinze': 15, 'seize': 16,
            'vingt': 20, 'trente': 30, 'quarante': 40, 'cinquante': 50
        }
        texte = texte.strip().lower()
        if texte.isdigit():
            return int(texte)
        return nombres_fr.get(texte, 0)


        
    def _extraire_competences(self, texte_lower: str, donnees: dict) -> None:
        """Extrait les compétences techniques (partagé)"""
        if "skills_required" not in donnees:
            donnees["skills_required"] = []
            
        skills_map = [
            (r'python', 'Python'), (r'javascript', 'JavaScript'), (r'typescript', 'TypeScript'),
            (r'java(?!script)', 'Java'), (r'c\+\+', 'C++'), (r'c#', 'C#'),
            (r'ruby', 'Ruby'), (r'rust', 'Rust'), (r'php', 'PHP'),
            (r'swift', 'Swift'), (r'kotlin', 'Kotlin'),
            (r'react', 'React'), (r'angular', 'Angular'),
            (r'vue(?:\.?js)?', 'Vue.js'),
            (r'node\.?js|nodejs', 'Node.js'),
            (r'django', 'Django'), (r'flask', 'Flask'), (r'fastapi', 'FastAPI'),
            (r'spring', 'Spring'), (r'express', 'Express'),
            (r'sql(?!ite)', 'SQL'), (r'sqlite', 'SQLite'),
            (r'nosql', 'NoSQL'), (r'mongodb', 'MongoDB'),
            (r'postgresql|postgres', 'PostgreSQL'), (r'mysql', 'MySQL'), (r'redis', 'Redis'),
            (r'docker', 'Docker'), (r'kubernetes|k8s', 'Kubernetes'),
            (r'aws', 'AWS'), (r'azure', 'Azure'), (r'gcp', 'GCP'),
            (r'git(?!hub)', 'Git'), (r'github', 'GitHub'), (r'gitlab', 'GitLab'),
            (r'ci/cd|ci cd', 'CI/CD'), (r'linux', 'Linux'),
            (r'terraform', 'Terraform'), (r'jenkins', 'Jenkins'),
            (r'machine learning', 'Machine Learning'), (r'deep learning', 'Deep Learning'),
            (r'\bia\b|intelligence artificielle', 'IA'),
            (r'\bnlp\b|traitement du langage', 'NLP'),
            (r'html', 'HTML'), (r'css', 'CSS'),
            (r'rest(?:\s*api)?', 'REST API'), (r'graphql', 'GraphQL'),
            (r'spark', 'Spark'), (r'hadoop', 'Hadoop'), (r'airflow', 'Airflow'),
            (r'tableau', 'Tableau'), (r'power\s*bi', 'Power BI'),
            (r'scrum', 'Scrum'), (r'agile', 'Agile'), (r'devops', 'DevOps'),
            (r'd[ée]veloppement\s+web', 'Développement Web'),
            (r'd[ée]veloppement\s+mobile', 'Développement Mobile'),
            (r'catia', 'Catia'), (r'proteus', 'Proteus'), (r'rdm', 'RDM'),
            (r'matlab', 'Matlab'), (r'simulink', 'Simulink'),
            (r'solidworks', 'SolidWorks'), (r'autocad', 'AutoCAD'),
            (r'[ée]lectronique', 'Électronique'), (r'm[ée]canique', 'Mécanique'),
            (r'embarqu[ée]', 'Embarqué'), (r'iot', 'IoT'),
            (r'automatisme', 'Automatisme'), (r'robotique', 'Robotique'),
            (r'technologies?\s+avancée?s?', 'Technologies Avancées'),
        ]
        for pattern, nom in skills_map:
            if re.search(r'\b' + pattern + r'\b', texte_lower):
                if nom not in donnees["skills_required"]:
                    donnees["skills_required"].append(nom)

    def _extraire_lieu(self, texte: str, texte_lower: str, donnees: dict) -> None:
        """Extrait le lieu (partagé)"""
        villes_connues = [
            'paris', 'lyon', 'marseille', 'bordeaux', 'lille', 'toulouse', 'nice',
            'nantes', 'strasbourg', 'montpellier', 'rennes', 'grenoble',
            'tunis', 'sousse', 'sfax', 'casablanca', 'rabat', 'alger', 'oran',
            'remote', 'télétravail', 'borj cedria', 'borjcedria', 'ariana',
            'nabeul', 'bizerte', 'monastir', 'kairouan', 'gabès', 'médenine'
        ]
        lieu_trouve = False
        for ville in villes_connues:
            if ville in texte_lower:
                donnees["location"] = ville.replace('borjcedria', 'Borj Cedria').title()
                lieu_trouve = True
                break
        if not lieu_trouve:
            # Chercher "à/en + NomPropre" mais filtrer les faux positifs
            match_lieu = re.search(r'\b(?:cit[ée]e?|situ[ée]e?|bas[ée]e?|localis[ée]e?)?\s*(?:à|en)\s+([A-ZÀ-Üa-zà-ü][\w\-\.]+(?:\s+[A-ZÀ-Üa-zà-ü][\w\-\.]+)*)', texte)
            if match_lieu:
                candidat = match_lieu.group(1).strip()
                stopwords = {
                    'le', 'la', 'un', 'une', 'des', 'mon', 'ma', 'ce', 'cette', 'notre', 'votre', 'leur', 'recherche',
                    'technologies', 'troisieme', 'cycle', 'ingénieur', 'ingenieur', 'développement', 'domaine',
                    'ia', 'qui', 'moin', 'moins', 'plus', 'contrat', 'experience', 'expérience',
                    'informatique', 'mecanique', 'electronique', 'IA'
                }
                mots_candidat = set(candidat.lower().split())
                if not mots_candidat.intersection(stopwords):
                    donnees["location"] = candidat.title()

    def _extraire_duree(self, texte_lower: str, donnees: dict) -> None:
        """Extrait la durée (partagé)"""
        match_duree = re.search(r'(?:dur[ée]e\s+(?:de\s+)?(?:du\s+projet\s+est\s+)?|pour\s+)(\d+|un|une|deux|trois|quatre|cinq|six)\s*(ans?|mois|semaines?)', texte_lower)
        
        # Fallback: capturer aussi les formats collés comme "6ans", "6mois"
        if not match_duree:
            match_duree = re.search(r'(?:dur[ée]e|de|pour)\s+(?:de\s+)?(\d+)(ans?|mois|semaines?)', texte_lower)
        
        est_experience = False
        if match_duree:
            start, end = match_duree.span()
            if "d'exp" in texte_lower[end:end+15] or "d\'exp" in texte_lower[end:end+15]:
                est_experience = True

        if match_duree and not est_experience:
            nombre = self._convertir_nombre(match_duree.group(1))
            unite = match_duree.group(2)
            donnees["duration"] = f"{nombre} {unite}"

    def _extraire_recrutement(self, texte: str) -> dict:
        """
        Extraction pour recrutement
        """
        texte_lower = texte.lower()
        
        donnees = {
            "job_title": "Non spécifié",
            "number_needed": 1,
            "skills_required": [],
            "experience_level": "Non spécifié",
            "contract_type": "Non spécifié",
            "location": "Non spécifié",
            "company_name": "Non spécifié",
            "duration": "Non spécifié",
            "salary": "Non spécifié",
            "additional_info": texte[:200]
        }
        
        # --- Extraire le nombre et le titre du poste ---
        nombres_pattern = r'(\d+|un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)'
        titres_base = [
            'ing[ée]nieur[s]?', 'd[ée]veloppeur[s]?', 'data scientist[s]?',
            'data engineer[s]?', 'data analyst[s]?', 'chef[s]? de projet',
            'designer[s]?', 'devops', 'technicien[s]?', 'consultant[s]?',
            'manager[s]?', 'architecte[s]?', 'analyste[s]?',
            'administrateur[s]?', 'personne[s]?', 'profil[s]?', 'candidat[s]?'
        ]
        pattern_titres = '|'.join(titres_base)
        
        # Pattern: nombre + titre (ex: "deux ingénieurs")
        match = re.search(
            r'\b' + nombres_pattern + r'\s+(' + pattern_titres + r')(?:\s+(?:en|de)\s+([\w\s]+?))?(?:\s+(?:qui|pour|avec|dans|sur|et|ou|à|,|\.))',
            texte_lower
        )
        if not match:
            match = re.search(
                r'\b' + nombres_pattern + r'\s+(' + pattern_titres + r')(?:\s+(\w+))?',
                texte_lower
            )
        
        if match:
            donnees["number_needed"] = self._convertir_nombre(match.group(1))
            titre = match.group(2).strip()
            qualificatif = match.group(3)
            if qualificatif:
                qualificatif = qualificatif.strip()
                mots_exclus = {'pour', 'avec', 'dans', 'sur', 'et', 'ou', 'à', 'du', 'des', 'le', 'la', 'les', 'qui'}
                if qualificatif not in mots_exclus:
                    titre = f"{titre} en {qualificatif}" if 'en' not in titre else f"{titre} {qualificatif}"
            donnees["job_title"] = titre.strip().capitalize()
        else:
            # Fallback: "d'un ingénieur en IA", "un ingénieur"
            match_titre = re.search(r"(?:d[''']\s*)?\b(?:un|une)\s+(" + pattern_titres + r")(?:\s+(?:en|de)\s+([\w\s]+?))?(?:\s+(?:qui|pour|avec|dans|sur|et|ou|à|,|\.))", texte_lower)
            if not match_titre:
                match_titre = re.search(r"(?:d[''']\s*)?\b(?:un|une)\s+(" + pattern_titres + r")(?:\s+(\w+))?", texte_lower)
            if match_titre:
                titre = match_titre.group(1).strip()
                qualificatif = match_titre.group(2)
                if qualificatif:
                    qualificatif = qualificatif.strip()
                    mots_exclus = {'pour', 'avec', 'dans', 'sur', 'et', 'ou', 'à', 'du', 'des', 'le', 'la', 'les', 'qui'}
                    if qualificatif not in mots_exclus:
                        titre = f"{titre} en {qualificatif}"
                donnees["job_title"] = titre.strip().capitalize()
                donnees["number_needed"] = 1
        
        # --- Extraire l'entreprise ---
        patterns_entreprise = [
            r"(?:[Ll]'entreprise|[Ll]a société|[Ll]'agence|[Ll]a startup|[Ll]a boîte|[Cc]hez|l'entrerpise)\s+([A-ZÀ-Ü0-9][\w\-\.]+(?:\s+[A-ZÀ-Ü0-9][\w\-\.]+)*)",
            r"(?:[Ee]ntreprise|[Ss]ociété|[Aa]gence|[Ss]tartup)\s+([A-ZÀ-Ü0-9][\w\-\.]+(?:\s+[A-ZÀ-Ü0-9][\w\-\.]+)*)",
        ]
        for pattern in patterns_entreprise:
            match_ent = re.search(pattern, texte)
            if match_ent:
                donnees["company_name"] = match_ent.group(1).strip()
                break

        # --- Appel aux méthodes partagées ---
        self._extraire_competences(texte_lower, donnees)
        self._extraire_lieu(texte, texte_lower, donnees)
        self._extraire_duree(texte_lower, donnees)
        
        # --- Extraire le niveau d'expérience (supporte "3ans" collé ou "3 ans") ---
        match_exp = re.search(r"(\d+|un|une|deux|trois|quatre|cinq)\s*(ans?|mois)\s*d.exp[ée]rience", texte_lower)
        if match_exp:
            nb = self._convertir_nombre(match_exp.group(1))
            donnees["experience_level"] = f"{nb} {match_exp.group(2)} d'expérience"
        
        # --- Extraire le salaire ---
        match_salaire = re.search(r'(\d+[\s.]?\d*)\s*(?:dt|tnd|€|eur(?:os?)?|\$|dinars?)', texte_lower)
        if match_salaire:
            donnees["salary"] = match_salaire.group(0).strip().upper()
        
        # --- Extraire le contrat ---
        match_contrat = re.search(r'\b(?:contrat[s]?\s+(?:de\s+(?:type\s+)?)?)?(?:en\s+)?(cdi|cdd|freelance|stage|alternance|intérim)\b', texte_lower)
        if match_contrat:
            contrats = {'cdi': 'CDI', 'cdd': 'CDD', 'freelance': 'Freelance', 'stage': 'Stage', 'alternance': 'Alternance', 'intérim': 'Intérim'}
            donnees["contract_type"] = contrats.get(match_contrat.group(1), match_contrat.group(1).upper())

        return donnees
    
    def _extraire_stage(self, texte: str) -> dict:
        """Extraction détaillée pour étudiant/stage"""
        texte_lower = texte.lower()
        donnees = {
            "education_level": "Non spécifié",
            "field_of_study": "Non spécifié",
            "internship_type": "Stage",
            "duration": "Non spécifié",
            "skills_required": [],  # Compétences possédées par l'étudiant
            "location": "Non spécifié",
            "start_date": "Non spécifié",
            "has_cv": "cv" in texte_lower
        }

        # --- 1. Niveau d'études ---
        patterns_niveau = [
            (r'(\d+)[eè]me\s+ann[ée]e\s+(?:cycle\s+)?(?:d[\']?)?ing[ée]nieur', "Cycle Ingénieur ({annee}A)"),
            (r'cycle\s+ing[ée]nieur', "Cycle Ingénieur"),
            (r'(\d+)[eè]me\s+ann[ée]e', "{annee}ème année"),
            (r'master\s*(\d)?', "Master {annee}"),
            (r'licence\s*(\d)?', "Licence {annee}"),
            (r'bac\s*\+\s*(\d)', "Bac+{annee}"),
            (r'pfe', "PFE (Fin d'études)")
        ]
        for pattern, format_str in patterns_niveau:
            match = re.search(pattern, texte_lower)
            if match:
                annee = match.group(1) if match.groups() else ""
                donnees["education_level"] = format_str.format(annee=annee).strip()
                break

        # --- 2. Domaine d'études ---
        domaines = [
            'informatique', 'développement', 'data science', 'intelligence artificielle',
            'mecanique', 'électrique', 'électronique', 'industriel', 'civil',
            'gestion', 'finance', 'marketing', 'technologies? avancée?s?'
        ]
        # Regex plus souple : cherche le domaine précédé de "en" ou "de" quelque part dans phrase
        pattern_domaine = r'(?:en|de)\s+(' + '|'.join(domaines) + r')'
        match_domaine = re.search(pattern_domaine, texte_lower)
        if match_domaine:
            donnees["field_of_study"] = match_domaine.group(1).title()
        else:
             # Fallback: chercher juste le mot clé du domaine s'il est proche de "étudiant" ou "ingénieur"
             for domaine in domaines:
                 if domaine in texte_lower:
                     donnees["field_of_study"] = domaine.title()
                     break

        # --- 3. Type de stage ---
        types_stage = {
            'pfe': 'PFE', 'pfa': 'PFA', 'ouvrier': 'Ouvrier', 'technicien': 'Technicien',
            'initiation': 'Initiation', 'été': 'Été', 'summer': 'Été'
        }
        for kw, val in types_stage.items():
            if kw in texte_lower:
                donnees["internship_type"] = val
                break
        
        # --- 4. Appel aux méthodes partagées ---
        self._extraire_competences(texte_lower, donnees) # Pour les skills de l'étudiant
        self._extraire_lieu(texte, texte_lower, donnees)
        self._extraire_duree(texte_lower, donnees)

        return donnees
    
