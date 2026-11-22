/* MyKwizz : interface du navigateur.
   Elle n'a aucune règle métier : elle demande tout au serveur Python (serveur.py) et affiche la réponse.
   Les bonnes réponses n'arrivent qu'après l'envoi des réponses du joueur. */
"use strict";

const COULEURS = ["jaune", "rose", "vert", "bleu", "orange", "lilas"];
const etat = { utilisateur: null, ia: false, partie: null, minuterie: null, brouillon: null };
const $ = (sel, racine = document) => racine.querySelector(sel);
const contenu = $("#contenu");

/* ------------------------------------------------------------ outils */
function h(texte) {
  return String(texte ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}
function couleur(id) { return COULEURS[(Number(id) || 0) % COULEURS.length]; }
function duree(s) {
  if (s == null) return "sans limite";
  const m = Math.floor(s / 60), r = Math.round(s % 60);
  return m ? `${m} min${r ? " " + String(r).padStart(2, "0") + " s" : ""}` : `${r} s`;
}
function horloge(s) { s = Math.max(0, Math.ceil(s)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; }
function date(iso) {
  if (!iso) return "";
  const d = new Date(iso.replace(" ", "T") + "Z");
  return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short" }) + ", " +
    d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}
const ICONES = {
  juste: '<path d="M4 12.5l5 5L20 6"/>',
  faux: '<path d="M6 6l12 12M18 6L6 18"/>',
  oubli: '<circle cx="12" cy="12" r="7.5"/>',
  retour: '<path d="M15 5l-7 7 7 7"/>',
  retirer: '<path d="M7 7l10 10M17 7L7 17"/>',
};
function icone(nom) { return `<svg class="icone" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONES[nom]}</svg>`; }
function pluriel(n, mot) { return `${n} ${mot}${n > 1 ? "s" : ""}`; }
/* Un nombre dont chaque chiffre arrive l'un après l'autre (flou -> net). Lu en entier par les lecteurs d'écran. */
function chiffres(n) {
  return `<span class="chiffres"><span class="vh">${n}</span>${[...String(n)].map((c, k) =>
    `<span class="chiffre" aria-hidden="true" style="--k: ${k}">${c}</span>`).join("")}</span>`;
}
function fleche() { return '<svg class="icone fleche" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 6l6 6-6 6"/></svg>'; }

async function api(chemin, { methode = "GET", corps } = {}) {
  let rep;
  try {
    rep = await fetch("/api/" + chemin, {
      method: methode, credentials: "same-origin",
      headers: corps ? { "Content-Type": "application/json" } : {},
      body: corps ? JSON.stringify(corps) : undefined,
    });
  } catch {
    throw new Error("Le serveur MyKwizz ne répond pas. Est-il toujours lancé (python serveur.py) ?");
  }
  const donnees = await rep.json().catch(() => null);
  if (!rep.ok) {
    if (rep.status === 401 && chemin !== "connexion") { etat.utilisateur = null; aller("#/connexion"); }
    if (rep.status === 403 && etat.utilisateur?.doit_changer) aller("#/mot-de-passe");
    throw new Error(donnees?.erreur || `Erreur ${rep.status}`);
  }
  return donnees;
}

let minuteurToast;
function toast(message, ton = "info") {
  const t = $("#toast");
  t.textContent = message;
  t.dataset.ton = ton;
  t.classList.add("visible");
  clearTimeout(minuteurToast);
  minuteurToast = setTimeout(() => t.classList.remove("visible"), 4200);
}

function confirmer({ titre, texte, action, danger = false }) {
  const d = $("#dialogue");
  d.innerHTML = `<form method="dialog" class="dialogue-corps">
      <h2>${h(titre)}</h2><p>${h(texte)}</p>
      <div class="dialogue-actions">
        <button value="non" class="bouton secondaire">Annuler</button>
        <button value="oui" class="bouton ${danger ? "danger" : ""}">${h(action)}</button>
      </div></form>`;
  return new Promise(ok => {
    d.addEventListener("close", () => ok(d.returnValue === "oui"), { once: true });
    d.showModal();
    $("button[value=non]", d).focus();
  });
}

function aller(hash) { if (location.hash !== hash) location.hash = hash; else route(); }
function chargement(lignes = 3) {
  contenu.innerHTML = `<div class="squelette" aria-busy="true" aria-label="Chargement">
    <div class="sq-titre"></div>${'<div class="sq-ligne"></div>'.repeat(lignes)}</div>`;
}
function erreurPage(e) {
  contenu.innerHTML = `<section class="page"><div class="vide">
    <h1 class="titre-page">Oups.</h1><p>${h(e.message)}</p>
    <a class="bouton" href="#/">Revenir à l'accueil</a></div></section>`;
}

/* ------------------------------------------------------------ routeur */
const ROUTES = [
  [/^#\/bienvenue$/, vueBienvenue, false],
  [/^#\/(connexion|inscription)$/, vueConnexion, false],
  [/^#\/mot-de-passe$/, vueMotDePasse, false],
  [/^#\/?$/, vueAccueil, true],
  [/^#\/quizz\/(\d+)$/, vuePreparer, true],
  [/^#\/jouer\/(\d+)$/, vueJouer, true],
  [/^#\/reprendre$/, vueReprendre, true],
  [/^#\/reviser$/, vueReviser, true],
  [/^#\/resultat$/, vueResultat, true],
  [/^#\/corrige\/(\d+)$/, vueCorrige, true],
  [/^#\/historique$/, vueHistorique, true],
  [/^#\/classements(?:\/(\d+))?$/, vueClassements, true],
  [/^#\/admin$/, vueTableauBord, true],
  [/^#\/admin\/quizz$/, vueAdmin, true],
  [/^#\/admin\/journal$/, vueJournal, true],
  [/^#\/tester\/(\d+)$/, id => vueJouer(id, true), true],
  [/^#\/admin\/nouveau$/, vueEditeur, true],
  [/^#\/admin\/editer\/(\d+)$/, vueEditeur, true],
  [/^#\/admin\/brouillon$/, vueEditeur, true],
  [/^#\/admin\/importer$/, vueImporter, true],
  [/^#\/admin\/generer$/, vueGenerer, true],
  [/^#\/admin\/utilisateurs$/, vueUtilisateurs, true],
  [/^#\/assistant$/, vueAssistant, true],
  [/^#\/moi$/, vueMoi, true],
];

const PUBLIQUES = ["#/bienvenue", "#/connexion", "#/inscription"];
async function route() {
  arreterMinuterie();
  nettoyerVue();
  const hash = location.hash || "#/";
  const u = etat.utilisateur;
  if (!u && !PUBLIQUES.includes(hash)) return aller("#/bienvenue");
  if (u?.doit_changer && hash !== "#/mot-de-passe") return aller("#/mot-de-passe");
  for (const [motif, vue, avecRail] of ROUTES) {
    const m = hash.match(motif);
    if (!m) continue;
    $("#rail").hidden = !avecRail;
    document.body.classList.toggle("sans-rail", !avecRail);
    majNav(hash);
    try { await vue(...m.slice(1)); } catch (e) { erreurPage(e); }
    if (!contenu.contains(document.activeElement)) contenu.focus({ preventScroll: true }); // la vue a pu placer le focus
    window.scrollTo(0, 0);
    return;
  }
  aller("#/");
}

function majNav(hash) {
  const section = hash.startsWith("#/admin") ? "admin" : hash.startsWith("#/historique") ? "historique"
    : hash.startsWith("#/classements") ? "classements" : hash.startsWith("#/assistant") ? "assistant"
    : hash.startsWith("#/moi") ? "moi" : "jouer";
  document.querySelectorAll(".nav a").forEach(a => {
    if (a.dataset.route === section) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  const u = etat.utilisateur;
  $("#lien-admin").hidden = !u?.admin;
  $("#qui").innerHTML = u ? `Connecté : <strong>${h(u.login)}</strong>${u.admin ? " (admin)" : ""}` : "";
}

/* ------------------------------------------------------------ comptes */
function vueConnexion(mode = "connexion") {
  contenu.innerHTML = `
  <section class="accueil-public">
    <div class="pitch">
      <a class="marque grande" href="#/bienvenue" aria-label="MyKwizz, page d'accueil">${logoKwizz()}</a>
      <h1>Révise en jouant. Corrige en un coup d'œil.</h1>
      <p class="sous">Des quizz courts, une minuterie si tu veux, et le corrigé de chaque question dès la fin.</p>
      <div class="eventail" aria-hidden="true">
        <div class="fiche-deco jaune"><span>Quelle est la capitale de la Pologne ?</span></div>
        <div class="fiche-deco rose"><span>Que signifie WBS ?</span></div>
        <div class="fiche-deco vert"><span>Que renvoie len("kwizz") ?</span></div>
      </div>
    </div>
    <div class="carte-acces">
      <div class="onglets" role="tablist" aria-label="Connexion ou inscription">
        <button role="tab" id="t-co" aria-selected="true" aria-controls="f-co">Se connecter</button>
        <button role="tab" id="t-in" aria-selected="false" aria-controls="f-in" tabindex="-1">Créer un compte</button>
      </div>
      <form id="f-co" role="tabpanel" aria-labelledby="t-co" class="formulaire" novalidate>
        <label class="champ"><span>Login</span><input name="login" autocomplete="username" required autofocus></label>
        <label class="champ"><span>Mot de passe</span><input name="mdp" type="password" autocomplete="current-password" required></label>
        <p class="erreur" role="alert"></p>
        <button class="bouton large">Se connecter</button>
        <p class="aide">Premier lancement : <strong>admin</strong> / <strong>admin</strong>, puis tu choisis un nouveau mot de passe.</p>
      </form>
      <form id="f-in" role="tabpanel" aria-labelledby="t-in" class="formulaire" hidden novalidate>
        <label class="champ"><span>Login</span><input name="login" autocomplete="username" minlength="3" maxlength="30" required>
          <small>3 à 30 caractères : lettres, chiffres, « . », « _ » ou « - ».</small></label>
        <label class="champ"><span>Mot de passe</span><input name="mdp" type="password" autocomplete="new-password" minlength="8" required>
          <small>8 caractères minimum, avec au moins une lettre et un chiffre.</small></label>
        <label class="champ"><span>Confirme le mot de passe</span><input name="mdp2" type="password" autocomplete="new-password" required></label>
        <p class="erreur" role="alert"></p>
        <button class="bouton large">Créer mon compte</button>
      </form>
    </div>
  </section>`;
  const onglets = [...contenu.querySelectorAll("[role=tab]")];
  const choisir = tab => onglets.forEach(t => {
    const on = t === tab;
    t.setAttribute("aria-selected", on); t.tabIndex = on ? 0 : -1;
    $("#" + t.getAttribute("aria-controls")).hidden = !on;
    if (on) $("#" + t.getAttribute("aria-controls") + " input").focus();
  });
  onglets.forEach((t, i) => {
    t.addEventListener("click", () => choisir(t));
    t.addEventListener("keydown", e => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") { const n = onglets[(i + 1) % 2]; choisir(n); n.focus(); }
    });
  });
  if (mode === "inscription") choisir(onglets[1]);
  brancher($("#f-co"), d => api("connexion", { methode: "POST", corps: d }));
  brancher($("#f-in"), d => api("inscription", { methode: "POST", corps: d }));

  function brancher(form, envoyer) {
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const err = $(".erreur", form), bouton = $("button", form);
      err.textContent = ""; bouton.disabled = true;
      try {
        etat.utilisateur = await envoyer(Object.fromEntries(new FormData(form)));
        aller(etat.utilisateur.doit_changer ? "#/mot-de-passe" : "#/");
        if (!etat.utilisateur.doit_changer) toast(`Bienvenue, ${etat.utilisateur.login} !`);
      } catch (x) { err.textContent = x.message; } finally { bouton.disabled = false; }
    });
  }
}

function vueMotDePasse() {
  contenu.innerHTML = `
  <section class="accueil-public seul">
    <div class="carte-acces">
      <h1 class="titre-carte">Choisis ton mot de passe</h1>
      <p class="sous">Le compte <strong>${h(etat.utilisateur?.login)}</strong> utilise encore le mot de passe par défaut. Remplace-le avant de continuer.</p>
      <form class="formulaire" novalidate>
        <label class="champ"><span>Nouveau mot de passe</span><input name="nouveau" type="password" autocomplete="new-password" required autofocus>
          <small>8 caractères minimum, avec au moins une lettre et un chiffre.</small></label>
        <label class="champ"><span>Confirme-le</span><input name="confirmation" type="password" autocomplete="new-password" required></label>
        <p class="erreur" role="alert"></p>
        <button class="bouton large">Enregistrer</button>
      </form>
    </div>
  </section>`;
  const form = $("form", contenu);
  form.addEventListener("submit", async e => {
    e.preventDefault();
    try {
      await api("mot-de-passe", { methode: "POST", corps: Object.fromEntries(new FormData(form)) });
      etat.utilisateur.doit_changer = false;
      toast("Mot de passe enregistré.");
      aller("#/");
    } catch (x) { $(".erreur", form).textContent = x.message; }
  });
}

/* ------------------------------------------------------------ jouer : accueil */
async function vueAccueil() {
  chargement(4);
  const [tous, reco, enCours, revision] = await Promise.all([api("quizz"), api("recommandation"),
    api("partie/en-cours"), api("revision")]);
  const liste = tous.filter(q => q.statut === "publie");
  const recoHtml = reco ? `
    <a class="reco fiche entre ${couleur(reco.quizz.id)}" style="--i: 3" href="#/quizz/${reco.quizz.id}">
      <span class="reco-pourquoi">Prochain quizz conseillé, car ${h(reco.raison)}</span>
      <span class="reco-titre">${h(reco.quizz.titre)}</span>
      <span class="reco-meta">${pluriel(reco.quizz.nb_questions, "question")}, ${duree(reco.quizz.duree)}</span>
      <span class="bouton">Jouer ce quizz${fleche()}</span>
    </a>` : `<div class="reco fiche fini entre" style="--i: 3"><span class="reco-titre">Tout est réussi à 100 %.</span>
      <span class="reco-meta">Rejoue un quizz pour garder la main.</span></div>`;
  // Repères calculés à partir des vrais meilleurs scores du joueur
  const joues = liste.filter(q => q.mon_meilleur != null).length;
  const parfaits = liste.filter(q => q.mon_meilleur != null && q.mon_meilleur === q.nb_questions).length;
  const part = liste.length ? joues / liste.length : 0;
  contenu.innerHTML = `
  <section class="page">
    ${revision.questions.length ? `<a class="reprise revision" href="#/reviser">
      <span><strong>Réviser mes erreurs</strong> : ${pluriel(revision.questions.length, "question")} ratée${revision.questions.length > 1 ? "s" : ""} à retravailler, sans compter dans ton score.</span>
      <span class="bouton secondaire">Réviser${fleche()}</span></a>` : ""}
    ${enCours && !enCours.test ? `<a class="reprise" href="#/reprendre">
      <span>Tu as une partie en cours : <strong>${h(enCours.titre)}</strong>${enCours.restant != null ? `, il reste ${horloge(enCours.restant)}` : ""}.</span>
      <span class="bouton">Reprendre${fleche()}</span></a>` : ""}
    <header class="entete"><h1 class="titre-page">Bonjour, <span class="prenom">${h(etat.utilisateur.login)}</span></h1>
      <p class="sous">Choisis un quizz. ${liste.length} disponible${liste.length > 1 ? "s" : ""}.</p></header>
    ${liste.length ? `<ul class="reperes" aria-label="Ta progression">
      <li class="entre" style="--i: 0">
        <svg class="anneau" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15.9" pathLength="100"/>
          <circle class="anneau-valeur" cx="18" cy="18" r="15.9" pathLength="100" style="--valeur: ${Math.round(part * 100)}"/></svg>
        <span><span class="repere-nom">Quizz joués</span><span class="repere-val">${chiffres(joues)}<small> / ${liste.length}</small></span></span></li>
      <li class="entre" style="--i: 1"><span class="repere-icone juste" aria-hidden="true">${icone("juste")}</span>
        <span><span class="repere-nom">Sans faute</span><span class="repere-val">${chiffres(parfaits)}<small> quizz à 100 %</small></span></span></li>
      <li class="entre" style="--i: 2"><span class="repere-icone" aria-hidden="true">${icone("oubli")}</span>
        <span><span class="repere-nom">À découvrir</span><span class="repere-val">${chiffres(liste.length - joues)}<small> jamais joué${liste.length - joues > 1 ? "s" : ""}</small></span></span></li>
    </ul>` : ""}
    ${liste.length ? recoHtml : ""}
    ${liste.length ? `<h2 class="titre-section entre" style="--i: 4">Tous les quizz</h2>
    <div class="filtres" role="group" aria-label="Filtrer par thème">${["Tous", ...new Set(liste.map(q => q.theme))].map(t =>
      `<button type="button" class="puce" data-theme="${h(t)}" aria-pressed="${t === (etat.theme || "Tous")}">${h(t)}</button>`).join("")}</div>
    <ul class="paquets">${liste.map((q, k) => `
      <li class="entre" style="--i: ${Math.min(5 + k, 12)}" data-theme="${h(q.theme)}"><a class="paquet ${couleur(q.id)}" href="#/quizz/${q.id}">
        <span class="paquet-pile" aria-hidden="true"></span>
        <span class="paquet-face">
          <span class="paquet-entete" aria-hidden="true"><span class="paquet-nb">${q.nb_questions}</span><span>question${q.nb_questions > 1 ? "s" : ""}</span>
            <span class="paquet-chrono">${q.duree ? horloge(q.duree) : "libre"}</span></span>
          <span class="paquet-theme">${h(q.theme)}</span>
          <span class="paquet-titre">${h(q.titre)}</span>
          ${q.description ? `<span class="paquet-desc">${h(q.description)}</span>` : ""}
          <span class="paquet-meta"><span class="vh">${pluriel(q.nb_questions, "question")}, ${q.duree ? "minuterie " + horloge(q.duree) : "sans minuterie"}.</span>
            <span class="paquet-score">${q.mon_meilleur == null ? "jamais joué" : `meilleur : ${q.mon_meilleur}/${q.nb_questions}`}</span></span>
        </span></a></li>`).join("")}
    </ul>` : `<div class="vide"><h2>Aucun quizz pour l'instant.</h2>
      <p>${etat.utilisateur.admin ? "Crée le premier, importe un fichier texte ou JSON, ou demande-le à l'IA." : "L'administrateur n'a encore rien publié."}</p>
      ${etat.utilisateur.admin ? `<a class="bouton" href="#/admin">Aller à l'administration</a>` : ""}</div>`}
  </section>`;
  const filtrer = theme => {
    etat.theme = theme;
    contenu.querySelectorAll(".filtres .puce").forEach(b => b.setAttribute("aria-pressed", b.dataset.theme === theme));
    contenu.querySelectorAll(".paquets > li").forEach(li => { li.hidden = theme !== "Tous" && li.dataset.theme !== theme; });
  };
  contenu.querySelectorAll(".filtres .puce").forEach(b => b.addEventListener("click", () => filtrer(b.dataset.theme)));
  if (etat.theme && contenu.querySelector(`.filtres .puce[data-theme="${CSS.escape(etat.theme)}"]`)) filtrer(etat.theme);
}

async function vuePreparer(id) {
  chargement(2);
  const liste = await api("quizz");
  const q = liste.find(x => x.id === Number(id));
  if (!q) throw new Error("Ce quizz n'existe plus.");
  contenu.innerHTML = `
  <section class="page etroite">
    <a class="retour" href="#/">${icone("retour")}Tous les quizz</a>
    <div class="fiche grande ${couleur(q.id)} preparation">
      <h1 class="fiche-titre">${h(q.titre)}</h1>
      <p class="origine">${q.source === "ia" ? "Généré avec l'IA, relu par l'admin" : q.source === "fichier" ? "Importé d'un fichier" : "Créé à la main"}</p>
      ${q.description ? `<p class="fiche-texte">${h(q.description)}</p>` : ""}
      <dl class="faits">
        <div><dt>Questions</dt><dd>${q.nb_questions}</dd></div>
        <div><dt>Minuterie</dt><dd>${q.duree ? horloge(q.duree) : "aucune"}</dd></div>
        <div><dt>Ton meilleur</dt><dd>${q.mon_meilleur == null ? "à faire" : `${q.mon_meilleur}/${q.nb_questions}`}</dd></div>
      </dl>
      <label class="interrupteur"><input type="checkbox" id="aleatoire"><span>Mélanger les questions et les réponses</span></label>
      <div class="actions">
        <a class="bouton" id="go" href="#/jouer/${q.id}">Commencer${fleche()}</a>
        <a class="lien" href="#/classements/${q.id}">Voir le classement</a>
      </div>
    </div>
  </section>`;
  const go = $("#go");
  go.addEventListener("click", () => { sessionStorage.setItem("kwizz-aleatoire", $("#aleatoire").checked ? "1" : "0"); });
}

/* ------------------------------------------------------------ jouer : partie */
function arreterMinuterie() { if (etat.minuterie) { clearInterval(etat.minuterie); etat.minuterie = null; } }

async function vueReprendre() {
  chargement(3);
  const r = await api("partie/en-cours");
  if (!r) { toast("Pas de partie en cours à reprendre."); return aller("#/"); }
  return vueJouer(r.id, r.test, r);
}

async function vueReviser() {
  chargement(3);
  const r = await api("revision");
  if (!r.questions.length) { toast("Aucune erreur à revoir : bravo !"); return aller("#/"); }
  return vueJouer(null, false, null, r);
}

async function vueJouer(id, test = false, reprise = null, revision = null) {
  chargement(3);
  const aleatoire = !test && sessionStorage.getItem("kwizz-aleatoire") === "1";
  const q = revision || reprise || await api(`quizz/${id}/jouer${test ? "?test=1" : aleatoire ? "?aleatoire=1" : ""}`);
  const p = etat.partie = { ...q, index: 0, reponses: reprise ? reprise.reponses : {}, envoyee: false,
    fin: q.duree ? Date.now() + (reprise ? reprise.restant : q.duree) * 1000 : null };
  let attenteSauvegarde;
  const sauver = () => {  // les réponses partent au serveur : une coupure ne fait pas perdre la partie
    clearTimeout(attenteSauvegarde);
    if (q.revision) return;  // une révision n'est pas une partie : rien à reprendre
    attenteSauvegarde = setTimeout(() => api(`quizz/${q.id}/sauver`, { methode: "POST",
      corps: { partie: q.partie, reponses: p.reponses } }).catch(() => {}), 400);
  };
  const teinte = couleur(q.id);
  contenu.innerHTML = `
  <section class="partie" style="--fiche: var(--${teinte})">
    <header class="partie-barre">
      <h1 class="partie-titre">${q.test ? `<span class="badge-test">Mode test</span> ` : ""}${h(q.titre)}</h1>
      <ol class="progression" aria-label="Progression">${q.questions.map((_, i) => `<li data-i="${i}"><span class="vh">Question ${i + 1}</span></li>`).join("")}</ol>
      ${p.fin ? `<div class="minuterie" id="minuterie" aria-hidden="true">${horloge(q.duree)}</div><p class="vh" id="minuterie-sr" aria-live="polite"></p>` : ""}
    </header>
    <div class="scene">
      <div class="pile" aria-hidden="true"><i></i><i></i></div>
      <div class="fiche-jeu" id="fiche"></div>
    </div>
    <footer class="partie-pied">
      <button class="lien" id="abandon" type="button">Abandonner</button>
      <div class="partie-nav">
        <button class="bouton secondaire" id="prec" type="button">Précédente</button>
        <button class="bouton" id="suiv" type="button">Suivante</button>
      </div>
    </footer>
  </section>`;
  $("#prec").addEventListener("click", () => montrer(p.index - 1));
  $("#suiv").addEventListener("click", () => p.index === q.questions.length - 1 ? terminer() : montrer(p.index + 1));
  $("#abandon").addEventListener("click", async () => {
    if (await confirmer({ titre: "Abandonner ce quizz ?", texte: "Ta partie ne sera pas enregistrée.", action: "Abandonner" })) aller(q.test ? "#/admin/quizz" : "#/");
  });
  contenu.querySelector(".partie").addEventListener("keydown", clavier);
  montrer(0);
  $("#enonce").focus({ preventScroll: true }); // sinon les touches 1 à 9 ne marchent qu'après un clic
  if (p.fin) {
    let dernierAnnonce = null;
    const tic = () => {
      const reste = (p.fin - Date.now()) / 1000;
      const m = $("#minuterie");
      if (!m) return arreterMinuterie();
      m.textContent = horloge(reste);
      m.classList.toggle("urgent", reste <= 10);
      const palier = reste <= 10 ? Math.ceil(reste) : Math.ceil(reste / 30) * 30;
      if (palier !== dernierAnnonce && (reste <= 10 || Math.ceil(reste) % 30 === 0)) {
        dernierAnnonce = palier;
        $("#minuterie-sr").textContent = `Il reste ${Math.ceil(reste)} secondes.`;
      }
      if (reste <= 0) { arreterMinuterie(); toast("Temps écoulé : tes réponses sont envoyées.", "alerte"); terminer(true); }
    };
    tic();
    etat.minuterie = setInterval(tic, 250);
  }

  function montrer(i) {
    if (i < 0 || i >= q.questions.length) return;
    const avant = p.index;
    p.index = i;
    const question = q.questions[i];
    const choisis = p.reponses[question.id] || [];
    const type = question.multiple ? "checkbox" : "radio";
    const fiche = $("#fiche");
    fiche.className = "fiche-jeu" + (i !== avant ? (i > avant ? " entre-droite" : " entre-gauche") : "");
    fiche.innerHTML = `
      <span class="badge-etape" aria-hidden="true">${i + 1}</span>
      <p class="fiche-num">Question ${i + 1} sur ${q.questions.length}</p>
      <h2 class="fiche-question" id="enonce" tabindex="-1">${h(question.enonce)}</h2>
      <p class="consigne">${question.multiple ? "Plusieurs bonnes réponses : coche-les toutes." : "Une seule bonne réponse."}</p>
      <fieldset class="choix" aria-labelledby="enonce">
        ${question.choix.map((c, k) => `
          <label class="choix-ligne">
            <input type="${type}" name="q${question.id}" value="${c.id}" ${choisis.includes(c.id) ? "checked" : ""}>
            <span class="case" aria-hidden="true"></span>
            <span class="choix-texte">${h(c.texte)}</span>
            <kbd aria-hidden="true">${k + 1}</kbd>
          </label>`).join("")}
      </fieldset>`;
    fiche.querySelectorAll("input").forEach(inp => inp.addEventListener("change", () => {
      p.reponses[question.id] = [...fiche.querySelectorAll("input:checked")].map(x => Number(x.value));
      majProgression();
      sauver();
    }));
    $("#prec").disabled = i === 0;
    $("#suiv").textContent = i === q.questions.length - 1 ? "Valider mes réponses" : "Suivante";
    majProgression();
    if (avant !== i) $("#enonce").focus?.();
  }

  function majProgression() {
    contenu.querySelectorAll(".progression li").forEach((li, i) => {
      const id = q.questions[i].id;
      li.classList.toggle("repondu", (p.reponses[id] || []).length > 0);
      li.classList.toggle("courant", i === p.index);
      li.querySelector(".vh").textContent = `Question ${i + 1}${(p.reponses[id] || []).length ? ", répondue" : ""}${i === p.index ? ", en cours" : ""}`;
    });
  }

  function clavier(e) {
    if (e.target.matches("textarea, input[type=text]")) return;
    const n = Number(e.key);
    if (n >= 1 && n <= 9) {
      const inp = contenu.querySelectorAll(".choix input")[n - 1];
      if (inp) { inp.click(); e.preventDefault(); }
    } else if (e.key === "ArrowRight") { $("#suiv").click(); e.preventDefault(); }
    else if (e.key === "ArrowLeft") { montrer(p.index - 1); e.preventDefault(); }
  }

  async function terminer(force = false) {
    if (p.envoyee) return;
    const manquantes = q.questions.filter(x => !(p.reponses[x.id] || []).length).length;
    if (!force && manquantes && !(await confirmer({
      titre: `${pluriel(manquantes, "question")} sans réponse`,
      texte: "Elles compteront comme fausses. Valider quand même ?", action: "Valider",
    }))) return;
    p.envoyee = true;
    arreterMinuterie();
    $("#suiv").disabled = true;
    try {
      const resultat = q.revision
        ? await api("revision/corriger", { methode: "POST", corps: { questions: q.questions.map(x => x.id), reponses: p.reponses } })
        : await api(`quizz/${q.id}/corriger`, { methode: "POST", corps: { partie: q.partie, reponses: p.reponses } });
      etat.resultat = resultat;
      const fiche = $("#fiche");
      const bascule = !matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (bascule) {
        fiche.insertAdjacentHTML("afterend", `<div class="fiche-verso" aria-hidden="true">
          <span class="verso-score">${resultat.score}<small>/${resultat.total}</small></span></div>`);
        contenu.querySelector(".scene").classList.add("retournee");
        await new Promise(r => setTimeout(r, 900));
      }
      aller("#/resultat");
    } catch (x) { p.envoyee = false; $("#suiv").disabled = false; toast(x.message, "alerte"); }
  }
}

/* ------------------------------------------------------------ résultat et corrigé */
async function vueCorrige(id) {
  chargement(4);
  etat.resultat = { ...(await api(`partie/${id}/corrige`)), revue: true };
  vueResultat();
}

function vueResultat() {
  const r = etat.resultat;
  if (!r) return aller("#/");
  const ratio = r.score / r.total;
  const verdict = ratio === 1 ? "Sans faute." : ratio >= .7 ? "Bien joué." : ratio >= .4 ? "C'est un début." : "À retravailler.";
  contenu.innerHTML = `
  <section class="page resultat" style="--fiche: var(--${couleur(r.id_quizz)})">
    <header class="score-bloc">
      <p class="score-quizz">${h(r.titre)}</p>
      <p class="score" aria-label="Score : ${r.score} sur ${r.total}">${chiffres(r.score)}<span>/${r.total}</span></p>
      <p class="verdict">${verdict}</p>
      ${r.test ? `<p class="note">Mode test : ce score n'est enregistré nulle part. ${r.statut === "brouillon"
        ? "Si tout est correct, valide le quizz pour le publier ; sinon, modifie-le puis reteste-le." : "Ce quizz est déjà publié."}</p>` : ""}
      ${r.revision ? `<p class="note">Révision : ce score n'est pas compté. Une question reste à revoir tant que tu ne l'as pas réussie dans une vraie partie du quizz.</p>` : ""}
      ${r.revue ? `<p class="score-meta">Partie du ${date(r.date)}${r.duree != null ? ", " + duree(r.duree) : ""}.</p>` : ""}
      <p class="score-meta" ${r.revue || r.revision ? "hidden" : ""}>${r.temps_ecoule ? "Temps écoulé. " : ""}${duree(r.duree)}${r.rang ? `, ${r.rang}${r.rang === 1 ? "er" : "e"} au classement` : ""}${r.meilleur > r.score ? ` grâce à ton meilleur score (${r.meilleur}/${r.total})` : ""}.</p>
      ${r.revision ? `<div class="actions">
        <a class="bouton" href="#/reviser">Réviser encore</a>
        <a class="lien" href="#/">Retour aux quizz</a>
      </div>` : r.revue ? `<div class="actions">
        ${r.archive ? "" : `<a class="bouton" href="#/jouer/${r.id_quizz}">Rejouer</a>`}
        <a class="bouton secondaire" href="#/historique">Retour à l'historique</a>
      </div>` : r.test ? `<div class="actions">
        ${r.statut === "brouillon" ? `<button class="bouton" type="button" id="valider-test">Valider et publier</button>` : ""}
        <a class="bouton secondaire" href="#/admin/editer/${r.id_quizz}">Modifier</a>
        <a class="bouton secondaire" href="#/tester/${r.id_quizz}">Retester</a>
        <a class="lien" href="#/admin/quizz">Tous les quizz</a>
      </div>` : `<div class="actions">
        <a class="bouton" href="#/jouer/${r.id_quizz}">Rejouer</a>
        <a class="bouton secondaire" href="#/classements/${r.id_quizz}">Classement</a>
        <a class="lien" href="#/">Autres quizz</a>
      </div>`}
    </header>
    <div class="corrige">
      <h2 class="titre-section">Le corrigé, question par question</h2>
      <p class="legende"><span><span class="marque-juste">${icone("juste")}</span>bonne réponse cochée</span>
        <span><span class="marque-faux">${icone("faux")}</span>cochée à tort</span>
        <span><span class="marque-oubli">${icone("oubli")}</span>bonne réponse oubliée</span></p>
      <ol class="fiches-corrige">${r.detail.map((d, i) => `
        <li class="fiche-corrige ${d.juste ? "est-juste" : "est-faux"}" style="--i: ${i}">
          <div class="fc-tete"><span class="fc-num">${i + 1}</span>
            <span class="fc-etat">${icone(d.juste ? "juste" : "faux")}${d.juste ? "Juste" : "Faux"}</span></div>
          <h3 class="fc-question">${h(d.enonce)}</h3>
          <ul class="fc-choix">${d.choix.map(c => {
            const m = c.correct && c.coche ? "juste" : !c.correct && c.coche ? "faux" : c.correct ? "oubli" : "neutre";
            const lu = { juste: "bonne réponse, cochée", faux: "cochée à tort", oubli: "bonne réponse, oubliée", neutre: "" }[m];
            return `<li class="fc-${m}"><span class="fc-marque" aria-hidden="true">${m === "neutre" ? "" : icone(m)}</span>
              ${h(c.texte)}${lu ? `<span class="vh"> (${lu})</span>` : ""}</li>`;
          }).join("")}</ul>
          ${d.explication || (!d.juste && etat.ia) ? `<button class="lien pourquoi" type="button" data-q="${d.id}" data-i="${i}"
              data-choisis="${d.choix.filter(c => c.coche).map(c => c.id).join(",")}">Pourquoi ?</button>
            <p class="explication" aria-live="polite"></p>` : ""}
        </li>`).join("")}
      </ol>
    </div>
  </section>`;
  $("#valider-test")?.addEventListener("click", () => validerQuizz(r.id_quizz, r.titre, "#/admin/quizz"));
  contenu.querySelectorAll(".pourquoi").forEach(b => b.addEventListener("click", async () => {
    const zone = b.nextElementSibling, gardee = r.detail[b.dataset.i].explication;
    if (gardee) { zone.textContent = gardee; b.hidden = true; return; }
    b.disabled = true; zone.textContent = "L'IA rédige une explication…";
    try {
      const rep = await api("expliquer", { methode: "POST", corps: { id_question: Number(b.dataset.q),
        choisis: b.dataset.choisis ? b.dataset.choisis.split(",").map(Number) : [] } });
      zone.textContent = rep.texte; b.hidden = true;
    } catch (x) { zone.textContent = x.message; b.disabled = false; }
  }));
}

/* ------------------------------------------------------------ historique */
async function vueHistorique() {
  chargement(5);
  const lignes = await api("historique");
  const parQuizz = new Map();
  lignes.forEach(t => { if (!parQuizz.has(t.id_quizz)) parQuizz.set(t.id_quizz, []); parQuizz.get(t.id_quizz).push(t); });
  contenu.innerHTML = `
  <section class="page">
    <header class="entete"><h1 class="titre-page">Historique</h1>
      <p class="sous">${lignes.length ? `${pluriel(lignes.length, "partie")} jouée${lignes.length > 1 ? "s" : ""}, de la plus récente à la plus ancienne.` : ""}</p></header>
    ${lignes.length ? `<div class="historique">${[...parQuizz.entries()].map(([id, ts]) => {
      const meilleur = Math.max(...ts.map(t => t.score));
      return `<article class="hist-groupe" style="--fiche: var(--${couleur(id)})">
        <header class="hist-tete"><h2>${h(ts[0].titre)}</h2>
          <p>meilleur <strong>${meilleur}/${ts[0].total}</strong>, ${pluriel(ts.length, "partie")}</p>
          ${ts[0].archive ? `<span class="hist-archive">quizz retiré</span>` : `<a class="lien" href="#/quizz/${id}">Rejouer</a>`}</header>
        <ol class="hist-parties">${ts.map(t => `
          <li><span class="hist-score ${t.score === meilleur ? "record" : ""}">${t.score}/${t.total}</span>
            <span class="hist-date">${date(t.date)}</span>
            <span class="hist-duree">${t.duree != null ? duree(t.duree) : ""}</span>
            ${t.revoir ? `<a class="lien" href="#/corrige/${t.id}">Revoir<span class="vh"> le corrigé de cette partie</span></a>` : ""}</li>`).join("")}</ol>
      </article>`;
    }).join("")}</div>` : `<div class="vide"><h2>Pas encore de partie.</h2><p>Ton historique se remplit dès ton premier quizz.</p>
      <a class="bouton" href="#/">Choisir un quizz</a></div>`}
  </section>`;
}

/* ------------------------------------------------------------ classements */
async function vueClassements(id) {
  chargement(4);
  const liste = (await api("quizz")).filter(q => q.statut === "publie");
  if (!liste.length) {
    contenu.innerHTML = `<section class="page"><h1 class="titre-page">Classements</h1><div class="vide"><p>Aucun quizz.</p></div></section>`;
    return;
  }
  const choisi = Number(id) || liste[0].id;
  const c = await api(`quizz/${choisi}/classement`);
  contenu.innerHTML = `
  <section class="page" style="--fiche: var(--${couleur(choisi)})">
    <header class="entete"><h1 class="titre-page">Classements</h1>
      <p class="sous">Le meilleur score de chaque joueur. À égalité, le premier arrivé passe devant.</p></header>
    <nav class="onglets-quizz" aria-label="Choisir un quizz">${liste.map(q => `
      <a href="#/classements/${q.id}" class="${q.id === choisi ? "actif" : ""}" style="--fiche: var(--${couleur(q.id)})"
        ${q.id === choisi ? 'aria-current="page"' : ""}>${h(q.titre)}</a>`).join("")}</nav>
    ${c.lignes.length ? `<ol class="podium">${c.lignes.map((l, i) => `
      <li class="${l.moi ? "moi" : ""} rang-${i + 1}">
        <span class="rang">${i + 1}</span>
        <span class="joueur">${h(l.login)}${l.moi ? " (toi)" : ""}</span>
        <span class="pts">${l.score}<small>/${c.total}</small></span>
      </li>`).join("")}</ol>` : `<div class="vide"><h2>Personne n'a encore joué ce quizz.</h2>
      <p>Sois le premier sur le podium.</p><a class="bouton" href="#/quizz/${choisi}">Jouer</a></div>`}
  </section>`;
}

/* ------------------------------------------------------------ administration : quizz */
const STATUTS = { brouillon: "Brouillon", publie: "Publié", archive: "Archivé" };
function etiquetteStatut(q) {
  if (q.archive) return `<span class="statut archive">Archivé</span>`;
  if (q.statut === "publie") return `<span class="statut publie">Publié</span>`;
  return `<span class="statut brouillon">Brouillon${q.teste_le ? " · testé" : " · à tester"}</span>`;
}

async function validerQuizz(id, titre, retour) {
  try { await api(`admin/quizz/${id}/valider`, { methode: "POST" }); toast(`« ${titre} » est publié pour les joueurs.`); }
  catch (x) { toast(x.message, "alerte"); }
  aller(retour);
}

async function vueAdmin() {
  if (!etat.utilisateur.admin) return aller("#/");
  chargement(4);
  const liste = await api("quizz?archives=1");
  const etatQ = q => q.archive ? "archive" : q.statut;
  const brouillons = liste.filter(q => etatQ(q) === "brouillon").length;
  contenu.innerHTML = `
  <section class="page">
    <header class="entete ligne"><div><h1 class="titre-page">Administration</h1>
      <p class="sous">Crée ou importe un quizz, teste-le, corrige-le, puis valide-le pour le publier.</p></div>
      <div class="actions">
        <a class="bouton" href="#/admin/nouveau">Nouveau quizz</a>
        <a class="bouton secondaire" href="#/admin/importer">Importer un fichier</a>
        ${etat.ia ? `<a class="bouton secondaire" href="#/admin/generer">Générer avec l'IA</a>` : ""}
      </div></header>
    ${sousNavAdmin("quizz")}
    <ol class="cycle" aria-label="Cycle de publication d'un quizz">
      <li><strong>1. Créer</strong> ou importer : brouillon</li><li><strong>2. Tester</strong> : tu joues, rien n'est compté</li>
      <li><strong>3. Modifier</strong> si besoin, puis retester</li><li><strong>4. Valider</strong> : visible des joueurs</li></ol>
    ${brouillons ? `<p class="note">${pluriel(brouillons, "quizz")} en brouillon, invisible${brouillons > 1 ? "s" : ""} pour les joueurs.</p>` : ""}
    ${etat.ia ? "" : `<p class="note">Assistant IA désactivé : ajoute ta clé dans le fichier <code>.env</code> pour générer des quizz.</p>`}
    <div class="filtres" role="group" aria-label="Filtrer par statut">${["Tous", "brouillon", "publie", "archive"].map(s =>
      `<button type="button" class="puce" data-statut="${s}" aria-pressed="${s === "Tous"}">${s === "Tous" ? "Tous" : STATUTS[s] + "s"}</button>`).join("")}</div>
    ${liste.length ? `<table class="table-admin">
      <thead><tr><th scope="col">Quizz</th><th scope="col">Statut</th><th scope="col">Thème</th><th scope="col">Questions</th><th scope="col">Minuterie</th><th scope="col"><span class="vh">Actions</span></th></tr></thead>
      <tbody>${liste.map(q => `<tr data-statut="${etatQ(q)}" ${q.archive ? "hidden" : ""}>
        <th scope="row"><span class="pastille" style="--fiche: var(--${couleur(q.id)})" aria-hidden="true"></span>${h(q.titre)}
          <small class="origine-q">${{ manuel: "à la main", fichier: "fichier", ia: "IA" }[q.source] || q.source}${q.valide_le ? ", validé le " + date(q.valide_le) : ""}</small></th>
        <td>${etiquetteStatut(q)}</td><td>${h(q.theme)}</td><td>${q.nb_questions}</td><td>${q.duree ? horloge(q.duree) : "aucune"}</td>
        <td class="cellule-actions">${q.archive ? `
          <button class="lien fort" type="button" data-act="restaurer" data-id="${q.id}" data-titre="${h(q.titre)}">Restaurer</button>
          <a class="lien" href="/api/admin/quizz/${q.id}/export" download>Exporter</a>` : `
          <a class="lien" href="#/tester/${q.id}">Tester</a>
          <a class="lien" href="#/admin/editer/${q.id}">Modifier</a>
          ${q.statut === "publie"
            ? `<button class="lien" type="button" data-act="depublier" data-id="${q.id}" data-titre="${h(q.titre)}">Retirer</button>`
            : `<button class="lien fort" type="button" data-act="valider" data-id="${q.id}" data-titre="${h(q.titre)}" ${q.teste_le ? "" : 'aria-disabled="true" title="Teste-le d\'abord"'}>Valider</button>`}
          <a class="lien" href="/api/admin/quizz/${q.id}/export" download>Exporter</a>
          <button class="bouton-suppr" type="button" data-act="suppr" data-id="${q.id}" data-titre="${h(q.titre)}">Supprimer</button>`}
        </td></tr>`).join("")}</tbody></table>`
    : `<div class="vide"><h2>Aucun quizz.</h2><p>Commence par un nouveau quizz ou importe <code>data/exemples/capitales.txt</code>.</p></div>`}
  </section>`;
  contenu.querySelectorAll(".filtres .puce").forEach(b => b.addEventListener("click", () => {
    contenu.querySelectorAll(".filtres .puce").forEach(x => x.setAttribute("aria-pressed", x === b));
    contenu.querySelectorAll("tbody tr").forEach(tr => {  // « Tous » = tout sauf l'archive
      tr.hidden = b.dataset.statut === "Tous" ? tr.dataset.statut === "archive" : tr.dataset.statut !== b.dataset.statut;
    });
  }));
  contenu.querySelectorAll("button[data-act]").forEach(b => b.addEventListener("click", async () => {
    const { id, titre } = b.dataset;
    if (b.dataset.act === "valider") {
      if (b.getAttribute("aria-disabled")) return toast("Teste d'abord ce quizz (lien « Tester ») avant de le valider.", "alerte");
      return validerQuizz(id, titre, "#/admin/quizz").then(vueAdmin);
    }
    if (b.dataset.act === "restaurer") {
      try { await api(`admin/quizz/${id}/restaurer`, { methode: "POST" }); toast(`« ${titre} » est restauré en brouillon : valide-le pour le republier.`); vueAdmin(); }
      catch (x) { toast(x.message, "alerte"); }
      return;
    }
    if (b.dataset.act === "depublier") {
      if (!(await confirmer({ titre: `Retirer « ${titre} » ?`, action: "Repasser en brouillon",
        texte: "Les joueurs ne le verront plus jusqu'à une nouvelle validation. Les scores déjà obtenus sont gardés." }))) return;
      try { await api(`admin/quizz/${id}/depublier`, { methode: "POST" }); toast("Quizz repassé en brouillon."); vueAdmin(); }
      catch (x) { toast(x.message, "alerte"); }
      return;
    }
    if (!(await confirmer({ titre: `Supprimer « ${titre} » ?`, danger: true, action: "Supprimer",
      texte: "Il disparaît pour tout le monde. S'il a déjà été joué, il est archivé : l'historique et les scores des joueurs sont gardés. Sinon, il est effacé." }))) return;
    try {
      const r = await api(`admin/quizz/${id}`, { methode: "DELETE" });
      toast(r.archive ? `Quizz archivé : ${pluriel(r.parties_gardees, "partie")} de joueurs gardée${r.parties_gardees > 1 ? "s" : ""}.` : "Quizz supprimé.");
      vueAdmin();
    }
    catch (x) { toast(x.message, "alerte"); }
  }));
}

/* ------------------------------------------------------------ administration : tableau de bord */
async function vueTableauBord() {
  if (!etat.utilisateur.admin) return aller("#/");
  chargement(5);
  const st = await api("admin/stats");
  const max = Math.max(1, ...st.par_jour.map(j => j.parties));
  contenu.innerHTML = `
  <section class="page">
    <header class="entete"><h1 class="titre-page">Administration</h1>
      <p class="sous">L'activité des joueurs et les résultats de chaque quizz.</p></header>
    ${sousNavAdmin("bord")}
    <ul class="cartes-stats">
      <li><span>Utilisateurs</span><strong>${chiffres(st.utilisateurs)}<small> dont ${st.admins} admin</small></strong></li>
      <li><span>Actifs (7 jours)</span><strong>${chiffres(st.actifs_7j)}</strong></li>
      <li><span>Quizz</span><strong>${chiffres(st.quizz)}<small> dont ${st.brouillons} brouillon${st.brouillons > 1 ? "s" : ""}</small></strong></li>
      <li><span>Parties jouées</span><strong>${chiffres(st.parties)}</strong></li>
      <li><span>Réussite moyenne</span><strong>${chiffres(st.reussite)}<small> %</small></strong></li>
    </ul>
    <h2 class="titre-section">Parties par jour (14 derniers jours)</h2>
    <ol class="histogramme" aria-label="Parties par jour">${st.par_jour.map(j => `<li title="${j.parties} partie(s)">
      <span class="colonne" style="height: ${Math.round(100 * j.parties / max)}%"></span>
      <span class="valeur">${j.parties || ""}</span>
      <span class="jour">${new Date(j.jour + "T12:00").toLocaleDateString("fr-FR", { day: "numeric", month: "numeric" })}</span>
      <span class="vh">${j.parties} partie(s)</span></li>`).join("")}</ol>
    <h2 class="titre-section">Résultats par quizz</h2>
    <div class="defile"><table class="table-admin">
      <thead><tr><th scope="col">Quizz</th><th scope="col">Statut</th><th scope="col">Parties</th><th scope="col">Joueurs</th><th scope="col">Réussite</th><th scope="col">Question la plus ratée</th></tr></thead>
      <tbody>${st.par_quizz.map(q => `<tr>
        <th scope="row">${h(q.titre)}<small class="origine-q">${h(q.theme)}</small></th>
        <td>${etiquetteStatut(q)}</td><td>${q.parties}</td><td>${q.joueurs}</td>
        <td>${q.parties ? `<span class="jauge" style="--v: ${q.reussite}%"></span>${q.reussite} %` : "—"}</td>
        <td class="pire">${q.pire ? `${h(q.pire.enonce)} <strong>(${q.pire.taux} % d'échec)</strong>` : "—"}</td></tr>`).join("")}</tbody></table></div>
    ${st.parties ? `<h2 class="titre-section">Réussite par thème</h2>${barres(st.themes.filter(t => t.parties))}` : ""}
    <h2 class="titre-section" id="titre-questions">Questions les plus ratées</h2>
    <label class="champ filtre-questions"><span>Quizz</span><select id="filtre-questions">
      <option value="">Tous les quizz</option>${st.par_quizz.filter(q => q.parties).map(q => `<option value="${q.id}">${h(q.titre)}</option>`).join("")}
    </select></label>
    <div id="questions-ratees"></div>
    <h2 class="titre-section">Dernières parties</h2>
    ${st.dernieres.length ? `<div class="defile"><table class="table-admin">
      <thead><tr><th scope="col">Joueur</th><th scope="col">Quizz</th><th scope="col">Score</th><th scope="col">Durée</th><th scope="col">Date</th></tr></thead>
      <tbody>${st.dernieres.map(d => `<tr><th scope="row">${h(d.login)}</th><td>${h(d.titre)}</td>
        <td>${d.score}/${d.total}</td><td>${d.duree != null ? duree(d.duree) : ""}</td><td>${date(d.date)}</td></tr>`).join("")}</tbody></table></div>`
      : `<p class="note">Aucune partie pour l'instant.</p>`}
    <p class="lien-suite"><a class="lien" href="#/admin/journal">Voir toutes les actions des utilisateurs</a></p>
  </section>`;
  const zone = $("#questions-ratees");
  const montrerQuestions = async id => {
    const qs = await api(`admin/questions${id ? "?quizz=" + id : ""}`);
    zone.innerHTML = qs.length ? `<div class="defile"><table class="table-admin" aria-labelledby="titre-questions">
      <thead><tr><th scope="col">Question</th><th scope="col">Quizz</th><th scope="col">Réponses</th><th scope="col">Réussite</th></tr></thead>
      <tbody>${qs.map(q => `<tr><th scope="row">${h(q.enonce)}</th><td>${h(q.titre)}</td><td>${q.reponses}</td>
        <td><span class="jauge" style="--v: ${q.reussite}%"></span>${q.reussite} %</td></tr>`).join("")}</tbody></table></div>`
      : `<p class="note">Aucune question jouée pour l'instant.</p>`;
  };
  $("#filtre-questions").addEventListener("change", e => montrerQuestions(e.target.value));
  montrerQuestions("");
}

/* ------------------------------------------------------------ administration : journal */
async function vueJournal() {
  if (!etat.utilisateur.admin) return aller("#/");
  chargement(6);
  const filtre = etat.filtreJournal || { utilisateur: "", action: "" };
  const [comptes, j] = await Promise.all([api("admin/utilisateurs"),
    api(`admin/journal?utilisateur=${encodeURIComponent(filtre.utilisateur)}&action=${encodeURIComponent(filtre.action)}`)]);
  contenu.innerHTML = `
  <section class="page">
    <header class="entete"><h1 class="titre-page">Administration</h1>
      <p class="sous">Toutes les actions des utilisateurs, de la plus récente à la plus ancienne (500 au maximum).</p></header>
    ${sousNavAdmin("journal")}
    <form class="filtres-journal" id="f-journal">
      <label class="champ"><span>Utilisateur</span><select name="utilisateur"><option value="">Tous</option>
        ${comptes.map(u => `<option value="${u.id}" ${String(u.id) === filtre.utilisateur ? "selected" : ""}>${h(u.login)}</option>`).join("")}</select></label>
      <label class="champ"><span>Action</span><select name="action"><option value="">Toutes</option>
        ${Object.entries(j.libelles).map(([k, v]) => `<option value="${k}" ${k === filtre.action ? "selected" : ""}>${h(v)}</option>`).join("")}</select></label>
    </form>
    ${tableJournal(j.lignes)}
  </section>`;
  $("#f-journal").addEventListener("change", e => {
    etat.filtreJournal = Object.fromEntries(new FormData(e.currentTarget)); vueJournal();
  });
}

function tableJournal(lignes, avecLogin = true) {
  if (!lignes.length) return `<p class="note">Aucune action enregistrée.</p>`;
  return `<div class="defile"><table class="table-admin journal">
    <thead><tr><th scope="col">Date</th>${avecLogin ? '<th scope="col">Utilisateur</th>' : ""}<th scope="col">Action</th><th scope="col">Détail</th></tr></thead>
    <tbody>${lignes.map(l => `<tr class="act-${h(l.action)}"><td>${date(l.date)}</td>
      ${avecLogin ? `<th scope="row">${h(l.login)}${l.id_utilisateur == null ? " <small>(supprimé)</small>" : ""}</th>` : ""}
      <td><span class="action">${h(l.libelle)}</span></td><td>${h(l.detail)}</td></tr>`).join("")}</tbody></table></div>`;
}

/* Fenêtre « historique » d'un utilisateur : ses parties et toutes ses actions. */
async function ouvrirHistorique(id) {
  const d = $("#dialogue");
  d.classList.add("large");
  d.innerHTML = `<div class="dialogue-corps"><p>Chargement…</p></div>`;
  d.showModal();
  d.addEventListener("close", () => d.classList.remove("large"), { once: true });
  try {
    const u = await api(`admin/utilisateurs/${id}/historique`);
    const t = u.tableau;
    d.innerHTML = `<div class="dialogue-corps">
      <div class="fenetre-tete"><h2>Historique de ${h(u.login)}${u.admin ? " (admin)" : ""}</h2>
        <form method="dialog"><button class="croix" aria-label="Fermer">${icone("retirer")}</button></form></div>
      <p>Compte créé le ${date(u.depuis)} · ${pluriel(t.parties, "partie")} · réussite ${t.reussite} % · temps de jeu ${duree(t.temps_total)}</p>
      <div class="onglets" role="tablist">
        <button role="tab" aria-selected="true" data-p="h-parties">Parties (${u.parties.length})</button>
        <button role="tab" aria-selected="false" data-p="h-actions" tabindex="-1">Actions (${u.actions.length})</button>
      </div>
      <div id="h-parties" class="fenetre-defile">${t.themes.length ? barres(t.themes) : ""}
        ${u.parties.length ? `<table class="table-admin"><thead><tr><th scope="col">Quizz</th><th scope="col">Score</th><th scope="col">Durée</th><th scope="col">Date</th></tr></thead>
        <tbody>${u.parties.map(p => `<tr><th scope="row">${h(p.titre)}</th><td>${p.score}/${p.total}</td>
          <td>${p.duree != null ? duree(p.duree) : ""}</td><td>${date(p.date)}</td></tr>`).join("")}</tbody></table>` : `<p class="note">Aucune partie.</p>`}</div>
      <div id="h-actions" class="fenetre-defile" hidden>${tableJournal(u.actions, false)}</div></div>`;
    d.querySelectorAll("[role=tab]").forEach(b => b.addEventListener("click", () => d.querySelectorAll("[role=tab]").forEach(x => {
      const on = x === b; x.setAttribute("aria-selected", on); x.tabIndex = on ? 0 : -1; $("#" + x.dataset.p, d).hidden = !on;
    })));
  } catch (x) { d.innerHTML = `<div class="dialogue-corps"><p>${h(x.message)}</p><form method="dialog"><button class="bouton">Fermer</button></form></div>`; }
}

const THEMES = ["Culture générale", "Code", "Histoire", "Mathématiques", "Physique-Chimie", "SVT", "Géographie"];
function quizzVide() { return { titre: "", description: "", duree: 120, source: "manuel", theme: "Culture générale",
  questions: [{ enonce: "", choix: [{ texte: "", correct: true }, { texte: "", correct: false }] }] }; }

async function vueEditeur(id) {
  if (!etat.utilisateur.admin) return aller("#/");
  let q, titre;
  if (location.hash === "#/admin/brouillon" && etat.brouillon) { q = etat.brouillon; titre = q.source === "ia" ? "Relis le quizz proposé par l'IA" : "Vérifie le quizz importé"; }
  else if (id) { chargement(4); q = await api(`admin/quizz/${id}`); titre = "Modifier le quizz"; }
  else { q = quizzVide(); titre = "Nouveau quizz"; }
  const rendre = () => {
    contenu.innerHTML = `
    <section class="page editeur">
      <a class="retour" href="#/admin/quizz">${icone("retour")}Quizz</a>
      <h1 class="titre-page">${titre}</h1>
      ${q.source === "ia" && !id ? `<p class="note">Proposé par l'IA : vérifie chaque question et chaque bonne réponse avant d'enregistrer.</p>` : ""}
      ${id ? `<p class="note">Enregistrer remplace les questions (les scores passés restent, le détail des réponses cochées est perdu) et repasse le quizz en brouillon : il disparaît pour les joueurs jusqu'à ce que tu le testes et le valides à nouveau.</p>`
        : `<p class="note">Un nouveau quizz est enregistré en brouillon : les joueurs ne le voient qu'après ton test et ta validation.</p>`}
      <form class="formulaire" id="form-q" novalidate>
        <div class="grille-meta">
          <label class="champ large"><span>Titre</span><input name="titre" value="${h(q.titre)}" required maxlength="120"></label>
          <label class="champ"><span>Minuterie (secondes)</span><input name="duree" type="number" min="1" step="1" inputmode="numeric" value="${q.duree ?? ""}" placeholder="aucune">
            <small>Vide : pas de minuterie.</small></label>
          <label class="champ"><span>Thème</span><input name="theme" list="themes" value="${h(q.theme || "Divers")}" maxlength="40" required>
            <datalist id="themes">${THEMES.map(t => `<option value="${h(t)}">`).join("")}</datalist></label>
          <label class="champ large"><span>Description</span><input name="description" value="${h(q.description)}" maxlength="300"></label>
        </div>
        <ol class="questions-ed">${q.questions.map((x, i) => `
          <li class="fiche-ed" data-i="${i}" style="--fiche: var(--${COULEURS[i % COULEURS.length]})">
            <div class="fe-tete"><span class="fe-num">Question ${i + 1}</span>
              <button class="lien" type="button" data-act="suppr-q" ${q.questions.length === 1 ? "disabled" : ""}>Retirer la question</button></div>
            <label class="champ"><span>Énoncé</span><textarea name="enonce" rows="2" required>${h(x.enonce)}</textarea></label>
            <label class="champ"><span>Explication (optionnelle)</span><textarea name="explication" rows="2" maxlength="1000"
              placeholder="Pourquoi la bonne réponse est juste. Montrée au joueur après la correction.">${h(x.explication || "")}</textarea></label>
            <fieldset class="choix-ed"><legend>Choix (coche les bonnes réponses)</legend>
              ${x.choix.map((c, k) => `<div class="choix-ed-ligne" data-k="${k}">
                <label class="case-correct"><input type="checkbox" ${c.correct ? "checked" : ""} data-act="correct"><span class="vh">Bonne réponse</span></label>
                <input class="texte-choix" value="${h(c.texte)}" aria-label="Choix ${k + 1}" placeholder="Choix ${k + 1}" data-act="texte">
                <button class="croix" type="button" data-act="suppr-c" aria-label="Retirer le choix ${k + 1}" ${x.choix.length <= 2 ? "disabled" : ""}>${icone("retirer")}</button>
              </div>`).join("")}
              <button class="lien" type="button" data-act="ajout-c">+ Ajouter un choix</button>
            </fieldset>
          </li>`).join("")}</ol>
        <button class="bouton secondaire" type="button" id="ajout-q">+ Ajouter une question</button>
        <p class="erreur" role="alert"></p>
        <div class="barre-enregistrer"><a class="lien" href="#/admin/quizz">Annuler</a>
          <button class="bouton">Enregistrer le quizz</button></div>
      </form>
    </section>`;
    const form = $("#form-q");
    const lire = () => {
      const f = new FormData(form);
      q.titre = f.get("titre"); q.description = f.get("description"); q.theme = f.get("theme"); q.duree = f.get("duree") ? Number(f.get("duree")) : null;
      form.querySelectorAll(".fiche-ed").forEach(li => {
        const x = q.questions[li.dataset.i];
        x.enonce = $("textarea[name=enonce]", li).value;
        x.explication = $("textarea[name=explication]", li).value;
        li.querySelectorAll(".choix-ed-ligne").forEach(l => {
          x.choix[l.dataset.k] = { texte: $(".texte-choix", l).value, correct: $("[data-act=correct]", l).checked };
        });
      });
    };
    form.addEventListener("click", e => {
      const b = e.target.closest("button[data-act]");
      if (!b) return;
      lire();
      const li = b.closest(".fiche-ed"), x = q.questions[li.dataset.i];
      if (b.dataset.act === "suppr-q") q.questions.splice(li.dataset.i, 1);
      if (b.dataset.act === "ajout-c") x.choix.push({ texte: "", correct: false });
      if (b.dataset.act === "suppr-c") x.choix.splice(b.closest(".choix-ed-ligne").dataset.k, 1);
      rendre();
    });
    $("#ajout-q").addEventListener("click", () => {
      lire(); q.questions.push({ enonce: "", choix: [{ texte: "", correct: true }, { texte: "", correct: false }] }); rendre();
      contenu.querySelector(".fiche-ed:last-child textarea").focus();
    });
    form.addEventListener("submit", async e => {
      e.preventDefault(); lire();
      const err = $(".erreur", form);
      try {
        await api(id ? `admin/quizz/${id}` : "admin/quizz", { methode: id ? "PUT" : "POST", corps: q });
        etat.brouillon = null;
        toast("Enregistré en brouillon : teste-le, puis valide-le pour le publier.");
        aller("#/admin/quizz");
      } catch (x) { err.textContent = x.message; err.scrollIntoView({ block: "center", behavior: "smooth" }); }
    });
  };
  rendre();
}

function vueImporter() {
  if (!etat.utilisateur.admin) return aller("#/");
  contenu.innerHTML = `
  <section class="page etroite">
    <a class="retour" href="#/admin/quizz">${icone("retour")}Quizz</a>
    <h1 class="titre-page">Importer un quizz</h1>
    <p class="sous">Un fichier texte (.txt) au format Kwizz, ou un export JSON (.json). Tu pourras le relire avant de l'enregistrer.</p>
    <label class="depot" id="depot">
      <input type="file" accept=".txt,.json,text/plain,application/json" id="fichier">
      <strong>Dépose un fichier ici</strong><span>ou clique pour le choisir</span>
    </label>
    <p class="erreur" role="alert"></p>
    <details class="format"><summary>Rappel du format texte</summary>
<pre># TITRE: Capitales d'Europe
# DESCRIPTION: Teste tes connaissances
# DUREE: 60
Q: Quelle est la capitale de l'Italie ?
- Milan
+ Rome
- Naples</pre>
      <p><code>+</code> bonne réponse, <code>-</code> mauvaise réponse ; au moins 2 choix et 1 bonne réponse par question.</p></details>
  </section>`;
  const depot = $("#depot"), err = $(".erreur", contenu);
  const lireFichier = async f => {
    if (!f) return;
    err.textContent = "";
    try {
      const contenuTexte = await f.text();
      etat.brouillon = await api("admin/import", { methode: "POST", corps: { nom: f.name, contenu: contenuTexte } });
      aller("#/admin/brouillon");
    } catch (x) { err.textContent = x.message; }
  };
  $("#fichier").addEventListener("change", e => lireFichier(e.target.files[0]));
  ["dragenter", "dragover"].forEach(t => depot.addEventListener(t, e => { e.preventDefault(); depot.classList.add("survol"); }));
  ["dragleave", "drop"].forEach(t => depot.addEventListener(t, () => depot.classList.remove("survol")));
  depot.addEventListener("drop", e => { e.preventDefault(); lireFichier(e.dataTransfer.files[0]); });
}

function vueGenerer() {
  if (!etat.utilisateur.admin) return aller("#/");
  if (!etat.ia) return aller("#/admin/quizz");
  contenu.innerHTML = `
  <section class="page etroite">
    <a class="retour" href="#/admin/quizz">${icone("retour")}Quizz</a>
    <h1 class="titre-page">Générer avec l'IA</h1>
    <p class="sous">L'IA propose un quizz ; rien n'est enregistré avant ta relecture.</p>
    <form class="formulaire" novalidate>
      <fieldset class="segments"><legend>À partir de</legend>
        <label><input type="radio" name="mode" value="theme" checked><span>Un thème</span></label>
        <label><input type="radio" name="mode" value="texte"><span>Un texte collé</span></label>
      </fieldset>
      <label class="champ" id="champ-sujet"><span>Thème</span><input name="sujet" placeholder="Par exemple : la méthode PERT" required></label>
      <label class="champ"><span>Nombre de questions</span><input name="nb" type="number" min="1" max="20" value="5" inputmode="numeric"></label>
      <p class="erreur" role="alert"></p>
      <button class="bouton large">Proposer un quizz</button>
    </form>
  </section>`;
  const form = $("form", contenu);
  form.addEventListener("change", e => {
    if (e.target.name !== "mode") return;
    const texte = e.target.value === "texte", ancien = form.sujet.value;
    $("#champ-sujet").innerHTML = texte
      ? `<span>Texte</span><textarea name="sujet" rows="8" required placeholder="Colle ici un cours ou un article"></textarea><small>20 000 caractères maximum.</small>`
      : `<span>Thème</span><input name="sujet" placeholder="Par exemple : la méthode PERT" required>`;
    form.sujet.value = ancien;
  });
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const b = $("button", form), err = $(".erreur", form);
    b.disabled = true; b.textContent = "L'IA rédige les questions…"; err.textContent = "";
    try {
      etat.brouillon = await api("admin/generer", { methode: "POST", corps: {
        sujet: form.sujet.value, nb: Number(form.nb.value), depuis_texte: form.mode.value === "texte" } });
      aller("#/admin/brouillon");
    } catch (x) { err.textContent = x.message; b.disabled = false; b.textContent = "Proposer un quizz"; }
  });
}

/* ------------------------------------------------------------ démarrage */
$(".rail .marque").innerHTML = logoKwizz();
$("#deconnexion").addEventListener("click", async () => {
  await api("deconnexion", { methode: "POST" }).catch(() => {});
  Object.assign(etat, { utilisateur: null, partie: null, resultat: null, brouillon: null, theme: null, filtreJournal: null });
  aller("#/bienvenue");
});

/* ------------------------------------------------------------ assistant RAG (V2) */
const SUGGESTIONS = ["C'est quoi la loi d'Ohm ?", "Pourquoi la recherche dichotomique est en O(log n) ?",
  "Combien de chromosomes a une cellule humaine ?", "Comment calculer un discriminant ?",
  "Quand est tombé le mur de Berlin ?", "Qui a écrit Les Misérables ?"];

function bulleHtml(m) {
  if (m.moi) return `<li class="bulle moi"><p>${h(m.texte)}</p></li>`;
  const sources = (m.sources || []).map(s => `<li><strong>${h(s.fiche)}</strong> · ${h(s.section)}
      ${s.liens.length ? `<span class="liens-source">${s.liens.map(l =>
        `<a href="${h(l)}" target="_blank" rel="noopener noreferrer">${h(new URL(l).hostname.replace(/^www\./, ""))}</a>`).join("")}</span>` : ""}</li>`).join("");
  return `<li class="bulle"><p>${h(m.texte)}</p>
    ${sources ? `<details class="sources"><summary>Sources (${m.sources.length})${m.mode === "fiches" ? " · réponse tirée des fiches" : ""}</summary><ul>${sources}</ul></details>` : ""}</li>`;
}

async function vueAssistant() {
  chargement(3);
  // le fil vient du serveur à chaque visite (jamais gardé dans la page) : chacun ne voit que le sien
  const chat = (await api("assistant")).flatMap(e => [{ moi: true, texte: e.question },
    { texte: e.reponse, sources: e.sources, mode: e.mode }]);
  contenu.innerHTML = `
  <section class="page assistant">
    <header class="entete ligne"><div><h1 class="titre-page">Assistant</h1>
      <p class="sous">Pose une question de cours : il répond à partir des fiches de MyKwizz et te donne des ressources fiables.</p></div>
      <div class="actions"><button class="bouton secondaire" type="button" id="chat-nouveau">Nouvelle discussion</button></div></header>
    <ol class="fil" id="fil" aria-live="polite">${chat.map(bulleHtml).join("") ||
      `<li class="bulle"><p>Salut ${h(etat.utilisateur.login)} ! Je connais la Culture générale, le Code, l'Histoire, les Mathématiques, la Physique-Chimie et les SVT. Que veux-tu comprendre ?</p></li>`}</ol>
    <div class="suggestions">${SUGGESTIONS.map(s => `<button type="button" class="puce">${h(s)}</button>`).join("")}</div>
    <form class="zone-saisie" id="chat-form">
      <label class="vh" for="chat-q">Ta question</label>
      <input id="chat-q" name="question" maxlength="500" autocomplete="off" placeholder="Ex. : c'est quoi la photosynthèse ?" required>
      <button class="bouton">Envoyer</button>
    </form>
  </section>`;
  const form = $("#chat-form"), champ = $("#chat-q"), fil = $("#fil");
  const defiler = () => fil.lastElementChild?.scrollIntoView({ block: "end", behavior: "smooth" });
  async function envoyer(question) {
    if (!question.trim()) return;
    fil.insertAdjacentHTML("beforeend", bulleHtml({ moi: true, texte: question }) + `<li class="bulle attente" id="attente"><p>…</p></li>`);
    defiler(); champ.value = ""; $("button", form).disabled = true;
    let bulle;
    try {
      const r = await api("assistant", { methode: "POST", corps: { question } });
      bulle = { texte: r.reponse, sources: r.sources, mode: r.mode };
    } catch (x) { bulle = { texte: x.message }; }
    $("#attente")?.remove();
    fil.insertAdjacentHTML("beforeend", bulleHtml(bulle));
    $("button", form).disabled = false; champ.focus(); defiler();
  }
  form.addEventListener("submit", e => { e.preventDefault(); envoyer(champ.value); });
  contenu.querySelectorAll(".puce").forEach(b => b.addEventListener("click", () => envoyer(b.textContent)));
  $("#chat-nouveau").addEventListener("click", async () => {
    await api("assistant", { methode: "DELETE" }).catch(() => {});
    vueAssistant();
  });
  champ.focus();
}

/* ------------------------------------------------------------ espace joueur (V2) */
function barres(lignes) {
  return `<ul class="barres">${lignes.map(l => `<li><span class="barre-nom">${h(l.theme)}</span>
    <span class="barre" role="img" aria-label="${l.reussite} % de réussite"><span style="width: ${l.reussite}%"></span></span>
    <span class="barre-val">${l.reussite} %<small> · ${pluriel(l.parties, "partie")}</small></span></li>`).join("")}</ul>`;
}

async function vueMoi() {
  chargement(4);
  const m = await api("moi");
  contenu.innerHTML = `
  <section class="page">
    <header class="entete"><h1 class="titre-page">Mon espace</h1>
      <p class="sous">Compte <strong>${h(m.login)}</strong>, créé le ${date(m.depuis)}.</p></header>
    <ul class="cartes-stats">
      <li><span>Parties jouées</span><strong>${chiffres(m.parties)}</strong></li>
      <li><span>Réussite moyenne</span><strong>${chiffres(m.reussite)}<small> %</small></strong></li>
      <li><span>Quizz découverts</span><strong>${chiffres(m.quizz_joues)}<small> / ${m.quizz_total}</small></strong></li>
      <li><span>Temps de jeu</span><strong>${duree(m.temps_total)}</strong></li>
    </ul>
    <h2 class="titre-section">Réussite par thème</h2>
    ${m.themes.length ? barres(m.themes) : `<p class="note">Joue un premier quizz pour voir tes points forts par thème.</p>`}
    <div class="deux-colonnes">
      <div class="carte-acces">
        <h2 class="titre-carte">Changer mon mot de passe</h2>
        <form class="formulaire" id="f-mdp" novalidate>
          <label class="champ"><span>Mot de passe actuel</span><input name="ancien" type="password" autocomplete="current-password" required></label>
          <label class="champ"><span>Nouveau mot de passe</span><input name="nouveau" type="password" autocomplete="new-password" minlength="8" required>
            <small>8 caractères minimum, avec au moins une lettre et un chiffre.</small></label>
          <label class="champ"><span>Confirme-le</span><input name="confirmation" type="password" autocomplete="new-password" required></label>
          <p class="erreur" role="alert"></p>
          <button class="bouton">Enregistrer</button>
        </form>
      </div>
      <div class="carte-acces raccourcis">
        <h2 class="titre-carte">Continuer</h2>
        <a class="bouton" href="#/">Jouer un quizz</a>
        <a class="bouton secondaire" href="#/historique">Voir mon historique</a>
        <a class="bouton secondaire" href="#/assistant">Poser une question à l'assistant</a>
      </div>
    </div>
  </section>`;
  const form = $("#f-mdp");
  form.addEventListener("submit", async e => {
    e.preventDefault();
    try {
      await api("mot-de-passe", { methode: "POST", corps: Object.fromEntries(new FormData(form)) });
      form.reset(); $(".erreur", form).textContent = ""; toast("Mot de passe modifié.");
    } catch (x) { $(".erreur", form).textContent = x.message; }
  });
}

/* ------------------------------------------------------------ administration : comptes (V2) */
function sousNavAdmin(actif) {
  const onglets = [["bord", "#/admin", "Tableau de bord"], ["quizz", "#/admin/quizz", "Quizz"],
    ["comptes", "#/admin/utilisateurs", "Utilisateurs"], ["journal", "#/admin/journal", "Journal d'activité"]];
  return `<nav class="onglets-quizz" aria-label="Administration">${onglets.map(([cle, lien, nom]) =>
    `<a href="${lien}" class="${actif === cle ? "actif" : ""}" ${actif === cle ? 'aria-current="page"' : ""}>${nom}</a>`).join("")}</nav>`;
}

async function vueUtilisateurs() {
  if (!etat.utilisateur.admin) return aller("#/");
  chargement(4);
  const liste = await api("admin/utilisateurs");
  contenu.innerHTML = `
  <section class="page">
    <header class="entete"><h1 class="titre-page">Administration</h1>
      <p class="sous">Crée, modifie et supprime les comptes. Les mots de passe ne sont jamais visibles, seulement réinitialisables.</p></header>
    ${sousNavAdmin("comptes")}
    <form class="carte-acces formulaire ligne-ajout" id="f-ajout" novalidate>
      <h2 class="titre-carte">Nouveau compte</h2>
      <label class="champ"><span>Login</span><input name="login" required minlength="3" maxlength="30" autocomplete="off"></label>
      <label class="champ"><span>Mot de passe</span><input name="mdp" type="password" required minlength="8" autocomplete="new-password">
        <small>8 caractères, une lettre et un chiffre.</small></label>
      <label class="case"><input type="checkbox" name="admin"> Administrateur</label>
      <p class="erreur" role="alert"></p>
      <button class="bouton">Créer le compte</button>
    </form>
    <table class="table-admin">
      <thead><tr><th scope="col">Login</th><th scope="col">Rôle</th><th scope="col">Parties</th><th scope="col">Réussite</th><th scope="col">Créé le</th><th scope="col"><span class="vh">Actions</span></th></tr></thead>
      <tbody>${liste.map(u => `<tr data-id="${u.id}" data-login="${h(u.login)}" data-admin="${u.admin ? 1 : 0}">
        <th scope="row">${h(u.login)}${u.login === etat.utilisateur.login ? " (toi)" : ""}</th>
        <td>${u.admin ? "admin" : "joueur"}</td><td>${u.parties}</td><td>${u.parties ? u.reussite + " %" : "—"}</td><td>${date(u.date)}</td>
        <td class="cellule-actions"><button class="lien fort" type="button" data-act="historique">Historique</button>
          <button class="lien" type="button" data-act="modifier">Modifier</button>
          ${u.login === etat.utilisateur.login ? "" : `<button class="bouton-suppr" type="button" data-act="suppr">Supprimer</button>`}</td>
      </tr>`).join("")}</tbody></table>
  </section>`;
  const fa = $("#f-ajout");
  fa.addEventListener("submit", async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(fa)); d.admin = !!d.admin;
    try { await api("admin/utilisateurs", { methode: "POST", corps: d }); toast(`Compte « ${d.login} » créé.`); vueUtilisateurs(); }
    catch (x) { $(".erreur", fa).textContent = x.message; }
  });
  contenu.querySelectorAll("tbody button").forEach(b => b.addEventListener("click", async () => {
    const tr = b.closest("tr"), id = tr.dataset.id;
    if (b.dataset.act === "historique") return ouvrirHistorique(id);
    if (b.dataset.act === "suppr") {
      if (!(await confirmer({ titre: `Supprimer le compte « ${tr.dataset.login} » ?`, danger: true, action: "Supprimer",
        texte: "Il ne pourra plus se connecter. S'il a déjà joué, son compte est anonymisé : ses parties restent dans les statistiques, sans son nom. Sinon, il est effacé. Cette action est définitive." }))) return;
      try {
        const r = await api(`admin/utilisateurs/${id}`, { methode: "DELETE" });
        toast(r.anonymise ? "Compte anonymisé : ses parties restent dans les statistiques." : "Compte supprimé.");
        vueUtilisateurs();
      }
      catch (x) { toast(x.message, "alerte"); }
      return;
    }
    const d = $("#dialogue");
    d.innerHTML = `<form method="dialog" class="dialogue-corps formulaire" novalidate>
      <h2>Modifier « ${h(tr.dataset.login)} »</h2>
      <label class="champ"><span>Login</span><input name="login" value="${h(tr.dataset.login)}" required></label>
      <label class="champ"><span>Nouveau mot de passe</span><input name="mdp" type="password" autocomplete="new-password" placeholder="inchangé si vide"></label>
      <label class="case"><input type="checkbox" name="admin" ${tr.dataset.admin === "1" ? "checked" : ""}> Administrateur</label>
      <p class="erreur" role="alert"></p>
      <div class="dialogue-actions"><button value="non" class="bouton secondaire" formnovalidate>Annuler</button>
        <button value="oui" class="bouton">Enregistrer</button></div></form>`;
    const f = $("form", d);
    f.addEventListener("submit", async e => {
      if (e.submitter?.value !== "oui") return;
      e.preventDefault();
      const v = Object.fromEntries(new FormData(f)); v.admin = !!v.admin;
      try { await api(`admin/utilisateurs/${id}`, { methode: "PUT", corps: v }); d.close(); toast("Compte modifié."); vueUtilisateurs(); }
      catch (x) { $(".erreur", f).textContent = x.message; }
    });
    d.showModal();
  }));
}

window.addEventListener("hashchange", route);
(async () => {
  try {
    const e = await api("etat");
    etat.utilisateur = e.utilisateur; etat.ia = e.ia;
  } catch (x) { contenu.innerHTML = `<section class="page"><div class="vide"><h1 class="titre-page">Hors ligne</h1><p>${h(x.message)}</p></div></section>`; return; }
  route();
})();
