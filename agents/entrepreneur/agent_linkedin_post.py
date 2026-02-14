from utils.logger import HackathonLogger
from utils.hf_client import HuggingFaceClient

class AgentLinkedInPost:
    """Agent responsable de la publication sur LinkedIn avec génération IA"""
    
    def __init__(self):
        self.logger = HackathonLogger("AgentLinkedInPost")
        try:
            self.hf_client = HuggingFaceClient()
        except Exception:
            self.logger.warning("Token HF manquant ou invalide, mode simulation simple activé")
            self.hf_client = None

    def poster_offre(self, details: dict, form_url: str = None):
        job_title = details.get('job_title', 'Poste inconnu')
        skills = ", ".join(details.get('skills_required', []))
        location = details.get('location', 'Non spécifié')
        company = details.get('company_name', 'Notre entreprise')
        salary = details.get('salary', 'Non spécifié')
        
        self.logger.info(f"Génération d'un post LinkedIn optimisé pour : {job_title}")
        
        post_content = ""
        form_url = form_url or "[Lien dans le premier commentaire]"
        
        if self.hf_client:
            prompt = f"""<s>[INST] Agis comme un expert en Copywriting RH. Rédige un post LinkedIn VIRAL pour recruter un {job_title} chez {company} ({location}).

Structure obligatoire :
1. 🎣 Une accroche percutante (Hook) avec un emoji fort.
2. 🚀 La mission en une phrase inspirante.
3. 🛠️ Les compétences clés : {skills} (sous forme de liste à puces).
4. 💎 Pourquoi nous rejoindre ? (Challenge technique, équipe passionnée).
5. 💰 Salaire indicatif : {salary}.
6. 👉 Appel à l'action clair : "Postulez ici : {form_url}"

Ton : Dynamique, professionnel, et engageant. Utilise des emojis intelligents.
Termine avec 3-4 hashtags pertinents.
[/INST]"""
            try:
                # Utilisation de Mistral/Zephyr via API
                response = self.hf_client.query_text("mistral", prompt, max_tokens=800, temperature=0.8)
                
                if isinstance(response, list) and len(response) > 0:
                     generated_text = response[0].get('generated_text', '')
                     if "[/INST]" in generated_text:
                         post_content = generated_text.split("[/INST]")[-1].strip()
                     else:
                         post_content = generated_text.replace(prompt, "").strip()
                else:
                    self.logger.warning("Réponse vide d'API IA, passage au fallback.")
                    post_content = self._generate_fallback_content(job_title, skills, location, company, salary, form_url)
            except Exception as e:
                self.logger.error(f"Erreur génération IA: {e}")
                post_content = self._generate_fallback_content(job_title, skills, location, company, salary, form_url)
        else:
            post_content = self._generate_fallback_content(job_title, skills, location, company, salary, form_url)

        # Affichage du résultat
        print("\n" + "🔵"*20 + " APERCU LINKEDIN " + "🔵"*20)
        print(post_content)
        print("🔵"*55 + "\n")
        
        self.logger.success(f"Offre publiée (ID: #LI-{abs(hash(job_title)) % 100000})")
        return {
            "content": post_content,
            "url": f"https://www.linkedin.com/jobs/view/{abs(hash(job_title)) % 100000}"
        }
    
    def _generate_fallback_content(self, title, skills, location, company, salary, link):
        import random
        
        # Hashtags dynamiques
        safe_title = title.replace(" ", "")
        safe_loc = location.replace(" ", "")
        tags = f"#{safe_title} #Recrutement #{safe_loc} #Emploi"

        templates = [
            f"🚀 {company} Recrute !\n\nNous recherchons un(e) **{title}** passionné(e) pour rejoindre notre équipe à {location}.\n\n💡 **Vos missions :** Participer à des projets ambitieux et innovants.\n\n🛠️ **Profil recherché :**\n{skills}\n\n💰 **Salaire :** {salary}\n\n👉 **Postulez maintenant :** {link}\n\n{tags}",
            
            f"🔥 Opportunité de carrière : {title} chez {company} !\n\nTu es expert(e) en {skills.split(',')[0]} ? Tu cherches un nouveau challenge à {location} ?\n\nRejoins-nous pour construire le futur ! 🚀\n\n📩 Candidature simple et rapide : {link}\n\n{tags}",
            
            f"We are hiring! 🌍\n\nPosition: {title}\nLocation: {location}\nCompany: {company}\n\nSkills required: {skills}\n\nApply here: {link} 🔗\n\n#Hiring #Tech #JobAlert"
        ]
        return random.choice(templates)
