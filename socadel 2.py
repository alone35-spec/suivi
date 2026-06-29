import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import secrets
import base64

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Portail Suivi de Chantier", page_icon="???", layout="wide")

# --- FICHIERS DE STOCKAGE DES DONNÉES SUR LE SERVEUR ---
CONFIG_FILE = "config_securite.json"
ENTREPRISES_FILE = "entreprises_data.json"
REPORTS_FILE = "rapports_chantiers.json"

def charger_fichier(nom_fichier, defaut):
    if os.path.exists(nom_fichier):
        with open(nom_fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    return defaut

def sauvegarder_fichier(nom_fichier, donnees):
    with open(nom_fichier, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=4, ensure_ascii=False)

# Initialisation des fichiers de données
config_secu = charger_fichier(CONFIG_FILE, {"password_oncle": "Controleur2026!"})
entreprises = charger_fichier(ENTREPRISES_FILE, {})
rapports_data = charger_fichier(REPORTS_FILE, {})

# --- APPLICATION PRINCIPALE ---
st.title("?? Plataforme de Suivi des Travaux & Compteurs")

# Choix de l'espace sur la page d'accueil (Deux onglets principaux)
espace_principal = st.radio(
    "Veuillez choisir votre espace d'accès :",
    ["?????? Suivi des Travaux (Contrôleur / Oncle)", "?? Entreprise Traitante"],
    horizontal=True
)

# ------------------------------------------------------------------
# ESPACE 1 : SUIVI DES TRAVAUX (VOTRE ONCLE)
# ------------------------------------------------------------------
if espace_principal == "?????? Suivi des Travaux (Contrôleur / Oncle)":
    st.header("Espace Superviseur — Contrôle des Travaux")
    
    # Authentification de l'oncle
    if "oncle_authentifie" not in st.session_state:
        st.session_state["oncle_authentifie"] = False
        
    if not st.session_state["oncle_authentifie"]:
        mdp_saisi = st.text_input("Entrez votre mot de passe unique :", type="password")
        if st.button("Se connecter à mon espace"):
            if mdp_saisi == config_secu["password_oncle"]:
                st.session_state["oncle_authentifie"] = True
                st.rerun()
            else:
                st.error("Mot de passe contrôleur incorrect.")
    else:
        st.success("Connecté en tant que Contrôleur Principal.")
        if st.button("?? Se déconnecter de l'espace contrôleur"):
            st.session_state["oncle_authentifie"] = False
            st.rerun()
            
        # Sous-onglets de l'oncle
        sub_tab1, sub_tab2, sub_tab3 = st.tabs([
            "?? Gestion de mon Mot de passe",
            "?? Enregistrer et Créer une Entreprise",
            "?? Consulter & Télécharger les Rapports"
        ])
        
        # Sous-onglet 1.1 : Changement de mot de passe de l'oncle
        with sub_tab1:
            st.subheader("Modifier votre mot de passe d'accès unique")
            ancien_mdp = st.text_input("Ancien mot de passe", type="password", key="anc_oncle")
            nouveau_mdp = st.text_input("Nouveau mot de passe", type="password", key="nouv_oncle")
            confirmer_mdp = st.text_input("Confirmer le nouveau mot de passe", type="password", key="conf_oncle")
            
            if st.button("Modifier le mot de passe définitif"):
                if ancien_mdp != config_secu["password_oncle"]:
                    st.error("L'ancien mot de passe est incorrect.")
                elif nouveau_mdp != confirmer_mdp:
                    st.error("Les nouveaux mots de passe ne correspondent pas.")
                elif len(nouveau_mdp) < 4:
                    st.error("Le mot de passe est trop court.")
                else:
                    config_secu["password_oncle"] = nouveau_mdp
                    sauvegarder_fichier(CONFIG_FILE, config_secu)
                    st.success("Votre mot de passe unique a été modifié avec succès !")
                    
        # Sous-onglet 1.2 : Création dynamique d'entreprise
        with sub_tab2:
            st.subheader("Enregistrement d'une nouvelle entreprise et Génération de clé")
            with st.form("creation_entreprise"):
                nom_ent = st.text_input("Nom de l'entreprise traitante *").strip()
                localite_ent = st.text_input("Localité / Emplacement du chantier *")
                projet_ent = st.text_input("Nom du projet en cours *")
                objet_ent = st.text_input("Objet du projet *")
                duree_ent = st.text_input("Durée estimée du projet (ex: 3 jours, 1 mois) *")
                
                # Informations compteurs demandées
                quantite_compteurs = st.number_input("Quantité de compteurs prévus", min_value=0, value=0)
                date_construction = st.date_input("Date de construction sur le terrain", datetime.today())
                
                soumis = st.form_submit_button("Créer l'entreprise & Générer le mot de passe")
                
                if soumis:
                    if not nom_ent or not projet_ent:
                        st.error("Le nom de l'entreprise et le projet sont obligatoires.")
                    else:
                        # Génération automatique d'un mot de passe sécurisé à 8 caractères
                        mdp_genere = secrets.token_hex(4).upper()
                        
                        entreprises[nom_ent] = {
                            "nom": nom_ent,
                            "localite": localite_ent,
                            "projet": projet_ent,
                            "objet": objet_ent,
                            "duree": duree_ent,
                            "quantite_compteurs": quantite_compteurs,
                            "date_construction": str(date_construction),
                            "mot_de_passe": mdp_genere
                        }
                        sauvegarder_fichier(ENTREPRISES_FILE, entreprises)
                        st.success(f"?? Entreprise enregistrée ! MOT DE PASSE GÉNÉRÉ : {mdp_genere}")
                        st.info(f"Transmettez ce mot de passe à l'entreprise '{nom_ent}' pour son premier contact.")

            # Liste des entreprises créées par l'oncle
            st.subheader("Entreprises actives & Mots de passe associés")
            if entreprises:
                df_ent = pd.DataFrame.from_dict(entreprises, orient='index')[["nom", "localite", "projet", "mot_de_passe"]]
                st.dataframe(df_ent, use_container_width=True)
            else:
                st.info("Aucune entreprise enregistrée pour le moment.")

        # Sous-onglet 1.3 : Consultation et téléchargement des rapports par l'oncle
        with sub_tab3:
            st.subheader("Historique global des rapports transmis sur le serveur")
            
            if rapports_data:
                for ent_nom, liste_rapports in rapports_data.items():
                    st.markdown(f"### ?? Entreprise : {ent_nom}")
                    
                    # On affiche les rapports de cette entreprise
                    for idx, rap in enumerate(reversed(liste_rapports)):
                        with st.expander(f"?? Rapport du {rap['date_saisie']} — Projet: {rap['projet_nom']}"):
                            st.write(f"**Saisie manuelle / Description :**\n{rap['description']}")
                            st.write(f"**Numéros de compteurs saisis :** {rap['numeros_compteurs']}")
                            
                            # Affichage de l'image réelle si elle existe
                            if rap.get("image_base64"):
                                try:
                                    img_data = base64.b64decode(rap["image_base64"])
                                    st.image(img_data, caption=f"Image du rapport - {rap['date_saisie']}", use_container_width=True)
                                except Exception as e:
                                    st.error("Impossible d'afficher l'image jointe.")
                            
                            # Préparation du texte pour téléchargement
                            texte_telechargement = f"ENTREPRISE: {ent_nom}\nDATE: {rap['date_saisie']}\nPROJET: {rap['projet_nom']}\nCOMPTEURS: {rap['numeros_compteurs']}\n\nDESCRIPTION:\n{rap['description']}"
                            
                            st.download_button(
                                label="?? Télécharger ce rapport (.txt)",
                                data=texte_telechargement,
                                file_name=f"Rapport_{ent_nom}_{rap['date_saisie']}.txt",
                                mime="text/plain",
                                key=f"dl_{ent_nom}_{idx}"
                            )
            else:
                st.info("Aucun rapport n'a encore été envoyé par les entreprises sur le serveur.")

# ------------------------------------------------------------------
# ESPACE 2 : ENTREPRISE TRAITANTE
# ------------------------------------------------------------------
elif espace_principal == "?? Entreprise Traitante":
    st.header("Espace Entreprises Ouvrières")
    
    if not entreprises:
        st.warning("Aucune entreprise n'est configurée sur le serveur par le contrôleur. Accès impossible.")
    else:
        # Sélection de l'entreprise
        liste_noms_entreprises = list(entreprises.keys())
        entreprise_selectionnee = st.selectbox("Sélectionnez votre Entreprise :", liste_noms_entreprises)
        
        mdp_entreprise_saisi = st.text_input("Entrez le mot de passe de votre entreprise :", type="password")
        
        # Vérification du mot de passe propre à l'entreprise sélectionnée
        if mdp_entreprise_saisi == entreprises[entreprise_selectionnee]["mot_de_passe"]:
            st.success(f"?? Accès autorisé pour l'entreprise : {entreprise_selectionnee}")
            
            # Affichage des informations fixes enregistrées par l'oncle
            info = entreprises[entreprise_selectionnee]
            st.info(f"?? **Localité :** {info['localite']} | ?? **Projet :** {info['projet']} | ?? **Date Construction :** {info['date_construction']} | ?? **Quantité prévue :** {info['quantite_compteurs']}")
            
            st.subheader("?? Rédiger et envoyer le Rapport d'activité")
            
            # Formulaire de saisie du rapport
            with st.form("form_rapport_entreprise"):
                date_du_jour = st.date_input("Date du rapport", datetime.today())
                
                # Demande spécifique sur les numéros de compteur
                num_compteurs_du_jour = st.text_area("Saisissez les numéros de compteurs installés (séparés par une virgule) :")
                
                # Rubrique description demandée
                description_rapport = st.text_area("Description détaillée du rapport (Activités, avancement) :")
                
                # Rubrique Images
                fichier_image = st.file_uploader("Ajouter une image de la journée (Optionnel)", type=["png", "jpg", "jpeg"])
                
                soumettre_rap = st.form_submit_button("?? Envoyer le rapport sur le serveur")
                
                if soumettre_rap:
                    # Encodage de l'image en Base64 si elle existe
                    image_encoded = None
                    if fichier_image is not None:
                        image_bytes = fichier_image.read()
                        image_encoded = base64.b64encode(image_bytes).decode("utf-8")

                    # Traitement du rapport
                    nouveau_rapport = {
                        "date_saisie": str(date_du_jour),
                        "projet_nom": info['projet'],
                        "numeros_compteurs": num_compteurs_du_jour,
                        "description": description_rapport,
                        "image_base64": image_encoded
                    }
                    
                    # Initialisation de la liste de rapports pour cette entreprise si inexistante
                    if entreprise_selectionnee not in rapports_data:
                        rapports_data[entreprise_selectionnee] = []
                        
                    rapports_data[entreprise_selectionnee].append(nouveau_rapport)
                    sauvegarder_fichier(REPORTS_FILE, rapports_data)
                    st.success("Le rapport et les numéros de compteurs ont été envoyés avec succès sur le serveur !")
        else: 
            if mdp_entreprise_saisi:
                st.error("Mot de passe incorrect pour cette entreprise.")