'use strict';

const choixDates = (() => {
  const nomsMois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
  const rapides = [['Aujourd’hui', "aujourd'hui"], ['Demain', 'demain'], ['Ce week-end', 'ce week-end'], ['Semaine prochaine', 'semaine prochaine']];
  const deuxChiffres = valeur => String(valeur).padStart(2, '0');

  function noeud(balise, classe, texte) {
    const element = document.createElement(balise);
    if (classe) element.className = classe;
    if (texte !== undefined) element.textContent = texte;
    return element;
  }

  function option(valeur, texte) {
    const element = noeud('option', '', texte);
    element.value = valeur;
    return element;
  }

  const nomsJours = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];

  function dateRapide(texte, maintenant = new Date()) {
    return comprendreDemande.date(texte, maintenant);
  }

  function dateEnLettres(valeur) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(valeur || '')) return '';
    const [a, m, j] = valeur.split('-').map(Number);
    const date = new Date(a, m - 1, j, 12);
    if (date.getDate() !== j) return '';
    return `${nomsJours[date.getDay()]} ${j} ${nomsMois[m - 1]} ${a}`;
  }

  function installer(conteneur) {
    const cible = document.getElementById(conteneur.dataset.cible);
    const libelle = conteneur.dataset.libelle;
    const base = conteneur.dataset.cible;
    const titre = noeud('span', 'titre-date', libelle);
    titre.id = `titre-${base}`;
    const groupeRapide = noeud('div', 'boutons-rapides');
    groupeRapide.setAttribute('role', 'group');
    groupeRapide.setAttribute('aria-label', `${libelle} : choix rapide`);
    const menus = noeud('div', 'menus-date');
    const jour = noeud('select');
    const mois = noeud('select');
    const annee = noeud('select');
    jour.id = `${base}-jour`;
    mois.id = `${base}-mois`;
    annee.id = `${base}-annee`;
    jour.setAttribute('aria-label', `${libelle} : jour`);
    mois.setAttribute('aria-label', `${libelle} : mois`);
    annee.setAttribute('aria-label', `${libelle} : année`);
    jour.append(option('', 'Jour'), ...Array.from({ length: 31 }, (_, i) => option(deuxChiffres(i + 1), String(i + 1))));
    mois.append(option('', 'Mois'), ...nomsMois.map((nom, i) => option(deuxChiffres(i + 1), nom)));
    const anneeCourante = new Date().getFullYear();
    annee.append(option('', 'Année'), ...Array.from({ length: 10 }, (_, i) => option(String(anneeCourante + i), String(anneeCourante + i))));
    menus.append(jour, mois, annee);
    const actions = noeud('div', 'actions-date');
    const dire = noeud('button', 'bouton-dire-date', 'Dire la date');
    dire.type = 'button';
    dire.hidden = !(typeof dictee !== 'undefined' && dictee.disponible());
    const effacer = noeud('button', 'bouton-effacer-date', 'Effacer');
    effacer.type = 'button';
    actions.append(dire, effacer);
    const lisible = noeud('p', 'date-lisible');
    lisible.id = `${base}-lisible`;
    lisible.setAttribute('aria-live', 'polite');
    const aide = noeud('p', 'aide-date');
    aide.setAttribute('aria-live', 'polite');
    aide.hidden = true;
    let arretDemande = false;

    function message(texte) {
      aide.textContent = texte;
      aide.hidden = !texte;
    }

    function assurerAnnee(valeur) {
      if (valeur && !Array.from(annee.options).some(item => item.value === valeur)) annee.append(option(valeur, valeur));
    }

    function remplir(valeur) {
      message('');
      jour.setCustomValidity('');
      if (!/^\d{4}-\d{2}-\d{2}$/.test(valeur || '')) {
        jour.value = mois.value = annee.value = '';
        cible.value = '';
        actualiserRapides();
        return;
      }
      const [a, m, j] = valeur.split('-');
      assurerAnnee(a);
      annee.value = a;
      mois.value = m;
      jour.value = j;
      cible.value = valeur;
      actualiserRapides();
    }

    function lireMenus() {
      message('');
      jour.setCustomValidity('');
      if (!jour.value && !mois.value && !annee.value) {
        cible.value = '';
        actualiserRapides();
        return;
      }
      const aujourdHui = new Date();
      if (!jour.value) jour.value = deuxChiffres(aujourdHui.getDate());
      if (!mois.value) mois.value = deuxChiffres(aujourdHui.getMonth() + 1);
      if (!annee.value) annee.value = String(aujourdHui.getFullYear());
      const date = new Date(Number(annee.value), Number(mois.value) - 1, Number(jour.value), 12);
      if (date.getDate() !== Number(jour.value)) {
        cible.value = '';
        const texte = `${libelle} : le ${Number(jour.value)} ${nomsMois[Number(mois.value) - 1]} ${annee.value} n’existe pas.`;
        jour.setCustomValidity(texte);
        message(texte);
      } else {
        cible.value = `${annee.value}-${mois.value}-${jour.value}`;
      }
      actualiserRapides();
    }

    function actualiserRapides() {
      const maintenant = new Date();
      lisible.textContent = cible.value ? dateEnLettres(cible.value) : '';
      groupeRapide.querySelectorAll('button').forEach(bouton => {
        bouton.setAttribute('aria-pressed', String(Boolean(cible.value) && dateRapide(bouton.dataset.texte, maintenant) === cible.value));
      });
    }

    for (const [texte, phrase] of rapides) {
      const bouton = noeud('button', 'bouton-date-rapide', texte);
      bouton.type = 'button';
      bouton.dataset.texte = phrase;
      bouton.addEventListener('click', () => remplir(dateRapide(phrase, new Date())));
      groupeRapide.append(bouton);
    }
    [jour, mois, annee].forEach(menu => menu.addEventListener('change', lireMenus));
    effacer.addEventListener('click', () => remplir(''));
    dire.addEventListener('click', () => {
      if (dictee.enCours()) {
        arretDemande = true;
        dictee.arreter();
        return;
      }
      arretDemande = false;
      if (document.activeElement && document.activeElement !== dire) document.activeElement.blur?.();
      ecouter(1);
    });

    function comprendre(texte) {
      const resultat = comprendreDemande.trouverDate(texte, new Date(), { seul: true });
      if (resultat.date) {
        remplir(resultat.date);
      } else if (resultat.choix.length) {
        message('');
        aide.append(noeud('span', '', `« ${texte.trim()} » : je ne suis pas sûr. Laquelle ?`),
          ...resultat.choix.map(valeur => {
            const bouton = noeud('button', 'choix-date-possible', dateEnLettres(valeur));
            bouton.type = 'button';
            bouton.addEventListener('click', () => remplir(valeur));
            return bouton;
          }));
        aide.hidden = false;
        aide.querySelector('button').focus({ preventScroll: true });
      } else {
        message(`Je n’ai pas compris la date dans « ${texte.trim()} ». Choisis-la dans les menus.`);
      }
    }

    function ecouter(essaisRestants) {
      message(essaisRestants ? 'Je t’écoute : dis la date, par exemple « vendredi » ou « le 15 novembre ».' : 'Je t’écoute encore…');
      dire.setAttribute('aria-pressed', 'true');
      let compris = false;
      let provisoire = '';
      let erreur = '';
      dictee.demarrer({
        surProvisoire(texte) {
          if (compris) return;
          provisoire = texte;
          if (texte.trim()) message(`J’entends : « ${texte.trim()} »`);
        },
        surFinal(texte) {
          if (compris) return;
          compris = true;
          comprendre(texte || provisoire);
        },
        surErreur(code) {
          if (compris) return;
          erreur = code;
          if (code === 'occupee') {
            dire.setAttribute('aria-pressed', 'false');
            message('Le micro est déjà en train d’écouter. Réessaie dans un instant.');
          }
        },
        surFin() {
          dire.setAttribute('aria-pressed', 'false');
          if (compris) return;
          if (arretDemande) {
            message('');
            return;
          }
          if (provisoire.trim()) {
            compris = true;
            comprendre(provisoire);
            return;
          }
          const messages = {
            'not-allowed': 'Le micro est bloqué pour Cap. Autorise-le dans les réglages du navigateur.',
            'service-not-allowed': 'Le micro est bloqué pour Cap. Autorise-le dans les réglages du navigateur.',
            network: 'La dictée a besoin d’internet. Choisis la date dans les menus.',
            'audio-capture': 'Aucun micro trouvé. Choisis la date dans les menus.'
          };
          if (messages[erreur]) {
            message(messages[erreur]);
          } else if (essaisRestants > 0 && (!erreur || erreur === 'no-speech' || erreur === 'aborted')) {
            setTimeout(() => ecouter(essaisRestants - 1), 150);
          } else {
            message('Je n’ai rien entendu. Réessaie, ou choisis la date dans les menus.');
          }
        }
      });
    }
    cible.form?.addEventListener('reset', () => remplir(''));
    conteneur.replaceChildren(titre, groupeRapide, menus, lisible, actions, aide);
    conteneur.setAttribute('role', 'group');
    conteneur.setAttribute('aria-labelledby', titre.id);
    remplir(cible.value);
    return { remplir };
  }

  return { installer, dateRapide, dateEnLettres };
})();
